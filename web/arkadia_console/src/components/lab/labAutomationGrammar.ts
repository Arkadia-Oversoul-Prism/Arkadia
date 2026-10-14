/**
 * Engineering Lab — automation grammar projection (Workstream 4).
 *
 * A pure projection of the automations read contract
 * (`GET /api/lab/engineering/automations` → `api/lab_routes.py::list_automations`,
 * which returns `{automations, grammar}` from
 * `lab/engineering_lab/automations.py`).
 *
 * The substrate declares the automation grammar as an ordered chain —
 * TRIGGER → AGENT → TOOLS → SANDBOX → OUTPUT → EVIDENCE → NOTIFICATION →
 * HUMAN_GATE — and is explicit that an automation *prepares* consequential
 * actions but "may never independently authorize them: the final transition is
 * always the human gate".
 *
 * This projection reads the served payload only. Two things follow from that:
 *
 *   * A grammar clause is reported **filled** only when the automation record
 *     carries a value for it. EVIDENCE is not carried on the definition record
 *     at all — evidence is produced by a *run*, not declared by a definition —
 *     so that clause stays visibly unfilled here rather than being inferred from
 *     the presence of a completed-looking state.
 *   * A record that claimed `may_authorize: true`, or a payload whose declared
 *     `final_transition` was not the human gate, is reported as a **boundary
 *     violation**, never accepted as a reading. The surface cannot confer
 *     authority, and it must not render a claim of authority as ordinary state.
 *
 * The state vocabulary is read from the served grammar when present; a state
 * outside that vocabulary is reported as unknown, not coerced into a known one.
 *
 * No network, no React, no store access: this file is importable and executable
 * on its own so its behaviour can be measured directly (see
 * `tests/test_prism_w4_automation_grammar.py`).
 */

export interface AutomationTriggerView {
  kind?: string;
  detail?: string;
  schedule?: string | null;
  event?: string | null;
}

export interface AutomationRecord {
  automation_id: string;
  name?: string;
  state?: string;
  trigger?: AutomationTriggerView;
  agent_role?: string;
  objective?: string;
  tools?: string[];
  sandbox_write_allowed?: boolean;
  notification_target?: string;
  may_authorize?: boolean;
  human_gate_required?: boolean;
  grammar?: string[];
  created_at?: string;
  updated_at?: string;
}

export interface AutomationGrammarView {
  grammar?: string[];
  states?: string[];
  trigger_kinds?: string[];
  may_prepare_consequential_action?: boolean;
  may_authorize_consequential_action?: boolean;
  final_transition?: string;
}

/** The subset of the served automations payload this projection consumes. */
export interface AutomationPayload {
  automations?: AutomationRecord[];
  grammar?: AutomationGrammarView;
}

/**
 * The ordered grammar chain. Pinned to `automations.grammar_view()["grammar"]`
 * by `tests/test_lab_automation_grammar_contract.py`, so a substrate reorder
 * reddens the guard instead of silently re-labelling a clause here.
 */
export const GRAMMAR_CLAUSES: readonly string[] = [
  "TRIGGER",
  "AGENT",
  "TOOLS",
  "SANDBOX",
  "OUTPUT",
  "EVIDENCE",
  "NOTIFICATION",
  "HUMAN_GATE",
];

/** The clause a *run* fills, not the definition. Never inferred here. */
export const RUN_PRODUCED_CLAUSES: readonly string[] = ["EVIDENCE"];

/**
 * States only a human act may leave or enter terminally. Pinned to
 * `automations.HUMAN_GATED_STATES` by the contract guard.
 */
export const HUMAN_GATED_STATES: readonly string[] = ["AWAITING_HUMAN_ACTION", "COMPLETED"];

/** States with no outgoing transition. Pinned to `automations.AUTOMATION_TRANSITIONS`. */
export const TERMINAL_STATES: readonly string[] = ["COMPLETED"];

/**
 * Trigger kinds whose clause is only complete with an event key. The remaining
 * kinds need a schedule (`scheduled`) or nothing (`manual`); both facts are
 * pinned against the substrate's `TRIGGER_KINDS` by the contract guard.
 */
export const EVENT_TRIGGER_KINDS: readonly string[] = [
  "repository_event",
  "pr_event",
  "runtime_health",
  "external_event",
];

export interface ClauseReading {
  clause: string;
  filled: boolean;
  basis: string;
  note: string;
}

