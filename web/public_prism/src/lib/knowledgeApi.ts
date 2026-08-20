/**
 * Arkadia Knowledge OS — Frontend API Client
 * All calls to /api/knowledge/* live here.
 */

import { API_BASE as API_BASE_CFG } from './apiConfig';

const API_BASE = API_BASE_CFG.replace(/\/$/, '');

/** Optional Bearer token for user-scoped Knowledge OS reads/writes. */
let _authToken: string | null = null;
export function setKnowledgeAuthToken(token: string | null) {
  _authToken = token;
}

async function fetchJSON<T>(path: string, options?: RequestInit): Promise<T> {
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    ...(options?.headers as Record<string, string> || {}),
  };
  if (_authToken && !headers['Authorization']) {
    headers['Authorization'] = `Bearer ${_authToken}`;
  }
  const res = await fetch(`${API_BASE}${path}`, {
    ...options,
    headers,
  });
  if (!res.ok) throw new Error(`${res.status} ${res.statusText}`);
  return res.json() as Promise<T>;
}

// ── Status ────────────────────────────────────────────────────────────────────
export interface KnowledgeStatus {
  status: string;
  vault: { notes: number; projects: number; chunks: number; embeddings: number; pending_embeddings: number };
  graph: { edges: number };
  timeline: { events: number };
  // Extended (K3-B)
  ontology?: { version: string; node_types_count: number; relationship_types_count: number };
  graph_version?: string;
  nodes_by_type?: Record<string, number>;
  relationships_by_type?: Record<string, number>;
  graph_density?: number;
  graph_health?: 'ok' | 'warn' | 'error';
  indexing_status?: { complete: number; pending: number; partial: number; failed: number };
  last_ingestion?: string | null;
  growth?: { notes_last_7d: number; edges_last_7d: number };
}
export const getStatus = () => fetchJSON<KnowledgeStatus>('/api/knowledge/status');

// ── Relationships analytics ───────────────────────────────────────────────────
export interface RelationshipEntry {
  type: string; display_name: string; direction: string; count: number;
}
export interface TopNode {
  id: number; title: string; note_type: string; degree: number;
}
export interface GraphRelationships {
  summary: {
    total_nodes: number;
    total_relationships: number;
    relationship_types_used: number;
    graph_density: number;
    average_degree: number;
    connected_components: number;
  };
  relationship_distribution: RelationshipEntry[];
  top_connected_nodes: TopNode[];
}
export const getGraphRelationships = () =>
  fetchJSON<GraphRelationships>('/api/knowledge/relationships');

// ── Graph health ──────────────────────────────────────────────────────────────
export interface GraphHealth {
  overall: 'ok' | 'warn' | 'error';
  checks?: Record<string, Record<string, unknown>>;
  error?: string;
}
export const getGraphHealth = () =>
  fetchJSON<GraphHealth>('/api/knowledge/graph/health');

// ── Graph ─────────────────────────────────────────────────────────────────────
export interface GraphNode {
  id: number; uuid: string; title: string; note_type: string; project_id: number | null; created_at: string;
}
export interface GraphEdge {
  source_note_id: number; target_note_id: number; relationship: string; weight: number;
}
export interface GraphData { nodes: GraphNode[]; edges: GraphEdge[] }
export const getGraph = () => fetchJSON<GraphData>('/api/knowledge/graph');
export const traverseGraph = (noteId: number, depth = 2) =>
  fetchJSON<GraphData>(`/api/knowledge/graph/${noteId}/traverse?depth=${depth}`);

// ── Timeline ──────────────────────────────────────────────────────────────────
export interface TimelineEvent {
  id: number; event_type: string; payload: Record<string, unknown>;
  note_id: number | null; project_id: number | null; provider: string | null;
  persona: string | null; created_at: string;
}
export const getTimeline = (params?: { event_type?: string; project_id?: number; since?: string; limit?: number }) => {
  const q = new URLSearchParams();
  if (params?.event_type) q.set('event_type', params.event_type);
  if (params?.project_id) q.set('project_id', String(params.project_id));
  if (params?.since) q.set('since', params.since);
  if (params?.limit) q.set('limit', String(params.limit));
  return fetchJSON<TimelineEvent[]>(`/api/knowledge/timeline?${q}`);
};
export const getRecentTimeline = (limit = 50) =>
  fetchJSON<TimelineEvent[]>(`/api/knowledge/timeline/recent?limit=${limit}`);

// ── Search ────────────────────────────────────────────────────────────────────
export interface SearchResult {
  semantic?: unknown[];
  fulltext?: unknown[];
  tag?: unknown[];
  timeline?: unknown[];
  project?: unknown[];
  people?: unknown[];
  reference?: unknown[];
}
export const search = (query: string, modes?: string[], topK = 20) =>
  fetchJSON<SearchResult>('/api/knowledge/search', {
    method: 'POST',
    body: JSON.stringify({ query, modes, top_k: topK }),
  });

