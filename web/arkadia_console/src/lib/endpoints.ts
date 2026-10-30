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

  solspireProjects: "/solspire/projects",
  solspireWorkspace: "/solspire/workspace",
  solspireWorkloads: "/solspire/workloads",
  solspirePulses: "/solspire/pulses",
  solspireSyntheses: "/solspire/syntheses",
  approvals: "/api/approvals",

  tts: "/api/tts",
  ttsStatus: "/api/tts/status",
  ttsVoices: "/api/tts/voices",
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
