/**
 * The global Arkana overlay — one shell-level conversational surface.
 *
 * The archived Prism mounted a single `ArkanaOverlay` at the top of its
 * experience (`archive/frontend/arkadia-prism/web/public_prism/src/components/
 * solspire/SolSpireExperience.tsx`): a persistent Arkana thread reachable from
 * *any* lens, carrying a bounded snapshot of the current surface and project
 * into each turn. The console had no equivalent — Arkana was reachable only by
 * navigating to the `/arkana` surface, so a question about the view in front of
 * you meant leaving it. This component restores that capability **without**
 * restoring the archived Prism wholesale and **without** a second conversation
 * engine.
 *
 * What it reuses, and what it deliberately does not create:
 *
 *   - the streaming/conversation infrastructure is `lib/arkana.ts`
 *     (`streamArkana`, `ArkanaMessage`, `ArkanaTurn`) — the *same* module
 *     `ArkanaPage` and `WorkspacePage` call. There is no second engine, no
 *     second session id, no second transport;
 *   - the project context is `lib/projectContext.tsx` (`useProjectContext`) —
 *     the one shared answer to "which project am I in". The overlay reads it;
 *     it never creates a second store or provider;
 *   - the bounded project snapshot is the existing owner-scoped read
 *     `GET /solspire/projects/{id}/runtime-context` (the same contract
 *     `ProjectRuntimeCanvas` renders), summarised to counts and binding state.
 *     No full-corpus dump, no invented schema;
 *   - the conversation history is `ArkanaThreadHistory`, the same owner-scoped
 *     `/api/commune/threads` read the Arkana surface and the workspace rail use.
 *
 * Bounded context awareness. Each turn is scoped to the surface the user is
 * looking at and, when a project is active, to that project. The scope is
 * *stated in the overlay* (a context pack) and *carried into the turn* as a
 * bounded preamble — never as an unbounded corpus. A project whose runtime
 * context cannot be read is reported as `unavailable`, never as empty.
 *
 * Lifecycle. The overlay is a real dialog: it traps nothing it should not,
 * closes on Escape and on a backdrop click, moves focus into the composer on
 * open and returns it to the trigger on close, and locks body scroll while
 * open. It is mounted exactly once, by the shell.
 *
 * Read-only by construction. The overlay issues no mutating request: it streams
 * a turn and reads history. Authorization, approval and execution remain the
 * separate human acts they are everywhere else in the product.
 */
import { useCallback, useEffect, useId, useMemo, useRef, useState } from "react";
import { streamArkana, type ArkanaMessage } from "../../lib/arkana";
import { ApiError, apiRequest } from "../../lib/apiClient";
import { solspireProjectRuntime } from "../../lib/endpoints";
import { useOptionalProjectContext } from "../../lib/projectContext";
import { useAuth } from "../../contexts/AuthContext";
import { SURFACE_BY_ID, type SurfaceId } from "../../lib/surfaces";
import MarkdownViewer from "./MarkdownViewer";
import { ArkanaThreadHistory } from "./ArkanaThreadHistory";
import { IconArkana, IconClose } from "../Icons";
import "./design/arkana-overlay.css";

type TurnRole = "user" | "assistant";

interface Turn {
  id: number;
  role: TurnRole;
  content: string;
  status?: string;
}

/** The bounded project snapshot the overlay carries into a turn. */
interface ProjectSnapshot {
  state: "idle" | "loading" | "ready" | "partial" | "unavailable";
  tasks: number | null;
  files: number | null;
  memory: number | null;
  events: number | null;
  unavailable: string[];
}

const EMPTY_SNAPSHOT: ProjectSnapshot = {
  state: "idle",
  tasks: null,
  files: null,
  memory: null,
  events: null,
  unavailable: [],
};

function isAbortError(error: unknown): boolean {
  if (error instanceof DOMException && error.name === "AbortError") return true;
  if (error instanceof Error && error.name === "AbortError") return true;
  return false;
}

function countOf(value: unknown): number | null {
  return Array.isArray(value) ? value.length : null;
}

/**
 * Read the bounded project snapshot from the existing runtime-context contract.
 *
 * The handler bounds every list, so this reads counts and the binding state's
 * own UNKNOWN entries — it never assembles a corpus. A read that fails yields
 * `unavailable` with the reason, never a zeroed snapshot that would read as
 * "this project has nothing".
 */
