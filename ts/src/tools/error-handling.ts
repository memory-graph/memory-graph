/**
 * Centralized error handling for CLI tool handlers.
 *
 * Wraps handler functions to catch known error types and return
 * user-friendly error strings.
 */

import {
  MemoryError,
  MemoryNotFoundError,
  RelationshipError,
  ValidationError,
} from "../errors.js";

export function handleToolErrors<T extends (...args: any[]) => Promise<any>>(
  operationName: string,
  fn: T
): (...args: Parameters<T>) => Promise<{ isError: boolean; text: string }> {
  return async (...args: Parameters<T>) => {
    try {
      const result = await fn(...args);
      // If the handler already returned a structured result, pass it through
      if (result && typeof result === "object" && "text" in result && "isError" in result) {
        return result;
      }
      return { isError: false, text: result };
    } catch (err) {
      if (err instanceof MemoryNotFoundError) {
        return { isError: true, text: String(err) };
      }
      if (err instanceof RelationshipError) {
        return { isError: true, text: `Relationship error: ${err}` };
      }
      if (err instanceof ValidationError) {
        return { isError: true, text: `Validation error: ${err}` };
      }
      if (err instanceof MemoryError) {
        return { isError: true, text: String(err) };
      }
      // Generic error
      console.error(`Failed to ${operationName}: ${err}`);
      return { isError: true, text: `Failed to ${operationName}: ${err}` };
    }
  };
}
