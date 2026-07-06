/**
 * Tests for the entity extraction module.
 */

import { describe, test, expect } from "bun:test";
import { EntityExtractor, extractEntities, EntityType, isEntityType, ALL_ENTITY_TYPES } from "../src/intelligence/entity-extraction.js";

describe("EntityExtractor", () => {
  test("extracts file entities from text", () => {
    const text = "I modified src/backends/sqlite.ts and updated package.json";
    const entities = extractEntities(text);
    const fileEntities = entities.filter((e) => e.entity_type === EntityType.FILE);
    expect(fileEntities.length).toBeGreaterThan(0);
    expect(fileEntities.some((e) => e.text.includes("sqlite.ts"))).toBe(true);
    expect(fileEntities.some((e) => e.text.includes("package.json"))).toBe(true);
  });

  test("extracts function entities", () => {
    const text = "Call getMemory() to retrieve data, then use parseResult() to format it";
    const entities = extractEntities(text);
    const funcEntities = entities.filter((e) => e.entity_type === EntityType.FUNCTION);
    expect(funcEntities.length).toBeGreaterThan(0);
  });

  test("extracts class entities", () => {
    const text = "Create a new DatabaseService class extending BaseHandler";
    const entities = extractEntities(text);
    const classEntities = entities.filter((e) => e.entity_type === EntityType.CLASS);
    expect(classEntities.length).toBeGreaterThan(0);
    expect(classEntities.some((e) => e.text.includes("DatabaseService"))).toBe(true);
  });

  test("extracts technology entities", () => {
    const text = "We use Redis for caching and PostgreSQL for persistent storage";
    const entities = extractEntities(text);
    const techEntities = entities.filter((e) => e.entity_type === EntityType.TECHNOLOGY);
    expect(techEntities.length).toBeGreaterThan(0);
  });

  test("respects minimum confidence threshold", () => {
    const text = "Check the config.ts file";
    const highConfEntities = extractEntities(text, 1.0);
    const allEntities = extractEntities(text, 0.0);
    expect(allEntities.length).toBeGreaterThanOrEqual(highConfEntities.length);
  });

  test("deduplicates entities", () => {
    const text = "Check config.ts and then check config.ts again";
    const entities = extractEntities(text);
    const configEntities = entities.filter((e) => e.text === "config.ts");
    expect(configEntities.length).toBe(1);
  });

  test("returns empty array for empty text", () => {
    const entities = extractEntities("");
    expect(entities).toEqual([]);
  });

  test("EntityExtractor class works", () => {
    const extractor = new EntityExtractor();
    const entities = extractor.extract("Use src/index.ts to start the server");
    expect(entities.length).toBeGreaterThan(0);
  });

  test("EntityExtractor with NLP enabled warns but still works", () => {
    const extractor = new EntityExtractor(true);
    const entities = extractor.extract("Use src/index.ts to start the server");
    expect(entities.length).toBeGreaterThan(0);
  });
});

describe("EntityType", () => {
  test("isEntityType validates correctly", () => {
    expect(isEntityType("file")).toBe(true);
    expect(isEntityType("function")).toBe(true);
    expect(isEntityType("invalid_type")).toBe(false);
  });

  test("ALL_ENTITY_TYPES contains expected types", () => {
    expect(ALL_ENTITY_TYPES).toContain("file");
    expect(ALL_ENTITY_TYPES).toContain("function");
    expect(ALL_ENTITY_TYPES).toContain("class");
    expect(ALL_ENTITY_TYPES).toContain("technology");
    expect(ALL_ENTITY_TYPES.length).toBeGreaterThan(5);
  });
});
