/**
 * Exceptions for the MemoryGraph SDK.
 *
 * Mirrors the Python SDK exception hierarchy. Each error optionally carries
 * the HTTP status code that triggered it.
 */

export class MemoryGraphError extends Error {
  statusCode?: number;

  constructor(message: string, statusCode?: number) {
    super(message);
    this.name = "MemoryGraphError";
    if (statusCode !== undefined) {
      this.statusCode = statusCode;
    }
  }
}

export class AuthenticationError extends MemoryGraphError {
  constructor(message = "Invalid or missing API key") {
    super(message, 401);
    this.name = "AuthenticationError";
  }
}

export class RateLimitError extends MemoryGraphError {
  constructor(message = "Rate limit exceeded") {
    super(message, 429);
    this.name = "RateLimitError";
  }
}

export class NotFoundError extends MemoryGraphError {
  constructor(message = "Resource not found") {
    super(message, 404);
    this.name = "NotFoundError";
  }
}

export class ValidationError extends MemoryGraphError {
  constructor(message = "Validation error") {
    super(message, 400);
    this.name = "ValidationError";
  }
}

export class ServerError extends MemoryGraphError {
  constructor(message = "Server error") {
    super(message, 500);
    this.name = "ServerError";
  }
}
