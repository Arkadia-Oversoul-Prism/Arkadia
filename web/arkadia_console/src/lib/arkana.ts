/**
 * Arkana conversational contract.
 *
 * Non-streaming: POST /api/commune/resonance
 * Streaming (A2): POST /api/commune/resonance/stream (SSE)
 */
import { apiRequest } from "./apiClient";
import { endpoints } from "./endpoints";
import { buildProvenance, type ArkanaProvenance } from "../components/arkana/arkanaProvenanceContract";

export interface ArkanaMessage {
  role: "user" | "assistant";
  content: string;
}

export interface ArkanaReply {
  reply: string;
  resonance: number;
  patterns: unknown[];
  rag_refs: Array<Record<string, unknown>>;
  rag_hits: number;
  sources: Array<Record<string, unknown>>;
  memory: Record<string, unknown>;
}

export interface ArkanaTurn extends ArkanaReply {
  provenance: ArkanaProvenance;
}

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
  return {
    ...reply,
    provenance: buildProvenance({
      rag_refs: reply.rag_refs,
      sources: reply.sources,
      memory: reply.memory,
    }),
  };
}

