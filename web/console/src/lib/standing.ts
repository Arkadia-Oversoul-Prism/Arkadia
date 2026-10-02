/**
 * Standing states — the map's explicit non-claims, promoted to first-class,
 * non-dismissible surfaces (architecture §7).
 *
 * The console must not let a human infer a state the Verified Boundary Map
 * does not support. These render persistently, never as transient warnings.
 *
 * Source: RECONCILED-BOUNDARY-MAP-01.md §0.
 */

export type StandingTone = "unverified" | "unprovisioned" | "preproduction" | "undeployed" | "verified" | "partial";

export interface StandingState {
  id: string;
  tone: StandingTone;
  headline: string;
  detail: string;
}

export const STANDING_STATES: StandingState[] = [
  {
    id: "render",
    tone: "verified",
    headline: "Render — PRODUCTION-VERIFIED",
    detail:
      "The live host (arkadia-kw64.onrender.com) runs the merged hardened perimeter " +
      "(PR #180, ae847dd). Anonymous calls 401; the self-approval guard is live. " +
      "Verified by F.1–F.4 — never inferred.",
  },
  {
    id: "sovereign",
    tone: "partial",
    headline: "Sovereign authority — 2 PROVISIONED",
    detail:
      "The declared Flamekeeper role is still unseated, but the enforcement layer's " +
      "sovereign tier (access_level >= 3) is now occupied by two provisioned principals " +
      "(zahrune, jessica). Multi-principal governance is demonstrated (F.4). The " +
      "declared/enforced gap remains an unresolved boundary.",
  },
  {
    id: "authority-closure",
    tone: "preproduction",
    headline: "AUTHORITY-CLOSURE-01 — PRE-PRODUCTION",
    detail:
      "The authority model (who may approve, and how authority is granted) is not " +
      "yet closed. BC-2 enforces the rule; it does not seat the declared role.",
  },
  {
    id: "deployment",
    tone: "verified",
    headline: "Boundary changes — DEPLOYED",
    detail:
      "BC-1 / BC-2 / BC-3 are merged (PR #180, ae847dd) and production-verified by " +
      "F.1–F.4. The provenance edges (EXECUTION → WORK_EVENT → EVIDENCE → VERIFICATION) " +
      "remain CONTRADICTED — absence is the measurement, not a deployment gap.",
  },
];
