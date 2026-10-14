/**
 * Engineering Lab — operational authority reading (Workstream 4, feature-local).
 *
 * A pure projection of the `authority` and `counts` blocks the Lab overview
 * already returns (`GET /api/lab/engineering/overview` →
 * `lab.engineering_lab.runtime.EngineeringLabRuntime.overview`, which spreads
 * `runtime.overview(uid)` and adds the operational sections).
 *
 * The substrate states its own ceiling and its own prohibitions, and those are
 * the facts this projection must not let a surface round off:
 *
 *   lab_authority_ceiling        — the maximum authority the Lab declares it may
 *                                  hold. It is a **ceiling**, not a consent: the
 *                                  Lab never grants itself a level, and reporting
 *                                  the number is not reporting a granted authority.
 *   autonomous_merge             — the Lab declares it may not merge.
 *   autonomous_deploy            — the Lab declares it may not deploy.
 *   human_authorization_required — every consequential act crosses this gate.
 *
 * The counts block carries the session ladder the Lab already keeps:
 * `active` (a run is underway) and `awaiting_human` (a run reached the review /
 * verifying boundary). A run that reached the boundary is **not** acceptance —
 * it is exactly the state in which a human decision is still owed. The reading
 * keeps "awaiting a human" distinct from "approved", and "active" distinct from
 * "succeeded".
 *
 * Nothing here is inferred: a missing or malformed block is reported as
 * `unknown`, never smoothed into a healthy-looking zero.
 *
 * No network, no React, no store access: this file is importable and executable
 * on its own so its behaviour can be measured directly (see
 * `tests/test_prism_w4_lab_governance_readings.py`).
 */

/** The `authority` block `runtime.overview` returns. */
export interface LabAuthorityView {
  lab_authority_ceiling?: number;
  autonomous_merge?: boolean;
  autonomous_deploy?: boolean;
  human_authorization_required?: boolean;
}

/** The `counts` block `runtime.overview` returns. */
export interface LabCountsView {
  sessions?: number;
  active?: number;
  awaiting_human?: number;
}

/** The subset of the served Lab overview this projection consumes. */
export interface LabGovernanceSource {
  authority?: LabAuthorityView;
  counts?: LabCountsView;
}

export interface LabGovernanceReading {
  /** The declared ceiling, or null when the handler did not report a number. */
  ceiling: number | null;
  /** True when a numeric ceiling was reported. */
  ceiling_reported: boolean;
  /**
   * True when the Lab declares it will not merge without a human. `null` when the
   * handler did not report the flag — an absent declaration is unknown, and must
   * never read as `false` (which would imply the ceiling permits merging).
   */
  autonomous_merge: boolean | null;
  /** See `autonomous_merge`; `null` when unreported. */
  autonomous_deploy: boolean | null;
  /**
   * True when the Lab declares a human authorization gate. `null` when unreported.
   */
  human_authorization_required: boolean | null;
  sessions: number | null;
  active: number | null;
  /** Runs sitting at the review/verifying boundary — awaiting a human, not accepted. */
  awaiting_human: number | null;
  /** True iff the handler reported the substrate as closed to autonomous merge and deploy. */
  mutation_closed: boolean;
  /** True iff the handler reported every consequential act requires a human gate. */
  human_gate_declared: boolean;
  /** True iff the authority block is present and internally consistent. */
  authority_reported: boolean;
  /** A human-readable reading of the authority ceiling. */
  note: string;
}

function num(value: unknown): number | null {
  return typeof value === "number" && Number.isFinite(value) ? value : null;
}

function flag(value: unknown): boolean | null {
  return typeof value === "boolean" ? value : null;
}

export function readLabGovernance(source: LabGovernanceSource | null | undefined): LabGovernanceReading {
  const authority = source?.authority;
  const counts = source?.counts;

  const ceiling = num(authority?.lab_authority_ceiling);
  const autonomous_merge = flag(authority?.autonomous_merge);
  const autonomous_deploy = flag(authority?.autonomous_deploy);
  const human_gate = flag(authority?.human_authorization_required);

  const authority_reported =
    authority !== undefined &&
    ceiling !== null &&
    autonomous_merge !== null &&
    autonomous_deploy !== null &&
    human_gate !== null;

  // Only an explicit `false` declaration closes a mutation path. An absent flag is
  // unknown, so it cannot stand in for a closed door.
  const mutation_closed = autonomous_merge === false && autonomous_deploy === false;
  const human_gate_declared = human_gate === true;

  let note: string;
  if (!authority_reported) {
    note = "The Lab did not report its authority block. The ceiling is unknown, and the Lab grants itself nothing it does not declare.";
  } else if (mutation_closed && human_gate_declared) {
    note = `The Lab declares a ceiling of ${ceiling} and closes autonomous merge and deploy. A ceiling is the maximum it may hold, not a granted authority; every consequential act requires a human decision.`;
  } else {
    note =
      "The Lab's declared authority block does not assert both a closed mutation path and a human gate. Read this as unknown scope, not as permission.";
  }

  return {
    ceiling,
    ceiling_reported: ceiling !== null,
    autonomous_merge,
    autonomous_deploy,
    human_authorization_required: human_gate,
    sessions: num(counts?.sessions),
    active: num(counts?.active),
    awaiting_human: num(counts?.awaiting_human),
    mutation_closed,
    human_gate_declared,
    authority_reported,
    note,
  };
}
