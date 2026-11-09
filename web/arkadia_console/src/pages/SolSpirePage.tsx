/**
 * SolSpire — the team and enterprise workspace over the shared substrate.
 *
 * The archived Prism expressed this surface as a set of routed lenses
 * (`SolSpireExperience` → `LensContent`: `opportunity-radar` labelled "Field",
 * plus the enterprise/commercial/voice vocabulary). The console reconciles that
 * vocabulary into the **same** navigation and interaction system the rest of the
 * product uses — the shared `SurfaceLenses` strip — so the surface's sections are
 * addressable at `/enterprise/<lens>` and the strip and the address bar cannot
 * disagree.
 *
 * Each lens carries a truthful state:
 *
 *  - `field`      — the archived `opportunity-radar` lens ("Where can Eden
 *                   transact?"): the real project field read through the
 *                   Opportunity Radar, plus the control-plane spine.
 *  - `enterprise` — the served `/solspire/enterprise/workspaces` family; the
 *                   console has no enterprise workspace projection yet, so the
 *                   lens says exactly that rather than rendering an empty board.
 *  - `voice`      — the served governed voice chain; no console surface yet.
 *  - `proposals`  — the served proposal and work-event spines; a decision is a
 *                   human act on the authority chain, so no control is offered.
 *
 * A section outside the declared lens set renders an honest "not a lens" state
 * listing the reconciled lenses, rather than silently showing the field view.
 */
import { Page, Panel, Facts, ContractState, NotYetWired } from "../components/ui";
import { SurfaceLenses } from "../components/SurfaceLenses";
import { OpportunityRadarSection } from "../components/opportunities/OpportunityRadarSection";
import { SolSpireControlPlane } from "../components/solspire/SolSpireControlPlane";
import { useAuth } from "../contexts/AuthContext";
import { useHydration } from "../lib/useHydration";
import { apiRequest } from "../lib/apiClient";
import { endpoints } from "../lib/endpoints";
import type { SurfaceId } from "../lib/surfaces";
import type { ProjectList } from "../lib/types";

/**
 * Sentinel, not a path: `NotYetWired` takes the advertised contract string, and
 * UNKNOWN is the repository's classification for a claim that is not established
 * (PUBLIC_SURFACE.md). It is a named constant so it reads as a classification,
 * not an advertised route.
 */
const UNKNOWN_CONTRACT = "UNKNOWN";

const LENSES = [
  { id: "field", label: "Field" },
  { id: "enterprise", label: "Enterprise" },
  { id: "voice", label: "Voice" },
  { id: "proposals", label: "Proposals" },
];

/** The lens ids this surface declares; a section outside this set is not a lens. */
const LENS_IDS = new Set(LENSES.map((l) => l.id));

export function SolSpirePage({
  section = "field",
  onNavigate,
}: {
  section?: string;
  onNavigate: (id: SurfaceId, section?: string) => void;
}) {
  const { isAuthenticated } = useAuth();
  const projects = useHydration<ProjectList>(
    endpoints.solspireProjects,
    (p) => apiRequest<ProjectList>(p),
    [isAuthenticated],
  );

  return (
    <Page title="SolSpire" subtitle="Team and enterprise workspace over the same canonical substrate.">
      <SurfaceLenses
        surface="solspire"
        lenses={LENSES}
        section={section}
        accent="text-gold"
        onNavigate={onNavigate}
      />

      <Panel className="mb-4">
        <p className="mb-3 font-mono text-[11px] uppercase tracking-widest text-white/40">Workspace projects</p>
        {projects.state === "ready" && projects.data ? (
          <Facts rows={[{ label: "count", value: String(projects.data.count) }]} />
        ) : (
          <ContractState state={projects.state} error={projects.error?.message} onRetry={projects.reload} />
        )}
      </Panel>

      {section === "field" && (
        <>
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
        </>
      )}

      {section === "enterprise" && (
        <NotYetWired
          contract="/solspire/enterprise/workspaces"
          note="Enterprise workspace dashboards, control-room, tasks and members are served, but the console has no enterprise workspace projection yet."
        />
      )}

      {section === "voice" && (
        <NotYetWired
          contract="/solspire/voice/events"
          note="Voice-boundary events and their chain are served, but the governed chain (understand → propose → authorize → execute → verify) has no console surface yet."
        />
      )}

      {section === "proposals" && (
        <div className="grid gap-4 md:grid-cols-2">
          <NotYetWired
            contract="/solspire/proposals"
            note="Proposal reads and the proposal decision endpoint are served, but a decision is a human act on the authority chain, so the console does not offer one yet."
          />
          <NotYetWired
            contract="/solspire/workevents"
            note="The work-event spine is served (list and single reads), but it is a provenance record whose event refs are not reconciled with the console's provenance surface yet."
          />
        </div>
      )}

      {!LENS_IDS.has(section) && (
        <NotYetWired
          contract={UNKNOWN_CONTRACT}
          note={`"${section}" is not a lens of this surface. The reconciled lenses are ${[...LENS_IDS]
            .map((id) => `"${id}"`)
            .join(", ")}.`}
        />
      )}
    </Page>
  );
}
