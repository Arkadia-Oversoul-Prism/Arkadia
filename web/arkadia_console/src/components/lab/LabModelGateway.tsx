/**
 * Engineering Lab — model gateway read surface (Workstream 4, feature-local).
 *
 * Renders `endpoints.labGateway` through the pure projection in `labGateway.ts`.
 * The gateway reports the deployment's *effective* provider configuration, and
 * its contract is that selection never fabricates availability. This surface
 * therefore leads with the blocked/available reading and never presents an
 * unconfigured provider as usable, a LOCAL class as free, or an AVAILABLE
 * provider as an authorization.
 *
 * Read-only by construction: GET only, no request of its own beyond the declared
 * registry entry, and no control that could run or select a model.
 */
import { Panel, Facts, ContractState } from "../ui";
import { useHydration } from "../../lib/useHydration";
import { apiRequest } from "../../lib/apiClient";
import { endpoints } from "../../lib/endpoints";
import { buildGatewayLedger, gatewayVerdict, type GatewayProvider, type GatewayView } from "./labGateway";

const GROUP_LABEL: Record<string, string> = {
  local_providers: "local",
  remote_providers: "remote",
  agent_providers: "agent runtime",
};

function ProviderRow({ entry }: { entry: GatewayProvider }) {
  const usable = entry.status === "AVAILABLE";
  const dispatchable = entry.dispatchable === true;
  return (
    <li
      className="rounded border border-line bg-ink/40 p-3"
      data-testid={`lab-gateway-provider-${entry.provider}`}
    >
      <p className="mb-2 font-mono text-xs text-white/80">
        <span className={usable ? "text-azure/80" : "text-white/45"}>{entry.provider}</span> ·{" "}
        {entry.status ?? "unknown"} · {entry.config_class ?? "unknown class"}
      </p>
      <Facts
        rows={[
          { label: "model", value: entry.model ?? "—" },
          { label: "configured", value: entry.configured ? "yes" : "no" },
          // Reachability and dispatchability are separate facts: a provider can be
          // AVAILABLE with no adapter bound, and a dispatch would then fail.
          { label: "dispatchable", value: dispatchable ? "yes" : "no" },
          { label: "detail", value: entry.detail || "—" },
        ]}
      />
    </li>
  );
}

export function LabModelGateway() {
  const gateway = useHydration<GatewayView>(endpoints.labGateway, (p) => apiRequest<GatewayView>(p));

  return (
    <Panel className="mb-4">
      <p className="mb-1 font-mono text-[11px] uppercase tracking-widest text-white/40">
        Model gateway
      </p>
      <p className="mb-4 text-xs text-white/40">
        Read-only. The gateway reports effective configuration. Availability is not an
        authorization, a configured key is not a reachable provider, a local class is not free, and
        an agent runtime is described without being probed.
      </p>

      {gateway.state === "ready" && gateway.data ? (
        <GatewayBody view={gateway.data} />
      ) : (
        <ContractState state={gateway.state} error={gateway.error?.message} onRetry={gateway.reload} />
      )}
    </Panel>
  );
}

function GatewayBody({ view }: { view: GatewayView }) {
  const ledger = buildGatewayLedger(view);
  const verdict = gatewayVerdict(ledger);

  return (
    <div data-testid="lab-gateway">
      <p
        className={`mb-3 font-mono text-[11px] uppercase tracking-widest ${
          ledger.dispatchable_provider_present ? "text-azure/80" : "text-gold"
        }`}
        data-testid="lab-gateway-verdict"
      >
        {verdict.state} · {verdict.note}
      </p>

      <Facts
        rows={[
          { label: "catalog", value: String(ledger.counts.catalog) },
          { label: "configured", value: String(ledger.counts.configured) },
          { label: "available", value: String(ledger.counts.available) },
          { label: "dispatchable", value: String(ledger.counts.dispatchable) },
          {
            label: "by class",
            value: `local ${ledger.counts.local} · remote ${ledger.counts.remote} · agent ${ledger.counts.agent_runtime}`,
          },
        ]}
      />

      {ledger.groups.map((group) => (
        <section key={group.group} className="mt-3">
          <p className="mb-1 font-mono text-[10px] uppercase tracking-wider text-white/40">
            {GROUP_LABEL[group.group]} providers ({group.declared.length})
          </p>
          {group.declared.length === 0 ? (
            <p className="text-xs text-white/45" data-testid={`lab-gateway-${group.group}-empty`}>
              The gateway declares no {GROUP_LABEL[group.group]} provider.
            </p>
          ) : (
            <ul className="flex flex-col gap-2">
              {group.entries.map((entry) => (
                <ProviderRow key={entry.provider} entry={entry} />
              ))}
            </ul>
          )}
          {group.missing_from_catalog.length > 0 && (
            <p className="mt-1 text-xs text-gold" data-testid={`lab-gateway-${group.group}-missing`}>
              declared but not described by the catalog: {group.missing_from_catalog.join(" · ")}
            </p>
          )}
          {group.group_class_mismatch.length > 0 && (
            <p className="mt-1 text-xs text-gold" data-testid={`lab-gateway-${group.group}-mismatch`}>
              declared here but classified elsewhere:{" "}
              {group.group_class_mismatch.map((e) => `${e.provider} (${e.config_class})`).join(" · ")}
            </p>
          )}
        </section>
      ))}

      {ledger.ungrouped_providers.length > 0 && (
        <p className="mt-3 text-xs text-gold" data-testid="lab-gateway-ungrouped">
          described but in no declared group:{" "}
          {ledger.ungrouped_providers.map((e) => e.provider).join(" · ")}
        </p>
      )}

      {ledger.duplicate_providers.length > 0 && (
        <p className="mt-2 text-xs text-gold" data-testid="lab-gateway-duplicates">
          described more than once: {ledger.duplicate_providers.join(" · ")}
        </p>
      )}

      {ledger.unknown_config_class.length > 0 && (
        <p className="mt-2 text-xs text-gold" data-testid="lab-gateway-unknown-class">
          unknown config class: {ledger.unknown_config_class.map((e) => e.provider).join(" · ")}
        </p>
      )}

      {ledger.configured_but_not_available.length > 0 && (
        <p className="mt-2 text-xs text-gold" data-testid="lab-gateway-configured-not-available">
          configured but not confirmed reachable:{" "}
          {ledger.configured_but_not_available.map((e) => e.provider).join(" · ")}
        </p>
      )}

      {ledger.available_but_not_dispatchable.length > 0 && (
        <p className="mt-2 text-xs text-gold" data-testid="lab-gateway-available-not-dispatchable">
          reachable but not dispatchable — no adapter is bound, so a run could not call one:{" "}
          {ledger.available_but_not_dispatchable.map((e) => e.provider).join(" · ")}
        </p>
      )}

      {ledger.agent_runtime_reported_available.length > 0 && (
        <p className="mt-2 text-xs text-gold" data-testid="lab-gateway-agent-available">
          agent runtime reported available (never probed by the gateway):{" "}
          {ledger.agent_runtime_reported_available.map((e) => e.provider).join(" · ")}
        </p>
      )}

      <p className="mt-3 text-xs text-white/40" data-testid="lab-gateway-cost">
        {ledger.cost_asserted
          ? "A cost note asserts a cost. Read it per provider."
          : "Cost is asserted nowhere. A local class is not thereby free."}
      </p>
    </div>
  );
}
