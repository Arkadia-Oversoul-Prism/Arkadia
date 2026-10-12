/**
 * Engineering Lab — model gateway read projection (Workstream 4).
 *
 * A pure projection of `GET /api/lab/engineering/gateway`
 * (`lab.engineering_lab.gateway.describe_gateway` → `ModelGateway.to_dict()`),
 * which returns `{local_providers, remote_providers, agent_providers, catalog}`.
 * Each catalog entry is a `ModelDescriptor.to_dict()`:
 * `{provider, model, config_class, configured, status, detail, cost_note}`.
 *
 * The gateway's own contract is that selection "never fabricates availability":
 * a provider that is not configured reports `UNAVAILABLE`/`UNCONFIGURED` and the
 * caller must treat model work as **blocked** rather than substitute a stub.
 * This projection preserves that, and the further non-collapses the handler
 * implies:
 *
 *   configured        != status AVAILABLE   (a key/env fact vs a probe result)
 *   status AVAILABLE  != authorized to run  (the gateway holds no authority)
 *   config_class LOCAL != free              (cost is explicitly not asserted)
 *   AGENT_RUNTIME     != probed             (agent runtimes are never probed)
 *
 * Missing and partial data are reported, never smoothed: a catalog provider that
 * belongs to none of the three declared groups would be dropped by a naive
 * group-by, and a provider listed twice would be counted twice. Both are
 * surfaced.
 *
 * No network, no React, no store access: this file is importable and executable
 * on its own so its behaviour can be measured directly (see
 * `tests/test_prism_w4_model_gateway.py`).
 */

export interface GatewayProvider {
  provider: string;
  model?: string;
  config_class?: string;
  configured?: boolean;
  status?: string;
  detail?: string;
  cost_note?: string;
}

export interface GatewayView {
  local_providers?: string[];
  remote_providers?: string[];
  agent_providers?: string[];
  catalog?: GatewayProvider[];
}

/** Provider groups the handler declares, in the order it declares them. */
export const PROVIDER_GROUPS = ["local_providers", "remote_providers", "agent_providers"] as const;
export type ProviderGroup = (typeof PROVIDER_GROUPS)[number];

/** Config classes the gateway declares, read from `CONFIG_CLASSES`. */
export const CONFIG_CLASSES: readonly string[] = ["LOCAL", "REMOTE", "AGENT_RUNTIME"];

/** The one status that means the gateway itself reports a usable provider. */
export const AVAILABLE_STATUS = "AVAILABLE";

export interface GroupReading {
  group: ProviderGroup;
  /** The names the handler listed under this group. */
  declared: string[];
  /** The catalog entries whose `config_class` maps to this group. */
  entries: GatewayProvider[];
  /** Declared names that the catalog does not describe. */
  missing_from_catalog: string[];
  /** Entries whose `config_class` maps to a *different* group than declared. */
  group_class_mismatch: GatewayProvider[];
}

export interface GatewayLedger {
  groups: GroupReading[];
  catalog: GatewayProvider[];
  /** Catalog providers belonging to no declared group — a naive group-by drops these. */
  ungrouped_providers: GatewayProvider[];
  /** Provider names the catalog describes more than once. */
  duplicate_providers: string[];
  /** Entries whose `config_class` is not a declared class. */
  unknown_config_class: GatewayProvider[];
  counts: {
    catalog: number;
    configured: number;
    available: number;
    local: number;
    remote: number;
    agent_runtime: number;
  };
  /**
   * `true` only when the gateway reports at least one provider it can actually
   * use. When false, model work is BLOCKED — the surface must not present an
   * unconfigured provider as usable.
   */
  usable_provider_present: boolean;
  /** Agent runtimes the gateway reported as AVAILABLE — it never probes them. */
  agent_runtime_reported_available: GatewayProvider[];
  /** A configured provider whose probe did not confirm reachability. */
  configured_but_not_available: GatewayProvider[];
  /** Cost is asserted nowhere by the gateway; surfaced so no class reads as free. */
  cost_asserted: boolean;
  /** Always true: the gateway is a description, not an authority. */
  authority_granted: false;
}

function groupFor(configClass: string | undefined): ProviderGroup | null {
  if (configClass === "LOCAL") return "local_providers";
  if (configClass === "REMOTE") return "remote_providers";
  if (configClass === "AGENT_RUNTIME") return "agent_providers";
  return null;
}

export function buildGatewayLedger(view: GatewayView): GatewayLedger {
  const catalog = view.catalog ?? [];
  const byProvider = new Map<string, GatewayProvider[]>();
  for (const entry of catalog) {
    const list = byProvider.get(entry.provider);
    if (list) list.push(entry);
    else byProvider.set(entry.provider, [entry]);
  }

  const groups: GroupReading[] = PROVIDER_GROUPS.map((group) => {
    const declared = view[group] ?? [];
    const entries = declared
      .map((name) => byProvider.get(name))
      .filter((list): list is GatewayProvider[] => Boolean(list))
      .map((list) => list[0]);
    return {
      group,
      declared,
      entries,
      missing_from_catalog: declared.filter((name) => !byProvider.has(name)),
      group_class_mismatch: entries.filter((entry) => groupFor(entry.config_class) !== group),
    };
  });

  const known = new Set(groups.flatMap((g) => g.declared));
  const ungrouped = catalog.filter((entry) => !known.has(entry.provider));
  const duplicates = [...byProvider.entries()].filter(([, list]) => list.length > 1).map(([name]) => name);

  const configured = catalog.filter((entry) => entry.configured === true);
  const available = catalog.filter((entry) => entry.status === AVAILABLE_STATUS);

  return {
    groups,
    catalog,
    ungrouped_providers: ungrouped,
    duplicate_providers: duplicates,
    unknown_config_class: catalog.filter((entry) => !CONFIG_CLASSES.includes(entry.config_class ?? "")),
    counts: {
      catalog: catalog.length,
      configured: configured.length,
      available: available.length,
      local: catalog.filter((e) => e.config_class === "LOCAL").length,
      remote: catalog.filter((e) => e.config_class === "REMOTE").length,
      agent_runtime: catalog.filter((e) => e.config_class === "AGENT_RUNTIME").length,
    },
    usable_provider_present: available.length > 0,
    agent_runtime_reported_available: available.filter((e) => e.config_class === "AGENT_RUNTIME"),
    configured_but_not_available: configured.filter((e) => e.status !== AVAILABLE_STATUS),
    // A cost note that asserts nothing means no class may be presented as free.
    cost_asserted: catalog.some((entry) => typeof entry.cost_note === "string" && entry.cost_note.length > 0 && !/not asserted/i.test(entry.cost_note)),
    authority_granted: false,
  };
}

/**
 * The sentence the surface shows for the gateway's overall reading. Derived only
 * from the ledger, so an unconfigured gateway can never read as ready.
 */
export function gatewayVerdict(ledger: GatewayLedger): { state: string; note: string } {
  if (ledger.counts.catalog === 0) {
    return {
      state: "NO_CATALOG",
      note: "The gateway reported no providers. That is an empty catalog, not an available model.",
    };
  }
  if (!ledger.usable_provider_present) {
    return {
      state: "MODEL_WORK_BLOCKED",
      note:
        "No provider reports AVAILABLE. Model work is blocked — the gateway refuses to substitute a stub for an unconfigured provider.",
    };
  }
  return {
    state: "PROVIDER_AVAILABLE",
    note:
      "At least one provider reports AVAILABLE. Availability is a configuration fact: it is not an authorization, and it is not a run.",
  };
}
