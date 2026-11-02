import { Page, Panel, Facts, ContractState } from "../components/ui";
import { MissionWorkspace } from "../components/lab/MissionWorkspace";
import { useAuth } from "../contexts/AuthContext";
import { useHydration } from "../lib/useHydration";
import { apiRequest } from "../lib/apiClient";
import { endpoints } from "../lib/endpoints";
import { SURFACES, type SurfaceId } from "../lib/surfaces";
import type { VersionInfo } from "../lib/types";

function Portal({ surface, onNavigate }: { surface: (typeof SURFACES)[number]; onNavigate: (id: SurfaceId) => void }) {
  return (
    <button
      onClick={() => onNavigate(surface.id)}
      data-testid={`portal-${surface.id}`}
      type="button"
      className="group home-portal flex min-h-[5.5rem] flex-col rounded-xl border border-line/90 bg-panel/50 p-3.5 text-left transition duration-150 hover:border-white/15 hover:bg-panel/80 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-emerald/60 sm:min-h-0 sm:p-4"
    >
      <p className={`font-mono text-[10px] uppercase tracking-[0.2em] ${surface.accent}`}>{surface.boundary}</p>
      <p className="mt-1.5 font-display text-base tracking-wide text-white/90 transition group-hover:text-white sm:text-[1.05rem]">{surface.name}</p>
      <p className="mt-1.5 text-[13px] leading-relaxed text-white/45">{surface.summary}</p>
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
 *
 * Flagship Home (ARE-HOME-001) keeps these entry targets intact and elevates
 * MissionWorkspace as the primary *operational* workspace on the authenticated
 * page itself. Solariun remains the primary entry destination and a major
 * capability surface.
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

/** Capability groups by user intent. Only declared surfaces; no invented routes. */
const CAPABILITY_GROUPS: Array<{ heading: string; ids: SurfaceId[] }> = [
  {
    heading: "Operational",
    ids: ["engineering-lab", "weaver", "solspire"],
  },
  {
    heading: "Personal & knowledge",
    ids: ["solariun", "knowledge", "arkana"],
  },
  {
    heading: "Public field",
    ids: ["novanet", "about"],
  },
];

export function HomePage({ onNavigate }: { onNavigate: (id: SurfaceId) => void }) {
  const { isAuthenticated } = useAuth();
  const version = useHydration<VersionInfo>(endpoints.version, (p) => apiRequest<VersionInfo>(p));
  const entry = entryActions(isAuthenticated);

  return (
    <Page
      title="ARKADIA"
      subtitle="Operational console. Identity, mission control, and governed execution over one canonical spine."
    >
      {/* Identity-aware entry — contract-preserving primary / secondary actions */}
      <Panel className="home-entry mb-6 border-line/80 bg-panel/55 sm:mb-7" data-testid="home-entry-panel">
        <div className="flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between sm:gap-5">
          <div className="min-w-0 max-w-xl">
            <p className="mb-1.5 font-mono text-[10px] uppercase tracking-[0.22em] text-white/40">
              {isAuthenticated ? "Entry · signed in" : "Entry · not signed in"}
            </p>
            <p className="text-sm leading-relaxed text-white/65 sm:text-[15px]">{entry.primary.body}</p>
          </div>
          <div className="flex w-full flex-col gap-2.5 sm:w-auto sm:flex-row sm:flex-wrap">
            <button
              onClick={() => onNavigate(entry.primary.id)}
              data-testid="home-entry-primary"
              type="button"
              className="min-h-11 w-full rounded-lg border border-emerald/55 bg-emerald/12 px-5 py-2.5 font-mono text-[11px] uppercase tracking-[0.18em] text-emerald transition duration-150 hover:border-emerald/70 hover:bg-emerald/20 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-emerald/60 sm:w-auto"
            >
              {entry.primary.label}
            </button>
            <button
              onClick={() => onNavigate(entry.secondary.id)}
              data-testid="home-entry-secondary"
              type="button"
              className="min-h-11 w-full rounded-lg border border-line bg-transparent px-4 py-2.5 font-mono text-[11px] uppercase tracking-[0.16em] text-white/55 transition duration-150 hover:border-gold/35 hover:text-white/85 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-gold/50 sm:w-auto"
            >
              {entry.secondary.label}
            </button>
          </div>
        </div>
      </Panel>

      {/* Primary operational workspace — authenticated only */}
      {isAuthenticated && (
        <section
          className="home-mission mb-8 rounded-xl border border-gold/20 bg-panel/40 p-3.5 sm:mb-9 sm:p-5"
          data-testid="home-mission-control"
          aria-labelledby="mission-control-heading"
        >
          <div className="mb-4 flex flex-wrap items-end justify-between gap-3 border-b border-line/70 pb-4">
            <div className="min-w-0 max-w-2xl">
              <p id="mission-control-heading" className="font-mono text-[11px] uppercase tracking-[0.22em] text-gold">
                Mission Control
              </p>
              <p className="mt-1.5 text-sm leading-relaxed text-white/55">
                Bounded engineering work with explicit human authorization. Create a session, authorize, execute a
                read-only investigation, and review evidence. An approval is not execution; a completed run is a
                proposal awaiting review.
              </p>
            </div>
            <button
              onClick={() => onNavigate("engineering-lab")}
              data-testid="home-open-full-lab"
              type="button"
              className="min-h-10 rounded-lg border border-line/90 bg-panel/60 px-3 py-1.5 font-mono text-[10px] uppercase tracking-[0.16em] text-white/55 transition hover:border-azure/40 hover:text-white/85 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-azure/50"
            >
              Full Engineering Lab
            </button>
          </div>
          <MissionWorkspace />
        </section>
      )}

      {/* Capability navigation by intent */}
      <section className="home-capabilities mb-8 sm:mb-9" aria-labelledby="capabilities-heading">
        <div className="mb-4 flex items-baseline justify-between gap-3 sm:mb-5">
          <p id="capabilities-heading" className="font-mono text-[11px] uppercase tracking-[0.22em] text-white/40">
            Capabilities
          </p>
          <span className="hidden font-mono text-[10px] uppercase tracking-widest text-white/25 sm:inline">
            Surfaces · one spine
          </span>
        </div>
        <div className="space-y-6 sm:space-y-7">
          {CAPABILITY_GROUPS.map((group) => {
            const surfaces = group.ids
              .map((id) => SURFACES.find((s) => s.id === id))
              .filter((s): s is (typeof SURFACES)[number] => Boolean(s));
            if (surfaces.length === 0) return null;
            return (
              <div key={group.heading} className="home-capability-group">
                <p className="mb-2.5 font-mono text-[10px] uppercase tracking-[0.18em] text-white/32">{group.heading}</p>
                <div className="grid gap-2.5 sm:grid-cols-2 sm:gap-3">
                  {surfaces.map((s) => (
                    <Portal key={s.id} surface={s} onNavigate={onNavigate} />
                  ))}
                </div>
              </div>
            );
          })}
        </div>
      </section>

      {/* Honest runtime reading — never fabricated */}
      <Panel className="home-runtime border-line/70 bg-panel/45" data-testid="home-runtime-panel">
        <p className="mb-3 font-mono text-[10px] uppercase tracking-[0.2em] text-white/40">Canonical runtime</p>
        {version.state === "ready" && version.data ? (
          <Facts
            rows={[
              { label: "service", value: version.data.service },
              { label: "deployment", value: version.data.canonical_deployment },
              {
                label: "revision",
                value: <span className="font-mono text-xs">{version.data.source_revision ?? "unknown"}</span>,
              },
              { label: "source", value: version.data.revision_source },
              { label: "conflict", value: String(version.data.revision_conflict) },
            ]}
          />
        ) : (
          <ContractState state={version.state} error={version.error?.message} onRetry={version.reload} />
        )}
        <p className="mt-4 text-xs leading-relaxed text-white/35">
          {isAuthenticated
            ? "Identity verified. Mission Control is available above. Private surfaces remain behind their existing authorization boundaries."
            : "Sign in to open Mission Control, personal workspaces, and governed execution."}
        </p>
      </Panel>
    </Page>
  );
}
