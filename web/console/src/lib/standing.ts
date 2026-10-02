/**
 * Standing states — the map's explicit non-claims, promoted to first-class,
 * non-dismissible surfaces (architecture §7).
 *
 * The console must not let a human infer a state the Verified Boundary Map
 * does not support. These render persistently, never as transient warnings.
 *
 * Source: RECONCILED-BOUNDARY-MAP-01.md §0.
 */

export type StandingTone = "unverified" | "unprovisioned" | "preproduction" | "undeployed";

export interface StandingState {
  id: string;
  tone: StandingTone;
  headline: string;
  detail: string;
}

export const STANDING_STATES: StandingState[] = [
  {
    id: "render",
    tone: "unverified",
    headline: "Render — UNVERIFIED",
    detail:
      "The live host (arkadia-kw64.onrender.com) runs pre-hardening code. Deployed " +
      "posture is UNVERIFIED, never green.",
  },
  {
    id: "flamekeeper",
    tone: "unprovisioned",
    headline: "Flamekeeper — UNPROVISIONED",
    detail:
      "The declared Govern role is enforced, but no principal is seated in it. It is not " +
      "true that approvals can never be decided: the enforcement layer also accepts the " +
      "sovereign tier (access_level >= 3), which existing node principals occupy. That " +
      "declared/enforced gap is an unresolved boundary, not a settled one.",
  },
  {
    id: "authority-closure",
    tone: "preproduction",
    headline: "AUTHORITY-CLOSURE-01 — PRE-PRODUCTION",
    detail:
      "The authority model (who may approve, and how authority is granted) is not " +
      "yet closed. BC-2 enforces the rule; it does not provision the role.",
  },
  {
    id: "deployment",
    tone: "undeployed",
    headline: "Boundary changes — NOT DEPLOYED",
    detail:
      "BC-1 / BC-2 / BC-3 are IMPLEMENTED and TESTED locally on the branch. Nothing " +
      "is deployed. Nothing is production-verified.",
  },
];
