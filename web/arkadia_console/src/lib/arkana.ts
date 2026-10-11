/**
 * Arkana conversational contract.
 *
 * The reply shape is the one `POST /api/commune/resonance` actually returns:
 * `reply`, `resonance`, `patterns`, and the RAG/memory diagnostics. Nothing is
 * simulated — a failure is surfaced as a real `ApiError`.
 */
import { apiRequest } from "./apiClient";
import { endpoints } from "./endpoints";

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
  rag_refs: Array<Record<string, unknown>>;
  rag_hits: number;
  sources: Record<string, unknown>;
  memory: Record<string, unknown>;
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
): Promise<ArkanaReply> {
  return apiRequest<ArkanaReply>(endpoints.arkanaResonance, {
    method: "POST",
    body: JSON.stringify({
      message,
      history: history.slice(-10),
      session_id: sessionId(),
      project_id: projectId ?? null,
    }),
  });
}
