import { Page, Panel, Facts, ContractState } from "../components/ui";
import { useHydration } from "../lib/useHydration";
import { apiRequest } from "../lib/apiClient";
import { endpoints } from "../lib/endpoints";
import type { KnowledgeStatus } from "../lib/types";

export function KnowledgePage() {
  const status = useHydration<KnowledgeStatus>(endpoints.knowledgeStatus, (p) => apiRequest<KnowledgeStatus>(p));

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
    </Page>
  );
}
