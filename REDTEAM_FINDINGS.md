# Red-Team Code Review Findings — MemoryGraph TypeScript

Adversarial review of `/Users/gregorydickson/memory-graph/ts/src/`.
Findings are sorted by severity. Only real, actionable issues are listed.

---

## CRITICAL

### C1. `searchMemories` ignores `offset` in all local backends → pagination infinite-loops / data loss
- **File**: `backends/falkordb-shared.ts:182-198`, `backends/bolt-shared.ts:225-241`, `backends/sqlite.ts:206-241`
- **Issue**: `searchMemories` applies `LIMIT $limit` but never adds `SKIP $offset`. `searchQuery.offset` is read into the query object but discarded.
- **Evidence** (falkordb-shared.ts):
  ```cypher
  MATCH (m:Memory)
  WHERE ${whereClause}
  RETURN m
  ORDER BY m.importance DESC, m.created_at DESC
  LIMIT $limit
  ```
  No `SKIP $offset` anywhere. Same in bolt-shared.ts and sqlite.ts (`LIMIT ?` only).
- **Impact**: `paginateMemories` (`utils/pagination.ts`) increments `offset` each batch but the backend returns the same first page forever. With `batchSize=1000` and `MemoryDatabase.searchMemoriesPaginated` capping `total_count` at 1000, exports/migrations silently truncate to the first 1000 memories. With a smaller batch size, `paginateMemories` yields duplicate batches until offset exceeds the (capped) total. This breaks `exportToJson`, `importFromJson` round-trips, migration verification, and `countMemories` for any DB with >1000 memories.
- **Fix**: Add `SKIP $offset` to the Cypher queries and bind `parameters["offset"] = searchQuery.offset`. For SQLite, append `OFFSET ?` and push `searchQuery.offset` to params.

### C2. `createRelationship` only matches `:Memory` nodes, so linking memories to `:Entity` nodes always fails silently
- **File**: `backends/falkordb-shared.ts:287-296`, `backends/bolt-shared.ts:330-339`, `integration/context-capture.ts:120-137`, `integration/workflow-tracking.ts:158-175`, `integration/project-analysis.ts:393-410`
- **Issue**: Integration modules create `:Entity` nodes (file/session entities) via `MERGE (f:Entity {...})` then call `backend.createRelationship(memoryId, entityId, ...)` to link them. But `createRelationship` hard-codes `MATCH (to:Memory {id: $to_id})` — entities are labeled `:Entity`, not `:Memory`, so the MATCH returns nothing and the relationship is never created. The thrown `RelationshipError` is swallowed by a `try/catch` that logs a warning.
- **Evidence**:
  ```ts
  // context-capture.ts
  await backend.executeQuery(`MERGE (f:Entity {name: $file_path, type: 'file'}) ...`, ...);
  await backend.createRelationship(memoryId, fileId, "INVOLVES", ...);  // fileId is an Entity id
  // falkordb-shared.ts createRelationship:
  MATCH (from:Memory {id: $from_id})
  MATCH (to:Memory {id: $to_id})   // <-- :Memory, but target is :Entity
  CREATE (from)-[r:...]->(to)
  ```
- **Impact**: All file-entity linking in `captureTaskContext`, `captureCommandExecution`, session linking in `trackWorkflow`, and file-change linking in `trackFileChanges` silently no-op. The graph never gets the entity relationships the intelligence/analytics modules query for (`MENTIONS`, `IN_SESSION`, `INVOLVES`, etc.), so `extractPatterns`, `predictNeeds`, `suggestPatterns`, `getSessionContext`, and others return empty results.
- **Fix**: Either add a separate `linkEntity` method on `GraphBackend` that matches `:Entity` nodes, or generalize `createRelationship` to accept a target label, or have integration modules create the relationship via `executeQuery` with the correct label.

### C3. Session briefing queries filter on `m.context` which is never stored as a single property
- **File**: `proactive/session-briefing.ts:191-322`
- **Issue**: Every query in `generateSessionBriefing` filters `WHERE m.context IS NOT NULL AND (m.context CONTAINS $project_path ...)`. But `memoryToNodeProperties` (`models.ts:226-252`) flattens context into `context_project_path`, `context_files_involved`, etc. — there is no `m.context` property on Memory nodes. So `m.context IS NOT NULL` is always false and every query returns zero rows.
- **Evidence**:
  ```cypher
  MATCH (m:Memory)
  WHERE m.context IS NOT NULL
    AND (m.context CONTAINS $project_path OR m.context CONTAINS $project_name)
  ```
  vs. storage in `models.ts`:
  ```ts
  const propKey = `context_${key}`;   // stores context_project_path, context_files_involved, ...
  props[propKey] = value;
  ```
