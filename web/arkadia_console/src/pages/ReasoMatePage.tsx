/**
 * ReasoMate — private node-to-node threads.
 *
 * Recovered from the archived Prism surface, which carried two lenses: the
 * Arkana conversation and direct threads. The Arkana conversation already has
 * its own surface (`/arkana`), so this surface is the second lens only and does
 * not duplicate it.
 *
 * Every read and write goes to the existing authenticated substrate
 * (`api/messages.py`: `GET /api/messages/inbox`, `GET /api/messages/thread/{peer_uid}`,
 * `POST /api/messages`). Nothing here is a second store: the same pairwise JSONL
 * the backend owns is read, and the only write path is the one the handler
 * already exposes. The surface is declared `requiresAuth`, and the shell refuses
 * it to an anonymous viewer before this component mounts.
 */
import { useState } from "react";
import { Page, Panel, ContractState, EmptyState } from "../components/ui";
import { useHydration } from "../lib/useHydration";
import { ApiError, apiRequest } from "../lib/apiClient";
import { endpoints, messagesThread } from "../lib/endpoints";
import {
  formatTimestamp,
  isInbox,
  isSentMessage,
  isThread,
  messageDirection,
  peerLabel,
  recipientField,
  type InboxEntry,
  type ThreadReading,
} from "./reasomate/reasomateContracts";

async function readInbox(path: string): Promise<InboxEntry[]> {
  const payload = await apiRequest<unknown>(path);
  if (!isInbox(payload)) {
    throw new ApiError("The inbox contract returned an unrecognised shape.", { kind: "UNKNOWN", path });
  }
  return payload.conversations;
}

async function readThread(path: string): Promise<ThreadReading> {
  const payload = await apiRequest<unknown>(path);
  if (!isThread(payload)) {
    throw new ApiError("The thread contract returned an unrecognised shape.", { kind: "UNKNOWN", path });
  }
  return payload;
}

export function ReasoMatePage() {
  const [selectedPeer, setSelectedPeer] = useState<string | null>(null);

  return (
    <Page
      title="ReasoMate"
      subtitle="Private node-to-node threads over the authenticated message substrate. The Arkana conversation lives on its own surface."
    >
      <div className="grid gap-4 lg:grid-cols-[minmax(0,320px)_minmax(0,1fr)]">
        <InboxPanel selectedPeer={selectedPeer} onSelect={setSelectedPeer} />
        {selectedPeer ? (
          <ThreadPanel peerUid={selectedPeer} onPeerChange={setSelectedPeer} />
        ) : (
          <Panel data-testid="reasomate-no-thread">
            <p className="mb-3 font-mono text-[11px] uppercase tracking-widest text-white/40">Thread</p>
            <EmptyState
              title="No thread selected"
              body="Choose a conversation from the inbox, or address a new one by node uid or @handle below."
            />
            <NewThreadForm onStarted={setSelectedPeer} />
          </Panel>
        )}
      </div>
    </Page>
  );
}

function InboxPanel({
  selectedPeer,
  onSelect,
}: {
  selectedPeer: string | null;
  onSelect: (peerUid: string) => void;
}) {
  const inbox = useHydration<InboxEntry[]>(endpoints.messagesInbox, readInbox);

  return (
    <Panel data-testid="reasomate-inbox">
      <p className="mb-3 font-mono text-[11px] uppercase tracking-widest text-white/40">Inbox</p>
      {inbox.state === "ready" && inbox.data ? (
        inbox.data.length === 0 ? (
          <EmptyState
            title="No conversations yet"
            body="This identity has no recorded thread. A new thread appears here once a message is sent or received."
          />
        ) : (
          <ul className="flex flex-col gap-2">
            {inbox.data.map((entry) => (
              <li key={entry.peer_uid}>
                <button
                  type="button"
                  onClick={() => onSelect(entry.peer_uid)}
                  aria-pressed={selectedPeer === entry.peer_uid}
                  data-testid={`reasomate-peer-${entry.peer_uid}`}
                  className={`w-full rounded border p-3 text-left transition ${
                    selectedPeer === entry.peer_uid
                      ? "border-gold/40 bg-gold/5"
                      : "border-line bg-ink/40 hover:border-white/20"
                  }`}
                >
                  <span className="flex items-baseline justify-between gap-2">
                    <span className="truncate font-mono text-[11px] text-white/70">{peerLabel(entry)}</span>
                    <span className="flex-none font-mono text-[10px] text-white/30">{entry.count}</span>
                  </span>
                  <span className="mt-1 block truncate text-[12px] text-white/45">
                    {entry.last_message.content}
                  </span>
                  <span className="mt-1 block font-mono text-[10px] text-white/25">
                    {formatTimestamp(entry.last_message.timestamp)}
                  </span>
                </button>
              </li>
            ))}
          </ul>
        )
      ) : (
        <ContractState state={inbox.state} error={inbox.error?.message} onRetry={inbox.reload} />
      )}
    </Panel>
  );
}