function useProjectSnapshot(projectId: string | null, authenticated: boolean): ProjectSnapshot {
  const [snapshot, setSnapshot] = useState<ProjectSnapshot>(EMPTY_SNAPSHOT);

  useEffect(() => {
    if (!projectId) {
      setSnapshot(EMPTY_SNAPSHOT);
      return;
    }
    if (!authenticated) {
      setSnapshot({ ...EMPTY_SNAPSHOT, state: "unavailable", unavailable: ["authentication required"] });
      return;
    }
    let live = true;
    setSnapshot({ ...EMPTY_SNAPSHOT, state: "loading" });
    apiRequest<Record<string, unknown>>(solspireProjectRuntime(projectId))
      .then((data) => {
        if (!live) return;
        const store = (data.project_store ?? {}) as Record<string, unknown>;
        const binding = (data.binding_state ?? {}) as Record<string, string>;
        const unavailable = Object.entries(binding)
          .filter(([, state]) => state === "UNKNOWN")
          .map(([name]) => name);
        setSnapshot({
          state: unavailable.length ? "partial" : "ready",
          tasks: countOf(store.tasks),
          files: countOf(store.files),
          memory: countOf(store.memory),
          events: countOf(store.events),
          unavailable,
        });
      })
      .catch(() => {
        if (!live) return;
        setSnapshot({ ...EMPTY_SNAPSHOT, state: "unavailable", unavailable: ["runtime context"] });
      });
    return () => {
      live = false;
    };
  }, [projectId, authenticated]);

  return snapshot;
}

/**
 * The bounded preamble carried into a turn.
 *
 * It names the surface and, when a project is active, the project and the
 * counts the runtime-context contract actually reported. It is a *scope
 * statement*, not a corpus: the model is told what the user is looking at, not
 * handed the records. A snapshot that could not be read is stated as
 * unavailable rather than omitted, so the turn never silently loses its scope.
 */
export function buildOverlayPreamble(
  surface: SurfaceId,
  projectName: string | null,
  projectId: string | null,
  snapshot: ProjectSnapshot,
): string {
  const lines = [
    "ARKANA OVERLAY CONTEXT",
    `Surface: ${SURFACE_BY_ID[surface].name} (${SURFACE_BY_ID[surface].boundary})`,
  ];
  if (projectId) {
    lines.push(`Project: ${projectName ?? projectId} (${projectId})`);
    if (snapshot.state === "ready" || snapshot.state === "partial") {
      lines.push(
        `Project snapshot (bounded): tasks ${snapshot.tasks ?? "—"} · files ${snapshot.files ?? "—"} · memory ${snapshot.memory ?? "—"} · events ${snapshot.events ?? "—"}`,
      );
      if (snapshot.unavailable.length) {
        lines.push(`Unavailable sources: ${snapshot.unavailable.join(", ")}`);
      }
    } else if (snapshot.state === "unavailable") {
      lines.push("Project snapshot: unavailable — the runtime context could not be read.");
    }
  } else {
    lines.push("Project: none selected — this turn is not scoped to a project.");
  }
  lines.push(
    "Answer in the context of the surface above. Do not claim to have executed, authorized or approved anything.",
  );
  return lines.join("\n");
}

