/**
 * Voice / read-aloud contract.
 *
 * `POST /api/tts` (`api/main.py::text_to_speech`) answers with an audio body and
 * an `X-TTS-Engine` header, not JSON, so it cannot go through `apiRequest` —
 * that helper decodes a JSON payload. This module owns the audio fetch and the
 * honest classification of its failures; the endpoint paths still come from the
 * registry so there is one API surface map.
 *
 * Two contracts matter for truthful UI:
 *
 *  - `GET /api/tts/status` reports the engine that will actually serve a
 *    request. `kernel/tts.py` marks `aetheria` as `requires_elevenlabs`; with no
 *    ElevenLabs key the synthesis silently falls back to the Edge voice. A UI
 *    that offers `aetheria` without reading this status is claiming a voice
 *    quality the deployment cannot deliver.
 *  - A failure is reported as a failure. There is no local synthesis, no cached
 *    placeholder audio, and no "success" inferred from an empty body.
 */
import { API_BASE } from "./apiConfig";
import { ApiError } from "./apiClient";
import { endpoints } from "./endpoints";

export interface VoiceDef {
  id: string;
  name: string;
  description?: string;
  gender?: string;
  accent?: string;
  /** True when this voice is only delivered by the ElevenLabs engine. */
  requires_elevenlabs?: boolean;
}

export interface VoiceCatalog {
  voices: Record<string, VoiceDef>;
  default: string;
}

export interface TtsStatus {
  engine: string;
  elevenlabs_active: boolean;
  edge_tts_active: boolean;
  ready: boolean;
  voices: string[];
  default: string;
  elevenlabs_voices: boolean;
  key_pool?: { total: number; available: number; quota_hit: number };
  preferred_engine: string;
}

/**
 * Whether a voice can be delivered by the engine the backend reports active.
 *
 * A `requires_elevenlabs` voice is unavailable on the Edge engine — the backend
 * substitutes a different voice rather than failing, so the UI must state the
 * substitution instead of presenting the selected voice as honoured.
 */
export function voiceIsDeliverable(voice: VoiceDef | undefined, status: TtsStatus | null): boolean {
  if (!voice) return false;
  if (!voice.requires_elevenlabs) return true;
  return Boolean(status?.elevenlabs_active);
}

/** Strip markdown so the spoken text is prose, not syntax. */
export function speakableText(markdown: string): string {
  let text = markdown;
  text = text.replace(/```[\s\S]*?```/g, " ");
  text = text.replace(/`([^`]+)`/g, "$1");
  text = text.replace(/<[^>]+>/g, " ");
  text = text.replace(/!\[[^\]]*\]\([^)]+\)/g, "");
  text = text.replace(/\[([^\]]+)\]\([^)]+\)/g, "$1");
  text = text.replace(/^\s{0,3}#{1,6}\s+/gm, "");
  text = text.replace(/^\s*[-*+]\s+/gm, "");
  text = text.replace(/^\s*\d+\.\s+/gm, "");
  text = text.replace(/^\s*>\s?/gm, "");
  text = text.replace(/(\*\*|__)(.*?)\1/g, "$2");
  text = text.replace(/(\*|_)(.*?)\1/g, "$2");
  text = text.replace(/https?:\/\/[^\s]+/g, " ");
  text = text.replace(/\|[^\n]*\|/g, " ");
  text = text.replace(/^\s*\|?[\s:=-]{3,}\|?\s*$/gm, " ");
  text = text.replace(/[\x00-\x1F\x7F]/g, " ");
  text = text.replace(/\n{2,}/g, ". ");
  text = text.replace(/\s{2,}/g, " ");
  return text.trim();
}

async function readJson<T>(path: string, init: RequestInit): Promise<T> {
  let response: Response;
  try {
    response = await fetch(`${API_BASE}${path}`, init);
  } catch (error) {
    throw new ApiError(error instanceof Error ? error.message : "Arkadia network request failed", {
      kind: "NETWORK_ERROR",
      path,
    });
  }
  if (!response.ok) {
    throw new ApiError(`voice read failed: ${response.status}`, {
      status: response.status,
      kind: response.status >= 500 ? "SERVER_ERROR" : "UNKNOWN",
      path,
    });
  }
  return (await response.json()) as T;
}

export function fetchVoiceCatalog(signal?: AbortSignal): Promise<VoiceCatalog> {
  return readJson<VoiceCatalog>(endpoints.ttsVoices, { signal });
}

export function fetchTtsStatus(signal?: AbortSignal): Promise<TtsStatus> {
  return readJson<TtsStatus>(endpoints.ttsStatus, { signal });
}

export interface SynthesisedAudio {
  blob: Blob;
  /** The engine the backend actually used — `X-TTS-Engine`. */
  engine: string | null;
}

/**
 * Synthesise speech for `text`.
 *
 * The returned `engine` is the backend's own report of what served the request,
 * not an assumption from the requested voice.
 */
export async function synthesiseSpeech(
  text: string,
  voice: string,
  speed = 1,
): Promise<SynthesisedAudio> {
  let response: Response;
  try {
    response = await fetch(`${API_BASE}${endpoints.tts}`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ text, voice, speed }),
    });
  } catch (error) {
    throw new ApiError(error instanceof Error ? error.message : "Arkadia network request failed", {
      kind: "NETWORK_ERROR",
      path: endpoints.tts,
    });
  }

  if (!response.ok) {
    let detail = "";
    try {
      const payload = (await response.json()) as { detail?: unknown };
      detail = payload?.detail ? String(payload.detail) : "";
    } catch {
      detail = "";
    }
    throw new ApiError(detail || `speech synthesis failed: ${response.status}`, {
      status: response.status,
      kind: response.status >= 500 ? "SERVER_ERROR" : "UNKNOWN",
      path: endpoints.tts,
    });
  }

  const blob = await response.blob();
  // An empty body is a failure, not silent success: playing it would show a
  // player that produces no sound and claims to have worked.
  if (blob.size === 0) {
    throw new ApiError("the voice contract returned an empty audio body", {
      status: response.status,
      kind: "SERVER_ERROR",
      path: endpoints.tts,
    });
  }

  return { blob, engine: response.headers.get("X-TTS-Engine") };
}
