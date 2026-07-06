/**
 * Custom error hierarchy for MemoryGraph.
 *
 * All memory-related errors inherit from MemoryError, allowing
 * for consistent error handling and categorization.
 */

export class MemoryError extends Error {
  details: Record<string, unknown>;

  constructor(message: string, details?: Record<string, unknown>) {
    super(message);
    this.name = "MemoryError";
    this.details = details ?? {};
  }

  toString(): string {
    if (Object.keys(this.details).length > 0) {
      return `${this.message} (Details: ${JSON.stringify(this.details)})`;
    }
    return this.message;
  }
}

export class MemoryNotFoundError extends MemoryError {
  memoryId: string;

  constructor(memoryId: string, details?: Record<string, unknown>) {
    super(`Memory not found: ${memoryId}`, details);
    this.name = "MemoryNotFoundError";
    this.memoryId = memoryId;
  }
}

export class RelationshipError extends MemoryError {
  constructor(message: string, details?: Record<string, unknown>) {
    super(message, details);
    this.name = "RelationshipError";
  }
}

export class ValidationError extends MemoryError {
  constructor(message: string, details?: Record<string, unknown>) {
    super(message, details);
    this.name = "ValidationError";
  }
}

export class DatabaseConnectionError extends MemoryError {
  constructor(message: string, details?: Record<string, unknown>) {
    super(message, details);
    this.name = "DatabaseConnectionError";
  }
}

export class SchemaError extends MemoryError {
  constructor(message: string, details?: Record<string, unknown>) {
    super(message, details);
    this.name = "SchemaError";
  }
}

export class NotFoundError extends MemoryError {
  constructor(message: string, details?: Record<string, unknown>) {
    super(message, details);
    this.name = "NotFoundError";
  }
}

export class BackendError extends MemoryError {
  constructor(message: string, details?: Record<string, unknown>) {
    super(message, details);
    this.name = "BackendError";
  }
}

export class ConfigurationError extends MemoryError {
  constructor(message: string, details?: Record<string, unknown>) {
    super(message, details);
    this.name = "ConfigurationError";
  }
}
