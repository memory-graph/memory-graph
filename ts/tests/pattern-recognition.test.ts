/**
 * Tests for the pattern recognition intelligence module.
 *
 * findSimilarProblems() and suggestPatterns() require a Cypher-capable
 * backend, so we test the module structure and error handling here.
 */

import { describe, test, expect } from "bun:test";
import { PatternRecognizer, findSimilarProblems, suggestPatterns, extractPatterns } from "../src/intelligence/pattern-recognition.js";
import { SQLiteBackend } from "../src/backends/sqlite.js";
import { join } from "node:path";
import { tmpdir } from "node:os";

const TEST_DB = join(tmpdir(), `mg-pattern-test-${Date.now()}.db`);

describe("PatternRecognizer module structure", () => {
  test("PatternRecognizer class can be instantiated", () => {
    const backend = new SQLiteBackend(TEST_DB);
    const recognizer = new PatternRecognizer(backend);
    expect(recognizer).toBeDefined();
    expect(recognizer.backend).toBe(backend);
  });

  test("findSimilarProblems is exported", () => {
    expect(typeof findSimilarProblems).toBe("function");
  });

  test("suggestPatterns is exported", () => {
    expect(typeof suggestPatterns).toBe("function");
  });

  test("extractPatterns is exported", () => {
    expect(typeof extractPatterns).toBe("function");
  });

  test("findSimilarProblems returns empty array on non-Cypher backend without crashing", async () => {
    const backend = new SQLiteBackend(TEST_DB);
    const results = await findSimilarProblems(backend, "connection timeout error");
    expect(results).toBeDefined();
    expect(Array.isArray(results)).toBe(true);
  });

  test("suggestPatterns returns empty array on non-Cypher backend without crashing", async () => {
    const backend = new SQLiteBackend(TEST_DB);
    const patterns = await suggestPatterns(backend, "timeout connection");
    expect(patterns).toBeDefined();
    expect(Array.isArray(patterns)).toBe(true);
  });
});
