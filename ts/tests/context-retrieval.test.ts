/**
 * Tests for the context retrieval intelligence module.
 *
 * getContext() requires a Cypher-capable backend, so we test the
 * module structure and error handling here.
 */

import { describe, test, expect } from "bun:test";
import { ContextRetriever, getContext, getProjectContext, getSessionContext } from "../src/intelligence/context-retrieval.js";
import { SQLiteBackend } from "../src/backends/sqlite.js";
import { join } from "node:path";
import { tmpdir } from "node:os";

const TEST_DB = join(tmpdir(), `mg-context-test-${Date.now()}.db`);

describe("ContextRetriever module structure", () => {
  test("ContextRetriever class can be instantiated", () => {
    const backend = new SQLiteBackend(TEST_DB);
    const retriever = new ContextRetriever(backend);
    expect(retriever).toBeDefined();
    expect(retriever.backend).toBe(backend);
  });

  test("getContext function is exported", () => {
    expect(typeof getContext).toBe("function");
  });

  test("getProjectContext function is exported", () => {
    expect(typeof getProjectContext).toBe("function");
  });

  test("getSessionContext function is exported", () => {
    expect(typeof getSessionContext).toBe("function");
  });

  test("getContext returns result on non-Cypher backend without crashing", async () => {
    const backend = new SQLiteBackend(TEST_DB);
    const result = await getContext(backend, "validation", 4000, null);
    expect(result).toBeDefined();
    expect(result.source_memories).toBeDefined();
  });
});