// ── Notes ─────────────────────────────────────────────────────────────────────
export interface Note {
  id: number; uuid: string; title: string; content: string; note_type: string;
  vault_path: string; tags: string; created_at: string; updated_at: string;
  embedding_status: string; source_provider: string | null;
  user_id?: string | null;
}
export const getNotes = (params?: { note_type?: string; project_id?: number; limit?: number }) => {
  const q = new URLSearchParams();
  if (params?.note_type) q.set('note_type', params.note_type);
  if (params?.project_id) q.set('project_id', String(params.project_id));
  if (params?.limit) q.set('limit', String(params.limit));
  return fetchJSON<Note[]>(`/api/knowledge/notes?${q}`);
};

/** P0-F: owner-only update of a private note */
export const updateNote = (uuid: string, body: { title?: string; content?: string; tags?: string[] }) =>
  fetchJSON<Note>(`/api/knowledge/notes/${uuid}`, { method: 'PATCH', body: JSON.stringify(body) });

/** P0-F: owner-only hard delete of a private note */
export const deleteNote = (uuid: string) =>
  fetchJSON<{ deleted: boolean; uuid: string }>(`/api/knowledge/notes/${uuid}`, { method: 'DELETE' });

// ── Projects ──────────────────────────────────────────────────────────────────
export interface Project {
  id: number; uuid: string; name: string; description: string;
  status: string; tags: string; created_at: string; updated_at: string;
}
export const getProjects = () => fetchJSON<Project[]>('/api/knowledge/projects');

// ── Providers ─────────────────────────────────────────────────────────────────
export interface ProviderInfo {
  name: string; display_name: string; capabilities: string[]; authenticated: boolean;
}
export interface ProviderHealth {
  provider: string; status: string; model: string; latency_ms: number; reason?: string;
}
export const getProviders = () => fetchJSON<ProviderInfo[]>('/api/knowledge/providers');
export const getProviderHealth = () => fetchJSON<ProviderHealth[]>('/api/knowledge/providers/health');

// ── Personas ──────────────────────────────────────────────────────────────────
export interface Persona {
  id: number; name: string; preferred_provider: string | null; created_at: string;
}
export const getPersonas = () => fetchJSON<Persona[]>('/api/knowledge/personas');

// ── Ingest ────────────────────────────────────────────────────────────────────
export const ingestNote = (payload: {
  title: string; content: string; note_type?: string;
  project_id?: number; tags?: string[]; source_provider?: string;
}) => fetchJSON('/api/knowledge/ingest', { method: 'POST', body: JSON.stringify(payload) });

export const sendWithContext = (payload: {
  messages: { role: string; content: string }[];
  persona?: string; provider?: string; project_id?: number;
  ingest_response?: boolean;
}) => fetchJSON('/api/knowledge/providers/send', { method: 'POST', body: JSON.stringify(payload) });

// ── Graph Explorer (K3-C) ─────────────────────────────────────────────────────
export interface EdgeDetail {
  id: number; relationship: string; weight: number; created_at: string;
  target_note_id?: number; source_note_id?: number;
  target_title?: string; target_type?: string; target_uuid?: string;
  source_title?: string; source_type?: string; source_uuid?: string;
}
export interface NodeDetail {
  node: Note;
  outbound_edges: EdgeDetail[];
  inbound_edges: EdgeDetail[];
  degree: number;
}
export const getNode = (noteId: number) =>
  fetchJSON<NodeDetail>(`/api/knowledge/node/${noteId}`);

export interface NeighborResult {
  root_id: number; depth: number;
  nodes: GraphNode[]; edges: GraphEdge[];
  node_count: number; edge_count: number;
}
export const getNeighbors = (noteId: number, depth = 1, relationship?: string) => {
  const q = new URLSearchParams({ depth: String(depth) });
  if (relationship) q.set('relationship', relationship);
  return fetchJSON<NeighborResult>(`/api/knowledge/neighbors/${noteId}?${q}`);
};

export interface PathResult {
  from_id: number; to_id: number;
  path_ids: number[]; path_nodes: GraphNode[]; hops: number; found: boolean;
}
export const getPath = (fromId: number, toId: number, maxDepth = 4) =>
  fetchJSON<PathResult>(`/api/knowledge/path?from_id=${fromId}&to_id=${toId}&max_depth=${maxDepth}`);

// ── Embedding queue (K3-C) ────────────────────────────────────────────────────
export interface EmbeddingStatus {
  total: number; complete: number; pending: number;
  partial: number; failed: number; coverage: number; backlog: number;
}
export const getEmbeddingStatus = () =>
  fetchJSON<EmbeddingStatus>('/api/knowledge/embeddings/status');

// ── Migration (K3-C) ──────────────────────────────────────────────────────────
export interface MigrationReport {
  summary: { total_edges: number; violated_types: number; affected_edges: number; clean: boolean };
  violations: { legacy_type: string; count: number; canonical_map: string | null; mappable: boolean }[];
}
export const getMigrationReport = () =>
  fetchJSON<MigrationReport>('/api/knowledge/migrate/edges/report');

export const applyEdgeMigration = (dryRun = true) =>
  fetchJSON('/api/knowledge/migrate/edges/apply?dry_run=' + dryRun, { method: 'POST' });
