/**
 * The two-axis primitive: FLOW × POSTURE.
 *
 * A boundary is never rendered as a bare "✓". It carries two independent
 * properties:
 *
 *   Axis A — FLOW     : where in the causal spine this sits (see grammar.ts)
 *   Axis B — POSTURE  : what is actually true about it, on two ladders
 *
 * The posture ladders are deliberately separate. A mechanism can be ENFORCED
 * in code while the deployment has never been probed (Render UNVERIFIED), and
 * the console must never let those collapse into a single green state.
 *
 * Source of truth for these values: RECONCILED-BOUNDARY-MAP-01.md §0 and §4.
 */

/** How a boundary is held — machine-checked, or merely asserted. */
export type MechanismStatus =
  | "ENFORCED"          // machine-checked at the boundary, with a dedicated test
  | "ENFORCED_UNTESTED" // machine-checked, but no dedicated test yet
  | "DECLARED";         // asserted in governance/contracts, not machine-checked

/** How far the boundary has actually travelled toward production. */
export interface DeploymentPosture {
  implemented: boolean;
  tested: boolean;
  deployed: boolean;
  productionVerified: boolean;
}

export interface Posture {
  mechanism: MechanismStatus;
  deployment: DeploymentPosture;
  /** Short, truthful caveat rendered verbatim (never softened). */
  note?: string;
}

export const UNPROVEN: DeploymentPosture = {
  implemented: false,
  tested: false,
  deployed: false,
  productionVerified: false,
};

/**
 * The deployment ladder, ordered. Each rung is independent on purpose: a
 * boundary may be implemented and tested while remaining undeployed, and a
 * deployed host may still be production-unverified (pre-hardening code).
 */
const LADDER: { key: keyof DeploymentPosture; label: string }[] = [
  { key: "implemented", label: "IMPLEMENTED" },
  { key: "tested", label: "TESTED" },
  { key: "deployed", label: "DEPLOYED" },
  { key: "productionVerified", label: "PRODUCTION VERIFIED" },
];

export interface LadderRung {
  key: keyof DeploymentPosture;
  label: string;
  reached: boolean;
}

export function deploymentLadder(p: DeploymentPosture): LadderRung[] {
  return LADDER.map((r) => ({ ...r, reached: p[r.key] }));
}

/** The highest rung actually reached, as a single token. */
export function deploymentHeadline(p: DeploymentPosture): string {
  for (let i = LADDER.length - 1; i >= 0; i--) {
    if (p[LADDER[i].key]) return LADDER[i].label;
  }
  return "NOT IMPLEMENTED";
}

export type PostureTone = "enforced" | "declared" | "unprovisioned" | "unverified" | "muted";

/**
 * Tone is derived from mechanism first, then from how far the deployment has
 * travelled. Crucially: an ENFORCED mechanism that is not production-verified
 * is NOT green — it is "unverified". Green is reserved for the top rung.
 */
export function postureTone(p: Posture): PostureTone {
  if (p.mechanism === "DECLARED") return "declared";
  if (p.deployment.productionVerified) return "enforced";
  return "unverified";
}

/** A compact, non-collapsible label, e.g. "ENFORCED · IMPLEMENTED / TESTED · NOT DEPLOYED". */
export function postureLabel(p: Posture): string {
  const mech =
    p.mechanism === "ENFORCED"
      ? "ENFORCED"
      : p.mechanism === "ENFORCED_UNTESTED"
        ? "ENFORCED (untested)"
        : "DECLARED";
  const d = p.deployment;
  const reached = [
    d.implemented && "IMPLEMENTED",
    d.tested && "TESTED",
    d.deployed && "DEPLOYED",
    d.productionVerified && "PRODUCTION VERIFIED",
  ].filter(Boolean) as string[];
  return `${mech} · ${reached.length ? reached.join(" / ") : "NOT IMPLEMENTED"}`;
}

/** True when every rung is reached — the only state that may render as settled. */
export function isFullyProven(p: Posture): boolean {
  const d = p.deployment;
  return d.implemented && d.tested && d.deployed && d.productionVerified;
}

/**
 * The witnessed status of a specific TRANSITION (an edge), distinct from the
 * posture of the stages it joins. A stage can be PRODUCTION-VERIFIED while the
 * edge leaving it is CONTRADICTED — the console must never infer an edge from
 * the health of its endpoints.
 *
 * Source: console-runtime-reconciliation-01.md (F.1–F.4 + PR #180).
 */
export type EdgeStatus = "DEMONSTRATED" | "CONTRADICTED" | "UNRESOLVED";

export type EdgeStatusTone = "demonstrated" | "contradicted" | "unresolved";

export function edgeStatusTone(s: EdgeStatus): EdgeStatusTone {
  if (s === "DEMONSTRATED") return "demonstrated";
  if (s === "CONTRADICTED") return "contradicted";
  return "unresolved";
}
