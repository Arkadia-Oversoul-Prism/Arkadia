/**
 * Tolerant readers for backend records whose OpenAPI schema is declared
 * `additionalProperties: true`.
 *
 * Several served handlers (the SolSpire project sub-resources, the AIS profile,
 * the canonical workspace) publish no field schema, so the console cannot type
 * them without inventing one. These readers render what a record actually
 * carries — its scalar fields — and report honestly when a payload is not a
 * record or a list. They never substitute mock data.
 */
import { ApiError } from "./apiClient";

export type ScalarRow = { label: string; value: string };

export function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

/** Scalar fields of a record, in declaration order. Nested values are skipped. */
export function scalarRows(value: unknown): ScalarRow[] {
  if (!isRecord(value)) return [{ label: "value", value: String(value) }];
  const rows: ScalarRow[] = [];
  for (const [label, v] of Object.entries(value)) {
    if (v === null || v === undefined) continue;
    if (typeof v === "object") continue;
    rows.push({ label, value: String(v) });
  }
  return rows;
}

/**
 * A record read. A handler may wrap its record under a single object-valued key
 * (for example `{project: {...}}`); that wrapper is unwrapped so the facts shown
 * are the record's own. A payload that is not a record is refused rather than
 * rendered as an empty one.
 */
export async function readRecord(
  path: string,
  fetcher: (p: string) => Promise<unknown>,
): Promise<Record<string, unknown>> {
  const payload = await fetcher(path);
  if (!isRecord(payload)) {
    throw new ApiError("The contract returned an unrecognised shape.", { kind: "UNKNOWN", path });
  }
  const keys = Object.keys(payload);
  if (keys.length === 1) {
    const only = payload[keys[0]];
    if (isRecord(only)) return only;
  }
  return payload;
}

/** The list a payload carries, or null when it carries none. */
export function asItems(payload: unknown): unknown[] | null {
  if (Array.isArray(payload)) return payload;
  if (isRecord(payload)) {
    for (const key of ["items", "tasks", "files", "events", "results", "data", "records"]) {
      const v = payload[key];
      if (Array.isArray(v)) return v;
    }
  }
  return null;
}
