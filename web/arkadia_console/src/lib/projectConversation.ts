/**
 * The project-conversation adapter — the reverse path of the journey.
 *
 * Forward: a conversation started in a project workspace is scoped to that
 * project (`streamArkana` carries `project_id`; a Lab session carries
 * `project_ref`). Reverse: a Lab session or mission outcome must be able to
 * return to the conversation thread it belongs to, so the journey closes
 * instead of running one way.
 *
 * This module is an *adapter over the existing routes*, not a new store:
 *
 *   GET  /solspire/projects/{id}/conversations
 *   POST /solspire/projects/{id}/conversations
 *   POST /solspire/projects/{id}/conversations/{conv_id}/messages
 *
 * The last one is `append_conversation_turn` (`solspire/conversation_bridge.py`),
 * which composes one turn across the substrates that already exist: the project
 * conversation record, the Knowledge OS thread/note, and the project activity
 * event. The console therefore persists through the canonical service and
 * creates no second database, no second approval system and no parallel thread.
 *
 * Two facts the shapes keep visible:
 *
 *  * A conversation is addressed by its canonical UUID, and the append route
 *    refuses a conversation that does not belong to the project (404). The
 *    adapter never invents an id.
 *  * The bridge reports its own Knowledge OS state (`knowledge.status`). A
 *    degraded ingestion is surfaced as degraded — the turn is durable either
 *    way, and the adapter does not relabel a failed ingestion as continuity.
 */
import { apiRequest } from "./apiClient";
import {
  solspireProjectConversations,
  solspireProjectConversationMessages,
} from "./endpoints";

/** One persisted turn, as the project conversation record stores it. */
export interface ProjectTurn {
  role: string;
  content: string;
  ts?: number;
}

/** One project conversation, as `project_store._conv_row` publishes it. */
export interface ProjectConversation {
  id: string;
  project_id: string;
  title: string;
  status: string;
  messages: ProjectTurn[];
  created_at: number;
  updated_at: number;
}

/** The Knowledge OS state the bridge reports for one appended turn. */
export interface TurnKnowledgeState {
  status: string;
  thread_uuid?: string | null;
  thread_id?: number | null;
  note_uuid?: string | null;
  duplicate?: boolean;
}

