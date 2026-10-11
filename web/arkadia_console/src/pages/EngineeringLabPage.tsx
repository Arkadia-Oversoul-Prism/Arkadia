import { Page, Panel, Facts, ContractState, NotYetWired } from "../components/ui";
import { useHydration } from "../lib/useHydration";
import { apiRequest } from "../lib/apiClient";
import { endpoints } from "../lib/endpoints";
import type { NAtlasCatalog } from "../lib/types";

export function EngineeringLabPage() {
  const overview = useHydration<Record<string, unknown>>(endpoints.labEngineeringOverview, (p) =>
    apiRequest<Record<string, unknown>>(p),
  );
  const catalog = useHydration<NAtlasCatalog>(endpoints.labNAtlasCatalog, (p) => apiRequest<NAtlasCatalog>(p));

  return (
    <Page
      title="Engineering Lab"
      subtitle="Technical operations: task state, provider status, execution history, and evidence. Reads are owner-scoped."
    >
      <Panel className="mb-4">
        <p className="mb-3 font-mono text-[11px] uppercase tracking-widest text-white/40">Lab overview</p>
        {overview.state === "ready" && overview.data ? (
          <Facts
            rows={Object.entries(overview.data)
              .slice(0, 12)
              .map(([k, v]) => ({ label: k, value: typeof v === "object" ? JSON.stringify(v) : String(v) }))}
          />
        ) : (
          <ContractState state={overview.state} error={overview.error?.message} onRetry={overview.reload} />
        )}
      </Panel>

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

      <div className="grid gap-4 md:grid-cols-2">
        <NotYetWired contract="/api/lab/engineering/sessions" note="Session list, authorize, execute, and transition controls." />
        <NotYetWired contract="/api/lab/engineering/artifacts" note="Artifact canvas and evidence records." />
      </div>
    </Page>
  );
}
