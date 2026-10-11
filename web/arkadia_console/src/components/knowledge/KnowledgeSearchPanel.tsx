/**
 * Knowledge OS — unified multi-mode search.
 *
 * Backed by the *verified* handler contract `POST /api/knowledge/search`
 * (`api/knowledge_routes.py::search` -> `knowledge.search.unified_search`); see
 * the capability matrix in the slice evidence. The request body is
 * `{ query, modes, top_k }`; the response is a mapping of mode name to the
 * records that mode retrieved.
 *
 * Ownership: the backend applies the ownership predicate (`own OR public` for an
 * authenticated caller, public-only otherwise). This panel never filters by
 * owner client-side — a client-side filter cannot prove a server-side boundary
 * and would misrepresent a leak as a boundary.
 *
 * The endpoint is supplied by the parent from the canonical registry
 * (`lib/endpoints.ts`, owned by Workstream 1). When the registry does not yet
 * carry the path the panel is not rendered: the page shows the blocked state it
 * selected, so an unwired contract cannot masquerade as a real search.
 */
import { useState, type FormEvent } from "react";
import { ApiError, apiRequest } from "../../lib/apiClient";
import { Panel } from "../ui";
import {
  SEARCH_MODES,
  countSearchRecords,
  isKnowledgeSearchData,
  recordDetail,
  recordTitle,
  type KnowledgeSearchData,
} from "../../pages/knowledge/knowledgeContracts";

const DEFAULT_MODES = ["semantic", "fulltext", "tag"];

export function KnowledgeSearchPanel({ endpoint }: { endpoint: string }) {
  const [query, setQuery] = useState("");
  const [modes, setModes] = useState<string[]>(DEFAULT_MODES);
  const [results, setResults] = useState<KnowledgeSearchData | null>(null);
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
      const response = await apiRequest<unknown>(endpoint, {
        method: "POST",
        body: JSON.stringify({ query: trimmed, modes, top_k: 20 }),
      });
      if (!isKnowledgeSearchData(response)) {
        // An unrecognised body must not read as a legitimate empty result.
        throw new ApiError("The knowledge search contract returned an unrecognised shape.", {
          kind: "UNKNOWN",
          path: endpoint,
        });
      }
      setResults(response);
    } catch (caught: unknown) {
      const apiError = caught instanceof ApiError ? caught : null;
      if (apiError?.kind === "AUTH_REQUIRED" || apiError?.kind === "FORBIDDEN") {
        setError("Authentication or access is required for this search. No result was inferred.");
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

  const total = results ? countSearchRecords(results) : 0;

  return (
    <Panel data-testid="knowledge-search-panel">
      <div className="mb-3">
        <p className="font-mono text-[11px] uppercase tracking-widest text-white/40">Knowledge retrieval</p>
        <p className="mt-1 text-sm text-white/55">
          Search the accessible corpus. Private and public visibility is enforced by the backend.
        </p>
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
        {modes.length === 0 && <p className="text-xs text-gold">Select at least one search mode.</p>}
      </form>

      {error && <p role="alert" className="mt-4 rounded border border-gold/30 p-3 text-sm text-gold">{error}</p>}

      {loading && <p className="mt-4 text-sm text-white/50">Searching the accessible corpus…</p>}

      {!loading && results && (
        <div className="mt-4" data-testid="knowledge-search-results">
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
                      const title = recordTitle(record, mode, index);
                      const detail = recordDetail(record);
                      return (
                        <li key={`${mode}-${index}`} className="border-l border-line pl-3">
                          <p className="text-sm text-white/85">{title}</p>
                          {detail && <p className="mt-1 line-clamp-3 whitespace-pre-wrap text-xs text-white/45">{detail}</p>}
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
