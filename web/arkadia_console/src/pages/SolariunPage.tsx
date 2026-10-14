/**
 * Solariun — the personal workspace and cognitive canvas.
 *
 * The lens strip is real navigation: every lens routes to `/solariun/<id>`
 * through the shared router, so the strip and the address bar cannot disagree
 * (the same contract `SurfaceLenses` already enforces for NovaNet). The archived
 * Prism declared these lenses as routed sub-views of `/solariun`
 * (`SolariunConsole` → `SolSpireExperience`, lenses overview/projects/knowledge/
 * memory/weaver/…); the console reconciles that vocabulary to four lenses and
 * gives each one a truthful state:
 *
 *  - `projects`  — the real `/solspire/projects` read (owner-scoped), plus the
 *                  per-project runtime-context canvas over its bounded
 *                  projection contract.
 *  - `knowledge` — the knowledge authority is the canonical Knowledge OS surface;
 *                  this lens points there instead of duplicating its read.
 *  - `weaver`    — the governance authority is the canonical Weaver surface;
 *                  same rule: point, do not fork.
 *  - `memory`    — the personal Echofeild read model (`/api/me/field`), with
 *                  per-source provenance from the canonical contract.
 *
 * A section outside the declared lens set renders an honest "not a lens" state
 * listing the reconciled lenses — previously `/solariun/bogus` silently showed
 * the projects view, leaving the address bar claiming something false.
 */
import { useState } from "react";
import { Page, Panel, Facts, ContractState, NotYetWired } from "../components/ui";
import { SurfaceLenses } from "../components/SurfaceLenses";
import { ProjectRuntimeCanvas } from "../components/solariun/ProjectRuntimeCanvas";
import { PersonalFieldPanel } from "../components/solariun/PersonalFieldPanel";
import { useAuth } from "../contexts/AuthContext";
import { useHydration } from "../lib/useHydration";
import { apiRequest } from "../lib/apiClient";
import { endpoints } from "../lib/endpoints";
import type { SurfaceId } from "../lib/surfaces";
import type { NodeProfile, ProjectList } from "../lib/types";

/**
 * Sentinel, not a path: `NotYetWired` takes the advertised contract string, and
 * UNKNOWN is the repository's classification for a claim that is not established
 * (PUBLIC_SURFACE.md). It is a named constant so it reads as a classification,
 * not an advertised route.
 */
const UNKNOWN_CONTRACT = "UNKNOWN";

const LENSES = [
  { id: "projects", label: "Projects" },
  { id: "knowledge", label: "Knowledge" },
  { id: "memory", label: "Memory" },
  { id: "weaver", label: "Weaver" },
];

/** The lens ids this surface declares; a section outside this set is not a lens. */
const LENS_IDS = new Set(LENSES.map((l) => l.id));

/**
 * Lenses whose authority lives on another canonical surface. One intelligence,
 * many interfaces: this lens names the canonical owner and offers the real
 * navigation to it rather than re-reading the same contract here.
 */
const OWNING_SURFACE: Record<string, { surface: SurfaceId; name: string; body: string }> = {
  knowledge: {
    surface: "knowledge",
    name: "Knowledge OS",
    body: "Continuity, memory, and the knowledge graph are read from the canonical Knowledge OS surface over /api/knowledge/*. This lens does not duplicate that read.",
  },
  weaver: {
    surface: "weaver",
    name: "Weaver",
    body: "Proposal, approval, execution, and verification are read from the canonical Weaver surface over /api/approvals and the Lab session view. This lens does not duplicate that read.",
  },
};

export function SolariunPage({
  section = "projects",
  onNavigate,
}: {
  section?: string;
  onNavigate: (id: SurfaceId, section?: string) => void;
}) {
  const { profile, isAuthenticated, identityState } = useAuth();
  const [selectedProject, setSelectedProject] = useState<string | null>(null);
  const projects = useHydration<ProjectList>(
    endpoints.solspireProjects,
    (p) => apiRequest<ProjectList>(p),
    [isAuthenticated],
  );
  const owner = OWNING_SURFACE[section];

  return (
    <Page title="Solariun" subtitle="Your personal workspace and cognitive canvas — projects, knowledge, and continuity.">
      <SurfaceLenses
        surface="solariun"
        lenses={LENSES}
        section={section}
        accent="text-violet"
        onNavigate={onNavigate}
      />

      <Panel className="mb-4">
        <p className="mb-3 font-mono text-[11px] uppercase tracking-widest text-white/40">Identity</p>
        {identityState === "ready" && profile ? (
          <Facts
            rows={[
              { label: "name", value: (profile as NodeProfile).display_name },
              { label: "role", value: `${profile.role_sigil} ${profile.role}` },
              { label: "node", value: profile.node_key ?? "—" },
              { label: "access", value: String(profile.access_level) },
            ]}
          />
        ) : (
          <div>
            <ContractState
              state={identityState === "ready" ? "error" : identityState === "loading" ? "loading" : "auth-required"}
              error={identityState === "auth-error" ? "Identity was rejected." : null}
            />
          </div>
        )}
      </Panel>

      {section === "projects" && (
        <Panel>
          <p className="mb-3 font-mono text-[11px] uppercase tracking-widest text-white/40">Projects</p>
          {projects.state === "ready" && projects.data ? (
            projects.data.count === 0 ? (
              <p className="text-sm text-white/50">No projects yet in this workspace.</p>
            ) : (
              <ul className="flex flex-col gap-2">
                {projects.data.projects.map((p) => (
                  <li key={p.id} className="rounded border border-line bg-ink/40 p-3">
                    <div className="flex items-baseline justify-between gap-3">
                      <p className="text-sm text-white/85">{p.name}</p>
                      <button
                        type="button"
                        onClick={() => setSelectedProject((current) => (current === p.id ? null : p.id))}
                        aria-pressed={selectedProject === p.id}
                        data-testid={`solariun-runtime-${p.id}`}
                        className="shrink-0 rounded border border-white/15 px-2 py-1 font-mono text-[10px] uppercase tracking-widest text-white/50 hover:text-white/80"
                      >
                        Runtime
                      </button>
                    </div>
                    <p className="font-mono text-[11px] text-white/40">{p.status ?? "active"}</p>
                  </li>
                ))}
              </ul>
            )
          ) : (
            <ContractState state={projects.state} error={projects.error?.message} onRetry={projects.reload} />
          )}
        </Panel>
      )}

      {section === "projects" && selectedProject && (
        <div className="mt-4">
          <ProjectRuntimeCanvas projectId={selectedProject} />
        </div>
      )}

      {owner && (
        <div data-testid="solariun-authority-owner">
          <Panel>
            <p className="font-display text-lg text-gold">Authority lives on {owner.name}</p>
            <p className="mt-1 text-sm text-white/60">{owner.body}</p>
            <button
              type="button"
              onClick={() => onNavigate(owner.surface)}
              data-testid={`solariun-open-${owner.surface}`}
              className="mt-4 rounded border border-gold/40 bg-gold/10 px-3 py-1.5 font-mono text-[11px] uppercase tracking-widest text-gold"
            >
              Open {owner.name}
            </button>
          </Panel>
        </div>
      )}

      {section === "memory" && <PersonalFieldPanel />}

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
