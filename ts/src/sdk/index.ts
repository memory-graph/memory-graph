/**
 * MemoryGraph SDK - TypeScript client library for the MemoryGraph Cloud API.
 *
 * Usage:
 *   import { MemoryGraphClient } from "./sdk/index.js";
 *
 *   const client = new MemoryGraphClient({ apiKey: "mgraph_..." });
 *   const memory = await client.createMemory({
 *     type: "solution",
 *     title: "Fixed timeout issue",
 *     content: "Used exponential backoff with retries",
 *     tags: ["redis", "timeout"],
 *   });
 *
 * The SDK is framework-agnostic and can be used with any JS/TS AI agent or
 * LLM framework (LangChain.js, Vercel AI SDK, custom agents, etc.).
 */

// Client
export { MemoryGraphClient } from "./client.js";
export type {
  MemoryGraphClientOptions,
  CreateMemoryParams,
  UpdateMemoryParams,
  SearchMemoriesParams,
  RecallMemoriesParams,
  CreateRelationshipParams,
  GetRelatedMemoriesParams,
} from "./client.js";

// Models
export {
  MemoryType,
  RelationshipType,
  type Memory,
  type MemoryCreate,
  type MemoryUpdate,
  type Relationship,
  type RelationshipCreate,
  type SearchResult,
  type RelatedMemory,
} from "./models.js";

// Exceptions
export {
  MemoryGraphError,
  AuthenticationError,
  RateLimitError,
  NotFoundError,
  ValidationError,
  ServerError,
} from "./exceptions.js";

export const SDK_VERSION = "0.1.0";
