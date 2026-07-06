# Security & Edge-Case Review: MemoryGraph TypeScript CLI

**Scope:** `ts/src/` - injection risks, data handling, edge cases causing crashes or data loss.
**Date:** 2026-07-05

---

## Findings (sorted by severity)

### 1. Critical — Command Injection via `--path` argument

| Field | Value |
|-------|-------|
| **Category** | Injection |
| **File** | `ts/src/integration/project-analysis.ts:186-189, 360-365, 389-391` |
| **Severity** | Critical |

**Issue:** `safeExecSync` interpolates the user-supplied directory path into a shell
command string using double-quote interpolation. A path containing `"` breaks out of
the shell quoting and allows arbitrary command execution.

**Evidence:**
```ts
// project-analysis.ts:186
const remoteResult = safeExecSync(
  `git -C "${dir}" config --get remote.origin.url`,
  { cwd: dir, timeout: 5000 }
);

// :360
const statusOutput = safeExecSync(`git -C "${dir}" status --porcelain`, {
  cwd: dir, timeout: 10000,
});

// :389
const diffOutput = safeExecSync(
  `git -C "${dir}" diff --numstat HEAD -- "${filePath}"`,
  { cwd: dir, timeout: 5000 }
);
```

`dir` flows from `cmdAnalyzeProject` → `parsed["path"]` (CLI arg). The same pattern
exists in `ts/src/utils/project-detection.ts:33-40` which calls
`execSync("git rev-parse --is-inside-work-tree", { cwd })` — that variant is safe
because `cwd` is passed as an option and not interpolated into the command string,
but the `git -C "${dir}"` form here is not.

**Impact:** A user (or an AI agent invoking `memorygraph analyze-project --path …`
with an attacker-controlled path) can execute arbitrary shell commands. Example:
`memorygraph analyze-project --path 'foo"; rm -rf $HOME; echo "'` produces
`git -C "foo"; rm -rf $HOME; echo "" config --get remote.origin.url`.

**Fix:** Stop interpolating `dir` into the command string. Pass the directory via
the `cwd` option (which `safeExecSync` already does) and drop the `git -C "${dir}"`
prefix. For the `diff` command that also interpolates `filePath`, use `execFileSync`
or `spawnSync` with an argument array instead of a shell string:
```ts
import { spawnSync } from "node:child_process";
const result = spawnSync("git", ["-C", dir, "diff", "--numstat", "HEAD", "--", filePath],
  { stdio: "pipe", timeout: 5000 });
```

---

### 2. High — Path Traversal in Markdown export via memory IDs

| Field | Value |
|-------|-------|
| **Category** | Path Traversal |
| **File** | `ts/src/utils/export-import.ts:165-166` |
| **Severity** | High |

**Issue:** `exportToMarkdown` sanitises the memory *title* before using it in a
filename, but does **not** sanitise `memory.id`, which is interpolated directly into
the output filename. Memory IDs originating from an imported JSON file can contain
`../../` sequences that escape the output directory.

**Evidence:**
```ts
// export-import.ts:165
const safeTitle = memory.title.replace(/[^a-zA-Z0-9 _-]/g, "_").replace(/ /g, "_");
const filename = `${safeTitle}_${memory.id?.slice(0, 8)}.md`;
// ...
await writeFile(join(outputDir, filename), lines.join("\n"));
```

A memory imported from a malicious JSON with `"id": "../../etc/cron.d/evil"` produces
filename `safeTitle_../../c.md`; `join(outputDir, …)` resolves outside `outputDir`.

**Impact:** Arbitrary file write outside the intended export directory. Combined with
`importFromJson` (which accepts any string as an id), an attacker who supplies a
crafted JSON file can overwrite files in arbitrary locations when the victim later
runs `memorygraph export --format markdown --output <dir>`.

**Fix:** Apply the same sanitisation to `memory.id` (or use only `slice(0,8)` after
replacing non-alphanumerics):
```ts
const safeId = (memory.id ?? "unknown").replace(/[^a-zA-Z0-9_-]/g, "_").slice(0, 12);
const filename = `${safeTitle}_${safeId}.md`;
```

---

### 3. Medium — Crash on malicious import JSON (non-array `memories`/`relationships`)

