/**
 * The mission contract: types and request bodies for the Lab session lifecycle.
 *
 * Every shape here is transcribed from the served handlers in
 * `api/lab_routes.py` — not inferred from the UI. The lifecycle is
 *
 *   register agent -> create session (PROPOSED) -> authorize (AUTHORIZED)
 *   -> execute (VERIFYING, stops at the review boundary) -> evidence
 *
 * Two facts the UI must not blur:
 *
 *  * `SESSION != AUTHORIZATION`. A session is created PROPOSED and the execute
 *    route refuses it with 400 until a human authorization is attached. The
 *    approval is a distinct recorded act, not a side effect of creating a
 *    session.
 *  * a run terminates at `VERIFYING` / `READY_FOR_REVIEW`. It is a proposal
 *    awaiting human review, never an acceptance. The substrate cannot merge,
 *    deploy, or self-authorize.
 */
import { apiRequest } from "../../lib/apiClient";
import { endpoints, labSession } from "../../lib/endpoints";

/**
 * A mutating sub-resource of a declared Lab session collection.
 *
 * Composed from `endpoints.labSessions` rather than written as a literal, so
 * the console's one endpoint registry stays the single source of these paths
 * (the registry-contract guard rejects a literal passed to `apiRequest`). The
 * id is percent-encoded so an id containing `/`, `?` or `#` cannot address a
 * different route.
 */
function sessionAction(sessionId: string, action: "authorize" | "execute" | "run-agent"): string {
  return `${endpoints.labSessions}/${encodeURIComponent(sessionId)}/${action}`;
}

/** Agent roles and their capability ceilings, from `lab/engineering_lab/models.py`. */
export const AGENT_ROLES = ["WEAVER", "BUILDER", "REVIEWER", "VISUALIST", "SENTINEL", "ARCHIVIST"] as const;
export type AgentRole = (typeof AGENT_ROLES)[number];

/** Read-only roles. A mission workspace that investigates must not deploy a
 *  write-capable agent, so the picker defaults to these. */
export const READ_ONLY_ROLES: readonly AgentRole[] = ["SENTINEL", "REVIEWER", "WEAVER", "ARCHIVIST"];

export interface LabAgent {
  agent_id: string;
  role: string;
  display_name: string;
  capabilities: string[];
  tool_access?: { tools?: string[]; write_allowed?: boolean };
}

export interface LabSession {
  session_id: string;
  subject_ref: string;
  workspace_ref: string;
  agent_id: string;
  state: string;
  objective: string;
  authorization_ref?: string | null;
  repository_ref?: string | null;
  created_at?: string;
  updated_at?: string;
}

export interface LabObservation {
  kind: string;
  target?: string;
  ok?: boolean;
  content?: string;
  error?: string;
}

export interface LabRunResult {
  run_id: string;
  session_id: string;
  state: string;
  result_state: string;
  summary?: string;
  observations?: LabObservation[];
  evidence_refs?: string[];
  artifact_refs?: string[];
}

export interface LabAuthorization {
  authorization_id: string;
  originated_by: string;
  scope_ref: string;
  operations_allowed: string[];
  duration_minutes: number;
  merge: boolean | string;
  production: boolean | string;
  merge_prohibited: boolean;
  production_prohibited: boolean;
  created_at: string;
}

/** Session states the substrate uses. Anything else is reported verbatim. */
export const SESSION_STATE_MEANING: Record<string, string> = {
  PROPOSED: "Created. No authorization attached — execution is refused.",
  AUTHORIZED: "A human authorization is attached. Bounded read-only execution is permitted.",
  QUEUED: "Queued for execution.",
  RUNNING: "A bounded run is in progress.",
  VERIFYING: "Run complete and awaiting human review. This is a proposal, not an acceptance.",
  READY_FOR_REVIEW: "Run complete and awaiting human review.",
  REVISION_REQUIRED: "A reviewer requested revision.",
  VERIFIED: "A human verified the result.",
  BLOCKED: "The run was blocked; see the evidence for the reason.",
};

export function registerAgent(role: AgentRole, displayName: string): Promise<LabAgent> {
  return apiRequest<LabAgent>(endpoints.labAgents, {
    method: "POST",
    body: JSON.stringify({ role, display_name: displayName }),
  });
}

export function createSession(workspaceRef: string, agentId: string, objective: string): Promise<LabSession> {
  return apiRequest<LabSession>(endpoints.labSessions, {
    method: "POST",
    body: JSON.stringify({ workspace_ref: workspaceRef, agent_id: agentId, objective }),
  });
}

export function authorizeSession(
  sessionId: string,
  operationsAllowed: string[],
  durationMinutes: number,
): Promise<{ authorization: LabAuthorization; session: LabSession }> {
  return apiRequest<{ authorization: LabAuthorization; session: LabSession }>(
    sessionAction(sessionId, "authorize"),
    {
      method: "POST",
      body: JSON.stringify({ operations_allowed: operationsAllowed, duration_minutes: durationMinutes }),
    },
  );
}