export function ArkanaOverlay({
  open,
  onClose,
  surface,
}: {
  open: boolean;
  onClose: () => void;
  surface: SurfaceId;
}) {
  const [turns, setTurns] = useState<Turn[]>([]);
  const [draft, setDraft] = useState("");
  const [sending, setSending] = useState(false);
  const [activity, setActivity] = useState("Ready");
  const [error, setError] = useState<string | null>(null);
  const nextId = useRef(0);
  const inputRef = useRef<HTMLTextAreaElement>(null);
  const endRef = useRef<HTMLDivElement>(null);
  const abortRef = useRef<AbortController | null>(null);
  const titleId = useId();

  const { isAuthenticated } = useAuth();
  // Tolerant read: the shell is rendered without a ProjectProvider in tests and
  // in any future embedding, and the overlay must degrade to "no project"
  // rather than crash the whole shell.
  const projectContext = useOptionalProjectContext();
  const activeProjectId = projectContext?.activeProjectId ?? null;
  const activeProject = projectContext?.activeProject ?? null;
  const snapshot = useProjectSnapshot(activeProjectId, isAuthenticated);

  // Focus the composer when the overlay opens, and return focus to whatever
  // opened it when it closes. The trigger is captured on open so a close always
  // restores the keyboard position the user left.
  const restoreRef = useRef<HTMLElement | null>(null);
  useEffect(() => {
    if (!open) return;
    restoreRef.current = (document.activeElement as HTMLElement) ?? null;
    const id = window.setTimeout(() => inputRef.current?.focus(), 0);
    return () => {
      window.clearTimeout(id);
      restoreRef.current?.focus?.();
    };
  }, [open]);

  // Escape closes the overlay; the body does not scroll behind it.
  useEffect(() => {
    if (!open) return;
    const onKey = (event: KeyboardEvent) => {
      if (event.key === "Escape") onClose();
    };
    window.addEventListener("keydown", onKey);
    const previousOverflow = document.body.style.overflow;
    document.body.style.overflow = "hidden";
    return () => {
      window.removeEventListener("keydown", onKey);
      document.body.style.overflow = previousOverflow;
    };
  }, [open, onClose]);

  useEffect(() => {
    // `scrollIntoView` is not implemented in every environment (jsdom, and some
    // embedded webviews). The overlay must not crash where it is absent — the
    // thread simply does not auto-scroll.
    endRef.current?.scrollIntoView?.({ behavior: "smooth", block: "end" });
  }, [turns, sending]);

  const stop = useCallback(() => {
    abortRef.current?.abort();
    abortRef.current = null;
    setSending(false);
    setActivity("Ready");
  }, []);

  // Abort an in-flight turn if the overlay unmounts, so a stream cannot outlive
  // the surface that started it.
  useEffect(() => () => abortRef.current?.abort(), []);

  async function runTurn(message: string, prior: Turn[]) {
    setError(null);
    setSending(true);
    setActivity("Arkana");

    const history: ArkanaMessage[] = prior.map(({ role, content }) => ({ role, content }));
    const userTurn: Turn = { id: nextId.current++, role: "user", content: message };
    const assistantId = nextId.current++;
    setTurns([...prior, userTurn, { id: assistantId, role: "assistant", content: "" }]);

    const controller = new AbortController();
    abortRef.current = controller;

    const runtimeMessage = [
      buildOverlayPreamble(surface, activeProject?.name ?? null, activeProjectId, snapshot),
      "",
      "Task: " + message,
    ].join("\n");

    try {
      const result = await streamArkana(
        runtimeMessage,
        history,
        {
          onStatus: (label: string) => setActivity(label),
          onDelta: (delta: string) =>
            setTurns((prev) =>
              prev.map((turn) => (turn.id === assistantId ? { ...turn, content: turn.content + delta } : turn)),
            ),
          signal: controller.signal,
        },
        activeProjectId ?? undefined,
      );
      setTurns((prev) =>
        prev.map((turn) =>
          turn.id === assistantId ? { ...turn, content: result.reply, status: undefined } : turn,
        ),
      );
    } catch (caught) {
      if (isAbortError(caught)) {
        setTurns((prev) =>
          prev.map((turn) =>
            turn.id === assistantId ? { ...turn, status: turn.content.trim() ? "Stopped" : "Cancelled" } : turn,
          ),
        );
        return;
      }
      const detail = caught instanceof ApiError ? caught.message : "Arkana could not complete this request.";
      setError(detail);
      setTurns((prev) => prev.filter((turn) => turn.id !== userTurn.id && turn.id !== assistantId));
      setDraft(message);
    } finally {
      if (abortRef.current === controller) abortRef.current = null;
      setSending(false);
      setActivity("Ready");
      inputRef.current?.focus();
    }
  }

  async function send() {
    const message = draft.trim();
    if (!message || sending) return;
    setDraft("");
    await runTurn(message, turns);
  }

  const contextLines = useMemo(() => {
    const lines = [
      isAuthenticated ? "AUTHENTICATED" : "AUTH REQUIRED",
      `SURFACE · ${SURFACE_BY_ID[surface].name}`,
      activeProjectId ? `PROJECT · ${activeProject?.name ?? activeProjectId}` : "PROJECT · NONE",
    ];
    if (activeProjectId) {
      lines.push(`PROJECT DATA · ${snapshot.state.toUpperCase()}`);
      if (snapshot.state === "ready" || snapshot.state === "partial") {
        lines.push(
          `TASKS ${snapshot.tasks ?? "—"} · FILES ${snapshot.files ?? "—"} · MEMORY ${snapshot.memory ?? "—"} · EVENTS ${snapshot.events ?? "—"}`,
        );
      }
      if (snapshot.unavailable.length) {
        lines.push(`UNAVAILABLE · ${snapshot.unavailable.join(", ")}`);
      }
    }
    lines.push("BOUNDED CONTEXT · NO FULL-CORPUS DUMP");
    return lines;
  }, [isAuthenticated, surface, activeProjectId, activeProject?.name, snapshot]);

  if (!open) return null;

  return (
    <div
      className="arkana-overlay"
      role="dialog"
      aria-modal="true"
      aria-labelledby={titleId}
      data-testid="arkana-overlay"
    >
      <button
        type="button"
        className="arkana-overlay-backdrop"
        aria-label="Close Arkana"
        data-testid="arkana-overlay-backdrop"
        onClick={onClose}
      />
      <div className="arkana-overlay-panel">
        <div className="arkana-overlay-head">
          <div className="min-w-0">
            <p className="font-mono text-[10px] uppercase tracking-[0.18em] text-emerald/70">
              Persistent Arkana thread
            </p>
            <h2 id={titleId} className="mt-1 flex items-center gap-2 font-display text-lg text-white/90">
              <span className="text-emerald/80">
                <IconArkana />
              </span>
              Arkana
            </h2>
          </div>
          <button
            type="button"
            onClick={onClose}
            aria-label="Close Arkana"
            data-testid="arkana-overlay-close"
            className="grid h-8 w-8 flex-none place-items-center rounded-lg border border-white/10 text-white/60 transition hover:text-white"
          >
            <IconClose />
          </button>
        </div>

        <div className="arkana-overlay-context" data-testid="arkana-overlay-context-pack">
          <p className="font-mono text-[10px] uppercase tracking-[0.18em] text-white/40">Current context</p>
          <div className="mt-2 flex flex-wrap gap-1.5">
            {contextLines.map((line) => (
              <span
                key={line}
                className="rounded border border-line bg-ink/40 px-2 py-0.5 font-mono text-[10px] uppercase tracking-wider text-white/50"
              >
                {line}
              </span>
            ))}
          </div>
          <p className="mt-2 text-[11px] leading-relaxed text-white/40">
            {activeProjectId
              ? "Fetched project records are summarised into each turn as bounded context. Missing sources remain visible."
              : "No project is selected, so this turn is scoped to the surface only."}
          </p>
        </div>

        <div className="arkana-overlay-body">
          <div className="arkana-overlay-thread" data-testid="arkana-overlay-thread">
            {turns.length === 0 ? (
              <p className="arkana-overlay-empty" data-testid="arkana-overlay-empty">
                Ask Arkana about what you are looking at. The turn is scoped to this surface
                {activeProjectId ? " and the active project" : ""}.
              </p>
            ) : (
              <ul className="flex flex-col gap-3">
                {turns.map((turn) => (
                  <li
                    key={turn.id}
                    className={"arkana-bubble " + (turn.role === "user" ? "arkana-bubble-user" : "arkana-bubble-assistant")}
                  >
                    <p className="font-mono text-[10px] uppercase tracking-widest text-white/35">
                      {turn.role === "user" ? "you" : "arkana"}
                      {turn.status ? " · " + turn.status : ""}
                    </p>
                    <div className="mt-2">
                      {turn.content ? (
                        <MarkdownViewer content={turn.content} compact presentationMode="denseConversation" />
                      ) : (
                        <p className="animate-pulse text-sm text-white/45">Working…</p>
                      )}
                    </div>
                  </li>
                ))}
              </ul>
            )}
            {sending ? (
              <p className="mt-3 animate-pulse font-mono text-[11px] uppercase tracking-widest text-white/40" data-testid="arkana-overlay-working">
                {activity}…
              </p>
            ) : null}
            <div ref={endRef} />
          </div>

          <aside className="arkana-overlay-history" aria-label="Conversation history">
            <ArkanaThreadHistory />
          </aside>
        </div>

        <div className="arkana-overlay-composer">
          <label className="sr-only" htmlFor="arkana-overlay-input">
            Message Arkana
          </label>
          <textarea
            id="arkana-overlay-input"
            ref={inputRef}
            value={draft}
            onChange={(event) => setDraft(event.target.value)}
            onKeyDown={(event) => {
              if (event.key === "Enter" && !event.shiftKey) {
                event.preventDefault();
                void send();
              }
            }}
            rows={2}
            placeholder="Ask Arkana about this surface…"
            data-testid="arkana-overlay-input"
            className="arkana-composer-input"
            disabled={sending}
          />
          <div className="arkana-composer-toolbar">
            <span className="font-mono text-[10px] uppercase tracking-widest text-white/30">
              Shift+Enter for newline
            </span>
            <div className="flex items-center gap-2">
              {sending ? (
                <button
                  type="button"
                  className="arkana-action-btn arkana-action-btn-danger"
                  data-testid="arkana-overlay-stop"
                  onClick={stop}
                >
                  Stop
                </button>
              ) : null}
              <button
                type="button"
                className="arkana-send"
                data-testid="arkana-overlay-send"
                disabled={sending || !draft.trim()}
                onClick={() => void send()}
              >
                {sending ? "Sending…" : "Send"}
              </button>
            </div>
          </div>
          {error ? (
            <p className="mt-2 text-xs text-gold/90" data-testid="arkana-overlay-error" role="alert">
              {error}
            </p>
          ) : null}
        </div>
      </div>
    </div>
  );
}
