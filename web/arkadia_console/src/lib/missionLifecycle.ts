/**
 * Mission lifecycle adapter — reads real governed lifecycle state.
 *
 * The backend chain is the canonical source of truth:
 *
 *   solspire/voice_contracts.py   — VoiceStage, STAGE_ORDER (the evidence
 *     timeline), requires_approval, RISK_LEVELS
 *   solspire/voice_router.py      — POST /solspire/voice/events/{id}/understand
 *     | propose | authorize | execute | verify; GET /events/{id}/chain
 *   solspire/voice_pipeline.py    — the pipeline that appends each stage as a
 *     separately recorded act (get() returns event + chain + chain_digest)
 *
 * The console's seven-stage lifecycle display (Understand → Propose →
 * Authorize → Execute → Verify → Accept → Release) is a *view* over the
 * canonical chain. The first five stages map 1:1 onto real recorded stages.
 * The last two — Accept and Release — have NO backend record: the substrate
 * never self-sets COMPLETED (lab/engineering_lab/contracts.py), and there is
 * no RELEASE act anywhere in the authority model. The adapter therefore marks
 * them `unavailable` with an explicit reason. A stage with no evidence renders
 * as unknown, never as complete: a green indicator never implies more than the
 * evidence supports.
 *
 * Nothing here creates authority, a state store, or an approval mechanism. The
 * adapter only *reads* the existing routes.
 */
import { apiRequest } from "./apiClient";
import { voiceEvent, voiceEventChain, voiceEventsForSession } from "./endpoints";
import type { Lifecycle, StageState } from "../components/workspace/Inspector";

/** The canonical backend stage vocabulary (VoiceStage, voice_contracts.py). */
export const CANONICAL_STAGES = [
  "VOICE_EVENT",
  "TRANSCRIPT",
  "INTENT",
  "CONTEXT",
  "AUTHORITY",
  "PROPOSAL",
  "APPROVAL",
  "AUTHORIZATION",
  "EXECUTION",
  "RESULT",
  "WORK_EVENT",
  "EVIDENCE",
  "VERIFICATION",
] as const;

export type CanonicalStage = (typeof CANONICAL_STAGES)[number];

/** One inspectable stage of the causal evidence chain (ChainStage, voice_contracts.py). */
export interface ChainStageRecord {
  stage: string;
  seq: number;
  record_type: string;
  record_id: string;
  payload: Record<string, unknown>;
  created_at: number;
  prev_record_id: string | null;
  payload_digest: string;
}

/** The read contract served by GET /solspire/voice/events/{id}/chain. */
export interface VoiceChain {
  event_id: string;
  stages: ChainStageRecord[];
  chain_digest: string;
}

/** The read contract served by GET /solspire/voice/events/{id}. */
export interface VoiceEventRecord {
  event: {
    event_id: string;
    session_id: string;
    subject: string;
    status: string;
    error_state: string | null;
    transcript: string;
    workspace_ref: string | null;
  };
  chain: ChainStageRecord[];
  chain_digest: string;
  stage_order: string[];
}

/**
 * What the backend is able to report about the lifecycle right now.
 *
 * `unavailable` means the adapter could not reach the contract — it is a
 * transport truth, not a claim about the mission. `empty` means the contract
 * answered with no recorded stages (a mission whose first act has not been
 * recorded yet). `ready` means the real chain was read.
 */
export type LifecycleReadState = "idle" | "loading" | "ready" | "empty" | "unavailable";

export interface MissionLifecycleRead {
  state: LifecycleReadState;
  eventId?: string;
  chain?: VoiceChain;
  error?: string;
}

/** How the inspector understands each canonical stage. */
const STAGE_UNDERSTANDING: Record<string, Lifecycle["stage"] | null> = {
  VOICE_EVENT: "understand",
  TRANSCRIPT: "understand",
  INTENT: "understand",
  CONTEXT: "understand",
  AUTHORITY: "understand",
  PROPOSAL: "propose",
  APPROVAL: "authorize",
  AUTHORIZATION: "authorize",
  EXECUTION: "execute",
  RESULT: "execute",
  WORK_EVENT: "execute",
  EVIDENCE: "execute",
  VERIFICATION: "verify",
};

/**
 * Project the canonical chain onto the inspector's seven-stage lifecycle.
 *
 * Rules:
 *  - A stage the canonical chain records as reached is `done`.
 *  - APPROVAL belongs to the authorise act (a human decision is present), and
 *    an APPROVAL record whose proposal status is not ACCEPTED renders as
 *    `pending`, never as done — the authorisation is not granted.
 *  - A canonical stage that has no record renders as `pending` only when an
 *    earlier stage proves the chain is in progress; otherwise `unknown`.
 *  - Accept and Release have no backend record anywhere. They are
 *    `unavailable` with a plain reason — the substrate never self-sets them.
 */