export function executeBounded(
  sessionId: string,
  objective: string,
  targets: string[],
  acceptance: string[],
): Promise<LabRunResult> {
  return apiRequest<LabRunResult>(
    sessionAction(sessionId, "execute"),
    {
      method: "POST",
      body: JSON.stringify({
        objective,
        // Read-only by construction: the mission workspace has no write control.
        operations: targets.map((target) => ({ kind: "read", target })),
        acceptance,
        requires_write: false,
      }),
    },
  );
}

/**
 * One bounded test operation on the existing execute route.
 *
 * The client contributes an optional selector only. It does not choose a
 * command: the server pins the allowlist and refuses anything else. A test
 * operation is not a write, a merge, or an acceptance, so `requires_write`
 * stays false. The returned `result_state` is the substrate's report — callers
 * must not relabel it as independent verification.
 */
export function executeBoundedTest(
  sessionId: string,
  objective: string,
  selector: string,
): Promise<LabRunResult> {
  return apiRequest<LabRunResult>(sessionAction(sessionId, "execute"), {
    method: "POST",
    body: JSON.stringify({
      objective,
      operations: [
        {
          kind: "test",
          target: selector.trim(),
          description: "bounded test operation",
        },
      ],
      acceptance: ["the substrate reports the test operation outcome"],
      requires_write: false,
    }),
  });
}

/**
 * Local mirror of the server selector rule, so an obviously illegal selector
 * is not sent.
 *
 * This is a preflight, not a result. The server remains the authority; a
 * refusal here means the request was not made.
 */
