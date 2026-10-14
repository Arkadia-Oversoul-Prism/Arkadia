/**
 * Knowledge OS — readable knowledge graph.
 *
 * Reads the declared `GET /api/knowledge/graph` contract through the shared
 * client and renders the viewer's *scope*, not a graph the viewer cannot see.
 * The backend decides what is readable (own notes plus the public corpus); this
 * panel reports that decision and never substitutes mock data for an empty or
 * refused answer.
 */
import { Panel, Facts, ContractState } from "../../components/ui";
import { useAuth } from "../../contexts/AuthContext";
import { useHydration } from "../../lib/useHydration";
import { apiRequest, ApiError } from "../../lib/apiClient";
import { endpoints } from "../../lib/endpoints";
import {
  isKnowledgeGraphData,
  summarizeGraph,
  summarizeProvenance,
  summarizeAuthorship,
  provenanceReading,
  provenanceNotice,
  authorshipReading,
  authorshipNotice,
  scopeNotice,
  type KnowledgeGraphData,
  type ViewerKind,
} from "./knowledgeContracts";

/** Cap on the per-node provenance rows rendered, so a large scope cannot turn
 *  the reading into an unbounded list. The count facts above stay exact. */
const PROVENANCE_ROWS = 8;

async function readGraph(path: string): Promise<KnowledgeGraphData> {
  const payload = await apiRequest<unknown>(path);
  if (!isKnowledgeGraphData(payload)) {
    throw new ApiError("The knowledge graph contract returned an unrecognised shape.", {
      kind: "UNKNOWN",
      path,
    });
  }
  return payload;
}

export function KnowledgeGraphPanel() {
  const { isAuthenticated } = useAuth();
  const viewer: ViewerKind = isAuthenticated ? "authenticated" : "anonymous";

  const graph = useHydration<KnowledgeGraphData>(endpoints.knowledgeGraph, readGraph, [isAuthenticated]);

  return (
    <Panel data-testid="knowledge-graph-panel">
      <p className="mb-3 font-mono text-[11px] uppercase tracking-widest text-white/40">Knowledge graph</p>
      {graph.state === "ready" && graph.data ? (
        <GraphReading graph={graph.data} viewer={viewer} />
      ) : (
        <ContractState state={graph.state} error={graph.error?.message} onRetry={graph.reload} />
      )}
    </Panel>
  );
}

function GraphReading({ graph, viewer }: { graph: KnowledgeGraphData; viewer: ViewerKind }) {
  const summary = summarizeGraph(graph);
  const notice = scopeNotice(summary.scope, viewer);
  const provenance = summarizeProvenance(graph);
  const provenanceCopy = provenanceNotice(provenance);
  const authorship = summarizeAuthorship(graph);
  const authorshipCopy = authorshipNotice(authorship);

  return (
    <div className="flex flex-col gap-4">
      <Facts
        rows={[
          { label: "nodes", value: String(summary.nodes) },
          { label: "edges", value: String(summary.edges) },
          { label: "scope", value: summary.scope },
          { label: "viewer", value: viewer },
          { label: "captured origin", value: String(provenance.captured) },
          { label: "origin unknown", value: String(provenance.unknown) },
          { label: "author declared", value: String(authorship.declared) },
          { label: "author not declared", value: String(authorship.undeclared) },
        ]}
      />

      {notice && (
        <p data-testid="knowledge-graph-scope" className="text-sm text-white/50">
          {notice}
        </p>
      )}

      {provenanceCopy && (
        <p data-testid="knowledge-graph-provenance" className="text-sm text-white/50">
          {provenanceCopy}
        </p>
      )}

      {authorshipCopy && (
        <p data-testid="knowledge-graph-authorship" className="text-sm text-white/50">
          {authorshipCopy}
        </p>
      )}

      {graph.nodes.length > 0 && (
        <ul className="flex flex-col gap-1" data-testid="knowledge-graph-provenance-rows">
          {graph.nodes.slice(0, PROVENANCE_ROWS).map((node) => (
            <li key={node.id} className="font-mono text-[11px] text-white/60">
              {node.title} · {provenanceReading(node)} · {authorshipReading(node)}
            </li>
          ))}
        </ul>
      )}

      {summary.titles.length > 0 && (
        <ul className="flex flex-wrap gap-2">
          {summary.titles.map((title) => (
            <li key={title} className="rounded border border-line px-2 py-1 font-mono text-[11px] text-white/60">
              {title}
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
