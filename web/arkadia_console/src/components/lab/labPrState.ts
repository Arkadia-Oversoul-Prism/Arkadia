/**
 * Engineering Lab — PR state projection (Workstream 4).
 *
 * Projects `GET /api/lab/engineering/pr/{number}` (`api.lab_routes.pr_state`,
 * EL-10) into a ledger the console can render without overstating it.
 *
 * The handler's own doctrine is the reason this module exists. It answers with
 * one of two states and never a third:
 *
 *   AVAILABLE   -> `pr` is a record read from GitHub
 *   UNAVAILABLE -> `pr` is `null` and `detail` says why (no token, HTTP status,
 *                  transport failure)
 *
 * GitHub remains the repository authority. The handler exposes the fields the
 * Lab's read-only boundary is allowed to observe, and this projection reports
 * only those: a field the payload omits is reported as *unreported*, never
 * inferred. `mergeable_state` in particular is GitHub's own coarse string and is
 * not a merge decision — an absent value is reported as not reported, not as
 * "clean".
 *
 * Non-collapses preserved:
 *   - reachability (AVAILABLE) is not mergeability;
 *   - `state: "closed"` is not `merged` — GitHub returns `closed` for both a
 *     merged and an abandoned PR, and the handler does not read `merged`, so the
 *     projection reports the *outcome* as unreported rather than guessing one;
 *   - `draft` is not `ready`, and a read is not a review or an acceptance.
 *
 * No network, no React, no store access: this file is importable and executable
 * on its own so its behaviour can be measured directly (see
 * `tests/test_prism_w4_lab_pr_state.py`).
 */

/** A pull request record as the EL-10 handler emits it. */
export interface LabPrRecord {
  number?: number | null;
  title?: string | null;
  state?: string | null;
  draft?: boolean | null;
  mergeable_state?: string | null;
  html_url?: string | null;
  head?: string | null;
  base?: string | null;
}

/** The handler's response envelope. */
export interface LabPrStatePayload {
  state?: string | null;
  detail?: string | null;
  pr?: LabPrRecord | null;
}

export type LabPrAvailability = "AVAILABLE" | "UNAVAILABLE" | "UNKNOWN";

/** The two handler states, read exactly. A third value is not invented. */
export function readAvailability(payload: LabPrStatePayload | null): LabPrAvailability {
  const state = payload?.state;
  if (state === "AVAILABLE") return "AVAILABLE";
  if (state === "UNAVAILABLE") return "UNAVAILABLE";
  return "UNKNOWN";
}

export interface LabPrReading {
  availability: LabPrAvailability;
  /** The handler's own reason for an unavailability; `null` when it gave none. */
  detail: string | null;
  /**
   * True only when the handler declared AVAILABLE *and* supplied a record. A
   * declared AVAILABLE with no record is a malformed answer, not a PR.
   */
  hasRecord: boolean;
  /** The PR's own state as reported, or null. Never derived from `detail`. */
  state: string | null;
  draft: boolean | null;
  mergeableState: string | null;
  head: string | null;
  base: string | null;
  htmlUrl: string | null;
}

/**
 * Read the payload into a ledger.
 *
 * A `null` payload (the request never produced a body) reads as UNKNOWN rather
 * than as an absence of PRs: "we did not get an answer" and "there is no PR" are
 * different facts and must not render the same way.
 */
export function readPrState(payload: LabPrStatePayload | null): LabPrReading {
  const availability = readAvailability(payload);
  const pr = payload?.pr ?? null;
  const hasRecord = availability === "AVAILABLE" && pr !== null;
  return {
    availability,
    detail: typeof payload?.detail === "string" && payload.detail ? payload.detail : null,
    hasRecord,
    state: hasRecord && typeof pr.state === "string" ? pr.state : null,
    draft: hasRecord && typeof pr.draft === "boolean" ? pr.draft : null,
    mergeableState: hasRecord && typeof pr.mergeable_state === "string" ? pr.mergeable_state : null,
    head: hasRecord && typeof pr.head === "string" && pr.head ? pr.head : null,
    base: hasRecord && typeof pr.base === "string" && pr.base ? pr.base : null,
    htmlUrl: hasRecord && typeof pr.html_url === "string" && pr.html_url ? pr.html_url : null,
  };
}

/** Render a reported value, or state that it was not reported. Never guess. */
export function reported(value: string | number | boolean | null): string {
  if (value === null || value === undefined || value === "") return NOT_REPORTED;
  return String(value);
}

export const NOT_REPORTED = "not reported";

/**
 * The lifecycle phrase, kept strictly to what the payload supports.
 *
 * `draft` is a separate fact from `state`; a `closed` state carries no outcome,
 * because the handler does not read GitHub's `merged` field and `closed` covers
 * both outcomes.
 */
export function lifecyclePhrase(reading: LabPrReading): string {
  if (!reading.hasRecord) return NOT_REPORTED;
  const parts: string[] = [];
  if (reading.state) parts.push(reading.state);
  if (reading.draft === true) parts.push("draft");
  else if (reading.draft === false) parts.push("ready for review");
  if (reading.state === "closed") parts.push("outcome not reported (merged vs. abandoned)");
  return parts.length > 0 ? parts.join(" · ") : NOT_REPORTED;
}

/** A PR number is a positive integer; anything else is not a target to read. */
export function isValidPrNumber(value: string): boolean {
  return /^[1-9][0-9]*$/.test(value.trim());
}

// ---------------------------------------------------------------------------
// Path — declared route from `api/lab_routes.py::pr_state`.
// ---------------------------------------------------------------------------

const BASE = "/api/lab/engineering/pr";

/**
 * Build the read path for a PR number.
 *
 * The number is validated and encoded rather than interpolated, so a malformed
 * input yields `null` and the surface renders "not a PR number" instead of
 * issuing a request the handler would answer `422` for.
 */
export function prStatePath(number: string): string | null {
  const trimmed = number.trim();
  if (!isValidPrNumber(trimmed)) return null;
  return `${BASE}/${encodeURIComponent(trimmed)}`;
}
