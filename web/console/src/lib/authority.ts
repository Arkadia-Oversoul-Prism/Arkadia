/**
 * Authority — the sovereign-control model, and its current posture.
 *
 * Principle (architecture §9 Q2): **unavailable authority is visible, but never
 * simulated.** An unavailable authorization capability is never drawn as a
 * button waiting to be clicked.
 *
 * Source: governance/roles.json; BC-2 enforcement; RECONCILED-BOUNDARY-MAP-01 §0.
 */

export type AuthorityProvision = "PROVISIONED" | "UNPROVISIONED";

export interface RoleSpec {
  name: string;
  description: string;
  permissions: string[];
  /** Grants the Govern permission (may decide approvals). */
  governs: boolean;
}

/** Mirrored from governance/roles.json. */
export const ROLES: RoleSpec[] = [
  {
    name: "Flamekeeper",
    description: "Sovereign overseer; grants high-level governance and approvals.",
    permissions: ["Govern", "Propose"],
    governs: true,
  },
  {
    name: "Weaver",
    description: "Primary agent for code formation; explicitly non-authoritative for governance.",
    permissions: ["Read", "Propose"],
    governs: false,
  },
  {
    name: "Witness",
    description: "Observer role providing attestations and audit perspectives.",
    permissions: ["Read"],
    governs: false,
  },
  {
    name: "Guest",
    description: "External or unauthenticated users with strictly read access to public Gate resources.",
    permissions: ["Read"],
    governs: false,
  },
];

/**
 * Current state of governing authority. The *declared* Govern role is unseated,
 * but the enforcement layer also admits the sovereign tier — see
 * authorityState().statement. This is why the console does not claim approvals
 * can never be decided.
 */
export const GOVERNING_AUTHORITY: AuthorityProvision = "UNPROVISIONED";

/** The operations that require a Govern principal. */
export const AUTHORITY_GATED_OPERATIONS = [
  "POST /api/approvals/{id}/approve",
  "POST /api/approvals/{id}/reject",
];

/** The two encodings of governing authority the enforcement layer accepts. */
export const AUTHORITY_ENCODINGS = [
  "role == Flamekeeper (declared in governance/roles.json — unseated)",
  "access_level >= 3 (sovereign tier — occupied by existing node principals)",
];

/** What remains available while governing authority is unprovisioned. */
export const AUTHORITY_INDEPENDENT_OPERATIONS = [
  "inspection",
  "evidence review",
  "boundary inspection",
  "provenance traversal",
  "proposals (subject-attributed)",
  "non-authoritative observation",
];

export interface AuthorityState {
  provision: AuthorityProvision;
  gatedOperations: string[];
  independentOperations: string[];
  /** The encodings of authority the enforcement layer accepts. */
  encodings: string[];
  /** A one-line truthful statement of the posture. */
  statement: string;
  /** Why nothing may be auto-provisioned. */
  constraint: string;
}

export function authorityState(): AuthorityState {
  return {
    provision: GOVERNING_AUTHORITY,
    gatedOperations: AUTHORITY_GATED_OPERATIONS,
    independentOperations: AUTHORITY_INDEPENDENT_OPERATIONS,
    encodings: AUTHORITY_ENCODINGS,
    statement:
      "GOVERNING AUTHORITY: the declared Flamekeeper role is UNPROVISIONED, but the " +
      "enforcement layer also accepts the sovereign tier (access_level >= 3), which " +
      "existing node principals occupy. Approvals are therefore decidable by a sovereign " +
      "principal — the declared/enforced gap is an unresolved boundary.",
    constraint: "No automatic provisioning permitted.",
  };
}
