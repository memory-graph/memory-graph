/**
 * Tests for the activity tools, including the fixed
 * handleSearchRelationshipsByContext.
 */

import { describe, test, expect, beforeEach, afterEach } from "bun:test";
import { SQLiteBackend } from "../src/backends/sqlite.js";
import { MemoryDatabase } from "../src/database.js";
import { createMemory, createRelationshipProperties } from "../src/models.js";
import { handleSearchRelationshipsByContext, handleGetRecentActivity } from "../src/tools/activity.js";
import { unlinkSync, existsSync } from "node:fs";
import { join } from "node:path";
import { tmpdir } from "node:os";

const TEST_DB = join(tmpdir(), `mg-activity-test-${Date.now()}.db`);

describe("handleSearchRelationshipsByContext", () => {
  let backend: SQLiteBackend;
  let db: MemoryDatabase;

  beforeEach(async () => {
    backend = new SQLiteBackend(TEST_DB);
    await backend.connect();
    await backend.initializeSchema();
    db = new MemoryDatabase(backend);

    // Store a problem and a solution
    const problem = createMemory({
      type: "problem",
      title: "Redis timeout errors",
      content: "Getting connection timeout errors from Redis in production",
      tags: ["redis", "production"],
      importance: 0.8,
    });
    const problemId = await db.storeMemory(problem);

    const solution = createMemory({
      type: "solution",
      title: "Use exponential backoff",
      content: "Implement retry logic with exponential backoff for Redis connections",
      tags: ["redis", "retry"],
      importance: 0.9,
    });
    const solutionId = await db.storeMemory(solution);

    // Link solution to problem
    await db.createRelationship(solutionId, problemId, "SOLVES", createRelationshipProperties({
      strength: 0.85,
      confidence: 0.9,
    }));
  });

  afterEach(async () => {
    await backend.disconnect();
    try {
      if (existsSync(TEST_DB)) unlinkSync(TEST_DB);
    } catch {
      // ignore
    }
  });

  test("returns error when memory_id is missing", async () => {
    const result = await handleSearchRelationshipsByContext(db, {});
    expect(result.text).toContain("'memory_id' parameter is required");
  });

  test("returns error for non-existent memory", async () => {
    const result = await handleSearchRelationshipsByContext(db, { memory_id: "nonexistent-id" });
    expect(result.text).toContain("Memory not found");
  });

  test("finds relationships for a memory", async () => {
    // First get the problem memory ID
    const memories = await db.searchMemories({
      query: "Redis timeout",
      terms: [],
      memory_types: ["problem"],
      tags: [],
      project_path: undefined,
      languages: [],
      frameworks: [],
      min_importance: undefined,
      min_confidence: undefined,
      min_effectiveness: undefined,
      created_after: undefined,
      created_before: undefined,
      limit: 10,
      offset: 0,
      include_relationships: true,
      search_tolerance: "normal",
      match_mode: "any",
      relationship_filter: undefined,
    });

    expect(memories.length).toBeGreaterThan(0);
    const problemId = memories[0].id!;

    const result = await handleSearchRelationshipsByContext(db, { memory_id: problemId });
    expect(result.text).toContain("Relationships for");
    expect(result.text).toContain("SOLVES");
  });

  test("filters by relationship type", async () => {
    const memories = await db.searchMemories({
      query: "Redis timeout",
      terms: [],
      memory_types: ["problem"],
      tags: [],
      project_path: undefined,
      languages: [],
      frameworks: [],
      min_importance: undefined,
      min_confidence: undefined,
      min_effectiveness: undefined,
      created_after: undefined,
      created_before: undefined,
      limit: 10,
      offset: 0,
      include_relationships: true,
      search_tolerance: "normal",
      match_mode: "any",
      relationship_filter: undefined,
    });

    const problemId = memories[0].id!;
    const result = await handleSearchRelationshipsByContext(db, {
      memory_id: problemId,
      relationship_types: ["SOLVES"],
    });
    expect(result.text).toContain("SOLVES");
  });

  test("filters by minimum strength", async () => {
    const memories = await db.searchMemories({
      query: "Redis timeout",
      terms: [],
      memory_types: ["problem"],
      tags: [],
      project_path: undefined,
      languages: [],
      frameworks: [],
      min_importance: undefined,
      min_confidence: undefined,
      min_effectiveness: undefined,
      created_after: undefined,
      created_before: undefined,
      limit: 10,
      offset: 0,
      include_relationships: true,
      search_tolerance: "normal",
      match_mode: "any",
      relationship_filter: undefined,
    });

    const problemId = memories[0].id!;

    // High threshold should still find the relationship (strength 0.85)
    const result = await handleSearchRelationshipsByContext(db, {
      memory_id: problemId,
      min_strength: 0.8,
    });
    expect(result.text).toContain("SOLVES");

    // Very high threshold should find nothing
    const result2 = await handleSearchRelationshipsByContext(db, {
      memory_id: problemId,
      min_strength: 0.99,
    });
    expect(result2.text).toContain("No relationships found");
  });
});

describe("handleGetRecentActivity", () => {
  let backend: SQLiteBackend;
  let db: MemoryDatabase;

  beforeEach(async () => {
    backend = new SQLiteBackend(TEST_DB);
    await backend.connect();
    await backend.initializeSchema();
    db = new MemoryDatabase(backend);

    const mem = createMemory({
      type: "solution",
      title: "Recent solution",
      content: "A recently stored solution",
      tags: ["test"],
      importance: 0.5,
    });
    await db.storeMemory(mem);
  });

  afterEach(async () => {
    await backend.disconnect();
    try {
      if (existsSync(TEST_DB)) unlinkSync(TEST_DB);
    } catch {
      // ignore
    }
  });

  test("returns activity summary", async () => {
    const result = await handleGetRecentActivity(db, { days: 7 });
    expect(result.text).toContain("Recent Activity Summary");
    expect(result.text).toContain("Total Memories");
  });

  test("includes recent memories in output", async () => {
    const result = await handleGetRecentActivity(db, { days: 7 });
    expect(result.text).toContain("Recent solution");
  });
});
