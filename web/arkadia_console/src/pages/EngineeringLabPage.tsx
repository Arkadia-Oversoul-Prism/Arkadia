import { Page, Panel, Facts, ContractState, NotYetWired } from "../components/ui";
import { LabSessionList } from "../components/lab/LabSessionList";
import { LabAuthorityReadings } from "../components/lab/LabAuthorityReadings";
import type { LabGovernanceSource } from "../components/lab/labGovernance";
import { LabArtifactCanvas } from "../components/lab/LabArtifactCanvas";
import { LabAgentRegistry } from "../components/lab/LabAgentRegistry";
import { LabModelGateway } from "../components/lab/LabModelGateway";
import { LabAutomationGrammar } from "../components/lab/LabAutomationGrammar";
import { LabOperationalSurfaces } from "../components/lab/LabOperationalSurfaces";
import { scalarOverview } from "../components/lab/labOperational";
import { ExecutionLoop } from "../components/lab/ExecutionLoop";
import { MissionWorkspace } from "../components/lab/MissionWorkspace";
import { useHydration } from "../lib/useHydration";
import { apiRequest } from "../lib/apiClient";
import { endpoints } from "../lib/endpoints";
import type { NAtlasCatalog } from "../lib/types";

/** The runtime's own loop definition, read directly from the overview response.
 *  A malformed payload yields no stages, so the surface reports an unfilled
 *  definition rather than inferring one. */
function readLoopStages(overview: Record<string, unknown> | null): string[] {
  const loop = overview?.loop;
  return Array.isArray(loop) ? loop.filter((stage): stage is string => typeof stage === "string") : [];
}

export function EngineeringLabPage() {
  const overview = useHydration<Record<string, unknown>>(endpoints.labEngineeringOverview, (p) =>
    apiRequest<Record<string, unknown>>(p),
  );
  const catalog = useHydration<NAtlasCatalog>(endpoints.labNAtlasCatalog, (p) => apiRequest<NAtlasCatalog>(p));

  return (
    <Page
      title="Engineering Lab"
      subtitle="Plan and run bounded engineering work with explicit human authorization. Technical evidence and diagnostics remain available on demand."
    >
      <MissionWorkspace />

      <details
        className="mb-4 rounded-lg border border-line bg-ink/40"
        data-testid="lab-engineering-details"
      >
        <summary className="cursor-pointer px-4 py-3 font-mono text-[11px] uppercase tracking-widest text-white/60 hover:text-white focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-gold">
          Engineering evidence &amp; diagnostics
        </summary>
        <div className="space-y-4 border-t border-line p-3 md:p-4">
        <Panel className="mb-4">
          <p className="mb-3 font-mono text-[11px] uppercase tracking-widest text-white/40">Lab overview</p>
          {overview.state === "ready" && overview.data ? (
            <Facts rows={scalarOverview(overview.data)} />
          ) : (
            <ContractState state={overview.state} error={overview.error?.message} onRetry={overview.reload} />
          )}
        </Panel>
  
        <LabOperationalSurfaces overview={overview.state === "ready" ? overview.data ?? null : null} />
  
        <ExecutionLoop stages={readLoopStages(overview.state === "ready" ? overview.data : null)} />
  
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
  
        <LabAuthorityReadings source={overview.data as LabGovernanceSource | null} />
  
  
        <LabSessionList />
  
        <LabArtifactCanvas />
  
        <LabAgentRegistry />
  
        <LabModelGateway />
  
        <LabAutomationGrammar />
  
        <NotYetWired
          contract="/api/lab/engineering/sessions/{session_id}/transition"
          note="The mission workspace above wires exactly one bounded act: a read-only mission that creates a session, records a human authorize decision, and executes a single read-only run to the review boundary. The remaining mutating Lab acts — transition, run-agent, merge and production deploy — require a separate human decision and are not wired to this surface. An approval is not an execution, and a run at the review boundary is not acceptance."
        />
        </div>
      </details>
    </Page>
  );
}
