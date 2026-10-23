/**
 * Spiral Codex corpus contract (feature-local).
 *
 * The shape `GET /api/codex` actually returns, measured against the canonical
 * deployment (`200`, 661 documents / 4,413,059 characters) rather than inferred
 * from the archived UI. `api/main.py::get_codex` builds it from `_get_scrolls()`
 * and returns the document map verbatim, so the fields below are the corpus's own
 * keys — `content` is the full body, not a preview.
 *
 * Two properties of this contract are load-bearing and are why this module exists
 * rather than the component reading the payload directly:
 *
 * 1. **`scrolls` is a MAP, not a list** (keyed by document id). The archive
 *    handled both shapes defensively (`PersonalCodex.tsx` branches on
 *    `Array.isArray`); the served contract is always an object, so the reader
 *    normalises to an array once, here.
 *
 * 2. **`/api/codex/categories` is NOT served.** `SpiralCodexFeed.tsx:90-91`
 *    fetched it in parallel with the corpus; the path is absent from
 *    `app.openapi()` and answers `404 {"detail":"Route not found"}` on the
 *    canonical deployment. Categories are therefore derived from each document's
 *    own `category`, and `deriveCategories` is the single place that does so — a
 *    facet list computed in the component could silently disagree with the
 *    documents it is filtering.
 */

/** One corpus document, as `_get_scrolls()` returns it. */
export interface CodexScroll {
  id?: string;
  /** Provenance: `github` for the repository-backed corpus. */
  source?: string;
  /** The document's own facet key (the served corpus reports `CREATIVE_OS`). */
  category?: string;
  priority?: number;
  label?: string;
  description?: string;
  chars?: number;
  preview?: string;
  /** The full document body. */
  content?: string;
  fetched_at?: string;
  /** Non-null when the fetch for this document failed; such docs are not "live". */
  error?: string | null;
  github_url?: string;
}

/** `GET /api/codex` response envelope. */
export interface CodexCorpus {
  status: string;
  total_docs: number;
  /** Documents with no `error` and a non-zero `chars` — the server's own count. */
  live_docs: number;
  total_chars: number;
  scrolls: Record<string, CodexScroll>;
}

/** A document with its map key resolved to a stable identity. */
export interface CodexDocument extends CodexScroll {
  /** The `scrolls` map key. Used for React keys and expansion state. */
  key: string;
}

/** A derived facet: the category name and how many documents carry it. */
export interface CodexCategory {
  name: string;
  count: number;
}

/** The facet used for "no category filter". Not a real `category` value. */
export const CODEX_ALL_CATEGORIES = "ALL";

/**
 * Normalise the served map into an array, preferring the map key as identity.
 *
 * The key is authoritative: a document whose own `id` is missing still has a
 * stable identity from the map, and the archive's expansion state keyed off the
 * map key for the same reason.
 */
export function toDocuments(corpus: CodexCorpus | null): CodexDocument[] {
  if (!corpus || !corpus.scrolls || typeof corpus.scrolls !== "object") return [];
  return Object.entries(corpus.scrolls).map(([key, scroll]) => ({ ...scroll, key }));
}

/**
 * Derive facets from the documents themselves.
 *
 * Derived rather than fetched because the served contract has no categories
 * route (see the module header). A document with no `category` is grouped under
 * `UNCATEGORISED` rather than being dropped — dropping it would make the facet
 * counts sum to less than the corpus and hide documents from every filter.
 */
export function deriveCategories(documents: CodexDocument[]): CodexCategory[] {
  const counts = new Map<string, number>();
  for (const doc of documents) {
    const name = doc.category?.trim() || "UNCATEGORISED";
    counts.set(name, (counts.get(name) ?? 0) + 1);
  }
  return [...counts.entries()]
    .map(([name, count]) => ({ name, count }))
    .sort((a, b) => b.count - a.count || a.name.localeCompare(b.name));
}

/**
 * Filter documents by facet and a case-insensitive query.
 *
 * Searches the same three fields the archived `SpiralCodexFeed` searched
 * (`label`, `description`, `preview`). `content` is deliberately **not**
 * searched: the payload carries the full body for every document, so matching
 * against it would make the result depend on text the list never shows, and a
 * reader could not see why a document matched.
 */
export function filterDocuments(
  documents: CodexDocument[],
  category: string,
  query: string,
): CodexDocument[] {
  const needle = query.trim().toLowerCase();
  return documents.filter((doc) => {
    if (category !== CODEX_ALL_CATEGORIES && (doc.category?.trim() || "UNCATEGORISED") !== category) {
      return false;
    }
    if (!needle) return true;
    return [doc.label, doc.description, doc.preview].some((field) =>
      (field ?? "").toLowerCase().includes(needle),
    );
  });
}

/**
 * How many documents the panel renders before it stops.
 *
 * The corpus is 661 documents and the response is ~5 MB, so the list is bounded
 * and the bound is stated in the UI. Rendering a subset silently would present a
 * truncated corpus as the whole one.
 */
export const CODEX_DISPLAY_LIMIT = 24;
