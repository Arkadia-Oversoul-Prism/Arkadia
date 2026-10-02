/**
 * The primary unit of the console: the BOUNDARY INSTANCE.
 *
 * Not a page, not a dashboard card. The smallest meaningful object answers:
 *   What is this? Who has authority here? What is allowed?
 *   What happened? What evidence exists? What remains unverified?
 *
 * Pages are views over these objects (architecture §9 Q5, §10).
 */
import type { Posture } from "./posture";
import type { StageId } from "./grammar";

/** The operator verbs (architecture §5). */
export type Verb = "SEE" | "DISTINGUISH" | "AUTHORIZE" | "INSPECT" | "VERIFY";

export const VERB_MEANING: Record<Verb, string> = {
  SEE: "read the boundary and its posture",
  DISTINGUISH: "tell enforced from declared; decision from act",
  AUTHORIZE: "make a decision as a distinct authority",
  INSPECT: "follow the evidence chain",
  VERIFY: "see whether the act stayed in bounds",
};

/** A non-collapse this boundary establishes, with its enforcement status. */
export interface NonCollapse {
  left: string;
  right: string;
  /** true when machine-enforced; false when merely declared. */
  enforced: boolean;
  evidence: string[];
}

/** One side of the boundary: a consequential transition between two stages. */
export interface BoundaryInstance {
  id: string;
  /** Human-facing name, e.g. "Approval ≠ Execution". */
  title: string;
  /** The transition this boundary guards. */
  from: StageId;
  to: StageId;
  /** What the boundary means, in one sentence. */
  means: string;
  /** The collapse that existed before, stated plainly. */
  priorCollapse: string;
  posture: Posture;
  nonCollapses: NonCollapse[];
  /** Proven surfaces touched by this boundary. */
  surfaces: string[];
  /** What remains unverified about this boundary. */
  unresolved: string[];
  /** Verbs actually available for this boundary right now. */
  verbs: Verb[];
  /** Verbs that would be available if authority were provisioned. */
  verbsBlockedByProvisioning: Verb[];
}
