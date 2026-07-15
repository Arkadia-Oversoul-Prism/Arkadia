/**
 * Arkadia Knowledge OS — Frontend API Client
 * All calls to /api/knowledge/* live here.
 */

const API_BASE = (import.meta.env.VITE_API_BASE_URL ?? '').replace(/\/$/, '');

async function fetchJSON<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    headers: { 'Content-Type': 'application/json', ...(options?.headers || {}) },
    ...options,
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
}
export const getStatus = () => fetchJSON<KnowledgeStatus>('/api/knowledge/status');

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
}
export const getNotes = (params?: { note_type?: string; project_id?: number; limit?: number }) => {
  const q = new URLSearchParams();
  if (params?.note_type) q.set('note_type', params.note_type);
  if (params?.project_id) q.set('project_id', String(params.project_id));
  if (params?.limit) q.set('limit', String(params.limit));
  return fetchJSON<Note[]>(`/api/knowledge/notes?${q}`);
};

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
