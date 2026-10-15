/**
 * Engineering Lab — run → work-event → evidence trace projection (Workstream 4).
 *
 * A pure projection of the Lab session view
 * (`GET /api/lab/engineering/sessions/{id}` → `EngineeringLabRuntime.session_view`)
 * into a per-run linkage ledger. It reads only references the handler actually
 * records, and it joins them on exactly the fields the store persists:
 *
 *   run → work events   `event.run_id === run.run_id`
 *   run → evidence      `evidence.run_ref === run.run_id`
 *   run → evidence_refs `run.evidence_refs` names evidence ids
 *   run → artifacts     `artifact.run_id === run.run_id`
 *   run → artifact_refs `run.artifact_refs` names artifact ids
 *
 * Every join is a *recorded* reference. A reference that does not resolve is
 * reported as unresolved rather than dropped or guessed, so the surface can
 * never imply a link the substrate did not write.
 *
 * Governance: the module preserves the non-collapses it renders —
 * execution (run) != evidence != verification != review != human acceptance.
 * In particular `verification` is derived only from recorded *state* values, so
 * the presence of an evidence record is never presented as verification, and
 * acceptance is reported only when the session carries the human terminal state.
 * An artifact is a *captured proposal*: it is linked to the run that captured it
 * and is never read as an applied change, an evidence record, or a verdict.
 *
 * No network, no React, no store access: this file is importable and executable
 * on its own so its behaviour can be measured directly (see
 * `tests/test_prism_w4_run_evidence_trace.py`).
 */

export interface LabRunRecord {
  run_id: string;
  session_id?: string;
  agent_id?: string;
  state?: string;
  objective?: string;
  result_state?: string | null;
  evidence_refs?: string[];
  artifact_refs?: string[];
  created_at?: string;
  updated_at?: string;
}

export interface LabWorkEvent {
  event_id: string;
  session_id?: string;
  run_id?: string | null;
  event_type?: string;
  sequence?: number;
  payload?: Record<string, unknown>;
  timestamp_utc?: string;
}

export interface LabEvidenceRecord {
  evidence_id: string;
  subject_ref?: string;
  workspace_ref?: string;
  run_ref?: string;
  state?: string;
  summary?: string;
  detail?: Record<string, unknown>;
  timestamp_utc?: string;
  provenance?: Record<string, unknown>;
}

/**
 * An artifact captured by a run — the proposal the substrate prepares and stops
 * short of applying. `run_id` is the recorded link to the run that captured it.
 */
export interface LabArtifactRecord {
  artifact_id: string;
  session_id?: string;
  run_id?: string | null;
  kind?: string;
  title?: string;
  content?: unknown;
  created_at?: string;
}

export interface LabTraceSession {
  session_id: string;
  state?: string;
  authorization_ref?: string | null;
  objective?: string;
}

/** The subset of the session view this projection consumes. */
export interface LabTraceSource {
  session: LabTraceSession;
  runs?: LabRunRecord[];
  events?: LabWorkEvent[];
  evidence?: LabEvidenceRecord[];
  artifacts?: LabArtifactRecord[];
  reached_review_boundary?: boolean;
  human_decision_required?: boolean;
}

/**
 * Recorded run states that mean the verification *stage was entered*.
 *
 * These are Lab `CHECKPOINT_STATES` values. `REVISION_REQUIRED` is included
 * because it is reachable only through `VERIFYING`. Entering a stage is not
 * concluding it: `_finish` records a successful bounded run as `VERIFYING`
 * while its evidence state stays `IMPLEMENTED`, and the substrate's own
 * non-collapse list says `IMPLEMENTED != VERIFIED`.
 */
export const VERIFICATION_STAGE_STATES: readonly string[] = [
  "VERIFYING",
  "READY_FOR_REVIEW",
  "REVISION_REQUIRED",
];

/**
 * The single evidence `RESULT_STATES` value that *asserts* verification
 * concluded successfully. Everything else (`IMPLEMENTED`, `BLOCKED`,
 * `UNAVAILABLE`, `UNRESOLVED`, `NOT_ATTEMPTED`) asserts nothing of the kind.
 */
export const VERIFIED_EVIDENCE_STATES: readonly string[] = ["VERIFIED"];

/** The recorded state that places a run or session at the human review boundary. */
export const REVIEW_STATES: readonly string[] = ["READY_FOR_REVIEW"];

