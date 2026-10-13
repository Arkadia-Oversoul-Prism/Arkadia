import { Page, Panel, Facts, ContractState, NotYetWired } from "../components/ui";
import { OpportunityRadarSection } from "../components/opportunities/OpportunityRadarSection";
import { SolSpireControlPlane } from "../components/solspire/SolSpireControlPlane";
import { useAuth } from "../contexts/AuthContext";
import { useHydration } from "../lib/useHydration";
import { apiRequest } from "../lib/apiClient";
import { endpoints } from "../lib/endpoints";
import type { ProjectList } from "../lib/types";

export function SolSpirePage() {
  const { isAuthenticated } = useAuth();
  const projects = useHydration<ProjectList>(
    endpoints.solspireProjects,
    (p) => apiRequest<ProjectList>(p),
    [isAuthenticated],
  );

  return (
    <Page title="SolSpire" subtitle="Team and enterprise workspace over the same canonical substrate.">
      <Panel className="mb-4">
        <p className="mb-3 font-mono text-[11px] uppercase tracking-widest text-white/40">Workspace projects</p>
        {projects.state === "ready" && projects.data ? (
          <Facts rows={[{ label: "count", value: String(projects.data.count) }]} />
        ) : (
          <ContractState state={projects.state} error={projects.error?.message} onRetry={projects.reload} />
        )}
      </Panel>

      <Panel className="mb-4">
        <p className="mb-3 font-mono text-[11px] uppercase tracking-widest text-white/40">
          Project field · Opportunity Radar
        </p>
        {projects.state === "ready" && projects.data ? (
          <OpportunityRadarSection projects={projects.data.projects} />
        ) : (
          <p className="text-sm text-white/60">
            The project list must load before a project board can be selected. This is not an empty
            opportunity board.
          </p>
        )}
      </Panel>

      <div className="mb-4">
        <SolSpireControlPlane />
      </div>

      <div className="grid gap-4 md:grid-cols-2">
        <NotYetWired
          contract="/solspire/proposals"
          note="Proposal reads and the proposal decision endpoint are served, but a decision is a human act on the authority chain, so the console does not offer one yet."
        />
        <NotYetWired
          contract="/solspire/workevents"
          note="The work-event spine is served (list and single reads), but it is a provenance record whose event refs are not reconciled with the console's provenance surface yet."
        />
        <NotYetWired
          contract="/solspire/enterprise/workspaces"
          note="Enterprise workspace dashboards, control-room, tasks and members are served, but the console has no enterprise workspace projection yet."
        />
        <NotYetWired
          contract="/solspire/voice/events"
          note="Voice-boundary events and their chain are served, but the governed chain (understand → propose → authorize → execute → verify) has no console surface yet."
        />
      </div>
    </Page>
  );
}
