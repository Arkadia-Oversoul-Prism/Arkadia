/**
 * Engineering Lab — session read model (Workstream 4, feature-local).
 *
 * Reads the Lab's owner-scoped session contract and presents the governed
 * state ladder without collapsing it: a proposal is not an approval, an
 * approval is not an execution, an execution is not evidence, and a run that
 * reached the review boundary is not an accepted result.
 *
 * Read-only by construction. This module issues GET requests only. The
 * mutating Lab endpoints (open / authorize / execute / transition / run-agent)
 * are a human decision and are deliberately not wired here — the Lab's
 * "read-only capability ceiling" is a product boundary, not a missing feature.
 */
import { useState } from "react";
import { Panel, Facts, ContractState } from "../ui";
import { LabRunTrace } from "./LabRunTrace";
import type { LabEvidenceRecord, LabRunRecord, LabWorkEvent } from "./labRunTrace";
import { useHydration } from "../../lib/useHydration";
import { apiRequest } from "../../lib/apiClient";
import { endpoints } from "../../lib/endpoints";

export interface LabSession {
  session_id: string;
  subject_ref?: string;
  workspace_ref?: string;
  agent_id?: string;
  state: string;
  objective?: string;
  project_ref?: string | null;
  repository_ref?: string | null;
  authorization_ref?: string | null;
  created_at?: string;
  updated_at?: string;
}

export interface LabSessionView {
  session: LabSession;
  agent: unknown;
  runs: LabRunRecord[];
  events: LabWorkEvent[];
  evidence: LabEvidenceRecord[];
  artifacts: Array<Record<string, unknown>>;
  loop: string[];
  reached_review_boundary: boolean;
  human_decision_required: boolean;
}

/**
 * Display grouping for a session state. Derived from the Lab's own
 * `LEGAL_TRANSITIONS` vocabulary. This groups a *state* into the governance
 * stage it belongs to; it never asserts that a later stage has occurred.
 */
const STATE_STAGE: Record<string, { stage: string; note: string }> = {
  PROPOSED: { stage: "PROPOSAL", note: "Proposed — no authorization recorded." },
  AUTHORIZED: {
    stage: "AUTHORIZATION",
    note: "Authorized — a decision was recorded. A decision is not execution.",
  },
  QUEUED: { stage: "EXECUTION", note: "Queued for a bounded run." },
  RUNNING: { stage: "EXECUTION", note: "A bounded run is in progress." },
  CHECKPOINTED: { stage: "EXECUTION", note: "Run checkpointed; awaiting verification." },
  VERIFYING: { stage: "VERIFICATION", note: "Verification in progress." },
  READY_FOR_REVIEW: {
    stage: "REVIEW",
    note: "At the human review boundary. This is not acceptance.",
  },
  REVISION_REQUIRED: { stage: "REVIEW", note: "Revision required before review." },
  BLOCKED: { stage: "BLOCKED", note: "Blocked — a boundary or dependency stopped the work." },
  FAILED: { stage: "BLOCKED", note: "The run failed." },
  ABORTED: { stage: "TERMINAL", note: "Aborted." },
  EXPIRED: { stage: "TERMINAL", note: "Expired." },
  COMPLETED: { stage: "ACCEPTANCE", note: "Accepted by a human authority." },
};

export function sessionStage(state: string): { stage: string; note: string } {
  return STATE_STAGE[state] ?? { stage: "UNKNOWN", note: `Unrecognised state '${state}'.` };
}

/**
 * The session view is a sub-resource of the declared sessions collection. The
 * path is built inline at the call site rather than through a helper, so the
 * first argument of `useHydration` is literally the registry member — the
 * registry-contract guard requires that, and `lib/endpoints.ts` is workstream
 * 1's file (a first-class `labSession(id)` helper is the recorded request).
 */
