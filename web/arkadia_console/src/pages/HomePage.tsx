import { Page, Panel, Facts, ContractState } from "../components/ui";
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

export function HomePage({ onNavigate }: { onNavigate: (id: SurfaceId) => void }) {
  const { isAuthenticated } = useAuth();
  const version = useHydration<VersionInfo>(endpoints.version, (p) => apiRequest<VersionInfo>(p));
  const entry = entryActions(isAuthenticated);

  return (
    <Page
      title="ARKADIA"
      subtitle="One coherent application over the canonical backend. Identity, workspace, and governed execution share a single spine."
    >
      <Panel className="mb-6 border-emerald/25">
        <p className="mb-1 font-mono text-[11px] uppercase tracking-widest text-white/40">
          {isAuthenticated ? "Entry · signed in" : "Entry · not signed in"}
        </p>
        <p className="text-sm text-white/60">{entry.primary.body}</p>
        <div className="mt-4 flex flex-wrap gap-3">
          <button
            onClick={() => onNavigate(entry.primary.id)}
            data-testid="home-entry-primary"
            className="rounded-lg border border-emerald/50 bg-emerald/10 px-4 py-2 font-mono text-[11px] uppercase tracking-widest text-emerald transition hover:bg-emerald/20"
          >
            {entry.primary.label}
          </button>
          <button
            onClick={() => onNavigate(entry.secondary.id)}
            data-testid="home-entry-secondary"
            className="rounded-lg border border-line bg-panel/60 px-4 py-2 font-mono text-[11px] uppercase tracking-widest text-white/70 transition hover:border-gold/40 hover:text-white"
          >
            {entry.secondary.label}
          </button>
        </div>
      </Panel>

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
