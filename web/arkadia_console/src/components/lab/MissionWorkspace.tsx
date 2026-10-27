/**
 * The mission workspace: one complete, deterministic mission lifecycle.
 *
 * This is the wired vertical slice. It creates a real session, records a real
 * human authorization, executes a real bounded read-only investigation, and
 * renders the real evidence the substrate returned.
 *
 * Three boundaries this surface makes explicit rather than smooths over:
 *
 *  1. **The authority boundary is a step, not a dialog.** Authorization is a
 *     distinct button that calls a distinct endpoint. There is no "create and
 *     run" affordance, because that would collapse a human decision into a
 *     side effect.
 *  2. **The gate is demonstrated, not described.** Before authorizing, the
 *     operator can press Execute and watch the backend refuse with its own
 *     message. A boundary the user cannot observe is a claim.
 *  3. **A completed run is a proposal.** The terminal state is rendered as
 *     awaiting human review, never as success. Nothing here merges or deploys.
 */
import { useCallback, useState } from "react";
import { Panel } from "../ui";
import { ApiError } from "../../lib/apiClient";
import {
  AGENT_ROLES,
  READ_ONLY_ROLES,
  SESSION_STATE_MEANING,
  authorizeSession,
  createSession,
  executeBounded,
  getSessionView,
  registerAgent,
  type AgentRole,
  type LabAuthorization,
  type LabEvent,
  type LabRunResult,
  type LabSession,
  MISSION_WORKSPACE_REF,
} from "./missionContract";

type Phase = "idle" | "working";

interface StepRecord {
  label: string;
  detail: string;
  ok: boolean;
  at: string;
}

function stamp(): string {
  return new Date().toISOString().replace("T", " ").slice(0, 19);
}

function describeError(error: unknown): string {
  if (error instanceof ApiError) return `${error.status ?? "—"} ${error.kind}: ${error.message}`;
  return error instanceof Error ? error.message : String(error);
}

function StateChip({ state }: { state: string }) {
  const tone =
    state === "AUTHORIZED" || state === "VERIFIED"
      ? "border-emerald/40 text-emerald"
      : state === "BLOCKED"
        ? "border-red-400/40 text-red-300"
        : state === "VERIFYING" || state === "READY_FOR_REVIEW"
          ? "border-gold/40 text-gold"
          : "border-white/20 text-white/60";
  return (
    <span className={`rounded border px-2 py-0.5 font-mono text-[10px] uppercase tracking-widest ${tone}`}>
      {state}
    </span>
  );
}

