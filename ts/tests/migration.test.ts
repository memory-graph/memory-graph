/**
 * Tests for migration manager.
 */

import { describe, test, expect, beforeEach, afterEach } from "bun:test";
import { SQLiteBackend } from "../src/backends/sqlite.js";
import { MemoryDatabase } from "../src/database.js";
import { createMemory } from "../src/models.js";
import {
  MigrationManager,
  backendConfigFromEnv,
  createMigrationOptions,
  type BackendConfig,
} from "../src/migration/index.js";
import { unlinkSync, existsSync } from "node:fs";
import { join } from "node:path";
import { tmpdir } from "node:os";

const SOURCE_DB = join(tmpdir(), `mg-migrate-src-${Date.now()}.db`);
const TARGET_DB = join(tmpdir(), `mg-migrate-tgt-${Date.now()}.db`);

describe("Migration Manager", () => {
  let sourceBackend: SQLiteBackend;
  let sourceDb: MemoryDatabase;

  beforeEach(async () => {
    sourceBackend = new SQLiteBackend(SOURCE_DB);
    await sourceBackend.connect();
    await sourceBackend.initializeSchema();
    sourceDb = new MemoryDatabase(sourceBackend);

    // Add test data
    await sourceDb.storeMemory(
      createMemory({ type: "solution", title: "Migration Test 1", content: "Content 1" })
    );
    await sourceDb.storeMemory(
      createMemory({ type: "problem", title: "Migration Test 2", content: "Content 2" })
    );
  });

  afterEach(async () => {
    await sourceBackend.disconnect();
    for (const dbPath of [SOURCE_DB, TARGET_DB]) {
      try {
        if (existsSync(dbPath)) unlinkSync(dbPath);
      } catch {
        // ignore
      }
    }
  });

  test("dry-run migration validates successfully", async () => {
    const sourceConfig: BackendConfig = {
      backend_type: "sqlite",
      path: SOURCE_DB,
    };
    const targetConfig: BackendConfig = {
      backend_type: "sqlite",
      path: TARGET_DB,
    };

    const manager = new MigrationManager();
    const result = await manager.migrate(
      sourceConfig,
      targetConfig,
      createMigrationOptions({ dry_run: true })
    );

    expect(result.success).toBe(true);
    expect(result.dry_run).toBe(true);
  });

  test("full migration transfers memories", async () => {
    const sourceConfig: BackendConfig = {
      backend_type: "sqlite",
      path: SOURCE_DB,
    };
    const targetConfig: BackendConfig = {
      backend_type: "sqlite",
      path: TARGET_DB,
    };

    const manager = new MigrationManager();
    const result = await manager.migrate(
      sourceConfig,
      targetConfig,
      createMigrationOptions({ dry_run: false, verify: true })
    );

    expect(result.success).toBe(true);
    expect(result.imported_memories).toBe(2);

    // Verify data was transferred
    const targetBackend = new SQLiteBackend(TARGET_DB);
    await targetBackend.connect();
    await targetBackend.initializeSchema();
    const targetDb = new MemoryDatabase(targetBackend);

    const allMemories = await targetDb.searchMemories({
      query: undefined,
      terms: [],
      memory_types: [],
      tags: [],
      project_path: undefined,
      languages: [],
      frameworks: [],
      min_importance: undefined,
      min_confidence: undefined,
      min_effectiveness: undefined,
      created_after: undefined,
      created_before: undefined,
      limit: 100,
      offset: 0,
      include_relationships: true,
      search_tolerance: "normal",
      match_mode: "any",
      relationship_filter: undefined,
    });

    expect(allMemories.length).toBe(2);
    await targetBackend.disconnect();
  });

  test("backendConfigFromEnv reads from environment", () => {
    process.env["MEMORY_BACKEND"] = "sqlite";
    process.env["MEMORY_SQLITE_PATH"] = SOURCE_DB;
    const config = backendConfigFromEnv();
    expect(config.backend_type).toBe("sqlite");
    expect(config.path).toBe(SOURCE_DB);
  });
});