| Field | Value |
|-------|-------|
| **Category** | Validation / DoS |
| **File** | `ts/src/utils/export-import.ts:53-67` |
| **Severity** | Medium |

**Issue:** `importFromJson` checks that `data["memories"]` and
`data["relationships"]` are truthy, but does not validate that they are arrays (or
that `data` is an object). A JSON file containing `{"memories":"abc",
"relationships":"def"}` passes the truthy check, then crashes with `TypeError:
Cannot use 'in' operator to search for 'id' in a` when iterating characters of the
string. `data === null` (`null` is a valid JSON document) crashes with `TypeError:
Cannot read properties of null`.

**Evidence:**
```ts
const data = await file.json();
if (!data["memories"] || !data["relationships"]) {  // null/[] both crash or pass
  throw new Error("Invalid export format: ...");
}
const memories = data["memories"] as Record<string, unknown>[];
const relationships = data["relationships"] as Record<string, unknown>[];
for (const memData of memories) {           // iterates chars if string
  for (const field of ["id","type","title","content"]) {
    if (!(field in memData))                // TypeError on primitive
```

**Impact:** Unhandled crash (DoS) when importing a crafted JSON file. The same
pattern exists in `ts/src/migration/manager.ts:175` (`validateExport`) where
`JSON.parse(readFileSync(...))` can also yield `null`.

**Fix:**
```ts
if (data === null || typeof data !== "object" || Array.isArray(data)) {
  throw new Error("Invalid export format: expected a JSON object");
}
if (!Array.isArray(data["memories"]) || !Array.isArray(data["relationships"])) {
  throw new Error("Invalid export format: 'memories' and 'relationships' must be arrays");
}
```

---

### 4. Medium — Secret exposure in `config` command (URIs with embedded credentials)

| Field | Value |
|-------|-------|
| **Category** | Info Leak |
| **File** | `ts/src/config.ts:218-225`, `ts/src/cli.ts:108-119` |
| **Severity** | Medium |

**Issue:** `Config.getConfigSummary()` returns `NEO4J_URI`, `MEMGRAPH_URI`, and
`FALKORDB_HOST` verbatim. If a user configures a connection string with embedded
credentials (e.g. `MEMORY_MEMGRAPH_URI=bolt://neo4j:secretpass@host:7687`), the
password is printed to stderr by `printConfigSummary()`.

**Evidence:**
```ts
// config.ts:219
neo4j: {
  uri: Config.NEO4J_URI,         // may contain bolt://user:pass@host
  user: Config.NEO4J_USER,
  password_configured: !!Config.NEO4J_PASSWORD,
  database: Config.NEO4J_DATABASE,
},
memgraph: {
  uri: Config.MEMGRAPH_URI,      // may contain bolt://user:pass@host
  ...
},
```

`cli.ts:113` prints `Cloud API URL: ${config.cloud.api_url}` — generally safe, but
the Neo4j/Memgraph URIs are not sanitised.

**Impact:** Credentials leak in terminal output, CI logs, or screen recordings.
The Bolt backend's `createDriver` (`bolt-shared.ts:120`) also embeds `this.uri` in
a thrown error message, compounding the leak when connection failures are logged.

**Fix:** Redact userinfo from URIs before printing:
```ts
function redactUri(uri: string): string {
  try { const u = new URL(uri); u.password = "***"; return u.toString(); }
  catch { return uri; }
}
```

---

### 5. Medium — Sensitive data in error messages (query params leaked)

| Field | Value |
|-------|-------|
| **Category** | Info Leak |
| **File** | `ts/src/backends/falkordb-shared.ts:105`, `ts/src/backends/bolt-shared.ts:139`, `ts/src/backends/sqlite.ts:81,153,233` |
| **Severity** | Medium |

**Issue:** Every backend's `executeQuery`/store catch block interpolates the raw
error into a new `DatabaseConnectionError` message and also `console.error`s it.
FalkorDB and Neo4j drivers frequently include the offending query text and bound
parameter values in their error strings, so memory content, tags, or relationship
context can appear in error output.