/**
 * The human terminal session state. Only a human act enters it
 * (`contracts.HUMAN_TERMINAL_STATES`, whose only member this is), so it is the
 * *only* recorded value this projection will read as acceptance.
 */
export const HUMAN_ACCEPTED_SESSION_STATES: readonly string[] = ["COMPLETED"];

export interface RunVerification {
  /** The verification stage was entered, per a recorded state. */
  stage_entered: boolean;
  /** A recorded value asserts verification concluded successfully. */
  asserted: boolean;
  entered_basis: string[];
  asserted_basis: string[];
  note: string;
}

export interface RunReview {
  at_boundary: boolean;
  /** The backend's own `human_decision_required` flag for the session. */
  human_decision_required: boolean;
  basis: string[];
  note: string;
}

export interface RunTrace {
  run_id: string;
  state: string;
  result_state: string | null;
  objective: string;
  agent_id: string | null;
  created_at: string | null;
  events: LabWorkEvent[];
  evidence: LabEvidenceRecord[];
  /** `run.evidence_refs` entries with no matching evidence record. */
  dangling_evidence_refs: string[];
  /** Evidence linked to this run that the run's own `evidence_refs` omits. */
  unreferenced_evidence_ids: string[];
  /** Artifacts joined by `artifact.run_id === run.run_id`. */
  artifacts: LabArtifactRecord[];
  /** `run.artifact_refs` entries with no matching artifact in this view. */
  dangling_artifact_refs: string[];
  /** Artifacts linked to this run that the run's own `artifact_refs` omits. */
  unreferenced_artifact_ids: string[];
  verification: RunVerification;
  review: RunReview;
}

export interface AcceptanceReading {
  state: "HUMAN_ACCEPTED" | "NOT_RECORDED";
  basis: string[];
  note: string;
}

export interface RunTraceLedger {
  runs: RunTrace[];
  /** Session-scoped events (no `run_id`) — recorded work, not a run's work. */
  session_events: LabWorkEvent[];
  /** Events whose `run_id` names no run in this view. */
  unlinked_events: LabWorkEvent[];
  /** Evidence whose `run_ref` names no run in this view. */
  unlinked_evidence: LabEvidenceRecord[];
  /** Evidence with no `run_ref` at all. */
  unattributed_evidence: LabEvidenceRecord[];
  /** Artifacts whose `run_id` names no run in this view. */
  unlinked_artifacts: LabArtifactRecord[];
  /** Artifacts with no `run_id` at all. */
  unattributed_artifacts: LabArtifactRecord[];
  /** Evidence ids that appear more than once in the view. */
  duplicate_evidence_ids: string[];
  /** Artifact ids that appear more than once in the view. */
  duplicate_artifact_ids: string[];
  /** Runs that produced evidence but no recorded value asserts verification. */
  evidence_without_verification: string[];
  /** Runs that produced evidence and also carry a recorded verification basis. */
  evidence_with_verification: string[];
  acceptance: AcceptanceReading;
  review_boundary: boolean;
  unresolved: string[];
}

function asArray<T>(value: T[] | undefined | null): T[] {
  return Array.isArray(value) ? value : [];
}

function dedupeById<T>(records: T[], idOf: (record: T) => string | undefined): {
  unique: T[];
  duplicates: string[];
} {
  const seen = new Set<string>();
  const duplicates = new Set<string>();
  const unique: T[] = [];
  for (const record of records) {
    const id = idOf(record);
    if (id === undefined || id === "") {
      unique.push(record);
      continue;
    }
    if (seen.has(id)) {
      duplicates.add(id);
      continue;
    }
    seen.add(id);
    unique.push(record);
  }
  return { unique, duplicates: Array.from(duplicates).sort() };
}

function verificationFor(run: LabRunRecord, evidence: LabEvidenceRecord[]): RunVerification {
  const entered: string[] = [];
  const asserted: string[] = [];
  if (run.state && VERIFICATION_STAGE_STATES.indexOf(run.state) !== -1) {
    entered.push(`run.state=${run.state}`);
  }
  for (const record of evidence) {
    if (record.state && VERIFIED_EVIDENCE_STATES.indexOf(record.state) !== -1) {
      asserted.push(`evidence.state=VERIFIED (${record.evidence_id})`);
    }
  }
  return {
    stage_entered: entered.length > 0,
    asserted: asserted.length > 0,
    entered_basis: entered,
    asserted_basis: asserted,
    note:
      asserted.length > 0
        ? "A recorded value asserts verification concluded. Review and acceptance remain separate acts."
        : entered.length > 0
          ? "The verification stage was entered. No recorded value asserts it concluded — an evidence record is a record, not a verdict."
          : "No verification recorded. An evidence record is a record, not a verdict.",
  };
}

