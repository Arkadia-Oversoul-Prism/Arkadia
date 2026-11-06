/**
 * Canonical API surface map.
 *
 * These paths are read directly from the deployed FastAPI application (see
 * `GET /openapi.json`). Surfaces reference the map; they do not inline paths,
 * so a contract change is a single edit here.
 */
export const endpoints = {
  version: "/api/version",
  health: "/health",

  me: "/api/me",
  codex: "/api/me/codex",
  identitySpine: "/api/me/identity-spine",
  field: "/api/me/field",

  arkanaResonance: "/api/commune/resonance",
  /** A2 SSE stream — additive; JSON resonance remains authoritative for non-stream clients. */
  arkanaResonanceStream: "/api/commune/resonance/stream",
  arkanaThreads: "/api/commune/threads",

  transmissions: "/api/transmissions",
  echoes: "/api/echoes",

  publicCodex: "/api/codex",
  stellarCartography: "/api/stellar-cartography",

  knowledgeStatus: "/api/knowledge/status",
  knowledgeGraph: "/api/knowledge/graph",
  knowledgeTimeline: "/api/knowledge/timeline",
  knowledgeProjects: "/api/knowledge/projects",
  knowledgeSearch: "/api/knowledge/search",

  labOverview: "/api/lab/overview",
  labEngineeringOverview: "/api/lab/engineering/overview",
  labSessions: "/api/lab/engineering/sessions",
  labAgents: "/api/lab/engineering/agents",
  labArtifacts: "/api/lab/engineering/artifacts",
  labAutomations: "/api/lab/engineering/automations",
  labGateway: "/api/lab/engineering/gateway",
  labNAtlasCatalog: "/api/lab/engineering/n-atlas/catalog",
  labRepository: "/api/lab/engineering/repository",
  labEngineeringPr: "/api/lab/engineering/pr/{number}",

  solspireProjects: "/solspire/projects",
  solspireWorkspace: "/solspire/workspace",
  aisProfile: "/api/me/ais-profile",
  sources: "/api/sources",
  knowledgeProviders: "/api/knowledge/providers",
  providerKeys: "/api/provider-keys",
  solspireWorkloads: "/solspire/workloads",
  solspirePulses: "/solspire/pulses",
  solspireSyntheses: "/solspire/syntheses",
  approvals: "/api/approvals",

  tts: "/api/tts",
  ttsStatus: "/api/tts/status",
  ttsVoices: "/api/tts/voices",

  /** Arkadia Voice — the governed mission lifecycle chain (solspire/voice_router.py). */
  voiceStatus: "/solspire/voice/status",
  voiceEvents: "/solspire/voice/events",
} as const;

export type EndpointName = keyof typeof endpoints;

export function labSession(sessionId: string): string {
  return `${endpoints.labSessions}/${encodeURIComponent(sessionId)}`;
}

export function labCanvas(artifactId: string): string {
  return `${endpoints.labArtifacts.replace(/\/artifacts$/, "/canvas")}/${encodeURIComponent(artifactId)}`;
}

export function solspireProjectRuntime(projectId: string): string {
  return `${endpoints.solspireProjects}/${encodeURIComponent(projectId)}/runtime-context`;
}

/** The canonical path of one project record. */
export function solspireProject(projectId: string): string {
  return `${endpoints.solspireProjects}/${encodeURIComponent(projectId)}`;
}

/** The project's task list. */
export function solspireProjectTasks(projectId: string): string {
  return `${solspireProject(projectId)}/tasks`;
}

/** The project's file/artifact list. */
export function solspireProjectFiles(projectId: string): string {
  return `${solspireProject(projectId)}/files`;
}

/** The project's activity (event) stream. */
export function solspireProjectEvents(projectId: string): string {
  return `${solspireProject(projectId)}/events`;
}

/**
 * The project's conversation collection.
 *
 * Served by `solspire/console_router.py` (`GET`/`POST
 * /projects/{project_id}/conversations`), guarded by `require_project_owner`.
 * A conversation created here is the canonical project record; the Knowledge OS
 * thread is derived from it by `solspire/conversation_bridge.py`, never the
 * other way round.
 */
export function solspireProjectConversations(projectId: string): string {
  return `${solspireProject(projectId)}/conversations`;
}

/** One project conversation, addressed by its canonical UUID. */
export function solspireProjectConversation(projectId: string, convId: string): string {
  return `${solspireProjectConversations(projectId)}/${encodeURIComponent(convId)}`;
}

/**
 * The turn-append sub-resource of one project conversation.
 *
 * This is the route that composes a turn across the existing substrates
 * (`append_conversation_turn`): the project conversation record, the Knowledge
 * OS thread/note, and the project activity event. It is the only write path the
 * console uses to persist a conversation turn, so no second store is created.
 */
export function solspireProjectConversationMessages(projectId: string, convId: string): string {
  return `${solspireProjectConversation(projectId, convId)}/messages`;
}

/** One voice event (the governed mission conversation), addressed by its canonical id. */
export function voiceEvent(eventId: string): string {
  return `${endpoints.voiceEvents}/${encodeURIComponent(eventId)}`;
}

/** The inspectable causal evidence chain of one voice event. */
export function voiceEventChain(eventId: string): string {
  return `${voiceEvent(eventId)}/chain`;
}

/**
 * The voice events of one conversation session, newest first.
 *
 * Derived from the declared `voiceEvents` collection so the base cannot drift,
 * and the session id is percent-encoded so an id containing `/` cannot address
 * another route.
 */
export function voiceEventsForSession(sessionId: string, limit = 1): string {
  return `${endpoints.voiceEvents}?session_id=${encodeURIComponent(sessionId)}&limit=${limit}`;
}
