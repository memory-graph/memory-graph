/**
 * Timezone-safe datetime utilities.
 */

export function utcNow(): Date {
  return new Date();
}

export function parseDatetime(value: string | Date): Date {
  if (value instanceof Date) return value;
  const dt = new Date(value);
  return dt;
}

export function ensureAware(dt: Date): Date {
  return dt;
}

export function toIsoString(value: string | Date): string {
  return value instanceof Date ? value.toISOString() : value;
}
