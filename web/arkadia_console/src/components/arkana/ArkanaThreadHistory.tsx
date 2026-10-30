/**
 * Arkana — first-class thread history (read-only slice, Workstream 4).
 *
 * Binds the console to the verified `/api/commune/threads` contract:
 *
 *   GET  /api/commune/threads                     -> { threads: ArkanaThread[] }
 *   GET  /api/commune/threads/{uuid}/messages      -> { messages: ArkanaThreadMessage[] }
 *
 * Both `GET` routes require an identity (`_user_id()` raises 401 with
 * `Authentication required`); reads are owner-scoped, so another identity's
 * thread is a 404, not a leak. This module therefore issues **no** mutating
 * request: opening, renaming, and appending to a thread are human acts and are
 * not wired here. Loading, empty, auth-required, unavailable, and read-failed
 * are distinct states — an empty list is never presented as a failure, and a
 * failure is never presented as an empty thread.
 *
 * The Arkana surface is reachable anonymously (its chat contract is public,
 * `/oracle` and `/commune` reconcile here). An owner-scoped read the visitor
 * cannot satisfy must not be *attempted*: issuing it produces a browser 401 for
 * every anonymous visit and collapses into an indistinguishable console error.
 * When no identity is present the slice states the authorization requirement
 * directly and spends no request; the read is spent only while an identity is
 * known, and `isAuthenticated` transitions `false -> true` on sign-in, so the
 * history hydrates immediately on authentication.
 *
 * `compact` is the A1.1 rail/drawer presentation: same contracts, less chrome.
 */
import { useState } from "react";
import type { ReactNode } from "react";
import { Panel, ContractState, Loading } from "../ui";
import { useHydration } from "../../lib/useHydration";
import { useAuth } from "../../contexts/AuthContext";
import { apiRequest } from "../../lib/apiClient";
import { endpoints } from "../../lib/endpoints";
import type { ArkanaThread, ArkanaThreadList, ArkanaThreadMessages } from "./arkanaThreadsContract";
import { readableTime } from "./arkanaThreadTime";

function MessageList({ uuid, compact }: { uuid: string; compact?: boolean }) {
  const messages = useHydration<ArkanaThreadMessages>(
    endpoints.arkanaThreads + "/" + encodeURIComponent(uuid) + "/messages",
    (p) => apiRequest<ArkanaThreadMessages>(p),
    [uuid],
  );

  if (messages.state !== "ready" || !messages.data) {
    return (
      <div className={compact ? "mt-2" : "mt-3"}>
        <ContractState state={messages.state} error={messages.error?.message} onRetry={messages.reload} />
      </div>
    );
  }

  const turns = messages.data.messages;
  if (turns.length === 0) {
    return (
      <p className={`${compact ? "mt-2 text-xs" : "mt-3 text-sm"} text-white/50`} data-testid="arkana-thread-empty">
        This thread has no recorded turns. An empty thread is not an error — it has simply not been used.
      </p>
    );
  }

  return (
    <ul className={`${compact ? "mt-2 gap-2" : "mt-3 gap-3"} flex flex-col`} data-testid="arkana-thread-messages">
      {turns.map((turn, index) => (
        <li key={index} className={`rounded border border-line bg-ink/40 ${compact ? "p-2" : "p-3"}`}>
          <p className="font-mono text-[10px] uppercase tracking-widest text-white/35">
            {turn.role === "user" ? "you" : "arkana"} · {readableTime(turn.created_at)}
          </p>
          <p className={`mt-1 whitespace-pre-wrap ${compact ? "text-xs" : "text-sm"} ${turn.role === "arkana" ? "text-emerald/90" : "text-white/85"}`}>
            {turn.content}
          </p>
        </li>
      ))}
    </ul>
  );
}

function ThreadHistoryFrame({ children, compact }: { children: ReactNode; compact?: boolean }) {
  if (compact) {
    return (
      <div className="flex flex-col gap-2" data-testid="arkana-thread-history-compact">
        <p className="font-mono text-[10px] uppercase tracking-widest text-white/35">Recent</p>
        {children}
      </div>
    );
  }
  return (
    <Panel className="mb-4">
      <p className="mb-1 font-mono text-[11px] uppercase tracking-widest text-white/40">Thread history</p>
      <p className="mb-4 text-xs text-white/40">
        Read-only. Threads are owner-scoped by the backend; opening, renaming, or appending a turn is a
        separate act this surface does not perform.
      </p>
      {children}
    </Panel>
  );
}

function AuthenticatedThreadHistory({ compact }: { compact?: boolean }) {
  const threads = useHydration<ArkanaThreadList>(endpoints.arkanaThreads, (p) =>
    apiRequest<ArkanaThreadList>(p),
  );
  const [selected, setSelected] = useState<string | null>(null);
  const rows = threads.data?.threads ?? [];

  return (
    <ThreadHistoryFrame compact={compact}>
      {threads.state === "ready" ? (
        rows.length === 0 ? (
          <p className={`${compact ? "text-xs" : "text-sm"} text-white/50`} data-testid="arkana-threads-empty">
            No threads recorded for this identity.
          </p>
        ) : (
          <ul className={`flex flex-col ${compact ? "gap-1.5" : "gap-2"}`}>
            {rows.map((thread: ArkanaThread) => {
              const active = selected === thread.uuid;
              return (
                <li key={thread.uuid}>
                  <button
                    type="button"
                    onClick={() => setSelected(active ? null : thread.uuid)}
                    aria-expanded={active}
                    data-testid={`arkana-thread-${thread.uuid}`}
                    className={`w-full rounded border text-left transition ${
                      compact ? "p-2 text-xs" : "p-3 text-sm"
                    } ${
                      active ? "border-emerald/50 bg-emerald/5 text-white/90" : "border-line bg-ink/40 text-white/70"
                    }`}
                  >
                    <span className="block truncate text-emerald/80">{thread.title || "Untitled conversation"}</span>
                    <span className="mt-0.5 block font-mono text-[10px] text-white/35">
                      {thread.project_id ? `project ${thread.project_id} · ` : ""}
                      {readableTime(thread.updated_at)}
                    </span>
                  </button>
                  {active && <MessageList uuid={thread.uuid} compact={compact} />}
                </li>
              );
            })}
          </ul>
        )
      ) : (
        <ContractState state={threads.state} error={threads.error?.message} onRetry={threads.reload} />
      )}
    </ThreadHistoryFrame>
  );
}

export function ArkanaThreadHistory() {
  const { loading, isAuthenticated } = useAuth();

  if (loading) {
    return (
      <ThreadHistoryFrame>
        <Loading label="Verifying identity…" />
      </ThreadHistoryFrame>
    );
  }

  if (!isAuthenticated) {
    return (
      <ThreadHistoryFrame>
        <ContractState state="auth-required" />
      </ThreadHistoryFrame>
    );
  }

  return <AuthenticatedThreadHistory />;
}
