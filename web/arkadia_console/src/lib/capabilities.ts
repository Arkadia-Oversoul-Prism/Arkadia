/**
 * Capability registry — the conversational workspace's map of what Arkana can
 * actually reach.
 *
 * This is a *declaration of verified contracts*, not a wish list. Every entry
 * names the endpoint it calls and the surface that already reads it, so a
 * capability cannot be advertised in the composer without a real route behind
 * it. An entry whose contract is not yet serviceable carries
 * `status: "unverified"` and the composer renders it as unavailable rather than
 * offering a control that would fail.
 *
 * The registry is deliberately separate from `endpoints.ts`: that module owns
 * *paths*, this one owns *capability semantics* (what a user can ask for, which
 * authority boundary applies, and whether the contract is proven). A path change
 * is one edit in `endpoints.ts`; a capability change is one edit here.
 */
import {
  endpoints,
  solspireProjectTasks,
  solspireProjectFiles,
  solspireProjectEvents,
} from "./endpoints";

export type CapabilityDomain =
  | "engineering"
  | "knowledge"
  | "missions"
  | "workspace";

export type CapabilityStatus = "verified" | "unverified";

export interface Capability {
  /** Stable id used by the composer's capability tokens. */
  id: string;
  /** The token a user types in the composer, without the leading `@`. */
  token: string;
  label: string;
  domain: CapabilityDomain;
  /** What asking for this actually does, in the user's terms. */
  summary: string;
  /**
   * The endpoint this capability dispatches to. A parameterised sub-resource
   * carries the builder from `endpoints.ts` rather than a hand-written path, so
   * the registry cannot drift from the one path map.
   */
  endpoint: string | ((id: string) => string);
  /** The surface that already reads the same contract (proves it is wired). */
  surface: string;
  /**
   * True when the capability can change state and therefore crosses an
   * authorization boundary. The composer marks these and the workspace never
   * dispatches one without a linked human grant.
   */
  consequential: boolean;
  status: CapabilityStatus;
  /** Why an unverified capability is not yet offered. */
  note?: string;
}

