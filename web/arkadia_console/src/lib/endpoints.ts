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
  arkanaThreads: "/api/commune/threads",

  transmissions: "/api/transmissions",
  echoes: "/api/echoes",

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
  labGateway: "/api/lab/engineering/gateway",
  labNAtlasCatalog: "/api/lab/engineering/n-atlas/catalog",

  solspireProjects: "/solspire/projects",
  approvals: "/api/approvals",
} as const;

export type EndpointName = keyof typeof endpoints;

/**
 * Path builders for a parameterized sub-resource of a declared collection.
 *
 * A sub-resource is derived from its collection entry so the base path cannot
 * drift from the registry, and each path parameter is percent-encoded so an id
 * containing `/`, `?` or `#` cannot address a different route. Declared here
 * (not in a feature module) so there is still one endpoint registry.
 */

/**
 * `GET /api/lab/engineering/sessions/{session_id}` — the Engineering Lab
 * session view (owner-scoped). Handler verified at `api/lab_routes.py`.
 */
export function labSession(sessionId: string): string {
  return `${endpoints.labSessions}/${encodeURIComponent(sessionId)}`;
}