- **Impact**: `memorygraph briefing` always reports 0 memories, 0 problems, 0 patterns, 0 warnings regardless of actual data. The feature is completely non-functional on Cypher backends. (On SQLite it would also fail because `executeQuery` throws.)
- **Fix**: Replace `m.context CONTAINS $project_path` with `m.context_project_path = $project_path` (or `CONTAINS`), and drop the `m.context IS NOT NULL` guard.

### C4. `cmdContextSearch` prints `[object Object]` instead of result text
- **File**: `cli.ts:660-666`
- **Issue**: `console.log(result)` prints the raw `{ isError, text }` object as `[object Object]`, unlike every other command which uses `console.log(result.text)`.
- **Evidence**:
  ```ts
  const result = await handleSearchRelationshipsByContext(db, toolArgs);
  console.log(result);            // <-- should be result.text
  if (result.isError) throw new ExitError(1);
  ```
- **Impact**: `memorygraph context-search` always outputs `[object Object]` to stdout; the user never sees the actual results. The command is unusable.
- **Fix**: `console.log(result.text);`

---

## HIGH

### H1. `extractKeywords` regex missing `g` flag → only extracts the first keyword
- **File**: `intelligence/context-retrieval.ts:297-300`, `intelligence/pattern-recognition.ts:295-298`
- **Issue**: `text.toLowerCase().match(/\b[a-z]{3,}\b/)` — without the `g` flag, `String.prototype.match` returns only the first match (or null). So `keywords` has at most one element.
- **Evidence**:
  ```ts
  private extractKeywords(text: string): string[] {
    const words = text.toLowerCase().match(/\b[a-z]{3,}\b/) ?? [];  // no /g
    const keywords = words.filter((w) => !STOP_WORDS.has(w));
    return Array.from(new Set(keywords));
  }
  ```
- **Impact**: `getContext` and `findSimilarProblems` only match on a single keyword, drastically reducing recall. Context retrieval and similar-problem search appear to work but miss most relevant memories.
- **Fix**: `match(/\b[a-z]{3,}\b/g)`.

### H2. `findSimilarProblems` does case-sensitive `CONTAINS` against original-case content
- **File**: `intelligence/pattern-recognition.ts:73-79`
- **Issue**: Keywords are lowercased (`extractKeywords` calls `.toLowerCase()`), but the Cypher `WHERE m.content CONTAINS keyword` is case-sensitive in FalkorDB/Memgraph. `context-retrieval.ts` correctly uses `toLower(m.content) CONTAINS keyword`; this module does not.
- **Evidence**:
  ```cypher
  WHERE any(keyword IN $keywords WHERE m.content CONTAINS keyword)
  ```
  `keywords` are lowercase; `m.content` is original case.
- **Impact**: Similar-problem matching fails for any content where the keyword appears with different capitalization (the common case).
- **Fix**: `toLower(m.content) CONTAINS keyword`.

### H3. Cloud backend method named `getStatistics` but interface requires `getMemoryStatistics` → stats always empty
- **File**: `backends/cloud.ts:493-495`, `database.ts:140-146`
- **Issue**: `CloudRESTAdapter` defines `async getStatistics()` but `GraphBackend` declares the optional method as `getMemoryStatistics?()`. `MemoryDatabase.getMemoryStatistics` / `CloudMemoryDatabase.getMemoryStatistics` check `if (this.backend.getMemoryStatistics)` — which is `undefined` on cloud, so they return `{}`.
- **Evidence**:
  ```ts
  // cloud.ts
  async getStatistics(): Promise<Record<string, unknown>> { ... }
  // database.ts
  async getMemoryStatistics(): Promise<Record<string, unknown>> {
    if (this.backend.getMemoryStatistics) { ... }   // undefined for cloud
    return {};
  }
  ```
- **Impact**: `memorygraph stats` with the cloud backend always prints an empty statistics block.
- **Fix**: Rename `getStatistics` to `getMemoryStatistics` in `cloud.ts`.