**Evidence:**
```ts
// falkordb-shared.ts:104
} catch (err) {
  console.error(`Query execution failed: ${err}`);
  throw new DatabaseConnectionError(`Query execution failed: ${err}`);
}
```

The CLI top-level handler (`cli.ts:415`) prints `Error: ${err.message}`, surfacing
the raw backend error to the user.

**Impact:** Memory contents (which may include sanitised-but-still-sensitive data,
user-provided text, or imported payloads) leak in error messages and logs.

**Fix:** Log the full error at debug level only; surface a generic message to the
caller. Keep the original error as `cause`:
```ts
throw new DatabaseConnectionError("Query execution failed", { cause: err });
```

---

### 6. Medium — DoS: unbounded BFS depth in SQLite `getRelatedMemories`

| Field | Value |
|-------|-------|
| **Category** | DoS |
| **File** | `ts/src/backends/sqlite.ts:264-303` |
| **Severity** | Medium |

**Issue:** The FalkorDB and Bolt backends clamp `maxDepth` to
`MAX_TRAVERSAL_DEPTH = 10` (`falkordb-shared.ts:293`, `bolt-shared.ts:298`). The
SQLite backend performs an iterative BFS but applies **no upper bound** on
`maxDepth`, which the CLI passes through unvalidated (`cli.ts:616`:
`max_depth: parseIntArg(parsed["max-depth"]) ?? 2`).

**Evidence:**
```ts
// sqlite.ts:265
const maxDepth = opts?.maxDepth ?? 2;   // no Math.min clamp
// ...
for (let depth = 0; depth < maxDepth; depth++) {
  // query every relationship of every node at currentLevel
```

**Impact:** `memorygraph related <id> --max-depth 999999` against the SQLite backend
performs up to 999999 rounds of BFS, each issuing one SQL query per node at the
current frontier — exponential DB load and potential memory exhaustion.

**Fix:** Clamp `maxDepth` in the SQLite backend the same way the Cypher backends do:
```ts
const maxDepth = Math.max(1, Math.min(Number(opts?.maxDepth ?? 2) || 2, 10));
```

---

### 7. Medium — SearchQuery schema bypass (unbounded `limit`)

| Field | Value |
|-------|-------|
| **Category** | Validation / DoS |
| **File** | `ts/src/tools/search.ts:18-37`, `ts/src/tools/relationship.ts:38` |
| **Severity** | Medium |

**Issue:** `SearchQuerySchema` constrains `limit` to `z.number().int().min(1).max(1000)`,
but the tool handlers construct the `SearchQuery` object **without** parsing it
through the Zod schema. `parseIntArg` returns any integer, so `--limit 999999999`
reaches the backend unmodified.

**Evidence:**
```ts
// tools/search.ts:30
limit: (args["limit"] as number) ?? 50,   // no schema parse
```
The CLI passes `limit: parseIntArg(parsed["limit"]) ?? 50` — `parseIntArg` does no
upper-bound check. The Cypher backends forward `limit` as a `$limit` parameter and
the SQLite backend interpolates it as `LIMIT ?`; both will honour arbitrarily large
values.

**Impact:** A user or agent can request unbounded result sets, exhausting memory and
DB time. `handleWhatChanged` (`tools/temporal.ts:158`) also hard-codes `limit: 1000`
with `offset: 0` and then iterates every memory calling `getRelatedMemories` —
quadratic blowup on large graphs.

**Fix:** Either parse through `SearchQuerySchema.parse(...)` in the tool handlers, or
clamp explicitly:
```ts
limit: Math.min(Math.max(parseIntArg(parsed["limit"]) ?? 50, 1), 1000),
```

---

### 8. Low — URL path injection in cloud backend

| Field | Value |
|-------|-------|
| **Category** | Injection / SSRF |
| **File** | `ts/src/backends/cloud.ts:283, 297, 339, 356` |
| **Severity** | Low |

**Issue:** `memoryId` is interpolated directly into the HTTP request path without
URL-encoding. A memory ID containing `..`, `?`, `#`, or `/` alters the request
target.

**Evidence:**
```ts
// cloud.ts:283
const result = await this.request("GET", `/memories/${memoryId}`);
// :297
const result = await this.request("PUT", `/memories/${memory.id}`, updates);
// :339 (related)
const result = await this.request("GET", `/search/memories/${memoryId}/related`, ...);
```

