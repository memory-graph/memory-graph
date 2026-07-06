/**
 * Context extraction utilities for relationship contexts.
 *
 * Provides pattern-based extraction of structured information
 * from natural language relationship context fields.
 */

export interface ContextStructure {
  text: string;
  scope?: string;
  components: string[];
  conditions: string[];
  evidence: string[];
  temporal?: string;
  exceptions: string[];
}

export function extractContextStructure(text?: string | null): Partial<ContextStructure> {
  if (!text) return {};
  if (typeof text !== "string") text = String(text);

  return {
    text,
    scope: extractScope(text),
    components: extractComponents(text),
    conditions: extractConditions(text),
    evidence: extractEvidence(text),
    temporal: extractTemporal(text),
    exceptions: extractExceptions(text),
  };
}

export function parseContext(context?: string | null): Record<string, unknown> {
  if (!context) return {};
  try {
    return JSON.parse(context);
  } catch {
    return extractContextStructure(context) as Record<string, unknown>;
  }
}

function extractScope(text: string): string | undefined {
  const lower = text.toLowerCase();
  if (/\bpartial(?:ly)?\b|\blimited\b|\bincomplete\b/.test(lower)) return "partial";
  if (/\bfull(?:y)?\b|\bcomplete(?:ly)?\b|\bentirely\b/.test(lower)) return "full";
  if (/\bconditional(?:ly)?\b|\bonly\b/.test(lower)) return "conditional";
  return undefined;
}

function extractConditions(text: string): string[] {
  const conditions: string[] = [];
  const patterns = [
    /\bwhen\s+([^,.;]+)/gi,
    /\bif\s+([^,.;]+)/gi,
    /\bin\s+([\w-]+)\s+environment/gi,
    /\brequires\s+([^,.;]+)/gi,
    /\bonly\s+(?:works\s+)?in\s+([^,.;]+)/gi,
  ];
  for (const pattern of patterns) {
    let match: RegExpExecArray | null;
    while ((match = pattern.exec(text)) !== null) {
      conditions.push(match[1].trim());
    }
  }
  return conditions;
}

function extractEvidence(text: string): string[] {
  const evidence: string[] = [];
  const patterns = [
    /\bverified\s+by\s+([^,.;]+)/gi,
    /\btested\s+by\s+([^,.;]+)/gi,
    /\bproven\s+by\s+([^,.;]+)/gi,
    /\bobserved\s+in\s+([^,.;]+)/gi,
  ];
  for (const pattern of patterns) {
    let match: RegExpExecArray | null;
    while ((match = pattern.exec(text)) !== null) {
      evidence.push(match[1].trim());
    }
  }
  return evidence;
}

function extractTemporal(text: string): string | undefined {
  const sinceMatch = text.match(/\bsince\s+([^,;]+?)(?:\s*,|\s*;|$)/i);
  if (sinceMatch) return sinceMatch[1].trim();

  const afterMatch = text.match(/\bafter\s+([^,;]+?)(?:\s*,|\s*;|$)/i);
  if (afterMatch) return afterMatch[1].trim();

  const asOfMatch = text.match(/\bas\s+of\s+([^,;]+?)(?:\s*,|\s*;|$)/i);
  if (asOfMatch) return asOfMatch[1].trim();

  const versionMatch = text.match(/\bv?\d+\.\d+(?:\.\d+)?/i);
  if (versionMatch) return versionMatch[0];

  return undefined;
}

function extractExceptions(text: string): string[] {
  const exceptions: string[] = [];
  const patterns = [
    /\bexcept\s+([^,.;]+)/gi,
    /\bexcluding\s+([^,.;]+)/gi,
    /\bbut\s+not\s+([^,.;]+)/gi,
    /\bwithout\s+([^,.;]+)/gi,
  ];
  for (const pattern of patterns) {
    let match: RegExpExecArray | null;
    while ((match = pattern.exec(text)) !== null) {
      exceptions.push(match[1].trim());
    }
  }
  return exceptions;
}

function extractComponents(text: string): string[] {
  const components: string[] = [];
  const nounPatterns = [
    /([\w-]+)\s+module/gi,
    /([\w-]+)\s+service/gi,
    /([\w-]+)\s+layer/gi,
    /([\w-]+)\s+system/gi,
    /([\w-]+)\s+component/gi,
    /([\w-]+)\s+database/gi,
    /([\w-]+)\s+API/gi,
    /([\w-]+)\s+threads?/gi,
    /([\w-]+)\s+process(?:es)?/gi,
    /([\w-]+)\s+flow/gi,
    /([\w-]+)\s+leak/gi,
  ];

  for (const pattern of nounPatterns) {
    let match: RegExpExecArray | null;
    while ((match = pattern.exec(text)) !== null) {
      const full = match[0];
      if (!components.includes(full)) components.push(full);
    }
  }

  // Action patterns: implements/fixes/supports/handles X
  const actionPatterns = [/\b(?:implements?|fixes?|supports?|handles?)\s+([\w-]+(?:\s+[\w-]+)?)/gi];
  for (const pattern of actionPatterns) {
    let match: RegExpExecArray | null;
    while ((match = pattern.exec(text)) !== null) {
      const comp = match[1].trim();
      if (!["partially", "fully", "feature", "all"].includes(comp.toLowerCase())) {
        if (!components.includes(comp)) components.push(comp);
      }
    }
  }

  // Capitalized technical terms
  let capMatch: RegExpExecArray | null;
  const capPattern = /\b([A-Z][A-Za-z0-9]{2,})\b/g;
  const skip = new Set(["The", "This", "That", "It", "Testing"]);
  while ((capMatch = capPattern.exec(text)) !== null) {
    if (!skip.has(capMatch[1]) && !components.includes(capMatch[1])) {
      components.push(capMatch[1]);
    }
  }

  // Hyphenated terms
  let hyphenMatch: RegExpExecArray | null;
  const hyphenPattern = /\b([\w]+-[\w]+)\b/g;
  while ((hyphenMatch = hyphenPattern.exec(text)) !== null) {
    if (!components.includes(hyphenMatch[1])) {
      components.push(hyphenMatch[1]);
    }
  }

  return components;
}