### H4. Session briefing unresolved-problems query has relationship direction backwards
- **File**: `proactive/session-briefing.ts:259-264`
- **Issue**: The query filters problems with `NOT EXISTS { MATCH (p)-[:SOLVES|ADDRESSES]->(:Memory) }`. But per the schema and `createRelationship`, `SOLVES` points from solution → problem, i.e. `(solution)-[:SOLVES]->(problem)`. So `(p)-[:SOLVES]->(:Memory)` checks whether the *problem* solves something, which is never true. Every problem is therefore reported as "unresolved". `analytics/advanced-queries.ts:525` correctly uses `<-[:SOLVES|ADDRESSES]-`.
- **Evidence**:
  ```cypher
  NOT EXISTS { MATCH (p)-[:SOLVES|ADDRESSES]->(:Memory) }   // wrong direction
  ```
- **Impact**: `briefing` lists all problems as unresolved even when solutions exist.
- **Fix**: `NOT EXISTS { MATCH (p)<-[:SOLVES|ADDRESSES]-(:Memory) }`.

### H5. Graph visualization query returns relationship objects but reads `from_id`/`to_id`/`type` that don't survive value conversion
- **File**: `analytics/advanced-queries.ts:128-152`, `backends/falkordb-shared.ts:103-111`, `backends/bolt-shared.ts:115-141`
- **Issue**: The visualization query does `collect(DISTINCT r) as relationships`. The result converters (`convertFalkorDBValue`, `convertValue`) strip relationship objects down to *only* their `properties` map — structural fields `type`, `startNodeElementId`/`endNodeElementId` are discarded. The code then reads `rel["type"]`, `rel["from_id"]`, `rel["to_id"]` which are all `undefined`.
- **Evidence**:
  ```ts
  // falkordb-shared.ts
  private convertFalkorDBValue(value: any): any {
    if (value && typeof value === "object" && "properties" in value) {
      return { ...value.properties };   // type / endpoints lost
    }
    return value;
  }
  // advanced-queries.ts
  visualization.edges.push({
    from: rel["from_id"] as string,   // undefined
    to: rel["to_id"] as string,       // undefined
    type: rel["type"] as string,      // undefined -> falls back to "RELATED_TO"
    ...
  });
  ```
- **Impact**: `memorygraph visualize` produces edges with `from: undefined, to: undefined`. The visualization is unusable for graph rendering.
- **Fix**: Rewrite the query to project endpoints explicitly, e.g. `RETURN startNode(r).id as from_id, endNode(r).id as to_id, type(r) as type, properties(r) as props`.

### H6. Cloud migration config uses wrong field names → cloud source/target migration always fails validation
- **File**: `migration/models.ts:12-43`, `migration/manager.ts:316-324`, `cli.ts:577-585`
- **Issue**: `backendConfigFromEnv()` returns `{ backend_type: "cloud", ... }` with NO `api_key` or `api_url` set for cloud. `validateBackendConfig` requires `config.api_key` and `config.api_url` for cloud. And `cli.ts cmdMigrate` puts the API key into `password` (not `api_key`), while `manager.createBackend` reads `config.api_key`/`config.api_url`.
- **Evidence**:
  ```ts
  // cli.ts
  const targetConfig: BackendConfig = {
    backend_type: targetBackend as any,
    password: targetBackend === "cloud" ? Config.MEMORYGRAPH_API_KEY : undefined,
    // api_key / api_url never set
  };
  // manager.ts
  return BackendFactory.createCloud(config.api_key, config.api_url);  // both undefined
  ```
- **Impact**: `memorygraph migrate --to cloud` (or `--from` cloud) fails validation or connects with no API key.
- **Fix**: In `backendConfigFromEnv`, set `api_key = Config.MEMORYGRAPH_API_KEY` and `api_url = Config.MEMORYGRAPH_API_URL` for cloud. In `cli.ts cmdMigrate`, set `api_key` (not `password`) and `api_url` for cloud targets.

### H7. Temporal intelligence relies on `is_current`/`superseded_by`/`PREVIOUS` infrastructure that backends never create
- **File**: `intelligence/temporal.ts:73-93, 113-134, 233-262`, `backends/falkordb-shared.ts:140-160`, `backends/bolt-shared.ts:182-202`
- **Issue**: `getMemoryHistory`, `getStateAt`, `trackEntityChanges`, and `createVersion` traverse `[:PREVIOUS]` chains and read `m.is_current` / `m.superseded_by`. But `storeMemory`/`updateMemory` never set these properties or create `PREVIOUS` relationships — `updateMemory` just does `SET m += $properties` in place. No `PREVIOUS` relationship is ever created anywhere in the codebase.
- **Evidence**: `intelligence/temporal.ts:73`:
  ```cypher
  MATCH path = (current:Memory {id: $memory_id})-[:PREVIOUS*0..]->(older:Memory)
  ```
  No backend method ever creates a `PREVIOUS` relationship or sets `is_current`.
