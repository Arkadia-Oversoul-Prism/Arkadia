/**
 * ReasoMate direct threads — the shapes the canonical message substrate returns.
 *
 * Every reader validates before it renders. `GET /api/messages/inbox` answers
 * `{"conversations": [...]}` and `GET /api/messages/thread/{peer_uid}` answers
 * `{"messages": [...], "peer_uid": ...}`; a shape the console does not recognise
 * is reported as unrecognised rather than rendered as an empty conversation,
 * because "no messages" and "a payload I cannot read" are different facts.
 */

export interface DirectMessage {
  id: string;
  sender_uid: string;
  recipient_uid: string;
  content: string;
  timestamp: number;
}

export interface InboxEntry {
  peer_uid: string;
  last_message: DirectMessage;
  count: number;
  peer_handle?: string;
}

export interface ThreadReading {
  messages: DirectMessage[];
  peer_uid: string;
  peer_handle?: string;
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

export function isDirectMessage(value: unknown): value is DirectMessage {
  if (!isRecord(value)) return false;
  return (
    typeof value.id === "string" &&
    typeof value.sender_uid === "string" &&
    typeof value.recipient_uid === "string" &&
    typeof value.content === "string" &&
    typeof value.timestamp === "number"
  );
}

export function isInboxEntry(value: unknown): value is InboxEntry {
  if (!isRecord(value)) return false;
  return (
    typeof value.peer_uid === "string" &&
    typeof value.count === "number" &&
    isDirectMessage(value.last_message) &&
    (value.peer_handle === undefined || typeof value.peer_handle === "string")
  );
}

export function isInbox(value: unknown): value is { conversations: InboxEntry[] } {
  if (!isRecord(value)) return false;
  const conversations = value.conversations;
  return Array.isArray(conversations) && conversations.every(isInboxEntry);
}

export function isThread(value: unknown): value is ThreadReading {
  if (!isRecord(value)) return false;
  return (
    typeof value.peer_uid === "string" &&
    Array.isArray(value.messages) &&
    value.messages.every(isDirectMessage) &&
    (value.peer_handle === undefined || typeof value.peer_handle === "string")
  );
}

export function isSentMessage(value: unknown): value is { message: DirectMessage } {
  if (!isRecord(value)) return false;
  return isDirectMessage(value.message);
}

/**
 * Which side of the thread a message belongs to.
 *
 * The substrate is pairwise (`data/messages/{pair_key}.jsonl`, deterministic
 * pair ordering), so within a thread exactly one of the two parties is the
 * viewer: a message whose sender is the peer is theirs, everything else is the
 * viewer's. This avoids inventing a "current uid" the thread payload never
 * carries.
 */
export function messageDirection(message: DirectMessage, peerUid: string): "in" | "out" {
  return message.sender_uid === peerUid ? "in" : "out";
}

/** The label a peer is shown under: their handle when the backend resolved one. */
export function peerLabel(entry: { peer_uid: string; peer_handle?: string }): string {
  return entry.peer_handle ? `@${entry.peer_handle}` : entry.peer_uid;
}

/** Milliseconds since the epoch, rendered as an ISO-8601 instant in UTC. */
export function formatTimestamp(timestamp: number): string {
  const date = new Date(timestamp);
  if (Number.isNaN(date.getTime())) return "unknown";
  return date.toISOString().replace("T", " ").replace(".000Z", "Z");
}

/**
 * A recipient may be addressed by node uid or by handle; the handler accepts
 * either field and rejects an empty one. Only the handle form carries a leading
 * `@` in the UI, so the `@` is stripped before it becomes a request field.
 */
export function recipientField(value: string): { recipient_handle?: string; recipient_uid?: string } {
  const trimmed = value.trim();
  if (!trimmed) return {};
  if (trimmed.startsWith("@")) return { recipient_handle: trimmed.slice(1) };
  return { recipient_uid: trimmed };
}