function ThreadPanel({ peerUid, onPeerChange }: { peerUid: string; onPeerChange: (peer: string) => void }) {
  const thread = useHydration<ThreadReading>(messagesThread(peerUid), readThread, [peerUid]);

  return (
    <Panel data-testid="reasomate-thread">
      <p className="mb-3 font-mono text-[11px] uppercase tracking-widest text-white/40">
        Thread · {peerUid}
      </p>
      {thread.state === "ready" && thread.data ? (
        <>
          {thread.data.messages.length === 0 ? (
            <EmptyState
              title="No messages in this thread"
              body="The substrate holds no message between this identity and that peer. Send one below to begin."
            />
          ) : (
            <ul className="flex max-h-[46vh] flex-col gap-2 overflow-y-auto" data-testid="reasomate-messages">
              {thread.data.messages.map((message) => {
                const direction = messageDirection(message, peerUid);
                return (
                  <li
                    key={message.id}
                    data-direction={direction}
                    className={`max-w-[85%] rounded border p-3 ${
                      direction === "out"
                        ? "self-end border-gold/25 bg-gold/5"
                        : "self-start border-line bg-ink/40"
                    }`}
                  >
                    <p className="whitespace-pre-wrap break-words text-[13px] text-white/75">{message.content}</p>
                    <p className="mt-1 font-mono text-[10px] text-white/25">
                      {direction === "out" ? "you" : peerLabel({ peer_uid: message.sender_uid, peer_handle: thread.data?.peer_handle })} ·{" "}
                      {formatTimestamp(message.timestamp)}
                    </p>
                  </li>
                );
              })}
            </ul>
          )}
          <Composer
            recipientValue={peerUid}
            lockRecipient
            onSent={() => {
              thread.reload();
              onPeerChange(peerUid);
            }}
          />
        </>
      ) : (
        <ContractState state={thread.state} error={thread.error?.message} onRetry={thread.reload} />
      )}
    </Panel>
  );
}

function NewThreadForm({ onStarted }: { onStarted: (peerUid: string) => void }) {
  return (
    <div className="mt-4 border-t border-line pt-4">
      <Composer
        recipientValue=""
        lockRecipient={false}
        onSent={(recipientUid) => {
          if (recipientUid) onStarted(recipientUid);
        }}
      />
    </div>
  );
}

/**
 * The one write path. The backend resolves a handle to a uid and returns the
 * stored message, so the surface never guesses the recipient's identity: the
 * thread it opens is the one the handler named in its response.
 */
function Composer({
  recipientValue,
  lockRecipient,
  onSent,
}: {
  recipientValue: string;
  lockRecipient: boolean;
  onSent: (recipientUid: string | null) => void;
}) {
  const [recipient, setRecipient] = useState(recipientValue);
  const [draft, setDraft] = useState("");
  const [sending, setSending] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const submit = async () => {
    const content = draft.trim();
    const addressed = recipientField(lockRecipient ? recipientValue : recipient);
    if (!content || (!addressed.recipient_handle && !addressed.recipient_uid)) {
      setError("A recipient and a message are both required.");
      return;
    }
    setSending(true);
    setError(null);
    try {
      const payload = await apiRequest<unknown>(endpoints.messages, {
        method: "POST",
        body: JSON.stringify({ ...addressed, content }),
      });
      if (!isSentMessage(payload)) {
        throw new ApiError("The send contract returned an unrecognised shape.", {
          kind: "UNKNOWN",
          path: endpoints.messages,
        });
      }
      setDraft("");
      onSent(payload.message.recipient_uid);
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "The message was not sent.");
    } finally {
      setSending(false);
    }
  };

  return (
    <div className="mt-4 border-t border-line pt-4">
      {!lockRecipient && (
        <label className="mb-2 block">
          <span className="mb-1 block font-mono text-[10px] uppercase tracking-widest text-white/35">
            Recipient · node uid or @handle
          </span>
          <input
            value={recipient}
            onChange={(event) => setRecipient(event.target.value)}
            data-testid="reasomate-recipient"
            className="w-full rounded border border-line bg-ink/60 px-3 py-2 text-[13px] text-white/80 outline-none focus:border-gold/40"
            placeholder="node uid or @handle"
          />
        </label>
      )}
      <label className="block">
        <span className="mb-1 block font-mono text-[10px] uppercase tracking-widest text-white/35">Message</span>
        <textarea
          value={draft}
          onChange={(event) => setDraft(event.target.value)}
          rows={3}
          data-testid="reasomate-draft"
          className="w-full resize-y rounded border border-line bg-ink/60 px-3 py-2 text-[13px] text-white/80 outline-none focus:border-gold/40"
          placeholder="Write a private message…"
        />
      </label>
      {error && (
        <p className="mt-2 break-words font-mono text-[11px] text-red-300/70" data-testid="reasomate-send-error">
          {error}
        </p>
      )}
      <div className="mt-2 flex items-center justify-between gap-3">
        <p className="text-[11px] text-white/30">
          Stored by the backend under its pairwise thread record. Sending is an authenticated write.
        </p>
        <button
          type="button"
          onClick={submit}
          disabled={sending}
          data-testid="reasomate-send"
          className="cg-btn cg-btn-primary disabled:opacity-50"
        >
          {sending ? "Sending…" : "Send"}
        </button>
      </div>
    </div>
  );
}
