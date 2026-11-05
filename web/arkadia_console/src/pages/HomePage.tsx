import { Page, Panel, Facts, ContractState } from "../components/ui";
import { useAuth } from "../contexts/AuthContext";
import { useHydration } from "../lib/useHydration";
import { apiRequest } from "../lib/apiClient";
import { endpoints } from "../lib/endpoints";
import { SURFACES, type SurfaceId } from "../lib/surfaces";
import type { ProjectList, VersionInfo } from "../lib/types";

function Portal({ surface, onNavigate }: { surface: (typeof SURFACES)[number]; onNavigate: (id: SurfaceId) => void }) {
  return (
    <button
      onClick={() => onNavigate(surface.id)}
      data-testid={`portal-${surface.id}`}
      className="rounded-xl border border-line bg-panel/60 p-4 text-left transition hover:border-emerald/40"
    >
      <p className={`font-mono text-[11px] uppercase tracking-[0.18em] ${surface.accent}`}>{surface.boundary}</p>
      <p className="mt-1 font-display text-lg text-white/90">{surface.name}</p>
      <p className="mt-1 text-sm text-white/50">{surface.summary}</p>
    </button>
  );
}

/**
 * The entry action is identity-aware, the way the archived Prism home was: an
 * authenticated node continues into its personal canvas, an anonymous visitor
 * crosses the sign-in threshold. The archived home rendered exactly one primary
 * entry ("Enter Arkadia" / "Open Solariun") and one secondary
 * ("Sign in / Create Node" / "Open your private field"); the console had no
 * primary action at all — a flat grid of equal-weight portals — so a returning
 * node had no single obvious way back into its workspace.
 *
 * The action targets are declared canonical surfaces, never a second surface:
 * the anonymous primary targets `login` (the real sign-in surface) rather than a
 * decorative gate, because the console has no separate gate surface.
 */
function entryActions(isAuthenticated: boolean): {
  primary: { id: SurfaceId; label: string; body: string };
  secondary: { id: SurfaceId; label: string };
} {
  if (isAuthenticated) {
    return {
      primary: {
        id: "solariun",
        label: "Open Solariun",
        body: "Your identity is verified — continue into your personal workspace and cognitive canvas.",
      },
      secondary: { id: "solspire", label: "Open the team workspace" },
    };
  }
  return {
    primary: {
      id: "login",
      label: "Enter Arkadia",
      body: "Sign in to open personal workspaces and governed execution. The public surfaces below need no identity.",
    },
    secondary: { id: "about", label: "See the architecture" },
  };
}

/**
 * The workspace overview: recent projects, current work, and shortcuts into the
 * main capabilities. Every reading is a real contract read; a signed-out visitor
 * sees the honest threshold rather than a zeroed dashboard.
 */
function WorkspaceOverview({ onNavigate }: { onNavigate: (id: SurfaceId, section?: string) => void }) {
  const { isAuthenticated } = useAuth();
  const projects = useHydration<ProjectList>(endpoints.solspireProjects, (p) => apiRequest<ProjectList>(p), [
    isAuthenticated,
  ]);

  return (
    <div className="mb-8 grid gap-4 lg:grid-cols-2">
      <Panel data-testid="home-recent-projects">
        <div className="mb-3 flex items-baseline justify-between gap-3">
          <p className="font-mono text-[11px] uppercase tracking-widest text-white/40">Recent projects</p>
          <button
            type="button"
            onClick={() => onNavigate("projects")}
            data-testid="home-open-projects"
            className="font-mono text-[10px] uppercase tracking-widest text-emerald/80 hover:text-emerald"
          >
            All projects
          </button>
        </div>
        {projects.state === "ready" && projects.data ? (
          projects.data.count === 0 ? (
            <p className="text-sm text-white/50">No projects yet — create one to begin.</p>
          ) : (
            <ul className="flex flex-col gap-2">
              {projects.data.projects.slice(0, 5).map((p) => (
                <li key={p.id} className="rounded border border-line bg-ink/40 p-3">
                  <button
                    type="button"
                    onClick={() => onNavigate("projects", p.id)}
                    data-testid={`home-project-${p.id}`}
                    className="text-left"
                  >
                    <span className="text-sm text-white/85">{p.name}</span>
                  </button>
                  <p className="mt-1 font-mono text-[10px] uppercase tracking-widest text-white/35">
                    {p.status ?? "active"}
                  </p>
                </li>
              ))}
            </ul>
          )
        ) : (
          <ContractState state={projects.state} error={projects.error?.message} onRetry={projects.reload} />
        )}
      </Panel>

      <Panel data-testid="home-shortcuts">
        <p className="mb-3 font-mono text-[11px] uppercase tracking-widest text-white/40">Shortcuts</p>
        <div className="flex flex-col gap-2">
          {(
            [
              { id: "arkana" as SurfaceId, label: "Ask Arkana", body: "Conversational intelligence over the shared spine." },
              { id: "engineering-lab" as SurfaceId, label: "Engineering Lab", body: "Sessions, evidence, and bounded execution." },
              { id: "weaver" as SurfaceId, label: "Weaver", body: "Governed execution — proposal, approval, verification." },
              { id: "knowledge" as SurfaceId, label: "Knowledge OS", body: "Continuity, memory, and the knowledge graph." },
            ]
          ).map((s) => (
            <button
              key={s.id}
              type="button"
              onClick={() => onNavigate(s.id)}
              data-testid={`home-shortcut-${s.id}`}
              className="rounded border border-line bg-ink/40 p-3 text-left transition hover:border-gold/40"
            >
              <p className="text-sm text-white/85">{s.label}</p>
              <p className="mt-0.5 text-xs text-white/45">{s.body}</p>
            </button>
          ))}
        </div>
      </Panel>
    </div>
  );
}

