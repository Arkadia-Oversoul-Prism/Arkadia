import { Page, Panel, Facts, ContractState, NotYetWired } from "../components/ui";
import { OpportunityRadarSection } from "../components/opportunities/OpportunityRadarSection";
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

      <div className="grid gap-4 md:grid-cols-2">
        <NotYetWired contract="/api/solspire/workloads" note="Team workload and assignment views." />
        <NotYetWired contract="/api/solspire/proposals" note="Proposal and work-event surfaces." />
        <NotYetWired contract="/api/solspire/pulses" note="Pulse and synthesis surfaces." />
        <NotYetWired contract="/api/solspire/voice" note="Voice boundary for governed operations." />
      </div>
    </Page>
  );
}
