/**
 * Engineering Lab — read-only overview projection (Workstream 4).
 *
 * A pure projection of `GET /api/lab/overview` (`lab.service.build_overview`).
 * The handler is the Lab's own snapshot of itself: repository state, architecture
 * counts, commit trajectory, canon sources, detected patterns, graph size,
 * deployment files, security observations and — most importantly — its
 * `governance` declaration.
 *
 * Two properties this projection must hold:
 *
 * 1. **`observed` != `authorized`.** `governance` states the Lab's own ceiling
 *    (`maximum_authority`, `autonomous_mutation: false`, `production_mutation:
 *    false`, `approval_required: true`). Those are declarations about what the
 *    substrate will refuse, not permissions this surface may confer. A reading of
 *    this snapshot is never an authorization to act.
 *
 * 2. **A credential must not reach the screen.** `repository.remote` is the
 *    output of `git remote get-url origin`, so it carries whatever userinfo the
 *    environment's remote URL holds — including a token, in any environment where
 *    the remote was configured with one. The handler's `security.values_redacted`
 *    flag is scoped to `security.observations` only; it does not cover
 *    `repository.remote`. `redactRemote()` therefore strips userinfo here, at the
 *    UI boundary, and reports that it did.
 *
 * `partial` is a real state: the handler records per-component failures in
 * `errors` and downgrades `status` from `observed` to `partial`. A failed
 * component means that section was NOT observed, so the projection surfaces each
 * failure rather than rendering an empty section as a zero.
 *
 * No network, no React, no store access: importable and executable on its own
 * (see `tests/test_prism_w4_lab_overview.py`).
 */

export interface LabRepository {
  branch?: string;
  head?: string;
  clean?: boolean;
  remote?: string | null;
  status?: string;
  reason?: string | null;
}

export interface LabArchitecture {
  components?: number;
  modules?: number;
  services?: number;
  routes?: number;
  execution_paths?: number;
  status?: string;
}

export interface LabTrajectory {
  commits_analysed?: number;
  major_transitions?: number;
  high_churn_components?: number;
  classifications?: Record<string, number>;
}

export interface LabGovernance {
  maximum_authority?: number;
  autonomous_mutation?: boolean;
  production_mutation?: boolean;
  approval_required?: boolean;
}

export interface LabOverviewView {
  schema_version?: string;
  collector_version?: string;
  analysis_version?: string;
  observed_at?: string;
  system?: string;
  status?: string;
  repository?: LabRepository;
  architecture?: LabArchitecture;
  trajectory?: LabTrajectory;
  canon?: { loaded?: boolean; sources?: Array<{ path?: string; classification?: string }>; version?: string | null };
  patterns?: unknown[];
  graph?: { entities?: number; relationships?: number; status?: string };
  deployments?: { files?: string[] };
  security?: { observations?: Array<{ path?: string; signals?: string[] }>; values_redacted?: boolean };
  governance?: LabGovernance;
  errors?: Array<{ component?: string; status?: string; reason?: string }>;
}

export interface RedactedRemote {
  /** The remote URL with any userinfo removed, or null when none was reported. */
  value: string | null;
  /** True when the handler's value carried userinfo that was stripped here. */
  redacted: boolean;
  /** The scheme, which is safe to show and useful for a lineage reading. */
  scheme: string | null;
}

/**
 * Strip `user:password@` (or a bare `token@`) from a URL, keeping the scheme and
 * host. Never returns the userinfo, and reports whether it removed any.
 */
