/**
 * Tests for temporal tools.
 */

import { describe, test, expect, beforeEach, afterEach } from "bun:test";
import { SQLiteBackend } from "../src/backends/sqlite.js";
import { MemoryDatabase } from "../src/database.js";
import { createMemory, createRelationshipProperties } from "../src/models.js";
import {
  handleQueryAsOf,
  handleGetRelationshipHistory,
  handleWhatChanged,
} from "../src/tools/temporal.js";
import { unlinkSync, existsSync } from "node:fs";
import { join } from "node:path";
import { tmpdir } from "node:os";

const TEST_DB = join(tmpdir(), `mg-temporal-test-${Date.now()}.db`);

describe("Temporal Tools", () => {
  let backend: SQLiteBackend;
  let db: MemoryDatabase;

  beforeEach(async () => {
    backend = new SQLiteBackend(TEST_DB);
    await backend.connect();
    await backend.initializeSchema();
    db = new MemoryDatabase(backend);
  });

  afterEach(async () => {
    await backend.disconnect();
    try {
      if (existsSync(TEST_DB)) unlinkSync(TEST_DB);
    } catch {
      // ignore
    }
  });

  test("query_as_of finds relationships valid at a time", async () => {
    const problemId = await db.storeMemory(
      createMemory({ type: "problem", title: "Problem", content: "A problem" })
    );
    const solutionId = await db.storeMemory(
      createMemory({ type: "solution", title: "Solution", content: "A solution" })
    );

    await db.createRelationship(
      solutionId,
      problemId,
      "SOLVES",
      createRelationshipProperties({ strength: 0.9 })
    );

    // Query as of now
    const result = await handleQueryAsOf(db, {
      memory_id: solutionId,
      as_of: new Date().toISOString(),
    });

    expect(result.isError).toBe(false);
    expect(result.text).toContain("SOLVES");
    expect(result.text).toContain("Problem");
  });

  test("query_as_of returns error for non-existent memory", async () => {
    const result = await handleQueryAsOf(db, {
      memory_id: "nonexistent",
      as_of: new Date().toISOString(),
    });

    expect(result.text).toContain("Memory not found");
  });

  test("query_as_of handles invalid timestamp", async () => {
    const memId = await db.storeMemory(
      createMemory({ type: "solution", title: "Test", content: "Content" })
    );

    const result = await handleQueryAsOf(db, {
      memory_id: memId,
      as_of: "invalid-timestamp",
    });

    expect(result.text).toContain("Invalid timestamp format");
  });

  test("get_relationship_history returns history", async () => {
    const problemId = await db.storeMemory(
      createMemory({ type: "problem", title: "Problem", content: "A problem" })
    );
    const solutionId = await db.storeMemory(
      createMemory({ type: "solution", title: "Solution", content: "A solution" })
    );

    await db.createRelationship(solutionId, problemId, "SOLVES");

    const result = await handleGetRelationshipHistory(db, {
      memory_id: solutionId,
    });

    expect(result.isError).toBe(false);
    expect(result.text).toContain("SOLVES");
  });

  test("what_changed finds recent changes", async () => {
    const problemId = await db.storeMemory(
      createMemory({ type: "problem", title: "Problem", content: "A problem" })
    );
    const solutionId = await db.storeMemory(
      createMemory({ type: "solution", title: "Solution", content: "A solution" })
    );

    await db.createRelationship(solutionId, problemId, "SOLVES");

    // Query changes since 1 hour ago
    const oneHourAgo = new Date(Date.now() - 3600 * 1000).toISOString();
    const result = await handleWhatChanged(db, {
      since: oneHourAgo,
    });

    expect(result.isError).toBe(false);
    expect(result.text).toContain("New Relationships");
  });

  test("what_changed returns no changes for old timestamp range", async () => {
    // Query changes since far future
    const future = new Date(Date.now() + 365 * 24 * 3600 * 1000).toISOString();
    const result = await handleWhatChanged(db, {
      since: future,
    });

    expect(result.text).toContain("No relationship changes found");
  });
});
