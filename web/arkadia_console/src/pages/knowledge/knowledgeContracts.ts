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
 * **The read is a bounded window, and it is the *newest* one.** `query()` selects
 * `ORDER BY id DESC LIMIT ? OFFSET ?` in a subquery and re-sorts ascending, so a
 * default read returns the newest `limit` events in chronological order. The last
 * row is therefore the log's newest event — the property the reader's `latest`
 * fact depends on — while `events[0]` is only the oldest event *still shown*.
 * `offset` pages backwards from the newest event into older history.
 *
 * Consequence for the reader: neither end of the list may be labelled as an
 * absolute of the log. `latest` is true; `first` is not, and this module offers
 * no such label. A saturated window holds older events beyond it, which the copy
 * below states rather than presenting a partial page as the complete log.
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
 *  - `unscoped`  a resolved anonymous viewer; the predicate is `1 = 0`, so a
 *                `[]` is a refusal to answer, not an empty log, and must not be
 *                shown as one;
 *  - `pending`   an identity that has not resolved yet. Firebase restores the
 *                session asynchronously, so the client is briefly neither
 *                signed in nor signed out. That state is not anonymity: the
 *                reader is owner-scoped, so it also answers `[]`, but the
 *                `unscoped` copy ("no identity is present") would be a claim the
 *                client cannot yet make about the viewer.
 */
export type TimelineScope = "owner" | "unscoped" | "pending";

/**
 * The viewer as this reader resolves it. It extends the shared `ViewerKind` with
 * the unresolved-identity state, which only surfaces that read a `1 = 0` scope
 * need to distinguish.
 */
export type TimelineViewer = ViewerKind | "pending";

export function classifyTimelineScope(viewer: TimelineViewer): TimelineScope {
  if (viewer === "authenticated") return "owner";
  return viewer === "pending" ? "pending" : "unscoped";
}

/**
 * Copy for a successful-but-empty read. The three scopes carry different
 * meanings and must never share wording: reporting a filtered `[]` as "no events
 * yet" is the exact failure this panel exists to avoid, and reporting an
 * unresolved session as a settled sign-out is the same class of error.
 */
export function emptyTimelineNotice(scope: TimelineScope): string {
  if (scope === "owner") {
    return "This node's timeline holds no events yet. The reader answered — this is an empty log, not a failed read.";
  }
  if (scope === "pending") {
    return "The reader is owner-scoped and your session is still resolving, so nothing was readable. This is not an empty log.";
  }
  return "The timeline is owner-scoped and no identity is present, so nothing was readable. This is not an empty log.";
}

/**
 * The window size the reader asks for. It matches the handler's default
 * (`Query(100, le=500)`) so the panel describes the page the backend actually
 * serves rather than an assumed one.
 */
export const TIMELINE_WINDOW_LIMIT = 100;

/** The bounded-window contract: what was asked for, and what came back. */
export interface TimelineWindow {
  /** How many events the reader asked the backend for. */
  limit: number;
  /** Events actually returned; `< limit` means the whole log is in the window. */
  returned: number;
}

/**
 * A bounded read is a window, not the whole log. Once the backend fills the
 * requested limit the window is *saturated*: older events exist beyond it, and
 * the reader must say so rather than presenting the page as the complete log.
 */
export function isWindowSaturated(window: TimelineWindow): boolean {
  return window.returned >= window.limit;
}

/**
 * Copy for the extent of the window. The reader returns the newest page, so
 * `events[0]` is the oldest event still visible — not the log's first event.
 */
export function timelineWindowNotice(window: TimelineWindow): string {
  return isWindowSaturated(window)
    ? `Showing the newest ${window.returned} events. The timeline holds older events beyond this window.`
    : `Showing all ${window.returned} events in this timeline.`;
}

/* ───────────────────────────────────────────────────────────────────────────
 * Knowledge timeline — paging backwards into older history
 *
 * `offset` pages *backwards from the newest event* (see the window contract
 * above): the default read is the newest `limit`, and `offset = shown` returns
 * the next page strictly older than everything already displayed. The reader
 * therefore accumulates pages toward the *past*, not the future — it has no
 * forward pager, because the newest window is already the present.
 *
 * Paging is a *bounded* control, not an "everything" control: each request asks
 * for at most `limit` more rows, and the reader stops when a page comes back
 * short of the limit, which is the backend's own signal that older history has
 * been exhausted.
 * ─────────────────────────────────────────────────────────────────────────── */

/** Whether the reader can still page further back, or has reached the start. */
export type OlderPage = "more" | "start";

/**
 * Decide the next paging state from the *last page fetched*. A page shorter than
 * the requested limit is the backend's signal that no older rows remain; a full
 * page means older history is still beyond it. The decision is made from the
 * response, never from an assumed log length.
 */
export function classifyOlderPage(returned: number, limit: number = TIMELINE_WINDOW_LIMIT): OlderPage {
  return returned >= limit ? "more" : "start";
}

/**
 * Merge an older page *beneath* the events already shown, dropping rows whose id
 * is already present. The drop is a de-duplication, not an ownership filter —
 * a repeated row would otherwise render twice if a caller re-requested an offset
 * it already held. The reader applies no ownership filter of its own.
 */
