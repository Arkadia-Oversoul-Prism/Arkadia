/**
 * Engineering Lab — repository & change projection (AEAS-01 P0.3, pure).
 *
 * The handler (`api/lab_routes.py::engineering_repository`) observes git and
 * returns readings; this module turns them into what the surface renders. It is
 * pure and dependency-free so the contract test can **execute** it under Node
 * rather than judge a source substring, and so no rendering decision can drift
 * away from the reading it projects.
 *
 * One rule runs through every helper: a value the observation did not produce
 * is stated as UNKNOWN. An absent `clean` must never render as "clean", a failed
 * status read must never render as "0 changes", and an unavailable diff must
 * carry its reason instead of a blank block that reads as "no differences".
 */

// ---------------------------------------------------------------------------
// Contract shapes — transcribed from the served handler
// ---------------------------------------------------------------------------

export interface RepositoryReading {
  branch: string | null;
  head: string | null;
  short_head: string | null;
  remote: string | null;
  remote_redacted: boolean;
  status: string;
  reason: string | null;
  /** `true` / `false` only when `git status --porcelain` actually ran. */
  clean: boolean | null;
}

export interface ChangeEntry {
  code: string;
  label: string;
  path: string;
  original_path?: string | null;
  staged: boolean;
  unstaged: boolean;
}

export interface ChangesReading {
  status: string;
  reason: string | null;
  files: ChangeEntry[];
  /** `null` when the read failed — never a healthy-looking 0. */
  count: number | null;
  truncated: boolean;
}

export interface DiffSide {
  status: string;
  reason: string | null;
  text: string;
  chars: number;
  truncated: boolean;
}

export interface RepositoryContext {
  schema: string;
  observed_at: string;
  repository: RepositoryReading;
  changes: ChangesReading;
  diff: { unstaged: DiffSide; staged: DiffSide };
  boundary?: string;
}

export type FactRow = { label: string; value: string };

// ---------------------------------------------------------------------------
// Sentinels — a missing reading is stated, never promoted
// ---------------------------------------------------------------------------

function present(value: unknown): boolean {
  return value !== null && value !== undefined && value !== "";
}

/** `clean` is tri-state on purpose: an unobserved tree is UNKNOWN, not clean. */
export function describeClean(clean: boolean | null | undefined): string {
  if (clean === true) return "clean";
  if (clean === false) return "changes present";
  return "UNKNOWN";
}

/** The change count, or an explicit unknown when the status read failed. */
export function describeChangeCount(count: number | null | undefined): string {
  if (typeof count === "number") return `${count} file${count === 1 ? "" : "s"}`;
  return "UNKNOWN — status not observed";
}

/** One diff side: observed / empty / unavailable (+reason) / UNKNOWN. */
export function describeDiff(side: DiffSide | null | undefined): string {
  if (!side) return "UNKNOWN — not observed";
  if (side.status === "observed") {
    return `observed · ${side.chars} chars${side.truncated ? " · truncated" : ""}`;
  }
  if (side.status === "empty") return "empty — the read succeeded and printed nothing";
  if (side.status === "unavailable") {
    return `unavailable${side.reason ? ` — ${side.reason}` : ""}`;
  }
  return `UNKNOWN — ${side.status}`;
}

/** Short revision for the fact list; a missing head stays UNKNOWN. */
export function describeRevision(repo: RepositoryReading | null | undefined): string {
  if (!repo) return "UNKNOWN";
  if (present(repo.short_head)) return repo.short_head as string;
  if (present(repo.head)) return String(repo.head).slice(0, 12);
  return `UNKNOWN${repo.reason ? ` — ${repo.reason}` : ""}`;
}

// ---------------------------------------------------------------- ---------------------------------------------------------------------------
// Facts — the panel's key/value ledger
// ---------------------------------------------------------------------------

/**
 * Build the fact rows from the handler's own reading. `value` is always a
 * string, so an absent field renders as a sentinel rather than a blank cell
 * that reads like a confirmed value.
 */
export function buildRepositoryFacts(view: RepositoryContext | null | undefined): FactRow[] {
  if (!view) return [{ label: "reading", value: "UNKNOWN — no observation loaded" }];
  const repo = view.repository ?? ({} as RepositoryReading);
  const rows: FactRow[] = [
    { label: "branch", value: present(repo.branch) ? String(repo.branch) : "UNKNOWN" },
    { label: "source revision", value: describeRevision(repo) },
    { label: "working tree", value: describeClean(repo.clean) },
    { label: "changes", value: describeChangeCount(view.changes?.count) },
    {
      label: "origin",
      value: present(repo.remote)
        ? `${String(repo.remote)}${repo.remote_redacted ? " (userinfo redacted)" : ""}`
        : "UNKNOWN",
    },
    { label: "status", value: present(repo.status) ? String(repo.status) : "UNKNOWN" },
    { label: "observed at", value: present(view.observed_at) ? String(view.observed_at) : "UNKNOWN" },
  ];
  if (repo.reason) rows.push({ label: "reading note", value: String(repo.reason) });
  return rows;
}

/** How many changed files the list shows, and whether it was capped. */
export function describeCoverage(changes: ChangesReading | null | undefined): string {
  if (!changes) return "UNKNOWN — no observation loaded";
  if (changes.status !== "observed") {
    return `not observed${changes.reason ? ` — ${changes.reason}` : ""}`;
  }
  const shown = changes.files.length;
  const total = typeof changes.count === "number" ? changes.count : shown;
  const cap = changes.truncated ? ` · list capped at ${shown}` : "";
  return `${shown} of ${total} shown${cap}`;
}
