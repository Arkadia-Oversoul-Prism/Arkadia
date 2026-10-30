/**
 * Arkana conversational contract.
 *
 * Non-streaming: POST /api/commune/resonance
 * Streaming (A2): POST /api/commune/resonance/stream (SSE)
 */
import { apiRequest, getApiAuthToken, ApiError } from "./apiClient";
import { API_BASE } from "./apiConfig";
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

export type StreamHandlers = {
  onStatus?: (label: string) => void;
  onDelta?: (text: string) => void;
  signal?: AbortSignal;
};

/**
 * Stream a turn via SSE. Falls back to non-streaming `askArkana` when the
 * stream route is unavailable (404/501) so the surface never dead-ends.
 */
export async function streamArkana(
  message: string,
  history: ArkanaMessage[],
  handlers: StreamHandlers = {},
  projectId?: string,
): Promise<ArkanaTurn> {
  const path = endpoints.arkanaResonanceStream;
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    Accept: "text/event-stream",
  };
  const token = getApiAuthToken();
  if (token) headers.Authorization = `Bearer ${token}`;

  let response: Response;
  try {
    response = await fetch(`${API_BASE}${path}`, {
      method: "POST",
      headers,
      body: JSON.stringify({
        message,
        history: history.slice(-10),
        session_id: sessionId(),
        project_id: projectId ?? null,
      }),
      signal: handlers.signal,
    });
  } catch (error) {
    throw new ApiError(error instanceof Error ? error.message : "Arkadia network request failed", {
      kind: "NETWORK_ERROR",
      path,
    });
  }

  // Stream route not deployed yet — fall back to the JSON contract.
  if (response.status === 404 || response.status === 501) {
    return askArkana(message, history, projectId);
  }

  if (!response.ok) {
    let detail = `${response.status} ${response.statusText}`;
    try {
      const payload = (await response.json()) as { error?: string; detail?: string };
      detail = payload.detail || payload.error || detail;
    } catch {
      /* ignore */
    }
    throw new ApiError(detail, {
      status: response.status,
      kind: response.status >= 500 ? "SERVER_ERROR" : "UNKNOWN",
      path,
    });
  }

  const reader = response.body?.getReader();
  if (!reader) {
    return askArkana(message, history, projectId);
  }

  const decoder = new TextDecoder();
  let buffer = "";
  let full = "";
  let donePayload: ArkanaReply | null = null;

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });
    const parts = buffer.split("\n\n");
    buffer = parts.pop() ?? "";
    for (const part of parts) {
      const line = part
        .split("\n")
        .find((l) => l.startsWith("data:"))
        ?.slice(5)
        .trim();
      if (!line) continue;
      let event: Record<string, unknown>;
      try {
        event = JSON.parse(line) as Record<string, unknown>;
      } catch {
        continue;
      }
      const type = event.type;
      if (type === "status" && typeof event.label === "string") {
        handlers.onStatus?.(event.label);
      } else if (type === "delta" && typeof event.text === "string") {
        full += event.text;
        handlers.onDelta?.(event.text);
      } else if (type === "done") {
        donePayload = {
          reply: typeof event.reply === "string" ? event.reply : full,
          resonance: typeof event.resonance === "number" ? event.resonance : 0,
          patterns: Array.isArray(event.patterns) ? event.patterns : [],
          rag_refs: Array.isArray(event.rag_refs) ? (event.rag_refs as Array<Record<string, unknown>>) : [],
          rag_hits: typeof event.rag_hits === "number" ? event.rag_hits : 0,
          sources: Array.isArray(event.sources) ? (event.sources as Array<Record<string, unknown>>) : [],
          memory: typeof event.memory === "object" && event.memory ? (event.memory as Record<string, unknown>) : {},
        };
      } else if (type === "error") {
        throw new ApiError(typeof event.error === "string" ? event.error : "Stream failed", {
          kind: "SERVER_ERROR",
          path,
        });
      }
    }
  }

  if (!donePayload) {
    if (!full.trim()) {
      throw new ApiError("Empty stream response", { kind: "SERVER_ERROR", path });
    }
    donePayload = {
      reply: full,
      resonance: 0,
      patterns: [],
      rag_refs: [],
      rag_hits: 0,
      sources: [],
      memory: {},
    };
  }

  return {
    ...donePayload,
    provenance: buildProvenance({
      rag_refs: donePayload.rag_refs,
      sources: donePayload.sources,
      memory: donePayload.memory,
    }),
  };
}