export function mergeOlderEvents(existing: TimelineEvent[], page: TimelineEvent[]): TimelineEvent[] {
  const seen = new Set(existing.map((event) => event.id));
  return [...page.filter((event) => !seen.has(event.id)), ...existing];
}

/** The offset the next older request must carry: how many rows are shown so far. */
export function olderOffset(shown: number): number {
  return shown;
}

/** Copy for the paging control. The two states must never share wording: one
 *  offers more history, the other states the history has been fully read. */
export function olderEventsNotice(page: OlderPage): string {
  return page === "more"
    ? "Older events exist beyond this window. Load them below — this never rewrites the events already shown."
    : "The start of the timeline has been reached; there are no older events to load.";
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

/* ───────────────────────────────────────────────────────────────────────────
 * Knowledge projects — GET /api/knowledge/projects
 *
 * Handler: `api.knowledge_routes.list_projects` -> `knowledge.vault.list_projects`.
 * Response: a bare list of project rows, `ORDER BY updated_at DESC`.
 *
 * Ownership here is the **third** shape in this subsystem, and it differs from
 * the timeline's: `knowledge.vault._project_owner_clause` is
 * `(user_id = ? OR user_id IS NULL)` when authenticated and `user_id IS NULL`
 * when anonymous. There *is* a public corpus on this reader, so an anonymous
 * caller legitimately reads projects — unlike the timeline, where the anonymous
 * scope is empty by construction.
 *
 * Consequence for the reader: a `[]` here is always a genuine empty read (the
 * public corpus is visible to everyone), while a *non-empty public-only* answer
 * for an authenticated viewer means their private projects are absent — which is
 * the boundary working, not a partial result. The two must not be conflated.
 *
 * The single-project read (`GET /api/knowledge/projects/{name_or_uuid}`) is
 * fail-closed: a non-owner receives `404`, not a distinguishable `403`.
 * ─────────────────────────────────────────────────────────────────────────── */

/** One project row, as `knowledge.vault.list_projects` returns it. */
export interface KnowledgeProject {
  id: number;
  uuid: string;
  name: string;
  description: string;
  /** The private owner stamp; `null` means the public corpus. */
  user_id: string | null;
  tags: string;
  status: string;
  created_at: string;
  updated_at: string;
}

/**
 * Structural guard for the declared payload. A bare list of rows carrying at
 * least an identity and an owner stamp; anything else is unrecognised.
 */
export function isKnowledgeProjects(value: unknown): value is KnowledgeProject[] {
  return (
    Array.isArray(value) &&
    value.every(
      (entry) =>
        typeof entry === "object" &&
        entry !== null &&
        typeof (entry as { name?: unknown }).name === "string" &&
        "user_id" in (entry as Record<string, unknown>),
    )
  );
}

/**
 * `public`  the readable set holds public-corpus projects only;
 * `scoped`  it holds the viewer's own private projects (and possibly public).
 *
 * There is no `empty` variant that is ambiguous here: unlike the timeline, the
 * public corpus is readable without identity, so a `[]` is a real empty read.
 */
export type ProjectScope = "public" | "scoped";

export function classifyProjectScope(projects: KnowledgeProject[]): ProjectScope {
  return projects.some((project) => project.user_id !== null && project.user_id !== undefined)
    ? "scoped"
    : "public";
}

export function projectNotice(scope: ProjectScope, viewer: ViewerKind): string | null {
  if (scope === "scoped") return null;
  if (viewer === "anonymous") {
    return "Signed-out view. The public corpus is readable; private projects are not part of this scope.";
  }
  return "Only public-corpus projects are readable in this scope; no private material is exposed here.";
}

/**
 * Structural guard for a *single* project row — the payload of
 * `GET /api/knowledge/projects/{name_or_uuid}` (`::get_project`). It is the same
 * row shape as the collection, without the list wrapper. An unrecognised body
 * (an error object, a wrapper, a bare string) must be an error the client does
 * not recognise — never a project the backend did not return.
 */
export function isKnowledgeProject(value: unknown): value is KnowledgeProject {
  return isKnowledgeProjects([value]);
}

/**
 * The single-project read is **fail-closed and deliberately indistinguishable**.
 * `knowledge.vault.get_project` applies the same ownership predicate as the
 * collection (`(user_id = ? OR user_id IS NULL)` authenticated, `user_id IS NULL`
 * anonymous), and `api.knowledge_routes.get_project` answers `404` when the
 * predicate matches no row.
 *
 * A `404` therefore means *either* "no such project" *or* "this project is not
 * readable by you" — the handler does not distinguish them, so neither may this
 * reader. Rendering a `404` as an ordinary transport error presents a real
 * boundary answer as a fault; guessing which of the two it was invents a fact
 * the contract withholds. Both are wrong, and the copy below says so.
 */
export function projectRefusalNotice(): string {
  return (
    "No project is readable at this address. The backend refuses a project the " +
    "caller cannot read with the same 404 as one that does not exist, so this " +
    "reader cannot tell the two apart — by design."
  );
}

/** Parse the `tags` column, which the reader stores as a JSON string. */
export function projectTags(project: KnowledgeProject): string[] {
  try {
    const parsed = JSON.parse(project.tags);
    return Array.isArray(parsed) ? parsed.filter((tag): tag is string => typeof tag === "string") : [];
  } catch {
    return [];
  }
}