- **Impact**: The entire temporal-intelligence module returns empty/incorrect results. `getMemoryHistory` returns only the current node (depth 0); `getStateAt` may return the wrong version; `trackEntityChanges` misses status transitions. The feature is non-functional.
- **Fix**: Either implement versioning in `updateMemory` (create new node + `PREVIOUS` rel, set `is_current`/`superseded_by`), or remove/disable the temporal-intelligence module until the infrastructure exists.

---

## MEDIUM

### M1. `recall` command is functionally identical to `search` — backend `recallMemories?` is never used
- **File**: `tools/search.ts:62-95`, `backends/sqlite.ts:419-440`, `backends/cloud.ts:298-315`
- **Issue**: `handleRecallMemories` builds a `SearchQuery` and calls `db.searchMemories` — the exact same path as `handleSearchMemories`. The `GraphBackend.recallMemories?` method (implemented by SQLite and Cloud with fuzzy/recall semantics) is never invoked. The CLI usage advertises recall as "fuzzy natural language search".
- **Evidence**:
  ```ts
  // handleRecallMemories — same as handleSearchMemories:
  const memories = await db.searchMemories(searchQuery);
  ```
  SQLite defines `recallMemories` and Cloud defines `recallMemories`, both unused.
- **Impact**: `recall` provides no fuzzy/semantic benefit over `search`; the feature is misleading.
- **Fix**: Have `handleRecallMemories` call `db.backend?.recallMemories?.(...)` when available, falling back to `searchMemories`.

### M2. `parseSimpleArgs` does not support `--key=value` syntax
- **File**: `cli.ts:384-399`
- **Issue**: Only `--key value` and `--key` (boolean) are handled. `--key=value` sets `key` to `true` and treats `=value` as a positional arg.
- **Evidence**: No `=` handling in the loop.
- **Impact**: Users who use the conventional `--query=foo` form get silently wrong parsing (query becomes `true`, `=foo` becomes positional).
- **Fix**: Split on `=`: `if (key.includes("=")) { result[key.split("=")[0]] = key.split("=").slice(1).join("="); }`.

### M3. `parseSimpleArgs` cannot pass values that start with `--`
- **File**: `cli.ts:388-389`
- **Issue**: `if (i + 1 < args.length && !args[i + 1].startsWith("--"))` — any value beginning with `--` is treated as a flag. So `--query --foo` or `--content --bar` misparse.
- **Impact**: Legitimate content/query strings starting with `--` are impossible to pass.
- **Fix**: Use `--` as an end-of-options sentinel, or accept `--key=--value`.

### M4. `cmdRecall`/`cmdContext`/`cmdPredict`/`cmdWarn` pass `true` as query when `--query` has no value
- **File**: `cli.ts:455, 678, 706, 740`
- **Issue**: `const query = parsed["query"] ?? ...`. If the user runs `memorygraph recall --query` (no value), `parsed["query"]` is `true`, which is truthy, so `if (!query)` passes and `true` is forwarded as the query string.
- **Evidence**:
  ```ts
  const query = parsed["query"] ?? (parsed["_positional"] as string[])?.join(" ");
  if (!query) { ... }   // true is truthy, passes
  ```
- **Impact**: A boolean `true` reaches the backend as the query, causing Cypher type errors or a search for the literal string "true".
- **Fix**: `if (!query || query === true) { ... }` or `if (typeof query !== "string")`.

### M5. Auto-select branch has dead condition `|| true`
- **File**: `backends/factory.ts:90`
- **Issue**: `if (Config.isEnvSet("FALKORDB_HOST") || true)` — the `|| true` makes the condition always true, so the env check is dead code.
- **Evidence**:
  ```ts
  if (Config.isEnvSet("FALKORDB_HOST") || true) {
  ```
- **Impact**: Misleading; suggests FALKORDB_HOST influences auto-selection when it never does.
- **Fix**: Remove `|| true` if the check is intended, or remove the whole `if` if FalkorDBLite should always be tried first.