export function localTestSelectorRefusal(selector: string): string | null {
  const cleaned = selector.trim().replaceAll("\\", "/");
  if (!cleaned) return null;
  if (cleaned.length > 200) return "selector exceeds 200 characters";
  if (cleaned.startsWith("-")) {
    return "a selector names a test and must not start with '-'";
  }
  if (cleaned.startsWith("/")) return "selector must be relative to the workspace";
  const parts = cleaned.split("/");
  if (parts.some((part) => part === "" || part === "." || part === "..")) {
    return "selector must be a normalized relative path without '..'";
  }
  if (!/^[A-Za-z0-9_./*=:+\-\[\]]+$/.test(cleaned)) {
    return "selector contains characters outside the test-selector grammar";
  }
  return null;
}

export interface LabEvent {
  event_id: string;
  session_id: string;
  run_id?: string | null;
  event_type: string;
  sequence: number;
  payload?: Record<string, unknown>;
  timestamp_utc: string;
}

/**
 * P0.5 — dispatching a model-backed worker.
 *
 * `POST /sessions/{id}/run-agent` runs the native agent loop inside an already
 * authorized session. Two facts the shape keeps visible:
 *
 *  * `loop_state` / `loop_reason` say what actually happened. With no
 *    configured inference provider the loop stops `BLOCKED` with a reason —
 *    this surface must render that, not a simulated worker.
 *  * `effective_tools` is the tool envelope the server granted for *this*
 *    run. It is the observable form of the authorization, not an assumption.
 */
export interface LabDispatchTurn {
  turn_index: number;
  text?: string;
  tool_name?: string | null;
  tool_arguments?: Record<string, unknown>;
  observation?: Record<string, unknown> | null;
  decision?: string;
  timestamp_utc?: string;
}

export interface LabDispatchResult {
  run_id: string;
  session_id: string;
  state: string;
  result_state: string;
  summary?: string;
  loop_state?: string;
  loop_reason?: string;
  effective_tools?: string[];
  provider?: string;
  model?: string;
  evidence_refs?: string[];
  human_decision_required?: boolean;
  merge?: boolean;
  deploy?: boolean;
  self_authorized?: boolean;
  turns?: LabDispatchTurn[];
}

/**
 * Dispatch one bounded agent loop. Read-only by construction: the route
 * intersects capability, tool envelope and the recorded human authorization,
 * and the loop's tool registry contains no mutating tool.
 */
export function dispatchWorker(
  sessionId: string,
  objective: string,
  provider: string,
  maxTurns: number,
): Promise<LabDispatchResult> {
  return apiRequest<LabDispatchResult>(sessionAction(sessionId, "run-agent"), {
    method: "POST",
    body: JSON.stringify({
      objective,
      provider,
      max_turns: Math.max(1, Math.min(8, Math.trunc(maxTurns))),
    }),
  });
}

/** One provider row from `GET /engineering/gateway`. */
export interface LabProviderStatus {
  provider: string;
  model: string;
  config_class: string;
  configured: boolean;
  status: string;
  detail?: string;
  /** A concrete inference adapter is bound — describing ≠ calling. */
  adapter_bound?: boolean;
  /** configured + reachable + bound: a dispatch could actually be attempted. */
  dispatchable?: boolean;
}

export interface LabGatewayView {
  local_providers?: string[];
  remote_providers?: string[];
  agent_providers?: string[];
  catalog?: LabProviderStatus[];
}

/**
 * Provider availability, read from the gateway rather than assumed. The
 * surface renders `status` and `dispatchable` as separate facts: a provider
 * can be configured and reachable yet not dispatchable because no adapter is
 * bound — reporting only `AVAILABLE` would imply a worker that cannot run.
 */
export function getGatewayView(): Promise<LabGatewayView> {
  return apiRequest<LabGatewayView>(endpoints.labGateway);
}

/**
 * The full inspectable session view.
 *
 * `GET /api/lab/engineering/sessions/{id}` does **not** return a bare session:
 * `EngineeringLabRuntime.session_view` wraps it as
 * `{session, agent, runs, events, evidence, artifacts, loop, ...}`. Reading
 * `view.state` therefore yields `undefined`; the state lives at
 * `view.session.state`. Typing the wrapper explicitly is what keeps that
 * distinction visible at the call site.
 */
export interface LabSessionView {
  session: LabSession;
  agent?: LabAgent;
  runs?: Array<Record<string, unknown>>;
  events?: LabEvent[];
  evidence?: Array<Record<string, unknown>>;
  artifacts?: Array<Record<string, unknown>>;
  loop?: string[];
  reached_review_boundary?: boolean;
  human_decision_required?: boolean;
}

export function getSessionView(sessionId: string): Promise<LabSessionView> {
  return apiRequest<LabSessionView>(labSession(sessionId));
}

/**
 * The workspace this mission is bound to.
 *
 * The session record requires a `workspace_ref`, and the Lab enforces a
 * canonical workspace binding when a `project_ref` is present. This workspace
 * does not manage projects, so it presents a stable operator-scoped reference
 * rather than inventing a project binding it cannot verify.
 */
export const MISSION_WORKSPACE_REF = "workspace:engineering-lab-mission";

/**
 * The session id a mission workspace may offer to resume, per operator.
 *
 * Measured constraint: the substrate **retains** a session across a page
 * reload (a fresh token for the same uid reads it back; a different uid gets
 * `404`), but nothing *reads an authorization back* — `GET
 * /sessions/{id}/authorize` is `405`, there is no `/authorizations` route, and
 * the session view carries only `authorization_ref`, not the record. A resumed
 * workspace therefore restores the session and the substrate's own events, and
 * re-reads state from the server; it must never reconstruct an authorization
 * object from a stored id, because it cannot know the original
 * `originated_by` / `operations_allowed` / duration.
 *
 * Scoped by uid so a shared browser cannot offer one operator's session to
 * another. This is a convenience hint only: the server is the authority, and a
 * stale or foreign id is refused with `404` on read.
 */
export interface MissionSessionHint {
  session_id: string;
  objective?: string;
  targets?: string[];
}

const RESUME_KEY = "arkadia_engineering_lab_mission_session";

function resumeKey(uid: string): string {
  return `${RESUME_KEY}:${uid}`;
}

/**
 * Store a user-scoped resume hint. The server remains authoritative for the
 * session and objective; targets are a local scope hint because the served
 * session view does not include the original requested target list.
 */
export function rememberMissionSession(
  uid: string,
  sessionId: string,
  objective?: string,
  targets?: string[],
): void {
  try {
    const hint: MissionSessionHint = { session_id: sessionId };
    if (typeof objective === "string") hint.objective = objective;
    if (targets) hint.targets = targets;
    window.localStorage.setItem(resumeKey(uid), JSON.stringify(hint));
  } catch {
    /* storage unavailable — resume is a convenience, never a requirement */
  }
}

export function forgetMissionSession(uid: string): void {
  try {
    window.localStorage.removeItem(resumeKey(uid));
  } catch {
    /* see above */
  }
}

export function recallMissionSession(uid: string): MissionSessionHint | null {
  try {
    const stored = window.localStorage.getItem(resumeKey(uid));
    if (!stored) return null;
    try {
      const parsed: unknown = JSON.parse(stored);
      if (typeof parsed === "string" && parsed.length > 0) return { session_id: parsed };
      if (!parsed || typeof parsed !== "object" || Array.isArray(parsed)) return null;
      const candidate = parsed as Record<string, unknown>;
      if (typeof candidate.session_id !== "string" || candidate.session_id.length === 0) return null;
      return {
        session_id: candidate.session_id,
        objective: typeof candidate.objective === "string" ? candidate.objective : undefined,
        targets: Array.isArray(candidate.targets)
          ? candidate.targets.filter((target): target is string => typeof target === "string")
          : undefined,
      };
    } catch {
      // Backward compatibility: earlier versions stored only the raw session id.
      return { session_id: stored };
    }
  } catch {
    return null;
  }
}