export function redactRemote(remote: string | null | undefined): RedactedRemote {
  if (typeof remote !== "string" || remote.length === 0) {
    return { value: null, redacted: false, scheme: null };
  }
  const schemeMatch = /^([a-z][a-z0-9+.-]*):\/\//i.exec(remote);
  const scheme = schemeMatch ? schemeMatch[1].toLowerCase() : null;
  const afterScheme = schemeMatch ? remote.slice(schemeMatch[0].length) : remote;
  // userinfo is everything before the first "@" in the authority component.
  const authorityEnd = afterScheme.search(/[/?#]/);
  const authority = authorityEnd === -1 ? afterScheme : afterScheme.slice(0, authorityEnd);
  const rest = authorityEnd === -1 ? "" : afterScheme.slice(authorityEnd);
  const at = authority.lastIndexOf("@");
  if (at === -1) {
    return { value: remote, redacted: false, scheme };
  }
  const host = authority.slice(at + 1);
  const prefix = schemeMatch ? schemeMatch[0] : "";
  return { value: `${prefix}${host}${rest}`, redacted: true, scheme };
}

export interface OverviewLedger {
  /** Repository reading, with `remote` already stripped of userinfo. */
  repository: {
    branch: string;
    head: string | null;
    clean: boolean | null;
    remote: RedactedRemote;
    status: string;
  };
  architecture: LabArchitecture;
  trajectory: LabTrajectory;
  counts: {
    canon_sources: number;
    patterns: number;
    deployment_files: number;
    graph_entities: number;
    graph_relationships: number;
    security_observations: number;
  };
  /**
   * The Lab's own declared ceiling. Read, never asserted as a permission.
   * `null` when the handler omitted the block.
   */
  governance: LabGovernance | null;
  /** True when `governance` says the substrate mutates nothing on its own. */
  autonomous_mutation_declared: boolean;
  /** True when `governance` says production mutation requires a human. */
  human_approval_required: boolean;
  /** Always true: reading this snapshot is not an authorization. */
  authority_granted: false;
  /** Per-component failures the handler recorded; each means a section was not observed. */
  component_failures: Array<{ component: string; reason: string }>;
  /** The handler's own status string (`observed` / `partial` / anything else). */
  reported_status: string;
  /** True when `reported_status` is not `observed` — the reading is incomplete. */
  reading_incomplete: boolean;
  /** The set of components the handler could not observe. */
  unobserved_components: string[];
  /** `security.observations` is redacted by the handler; `repository.remote` is not. */
  handler_redaction_scope: "security.observations only";
}

export function buildOverviewLedger(view: LabOverviewView): OverviewLedger {
  const errors = view.errors ?? [];
  const componentFailures = errors.map((e) => ({
    component: e.component ?? "unknown",
    reason: e.reason ?? "no reason given",
  }));
  const reportedStatus = view.status ?? "unknown";
  const governance = view.governance ?? null;

  return {
    repository: {
      branch: view.repository?.branch ?? "unknown",
      head: view.repository?.head ?? null,
      clean: view.repository?.clean ?? null,
      remote: redactRemote(view.repository?.remote),
      status: view.repository?.status ?? "unknown",
    },
    architecture: view.architecture ?? {},
    trajectory: view.trajectory ?? {},
    counts: {
      canon_sources: view.canon?.sources?.length ?? 0,
      patterns: view.patterns?.length ?? 0,
      deployment_files: view.deployments?.files?.length ?? 0,
      graph_entities: view.graph?.entities ?? 0,
      graph_relationships: view.graph?.relationships ?? 0,
      security_observations: view.security?.observations?.length ?? 0,
    },
    governance,
    autonomous_mutation_declared: governance?.autonomous_mutation === false,
    human_approval_required: governance?.approval_required === true,
    authority_granted: false,
    component_failures: componentFailures,
    reported_status: reportedStatus,
    reading_incomplete: reportedStatus !== "observed",
    unobserved_components: componentFailures.map((f) => f.component),
    handler_redaction_scope: "security.observations only",
  };
}

/**
 * The surface's headline reading. Derived only from the ledger, so an incomplete
 * snapshot can never read as a complete observation.
 */
export function overviewVerdict(ledger: OverviewLedger): { state: string; note: string } {
  if (ledger.reading_incomplete) {
    return {
      state: "READING_INCOMPLETE",
      note: `The handler reported status "${ledger.reported_status}". Components not observed: ${
        ledger.unobserved_components.join(", ") || "none named"
      }. An unobserved section is not a zero.`,
    };
  }
  return {
    state: "OBSERVED",
    note:
      "The snapshot is complete. It is an observation of the substrate, not an authorization to act in it.",
  };
}
