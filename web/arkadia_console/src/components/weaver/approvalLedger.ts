/**
 * Weaver — approval ledger projection (Workstream 4, feature-local).
 *
 * A pure projection of the approvals read contract
 * (`GET /api/approvals` → `api/approval_routes.py::api_list_approvals`, which
 * returns `{approvals: [...]}`). The handler is authenticated (`require_auth`)
 * and filters to what the caller may see: an ordinary identity sees only the
 * approvals it originated, while a principal holding `Govern` authority sees
 * every pending approval.
 *
 * The substrate keeps one distinction that a bare "status" string erases: a
 * recorded decision (`approved` / `rejected`) is **not** an execution. The
 * approval is spent later, at the tool-run boundary, and only there does a
 * `consumed_at` exist. The decision, the consumption, and the requester's
 * ability to act are three separate facts:
 *
 *   * `pending`          — requested, not yet decided.
 *   * `approved`/`rejected` — a human decision recorded. NOT an execution.
 *   * `consumed_at` set  — the permitted action was actually taken.
 *
 * Two boundary properties this projection defends, both traceable to the handler:
 *
 *   * **A decision is never rendered as an execution.** The `status` alone can
 *     never yield the `consumed` phase; only a real `consumed_at` can. A record
 *     that carried `consumed_at` while still `pending` is contradictory and is
 *     reported as such rather than being quietly advanced.
 *   * **Self-approval is a violation; self-rejection is not.** `api_approve`
 *     refuses a principal that decides its own request (403). `api_reject`
 *     explicitly *permits* it — "withdrawing one's own request is not a
 *     governance decision over another's consequential operation" — so a
 *     self-rejection is a legitimate withdrawal the backend does produce. When a
 *     record's `subject_ref` equals its `decided_by`, the ledger reports a
 *     boundary violation only for an **approval**; a **self-rejection** is read
 *     as a permitted withdrawal, never accused of a boundary the backend does
 *     not enforce.
 *
 * The record shape, the status vocabulary, and the phase ceiling are pinned to
 * the handler and to the tool-execution surface by
 * `tests/test_prism_w4_weaver_approval_ledger.py`, so a handler rename reddens
 * the guard rather than silently mis-labelling a record here.
 *
 * No network, no React, no store access: this file is importable and executable
 * on its own so its behaviour can be measured directly (see the test above).
 */

/** The subset of an approval record this projection consumes (from `queue_approval`). */
export interface ApprovalRecord {
  id?: string;
  tool_name?: string;
  description?: string;
  status?: string;
  created_at?: string;
  decided_at?: string | null;
  /** Identity the approval was requested on behalf of (never spent by another). */
  subject_ref?: string | null;
  /** Identity that rendered the decision. */
  decided_by?: string | null;
  /** Set only when the permitted action was actually taken at the tool boundary. */
  consumed_at?: string | null;
  consumed_by?: string | null;
}

/** The served approvals payload: `{approvals: [...]}`. */
export interface ApprovalPayload {
  approvals?: ApprovalRecord[];
}

/**
 * Recorded decision vocabulary, pinned to `api/approval_routes.py`. A status
 * outside this set is reported as unknown, never coerced into a known one.
 */
export const DECISION_STATUSES: readonly string[] = ["pending", "approved", "rejected"];

/**
 * The lifecycle phases a record may be read into. They are ordered so the surface
 * can show where a record sits **before** the execution boundary:
 *
 *   REQUESTED → DECIDED → CONSUMED
 *
 * `DECIDED` is deliberately not the last phase: an approval is an authorization,
 * and an authorization is not the act it authorizes.
 */
export type ApprovalPhase = "REQUESTED" | "DECIDED" | "CONSUMED" | "UNKNOWN";

export interface ApprovalReading {
  id: string;
  tool_name: string;
  description: string;
  /** Raw status as served. */
  status: string;
  /** True when `status` is one of `DECISION_STATUSES`. */
  status_known: boolean;
  phase: ApprovalPhase;
  /** True only when a real `consumed_at` is present — never inferred from status. */
  consumed: boolean;
  /** True when `subject_ref` and `decided_by` name the same identity. */
  self_decided: boolean;
  /**
   * True when the requester approved its own request — the one self-decision the
   * backend refuses (`api_approve` → 403).
   */
  self_approved: boolean;
  /**
   * True when the requester rejected its own request — *permitted* by `api_reject`
   * ("withdrawing one's own request"), so a legitimate record, not a violation.
   */
  self_rejected: boolean;
  /** True when `consumed_at` is present but the record is still `pending`. */
  contradictory: boolean;
  /** True when the recorded state is one the backend would refuse (self-approval, or contradictory). */
  boundary_violation: boolean;
  subject_ref: string | null;
  decided_by: string | null;
  created_at: string | null;
  decided_at: string | null;
  consumed_at: string | null;
  note: string;
}

