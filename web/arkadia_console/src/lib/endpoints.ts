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
