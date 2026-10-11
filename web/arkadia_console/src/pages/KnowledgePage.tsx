import { Page, Panel, Facts, ContractState, NotYetWired } from "../components/ui";
import { useHydration } from "../lib/useHydration";
import { apiRequest } from "../lib/apiClient";
import { endpoints } from "../lib/endpoints";
import type { KnowledgeStatus } from "../lib/types";
import { KnowledgeGraphPanel } from "./knowledge/KnowledgeGraphPanel";
import { KnowledgeSearchPanel } from "../components/knowledge/KnowledgeSearchPanel";

/**
 * The shared endpoint registry (`lib/endpoints.ts`) is owned by Workstream 1.
 * The verified `POST /api/knowledge/search` path is not yet an entry there, so it
 * is read through the registry *shape* rather than a named property: referencing
 * `endpoints.knowledgeSearch` directly would not compile until Workstream 1 adds
 * it, and inventing a page-local path is the second-registry defect §3.1 forbids.
 *
 * When the registry carries the path the panel mounts; until then the surface
 * shows the blocked state below instead of requesting an unregistered endpoint.
 */
function registeredSearchEndpoint(): string | null {
  const value = (endpoints as Record<string, string | undefined>)["knowledgeSearch"];
  return typeof value === "string" && value.startsWith("/") ? value : null;
}

export function KnowledgePage() {
  const status = useHydration<KnowledgeStatus>(endpoints.knowledgeStatus, (p) => apiRequest<KnowledgeStatus>(p));
  const searchEndpoint = registeredSearchEndpoint();

  return (
    <Page title="Knowledge OS" subtitle="Continuity, memory, and the knowledge graph — the shared memory substrate.">
      <Panel>
        <p className="mb-3 font-mono text-[11px] uppercase tracking-widest text-white/40">Vault status</p>
        {status.state === "ready" && status.data ? (
          <div className="flex flex-col gap-5">
            <Facts
              rows={[
                { label: "health", value: status.data.status },
                { label: "notes", value: String(status.data.vault.notes) },
                { label: "chunks", value: String(status.data.vault.chunks) },
                { label: "embeddings", value: String(status.data.vault.embeddings) },
                { label: "pending", value: String(status.data.vault.pending_embeddings) },
                { label: "graph edges", value: String(status.data.graph.edges) },
                { label: "timeline", value: String(status.data.timeline.events) },
                { label: "graph health", value: status.data.graph_health },
                { label: "last ingestion", value: status.data.last_ingestion ?? "—" },
              ]}
            />
            <div>
              <p className="mb-2 font-mono text-[11px] uppercase tracking-widest text-white/40">Nodes by type</p>
              <ul className="flex flex-wrap gap-2">
                {Object.entries(status.data.nodes_by_type).map(([type, count]) => (
                  <li key={type} className="rounded border border-line px-2 py-1 font-mono text-[11px] text-white/60">
                    {type} · {count}
                  </li>
                ))}
              </ul>
            </div>
          </div>
        ) : (
          <ContractState state={status.state} error={status.error?.message} onRetry={status.reload} />
        )}
      </Panel>

      <div className="mt-4">
        <KnowledgeGraphPanel />
      </div>

      <div className="mt-4">
        {searchEndpoint ? (
          <KnowledgeSearchPanel endpoint={searchEndpoint} />
        ) : (
          <NotYetWired
            contract="/api/knowledge/search"
            note="Verified handler contract (POST, optional auth, backend-enforced ownership), but the shared endpoint registry does not yet carry it. A precise integration request was sent to Workstream 1; the panel is implemented and mounts as soon as the registry entry exists."
          />
        )}
      </div>

      <div className="mt-4">
        <NotYetWired
          contract="/api/knowledge/timeline"
          note="Continuity and the memory timeline are declared contracts, not yet wired into this surface."
        />
      </div>
    </Page>
  );
}