export interface AuthorizationReading {
  /** The record's own `may_authorize` value, if it carried one. */
  recorded: boolean | null;
  /** True when a record or payload claimed an authority the substrate forbids. */
  violation: boolean;
  basis: string[];
  note: string;
}

export interface HumanGateReading {
  required: boolean;
  final_transition: string | null;
  violation: boolean;
  basis: string[];
  note: string;
}

export interface AutomationStateReading {
  state: string;
  known: boolean;
  human_gated: boolean;
  terminal: boolean;
  basis: string[];
  note: string;
}

export interface AutomationReading {
  automation_id: string;
  name: string;
  state: AutomationStateReading;
  trigger: AutomationTriggerView;
  agent_role: string | null;
  clauses: ClauseReading[];
  unfilled_clauses: string[];
  /** Unfilled clauses a *definition* cannot carry — a run fills them. */
  run_produced_clauses: string[];
  authorization: AuthorizationReading;
  human_gate: HumanGateReading;
  tools: string[];
  sandbox_write_allowed: boolean;
  notification_target: string;
  created_at: string | null;
  updated_at: string | null;
  unresolved: string[];
}

export interface AutomationLedger {
  automations: AutomationReading[];
  /** The payload's declared grammar chain, and whether it is the one rendered. */
  declared_grammar: string[];
  grammar_matches: boolean;
  declared_states: string[];
  final_transition: string | null;
  /** Every recorded authority claim the substrate forbids. */
  boundary_violations: string[];
  /** Recorded states outside the served state vocabulary. */
  unknown_states: string[];
  state_counts: Record<string, number>;
  unresolved: string[];
}

function asArray<T>(value: T[] | undefined | null): T[] {
  return Array.isArray(value) ? value : [];
}

function isNonEmpty(value: string | undefined | null): boolean {
  return typeof value === "string" && value.trim() !== "";
}

function clauseReading(clause: string, filled: boolean, basis: string, note: string): ClauseReading {
  return { clause, filled, basis, note };
}

function triggerClauses(record: AutomationRecord): ClauseReading[] {
  const trigger = record.trigger ?? {};
  const kind = trigger.kind;
  const kindKnown = isNonEmpty(kind);
  const readings: ClauseReading[] = [];

  if (!kindKnown) {
    readings.push(
      clauseReading(
        "TRIGGER",
        false,
        "no trigger kind recorded",
        "A trigger with no kind is an incomplete definition, not a manual trigger.",
      ),
    );
  } else if (EVENT_TRIGGER_KINDS.indexOf(kind as string) !== -1) {
    const hasEvent = isNonEmpty(trigger.event);
    readings.push(
      clauseReading(
        "TRIGGER",
        hasEvent,
        hasEvent ? `kind=${kind}, event=${trigger.event}` : `kind=${kind}, no event key`,
        hasEvent
          ? "The event kind names the key it fires on."
          : "An event trigger with no event key cannot fire; the clause stays unfilled.",
      ),
    );
  } else if (kind === "scheduled") {
    const hasSchedule = isNonEmpty(trigger.schedule);
    readings.push(
      clauseReading(
        "TRIGGER",
        hasSchedule,
        hasSchedule ? `kind=scheduled, schedule=${trigger.schedule}` : "kind=scheduled, no schedule",
        hasSchedule
          ? "The scheduled kind carries the cadence it fires on."
          : "A scheduled trigger with no schedule cannot fire; the clause stays unfilled.",
      ),
    );
  } else {
    readings.push(
      clauseReading(
        "TRIGGER",
        true,
        `kind=${kind}`,
        "A manual trigger needs neither a schedule nor an event key.",
      ),
    );
  }

  const roleFilled = isNonEmpty(record.agent_role);
  readings.push(
    clauseReading(
      "AGENT",
      roleFilled,
      roleFilled ? `agent_role=${record.agent_role}` : "no agent role recorded",
      roleFilled
        ? "The automation names the role that would run it."
        : "No role is named, so the agent clause is unfilled.",
    ),
  );

  const tools = asArray(record.tools);
  readings.push(
    clauseReading(
      "TOOLS",
      true,
      tools.length > 0 ? `tools declared: ${tools.join(", ")}` : "no tools declared",
      "The tool list is a declared envelope, not a grant. An empty list declares no tools.",
    ),
  );

  const sandboxRecorded = typeof record.sandbox_write_allowed === "boolean";
  readings.push(
    clauseReading(
      "SANDBOX",
      sandboxRecorded,
      sandboxRecorded ? `write_allowed=${record.sandbox_write_allowed}` : "no sandbox envelope recorded",
      sandboxRecorded
        ? "The write envelope the substrate would enforce is recorded."
        : "No sandbox envelope is recorded, so the clause stays unfilled.",
    ),
  );

  const objective = isNonEmpty(record.objective) ? (record.objective as string) : "";
  const objectiveFilled = objective.length > 0;
  readings.push(
    clauseReading(
      "OUTPUT",
      objectiveFilled,
      objectiveFilled ? `objective declared (${objective.length} chars)` : "no objective declared",
      objectiveFilled
        ? "The automation declares what it is for."
        : "No objective is declared, so the output clause is unfilled.",
    ),
  );

  readings.push(
    clauseReading(
      "EVIDENCE",
      false,
      "not carried by the automation definition",
      "Evidence is produced by a run, not declared by a definition. This clause is filled at run time; it is never inferred here from the recorded state.",
    ),
  );

  const notificationFilled = isNonEmpty(record.notification_target);
  readings.push(
    clauseReading(
      "NOTIFICATION",
      notificationFilled,
      notificationFilled ? `target=${record.notification_target}` : "no notification target recorded",
      notificationFilled
        ? "The automation names where its glance would be delivered."
        : "No notification target is recorded, so the clause stays unfilled.",
    ),
  );

  const gateRequired = record.human_gate_required === true;
  readings.push(
    clauseReading(
      "HUMAN_GATE",
      gateRequired,
      gateRequired ? "human_gate_required=true" : "human gate not asserted by the record",
      gateRequired
        ? "The final transition is the human gate, as the substrate requires."
        : "The record does not assert the human gate; the clause stays unfilled rather than assumed.",
    ),
  );

  return readings;
}