function SessionDetail({ sessionId }: { sessionId: string }) {
  const view = useHydration<LabSessionView>(
    endpoints.labSessions + "/" + encodeURIComponent(sessionId),
    (p) => apiRequest<LabSessionView>(p),
  );

  if (view.state !== "ready" || !view.data) {
    return (
      <div className="mt-2">
        <ContractState state={view.state} error={view.error?.message} onRetry={view.reload} />
      </div>
    );
  }

  const { session, runs, events, evidence, artifacts, loop } = view.data;
  const { stage, note } = sessionStage(session.state);

  return (
    <div className="mt-2 rounded border border-line bg-ink/40 p-3">
      <Facts
        rows={[
          { label: "stage", value: `${stage} · ${session.state}` },
          { label: "objective", value: session.objective || "—" },
          { label: "workspace", value: session.workspace_ref ?? "—" },
          { label: "agent", value: session.agent_id ?? "—" },
          { label: "authorization", value: session.authorization_ref ?? "none recorded" },
          { label: "updated", value: session.updated_at ?? "—" },
        ]}
      />
      <p className="mt-3 text-xs text-white/50">{note}</p>

      <dl className="mt-3 grid grid-cols-4 gap-2 text-center">
        {[
          { label: "runs", value: runs.length },
          { label: "events", value: events.length },
          { label: "evidence", value: evidence.length },
          { label: "artifacts", value: artifacts.length },
        ].map((count) => (
          <div key={count.label} className="rounded border border-line/60 p-2">
            <dt className="font-mono text-[10px] uppercase tracking-wider text-white/40">{count.label}</dt>
            <dd className="text-lg text-white/85">{count.value}</dd>
          </div>
        ))}
      </dl>

      {view.data.reached_review_boundary && (
        <p className="mt-3 font-mono text-[11px] uppercase tracking-widest text-gold">
          Reached the review boundary · acceptance is a separate human act
        </p>
      )}

      <div className="mt-3 flex flex-col gap-3">
        <section>
          <p className="mb-1 font-mono text-[10px] uppercase tracking-wider text-white/40">
            execution records (runs)
          </p>
          {runs.length === 0 ? (
            <p className="text-xs text-white/45" data-testid="lab-runs-empty">
              No execution records. An authorized session is not an executed run.
            </p>
          ) : (
            <ul className="flex flex-col gap-1" data-testid="lab-runs">
              {runs.map((run, i) => (
                <li key={String(run.run_id ?? i)} className="font-mono text-[11px] text-white/65">
                  {String(run.run_id ?? "run")} · {String(run.state ?? "unknown")}
                  {run.result_state ? ` · ${String(run.result_state)}` : ""}
                </li>
              ))}
            </ul>
          )}
        </section>

        <section>
          <p className="mb-1 font-mono text-[10px] uppercase tracking-wider text-white/40">
            work events
          </p>
          {events.length === 0 ? (
            <p className="text-xs text-white/45" data-testid="lab-events-empty">
              No work events recorded. An event is a thing that happened, not a consequence.
            </p>
          ) : (
            <ul className="flex flex-col gap-1" data-testid="lab-events">
              {events.map((event, i) => (
                <li key={String(event.event_id ?? i)} className="font-mono text-[11px] text-white/55">
                  <span className="text-azure/80">{String(event.event_type ?? "event")}</span>
                  {typeof event.sequence === "number" ? ` · #${event.sequence}` : ""}
                  {event.timestamp_utc ? ` · ${String(event.timestamp_utc)}` : ""}
                </li>
              ))}
            </ul>
          )}
        </section>

        <section>
          <p className="mb-1 font-mono text-[10px] uppercase tracking-wider text-white/40">
            evidence records
          </p>
          {evidence.length === 0 ? (
            <p className="text-xs text-white/45" data-testid="lab-evidence-empty">
              No evidence records. Evidence is a record, not a verdict.
            </p>
          ) : (
            <ul className="flex flex-col gap-1" data-testid="lab-evidence">
              {evidence.map((record, i) => (
                <li key={String(record.evidence_id ?? i)} className="font-mono text-[11px] text-white/55">
                  {String(record.evidence_id ?? "evidence")} · {String(record.state ?? "recorded")} · not a verdict
                </li>
              ))}
            </ul>
          )}
        </section>
      </div>

      {loop.length > 0 && (
        <p className="mt-3 font-mono text-[10px] uppercase tracking-wider text-white/35">
          canonical loop: {loop.join(" → ")}
        </p>
      )}

      <div className="mt-4">
        <LabRunTrace view={view.data} />
      </div>
    </div>
  );
}

export function LabSessionList() {
  const sessions = useHydration<{ sessions: LabSession[] }>(endpoints.labSessions, (p) =>
    apiRequest<{ sessions: LabSession[] }>(p),
  );
  const [selected, setSelected] = useState<string | null>(null);
  const rows = sessions.data?.sessions ?? [];

  return (
    <Panel className="mb-4">
      <p className="mb-1 font-mono text-[11px] uppercase tracking-widest text-white/40">Lab sessions</p>
      <p className="mb-4 text-xs text-white/40">
        Read-only. A proposal is not an approval, an approval is not an execution, and a run at the
        review boundary is not an accepted result.
      </p>

      {sessions.state === "ready" ? (
        rows.length === 0 ? (
          <p className="text-sm text-white/50">No sessions for this identity.</p>
        ) : (
          <ul className="flex flex-col gap-2">
            {rows.map((s) => {
              const { stage } = sessionStage(s.state);
              const active = selected === s.session_id;
              return (
                <li key={s.session_id}>
                  <button
                    type="button"
                    onClick={() => setSelected(active ? null : s.session_id)}
                    aria-expanded={active}
                    data-testid={`lab-session-${s.session_id}`}
                    className={`w-full rounded border p-3 text-left font-mono text-xs transition ${
                      active ? "border-azure/50 bg-azure/5 text-white/90" : "border-line bg-ink/40 text-white/70"
                    }`}
                  >
                    <span className="text-azure">{stage}</span> · {s.state} · {s.objective || "no objective"}
                  </button>
                  {active && <SessionDetail sessionId={s.session_id} />}
                </li>
              );
            })}
          </ul>
        )
      ) : (
        <ContractState state={sessions.state} error={sessions.error?.message} onRetry={sessions.reload} />
      )}
    </Panel>
  );
}