function reviewFor(
  run: LabRunRecord,
  sessionState: string | undefined,
  reached: boolean,
  humanDecisionRequired: boolean,
): RunReview {
  const basis: string[] = [];
  if (run.state && REVIEW_STATES.indexOf(run.state) !== -1) basis.push(`run.state=${run.state}`);
  if (sessionState && REVIEW_STATES.indexOf(sessionState) !== -1) {
    basis.push(`session.state=${sessionState}`);
  }
  if (basis.length === 0 && (reached || humanDecisionRequired)) {
    basis.push("session.reached_review_boundary=true");
  }
  const at_boundary = basis.length > 0;
  return {
    at_boundary,
    human_decision_required: humanDecisionRequired,
    basis,
    note: at_boundary
      ? "At the human review boundary. A run at this boundary is not an accepted result."
      : "Not at the review boundary.",
  };
}

function acceptanceFor(sessionState: string | undefined): AcceptanceReading {
  const accepted = !!sessionState && HUMAN_ACCEPTED_SESSION_STATES.indexOf(sessionState) !== -1;
  return {
    state: accepted ? "HUMAN_ACCEPTED" : "NOT_RECORDED",
    basis: accepted ? [`session.state=${sessionState}`] : [],
    note: accepted
      ? "The session carries the human terminal state. Acceptance is a human act and was recorded."
      : "Acceptance is not recorded. It is never inferred from a run, a work event, or an evidence record.",
  };
}

/**
 * Project a session view into a run → work-event → evidence trace ledger.
 *
 * Defensive by construction: a view missing `runs`, `events`, or `evidence`
 * yields an empty ledger, not a throw. The handler filters evidence to the
 * session's runs before returning, so orphan evidence normally cannot appear —
 * it is still classified here so a future change to that filter surfaces as an
 * unresolved link instead of a silent omission.
 */
