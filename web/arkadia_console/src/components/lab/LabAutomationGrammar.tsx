/**
 * Engineering Lab — automation grammar read surface (Workstream 4, feature-local).
 *
 * Renders `endpoints.labAutomations` through the pure projection in
 * `labAutomationGrammar.ts`. The served contract is
 * `GET /api/lab/engineering/automations` → `{automations, grammar}`, owner-scoped.
 *
 * The substrate is explicit that an automation *prepares* consequential actions
 * and may never independently authorize them: the final transition is always the
 * human gate. This surface therefore renders the grammar chain clause by clause,
 * keeps the run-produced EVIDENCE clause visibly unfilled, and reports any
 * recorded claim of authority as a boundary violation rather than as state.
 *
 * Read-only by construction: GET only. Creating an automation
 * (`POST /engineering/automations`) and moving its state
 * (`POST /engineering/automations/{id}/state`) are mutating acts and stay unwired.
 */
import { Panel, Facts, ContractState } from "../ui";
import { useHydration } from "../../lib/useHydration";
import { apiRequest } from "../../lib/apiClient";
import { endpoints } from "../../lib/endpoints";
import {
  buildAutomationLedger,
  type AutomationPayload,
  type AutomationReading,
} from "./labAutomationGrammar";

function ClauseStrip({ reading }: { reading: AutomationReading }) {
  return (
    <ul className="mb-2 flex flex-wrap gap-1" data-testid={`lab-automation-clauses-${reading.automation_id}`}>
      {reading.clauses.map((clause) => (
        <li
          key={clause.clause}
          className={`rounded border px-2 py-0.5 font-mono text-[10px] uppercase tracking-wider ${
            clause.filled
              ? "border-azure/40 text-azure/80"
              : "border-line text-white/35"
          }`}
          title={clause.note}
          data-testid={`lab-automation-clause-${reading.automation_id}-${clause.clause}`}
          data-filled={clause.filled ? "true" : "false"}
        >
          {clause.clause}
          {clause.filled ? "" : " · unfilled"}
        </li>
      ))}
    </ul>
  );
}

function AutomationRow({ reading }: { reading: AutomationReading }) {
  return (
    <li
      className="rounded border border-line bg-ink/40 p-3"
      data-testid={`lab-automation-${reading.automation_id}`}
    >
      <p className="mb-2 font-mono text-xs text-white/80">
        <span className={reading.state.known ? "text-azure/80" : "text-white/45"}>
          {reading.state.state}
        </span>{" "}
        · {reading.name}
        {reading.state.human_gated ? (
          <span className="ml-2 text-[10px] uppercase tracking-wider text-white/45">human-gated</span>
        ) : null}
      </p>

      <ClauseStrip reading={reading} />

      <Facts
        rows={[
          { label: "trigger", value: reading.trigger.kind ?? "—" },
          { label: "schedule", value: reading.trigger.schedule ?? "—" },
          { label: "event", value: reading.trigger.event ?? "—" },
          { label: "agent role", value: reading.agent_role ?? "—" },
          { label: "tools", value: reading.tools.join(" · ") || "none declared" },
          { label: "sandbox write", value: reading.sandbox_write_allowed ? "allowed" : "not allowed" },
          { label: "notification", value: reading.notification_target },
        ]}
      />

      <p className="mt-2 text-[11px] text-white/45">{reading.state.note}</p>

      {reading.authorization.violation ? (
        <p
          className="mt-2 rounded border border-red-500/40 p-2 text-[11px] text-red-300/80"
          data-testid={`lab-automation-violation-${reading.automation_id}`}
        >
          Boundary violation: {reading.authorization.note}
        </p>
      ) : null}

      {reading.unresolved.length > 0 ? (
        <ul
          className="mt-2 flex flex-col gap-1 text-[11px] text-white/45"
          data-testid={`lab-automation-unresolved-${reading.automation_id}`}
        >
          {reading.unresolved.map((line) => (
            <li key={line}>{line}</li>
          ))}
        </ul>
      ) : null}
    </li>
  );
}

export function LabAutomationGrammar() {
  const automations = useHydration<AutomationPayload>(endpoints.labAutomations, (p) =>
    apiRequest<AutomationPayload>(p),
  );

  if (automations.state !== "ready") {
    return (
      <Panel className="mb-4">
        <p className="mb-3 font-mono text-[11px] uppercase tracking-widest text-white/40">
          Native automations
        </p>
        <ContractState
          state={automations.state}
          error={automations.error?.message}
          onRetry={automations.reload}
        />
      </Panel>
    );
  }

  const ledger = buildAutomationLedger(automations.data);

  return (
    <Panel className="mb-4">
      <p className="mb-1 font-mono text-[11px] uppercase tracking-widest text-white/40">
        Native automations
      </p>
      <p className="mb-4 text-xs text-white/40">
        An automation prepares consequential actions; it never authorizes them. The grammar chain ends
        at the human gate, and a clause the definition cannot carry stays visibly unfilled rather than
        assumed.
      </p>

      <div className="mb-3" data-testid="lab-automation-grammar">
        <p className="mb-1 font-mono text-[10px] uppercase tracking-widest text-white/35">
          grammar chain
        </p>
        <p className="font-mono text-[11px] text-white/60">
          {ledger.declared_grammar.join(" → ") || "(not declared)"}
        </p>
        {!ledger.grammar_matches ? (
          <p className="mt-1 text-[11px] text-red-300/80" data-testid="lab-automation-grammar-mismatch">
            The served grammar chain is not the rendered chain. Reported, not reconciled.
          </p>
        ) : null}
        <p className="mt-1 text-[11px] text-white/45">
          final transition: {ledger.final_transition ?? "not declared"} · an automation may prepare a
          consequential action and may never authorize one
        </p>
      </div>

      {ledger.boundary_violations.length > 0 ? (
        <ul
          className="mb-3 rounded border border-red-500/40 p-2 text-[11px] text-red-300/80"
          data-testid="lab-automation-boundary-violations"
        >
          {ledger.boundary_violations.map((line) => (
            <li key={line}>{line}</li>
          ))}
        </ul>
      ) : null}

      {ledger.automations.length === 0 ? (
        <p className="text-sm text-white/50" data-testid="lab-automations-empty">
          No automations are recorded for this identity. Creating one is a mutating act and is not
          wired to this read-only surface.
        </p>
      ) : (
        <ul className="flex flex-col gap-2" data-testid="lab-automations">
          {ledger.automations.map((reading) => (
            <AutomationRow key={reading.automation_id} reading={reading} />
          ))}
        </ul>
      )}
    </Panel>
  );
}
