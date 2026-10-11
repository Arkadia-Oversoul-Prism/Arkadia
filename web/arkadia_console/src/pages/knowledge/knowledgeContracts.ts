/**
 * Knowledge OS — feature-local contract for the Knowledge Graph surface.
 *
 * This module is deliberately pure: it holds the shape of the declared
 * `/api/knowledge/graph` contract and the vocabulary that maps that contract
 * onto visible states. It owns no transport (the shared `apiClient` does), no
 * routing and no global shell. Keeping the classification here means the
 * "private material is not public corpus" distinction can be tested without a
 * DOM.
 *
 * Contract source: `GET /api/knowledge/graph` -> `knowledge.graph.full_graph_export`.
 * The endpoint applies an ownership predicate server-side; this module never
 * re-derives ownership from the payload, because a client-side filter cannot
 * prove a server-side boundary.
 */

/** The viewer's authorization context, as the backend would resolve it. */
export type ViewerKind = "anonymous" | "authenticated";

/** One note as the graph projection returns it. `user_id` is the private owner
 *  stamp; `null` means the public/legacy corpus. */
export interface GraphNode {
  id: number;
  uuid: string;
  title: string;
  note_type: string;
  project_id: number | null;
  created_at: string;
  user_id: string | null;
}

export interface GraphEdge {
  source_note_id: number;
  target_note_id: number;
  relationship: string;
  weight: number;
}

export interface KnowledgeGraphData {
  nodes: GraphNode[];
  edges: GraphEdge[];
}

export function emptyGraph(): KnowledgeGraphData {
  return { nodes: [], edges: [] };
}

/**
 * Structural guard for the declared payload.
 *
 * The transport returns `unknown` until it is validated. Without this, an
 * unrecognised body would either throw during render or read as a legitimate
 * `empty` scope — the "infer success from an empty response" failure. A shape
 * that does not match the declared contract is an error the client does not
 * recognise, and is surfaced as one.
 */
export function isKnowledgeGraphData(value: unknown): value is KnowledgeGraphData {
  if (typeof value !== "object" || value === null) return false;
  const candidate = value as { nodes?: unknown; edges?: unknown };
  return Array.isArray(candidate.nodes) && Array.isArray(candidate.edges);
}

/**
 * Distinguish the three cases that a raw node list collapses into one:
 *  - `empty`    the contract answered, the viewer's scope holds nothing;
 *  - `public`   the scope holds public-corpus nodes only;
 *  - `scoped`   the scope holds the viewer's own private nodes (and maybe public).
 *
 * `public` is not a weaker `scoped`: for an authenticated viewer a
 * public-only answer means their private material is absent from the response,
 * which is the boundary behaving correctly rather than a partial result.
 */
export type GraphScope = "empty" | "public" | "scoped";

export function classifyGraphScope(graph: KnowledgeGraphData): GraphScope {
  if (graph.nodes.length === 0) return "empty";
  return graph.nodes.some((node) => node.user_id !== null && node.user_id !== undefined)
    ? "scoped"
    : "public";
}

export interface GraphSummary {
  nodes: number;
  edges: number;
  scope: GraphScope;
  /** Node titles, capped for display. Never synthesised: titles come from the contract. */
  titles: string[];
}

const TITLE_LIMIT = 8;

export function summarizeGraph(graph: KnowledgeGraphData): GraphSummary {
  const scope = classifyGraphScope(graph);
  const titles = graph.nodes.slice(0, TITLE_LIMIT).map((node) => node.title);
  return { nodes: graph.nodes.length, edges: graph.edges.length, scope, titles };
}

/**
 * Copy shown when a viewer's scope holds no private nodes. Stated as a boundary,
 * not as an error: an anonymous viewer legitimately sees the public corpus only.
 */
export function scopeNotice(scope: GraphScope, viewer: ViewerKind): string | null {
  if (scope === "scoped") return null;
  if (viewer === "anonymous") {
    return "Signed-out view. The public corpus is readable; private material is not part of this scope.";
  }
  return scope === "empty"
    ? "No notes are readable in this scope yet."
    : "Only public-corpus notes are readable in this scope; no private material is exposed here.";
}

/* ───────────────────────────────────────────────────────────────────────────
 * Knowledge search — POST /api/knowledge/search
 *
 * The handler (`api.knowledge_routes.search` -> `knowledge.search.unified_search`)
 * returns a mapping of *mode name* to a list of records. The mode keys are not
 * fixed: `unified_search` emits only the modes it was asked for, and an
 * unrecognised key is simply another retrieved grouping. The moderator is
 * therefore "is this an object whose every value is an array", not a fixed key
 * list — a schema this client does not recognise must be an error, never a
 * silent empty result.
 * ─────────────────────────────────────────────────────────────────────────── */

export type SearchRecords = Record<string, unknown>[];
export type KnowledgeSearchData = Record<string, SearchRecords>;

/** Modes the handler advertises. `graph` is excluded: it needs a note anchor. */
export const SEARCH_MODES = [
  { id: "semantic", label: "Semantic" },
  { id: "fulltext", label: "Full text" },
  { id: "tag", label: "Tags" },
  { id: "timeline", label: "Timeline" },
  { id: "project", label: "Projects" },
  { id: "people", label: "People" },
  { id: "reference", label: "References" },
] as const;

export function isKnowledgeSearchData(value: unknown): value is KnowledgeSearchData {
  if (typeof value !== "object" || value === null || Array.isArray(value)) return false;
  return Object.values(value).every(Array.isArray);
}