**Impact:** Bounded — the cloud API enforces auth with the caller's own API key, so
path traversal at most redirects to another endpoint the same key would authorise.
Still, malformed IDs produce confusing 404s or cross-endpoint requests, and the
pattern is a latent SSRF if the API ever trusts path segments for tenant routing.

**Fix:** Encode path segments:
```ts
const result = await this.request("GET", `/memories/${encodeURIComponent(memoryId)}`);
```

---

### 9. Low — Weak sensitive-data filter in context capture

| Field | Value |
|-------|-------|
| **Category** | Validation |
| **File** | `ts/src/integration/context-capture.ts:42-56` |
| **Severity** | Low |

**Issue:** `sanitizeContent` relies on a small set of regexes. It misses:
- multi-word leaks (`"the password is hunter2"`)
- secrets whose key lacks the `api[_-]?key|token|…` prefix
- emails on TLDs other than `.com/.net/.org/.io/.dev` (e.g. `.co`, `.ai`, `.app`)
- base64/hex blobs, `AKIA…` AWS keys without the `aws_access_key` label
- `ssh-ed25519 …` public keys (only RSA/EC private keys are matched)

**Evidence:**
```ts
const SENSITIVE_PATTERNS: RegExp[] = [
  /(?:api[_-]?key|token|password|secret|auth)[=:\s]+['"]?[\w\-.]+['"]?/gi,
  // ...
  /\b[\w.-]+@[\w.-]+\.(?:com|net|org|io|dev)\b/,
];
```

**Impact:** Best-effort filter provides false sense of security; sensitive strings
can still be stored in the graph. Mitigation is documented as best-effort, hence Low.

**Fix:** Expand patterns (add `AKIA[0-9A-Z]{16}`, `gh[ps]_[A-Za-z0-9]{36}`, longer
TLD list, `ssh-ed25519`/`ssh-rsa` lines) and consider warning rather than silently
relying on regex. Document the limitation in the module header.

---

### 10. Low — LIKE wildcard injection in SQLite tag/project search

| Field | Value |
|-------|-------|
| **Category** | Validation |
| **File** | `ts/src/backends/sqlite.ts:165-175` |
| **Severity** | Low |

**Issue:** Tag and `project_path` values are interpolated into LIKE pattern strings
(`%"${tag}"%`, `%"project_path":"${project_path}"%`). The values are passed as
**bind parameters**, so this is not SQL injection — but LIKE wildcards `%` and `_`
inside the user input are not escaped, and `"` inside the input breaks the JSON
substring match.

**Evidence:**
```ts
for (const tag of searchQuery.tags) {
  params.push(`%"${tag}"%`);              // % and _ in tag are wildcards
}
// ...
params.push(`%"project_path":"${searchQuery.project_path}"%`);
```

**Impact:** Correctness bug: a tag like `100%` matches any tag containing `100`
followed by anything; a project path containing `"` never matches. No data leak, no
injection — just unexpected search results.

**Fix:** Escape LIKE wildcards and double-quotes:
```ts
const escapeLike = (s: string) => s.replace(/[%_"\\]/g, (c) => `\\${c}`);
params.push(`%"${escapeLike(tag)}"%`);
```
and add `ESCAPE '\\'` to the `LIKE` clause.

---

### 11. Low — Relationship type not validated by SQLite backend

| Field | Value |
|-------|-------|
| **Category** | Validation |
| **File** | `ts/src/backends/sqlite.ts:248` (createRelationship), `ts/src/utils/export-import.ts:120` |
| **Severity** | Low |

**Issue:** FalkorDB and Bolt backends call `validateRelType` (alphanumeric +
underscore only) before storing a relationship. The SQLite backend accepts any
string. `importFromJson` passes `relData["type"]` straight through, so a malicious
JSON file can populate the SQLite DB with arbitrary `rel_type` values. The tool
handler `handleCreateRelationship` (`tools/relationship.ts:18`) does check
`isRelationshipType`, but only when invoked through the CLI `link` command — the
import path bypasses it.

