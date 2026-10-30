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
import { LabRepositoryContext } from "../components/lab/LabRepositoryContext";
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

      <LabRepositoryContext />

      <LabSessionList />

      <LabArtifactCanvas />

      <LabAgentRegistry />

      <LabModelGateway />

      <LabAutomationGrammar />

      <NotYetWired
        contract="/api/lab/engineering/sessions/{session_id}/transition"
        note="The mission workspace above wires exactly one bounded act: a read-only mission that creates a session, records a human authorize decision, and executes a single read-only run to the review boundary. The remaining mutating Lab acts — transition, run-agent, merge and production deploy — require a separate human decision and are not wired to this surface. An approval is not an execution, and a run at the review boundary is not acceptance."
      />
    </Page>
  );
}
