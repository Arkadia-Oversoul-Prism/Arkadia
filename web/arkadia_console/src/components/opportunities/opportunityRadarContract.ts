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

/**
 * Sub-resource paths derived from the *board* path.
 *
 * `ProjectOpportunityRadar` is handed a board path and never a project id, so
 * the write targets are derived from the same string it already reads. One
 * derivation chain means the POST/PATCH target cannot drift from the GET.
 */
export function entriesPathFromBoard(boardPath: string): string {
  return `${boardPath}/entries`;
}

export function entryPathFromBoard(boardPath: string, entryId: string): string {
  return `${entriesPathFromBoard(boardPath)}/${encodeURIComponent(entryId)}`;
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

// ---------------------------------------------------------------------------
// Write contract — `BuyerReconEntryInput` (POST) and `BuyerReconEntryPatch` (PATCH)
// ---------------------------------------------------------------------------

/**
 * The fields the create/edit control may transmit, each with the backend's own
 * declared default from `BuyerReconEntryInput`.
 *
 * A field is present here only if the handler declares it. Omitting an
 * unverified commercial fact is what keeps it `UNKNOWN`: the backend default is
 * applied server-side, so the client never asserts a value it does not hold.
 * Blank means "not recorded" for the descriptive fields and `UNKNOWN` for the
 * commercial ones — never `""`, which would read as a measured value of empty.
 */
export interface ProspectDraft {
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
  why_this_prospect: string;
  status: string;
  notes: string;
}

/** Descriptive (non-commercial) fields; blank is stored as blank by the handler. */
export const DESCRIPTIVE_FIELDS = [
  "location",
  "buyer_type",
  "contact_route",
  "commodity",
  "why_this_prospect",
  "notes",
] as const satisfies readonly (keyof ProspectDraft)[];

/** Commercial fields; the backend's `UNKNOWN` sentinel is their honest default. */
export const COMMERCIAL_FIELDS = [
  "estimated_demand",
  "procurement_frequency",
  "decision_maker",
  "current_price",
  "quantity",
  "specification",
  "delivery_point",
  "delivery_window",
  "payment_terms",
  "supplier",
  "source_price",
  "available_quantity",
  "logistics_quote",
  "packaging_qc_cost",
  "landed_cost",
  "buyer_price",
  "expected_gross_margin",
  "capital_required",
] as const satisfies readonly (keyof ProspectDraft)[];

export function emptyDraft(status: string = "UNCONTACTED"): ProspectDraft {
  const draft = { prospect: "", status } as ProspectDraft;
  for (const field of DESCRIPTIVE_FIELDS) draft[field] = "";
  for (const field of COMMERCIAL_FIELDS) draft[field] = UNVERIFIED;
  return draft;
}

/**
 * A field is *supplied* only when the operator typed something that is not the
 * unverified sentinel. An empty control means "not recorded" and is omitted, so
 * the backend's own default is applied rather than the client asserting a value.
 */
export function isSupplied(field: keyof ProspectDraft, value: string): boolean {
  const trimmed = value.trim();
  if (!trimmed) return false;
  if ((COMMERCIAL_FIELDS as readonly string[]).includes(field) && trimmed.toUpperCase() === UNVERIFIED) {
    return false;
  }
  return true;
}

/**
 * The POST body for `BuyerReconEntryInput`.
 *
 * `prospect` is always present because the handler requires it; every other
 * field is included only when supplied. `evidence_status` and `evidence` are
 * deliberately never sent: capture records a prospect, it does not assert that
 * evidence exists, so the backend's `NONE`/`[]` defaults stand.
 */
export function createEntryBody(draft: ProspectDraft): Record<string, unknown> {
  const body: Record<string, unknown> = { prospect: draft.prospect.trim() };
  for (const field of [...DESCRIPTIVE_FIELDS, ...COMMERCIAL_FIELDS]) {
    if (isSupplied(field, draft[field])) body[field] = draft[field].trim();
  }
  if (isKnownStatus(draft.status)) body.status = draft.status;
  return body;
}

/**
 * The PATCH body for `BuyerReconEntryPatch` (declared `extra="allow"`).
 *
 * Only supplied fields are sent, so an edit is a partial update: a field the
 * operator left untouched keeps its stored value rather than being rewritten.
 * `prospect` is included only when supplied — the backend's create-time
 * requirement is not a patch-time requirement, and sending an empty one would
 * blank a recorded prospect.
 *
 * When the recorded entry is supplied as `base`, a field equal to its stored
 * value is omitted too, so saving an unmodified form sends an empty body rather
 * than rewriting every column with the value it already had.
 */
export function editEntryBody(draft: ProspectDraft, base?: OpportunityEntry): Record<string, unknown> {
  const body: Record<string, unknown> = {};
  for (const field of [...DESCRIPTIVE_FIELDS, ...COMMERCIAL_FIELDS]) {
    if (!isSupplied(field, draft[field])) continue;
    const next = draft[field].trim();
    if (base && fact(base[field]) === next) continue;
    body[field] = next;
  }
  if (isSupplied("prospect", draft.prospect)) {
    const next = draft.prospect.trim();
    if (!base || base.prospect !== next) body.prospect = next;
  }
  if (isKnownStatus(draft.status) && (!base || base.status !== draft.status)) {
    body.status = draft.status;
  }
  return body;
}

/**
 * Client-side pre-flight for the one rule the operator can violate locally:
 * `BuyerReconManager.create_entry` raises `ValueError("prospect is required")`
 * for a blank prospect, which the router reports as `400`.
 *
 * This mirrors the server rule so the control can explain it before a round
 * trip. It is a convenience, not a boundary: the server remains the authority,
 * and a blank prospect submitted anyway is still refused there.
 */
export function prospectRequired(draft: ProspectDraft): string | null {
  return draft.prospect.trim() ? null : "A prospect is required. The backend refuses a blank one.";
}

/** True when an edit would send nothing — the PATCH would be a no-op. */
export function isNoOpEdit(draft: ProspectDraft, base?: OpportunityEntry): boolean {
  return Object.keys(editEntryBody(draft, base)).length === 0;
}

/** Seed an edit control from a recorded entry, carrying its values verbatim. */
export function draftFromEntry(entry: OpportunityEntry): ProspectDraft {
  const draft = emptyDraft(isKnownStatus(entry.status) ? entry.status : "UNCONTACTED");
  draft.prospect = entry.prospect ?? "";
  for (const field of DESCRIPTIVE_FIELDS) draft[field] = entry[field] ?? "";
  for (const field of COMMERCIAL_FIELDS) draft[field] = fact(entry[field]);
  return draft;
}

/**
 * The mutation response is `{"entry": {...}}` on both routes
 * (`create_project_buyer_recon_entry`, `update_project_buyer_recon_entry`).
 * The client must read the created/updated entry from that key: a body without
 * it is an unrecognised shape, not a successful empty write.
 */
export function parseEntryResponse(payload: unknown): OpportunityEntry | null {
  if (typeof payload !== "object" || payload === null) return null;
  const entry = (payload as { entry?: unknown }).entry;
  if (typeof entry !== "object" || entry === null) return null;
  const candidate = entry as Record<string, unknown>;
  if (typeof candidate.id !== "string" || typeof candidate.prospect !== "string") return null;
  return candidate as unknown as OpportunityEntry;
}

/** Replace one entry in a board list by id, keeping the server's ordering rule. */
export function upsertEntry(entries: OpportunityEntry[], entry: OpportunityEntry): OpportunityEntry[] {
  const index = entries.findIndex((item) => item.id === entry.id);
  if (index < 0) return [entry, ...entries];
  return entries.map((item) => (item.id === entry.id ? entry : item));
}
