import { useState, type FormEvent } from "react";
import { ApiError, apiRequest } from "../../lib/apiClient";
import { Panel } from "../ui";

const SEARCH_MODES = [
  { id: "semantic", label: "Semantic" },
  { id: "fulltext", label: "Full text" },
  { id: "tag", label: "Tags" },
  { id: "timeline", label: "Timeline" },
  { id: "project", label: "Projects" },
  { id: "people", label: "People" },
  { id: "reference", label: "References" },
] as const;

type SearchRecord = Record<string, unknown>;
type SearchResponse = Record<string, SearchRecord[]>;

function asText(value: unknown): string {
  return typeof value === "string" || typeof value === "number" ? String(value) : "";
}

/**
 * Knowledge OS search, backed by POST /api/knowledge/search.
 *
 * The parent supplies the endpoint from the canonical endpoint registry. Search
 * results are rendered as retrieved records; no result is fabricated and the
 * backend remains responsible for private/public ownership filtering.
 */
export function KnowledgeSearchPanel({ endpoint }: { endpoint: string }) {
  const [query, setQuery] = useState("");
  const [modes, setModes] = useState<string[]>(["semantic", "fulltext", "tag"]);
  const [results, setResults] = useState<SearchResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  function toggleMode(mode: string) {
    setModes((current) => current.includes(mode) ? current.filter((item) => item !== mode) : [...current, mode]);
  }

  async function search(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const trimmed = query.trim();
    if (!trimmed || loading || modes.length === 0) return;
    setLoading(true);
    setError(null);
    try {
      const response = await apiRequest<SearchResponse>(endpoint, {
        method: "POST",
        body: JSON.stringify({ query: trimmed, modes, top_k: 20 }),
      });
      setResults(response);
    } catch (caught: unknown) {
      const apiError = caught instanceof ApiError ? caught : null;
      if (apiError?.kind === "AUTH_REQUIRED" || apiError?.kind === "FORBIDDEN") {
        setError("Authentication or access is required for this search.");
      } else if (apiError?.kind === "NETWORK_ERROR" || apiError?.kind === "SERVER_ERROR") {
        setError("The Knowledge OS search service is unavailable. No search result was inferred.");
      } else {
        setError(apiError?.message ?? (caught instanceof Error ? caught.message : "Search failed."));
      }
      setResults(null);
    } finally {
      setLoading(false);
    }
  }

  const total = results ? Object.values(results).reduce((sum, records) => sum + (Array.isArray(records) ? records.length : 0), 0) : 0;

  return (
    <Panel>
      <div className="mb-3">
        <p className="font-mono text-[11px] uppercase tracking-widest text-white/40">Knowledge retrieval</p>
        <p className="mt-1 text-sm text-white/55">Search the accessible corpus. Private and public visibility is enforced by the backend.</p>
      </div>
      <form onSubmit={(event) => void search(event)} className="flex flex-col gap-3">
        <div className="flex flex-col gap-2 sm:flex-row">
          <label className="sr-only" htmlFor="knowledge-search-query">Search query</label>
          <input
            id="knowledge-search-query"
            value={query}
            onChange={(event) => setQuery(event.target.value)}
            placeholder="Search notes, ideas, people, projects…"
            className="min-w-0 flex-1 rounded-lg border border-line bg-ink/50 px-3 py-2 text-sm text-white outline-none focus:border-emerald/50"
          />
          <button
            type="submit"
            disabled={loading || !query.trim() || modes.length === 0}
            className="rounded-lg border border-emerald/40 px-4 py-2 font-mono text-[11px] uppercase tracking-widest text-emerald disabled:opacity-40"
          >
            {loading ? "Searching…" : "Search"}
          </button>
        </div>
        <fieldset className="flex flex-wrap gap-2">
          <legend className="mb-2 font-mono text-[10px] uppercase tracking-widest text-white/35">Search modes</legend>
          {SEARCH_MODES.map((mode) => {
            const selected = modes.includes(mode.id);
            return (
              <button
                key={mode.id}
                type="button"
                aria-pressed={selected}
                onClick={() => toggleMode(mode.id)}
                className={`rounded border px-2 py-1 text-xs ${selected ? "border-emerald/50 bg-emerald/10 text-emerald" : "border-line text-white/45"}`}
              >
                {mode.label}
              </button>
            );
          })}
        </fieldset>
      </form>

      {error && <p role="alert" className="mt-4 rounded border border-gold/30 p-3 text-sm text-gold">{error}</p>}
      {results && (
        <div className="mt-4">
          <p className="mb-3 font-mono text-[10px] uppercase tracking-widest text-white/40">
            {total} retrieved record(s) across {Object.keys(results).length} mode(s)
          </p>
          {total === 0 ? (
            <p className="text-sm text-white/50">The selected modes returned no records for this query.</p>
          ) : (
            <div className="flex flex-col gap-3">
              {Object.entries(results).map(([mode, records]) => records.length > 0 && (
                <section key={mode} className="rounded-lg border border-line p-3">
                  <h3 className="mb-2 font-mono text-[10px] uppercase tracking-widest text-white/45">{mode} · {records.length}</h3>
                  <ul className="flex flex-col gap-2">
                    {records.map((record, index) => {
                      const title = asText(record.title) || asText(record.label) || asText(record.name) || `Record ${index + 1}`;
                      const detail = asText(record.content) || asText(record.description) || asText(record.target_ref) || asText(record.vault_path);
                      return (
                        <li key={asText(record.uuid) || asText(record.id) || `${mode}-${index}`} className="border-l border-line pl-3">
                          <p className="text-sm text-white/85">{title}</p>
                          {detail && <p className="mt-1 line-clamp-3 whitespace-pre-wrap text-xs text-white/45">{detail}</p>}
                          {record.note_type && <p className="mt-1 font-mono text-[10px] text-white/30">{asText(record.note_type)}</p>}
                        </li>
                      );
                    })}
                  </ul>
                </section>
              ))}
            </div>
          )}
        </div>
      )}
    </Panel>
  );
}
