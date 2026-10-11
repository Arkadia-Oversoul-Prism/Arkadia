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
  runs: Array<Record<string, unknown>>;
  events: Array<Record<string, unknown>>;
  evidence: Array<Record<string, unknown>>;
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
 * The session view is a sub-resource of the declared sessions collection. It is
 * built here rather than added to `lib/endpoints.ts` because that registry is
 * workstream 1's file and a second writer on it is a merge hazard — an interface
 * request for a first-class `labSession(id)` entry follows.
 */
function sessionViewPath(sessionId: string): string {
  return `${endpoints.labSessions}/${encodeURIComponent(sessionId)}`;
}

function SessionDetail({ sessionId }: { sessionId: string }) {
  const path = sessionViewPath(sessionId);
  const view = useHydration<LabSessionView>(path, (p) => apiRequest<LabSessionView>(p));

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

      {loop.length > 0 && (
        <p className="mt-3 font-mono text-[10px] uppercase tracking-wider text-white/35">
          canonical loop: {loop.join(" → ")}
        </p>
      )}
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