### M6. `getRelatedMemories` query uses `WHERE related.id <> start.id` but `r[0]` may be from the wrong direction
- **File**: `backends/falkordb-shared.ts:316-328`, `backends/bolt-shared.ts:359-371`
- **Issue**: The traversal pattern `(start)-[r...*1..N]-(related)` is undirected, so `r[0]` (the first relationship on the path) could be either outgoing or incoming. The reconstructed `Relationship` always sets `from_memory_id: memoryId, to_memory_id: mem.id`, which may reverse the actual direction. The `type(rel)` and `properties(rel)` are correct, but `from`/`to` can be swapped.
- **Impact**: Relationship direction reported by `related`/`history` may be backwards for incoming relationships.
- **Fix**: Determine direction from `startNode(rel)` vs `endNode(rel)` and set `from`/`to` accordingly.

### M7. `linkEntities` and all intelligence/analytics modules call `executeQuery` which throws on SQLite/Cloud backends
- **File**: `intelligence/entity-extraction.ts:340-345`, `backends/sqlite.ts:118-124`, `backends/cloud.ts:243-249`, `cli.ts:625-636`
- **Issue**: `cmdEntities --link`, `cmdPatterns`, `cmdContext`, `cmdVisualize`, `cmdSimilarity`, `cmdLearning`, `cmdGaps`, `cmdBriefing`, `cmdPredict`, `cmdWarn`, `cmdOutcome` all do `(db as MemoryDatabase).backend` then call `executeQuery`. SQLite and Cloud backends throw `"does not support Cypher queries"` from `executeQuery`. The CLI casts `db as MemoryDatabase` which is unsafe for `CloudMemoryDatabase` (whose `backend` field exists but is a CloudRESTAdapter).
- **Evidence**:
  ```ts
  // cli.ts cmdEntities
  const backend = (db as MemoryDatabase).backend;
  await linkEntities(backend, ...);   // calls executeQuery → throws on sqlite/cloud
  ```
- **Impact**: All intelligence/analytics/proactive/integration commands fail with a runtime error on SQLite (the documented zero-config fallback) and Cloud backends. They only work on FalkorDB-family/Memgraph.
- **Fix**: Guard with `backend.isCypherCapable()` and return a clear "not supported on this backend" message, or implement the operations via the backend's CRUD methods.

### M8. SDK client and internal cloud adapter target different APIs
- **File**: `sdk/client.ts:62-66, 84, 116`, `backends/cloud.ts:80-82, 218-220`
- **Issue**: The SDK uses base URL `https://api.memorygraph.dev`, `Authorization: Bearer <key>`, and paths `/api/v1/memories`. The internal `CloudRESTAdapter` uses `https://graph-api.memorygraph.dev`, `X-API-Key: <key>`, and paths `/memories`. These are incompatible.
- **Impact**: The SDK cannot talk to the same backend the CLI uses; one of them is wrong.
- **Fix**: Align base URL, auth header, and path scheme between the SDK and the internal adapter.

### M9. CLI `VERSION` is stale (0.12.4 vs package.json 0.13.0)
- **File**: `cli.ts:60`, `ts/package.json:3`
- **Issue**: `const VERSION = "0.12.4";` but `package.json` is `0.13.0`.
- **Impact**: `memorygraph --version` and help text report the wrong version.
- **Fix`: Read version from `package.json` at build time, or update the constant.

### M10. Unused `parseArgs` import in cli.ts
- **File**: `cli.ts:11`
- **Issue**: `import { parseArgs } from "node:util";` — never used (the file uses its own `parseSimpleArgs`).
- **Impact**: Dead import; may cause lint failures.
- **Fix**: Remove the import.

### M11. `recordOutcome` generates a fractional ID `outcome_<seconds>.<ms>`
- **File**: `proactive/outcome-learning.ts:69`
- **Issue**: `const outcomeId = \`outcome_${Date.now() / 1000}\`;` produces e.g. `outcome_1751234567.891`. Not a clean identifier and could collide if two outcomes are recorded in the same millisecond.
- **Fix**: Use `randomUUID()` (already imported elsewhere in the codebase).

### M12. `handleWhatChanged` does N+1 `getRelatedMemories` calls over all memories — O(N) round trips
- **File**: `tools/temporal.ts:213-242`
- **Issue**: To find relationship changes since a timestamp, the handler fetches up to 1000 memories then calls `getRelatedMemories` for each one individually. With 1000 memories that's 1000 Cypher round trips.
- **Impact**: `memorygraph changes` is extremely slow on any non-trivial DB.
- **Fix**: Issue a single Cypher query filtering relationships by `recorded_at >= $since` or `valid_until >= $since`.

---

## LOW

### L1. `extractContextStructure` reassigns `text` parameter without type narrowing
- **File**: `utils/context-extractor.ts:17-18`
- **Issue**: `if (typeof text !== "string") text = String(text);` — but the param is typed `string | null | undefined`, and after the `if (!text) return {}` guard, `text` is already `string`. The reassignment is dead and the TS type remains `string | undefined`.
- **Fix**: Remove the redundant cast.

