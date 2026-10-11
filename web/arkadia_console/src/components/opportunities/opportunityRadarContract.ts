/**
 * Project Opportunity Radar — contract model.
 *
 * Reconnaissance state for one SolSpire project, over the existing backend
 * contract `solspire/buyer_recon_router.py` (mounted at `/solspire/buyer-recon`,
 * under the `/solspire` router's `require_auth` dependency).
 *
 * Nothing here is invented: the status vocabulary is the backend's own
 * `STATUSES` tuple, the paths are the router's declared routes, and the
 * "unverified" sentinel is the backend's own default. This module holds the
 * pure logic so the surface and its tests share one source of truth.
 */

/** The backend `solspire.buyer_recon.STATUSES` vocabulary, in pipeline order. */
export const BUYER_RECON_STATUSES = [
  "UNCONTACTED",
  "CONTACTED",
  "CONVERSATION",
  "REQUIREMENT_CAPTURED",
  "PRICE_CONFIRMED",
  "BUYER_COMMITMENT",
  "SUPPLIER_CONFIRMED",
  "ECONOMICS_CLOSED",
  "READY_TO_EXECUTE",
  "EXECUTED",
  "SETTLED",
] as const;

export type BuyerReconStatus = (typeof BUYER_RECON_STATUSES)[number];

/** The backend's default for a commercial fact that has not been verified. */
export const UNVERIFIED = "UNKNOWN";

/** The backend's default evidence status for a newly captured prospect. */
export const NO_EVIDENCE = "NONE";

/**
 * Statuses whose presence means "there is a decision to make", not "this will
 * be executed". Grouping only — it grants no authority. Recovered from the
 * archived Prism `ProjectOpportunityRadar` metric of the same name.
 */
export const ACTIONABLE_STATUSES: readonly BuyerReconStatus[] = [
  "BUYER_COMMITMENT",
  "SUPPLIER_CONFIRMED",
  "ECONOMICS_CLOSED",
  "READY_TO_EXECUTE",
];

export function isKnownStatus(value: string): value is BuyerReconStatus {
  return (BUYER_RECON_STATUSES as readonly string[]).includes(value);
}

/** The next pipeline status, or `null` at the terminal status. */
export function nextStatus(status: string): BuyerReconStatus | null {
  const index = (BUYER_RECON_STATUSES as readonly string[]).indexOf(status);
  if (index < 0 || index >= BUYER_RECON_STATUSES.length - 1) return null;
  return BUYER_RECON_STATUSES[index + 1];
}

export function isTerminal(status: string): boolean {
  return nextStatus(status) === null;
}

/** A captured fact is unverified unless it carries a value the backend supplied. */
export function isUnverified(value: string | undefined | null): boolean {
  return !value || value === UNVERIFIED;
}

/** Read a fact for display, never substituting a guessed value. */
export function fact(value: string | undefined | null): string {
  return isUnverified(value) ? UNVERIFIED : (value as string);
}

// ---------------------------------------------------------------------------
// Paths — declared routes from `solspire/buyer_recon_router.py`.
// ---------------------------------------------------------------------------

const BASE = "/solspire/buyer-recon";

export function projectBoardPath(projectId: string): string {
  return `${BASE}/projects/${encodeURIComponent(projectId)}`;
}

export function projectEntriesPath(projectId: string): string {
  return `${projectBoardPath(projectId)}/entries`;
}

export function projectEntryPath(projectId: string, entryId: string): string {
  return `${projectEntriesPath(projectId)}/${encodeURIComponent(entryId)}`;
}

// ---------------------------------------------------------------------------
// Response shapes — read from the handlers, not inferred.
// ---------------------------------------------------------------------------

export interface OpportunityEntry {
  id: string;
  prospect: string;
  location: string;
  buyer_type: string;
  contact_route: string;
  commodity: string;
  estimated_demand: string;
  procurement_frequency: string;
  decision_maker: string;
  current_price: string;
  quantity: string;
  specification: string;
  delivery_point: string;
  delivery_window: string;
  payment_terms: string;
  supplier: string;
  source_price: string;
  available_quantity: string;
  logistics_quote: string;
  packaging_qc_cost: string;
  landed_cost: string;
  buyer_price: string;
  expected_gross_margin: string;
  capital_required: string;
  evidence_status: string;
  evidence: unknown[];
  why_this_prospect: string;
  status: string;
  notes: string;
}

export interface OpportunityBoard {
  id: string;
  workspace_ref: string;
  board_type: string;
  display_name: string;
  lifecycle: string;
}

export interface OpportunityAuthority {
  reconnaissance_only: boolean;
  execution_authority: string;
  budget_authority: string;
}

export interface ProjectOpportunityBoard {
  board: OpportunityBoard;
  project_id: string;
  entries: OpportunityEntry[];
  statuses: string[];
  persistence: {
    scope: string;
    subject_binding: string;
    project_binding: boolean;
    instantiated: boolean;
  };
  authority: OpportunityAuthority;
}

export interface OpportunitySummary {
  total: number;
  actionable: number;
  withEvidence: number;
  byStatus: Record<string, number>;
}

/** Counts derived from real entries only — an empty board stays visibly empty. */
export function summarize(entries: OpportunityEntry[]): OpportunitySummary {
  const byStatus: Record<string, number> = {};
  for (const status of BUYER_RECON_STATUSES) byStatus[status] = 0;
  let actionable = 0;
  let withEvidence = 0;
  for (const entry of entries) {
    byStatus[entry.status] = (byStatus[entry.status] ?? 0) + 1;
    if ((ACTIONABLE_STATUSES as readonly string[]).includes(entry.status)) actionable += 1;
    if (entry.evidence_status && entry.evidence_status !== NO_EVIDENCE) withEvidence += 1;
  }
  return { total: entries.length, actionable, withEvidence, byStatus };
}
