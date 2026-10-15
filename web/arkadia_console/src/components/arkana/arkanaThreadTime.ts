/**
 * Arkana thread timestamps — one canonical reading (feature-local, Workstream 4).
 *
 * The thread contract's `created_at` / `updated_at` come straight off the
 * Knowledge OS columns, whose default is SQLite's `datetime('now')`: the string
 * `YYYY-MM-DD HH:MM:SS` in **UTC**, with no zone designator. The backend passes
 * the column through unchanged (`api/commune_threads.py`), so the wire value is
 * zoneless UTC.
 *
 * That form is the trap. Per ECMA-262 a date-time string with no offset is read
 * as **local** time, so `new Date("2026-10-14T06:06:12")` yields a different
 * instant in every timezone — silently, and only off-UTC. On a UTC host (CI, a
 * UTC container) it is accidentally correct, which is why the defect survives a
 * green build. Measured: the same value shifts +240 min in America/New_York,
 * -60 min in Europe/London, -330 min in Asia/Kolkata.
 *
 * The reading is therefore pinned here rather than re-derived per surface:
 * zoneless values are UTC and get the designator; values that already carry one
 * are left alone. Rendering names the reader's zone so a displayed time is never
 * ambiguous about which clock it is on.
 */

/** Trailing zone designator: `Z`, or `+HH:MM` / `+HHMM` / `-HH`. */
const ZONE_DESIGNATOR = /(?:Z|[+-]\d{2}:?\d{2})$/i;

/** Date-time with no zone designator — `YYYY-MM-DD HH:MM:SS` or the `T` form. */
const ZONELESS_DATETIME = /^\d{4}-\d{2}-\d{2}[ T]\d{2}:\d{2}(:\d{2}(\.\d+)?)?$/;

/**
 * Put a backend timestamp on an unambiguous instant.
 *
 * A zoneless value is UTC by the column's contract, so it gains the designator.
 * Anything already carrying an offset — or that is not a date-time at all — is
 * returned unchanged: guessing a zone for a value that already states one would
 * move the instant.
 */
export function normalizeTimestamp(value: string): string {
  const trimmed = value.trim();
  if (ZONE_DESIGNATOR.test(trimmed)) return trimmed;
  if (!ZONELESS_DATETIME.test(trimmed)) return trimmed;
  return trimmed.replace(" ", "T") + "Z";
}

/** True when a value is not a timestamp this module can place on the timeline. */
export function unparsable(value: string): boolean {
  return Number.isNaN(new Date(normalizeTimestamp(value)).getTime());
}

/** The reader's own zone, e.g. `GMT-4` — named so a shown time is never ambiguous. */
export function readerZoneLabel(at: Date): string {
  const parts = new Intl.DateTimeFormat(undefined, { timeZoneName: "shortOffset" }).formatToParts(at);
  const zone = parts.find((p) => p.type === "timeZoneName");
  return zone ? zone.value : "";
}

/**
 * Render a backend timestamp in the reader's zone, labelled with that zone.
 *
 * An unreadable value is shown verbatim and marked, so it is never presented as
 * a time that was actually recorded.
 */
export function readableTime(value: string | null): string {
  if (!value) return "—";
  const instant = new Date(normalizeTimestamp(value));
  if (Number.isNaN(instant.getTime())) return `${value} (unparsed)`;
  const zone = readerZoneLabel(instant);
  const shown = instant.toLocaleString();
  return zone ? `${shown} ${zone}` : shown;
}