/** Total retrieved records across every returned mode. */
export function countSearchRecords(data: KnowledgeSearchData): number {
  return Object.values(data).reduce((sum, records) => sum + records.length, 0);
}

/**
 * Read a display title from a retrieved record.
 *
 * Records arrive from heterogeneous modes (`notes`, `projects`, `people`,
 * `references`, `timeline` events), so there is no single title field. When no
 * known field carries one the record is labelled by its mode and index — a
 * *position*, never invented content. Fabricating a plausible title here would
 * present a record the backend did not return.
 */
export function recordTitle(record: Record<string, unknown>, mode: string, index: number): string {
  const candidates = ["title", "label", "name", "target_ref", "event_type", "vault_path"];
  for (const field of candidates) {
    const value = record[field];
    if (typeof value === "string" && value.trim()) return value;
  }
  return `${mode} record ${index + 1}`;
}

/** Secondary copy for a record, drawn only from fields the record carries. */
export function recordDetail(record: Record<string, unknown>): string {
  for (const field of ["content", "description", "payload", "target_ref"]) {
    const value = record[field];
    if (typeof value === "string" && value.trim()) return value;
    if (value !== undefined && value !== null && typeof value === "object") {
      return JSON.stringify(value);
    }
  }
  return "";
}

/* ───────────────────────────────────────────────────────────────────────────
 * Knowledge timeline — GET /api/knowledge/timeline
 *
 * Handler: `api.knowledge_routes.get_timeline` -> `knowledge.timeline.query`.
 * Query: `event_type`, `project_id`, `note_id`, `since`, `until`,
 * `limit` (default 100, `le=500`), `offset`; ascending by `id`.
 *
 * Ownership is *stricter* here than on the graph/search readers. The predicate
 * is `knowledge.timeline._timeline_owner_clause`: an authenticated caller gets
 * `user_id = ?` and an anonymous caller gets `1 = 0`. There is no public corpus
 * on this reader, so an anonymous answer is always `200 []`.
 *
 * That makes the transport status uninformative in the one case that matters:
 * `200 []` is what *both* "this owner has no events" and "this caller owns
 * nothing here" look like. The distinction is therefore derived from the
 * viewer's *identity* (a fact the client already holds), never from the
 * payload — the client cannot tell from a body whether the server filtered.
 * ─────────────────────────────────────────────────────────────────────────── */

/** One appended timeline event, as `knowledge.timeline.query` returns it. */
export interface TimelineEvent {
  id: number;
  event_type: string;
  /** JSON payload, decoded by the reader before it is serialised to HTTP. */
  payload: unknown;
  note_id: number | null;
  project_id: number | null;
  provider: string | null;
  persona: string | null;
  user_id: string | null;
  created_at: string;
}

/**
 * Structural guard for the declared payload.
 *
 * `query` returns a bare list. An unrecognised body (an error object, a single
 * event, a wrapper) must be an error the client does not recognise — never a
 * timeline that renders as empty, because "empty" is a real and meaningful
 * answer on this reader.
 */
export function isTimelineEvents(value: unknown): value is TimelineEvent[] {
  return (
    Array.isArray(value) &&
    value.every(
      (entry) =>
        typeof entry === "object" &&
        entry !== null &&
        typeof (entry as { id?: unknown }).id === "number" &&
        typeof (entry as { event_type?: unknown }).event_type === "string",
    )
  );
}

/**
 * The reader is owner-scoped, so the scope of an answer is a function of the
 * viewer, not of the payload:
 *  - `owner`     an authenticated viewer; a `[]` here means *their own* log is
 *                empty, which is a genuine empty read;
 *  - `unscoped`  an anonymous viewer; the predicate is `1 = 0`, so a `[]` is a
 *                refusal to answer, not an empty log, and must not be shown as
 *                one.
 */
export type TimelineScope = "owner" | "unscoped";

export function classifyTimelineScope(viewer: ViewerKind): TimelineScope {
  return viewer === "authenticated" ? "owner" : "unscoped";
}

/**
 * Copy for a successful-but-empty read. The two scopes carry opposite meanings
 * and must never share wording: reporting a filtered `[]` as "no events yet"
 * is the exact failure this panel exists to avoid.
 */
export function emptyTimelineNotice(scope: TimelineScope): string {
  return scope === "owner"
    ? "This node's timeline holds no events yet. The reader answered — this is an empty log, not a failed read."
    : "The timeline is owner-scoped and no identity is present, so nothing was readable. This is not an empty log.";
}

/** A short, non-invented label for an event: the fields its payload carries. */
export function timelineEventSummary(event: TimelineEvent): string {
  const payload = event.payload;
  if (payload !== null && typeof payload === "object") {
    const keys = Object.keys(payload as Record<string, unknown>);
    return keys.length > 0 ? keys.slice(0, 4).join(", ") : "—";
  }
  if (typeof payload === "string" && payload.trim()) return payload;
  return "—";
}

/**
 * The event types `knowledge.timeline.EVENT_TYPES` accepts. Offered as filter
 * choices so the control cannot request a type the reader does not know.
 */
export const TIMELINE_EVENT_TYPES = [
  "conversation",
  "prompt",
  "response",
  "knowledge_created",
  "knowledge_modified",
  "review",
  "decision",
  "sync",
  "error",
  "pipeline_run",
  "embed_complete",
  "graph_link",
  "search_query",
  "provider_call",
  "source_registered",
  "capture_recorded",
  "capture_bound",
] as const;