export function MissionWorkspace() {
  const [phase, setPhase] = useState<Phase>("idle");
  const [role, setRole] = useState<AgentRole>("SENTINEL");
  const [objective, setObjective] = useState("Read-only investigation of repository entry points");
  const [targets, setTargets] = useState("README.md");

  const [agentId, setAgentId] = useState<string | null>(null);
  const [session, setSession] = useState<LabSession | null>(null);
  const [authorization, setAuthorization] = useState<LabAuthorization | null>(null);
  const [run, setRun] = useState<LabRunResult | null>(null);
  const [steps, setSteps] = useState<StepRecord[]>([]);
  const [backendEvents, setBackendEvents] = useState<LabEvent[]>([]);
  const [error, setError] = useState<string | null>(null);

  const note = useCallback((label: string, detail: string, ok = true) => {
    setSteps((prev) => [...prev, { label, detail, ok, at: stamp() }]);
  }, []);

  /** Pull the session view so the timeline shows the substrate's own events. */
  const refreshView = useCallback(async (sessionId: string) => {
    const view = await getSessionView(sessionId);
    if (view.session) setSession(view.session);
    setBackendEvents(view.events ?? []);
  }, []);

  const reset = useCallback(() => {
    setAgentId(null);
    setSession(null);
    setAuthorization(null);
    setRun(null);
    setSteps([]);
    setBackendEvents([]);
    setError(null);
  }, []);

  const targetList = targets
    .split(/[,\n]/)
    .map((t) => t.trim())
    .filter(Boolean);

  /** Step 1 — deploy a bounded agent. No agent receives implicit authority. */
  const onCreateAgent = useCallback(async () => {
    setPhase("working");
    setError(null);
    try {
      const agent = await registerAgent(role, `${role} mission agent`);
      setAgentId(agent.agent_id);
      note("Agent deployed", `${agent.agent_id} · role ${agent.role} · caps ${(agent.capabilities ?? []).join(",")}`);
    } catch (e) {
      setError(describeError(e));
      note("Agent deployment failed", describeError(e), false);
    } finally {
      setPhase("idle");
    }
  }, [role, note]);

  /** Step 2 — create the mission. It is created PROPOSED and cannot execute. */
  const onCreateSession = useCallback(async () => {
    if (!agentId) return;
    setPhase("working");
    setError(null);
    try {
      const created = await createSession(MISSION_WORKSPACE_REF, agentId, objective);
      setSession(created);
      note("Mission created", `${created.session_id} · state ${created.state}`);
      await refreshView(created.session_id);
    } catch (e) {
      setError(describeError(e));
      note("Mission creation failed", describeError(e), false);
    } finally {
      setPhase("idle");
    }
  }, [agentId, objective, note]);

  /**
   * Step 3 — attempt execution BEFORE authorization.
   *
   * This is deliberately available. The backend refuses with its own message,
   * and showing that refusal is the only way the operator sees the boundary
   * rather than reading about it.
   */
  const onExecuteUnauthorized = useCallback(async () => {
    if (!session) return;
    setPhase("working");
    setError(null);
    try {
      const result = await executeBounded(session.session_id, objective, targetList, ["read succeeds"]);
      // Reaching here means the gate did NOT hold — surface that loudly rather
      // than recording it as an ordinary step.
      setRun(result);
      note("BOUNDARY NOT ENFORCED", "execution succeeded without an authorization record", false);
    } catch (e) {
      const detail = describeError(e);
      note("Execution refused (expected)", detail, false);
    } finally {
      setPhase("idle");
    }
  }, [session, objective, targetList, note]);

  /** Step 4 — the human decision, recorded as its own act. */
  const onAuthorize = useCallback(async () => {
    if (!session) return;
    setPhase("working");
    setError(null);
    try {
      const result = await authorizeSession(session.session_id, ["read", "test"], 60);
      setAuthorization(result.authorization);
      setSession(result.session);
      await refreshView(result.session.session_id);
      note(
        "Authorization recorded",
        `${result.authorization.authorization_id} · originated_by ${result.authorization.originated_by} · ` +
          `merge ${String(result.authorization.merge)} · production ${String(result.authorization.production)}`,
      );
    } catch (e) {
      setError(describeError(e));
      note("Authorization failed", describeError(e), false);
    } finally {
      setPhase("idle");
    }
  }, [session, note]);

  /** Step 5 — bounded read-only execution. Stops at the review boundary. */
  const onExecute = useCallback(async () => {
    if (!session) return;
    setPhase("working");
    setError(null);
    try {
      const result = await executeBounded(session.session_id, objective, targetList, ["read succeeds"]);
      setRun(result);
      note(
        "Bounded run complete",
        `${result.run_id} · state ${result.state} · result ${result.result_state}`,
      );
      // Refresh so the timeline shows the substrate's own event stream and the
      // displayed state reflects the run that just happened.
      try {
        await refreshView(session.session_id);
      } catch {
        /* the run result is authoritative for this step; leave the state as-is */
      }
    } catch (e) {
      setError(describeError(e));
      note("Bounded run failed", describeError(e), false);
    } finally {
      setPhase("idle");
    }
  }, [session, objective, targetList, note, refreshView]);

  const busy = phase === "working";
  const canCreateSession = Boolean(agentId) && !session && !busy;
  const canAttempt = Boolean(session) && !authorization && !busy;
  const canAuthorize = Boolean(session) && !authorization && !busy;
  const canExecute = Boolean(session && authorization) && !run && !busy;

  return (
    <div className="space-y-4" data-testid="mission-workspace">
      <Panel>
        <div className="mb-3 flex items-center justify-between">
          <p className="font-mono text-[11px] uppercase tracking-widest text-white/40">Mission workspace</p>
          <button
            type="button"
            onClick={reset}
            disabled={busy || steps.length === 0}
            data-testid="mission-reset"
            className="font-mono text-[10px] uppercase tracking-widest text-white/40 hover:text-white/80 disabled:opacity-30"
          >
            Reset
          </button>
        </div>

        <div className="grid gap-3 md:grid-cols-2">
          <label className="block">
            <span className="font-mono text-[10px] uppercase tracking-widest text-white/40">Agent role</span>
            <select
              value={role}
              onChange={(e) => setRole(e.target.value as AgentRole)}
              disabled={Boolean(agentId) || busy}
              data-testid="mission-role"
              className="mt-1 w-full rounded border border-line bg-ink px-2 py-1.5 text-sm text-white disabled:opacity-50"
            >
              {AGENT_ROLES.map((r) => (
                <option key={r} value={r}>
                  {r}
                  {READ_ONLY_ROLES.includes(r) ? " (read-only)" : ""}
                </option>
              ))}
            </select>
          </label>

          <label className="block">
            <span className="font-mono text-[10px] uppercase tracking-widest text-white/40">
              Read targets (comma separated)
            </span>
            <input
              value={targets}
              onChange={(e) => setTargets(e.target.value)}
              disabled={Boolean(run) || busy}
              data-testid="mission-targets"
              className="mt-1 w-full rounded border border-line bg-ink px-2 py-1.5 font-mono text-xs text-white disabled:opacity-50"
            />
          </label>
        </div>

        <label className="mt-3 block">
          <span className="font-mono text-[10px] uppercase tracking-widest text-white/40">Objective</span>
          <input
            value={objective}
            onChange={(e) => setObjective(e.target.value)}
            disabled={Boolean(run) || busy}
            data-testid="mission-objective"
            className="mt-1 w-full rounded border border-line bg-ink px-2 py-1.5 text-sm text-white disabled:opacity-50"
          />
        </label>

        <div className="mt-4 flex flex-wrap gap-2">
          <button
            type="button"
            onClick={onCreateAgent}
            disabled={Boolean(agentId) || busy}
            data-testid="mission-deploy-agent"
            className="rounded border border-white/20 px-3 py-1.5 font-mono text-[10px] uppercase tracking-widest text-white/70 hover:border-white/40 disabled:opacity-30"
          >
            1 · Deploy agent
          </button>
          <button
            type="button"
            onClick={onCreateSession}
            disabled={!canCreateSession}
            data-testid="mission-create"
            className="rounded border border-white/20 px-3 py-1.5 font-mono text-[10px] uppercase tracking-widest text-white/70 hover:border-white/40 disabled:opacity-30"
          >
            2 · Create mission
          </button>
          <button
            type="button"
            onClick={onExecuteUnauthorized}
            disabled={!canAttempt}
            data-testid="mission-attempt"
            title="Attempts execution before authorization, to show the boundary refusing."
            className="rounded border border-amber-400/40 px-3 py-1.5 font-mono text-[10px] uppercase tracking-widest text-amber-300/90 hover:border-amber-400/70 disabled:opacity-30"
          >
            3 · Attempt before approval
          </button>
          <button
            type="button"
            onClick={onAuthorize}
            disabled={!canAuthorize}
            data-testid="mission-authorize"
            className="rounded border border-gold/50 px-3 py-1.5 font-mono text-[10px] uppercase tracking-widest text-gold hover:border-gold disabled:opacity-30"
          >
            4 · Record human approval
          </button>
          <button
            type="button"
            onClick={onExecute}
            disabled={!canExecute}
            data-testid="mission-execute"
            className="rounded border border-emerald/40 px-3 py-1.5 font-mono text-[10px] uppercase tracking-widest text-emerald hover:border-emerald/70 disabled:opacity-30"
          >
            5 · Execute bounded run
          </button>
        </div>

        {error ? (
          <p className="mt-3 rounded border border-red-400/30 bg-red-400/5 px-3 py-2 text-xs text-red-300" data-testid="mission-error">
            {error}
          </p>
        ) : null}

        <p className="mt-3 text-xs text-white/40">
          Step 3 is intentional. It calls the real execute endpoint before any approval exists so the backend's own
          refusal is visible. SESSION ≠ AUTHORIZATION: the substrate refuses a PROPOSED session.
        </p>
      </Panel>

      {session ? (
        <Panel>
          <p className="mb-3 font-mono text-[11px] uppercase tracking-widest text-white/40">Mission state</p>
          <dl className="grid gap-2 text-xs sm:grid-cols-2">
            <div>
              <dt className="font-mono text-[10px] uppercase tracking-widest text-white/35">session</dt>
              <dd className="font-mono text-white/80" data-testid="mission-session-id">{session.session_id}</dd>
            </div>
            <div>
              <dt className="font-mono text-[10px] uppercase tracking-widest text-white/35">state</dt>
              <dd className="mt-0.5"><span data-testid="mission-session-state"><StateChip state={session.state} /></span></dd>
            </div>
            <div>
              <dt className="font-mono text-[10px] uppercase tracking-widest text-white/35">agent</dt>
              <dd className="font-mono text-white/80">{session.agent_id}</dd>
            </div>
            <div>
              <dt className="font-mono text-[10px] uppercase tracking-widest text-white/35">authorization</dt>
              <dd className="font-mono text-white/80">{session.authorization_ref ?? "— none attached —"}</dd>
            </div>
          </dl>
          <p className="mt-3 text-xs text-white/45">
            {SESSION_STATE_MEANING[session.state] ?? "State reported verbatim by the substrate."}
          </p>
        </Panel>
      ) : null}

      <Panel>
        <p className="mb-3 font-mono text-[11px] uppercase tracking-widest text-white/40">
          Execution timeline — substrate events
        </p>
        {backendEvents.length === 0 ? (
          <p className="text-xs text-white/35">
            No substrate events yet. This panel reads the session's own event stream; it is empty until a mission
            exists.
          </p>
        ) : (
          <ol className="space-y-2" data-testid="mission-event-stream">
            {backendEvents.map((e) => (
              <li key={e.event_id} className="flex gap-3 text-xs">
                <span className="shrink-0 font-mono text-[10px] text-white/30">#{e.sequence}</span>
                <span className="shrink-0 font-mono text-[10px] uppercase tracking-widest text-azure">
                  {e.event_type}
                </span>
                <span className="min-w-0 break-words font-mono text-[11px] text-white/50">
                  {JSON.stringify(e.payload ?? {}).slice(0, 200)}
                </span>
              </li>
            ))}
          </ol>
        )}
        <p className="mt-3 text-xs text-white/35">
          These {backendEvents.length} events are recorded by the substrate, not narrated by this surface. The
          sequence is the backend's own.
        </p>
      </Panel>

      <Panel>
        <p className="mb-3 font-mono text-[11px] uppercase tracking-widest text-white/40">
          Operator actions — client record
        </p>
        {steps.length === 0 ? (
          <p className="text-xs text-white/35">No operator actions yet.</p>
        ) : (
          <ol className="space-y-2" data-testid="mission-timeline">
            {steps.map((s, i) => (
              <li key={`${s.at}-${i}`} className="flex gap-3 text-xs">
                <span className="shrink-0 font-mono text-[10px] text-white/30">{s.at}</span>
                <span
                  className={`shrink-0 font-mono text-[10px] uppercase tracking-widest ${
                    s.ok ? "text-emerald" : "text-amber-300"
                  }`}
                >
                  {s.label}
                </span>
                <span className="min-w-0 break-words font-mono text-[11px] text-white/60">{s.detail}</span>
              </li>
            ))}
          </ol>
        )}
      </Panel>

      {run ? (
        <Panel>
          <p className="mb-3 font-mono text-[11px] uppercase tracking-widest text-white/40">
            Evidence · {run.result_state}
          </p>
          <dl className="mb-3 grid gap-2 text-xs sm:grid-cols-3">
            <div>
              <dt className="font-mono text-[10px] uppercase tracking-widest text-white/35">run</dt>
              <dd className="font-mono text-white/80" data-testid="mission-run-id">{run.run_id}</dd>
            </div>
            <div>
              <dt className="font-mono text-[10px] uppercase tracking-widest text-white/35">state</dt>
              <dd className="mt-0.5"><StateChip state={run.state} /></dd>
            </div>
            <div>
              <dt className="font-mono text-[10px] uppercase tracking-widest text-white/35">evidence</dt>
              <dd className="font-mono text-white/80" data-testid="mission-evidence-ref">
                {(run.evidence_refs ?? []).join(", ") || "—"}
              </dd>
            </div>
          </dl>

          {(run.observations ?? []).length === 0 ? (
            <p className="text-xs text-white/35">The run recorded no observations.</p>
          ) : (
            <ul className="space-y-2">
              {(run.observations ?? []).map((o, i) => (
                <li key={i} className="rounded border border-line bg-ink/60 p-2">
                  <p className="font-mono text-[10px] uppercase tracking-widest text-white/40">
                    {o.kind} · {o.target ?? "—"} · {o.ok ? "ok" : "failed"}
                  </p>
                  {o.error ? (
                    <p className="mt-1 text-xs text-red-300">{o.error}</p>
                  ) : (
                    <pre className="mt-1 max-h-48 overflow-auto whitespace-pre-wrap break-words font-mono text-[11px] text-white/60">
                      {(o.content ?? "").slice(0, 4000) || "— empty —"}
                    </pre>
                  )}
                </li>
              ))}
            </ul>
          )}

          <p className="mt-3 rounded border border-gold/30 bg-gold/5 px-3 py-2 text-xs text-gold/90">
            This run reached <span className="font-mono">{run.state}</span> — a proposal awaiting human review. It is
            not an acceptance, and the substrate cannot merge, deploy, or self-authorize.
          </p>
        </Panel>
      ) : null}
    </div>
  );
}
