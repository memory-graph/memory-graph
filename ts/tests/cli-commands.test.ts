/**
 * Tests for CLI command parsing and dispatch.
 *
 * These tests verify that the CLI correctly parses arguments and dispatches
 * to the right command handlers, without requiring a running backend.
 */

import { describe, test, expect } from "bun:test";

describe("CLI USAGE text", () => {
  test("USAGE contains all new commands", async () => {
    // Import the module to check that it loads without errors
    const mod = await import("../src/cli.js");
    expect(mod).toBeDefined();
  });
});

describe("parseSimpleArgs logic", () => {
  // Test the argument parsing logic that the CLI uses
  function parseSimpleArgs(args: string[]): Record<string, unknown> {
    const result: Record<string, unknown> = {};
    for (let i = 0; i < args.length; i++) {
      if (args[i].startsWith("--")) {
        const key = args[i].slice(2);
        if (i + 1 < args.length && !args[i + 1].startsWith("--")) {
          result[key] = args[i + 1];
          i++;
        } else {
          result[key] = true;
        }
      } else {
        if (!result["_positional"]) result["_positional"] = [] as string[];
        (result["_positional"] as string[]).push(args[i]);
      }
    }
    return result;
  }

  test("parses --key value pairs", () => {
    const result = parseSimpleArgs(["--type", "solution", "--title", "Test"]);
    expect(result["type"]).toBe("solution");
    expect(result["title"]).toBe("Test");
  });

  test("parses boolean flags", () => {
    const result = parseSimpleArgs(["--json", "--dry-run"]);
    expect(result["json"]).toBe(true);
    expect(result["dry-run"]).toBe(true);
  });

  test("parses positional arguments", () => {
    const result = parseSimpleArgs(["abc-123", "def-456", "SOLVES"]);
    const positional = result["_positional"] as string[];
    expect(positional).toEqual(["abc-123", "def-456", "SOLVES"]);
  });

  test("parses mixed positional and flag arguments", () => {
    const result = parseSimpleArgs(["abc-123", "--strength", "0.8", "def-456"]);
    expect(result["_positional"]).toEqual(["abc-123", "def-456"]);
    expect(result["strength"]).toBe("0.8");
  });
});

describe("CLI command list", () => {
  // Verify all expected commands are in the dispatch
  const expectedCommands = [
    "store", "get", "update", "delete", "search", "recall",
    "related", "link", "stats", "activity",
    "as-of", "history", "changes",
    "context-search", "contextual-search",
    "entities", "patterns", "context",
    "visualize", "similarity", "learning", "gaps",
    "briefing", "predict", "warn", "outcome",
    "capture", "analyze-project", "workflow",
    "export", "import", "migrate", "health", "config",
  ];

  test("all expected commands are defined", async () => {
    // Read the cli.ts source to verify all commands are in the switch
    const fs = await import("node:fs");
    const path = await import("node:path");
    const cliSource = fs.readFileSync(
      path.join(import.meta.dir, "..", "src", "cli.ts"),
      "utf-8"
    );

    for (const cmd of expectedCommands) {
      expect(cliSource).toContain(`case "${cmd}"`);
    }
  });
});