export interface AppendTurnResult {
  ok: boolean;
  message: { conversation_id: string; role: string; content: string };
  knowledge: TurnKnowledgeState;
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

function readTurns(value: unknown): ProjectTurn[] {
  if (!Array.isArray(value)) return [];
  return value
    .filter(isRecord)
    .map((row) => ({
      role: typeof row.role === "string" ? row.role : "user",
      content: typeof row.content === "string" ? row.content : "",
      ts: typeof row.ts === "number" ? row.ts : undefined,
    }))
    .filter((turn) => turn.content.length > 0);
}

function readConversation(value: unknown): ProjectConversation | null {
  if (!isRecord(value)) return null;
  const id = value.id;
  if (typeof id !== "string" || !id) return null;
  return {
    id,
    project_id: typeof value.project_id === "string" ? value.project_id : "",
    title: typeof value.title === "string" ? value.title : "Untitled",
    status: typeof value.status === "string" ? value.status : "active",
    messages: readTurns(value.messages),
    created_at: typeof value.created_at === "number" ? value.created_at : 0,
    updated_at: typeof value.updated_at === "number" ? value.updated_at : 0,
  };
}

/** The project's conversations, newest first (the server's own ordering). */
export async function listProjectConversations(projectId: string): Promise<ProjectConversation[]> {
  const payload = await apiRequest<unknown>(solspireProjectConversations(projectId));
  if (!isRecord(payload) || !Array.isArray(payload.conversations)) return [];
  return payload.conversations
    .map(readConversation)
    .filter((conversation): conversation is ProjectConversation => conversation !== null);
}

/** Create a project conversation. The server owns the id and the timestamps. */
export async function createProjectConversation(
  projectId: string,
  title: string,
): Promise<ProjectConversation> {
  const payload = await apiRequest<unknown>(solspireProjectConversations(projectId), {
    method: "POST",
    body: JSON.stringify({ title }),
  });
  const conversation = readConversation(payload);
  if (!conversation) {
    throw new Error("The conversation contract returned an unrecognised shape.");
  }
  return conversation;
}

/**
 * Append one turn through the canonical bridge.
 *
 * The returned `knowledge` block is the bridge's own report. A caller that
 * renders it must show `status` verbatim: `ingested` is continuity, `error` is
 * a degraded bridge, and neither is a claim this adapter may upgrade.
 */
export async function appendProjectTurn(
  projectId: string,
  conversationId: string,
  role: string,
  content: string,
): Promise<AppendTurnResult> {
  const payload = await apiRequest<unknown>(
    solspireProjectConversationMessages(projectId, conversationId),
    {
      method: "POST",
      body: JSON.stringify({ role, content }),
    },
  );
  if (!isRecord(payload) || !isRecord(payload.message)) {
    throw new Error("The turn-append contract returned an unrecognised shape.");
  }
  const knowledge = isRecord(payload.knowledge) ? payload.knowledge : {};
  return {
    ok: payload.ok === true,
    message: {
      conversation_id: String(payload.message.conversation_id ?? conversationId),
      role: String(payload.message.role ?? role),
      content: String(payload.message.content ?? content),
    },
    knowledge: {
      status: typeof knowledge.status === "string" ? knowledge.status : "unknown",
      thread_uuid: typeof knowledge.thread_uuid === "string" ? knowledge.thread_uuid : null,
      thread_id: typeof knowledge.thread_id === "number" ? knowledge.thread_id : null,
      note_uuid: typeof knowledge.note_uuid === "string" ? knowledge.note_uuid : null,
      duplicate: typeof knowledge.duplicate === "boolean" ? knowledge.duplicate : undefined,
    },
  };
}

/**
 * The thread a project workspace should attach to.
 *
 * Reuses the most recent conversation when one exists, and creates one only
 * when the project has none. This keeps a project to one working thread rather
 * than minting a new conversation per page load — the failure mode that makes a
 * "persistent" thread impossible to find again.
 */
export async function ensureProjectConversation(
  projectId: string,
  title: string,
): Promise<ProjectConversation> {
  const existing = await listProjectConversations(projectId);
  const active = existing.find((conversation) => conversation.status !== "archived");
  if (active) return active;
  return createProjectConversation(projectId, title);
}

/**
 * The recorded form of a Lab outcome, as it returns to the thread.
 *
 * A mission outcome is written as an `arkana`-role turn so the conversation
 * reads as one continuous exchange. The body is composed from the substrate's
 * own report — session id, state, run id, result state — and never asserts an
 * acceptance: a run that stopped at the review boundary is recorded as exactly
 * that.
 */
export interface LabOutcome {
  sessionId: string;
  state: string;
  runId?: string | null;
  resultState?: string | null;
  summary?: string | null;
  authorizationRef?: string | null;
}

export function composeLabOutcomeTurn(outcome: LabOutcome): string {
  const lines = [
    "**Engineering Lab outcome**",
    "",
    `- session: \`${outcome.sessionId}\``,
    `- session state: \`${outcome.state}\``,
  ];
  if (outcome.runId) lines.push(`- run: \`${outcome.runId}\``);
  if (outcome.resultState) lines.push(`- result state: \`${outcome.resultState}\``);
  if (outcome.authorizationRef) lines.push(`- authorization: \`${outcome.authorizationRef}\``);
  if (outcome.summary) lines.push("", outcome.summary);
  lines.push(
    "",
    "_Recorded from the substrate's own report. A run that stopped at the review boundary is a proposal awaiting human review, not an acceptance._",
  );
  return lines.join("\n");
}

/**
 * Return a Lab outcome to its project thread.
 *
 * This is the reverse edge of the journey: the session was created with this
 * project's `project_ref`, so its outcome belongs in this project's
 * conversation. The turn is appended through the same canonical bridge as any
 * other turn — there is no separate "mission log" store.
 */
export async function returnLabOutcomeToThread(
  projectId: string,
  conversationId: string,
  outcome: LabOutcome,
): Promise<AppendTurnResult> {
  return appendProjectTurn(projectId, conversationId, "arkana", composeLabOutcomeTurn(outcome));
}
