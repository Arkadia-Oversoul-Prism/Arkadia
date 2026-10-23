/**
 * NovaNet — the shared public document corpus (the Encyclopedia Galactica).
 *
 * The archived Prism built two routes on `GET /api/codex` — `/encyclopedia`
 * (`NexusSpiralCodex`, `initialMode="scrolls"`) and `/spiral-codex`
 * (`SpiralCodexFeed`) — plus `SpiralVault` and `ShereSanctuary`. The console
 * referenced the contract nowhere, so a verified open read carrying 661
 * documents and 4.4M characters had no surface at all.
 *
 * This is a **read**. The archive also offered an upload (`POST /api/codex/upload`)
 * and a category fetch (`/api/codex/categories`); neither is wired here:
 *
 *   * upload is a mutation on the shared corpus and belongs in its own slice with
 *     its own authority review — this panel offers no control for it;
 *   * `/api/codex/categories` **is not served** (absent from `app.openapi()`,
 *     `404` on the canonical deployment), so facets are derived from the
 *     documents' own `category` field in `spiralCodexContract.ts`.
 *
 * Nothing is invented. Every count is the server's own (`total_docs`,
 * `live_docs`, `total_chars`) or a facet count over the documents actually
 * returned; the panel states which of the corpus it is showing, because 661
 * documents are not rendered and a silent subset would misrepresent the corpus.
 */
import { useMemo, useState } from "react";
import { ContractState, Facts, Loading, Panel } from "../ui";
import { useHydration } from "../../lib/useHydration";
import { apiRequest } from "../../lib/apiClient";
import { endpoints } from "../../lib/endpoints";
import {
  CODEX_ALL_CATEGORIES,
  CODEX_DISPLAY_LIMIT,
  deriveCategories,
  filterDocuments,
  toDocuments,
  type CodexCorpus,
} from "./spiralCodexContract";

