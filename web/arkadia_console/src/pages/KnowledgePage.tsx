import { Page, Panel, Facts, ContractState } from "../components/ui";
import { useHydration } from "../lib/useHydration";
import { ApiError, apiRequest } from "../lib/apiClient";
import { endpoints } from "../lib/endpoints";
import {
  requireKnowledgeStatusReading,
  type KnowledgeStatusReading,
} from "./knowledge/knowledgeContracts";
import { KnowledgeGraphPanel } from "./knowledge/KnowledgeGraphPanel";
import { KnowledgeSearchPanel } from "../components/knowledge/KnowledgeSearchPanel";
import { KnowledgeTimelinePanel } from "../components/knowledge/KnowledgeTimelinePanel";
import { KnowledgeProjectsPanel } from "../components/knowledge/KnowledgeProjectsPanel";

/**
 * The status handler answers `200 {"status":"error", ...}` for a failed read, so
 * the status code cannot be trusted as the reading. The body is validated
 * through the shared contract reader, which keeps a dead vault from rendering as
 * a zeroed one — and keeps this reader from dereferencing `vault.notes` on the
 * handler's failure envelope.
 */
async function readStatus(path: string): Promise<KnowledgeStatusReading> {
  const payload = await apiRequest<unknown>(path);
  try {
    return requireKnowledgeStatusReading(payload);
  } catch (err) {
    throw new ApiError(
      err instanceof Error ? err.message : "The knowledge status contract returned an unrecognised shape.",
      { kind: "UNKNOWN", path },
    );
  }
}

export function KnowledgePage() {
  const status = useHydration<KnowledgeStatusReading>(endpoints.knowledgeStatus, readStatus);

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
        <KnowledgeSearchPanel endpoint={endpoints.knowledgeSearch} />
      </div>

      <div className="mt-4">
        <KnowledgeTimelinePanel />
      </div>

      <div className="mt-4">
        <KnowledgeProjectsPanel />
      </div>
    </Page>
  );
}
