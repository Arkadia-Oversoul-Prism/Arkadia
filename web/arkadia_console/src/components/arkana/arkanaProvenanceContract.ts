/**
 * Arkana — response provenance contract (feature-local).
 *
 * The Oracle's reply carries *what informed it*, and an earlier render dropped
 * that on the floor. `POST /api/commune/resonance` returns three retrieval
 * channels alongside `reply` (all measured against `api/main.py` and
 * `api/oracle_spine.py`, not inferred from an archive):
 *
 *   * `rag_refs`  — corpus scrolls scored into the prompt, from `_rag_context`.
 *                   Each ref is `{ id, label, category }`.
 *   * `sources`   — Knowledge OS notes actually part of the retrieved context,
 *                   from `oracle_spine.build_sources`; emitted ONLY when a note
 *                   was really handed to the provider. Each is
 *                   `{ id, title, type, via: "note" | "graph", excerpt }`.
 *   * `memory`    — the Knowledge OS turn metadata, including
 *                   `{ notes_retrieved, thread_id, session_id, source, injected }`.
 *
 * The console rendered none of these, so a reader could not tell why a reply
 * was shaped the way it was. This module holds the pure normalisation so the
 * surface and its tests share one source of truth. Nothing here manufactures a
 * citation: `rag_refs`/`sources` are taken verbatim from the response, and a
 * channel the backend reported as empty stays visibly empty.
 */

/** One corpus scroll that `_rag_context` scored into the prompt. */
export interface ArkanaRagRef {
  id?: string;
  label?: string;
  category?: string;
  [key: string]: unknown;
}

/** One Knowledge OS note that was actually part of the retrieved context. */
export interface ArkanaSourceRef {
  id?: string;
  title?: string;
  type?: string;
  via?: "note" | "graph" | string;
  excerpt?: string;
  [key: string]: unknown;
}

/** The Knowledge OS memory channel, as `oracle_spine` reports it. */
export interface ArkanaMemoryRef {
  session_id?: string | null;
  thread_id?: number | null;
  notes_retrieved?: number;
  source?: string;
  injected?: boolean;
  [key: string]: unknown;
}

/**
 * The provenance slice a reply carries. All three are optional because the
 * response only includes what the backend actually produced.
 */
export interface ArkanaProvenanceInput {
  rag_refs?: ArkanaRagRef[] | null;
  sources?: ArkanaSourceRef[] | null;
  memory?: Record<string, unknown> | null;
}

export interface ArkanaProvenance {
  ragRefs: ArkanaRagRef[];
  sources: ArkanaSourceRef[];
  memory: ArkanaMemoryRef | null;
}

/** Normalise a raw reply's provenance channels into the display shape. */
export function buildProvenance(input: ArkanaProvenanceInput): ArkanaProvenance {
  return {
    ragRefs: Array.isArray(input.rag_refs) ? input.rag_refs.filter(Boolean) : [],
    sources: Array.isArray(input.sources) ? input.sources.filter(Boolean) : [],
    memory: input.memory && typeof input.memory === "object" ? (input.memory as ArkanaMemoryRef) : null,
  };
}

/**
 * Whether the reply reported any retrieval channel at all.
 *
 * A `memory` object is present on every successful call, so it is not by itself
 * evidence of retrieval. Retrieval is real only when a corpus scroll or a
 * Knowledge OS note was supplied, or when `notes_retrieved` is non-zero — the
 * injection flag alone is not counted, because the backend sets it from the
 * presence of a memory *block*, not from a citation.
 */
export function hasRetrieval(provenance: ArkanaProvenance): boolean {
  return (
    provenance.ragRefs.length > 0 ||
    provenance.sources.length > 0 ||
    (provenance.memory?.notes_retrieved ?? 0) > 0
  );
}

/** A scroll's display label, never a fabricated one. */
export function ragLabel(ref: ArkanaRagRef): string {
  return (ref.label && String(ref.label)) || "Untitled scroll";
}

/** A note's display title, never a fabricated one. */
export function sourceTitle(ref: ArkanaSourceRef): string {
  return (ref.title && String(ref.title)) || "Untitled note";
}