export function buildRunTrace(source: LabTraceSource): RunTraceLedger {
  const runs = asArray(source.runs);
  const sessionState = source.session?.state;
  const reached = source.reached_review_boundary === true;
  const humanDecisionRequired = source.human_decision_required === true;

  const evidenceDedup = dedupeById(asArray(source.evidence), (r) => r.evidence_id);
  const evidence = evidenceDedup.unique;
  const artifactDedup = dedupeById(asArray(source.artifacts), (r) => r.artifact_id);
  const artifacts = artifactDedup.unique;
  const events = asArray(source.events);

  const runsById = new Map<string, LabRunRecord>();
  for (const run of runs) runsById.set(run.run_id, run);

  const eventsByRun = new Map<string, LabWorkEvent[]>();
  const sessionEvents: LabWorkEvent[] = [];
  const unlinkedEvents: LabWorkEvent[] = [];
  for (const event of events) {
    if (!event.run_id) {
      sessionEvents.push(event);
      continue;
    }
    if (!runsById.has(event.run_id)) {
      unlinkedEvents.push(event);
      continue;
    }
    const bucket = eventsByRun.get(event.run_id) ?? [];
    bucket.push(event);
    eventsByRun.set(event.run_id, bucket);
  }

  const evidenceByRun = new Map<string, LabEvidenceRecord[]>();
  const unlinkedEvidence: LabEvidenceRecord[] = [];
  const unattributedEvidence: LabEvidenceRecord[] = [];
  for (const record of evidence) {
    if (!record.run_ref) {
      unattributedEvidence.push(record);
      continue;
    }
    if (!runsById.has(record.run_ref)) {
      unlinkedEvidence.push(record);
      continue;
    }
    const bucket = evidenceByRun.get(record.run_ref) ?? [];
    bucket.push(record);
    evidenceByRun.set(record.run_ref, bucket);
  }

  const artifactsByRun = new Map<string, LabArtifactRecord[]>();
  const unlinkedArtifacts: LabArtifactRecord[] = [];
  const unattributedArtifacts: LabArtifactRecord[] = [];
  for (const artifact of artifacts) {
    if (!artifact.run_id) {
      unattributedArtifacts.push(artifact);
      continue;
    }
    if (!runsById.has(artifact.run_id)) {
      unlinkedArtifacts.push(artifact);
      continue;
    }
    const bucket = artifactsByRun.get(artifact.run_id) ?? [];
    bucket.push(artifact);
    artifactsByRun.set(artifact.run_id, bucket);
  }

  const traces: RunTrace[] = runs.map((run) => {
    const runEvents = eventsByRun.get(run.run_id) ?? [];
    const runEvidence = evidenceByRun.get(run.run_id) ?? [];
    const declared = asArray(run.evidence_refs);
    const present = new Set<string>(runEvidence.map((r) => r.evidence_id));
    const runArtifacts = artifactsByRun.get(run.run_id) ?? [];
    const declaredArtifacts = asArray(run.artifact_refs);
    const artifactsPresent = new Set<string>(runArtifacts.map((a) => a.artifact_id));
    return {
      run_id: run.run_id,
      state: run.state ?? "UNKNOWN",
      result_state: run.result_state ?? null,
      objective: run.objective ?? "",
      agent_id: run.agent_id ?? null,
      created_at: run.created_at ?? null,
      events: runEvents,
      evidence: runEvidence,
      dangling_evidence_refs: declared.filter((id) => !present.has(id)),
      unreferenced_evidence_ids: runEvidence
        .map((r) => r.evidence_id)
        .filter((id) => declared.indexOf(id) === -1),
      artifacts: runArtifacts,
      dangling_artifact_refs: declaredArtifacts.filter((id) => !artifactsPresent.has(id)),
      unreferenced_artifact_ids: runArtifacts
        .map((a) => a.artifact_id)
        .filter((id) => declaredArtifacts.indexOf(id) === -1),
      verification: verificationFor(run, runEvidence),
      review: reviewFor(run, sessionState, reached, humanDecisionRequired),
    };
  });

  const unresolved: string[] = [];
  if (unlinkedEvents.length > 0) {
    unresolved.push(
      `${unlinkedEvents.length} work event(s) name a run that is not in this view.`,
    );
  }
  if (unlinkedEvidence.length > 0) {
    unresolved.push(`${unlinkedEvidence.length} evidence record(s) name a run not in this view.`);
  }
  if (unattributedEvidence.length > 0) {
    unresolved.push(`${unattributedEvidence.length} evidence record(s) carry no run reference.`);
  }
  if (unlinkedArtifacts.length > 0) {
    unresolved.push(`${unlinkedArtifacts.length} artifact(s) name a run not in this view.`);
  }
  if (unattributedArtifacts.length > 0) {
    unresolved.push(`${unattributedArtifacts.length} artifact(s) carry no run reference.`);
  }
  const dangling = traces.reduce((n, t) => n + t.dangling_evidence_refs.length, 0);
  if (dangling > 0) {
    unresolved.push(`${dangling} declared evidence reference(s) do not resolve.`);
  }
  const danglingArtifacts = traces.reduce((n, t) => n + t.dangling_artifact_refs.length, 0);
  if (danglingArtifacts > 0) {
    unresolved.push(`${danglingArtifacts} declared artifact reference(s) do not resolve.`);
  }
  if (evidenceDedup.duplicates.length > 0) {
    unresolved.push(
      `duplicate evidence id(s) in the view: ${evidenceDedup.duplicates.join(", ")}.`,
    );
  }
  if (artifactDedup.duplicates.length > 0) {
    unresolved.push(
      `duplicate artifact id(s) in the view: ${artifactDedup.duplicates.join(", ")}.`,
    );
  }
  if (unresolved.length === 0 && (runs.length > 0 || events.length > 0 || artifacts.length > 0)) {
    unresolved.push("Every recorded reference in this view resolves.");
  }

  return {
    runs: traces,
    session_events: sessionEvents,
    unlinked_events: unlinkedEvents,
    unlinked_evidence: unlinkedEvidence,
    unattributed_evidence: unattributedEvidence,
    unlinked_artifacts: unlinkedArtifacts,
    unattributed_artifacts: unattributedArtifacts,
    duplicate_evidence_ids: evidenceDedup.duplicates,
    duplicate_artifact_ids: artifactDedup.duplicates,
    evidence_without_verification: traces
      .filter((t) => t.evidence.length > 0 && !t.verification.asserted)
      .map((t) => t.run_id),
    evidence_with_verification: traces
      .filter((t) => t.evidence.length > 0 && t.verification.asserted)
      .map((t) => t.run_id),
    acceptance: acceptanceFor(sessionState),
    review_boundary: reached || traces.some((t) => t.review.at_boundary),
    unresolved,
  };
}