export const CAPABILITIES: Capability[] = [
  {
    id: "knowledge.search",
    token: "knowledge",
    label: "Knowledge OS search",
    domain: "knowledge",
    summary: "Search the accessible Knowledge OS corpus and keep the retrieved records visible as evidence.",
    endpoint: endpoints.knowledgeSearch,
    surface: "Arkana (research mode)",
    consequential: false,
    status: "verified",
  },
  {
    id: "knowledge.graph",
    token: "graph",
    label: "Knowledge graph",
    domain: "knowledge",
    summary: "Read the knowledge graph and its relationships for the current scope.",
    endpoint: endpoints.knowledgeGraph,
    surface: "Knowledge OS",
    consequential: false,
    status: "verified",
  },
  {
    id: "project.list",
    token: "projects",
    label: "Projects",
    domain: "workspace",
    summary: "List the projects this identity can see, with their status and activity.",
    endpoint: endpoints.solspireProjects,
    surface: "Projects",
    consequential: false,
    status: "verified",
  },
  {
    id: "project.tasks",
    token: "tasks",
    label: "Project tasks",
    domain: "workspace",
    summary: "Read the task list attached to the selected project.",
    endpoint: solspireProjectTasks,
    surface: "Projects",
    consequential: false,
    status: "verified",
  },
  {
    id: "project.files",
    token: "files",
    label: "Project files",
    domain: "workspace",
    summary: "Read the files and artifacts attached to the selected project.",
    endpoint: solspireProjectFiles,
    surface: "Projects",
    consequential: false,
    status: "verified",
  },
  {
    id: "project.events",
    token: "activity",
    label: "Project activity",
    domain: "workspace",
    summary: "Read the project's activity stream — what happened, in order.",
    endpoint: solspireProjectEvents,
    surface: "Projects",
    consequential: false,
    status: "verified",
  },
  {
    id: "lab.sessions",
    token: "lab",
    label: "Engineering Lab sessions",
    domain: "engineering",
    summary: "List engineering sessions and their bounded execution state.",
    endpoint: endpoints.labSessions,
    surface: "Engineering Lab",
    consequential: false,
    status: "verified",
  },
  {
    id: "lab.artifacts",
    token: "artifacts",
    label: "Lab artifacts",
    domain: "engineering",
    summary: "Read the artifacts a session produced, with their evidence.",
    endpoint: endpoints.labArtifacts,
    surface: "Engineering Lab",
    consequential: false,
    status: "verified",
  },
  {
    id: "lab.repository",
    token: "repo",
    label: "Repository state",
    domain: "engineering",
    summary: "Read the repository revision, branch and working state the Lab observes.",
    endpoint: endpoints.labRepository,
    surface: "Engineering Lab",
    consequential: false,
    status: "verified",
  },
  {
    id: "lab.authorize",
    token: "authorize",
    label: "Authorize a session operation",
    domain: "engineering",
    summary: "Record a human authorization naming the operations a session may perform. This is a human act, never an agent one.",
    endpoint: endpoints.labSessions,
    surface: "Engineering Lab",
    consequential: true,
    status: "verified",
  },
  {
    id: "lab.execute",
    token: "execute",
    label: "Execute a bounded operation",
    domain: "engineering",
    summary: "Dispatch a bounded write/run/test inside the session sandbox. Refused unless a usable, session-scoped grant names the operation.",
    endpoint: endpoints.labSessions,
    surface: "Engineering Lab",
    consequential: true,
    status: "verified",
  },
  {
    id: "weaver.workloads",
    token: "weaver",
    label: "Weaver workloads",
    domain: "missions",
    summary: "Read governed workloads and their execution status.",
    endpoint: endpoints.solspireWorkloads,
    surface: "Weaver",
    consequential: false,
    status: "verified",
  },
  {
    id: "approvals.pending",
    token: "approvals",
    label: "Pending approvals",
    domain: "missions",
    summary: "Read the approvals waiting on a human decision. Reading is not deciding.",
    endpoint: endpoints.approvals,
    surface: "Weaver",
    consequential: false,
    status: "verified",
  },
  {
    id: "mission.lifecycle",
    token: "mission",
    label: "Mission lifecycle",
    domain: "missions",
    summary: "Drive a mission through understand → propose → authorize → execute → verify, with each stage a separate recorded act.",
    endpoint: "/solspire/voice/events",
    surface: "not yet wired in the console",
    consequential: true,
    status: "unverified",
    note: "The backend chain exists (solspire/voice_router.py) but no console surface reads it yet, so the composer does not offer it.",
  },
  {
    id: "project.conversations",
    token: "conversation",
    label: "Project conversations",
    domain: "workspace",
    summary: "Persist a conversation turn against a project, so the thread survives a reload and stays attached to its work.",
    endpoint: "/solspire/projects/{project_id}/conversations",
    surface: "not yet wired in the console",
    consequential: false,
    status: "unverified",
    note: "The route and the server-side bridge exist (solspire/conversation_bridge.py); the console has no adapter yet.",
  },
];

export const CAPABILITY_BY_TOKEN: Record<string, Capability> = Object.fromEntries(
  CAPABILITIES.map((c) => [c.token, c]),
);

export const CAPABILITY_DOMAINS: Array<{ id: CapabilityDomain; label: string }> = [
  { id: "engineering", label: "Engineering" },
  { id: "knowledge", label: "Knowledge & cognition" },
  { id: "missions", label: "Missions & orchestration" },
  { id: "workspace", label: "Personal workspace" },
];

/**
 * The composer's capability tokens.
 *
 * These are a **proposed interaction convention**, not an implemented backend
 * feature: typing `@repo` does not itself call anything. The token selects the
 * capability the turn is scoped to, and the workspace dispatches through the
 * registry entry above — which is why an unverified entry is shown as
 * unavailable rather than silently accepted.
 */
export const COMPOSER_TOKENS = CAPABILITIES.filter((c) => c.status === "verified").map(
  (c) => c.token,
);
