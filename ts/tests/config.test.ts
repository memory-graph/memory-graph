/**
 * Tests for config module.
 */

import { describe, test, expect, beforeEach, afterEach } from "bun:test";
import { Config, TOOL_PROFILES, type BackendType } from "../src/config.js";

describe("Config", () => {
  const originalEnv = { ...process.env };

  afterEach(() => {
    // Restore env
    for (const key of Object.keys(process.env)) {
      if (!(key in originalEnv)) delete process.env[key];
    }
    Object.assign(process.env, originalEnv);
  });

  test("default backend is falkordblite", () => {
    delete process.env["MEMORY_BACKEND"];
    expect(Config.BACKEND).toBe("falkordblite");
  });

  test("backend can be overridden via env", () => {
    process.env["MEMORY_BACKEND"] = "sqlite";
    expect(Config.BACKEND).toBe("sqlite");
  });

  test("getBackendType returns valid BackendType", () => {
    process.env["MEMORY_BACKEND"] = "sqlite";
    expect(Config.getBackendType()).toBe("sqlite");
  });

  test("getBackendType returns auto for unknown", () => {
    process.env["MEMORY_BACKEND"] = "unknown";
    expect(Config.getBackendType()).toBe("auto");
  });

  test("TOOL_PROFILES has core and extended", () => {
    expect(TOOL_PROFILES["core"]).toBeDefined();
    expect(TOOL_PROFILES["extended"]).toBeDefined();
    expect(TOOL_PROFILES["core"].length).toBe(9);
    expect(TOOL_PROFILES["extended"].length).toBe(12);
  });

  test("getEnabledTools returns core tools by default", () => {
    delete process.env["MEMORY_TOOL_PROFILE"];
    const tools = Config.getEnabledTools()!;
    expect(tools).toContain("store_memory");
    expect(tools).toContain("recall_memories");
    expect(tools.length).toBe(9);
  });

  test("getEnabledTools returns extended tools", () => {
    process.env["MEMORY_TOOL_PROFILE"] = "extended";
    const tools = Config.getEnabledTools()!;
    expect(tools.length).toBe(12);
    expect(tools).toContain("get_memory_statistics");
  });

  test("legacy profile names are mapped", () => {
    process.env["MEMORY_TOOL_PROFILE"] = "full";
    const tools = Config.getEnabledTools()!;
    expect(tools.length).toBe(12);
  });

  test("isMultiTenantMode defaults to false", () => {
    delete process.env["MEMORY_MULTI_TENANT_MODE"];
    expect(Config.isMultiTenantMode()).toBe(false);
  });

  test("getConfigSummary returns expected structure", () => {
    const summary = Config.getConfigSummary();
    expect(summary).toHaveProperty("backend");
    expect(summary).toHaveProperty("sqlite");
    expect(summary).toHaveProperty("cloud");
    expect(summary).toHaveProperty("falkordblite");
  });
});