export function SpiralCodexPanel() {
  const corpus = useHydration<CodexCorpus>(endpoints.publicCodex, (p) => apiRequest<CodexCorpus>(p));
  const [category, setCategory] = useState<string>(CODEX_ALL_CATEGORIES);
  const [query, setQuery] = useState("");
  const [expanded, setExpanded] = useState<string | null>(null);

  const documents = useMemo(() => toDocuments(corpus.data), [corpus.data]);
  const categories = useMemo(() => deriveCategories(documents), [documents]);
  const matches = useMemo(
    () => filterDocuments(documents, category, query),
    [documents, category, query],
  );
  const shown = matches.slice(0, CODEX_DISPLAY_LIMIT);

  if (corpus.state !== "ready") {
    return (
      <Panel>
        <p className="mb-3 font-mono text-[11px] uppercase tracking-widest text-white/40">
          Encyclopedia Galactica · shared corpus
        </p>
        {corpus.state === "loading" || corpus.state === "idle" ? (
          <Loading label="Reading the shared corpus…" />
        ) : (
          <ContractState
            state={corpus.state}
            error={corpus.error?.message}
            onRetry={corpus.reload}
          />
        )}
      </Panel>
    );
  }

  if (!corpus.data || documents.length === 0) {
    return (
      <Panel>
        <p className="mb-3 font-mono text-[11px] uppercase tracking-widest text-white/40">
          Encyclopedia Galactica · shared corpus
        </p>
        <p className="text-sm text-white/60">
          The corpus is reachable but holds no documents. This is an empty corpus, not an
          unreachable one.
        </p>
      </Panel>
    );
  }

  return (
    <>
      <Panel className="mb-4">
        <p className="mb-3 font-mono text-[11px] uppercase tracking-widest text-white/40">
          Encyclopedia Galactica · shared corpus
        </p>
        <Facts
          rows={[
            { label: "status", value: corpus.data.status },
            { label: "documents", value: String(corpus.data.total_docs) },
            { label: "live", value: String(corpus.data.live_docs) },
            { label: "characters", value: corpus.data.total_chars.toLocaleString() },
            { label: "facets", value: String(categories.length) },
          ]}
        />
        <p className="mt-3 font-mono text-[11px] text-white/35">
          An open read over the canonical backend — no identity required.
        </p>
      </Panel>

      <Panel className="mb-4">
        <label className="mb-3 flex flex-col gap-1">
          <span className="font-mono text-[11px] uppercase tracking-widest text-white/40">
            Search the corpus
          </span>
          <input
            type="search"
            value={query}
            onChange={(event) => setQuery(event.target.value)}
            placeholder="label, description, or preview…"
            data-testid="codex-search"
            className="rounded border border-line bg-ink/60 px-3 py-2 text-sm text-white/85 placeholder:text-white/30"
          />
        </label>

        <ul className="flex flex-wrap gap-2" data-testid="codex-categories">
          <li>
            <button
              type="button"
              onClick={() => setCategory(CODEX_ALL_CATEGORIES)}
              aria-pressed={category === CODEX_ALL_CATEGORIES}
              data-testid="codex-category-all"
              className={`rounded border px-2 py-1 font-mono text-[11px] ${
                category === CODEX_ALL_CATEGORIES
                  ? "border-azure/60 bg-azure/10 text-azure"
                  : "border-line text-white/60"
              }`}
            >
              ALL · {documents.length}
            </button>
          </li>
          {categories.map((facet) => (
            <li key={facet.name}>
              <button
                type="button"
                onClick={() => setCategory(facet.name)}
                aria-pressed={category === facet.name}
                data-testid={`codex-category-${facet.name}`}
                className={`rounded border px-2 py-1 font-mono text-[11px] ${
                  category === facet.name
                    ? "border-azure/60 bg-azure/10 text-azure"
                    : "border-line text-white/60"
                }`}
              >
                {facet.name} · {facet.count}
              </button>
            </li>
          ))}
        </ul>
        {/* Facets are derived from the documents, not fetched: the archived
            `/api/codex/categories` route is not served. Stated here so a reader
            is not left guessing where the counts came from. */}
        <p className="mt-3 font-mono text-[11px] text-white/30">
          Facets are derived from the documents themselves — this contract serves no categories
          route.
        </p>
      </Panel>

      <Panel>
        <p className="mb-3 font-mono text-[11px] uppercase tracking-widest text-white/40">
          Documents · {matches.length} match{matches.length === 1 ? "" : "es"}
        </p>

        {matches.length === 0 ? (
          <p className="text-sm text-white/60" data-testid="codex-no-matches">
            No document matches {category === CODEX_ALL_CATEGORIES ? "that search" : `"${category}" with that search`}.
            The corpus itself is not empty — {documents.length} documents were read.
          </p>
        ) : (
          <>
            <ul className="flex flex-col gap-2" data-testid="codex-documents">
              {shown.map((doc) => {
                const isOpen = expanded === doc.key;
                return (
                  <li key={doc.key} className="rounded border border-line bg-ink/40 p-3">
                    <div className="flex items-baseline justify-between gap-3">
                      <p className="text-sm text-white/85">{doc.label ?? doc.key}</p>
                      <p className="font-mono text-[10px] text-white/30">
                        {doc.chars?.toLocaleString() ?? "—"} chars
                      </p>
                    </div>
                    <p className="mt-1 font-mono text-[10px] text-white/35">
                      {doc.category ?? "UNCATEGORISED"}
                      {doc.source ? ` · ${doc.source}` : ""}
                      {doc.priority != null ? ` · priority ${doc.priority}` : ""}
                      {doc.error ? " · fetch error" : ""}
                    </p>
                    {doc.description ? (
                      <p className="mt-2 text-xs text-white/50">{doc.description}</p>
                    ) : null}
                    <button
                      type="button"
                      onClick={() => setExpanded(isOpen ? null : doc.key)}
                      aria-expanded={isOpen}
                      data-testid={`codex-expand-${doc.key}`}
                      className="mt-2 rounded border border-line px-2 py-0.5 font-mono text-[10px] uppercase tracking-widest text-white/50"
                    >
                      {isOpen ? "Collapse" : "Read"}
                    </button>
                    {isOpen ? (
                      <pre className="mt-2 max-h-72 overflow-auto whitespace-pre-wrap rounded border border-line bg-ink/60 p-2 text-xs text-white/70">
                        {doc.content || doc.preview || "This document has no body."}
                      </pre>
                    ) : null}
                    {doc.github_url ? (
                      <a
                        href={doc.github_url}
                        target="_blank"
                        rel="noreferrer noopener"
                        className="mt-2 inline-block font-mono text-[10px] text-azure/70"
                      >
                        source ↗
                      </a>
                    ) : null}
                  </li>
                );
              })}
            </ul>

            {matches.length > CODEX_DISPLAY_LIMIT ? (
              <p
                className="mt-3 font-mono text-[11px] text-white/40"
                data-testid="codex-truncation"
              >
                Showing {CODEX_DISPLAY_LIMIT} of {matches.length} matching documents — the
                remainder is not rendered on this surface.
              </p>
            ) : null}
          </>
        )}
      </Panel>
    </>
  );
}