export function projectLifecycle(read: MissionLifecycleRead): Lifecycle[] {
  const stages = read.chain?.stages ?? [];
  const recorded = new Set(stages.map((s) => s.stage));

  const unavailable = read.state === "unavailable";
  const unreachableNote =
    read.error ?? "The mission lifecycle contract is not reachable for this identity";

  const approvalStage = stages.find((s) => s.stage === "APPROVAL");
  const inProgress = Boolean(stages.length);
  const verification = stages.find((s) => s.stage === "VERIFICATION");
  const verificationPayload = verification
    ? (verification.payload?.verification as { verdict?: string } | undefined)
    : undefined;
  const verificationVerdict = verificationPayload?.verdict ?? "";

  const stageState = (canonical: string): { state: StageState; evidence?: string } => {
    if (unavailable) {
      return { state: "unavailable", evidence: unreachableNote };
    }
    if (!recorded.has(canonical)) {
      return {
        state: inProgress ? "pending" : "unknown",
        evidence: inProgress
          ? "Not reached in the recorded evidence chain"
          : "No governed mission is recorded against this conversation yet",
      };
    }
    const record = stages.find((s) => s.stage === canonical);
    const payload = record?.payload ?? {};
    if (canonical === "APPROVAL") {
      const status = String(payload.proposal_status ?? "");
      if (status !== "ACCEPTED") {
        return {
          state: "pending",
          evidence: `Human decision recorded but not ACCEPTED (${status || "unknown"})`,
        };
      }
    }
    return { state: "done", evidence: `${canonical} recorded (${record?.record_id ?? "?"})` };
  };

  const lifecycle: Lifecycle[] = [];
  let current: Lifecycle["stage"] | null = null;
  for (const canonical of CANONICAL_STAGES) {
    const mapped = STAGE_UNDERSTANDING[canonical];
    if (mapped === null || mapped === undefined) continue;
    if (mapped === current) continue;
    current = mapped;

    // The first canonical act of a mapped group decides when the stage began;
    // later sub-acts of the same group refine the evidence but never upgrade
    // the state on their own. The one exception is the authorize stage: it is
    // done *only* when the AUTHORIZATION grant is recorded — APPROVAL without
    // AUTHORIZATION is the AUTHORIZATION_REQUIRED posture, not authorization.
    if (mapped === "authorize") {
      const grantState = stageState("AUTHORIZATION");
      const grantRecorded = recorded.has("AUTHORIZATION");
      const approvalStatus = String(
        approvalStage?.payload?.proposal_status ?? "",
      );
      lifecycle.push({
        stage: "authorize",
        state: grantRecorded
          ? grantState.state
          : unavailable
            ? "unavailable"
            : inProgress
              ? "pending"
              : "unknown",
        evidence: grantRecorded
          ? grantState.evidence
          : unavailable
            ? unreachableNote
            : !inProgress
              ? "No governed mission is recorded against this conversation yet"
              : approvalStatus === "ACCEPTED"
                ? "Proposal accepted by a human decision, but no authorization grant is recorded yet"
                : approvalStatus
                  ? `Human decision recorded but not ACCEPTED (${approvalStatus})`
                  : "No authorization grant is recorded for this mission",
      });
      continue;
    }

    const { state, evidence } = stageState(canonical);
    lifecycle.push({ stage: mapped, state, evidence });
  }

  // Accept and Release have no backend record anywhere — the substrate never
  // self-sets COMPLETED and no RELEASE act exists in the authority model.
  // They render as unavailable with a plain reason, never as complete.
  lifecycle.push({
    stage: "accept",
    state: "unavailable",
    evidence: unavailable
      ? unreachableNote
      : "No backend record represents human acceptance — the substrate never self-sets COMPLETED (lab/engineering_lab/contracts.py)",
  });
  lifecycle.push({
    stage: "release",
    state: "unavailable",
    evidence: unavailable
      ? unreachableNote
      : "No RELEASE act exists in the authority model; nothing in this environment is released",
  });

  if (verificationVerdict && verificationVerdict !== "PENDING") {
    const verify = lifecycle.find((l) => l.stage === "verify");
    if (verify) {
      verify.state = "done";
      verify.evidence = `VERIFICATION recorded — ${verificationVerdict}`;
    }
  }

  return lifecycle;
}

/** Read the canonical chain for one voice event. */
export async function readMissionLifecycle(eventId: string): Promise<MissionLifecycleRead> {
  try {
    const chain = await apiRequest<VoiceChain>(voiceEventChain(eventId));
    return { state: chain.stages.length ? "ready" : "empty", eventId, chain };
  } catch (error) {
    return {
      state: "unavailable",
      eventId,
      error:
        error instanceof Error
          ? error.message
          : "mission lifecycle contract unreachable",
    };
  }
}

/** The first voice event of a conversation session, if one exists. */
export interface VoiceEventSummary {
  event_id: string;
  session_id: string;
  status: string;
  transcript: string;
}

export async function readLatestVoiceEvent(sessionId: string): Promise<VoiceEventSummary | null> {
  try {
    const payload = await apiRequest<{ events: VoiceEventSummary[] }>(
      voiceEventsForSession(sessionId),
    );
    return payload.events?.[0] ?? null;
  } catch {
    // A 401/403 here means the signed-in identity cannot read the chain — the
    // lifecycle stays "unavailable", never rendered as complete.
    return null;
  }
}

/** Read a single event with its full chain in one call (compact inspector read). */
export async function readVoiceEvent(eventId: string): Promise<VoiceEventRecord | null> {
  try {
    return await apiRequest<VoiceEventRecord>(voiceEvent(eventId));
  } catch {
    return null;
  }
}
