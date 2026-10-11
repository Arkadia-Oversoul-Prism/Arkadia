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

export function HomePage({ onNavigate }: { onNavigate: (id: SurfaceId) => void }) {
  const { isAuthenticated } = useAuth();
  const version = useHydration<VersionInfo>(endpoints.version, (p) => apiRequest<VersionInfo>(p));

  return (
    <Page
      title="ARKADIA"
      subtitle="One coherent application over the canonical backend. Identity, workspace, and governed execution share a single spine."
    >
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
