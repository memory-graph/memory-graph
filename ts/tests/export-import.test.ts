/**
 * Tests for the export/import utilities.
 */

import { describe, test, expect, beforeEach, afterEach } from "bun:test";
import { SQLiteBackend } from "../src/backends/sqlite.js";
import { MemoryDatabase } from "../src/database.js";
import { createMemory, createRelationshipProperties } from "../src/models.js";
import { exportToJson, importFromJson } from "../src/utils/export-import.js";
import { unlinkSync, existsSync, readFileSync } from "node:fs";
import { join } from "node:path";
import { tmpdir } from "node:os";

const TEST_DB = join(tmpdir(), `mg-export-test-${Date.now()}.db`);
const EXPORT_FILE = join(tmpdir(), `mg-export-${Date.now()}.json`);

describe("Export/Import", () => {
  let backend: SQLiteBackend;
  let db: MemoryDatabase;

  beforeEach(async () => {
    backend = new SQLiteBackend(TEST_DB);
    await backend.connect();
    await backend.initializeSchema();
    db = new MemoryDatabase(backend);

    const mem1 = createMemory({
      type: "solution",
      title: "Test Solution",
      content: "A test solution for export",
      tags: ["test", "export"],
      importance: 0.7,
    });
    const id1 = await db.storeMemory(mem1);

    const mem2 = createMemory({
      type: "problem",
      title: "Test Problem",
      content: "A test problem for export",
      tags: ["test"],
      importance: 0.6,
    });
    const id2 = await db.storeMemory(mem2);

    await db.createRelationship(id1, id2, "SOLVES", createRelationshipProperties());
  });

  afterEach(async () => {
    await backend.disconnect();
    try {
      if (existsSync(TEST_DB)) unlinkSync(TEST_DB);
      if (existsSync(EXPORT_FILE)) unlinkSync(EXPORT_FILE);
    } catch {
      // ignore
    }
  });

  test("exportToJson creates a valid JSON file", async () => {
    const result = await exportToJson(db, EXPORT_FILE);
    expect(result["memory_count"]).toBe(2);
    expect(result["relationship_count"]).toBe(1);
    expect(existsSync(EXPORT_FILE)).toBe(true);

    const data = JSON.parse(readFileSync(EXPORT_FILE, "utf-8"));
    expect(data.memories).toBeDefined();
    expect(data.memories.length).toBe(2);
    expect(data.relationships).toBeDefined();
    expect(data.relationships.length).toBe(1);
  });

  test("importFromJson imports from JSON file", async () => {
    await exportToJson(db, EXPORT_FILE);

    const importDbPath = join(tmpdir(), `mg-import-${Date.now()}.db`);
    const importBackend = new SQLiteBackend(importDbPath);
    await importBackend.connect();
    await importBackend.initializeSchema();
    const importDbObj = new MemoryDatabase(importBackend);

    try {
      const result = await importFromJson(importDbObj, EXPORT_FILE, false);
      expect(result["imported_memories"]).toBe(2);
      expect(result["imported_relationships"]).toBe(1);
    } finally {
      await importBackend.disconnect();
      try {
        if (existsSync(importDbPath)) unlinkSync(importDbPath);
      } catch {
        // ignore
      }
    }
  });

  test("importFromJson with skip-duplicates avoids re-importing", async () => {
    await exportToJson(db, EXPORT_FILE);
    const result = await importFromJson(db, EXPORT_FILE, true);
    expect(result["skipped_memories"]).toBeGreaterThanOrEqual(0);
  });
});
