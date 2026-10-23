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
  labAutomations: "/api/lab/engineering/automations",
  labGateway: "/api/lab/engineering/gateway",
  labNAtlasCatalog: "/api/lab/engineering/n-atlas/catalog",

  solspireProjects: "/solspire/projects",
  approvals: "/api/approvals",

  /**
   * Voice / read-aloud. `POST /api/tts` returns an audio body, not JSON, so it
   * is read by `lib/voice.ts` rather than through `apiRequest`; the path is
   * still declared here so there is one API surface map (§3.1).
   *
   * `/api/tts/status` reports which engine will actually serve a request
   * (`edge_tts` when no ElevenLabs key is configured). It is the contract the
   * UI must read before claiming a voice quality: `aetheria` is declared
   * `requires_elevenlabs`, and without a key it silently falls back to the
   * Edge voice — a locked voice presented as available is a fabricated claim.
   */
  tts: "/api/tts",
  ttsStatus: "/api/tts/status",
  ttsVoices: "/api/tts/voices",
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

/**
 * `GET /api/lab/engineering/canvas/{artifact_id}` — the artifact canvas view
 * (owner-scoped). Handler verified at `api/lab_routes.py::get_canvas`.
 *
 * The served route is a **sibling** of `endpoints.labArtifacts`, not a
 * sub-resource of it: the backend declares `/engineering/artifacts` and
 * `/engineering/canvas/{artifact_id}` and does **not** serve
 * `/engineering/artifacts/{artifact_id}`. The canvas base is therefore derived
 * from the declared artifacts collection by replacing its terminal segment —
 * so the base cannot drift from the registry — rather than by declaring a
 * second collection entry for a path the app does not serve on its own
 * (`/engineering/canvas` alone is not a route).
 *
 * The substitution is asserted in the contract guard, so a registry rename
 * cannot turn this into a silent no-op that composes a 404.
 */
export function labCanvas(artifactId: string): string {
  return `${endpoints.labArtifacts.replace(/\/artifacts$/, "/canvas")}/${encodeURIComponent(artifactId)}`;
}

/**
 * `GET /solspire/projects/{project_id}/runtime-context` — the bounded project
 * runtime-context projection (owner-scoped). Handler verified at
 * `solspire/console_router.py::project_runtime_context`, mounted under the
 * `/solspire` router with `require_auth` + `require_project_owner`.
 *
 * The sub-resource is derived from the declared `solspireProjects` collection
 * so the base cannot drift from the registry, and the id is percent-encoded so
 * an id containing `/`, `?` or `#` cannot address a different route.
 */
export function solspireProjectRuntime(projectId: string): string {
  return `${endpoints.solspireProjects}/${encodeURIComponent(projectId)}/runtime-context`;
}