function stateReadingFor(state: string, vocabulary: string[]): AutomationStateReading {
  const known = vocabulary.length === 0 || vocabulary.indexOf(state) !== -1;
  const humanGated = HUMAN_GATED_STATES.indexOf(state) !== -1;
  const terminal = TERMINAL_STATES.indexOf(state) !== -1;
  const basis: string[] = [`state=${state}`];
  if (humanGated) basis.push("human-gated state");
  if (terminal) basis.push("terminal state");
  return {
    state,
    known,
    human_gated: humanGated,
    terminal,
    basis,
    note: !known
      ? "This state is not in the served vocabulary. It is reported as recorded and not mapped onto a known state."
      : terminal
        ? "A terminal state. It is entered through the human gate and is not a self-serve result."
        : humanGated
          ? "A human-gated state. Only a human act leaves it; an automation cannot return itself to work."
          : "A working state. Reaching it is not evidence, verification, or acceptance.",
  };
}

function authorizationFor(record: AutomationRecord): AuthorizationReading {
  const recorded =
    typeof record.may_authorize === "boolean" ? (record.may_authorize as boolean) : null;
  const violation = recorded === true;
  const basis: string[] = [];
  if (recorded !== null) basis.push(`may_authorize=${recorded}`);
  return {
    recorded,
    violation,
    basis,
    note: violation
      ? "The record claims it may authorize a consequential action. The substrate forbids this and the claim is reported as a boundary violation, never as state."
      : "The record claims no authority to authorize. Preparing an action is not authorizing it.",
  };
}

function humanGateFor(record: AutomationRecord, payloadGate: string | null): HumanGateReading {
  const required = record.human_gate_required === true;
  const basis: string[] = [];
  if (required) basis.push("record.human_gate_required=true");
  if (payloadGate !== null) basis.push(`grammar.final_transition=${payloadGate}`);
  const violation = payloadGate !== null && payloadGate !== "HUMAN_GATE";
  return {
    required,
    final_transition: payloadGate,
    violation,
    basis,
    note: violation
      ? "The served grammar declares a final transition that is not the human gate. That is a boundary violation, not a reading."
      : "The final transition is the human gate. An automation may prepare a consequential action and may never authorize it.",
  };
}

/**
 * Project the served automations payload into a grammar ledger.
 *
 * Defensive by construction: a payload missing `automations` or `grammar` yields
 * an empty ledger, not a throw.
 */
