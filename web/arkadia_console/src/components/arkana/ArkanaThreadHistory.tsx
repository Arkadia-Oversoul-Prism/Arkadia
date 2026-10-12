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
 */
import { useState } from "react";
import type { ReactNode } from "react";
import { Panel, ContractState, Loading } from "../ui";
import { useHydration } from "../../lib/useHydration";
import { useAuth } from "../../contexts/AuthContext";
import { apiRequest } from "../../lib/apiClient";
import { endpoints } from "../../lib/endpoints";
import type { ArkanaThread, ArkanaThreadList, ArkanaThreadMessages } from "./arkanaThreadsContract";

/** A timestamp the backend may return in either ISO-8601 or SQLite form. */
function readableTime(value: string | null): string {
  if (!value) return "—";
  // SQLite's DATETIME default is `YYYY-MM-DD HH:MM:SS` (space, no zone); the
  // browser parses that inconsistently, so normalise it to ISO before parsing.
  const normalized = value.includes("T") ? value : value.replace(" ", "T");
  const parsed = new Date(normalized);
  return Number.isNaN(parsed.getTime()) ? value : parsed.toLocaleString();
}

function MessageList({ uuid }: { uuid: string }) {
  // Anchor the parameterised sub-resource on the declared collection: the
  // registry remains the single source of the base path (the registry-contract
  // guard requires the `useHydration` path argument to start with `endpoints.`).
  const messages = useHydration<ArkanaThreadMessages>(
    endpoints.arkanaThreads + "/" + encodeURIComponent(uuid) + "/messages",
    (p) => apiRequest<ArkanaThreadMessages>(p),
    [uuid],
  );

  if (messages.state !== "ready" || !messages.data) {
    return (
      <div className="mt-3">
        <ContractState state={messages.state} error={messages.error?.message} onRetry={messages.reload} />
      </div>
    );
  }

  const turns = messages.data.messages;
  if (turns.length === 0) {
    return (
      <p className="mt-3 text-sm text-white/50" data-testid="arkana-thread-empty">
        This thread has no recorded turns. An empty thread is not an error — it has simply not been used.
      </p>
    );
  }

  return (
    <ul className="mt-3 flex flex-col gap-3" data-testid="arkana-thread-messages">
      {turns.map((turn, index) => (
        <li key={index} className="rounded border border-line bg-ink/40 p-3">
          <p className="font-mono text-[10px] uppercase tracking-widest text-white/35">
            {turn.role === "user" ? "you" : "arkana"} · {readableTime(turn.created_at)}
          </p>
          <p className={`mt-1 whitespace-pre-wrap text-sm ${turn.role === "arkana" ? "text-emerald/90" : "text-white/85"}`}>
            {turn.content}
          </p>
        </li>
      ))}
    </ul>
  );
}

function ThreadHistoryFrame({ children }: { children: ReactNode }) {
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

/**
 * The read is mounted only while an identity holds it. Splitting it out keeps the
 * owner-scoped request from being attempted anonymously: the Arkana surface mounts
 * this module on every visit, so the fetch must live behind the identity gate, not
 * inside the always-rendered shell.
 */
function AuthenticatedThreadHistory() {
  const threads = useHydration<ArkanaThreadList>(endpoints.arkanaThreads, (p) =>
    apiRequest<ArkanaThreadList>(p),
  );
  const [selected, setSelected] = useState<string | null>(null);
  const rows = threads.data?.threads ?? [];

  return (
    <ThreadHistoryFrame>
      {threads.state === "ready" ? (
        rows.length === 0 ? (
          <p className="text-sm text-white/50" data-testid="arkana-threads-empty">
            No threads recorded for this identity.
          </p>
        ) : (
          <ul className="flex flex-col gap-2">
            {rows.map((thread: ArkanaThread) => {
              const active = selected === thread.uuid;
              return (
                <li key={thread.uuid}>
                  <button
                    type="button"
                    onClick={() => setSelected(active ? null : thread.uuid)}
                    aria-expanded={active}
                    data-testid={`arkana-thread-${thread.uuid}`}
                    className={`w-full rounded border p-3 text-left text-sm transition ${
                      active ? "border-emerald/50 bg-emerald/5 text-white/90" : "border-line bg-ink/40 text-white/70"
                    }`}
                  >
                    <span className="text-emerald/80">{thread.title || "Untitled conversation"}</span>
                    <span className="ml-2 font-mono text-[10px] text-white/35">
                      {thread.project_id ? `project ${thread.project_id} · ` : ""}
                      {readableTime(thread.updated_at)}
                    </span>
                  </button>
                  {active && <MessageList uuid={thread.uuid} />}
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
