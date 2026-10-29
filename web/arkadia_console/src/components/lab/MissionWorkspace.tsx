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
 *  4. **A reload is not a reset.** The substrate retains the session, so the
 *     surface offers to resume it rather than silently presenting a blank form
 *     that hides a live mission. Resume restores only what the server will
 *     still confirm — it re-reads the view and never reconstructs an
 *     authorization from a stored id, because no route can read one back.
 */
import { useCallback, useEffect, useState } from "react";
import { Panel } from "../ui";
import { ApiError } from "../../lib/apiClient";
import { useAuth } from "../../contexts/AuthContext";
import {
  AGENT_ROLES,
  READ_ONLY_ROLES,
  SESSION_STATE_MEANING,
  authorizeSession,
  createSession,
  executeBounded,
  forgetMissionSession,
  getSessionView,
  recallMissionSession,
  registerAgent,
  rememberMissionSession,
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
  const { user } = useAuth();
  const uid = user?.uid ?? null;

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

  /** A retained session this operator could resume, if the server still serves
   *  it. Held separately from `session` so nothing renders as live until the
   *  server confirms it. */
  const [resumable, setResumable] = useState<string | null>(null);

  const note = useCallback((label: string, detail: string, ok = true) => {
    setSteps((prev) => [...prev, { label, detail, ok, at: stamp() }]);
  }, []);

  /** Pull the session view so the timeline shows the substrate's own events. */
  const refreshView = useCallback(async (sessionId: string) => {
    const view = await getSessionView(sessionId);
    if (view.session) setSession(view.session);
    setBackendEvents(view.events ?? []);
  }, []);

  /**
   * On mount, offer to resume a retained session.
   *
   * The id is only a hint. It is confirmed by a real read before it becomes
   * anything the operator can act on: a `404` (foreign, deleted, or an id from
   * another deployment) clears it silently, so a stale hint can never present a
   * mission that is not there. Nothing is reconstructed from storage — the
   * session, its state, and its events all come back from the server.
   */
  useEffect(() => {
    if (!uid) return;
    const retained = recallMissionSession(uid);
    if (!retained) return;
    let cancelled = false;
    getSessionView(retained)
      .then((view) => {
        if (cancelled || !view.session) return;
        setResumable(view.session.session_id);
      })
      .catch(() => {
        if (cancelled) return;
        forgetMissionSession(uid);
      });
    return () => {
      cancelled = true;
    };
  }, [uid]);

  /** Resume: adopt the retained session and re-read everything from the server.
   *
   *  The authorization is deliberately NOT restored. No route reads one back
   *  (`GET /sessions/{id}/authorize` is 405), so a resumed session shows its
   *  `authorization_ref` and its true state, and the authorize act stays
   *  available only if the state says the session is still PROPOSED. A run that
   *  already reached the review boundary stays there — the substrate refuses a
   *  second execution with its own message. */
  const onResume = useCallback(async () => {
    if (!uid || !resumable) return;
    setPhase("working");
    setError(null);
    try {
      const view = await getSessionView(resumable);
      setSession(view.session);
      setBackendEvents(view.events ?? []);
      setResumable(null);
      const runs = view.runs ?? [];
      const last = runs.length > 0 ? (runs[runs.length - 1] as unknown as LabRunResult) : null;
      if (last) setRun(last);
      note(
        "Mission resumed",
        `${view.session.session_id} · state ${view.session.state} · ` +
          `${runs.length} run(s) · ${(view.events ?? []).length} substrate event(s) · ` +
          `authorization ${view.session.authorization_ref ?? "none attached"}`,
      );
      if (view.session.authorization_ref && !last) {
        note(
          "Authorization not re-read",
          `${view.session.authorization_ref} is attached to this session, but no served route reads an ` +
            `authorization back. Its original terms are not reconstructed here.`,
          false,
        );
      }
    } catch (e) {
      const detail = describeError(e);
      setError(detail);
      forgetMissionSession(uid);
      setResumable(null);
      note("Resume failed", detail, false);
    } finally {
      setPhase("idle");
    }
  }, [uid, resumable, note]);

  /** Discard the resume hint without touching the session server-side. */
  const onDismissResume = useCallback(() => {
    if (uid) forgetMissionSession(uid);
    setResumable(null);
  }, [uid]);

  const reset = useCallback(() => {
    if (uid) forgetMissionSession(uid);
    setAgentId(null);
    setSession(null);
    setAuthorization(null);
    setRun(null);
    setSteps([]);
    setBackendEvents([]);
    setError(null);
  }, [uid]);

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
      if (uid) rememberMissionSession(uid, created.session_id);
      note("Mission created", `${created.session_id} · state ${created.state}`);
      await refreshView(created.session_id);
    } catch (e) {
      setError(describeError(e));
      note("Mission creation failed", describeError(e), false);
    } finally {
      setPhase("idle");
    }
  }, [agentId, objective, note, uid]);

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

  // "Has an authorization" must mean the SUBSTRATE says so, not that this
  // component recorded one. A resumed session carries `authorization_ref` while
  // the local authorization object is empty (no route can read one back). Keyed
  // off the local object, step 3 on a resumed AUTHORIZED session would execute
  // successfully and then report "BOUNDARY NOT ENFORCED" — a false alarm about
  // a gate that held.
  const sessionAuthorized = Boolean(session?.authorization_ref) || Boolean(authorization);
  const executableState = session?.state === "AUTHORIZED" || session?.state === "QUEUED";
  const busy = phase === "working";
  const nextDecision = (() => {
    if (busy) return "A bounded operation is in progress. Wait for the returned state before taking another action.";
    if (!agentId) return "Deploy a read-only agent to begin.";
    if (!session) return "Create a mission to capture intent and scope.";
    if (session.state === "READY_FOR_REVIEW") {
      return "Inspect the recorded events and evidence. This session is at the human-review boundary and cannot execute again.";
    }
    if (run) return "Inspect the returned evidence. Human acceptance remains a separate act.";
    if (executableState && sessionAuthorized) {
      return "Execute the bounded read-only run; the substrate reports this session as executable.";
    }
    if (session.state === "PROPOSED" && !sessionAuthorized) {
      return "Review the scope, then record explicit human authorization before execution.";
    }
    return `No next action is enabled for substrate state ${session.state}. Refresh the session or inspect its recorded events.`;
  })();
  const canCreateSession = Boolean(agentId) && !session && !busy;
  const canAttempt = Boolean(session) && !sessionAuthorized && !busy;
  const canAuthorize = Boolean(session) && !sessionAuthorized && !busy;
  const canExecute = Boolean(session) && sessionAuthorized && executableState && !run && !busy;

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

        <div
          className="mb-4 rounded-lg border border-gold/25 bg-gold/5 px-3 py-3"
          data-testid="mission-next-decision"
        >
          <p className="font-mono text-[10px] uppercase tracking-widest text-gold/80">Next decision</p>
          <p className="mt-1 text-sm leading-6 text-white/75">{nextDecision}</p>
        </div>

        {resumable ? (
          <div
            className="mb-3 rounded border border-azure/40 bg-azure/5 px-3 py-2"
            data-testid="mission-resume-offer"
          >
            <p className="text-xs text-white/70">
              A mission from a previous visit is still on the substrate:{" "}
              <span className="font-mono text-azure">{resumable}</span>. Resuming re-reads it from the server — it
              does not restore an authorization record, because no served route reads one back.
            </p>
            <div className="mt-2 flex flex-wrap gap-2">
              <button
                type="button"
                onClick={onResume}
                disabled={busy}
                data-testid="mission-resume"
                className="rounded border border-azure/50 px-3 py-1 font-mono text-[10px] uppercase tracking-widest text-azure hover:border-azure disabled:opacity-30"
              >
                Resume mission
              </button>
              <button
                type="button"
                onClick={onDismissResume}
                disabled={busy}
                data-testid="mission-resume-dismiss"
                className="rounded border border-white/20 px-3 py-1 font-mono text-[10px] uppercase tracking-widest text-white/50 hover:border-white/40 disabled:opacity-30"
              >
                Start fresh
              </button>
            </div>
          </div>
        ) : null}

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
