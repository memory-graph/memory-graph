/**
 * MemoryGraph - Graph-based memory CLI for AI coding agents.
 *
 * TypeScript/Bun port of the Python memorygraph MCP server.
 * Changed from MCP server to CLI interface.
 * Local storage via FalkorDBLite or SQLite, cloud sync via MemoryGraph Cloud API.
 */

export const VERSION = "0.12.4";

// Models
export {
  MemoryType,
  RelationshipType,
  isMemoryType,
  isRelationshipType,
  ALL_MEMORY_TYPES,
  ALL_RELATIONSHIP_TYPES,
  MemorySchema,
  MemoryContextSchema,
  RelationshipSchema,
  RelationshipPropertiesSchema,
  SearchQuerySchema,
  PaginatedResultSchema,
  MemoryGraphSchema,
  AnalysisResultSchema,
  memoryToNodeProperties,
  createMemory,
  createRelationshipProperties,
  parseDate,
  type Memory,
  type MemoryContext,
  type Relationship,
  type RelationshipProperties,
  type SearchQuery,
  type PaginatedResult,
  type MemoryGraph,
  type AnalysisResult,
  type MemoryNode,
} from "./models.js";

// Errors
export {
  MemoryError,
  MemoryNotFoundError,
  RelationshipError,
  ValidationError,
  DatabaseConnectionError,
  SchemaError,
  NotFoundError,
  BackendError,
  ConfigurationError,
} from "./errors.js";

// Config
export { Config, TOOL_PROFILES, type BackendType, ALL_BACKEND_TYPES } from "./config.js";

// Backends
export {
  type GraphBackend,
  type HealthCheckResult,
  BaseFalkorDBBackend,
  FalkorDBLiteBackend,
  FalkorDBBackend,
  BaseBoltBackend,
  MemgraphBackend,
  CloudRESTAdapter,
  CloudBackend,
  CircuitBreaker,
  SQLiteBackend,
} from "./backends/index.js";

export { BackendFactory } from "./backends/factory.js";

// Database
export { MemoryDatabase, CloudMemoryDatabase, type IMemoryDatabase } from "./database.js";

// Tools
export {
  handleStoreMemory,
  handleGetMemory,
  handleUpdateMemory,
  handleDeleteMemory,
  handleSearchMemories,
  handleRecallMemories,
  handleContextualSearch,
  handleCreateRelationship,
  handleGetRelatedMemories,
  handleGetMemoryStatistics,
  handleGetRecentActivity,
  handleQueryAsOf,
  handleGetRelationshipHistory,
  handleWhatChanged,
} from "./tools/index.js";

// Utils
export {
  utcNow,
  parseDatetime,
  ensureAware,
  parseMemoryFromProperties,
  validateMemoryInput,
  validateSearchInput,
  validateRelationshipInput,
  detectProjectContext,
  extractContextStructure,
  parseContext,
  hasCycle,
  exportToJson,
  importFromJson,
  exportToMarkdown,
} from "./utils/index.js";

// Migration
export {
  type BackendConfig,
  type MigrationOptions,
  type MigrationResult,
  MigrationManager,
  MigrationError,
  backendConfigFromEnv,
  createMigrationOptions,
} from "./migration/index.js";

// Intelligence
export * as intelligence from "./intelligence/index.js";

// Analytics
export * as analytics from "./analytics/index.js";

// Proactive
export * as proactive from "./proactive/index.js";

// Integration
export * as integration from "./integration/index.js";

// SDK
export * as sdk from "./sdk/index.js";

// CLI entry point - call main() when run directly
import { main } from "./cli.js";
main();
