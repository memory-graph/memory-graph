/**
 * REGRESSION: the session briefing must surface memories that belong to the
 * detected project even when those memories are not tagged with a
 * `context_project_path` property.
 *
 * Observed on the `armate` project after 0.14.0: `briefing` reported
 * "Total memories: 0" while `health`/`stats` showed 73 memories. The briefing
 * queries filtered exclusively on `m.context_project_path`, but nothing in
 * the write flows sets that property — project membership is encoded as the
 * project-name tag and sometimes as a `PART_OF` relationship to a
 * `Project: <name>` node. So no memory ever matched.
 *
 * These tests pin:
 *  1. A memory tagged with the project name counts toward the briefing
 *     (tag-based membership).
 *  2. A memory carrying `context.project_path` counts toward the briefing
 *     (path-based membership, preserved for stores that do set it).
 *  3. `detectProject` reuses an existing `Project: <name>` node instead of
 *     creating a fresh duplicate every call.
 */

import { describe, test, expect, beforeAll, afterAll } from "bun:test";
import { mkdtempSync, rmSync, mkdirSync } from "node:fs";
import { join } from "node:path";
import { tmpdir } from "node:os";

import { FalkorDBLiteBackend } from "../src/backends/falkordblite.js";
import { generateSessionBriefing } from "../src/proactive/session-briefing.js";
import { detectProject } from "../src/integration/project-analysis.js";
import { createMemory, MemoryType } from "../src/models.js";

const STASH_FALKORDBLITE_PATH = process.env.MEMORY_FALKORDBLITE_PATH;

let dir: string;
let backend: FalkorDBLiteBackend;

function freshTempDir(): string {
  return mkdtempSync(join(tmpdir(), `mg-brief-${Date.now()}-${Math.random().toString(36).slice(2, 8)}-`));
}

async function store(type: string, title: string, content: string, tags: string[], projectPath?: string): Promise<void> {
  await backend.storeMemory(
    createMemory({
      type,
      title,
      content,
      tags,
      context: projectPath ? { project_path: projectPath } : undefined,
    })
  );
}

beforeAll(async () => {
  dir = freshTempDir();
  // A real project directory for detectProject.
  process.env.MEMORY_FALKORDBLITE_PATH = join(dir, "falkordblite.db");
  const projDir = join(dir, "armate");
  mkdirSync(projDir, { recursive: true });
  backend = new FalkorDBLiteBackend();
  await backend.connect();
  await backend.initializeSchema();
});

afterAll(async () => {
  try {
    await backend.disconnect();
  } catch {
    // best-effort
  }
  delete process.env.MEMORY_FALKORDBLITE_PATH;
  if (STASH_FALKORDBLITE_PATH) process.env.MEMORY_FALKORDBLITE_PATH = STASH_FALKORDBLITE_PATH;
  try {
    rmSync(dir, { recursive: true, force: true });
  } catch {
    // ignore
  }
});

describe("session briefing is scoped to project memories correctly", () => {
  test("memories tagged with the project name are counted and listed", async () => {
    await store(MemoryType.SOLUTION, "Seam refactor", "Refactored armate seam.", ["armate", "refactor"]);
    await store(MemoryType.PROBLEM, "Bug in parser", "Parser throws on unicode.", ["armate", "bug"]);

    const project = await detectProject(backend, join(dir, "armate"));
    expect(project).not.toBeNull();
    const briefing = await generateSessionBriefing(backend, join(dir, "armate"));
    expect(briefing).not.toBeNull();
    expect(briefing!.total_memories).toBeGreaterThanOrEqual(2);

    const titles = briefing!.recent_activities.map((a) => a.title);
    expect(titles).toContain("Seam refactor");
    expect(titles).toContain("Bug in parser");
  });

  test("memories with context.project_path are counted even without the tag", async () => {
    await store(MemoryType.SOLUTION, "Path-tagged memory", "Only path scoped.", [], join(dir, "armate"));

    const briefing = await generateSessionBriefing(backend, join(dir, "armate"));
    expect(briefing).not.toBeNull();
    expect(briefing!.total_memories).toBeGreaterThanOrEqual(1);

    const titles = briefing!.recent_activities.map((a) => a.title);
    expect(titles).toContain("Path-tagged memory");
  });

  test("detectProject reuses an existing Project node instead of duplicating", async () => {
    const first = await detectProject(backend, join(dir, "armate"));
    const firstId = first!.project_id;
    const second = await detectProject(backend, join(dir, "armate"));
    expect(second!.project_id).toBe(firstId);
  });
});