### L2. `calculateConfidence` checks `text.endsWith("()")` for FUNCTION entities, but the regex captures the name without parens
- **File**: `intelligence/entity-extraction.ts:289-291`
- **Issue**: FUNCTION patterns use `group: 1` capturing `[a-z_]\w*` (the name only, no `()`). So `entityText` never ends with `()`; the `0.9` confidence branch is dead.
- **Fix**: Adjust the confidence check or include the parens in the captured group.

### L3. SQLite `project_path` filter uses brittle JSON `LIKE` matching
- **File**: `backends/sqlite.ts:188-190`
- **Issue**: `context LIKE '%"project_path":"${project_path}"%'` assumes exact JSON key/value formatting with no spaces. `JSON.stringify` doesn't add spaces by default so this usually works, but a `project_path` containing `%` or `_` would be interpreted as LIKE wildcards, and any path containing `"` would break the match.
- **Fix**: Parse the JSON `context` column in a subquery or use `json_extract`.

### L4. `identifyCodePatterns`/`trackFileChanges` use relationship types (`PART_OF`, `MODIFIES`, `CREATES`, `FOUND_IN`, `INVOLVES`, `IN_SESSION`, `EXECUTED_IN`, `EXHIBITS`) not in `RelationshipType` enum
- **File**: `integration/project-analysis.ts:401, 415-422`, `integration/context-capture.ts:131, 144`, `integration/workflow-tracking.ts:160, 178`
- **Issue**: These types bypass `isRelationshipType` validation (integration modules call `backend.createRelationship` directly, not the tool handler). They're created in the graph but are invisible to the CLI `link` command which validates against the enum.
- **Fix**: Add these to `RelationshipType` or have integration modules use existing types.

### L5. `findAllCycles` throws "not yet implemented"
- **File**: `utils/graph-algorithms.ts:53-56`
- **Issue**: Stub that throws. The only caller is `hasCycle` which is not currently wired into relationship creation (`Config.ALLOW_RELATIONSHIP_CYCLES` is read but never checked against `hasCycle`).
- **Fix**: Either implement or remove and document that cycle prevention is unenforced.

### L6. `getProjectFromMemories` is a stub returning `null`
- **File**: `utils/project-detection.ts:51-55`
- **Issue**: `export async function getProjectFromMemories(...): Promise<string | null> { return null; }` — always returns null.
- **Fix**: Implement or remove.

---

## Stub / Placeholder Code (separate list)

| File | Symbol | Status |
|------|--------|--------|
| `backends/factory.ts:166-171` | `createNeo4j()` | Throws "not yet implemented" |
| `backends/factory.ts:181-186` | `createTurso()` | Throws "not yet implemented" |
| `backends/factory.ts:188-193` | `createLadybugDB()` | Throws "not yet implemented" |
| `utils/graph-algorithms.ts:53-56` | `findAllCycles()` | Throws "not yet implemented" |
| `utils/project-detection.ts:51-55` | `getProjectFromMemories()` | Returns `null` always |
| `intelligence/entity-extraction.ts:152-158` | `enableNlp` extraction | No-op stub (no JS spaCy equivalent) |
| `proactive/outcome-learning.ts:330-345` | `designDecayMechanism()` | Design doc only; decay not implemented |
| `intelligence/temporal.ts` (whole module) | `getMemoryHistory`/`getStateAt`/`createVersion`/`trackEntityChanges` | Built on `PREVIOUS`/`is_current`/`superseded_by` schema that backends never populate (see H7) |

---

## Test coverage assessment

- `tests/cli-commands.test.ts`: Vacuous. Tests a *local re-implementation* of `parseSimpleArgs` (not the exported one), and only asserts that `cli.ts` source contains `case "<cmd>"` strings. No command execution is tested. The `cmdContextSearch` bug (C4) is not caught.
- `tests/sqlite-backend.test.ts`: Reasonable CRUD coverage but does **not** test `offset`/pagination, so C1 is not caught.
- `tests/falkordb-backends.test.ts`: Only tests constructor/healthCheck without a server; no query logic exercised.
- `tests/migration.test.ts`, `tests/export-import.test.ts`: Exercise small datasets (< batchSize), so the pagination bug never manifests.
- No tests exist for `intelligence/`, `analytics/`, `proactive/`, `integration/` modules, so H1-H7 are undetected.
