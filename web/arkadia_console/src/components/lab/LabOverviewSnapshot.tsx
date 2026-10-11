/**
 * Engineering Lab — read-only substrate overview surface (Workstream 4).
 *
 * Renders `endpoints.labOverview` through the pure projection in `labOverview.ts`.
 * The handler is the Lab's snapshot of itself, so the surface's job is to report
 * what was observed, what was not, and what the substrate declares it will refuse.
 *
 * `repository.remote` is the output of `git remote get-url origin`. In any
 * environment whose remote URL carries userinfo, that value carries a credential,
 * and the handler's `security.values_redacted` flag does not cover it. The
 * projection strips userinfo before render and reports that it did; the raw value
 * is never placed in the DOM.
 *
 * Read-only by construction: GET only, one declared registry entry, and no
 * control that could act on the substrate.
 */
import { Panel, Facts, ContractState } from "../ui";
import { useHydration } from "../../lib/useHydration";
import { apiRequest } from "../../lib/apiClient";
import { endpoints } from "../../lib/endpoints";
import { buildOverviewLedger, overviewVerdict, type LabOverviewView } from "./labOverview";

export function LabOverviewSnapshot() {
  const overview = useHydration<LabOverviewView>(endpoints.labOverview, (p) =>
    apiRequest<LabOverviewView>(p),
  );

  return (
    <Panel className="mb-4">
      <p className="mb-1 font-mono text-[11px] uppercase tracking-widest text-white/40">
        Substrate snapshot
      </p>
      <p className="mb-4 text-xs text-white/40">
        Read-only. The Lab observes itself here: repository state, architecture counts, canon
        sources, patterns and its own declared governance ceiling. An observation is not an
        authorization, and a section the collector could not read is reported as unobserved rather
        than as zero.
      </p>

      {overview.state === "ready" && overview.data ? (
        <OverviewBody view={overview.data} />
      ) : (
        <ContractState state={overview.state} error={overview.error?.message} onRetry={overview.reload} />
      )}
    </Panel>
  );
}

function OverviewBody({ view }: { view: LabOverviewView }) {
  const ledger = buildOverviewLedger(view);
  const verdict = overviewVerdict(ledger);
  const g = ledger.governance;

  return (
    <div data-testid="lab-overview">
      <p
        className={`mb-3 font-mono text-[11px] uppercase tracking-widest ${
          ledger.reading_incomplete ? "text-gold" : "text-azure/80"
        }`}
        data-testid="lab-overview-verdict"
      >
        {verdict.state} · {verdict.note}
      </p>

      <Facts
        rows={[
          { label: "system", value: view.system ?? "—" },
          { label: "observed at", value: view.observed_at ?? "—" },
          { label: "branch", value: ledger.repository.branch },
          { label: "head", value: ledger.repository.head ?? "—" },
          {
            label: "working tree",
            value:
              ledger.repository.clean === null ? "unknown" : ledger.repository.clean ? "clean" : "dirty",
          },
          {
            label: "remote",
            value: ledger.repository.remote.value
              ? `${ledger.repository.remote.value}${
                  ledger.repository.remote.redacted ? "  (userinfo stripped)" : ""
                }`
              : "—",
          },
          { label: "schema", value: `${view.schema_version ?? "—"} · ${view.collector_version ?? "—"}` },
        ]}
      />

      {ledger.repository.remote.redacted && (
        <p className="mt-2 text-xs text-gold" data-testid="lab-overview-remote-redacted">
          The remote URL carried userinfo. It was stripped before render and is not shown; the
          handler's redaction flag covers security observations only, not the repository remote.
        </p>
      )}

      <section className="mt-4">
        <p className="mb-1 font-mono text-[10px] uppercase tracking-wider text-white/40">
          architecture
        </p>
        <Facts
          rows={[
            { label: "components", value: String(ledger.architecture.components ?? 0) },
            { label: "modules", value: String(ledger.architecture.modules ?? 0) },
            { label: "services", value: String(ledger.architecture.services ?? 0) },
            { label: "routes", value: String(ledger.architecture.routes ?? 0) },
            { label: "execution paths", value: String(ledger.architecture.execution_paths ?? 0) },
          ]}
        />
      </section>

      <section className="mt-4">
        <p className="mb-1 font-mono text-[10px] uppercase tracking-wider text-white/40">
          collected
        </p>
        <Facts
          rows={[
            { label: "commits analysed", value: String(ledger.trajectory.commits_analysed ?? 0) },
            { label: "major transitions", value: String(ledger.trajectory.major_transitions ?? 0) },
            { label: "canon sources", value: String(ledger.counts.canon_sources) },
            { label: "patterns", value: String(ledger.counts.patterns) },
            { label: "graph", value: `${ledger.counts.graph_entities} entities · ${ledger.counts.graph_relationships} relationships` },
            { label: "deployment files", value: String(ledger.counts.deployment_files) },
            { label: "security observations", value: `${ledger.counts.security_observations} (values redacted by the handler)` },
          ]}
        />
      </section>

      <section className="mt-4">
        <p className="mb-1 font-mono text-[10px] uppercase tracking-wider text-white/40">
          declared governance ceiling
        </p>
        {g ? (
          <>
            <Facts
              rows={[
                { label: "maximum authority", value: String(g.maximum_authority ?? "—") },
                {
                  label: "autonomous mutation",
                  value: g.autonomous_mutation === false ? "declared none" : "not declared none",
                },
                {
                  label: "production mutation",
                  value: g.production_mutation === false ? "declared none" : "not declared none",
                },
                {
                  label: "approval required",
                  value: g.approval_required === true ? "yes" : "not declared",
                },
              ]}
            />
            <p className="mt-2 text-xs text-white/45" data-testid="lab-overview-governance-note">
              These are the substrate's own declarations about what it will refuse. They are not
              permissions this surface can confer, and reading them grants nothing.
            </p>
          </>
        ) : (
          <p className="text-xs text-gold" data-testid="lab-overview-governance-absent">
            The handler reported no governance block. Absence is not a declaration of autonomy —
            treat the ceiling as unknown.
          </p>
        )}
      </section>

      {ledger.component_failures.length > 0 && (
        <section className="mt-4" data-testid="lab-overview-failures">
          <p className="mb-1 font-mono text-[10px] uppercase tracking-wider text-gold">
            components not observed
          </p>
          <ul className="flex flex-col gap-1">
            {ledger.component_failures.map((f) => (
              <li key={f.component} className="text-xs text-gold">
                <span className="font-mono">{f.component}</span> — {f.reason}
              </li>
            ))}
          </ul>
          <p className="mt-1 text-xs text-white/45">
            A failed component means that section was not read. It is not a zero.
          </p>
        </section>
      )}
    </div>
  );
}
