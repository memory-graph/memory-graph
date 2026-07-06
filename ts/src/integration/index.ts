/**
 * Claude Code Integration module for automatic context capture and project awareness.
 *
 * Port of the Python `memorygraph.integration.__init__` module.
 *
 * This module provides deep integration with Claude Code development workflows:
 * - Development context capture (tasks, commands, errors)
 * - Project-aware memory (codebase analysis, file tracking)
 * - Workflow memory tools (tracking, suggestions, optimization)
 */

// Context Capture
export type { TaskContext, CommandExecution, ErrorPattern } from "./context-capture.js";
export {
  captureTaskContext,
  captureCommandExecution,
  analyzeErrorPatterns,
  trackSolutionEffectiveness,
} from "./context-capture.js";

// Project Analysis
export type { ProjectInfo, CodebaseInfo, FileChange, Pattern } from "./project-analysis.js";
export {
  detectProject,
  analyzeCodebase,
  trackFileChanges,
  identifyCodePatterns,
} from "./project-analysis.js";

// Workflow Tracking
export type {
  WorkflowAction,
  WorkflowSuggestion,
  Recommendation,
  SessionState,
} from "./workflow-tracking.js";
export {
  trackWorkflow,
  suggestWorkflow,
  optimizeWorkflow,
  getSessionState,
} from "./workflow-tracking.js";