export function buildAutomationLedger(payload: AutomationPayload | null | undefined): AutomationLedger {
  const source = payload ?? {};
  const records = asArray(source.automations);
  const grammar = source.grammar ?? {};

  const declaredGrammar = asArray(grammar.grammar);
  const declaredStates = asArray(grammar.states);
  const payloadGate = isNonEmpty(grammar.final_transition) ? (grammar.final_transition as string) : null;

  const grammarMatches =
    declaredGrammar.length === GRAMMAR_CLAUSES.length &&
    GRAMMAR_CLAUSES.every((clause, index) => declaredGrammar[index] === clause);

  const automations: AutomationReading[] = records.map((record) => {
    const clauses = triggerClauses(record);
    const unfilled = clauses.filter((c) => !c.filled).map((c) => c.clause);
    const runProduced = unfilled.filter((c) => RUN_PRODUCED_CLAUSES.indexOf(c) !== -1);
    const state = stateReadingFor(
      isNonEmpty(record.state) ? (record.state as string) : "UNKNOWN",
      declaredStates,
    );
    const authorization = authorizationFor(record);
    const humanGate = humanGateFor(record, payloadGate);
    const unresolved: string[] = [];
    // A clause a run fills is not an incomplete definition; naming it as
    // unresolved would report the substrate's own non-collapse as a defect.
    const incomplete = unfilled.filter((c) => RUN_PRODUCED_CLAUSES.indexOf(c) === -1);
    if (incomplete.length > 0) {
      unresolved.push(`unfilled grammar clause(s): ${incomplete.join(", ")}.`);
    }
    if (!state.known) unresolved.push(`state ${state.state} is outside the served vocabulary.`);
    if (authorization.violation) unresolved.push("the record claims authority it does not have.");
    return {
      automation_id: record.automation_id,
      name: isNonEmpty(record.name) ? (record.name as string) : "(unnamed)",
      state,
      trigger: record.trigger ?? {},
      agent_role: isNonEmpty(record.agent_role) ? (record.agent_role as string) : null,
      clauses,
      unfilled_clauses: unfilled,
      run_produced_clauses: runProduced,
      authorization,
      human_gate: humanGate,
      tools: asArray(record.tools),
      sandbox_write_allowed: record.sandbox_write_allowed === true,
      notification_target: isNonEmpty(record.notification_target)
        ? (record.notification_target as string)
        : "(none)",
      created_at: record.created_at ?? null,
      updated_at: record.updated_at ?? null,
      unresolved,
    };
  });

  const boundaryViolations: string[] = [];
  if (!grammarMatches) {
    boundaryViolations.push(
      `served grammar chain is not the rendered chain: ${declaredGrammar.join(" -> ") || "(none)"}.`,
    );
  }
  if (payloadGate !== null && payloadGate !== "HUMAN_GATE") {
    boundaryViolations.push(`served final_transition is ${payloadGate}, not the human gate.`);
  }
  if (grammar.may_authorize_consequential_action === true) {
    boundaryViolations.push("served grammar claims an automation may authorize a consequential action.");
  }
  for (const reading of automations) {
    if (reading.authorization.violation) {
      boundaryViolations.push(`${reading.automation_id} claims may_authorize=true.`);
    }
  }

  const unknownStates = automations.filter((a) => !a.state.known).map((a) => a.state.state);

  const stateCounts: Record<string, number> = {};
  for (const reading of automations) {
    const key = reading.state.state;
    stateCounts[key] = (stateCounts[key] ?? 0) + 1;
  }

  const unresolved: string[] = [];
  if (records.length === 0) {
    unresolved.push("No automations are recorded for this identity.");
  }
  for (const reading of automations) {
    for (const line of reading.unresolved) {
      unresolved.push(`${reading.automation_id}: ${line}`);
    }
  }
  if (unresolved.length === 0) {
    const runFilled = automations.reduce((n, a) => n + a.run_produced_clauses.length, 0);
    unresolved.push(
      runFilled > 0
        ? "Every grammar clause a definition can carry is filled. The run-produced clause(s) remain unfilled by design."
        : "Every grammar clause this record can carry is filled.",
    );
  }

  return {
    automations,
    declared_grammar: declaredGrammar,
    grammar_matches: grammarMatches,
    declared_states: declaredStates,
    final_transition: payloadGate,
    boundary_violations: boundaryViolations,
    unknown_states: unknownStates,
    state_counts: stateCounts,
    unresolved,
  };
}
