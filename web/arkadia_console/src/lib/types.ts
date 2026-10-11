/**
 * Response shapes for the Arkadia backend contracts this frontend consumes.
 *
 * Fields are typed to the shape actually returned by the deployed API. Optional
 * fields are the ones the backend may omit; nothing here is invented.
 */

export interface VersionInfo {
  schema: string;
  service: string;
  read_only: boolean;
  canonical_deployment: string;
  source_revision: string | null;
  revision_source: string;
  revision_conflict: boolean;
}

export interface NodeProfile {
  uid: string;
  email: string;
  node_key: string | null;
  display_name: string;
  username?: string | null;
  bio?: string | null;
  avatar_url?: string | null;
  role: string;
  role_sigil: string;
  ims_id: string | null;
  access_level: number;
  status: string;
  access_tools: string[];
  profile_complete?: boolean;
}

export interface KnowledgeStatus {
  status: string;
  vault: { notes: number; projects: number; chunks: number; embeddings: number; pending_embeddings: number };
  graph: { edges: number };
  timeline: { events: number };
  ontology: { version: string; node_types_count: number; relationship_types_count: number };
  nodes_by_type: Record<string, number>;
  graph_health: string;
  indexing_status: { complete: number; pending: number; partial: number; failed: number; coverage: number };
  last_ingestion: string | null;
}

export interface SolspireProject {
  id: string;
  name: string;
  status?: string;
  description?: string | null;
  owner_uid?: string;
  created_at?: number | string;
  updated_at?: number | string;
}

export interface ProjectList {
  projects: SolspireProject[];
  count: number;
}

export interface LabOverview {
  [key: string]: unknown;
}

export interface NAtlasCatalog {
  status: string;
  detail?: string;
  [key: string]: unknown;
}