**Evidence:**
```ts
// sqlite.ts:248 — no validateRelType call
.run(relationshipId, fromMemoryId, toMemoryId, relationshipType, ...)

// export-import.ts:120 — no isRelationshipType check
await db.createRelationship(
  relData["from_memory_id"] as string,
  relData["to_memory_id"] as string,
  relData["type"] as string,   // arbitrary
  ...
);
```

**Impact:** Not an injection (SQLite uses `?` placeholders for `rel_type`). The
risk is data-integrity drift: a migrated SQLite DB may hold rel types that the
Cypher backends would reject, breaking later migrations to FalkorDB.

**Fix:** Call `validateRelType(relationshipType)` at the top of
`SQLiteBackend.createRelationship`, and/or validate inside `importFromJson` before
calling `db.createRelationship`.

---

### 12. Low — Floating promise at CLI entry point

| Field | Value |
|-------|-------|
| **Category** | Other |
| **File** | `ts/src/cli.ts:1397` |
| **Severity** | Low |

**Issue:** `if (import.meta.main) { main(); }` fires `main()` without `await` or
`.catch`. `main()` itself wraps command dispatch in `try/catch`, but if `createDb()`
rejects inside a command function **before** the inner `try` block opens, the
rejection propagates to `main()`'s `catch` — which is fine. However, any rejection
that escapes `main()` (e.g. from a `finally` block after an `ExitError` rethrow
path) becomes an unhandled promise rejection rather than a clean exit.

**Evidence:**
```ts
if (import.meta.main) {
  main();   // floating promise
}
```

**Impact:** Rare, but on certain error paths the CLI may print an unhandled
rejection warning instead of exiting cleanly with a status code.

**Fix:**
```ts
if (import.meta.main) {
  main().catch((err) => {
    console.error(`Fatal: ${err instanceof Error ? err.message : String(err)}`);
    process.exit(1);
  });
}
```

---

## Summary

| # | Severity | Category | File | One-liner |
|---|----------|----------|------|-----------|
| 1 | Critical | Injection | project-analysis.ts | `git -C "${dir}"` shell injection via `--path` |
| 2 | High | Path Traversal | export-import.ts | `memory.id` unsanitised in export filename |
| 3 | Medium | Validation/DoS | export-import.ts | Non-array `memories`/`relationships` crashes import |
| 4 | Medium | Info Leak | config.ts / cli.ts | URIs with embedded passwords printed by `config` |
| 5 | Medium | Info Leak | falkordb-shared / bolt-shared / sqlite | Raw errors leak query params |
| 6 | Medium | DoS | sqlite.ts | No `maxDepth` cap in BFS |
| 7 | Medium | Validation/DoS | tools/search.ts | `limit` bypasses `SearchQuerySchema.max(1000)` |
| 8 | Low | Injection/SSRF | cloud.ts | `memoryId` not URL-encoded in path |
| 9 | Low | Validation | context-capture.ts | Weak sensitive-data regex filter |
| 10 | Low | Validation | sqlite.ts | LIKE wildcards in tags/project_path not escaped |
| 11 | Low | Validation | sqlite.ts / export-import.ts | `rel_type` not validated on import/SQLite |
| 12 | Low | Other | cli.ts | Floating promise at entry point |

**Things that are correctly handled (no finding):**
- Cypher queries in `falkordb-shared.ts` and `bolt-shared.ts` use `$parameter`
  binding for all user content (title, content, tags, search query, IDs). Only
  relationship *types* are interpolated, and those are guarded by `validateRelType`.
- SQL queries in `sqlite.ts` use `?` placeholders for all user values — no SQL
  injection.
- `exportToMarkdown` YAML frontmatter is double-quoted with `\\` and `"` escaping,
  preventing frontmatter injection.
- `Config.getConfigSummary` exposes secrets only as `*_configured: boolean` flags
  (except for the URI leak in finding #4).
- `detectFromGit` in `project-detection.ts` strips embedded credentials from git
  remote URLs before storing them.
- `CircuitBreaker` in `cloud.ts` serialises state mutations through a promise lock.
- The cloud backend sets an `AbortController` timeout on every request.
- FalkorDB/Bolt `getRelatedMemories` clamps `maxDepth` to `MAX_TRAVERSAL_DEPTH = 10`.