export interface ApprovalLedger {
  readings: ApprovalReading[];
  /** A human coalesced summary for the surface header. */
  counts: {
    total: number;
    pending: number;
    decided: number;
    consumed: number;
    unknown: number;
  };
  /** Records whose recorded state the backend would not have produced. */
  violations: ApprovalReading[];
}

function str(value: unknown): string {
  return typeof value === "string" ? value : "";
}

function nullable(value: unknown): string | null {
  return typeof value === "string" && value.length > 0 ? value : null;
}

/**
 * Read one record. The phase is derived from the *facts* (`consumed_at`), not
 * from the `status` string, so a decision can never be shown as an execution.
 */
export function readApproval(record: ApprovalRecord, index: number): ApprovalReading {
  const status = str(record.status) || "pending";
  const status_known = DECISION_STATUSES.includes(status);
  const id = str(record.id) || `approval-${index}`;
  const subject_ref = nullable(record.subject_ref);
  const decided_by = nullable(record.decided_by);
  const consumed_at = nullable(record.consumed_at);
  const decided_at = nullable(record.decided_at);

  const consumed = consumed_at !== null;
  const self_decided = subject_ref !== null && decided_by !== null && subject_ref === decided_by;
  // Only self-*approval* is refused by the backend (`api_approve` -> 403).
  // Self-rejection is explicitly permitted (`api_reject`: withdrawing one's own
  // request), so the two self-decisions must not collapse into one flag.
  const self_approved = self_decided && status === "approved";
  const self_rejected = self_decided && status === "rejected";
  // A pending record cannot have been consumed: the act precedes no decision.
  const contradictory = consumed && status === "pending";

  let phase: ApprovalPhase;
  if (!status_known) phase = "UNKNOWN";
  else if (consumed) phase = "CONSUMED";
  else if (status === "pending") phase = "REQUESTED";
  else phase = "DECIDED";

  const boundary_violation = self_approved || contradictory;

  return {
    id,
    tool_name: str(record.tool_name) || "(unnamed tool)",
    description: str(record.description),
    status,
    status_known,
    phase,
    consumed,
    self_decided,
    self_approved,
    self_rejected,
    contradictory,
    boundary_violation,
    subject_ref,
    decided_by,
    created_at: nullable(record.created_at),
    decided_at,
    consumed_at,
    note: noteFor(phase, boundary_violation, self_approved, self_rejected, contradictory),
  };
}

function noteFor(
  phase: ApprovalPhase,
  violation: boolean,
  self_approved: boolean,
  self_rejected: boolean,
  contradictory: boolean,
): string {
  if (self_approved) {
    return "Boundary violation: a principal may not approve its own request (the backend refuses self-approval).";
  }
  if (contradictory) {
    return "Contradictory record: a consumed approval cannot still be pending.";
  }
  if (self_rejected) {
    return "Withdrawn by the requester. Self-rejection is permitted — withdrawing one's own request is not a governance decision over another's operation.";
  }
  switch (phase) {
    case "REQUESTED":
      return "Awaiting a decision. An open request is not an authorization.";
    case "DECIDED":
      return "A decision is recorded. An approval is not the execution it authorizes.";
    case "CONSUMED":
      return "The permitted action was taken. Consumption is the execution boundary.";
    default:
      return violation
        ? "Unrecognised record state."
        : "Unrecognised status; reported as unknown rather than coerced.";
  }
}

/** Project a served payload into an ordered ledger. */
export function buildApprovalLedger(payload: ApprovalPayload | null | undefined): ApprovalLedger {
  const records = Array.isArray(payload?.approvals) ? payload!.approvals! : [];
  const readings = records.map((record, i) => readApproval(record ?? {}, i));

  const counts = {
    total: readings.length,
    pending: readings.filter((r) => r.phase === "REQUESTED").length,
    decided: readings.filter((r) => r.phase === "DECIDED").length,
    consumed: readings.filter((r) => r.phase === "CONSUMED").length,
    unknown: readings.filter((r) => r.phase === "UNKNOWN").length,
  };

  return {
    readings,
    counts,
    violations: readings.filter((r) => r.boundary_violation),
  };
}