export function HomePage({ onNavigate }: { onNavigate: (id: SurfaceId, section?: string) => void }) {
  const { isAuthenticated } = useAuth();
  const version = useHydration<VersionInfo>(endpoints.version, (p) => apiRequest<VersionInfo>(p));
  const entry = entryActions(isAuthenticated);

  return (
    <Page
      title="ARKADIA"
      subtitle="One coherent application over the canonical backend. Identity, workspace, and governed execution share a single spine."
    >
      <Panel className="mb-6 overflow-hidden" tone="gold">
        <div className="flex flex-col gap-6 sm:flex-row sm:items-center">
          <span className="cg-orb cg-orb-float h-16 w-16 flex-none" aria-hidden="true" />
          <div className="min-w-0 flex-1">
            <p className="cg-eyebrow mb-1.5">
              {isAuthenticated ? "Entry · signed in" : "Entry · not signed in"}
            </p>
            <p className="text-[13.5px] leading-relaxed text-white/60">{entry.primary.body}</p>
            <div className="mt-4 flex flex-wrap gap-2.5">
              <button
                onClick={() => onNavigate(entry.primary.id)}
                data-testid="home-entry-primary"
                className="cg-btn cg-btn-primary"
              >
                {entry.primary.label}
              </button>
              <button
                onClick={() => onNavigate(entry.secondary.id)}
                data-testid="home-entry-secondary"
                className="cg-btn"
              >
                {entry.secondary.label}
              </button>
            </div>
          </div>
        </div>
      </Panel>

      {isAuthenticated ? (
        <WorkspaceOverview onNavigate={onNavigate} />
      ) : (
        <Panel className="mb-8 border-dashed border-line" data-testid="home-first-use">
          <p className="font-mono text-[11px] uppercase tracking-widest text-white/40">First use</p>
          <p className="mt-2 text-[13px] leading-relaxed text-white/65">
            Sign in to open your workspace overview — recent projects, current work, and shortcuts into
            Arkana, the Engineering Lab, Weaver, and the Knowledge OS. The public surfaces below need no
            identity.
          </p>
        </Panel>
      )}

      <div className="mb-8 grid gap-3 sm:grid-cols-2">
        {SURFACES.filter((s) => s.id !== "home").map((s) => (
          <Portal key={s.id} surface={s} onNavigate={onNavigate} />
        ))}
      </div>

      <Panel>
        <p className="mb-3 font-mono text-[11px] uppercase tracking-widest text-white/40">Canonical runtime</p>
        {version.state === "ready" && version.data ? (
          <Facts
            rows={[
              { label: "service", value: version.data.service },
              { label: "deployment", value: version.data.canonical_deployment },
              { label: "revision", value: <span className="font-mono text-xs">{version.data.source_revision ?? "unknown"}</span> },
              { label: "source", value: version.data.revision_source },
              { label: "conflict", value: String(version.data.revision_conflict) },
            ]}
          />
        ) : (
          <ContractState state={version.state} error={version.error?.message} onRetry={version.reload} />
        )}
        <p className="mt-4 text-xs text-white/35">
          {isAuthenticated
            ? "Your private workspace is open."
            : "Sign in to open personal workspaces and governed execution."}
        </p>
      </Panel>
    </Page>
  );
}
