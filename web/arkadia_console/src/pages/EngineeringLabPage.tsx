import { Page, Panel, Facts, ContractState, NotYetWired } from "../components/ui";
import { LabSessionList } from "../components/lab/LabSessionList";
import { LabArtifactCanvas } from "../components/lab/LabArtifactCanvas";
import { LabAgentRegistry } from "../components/lab/LabAgentRegistry";
import { LabModelGateway } from "../components/lab/LabModelGateway";
import { LabOperationalSurfaces } from "../components/lab/LabOperationalSurfaces";
import { scalarOverview } from "../components/lab/labOperational";
import { useHydration } from "../lib/useHydration";
import { apiRequest } from "../lib/apiClient";
import { endpoints } from "../lib/endpoints";
import type { NAtlasCatalog } from "../lib/types";

export function EngineeringLabPage() {
  const overview = useHydration<Record<string, unknown>>(endpoints.labEngineeringOverview, (p) =>
    apiRequest<Record<string, unknown>>(p),
  );
  const catalog = useHydration<NAtlasCatalog>(endpoints.labNAtlasCatalog, (p) => apiRequest<NAtlasCatalog>(p));

  return (
    <Page
      title="Engineering Lab"
      subtitle="Technical operations: task state, provider status, execution history, and evidence. Reads are owner-scoped."
    >
      <Panel className="mb-4">
        <p className="mb-3 font-mono text-[11px] uppercase tracking-widest text-white/40">Lab overview</p>
        {overview.state === "ready" && overview.data ? (
          <Facts rows={scalarOverview(overview.data)} />
        ) : (
          <ContractState state={overview.state} error={overview.error?.message} onRetry={overview.reload} />
        )}
      </Panel>

      <LabOperationalSurfaces overview={overview.state === "ready" ? overview.data ?? null : null} />

      <Panel className="mb-4">
        <p className="mb-3 font-mono text-[11px] uppercase tracking-widest text-white/40">N-ATLAS provider (effective state)</p>
        {catalog.state === "ready" && catalog.data ? (
          <Facts
            rows={[
              { label: "status", value: catalog.data.status },
              { label: "detail", value: catalog.data.detail ?? "—" },
            ]}
          />
        ) : (
          <ContractState state={catalog.state} error={catalog.error?.message} onRetry={catalog.reload} />
        )}
        <p className="mt-3 text-xs text-white/40">
          This reports the deployment's effective configuration, not repository defaults.
        </p>
      </Panel>

      <LabSessionList />

      <LabArtifactCanvas />

      <LabAgentRegistry />

      <LabModelGateway />

      <NotYetWired
        contract="/api/lab/engineering/sessions/{id}/execute"
        note="The mutating Lab acts — authorize, execute, transition and run-agent — require a human decision and are not wired to this read-only surface. An approval is not an execution, and a run at the review boundary is not acceptance."
      />
    </Page>
  );
}
