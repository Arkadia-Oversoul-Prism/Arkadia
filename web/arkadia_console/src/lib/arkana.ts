/**
 * Arkana conversational contract.
 *
 * The reply shape is the one `POST /api/commune/resonance` actually returns:
 * `reply`, `resonance`, `patterns`, and the RAG/memory diagnostics. Nothing is
 * simulated — a failure is surfaced as a real `ApiError`.
 */
import { apiRequest } from "./apiClient";
import { endpoints } from "./endpoints";
import { buildProvenance, type ArkanaProvenance } from "../components/arkana/arkanaProvenanceContract";

export interface ArkanaMessage {
  role: "user" | "assistant";
  content: string;
}

export interface ArkanaSources {
  memory?: { session_id: string | null; thread_id: number | null; notes_retrieved: number; injected: boolean };
  rag_refs?: Array<{ title?: string; source?: string; [key: string]: unknown }>;
  rag_hits?: number;
}

export interface ArkanaReply {
  reply: string;
  resonance: number;
  patterns: unknown[];
  /** Corpus scrolls `_rag_context` scored into the prompt: `{ id, label, category }`. */
  rag_refs: Array<Record<string, unknown>>;
  rag_hits: number;
  /** Knowledge OS notes actually injected, from `oracle_spine.build_sources`. */
  sources: Array<Record<string, unknown>>;
  /** Knowledge OS turn metadata: `notes_retrieved`, `thread_id`, `source`, … */
  memory: Record<string, unknown>;
}

/** A reply plus the provenance channels it reported. */
export interface ArkanaTurn extends ArkanaReply {
  provenance: ArkanaProvenance;
}

/** A stable, session-scoped conversation id (persisted for continuity). */
const SESSION_KEY = "arkadia_session_id";

export function sessionId(): string {
  if (typeof window === "undefined") return "anon";
  let id = window.localStorage.getItem(SESSION_KEY);
  if (!id) {
    id = `sess_${Date.now().toString(36)}_${Math.random().toString(36).slice(2, 10)}`;
    window.localStorage.setItem(SESSION_KEY, id);
  }
  return id;
}

export async function askArkana(
  message: string,
  history: ArkanaMessage[],
  projectId?: string,
): Promise<ArkanaTurn> {
  const reply = await apiRequest<ArkanaReply>(endpoints.arkanaResonance, {
    method: "POST",
    body: JSON.stringify({
      message,
      history: history.slice(-10),
      session_id: sessionId(),
      project_id: projectId ?? null,
    }),
  });
  // Normalise the provenance channels here so the surface renders exactly what
  // the response carried — the extra field never leaves this boundary.
  return {
    ...reply,
    provenance: buildProvenance({
      rag_refs: reply.rag_refs,
      sources: reply.sources,
      memory: reply.memory,
    }),
  };
}
