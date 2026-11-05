/**
 * Workspace — the conversational surface (default destination).
 *
 * One conversation, multiple specialized systems. The user expresses an
 * intention; Arkana understands it; SolSpire coordinates the capability; the
 * governed execution layer performs only authorized actions; the canvas renders
 * the result.
 *
 * What this page does NOT do, deliberately:
 *   - it does not invent a second approval system (authorization is read from
 *     the existing Lab grant contract, and the inspector shows the real state);
 *   - it does not fabricate a visualization for every answer (`selectArtifact`
 *     returns null for an ordinary reply, which then renders as Markdown);
 *   - it does not present a capability as available when its contract is
 *     unverified (the composer reads `capabilities.ts` and marks those).
 *
 * The conversation is held in component state, and — when a project is active —
 * each completed turn is persisted through the canonical project-conversation
 * service (`lib/projectConversation.ts`), which composes the turn across the
 * existing substrates. The thread is therefore attached to its project and
 * survives a reload; the inspector reports the bridge's own Knowledge OS state
 * rather than claiming continuity it did not get.
 */
import { useEffect, useRef, useState } from "react";
import { streamArkana, type ArkanaMessage } from "../lib/arkana";
import { apiRequest, ApiError } from "../lib/apiClient";
import { endpoints } from "../lib/endpoints";
import { CAPABILITIES, CAPABILITY_BY_TOKEN, type Capability } from "../lib/capabilities";
import { useProjectContext } from "../lib/projectContext";
import { useAuth } from "../contexts/AuthContext";
import {
  appendProjectTurn,
  ensureProjectConversation,
  type ProjectConversation,
} from "../lib/projectConversation";
import { isKnowledgeSearchData, recordDetail, recordTitle } from "./knowledge/knowledgeContracts";
import type { KnowledgeSearchData } from "./knowledge/knowledgeContracts";
import MarkdownViewer from "../components/arkana/MarkdownViewer";
import { WorkspaceShell } from "../components/workspace/WorkspaceShell";
import { Inspector, type InspectorContext, type Lifecycle } from "../components/workspace/Inspector";
import { ArtifactView, selectArtifact, type Artifact } from "../components/workspace/ArtifactView";

type TurnRole = "user" | "assistant";

interface Turn {
  id: number;
  role: TurnRole;
  content: string;
  /** The capability this turn was scoped to, if any. */
  capability?: Capability;
  /** Retrieved evidence, kept visible rather than summarised away. */
  evidence?: Array<{ id: string; mode: string; title: string; detail: string }>;
  artifact?: Artifact | null;
  status?: string;
  error?: string;
}

const RESEARCH_MODES = ["semantic", "fulltext", "tag", "timeline", "project", "people", "reference"];

function extractEvidence(data: KnowledgeSearchData) {
  let sequence = 0;
  return Object.entries(data).flatMap(([mode, records]) =>
    records.map((record) => {
      sequence += 1;
      const detail = recordDetail(record);
      return {
        id: "R" + sequence,
        mode,
        title: recordTitle(record, mode, sequence - 1),
        detail: detail.length > 1200 ? detail.slice(0, 1200) + "…" : detail,
      };
    }),
  );
}

function isAbortError(error: unknown): boolean {
  if (error instanceof DOMException && error.name === "AbortError") return true;
  if (error instanceof Error && error.name === "AbortError") return true;
  return false;
}

/** Parse a leading `@token` from the draft, returning the capability and the rest. */
function parseToken(draft: string): { capability: Capability | null; rest: string } {
  const match = draft.match(/^@([a-z-]+)\s*/i);
  if (!match) return { capability: null, rest: draft };
  const capability = CAPABILITY_BY_TOKEN[match[1].toLowerCase()] ?? null;
  return { capability, rest: draft.slice(match[0].length) };
}

export function WorkspacePage() {
  const [turns, setTurns] = useState<Turn[]>([]);
  const [draft, setDraft] = useState("");
  const [sending, setSending] = useState(false);
  const [activity, setActivity] = useState("Ready");
  const [error, setError] = useState<string | null>(null);
  const nextId = useRef(0);
  const inputRef = useRef<HTMLTextAreaElement>(null);
  const endRef = useRef<HTMLDivElement>(null);
  const abortRef = useRef<AbortController | null>(null);

  // The active project is the shared context's, not this page's. One answer to
  // "which project am I in" is what keeps a conversation scoped to the same
  // project as the Lab session it produces.
  const { projects, projectRows, activeProjectId, activeProject, selectProject } = useProjectContext();
  const { isAuthenticated } = useAuth();

  // The canonical project thread. `null` means no thread is attached yet;
  // `threadState` reports why, so the inspector never implies persistence it
  // does not have.
  const [thread, setThread] = useState<ProjectConversation | null>(null);
  const [threadState, setThreadState] = useState<"idle" | "attaching" | "attached" | "unavailable">(
    "idle",
  );
  const [threadNote, setThreadNote] = useState<string | null>(null);

  // Attach (or re-attach) the project thread whenever the active project
  // changes. A project with no conversation gets one; a project that already
  // has one reuses it, so the thread is findable again after a reload.
  useEffect(() => {
    if (!activeProjectId || !isAuthenticated) {
      setThread(null);
      setThreadState("idle");
      setThreadNote(null);
      return;
    }
    let cancelled = false;
    setThreadState("attaching");
    setThreadNote(null);
    ensureProjectConversation(activeProjectId, `${activeProject?.name ?? "Project"} conversation`)
      .then((conversation) => {
        if (cancelled) return;
        setThread(conversation);
        setThreadState("attached");
      })
      .catch((caught) => {
        if (cancelled) return;
        setThread(null);
        setThreadState("unavailable");
        setThreadNote(
          caught instanceof ApiError
            ? `${caught.status ?? "—"} ${caught.kind}: ${caught.message}`
            : "The project conversation service could not be reached.",
        );
      });
    return () => {
      cancelled = true;
    };
  }, [activeProjectId, activeProject?.name, isAuthenticated]);

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: "smooth", block: "end" });
  }, [turns, sending]);

  const parsed = parseToken(draft);
  const activeCapability = parsed.capability;

  /**
   * Persist one completed turn through the canonical bridge.
   *
   * A persistence failure is reported, never swallowed: the turn stays visible
   * in the canvas, and the inspector says the thread did not record it. The
   * bridge's own Knowledge OS state is surfaced verbatim.
   */
  async function persistTurn(role: string, content: string) {
    if (!activeProjectId || !thread) return;
    try {
      const result = await appendProjectTurn(activeProjectId, thread.id, role, content);
      setThreadNote(
        result.knowledge.status === "ingested"
          ? "Turn recorded in the project thread and ingested into Knowledge OS."
          : `Turn recorded in the project thread. Knowledge OS ingestion reported: ${result.knowledge.status}.`,
      );
    } catch (caught) {
      setThreadNote(
        caught instanceof ApiError
          ? `Turn not recorded: ${caught.status ?? "—"} ${caught.kind}: ${caught.message}`
          : "Turn not recorded: the project conversation service could not be reached.",
      );
    }
  }

  function stop() {
    abortRef.current?.abort();
    abortRef.current = null;
    setSending(false);
    setActivity("Ready");
  }

  async function runTurn(message: string, capability: Capability | null, prior: Turn[]) {
    setError(null);
    setSending(true);
    setActivity(capability ? capability.label : "Arkana");

    const history: ArkanaMessage[] = prior.map(({ role, content }) => ({ role, content }));
    const userTurn: Turn = { id: nextId.current++, role: "user", content: message, capability: capability ?? undefined };
    const assistantId = nextId.current++;
    setTurns([...prior, userTurn, { id: assistantId, role: "assistant", content: "", capability: capability ?? undefined }]);

    const controller = new AbortController();
    abortRef.current = controller;

    try {
      let runtimeMessage = message;
      let evidence: Turn["evidence"];

      // A knowledge-scoped turn retrieves real corpus records first and keeps
      // them visible. The synthesis is then constrained to that evidence.
      if (capability?.id === "knowledge.search") {
        setActivity("Searching Knowledge OS");
        const payload = await apiRequest<unknown>(endpoints.knowledgeSearch, {
          method: "POST",
          body: JSON.stringify({ query: message, modes: RESEARCH_MODES, top_k: 12 }),
          signal: controller.signal,
        });
        if (!isKnowledgeSearchData(payload)) {
          throw new ApiError("The Knowledge OS search contract returned an unrecognised shape.", {
            kind: "UNKNOWN",
            path: endpoints.knowledgeSearch,
          });
        }
        evidence = extractEvidence(payload);
        if (evidence.length === 0) {
          setTurns((prev) =>
            prev.map((turn) =>
              turn.id === assistantId
                ? {
                    ...turn,
                    content:
                      "No records were returned by the accessible Knowledge OS corpus for this query. No synthesis was generated.",
                    status: "No corpus records",
                    evidence: [],
                  }
                : turn,
            ),
          );
          return;
        }
        setTurns((prev) =>
          prev.map((turn) => (turn.id === assistantId ? { ...turn, evidence, status: "Retrieved evidence" } : turn)),
        );
        runtimeMessage = [
          "ARKANA OPERATING MODE: RESEARCH",
          "Synthesize only from the retrieved Knowledge OS evidence below. Do not invent external sources.",
          "Question: " + message,
          "Evidence:",
          JSON.stringify(evidence.map(({ id, mode, title, detail }) => ({ id, mode, title, detail }))),
        ].join("\n\n");
      } else if (capability) {
        runtimeMessage = [
          "ARKANA OPERATING MODE: " + capability.label.toUpperCase(),
          capability.summary,
          "Task: " + message,
        ].join("\n\n");
      }

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
          turn.id === assistantId
            ? {
                ...turn,
                content: result.reply,
                status: undefined,
                // An ordinary answer stays ordinary Markdown: no artifact is
                // fabricated for it.
                artifact: selectArtifact({}),
              }
            : turn,
        ),
      );

      // The reverse edge of the journey: the turn is recorded against the
      // project, so the thread survives a reload and a Lab outcome can return
      // to it. Both turns are appended, in order.
      await persistTurn("user", message);
      await persistTurn("arkana", result.reply);
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
    const message = parsed.rest.trim();
    if (!message || sending) return;
    setDraft("");
    await runTurn(message, activeCapability, turns);
  }

  const selectedProject = activeProject;

  const lifecycle: Lifecycle[] = [
    {
      stage: "understand",
      state: turns.length ? "done" : "pending",
      evidence: turns.length ? `${turns.length} turn(s) in this conversation` : undefined,
    },
    { stage: "propose", state: "pending", evidence: "No proposal has been raised in this conversation" },
    { stage: "authorize", state: "pending", evidence: "No grant is linked to this session" },
    { stage: "execute", state: "pending", evidence: "Nothing has been dispatched" },
    { stage: "verify", state: "pending" },
    { stage: "accept", state: "pending" },
    { stage: "release", state: "pending" },
  ];

  const inspectorContext: InspectorContext = {
    projectName: selectedProject?.name,
    projectId: selectedProject?.id,
    taskLabel: turns.length ? turns[turns.length - 1].content.slice(0, 80) : undefined,
    taskState: sending ? "running" : turns.length ? "idle" : undefined,
    sources: turns
      .flatMap((t) => t.evidence ?? [])
      .slice(0, 6)
      .map((e) => ({ label: `[${e.id}] ${e.title}`, detail: e.mode })),
    authorization: null,
    lifecycle,
    thread: activeProjectId
      ? {
          state: threadState,
          conversationId: thread?.id,
          note: threadNote,
        }
      : undefined,
  };

  const rail = (
    <div className="cg-rail-body">
      <div className="cg-rail-brand">
        <span className="cg-orb cg-sheen h-7 w-7" aria-hidden />
        <div className="min-w-0">
          <p className="font-display text-sm tracking-[0.16em] text-gold">Arkadia</p>
          <p className="font-mono text-[9px] uppercase tracking-widest text-white/35">Human-governed</p>
        </div>
      </div>

      <button
        type="button"
        className="cg-rail-action"
        data-testid="workspace-new-conversation"
        onClick={() => {
          setTurns([]);
          setError(null);
          inputRef.current?.focus();
        }}
      >
        New conversation
      </button>

      <nav className="cg-rail-nav" aria-label="Workspace destinations">
        <p className="cg-rail-label">Projects</p>
        {projects.state === "loading" ? (
          <p className="cg-rail-empty">Reading projects…</p>
        ) : projectRows.length === 0 ? (
          <p className="cg-rail-empty">
            {projects.state === "auth-required"
              ? "Sign in to see your projects."
              : projects.state === "ready"
                ? "No projects are visible to this identity."
                : "Projects could not be read."}
          </p>
        ) : (
          <ul className="cg-rail-list">
            {projectRows.slice(0, 8).map((project) => (
              <li key={project.id}>
                <button
                  type="button"
                  className={"cg-rail-item " + (activeProjectId === project.id ? "is-active" : "")}
                  aria-current={activeProjectId === project.id ? "true" : undefined}
                  data-testid={`workspace-project-${project.id}`}
                  onClick={() => selectProject(activeProjectId === project.id ? null : project.id)}
                >
                  <span className="min-w-0 truncate">{project.name}</span>
                  <span className="cg-rail-item-state">{project.status}</span>
                </button>
              </li>
            ))}
          </ul>
        )}
      </nav>

      <div className="cg-rail-foot">
        <p className="cg-rail-label">Capabilities</p>
        <ul className="cg-rail-caps">
          {CAPABILITIES.filter((c) => c.status === "verified")
            .slice(0, 6)
            .map((c) => (
              <li key={c.id} className="cg-rail-cap">
                <span className="font-mono text-[10px] text-teal/70">@{c.token}</span>
                <span className="min-w-0 truncate text-[11px] text-white/45">{c.label}</span>
              </li>
            ))}
        </ul>
      </div>
    </div>
  );

  const composer = (
    <div className="cg-composer-box">
      <label className="sr-only" htmlFor="workspace-composer">
        Message Arkana
      </label>
      <textarea
        id="workspace-composer"
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
        placeholder="Ask Arkana, or type @ to scope a capability…"
        data-testid="workspace-composer-input"
        className="cg-composer-input"
        disabled={sending}
      />
      <div className="cg-composer-toolbar">
        <div className="flex min-w-0 flex-wrap items-center gap-2">
          {activeCapability ? (
            <span className="cg-token-chip" data-testid="workspace-active-capability">
              @{activeCapability.token} · {activeCapability.label}
              {activeCapability.consequential ? " · consequential" : ""}
            </span>
          ) : (
            <span className="font-mono text-[10px] uppercase tracking-widest text-white/30">
              No capability scoped
            </span>
          )}
          {activeProjectId ? (
            <span className="cg-token-chip cg-token-chip-quiet" data-testid="workspace-project-chip">
              project · {selectedProject?.name ?? activeProjectId}
            </span>
          ) : null}
        </div>
        <div className="flex items-center gap-2">
          {sending ? (
            <button type="button" className="cg-btn cg-btn-danger" data-testid="workspace-stop" onClick={stop}>
              Stop
            </button>
          ) : null}
          <button
            type="button"
            className="cg-btn cg-btn-primary"
            data-testid="workspace-send"
            disabled={sending || !parsed.rest.trim()}
            onClick={() => void send()}
          >
            {sending ? "Working…" : "Send"}
          </button>
        </div>
      </div>
      <div className="cg-token-row" data-testid="workspace-token-row">
        {CAPABILITIES.map((c) => (
          <button
            key={c.id}
            type="button"
            className={"cg-token " + (c.status === "unverified" ? "is-unavailable" : "")}
            data-testid={`workspace-token-${c.token}`}
            title={c.status === "unverified" ? c.note : c.summary}
            disabled={c.status === "unverified"}
            onClick={() => {
              setDraft(`@${c.token} `);
              inputRef.current?.focus();
            }}
          >
            @{c.token}
          </button>
        ))}
      </div>
      {error ? (
        <p className="mt-2 text-xs text-gold/90" data-testid="workspace-error" role="alert">
          {error}
        </p>
      ) : null}
    </div>
  );

  return (
    <WorkspaceShell
      rail={rail}
      inspector={<Inspector context={inspectorContext} />}
      header={
        <div className="min-w-0">
          <p className="font-display text-sm tracking-[0.16em] text-gold">Workspace</p>
          <p className="font-mono text-[10px] uppercase tracking-widest text-emerald/70">
            {sending ? activity + "…" : "Arkana · Solariun canvas"}
          </p>
        </div>
      }
      composer={composer}
    >
      {turns.length === 0 ? (
        <div className="cg-welcome" data-testid="workspace-welcome">
          <span className="cg-orb cg-sheen h-14 w-14" aria-hidden />
          <h1 className="cg-welcome-title">What are we working on?</h1>
          <p className="cg-welcome-sub">
            One conversation reaches every capability. Arkana understands the intention, SolSpire
            coordinates the capability, and only authorized actions execute.
          </p>
          <div className="cg-welcome-grid">
            {CAPABILITIES.filter((c) => c.status === "verified")
              .slice(0, 6)
              .map((c) => (
                <button
                  key={c.id}
                  type="button"
                  className="cg-welcome-card"
                  data-testid={`workspace-start-${c.token}`}
                  onClick={() => {
                    setDraft(`@${c.token} `);
                    inputRef.current?.focus();
                  }}
                >
                  <span className="font-mono text-[10px] uppercase tracking-widest text-teal/75">
                    @{c.token}
                  </span>
                  <span className="mt-1 block text-left text-xs text-white/55">{c.summary}</span>
                </button>
              ))}
          </div>
          <p className="cg-welcome-note">
            Capability tokens are a proposed interaction convention. A token scopes the turn; it does
            not itself grant authority.
          </p>
        </div>
      ) : (
        <div className="cg-turns" data-testid="workspace-canvas">
          <ul className="cg-turn-list">
            {turns.map((turn) => (
              <li
                key={turn.id}
                className={"cg-turn " + (turn.role === "user" ? "cg-turn-user" : "cg-turn-assistant")}
              >
                <p className="cg-turn-meta">
                  {turn.role === "user" ? "you" : "arkana"}
                  {turn.capability ? " · @" + turn.capability.token : ""}
                  {turn.status ? " · " + turn.status : ""}
                </p>
                <div className="mt-2">
                  {turn.content ? (
                    <MarkdownViewer content={turn.content} compact presentationMode="denseConversation" />
                  ) : (
                    <p className="animate-pulse text-sm text-white/45">Working…</p>
                  )}
                </div>
                {turn.artifact ? <ArtifactView artifact={turn.artifact} /> : null}
                {turn.evidence?.length ? (
                  <section className="cg-evidence" data-testid="workspace-evidence">
                    <p className="cg-evidence-title">
                      Knowledge OS evidence · {turn.evidence.length} retrieved record(s)
                    </p>
                    <ol className="cg-evidence-list">
                      {turn.evidence.map((item) => (
                        <li key={item.id} className="cg-evidence-item">
                          <p className="text-xs text-white/80">
                            [{item.id}] {item.title}
                          </p>
                          <p className="mt-1 text-[11px] leading-relaxed text-white/45">
                            {item.mode}
                            {item.detail ? " · " + item.detail : ""}
                          </p>
                        </li>
                      ))}
                    </ol>
                  </section>
                ) : null}
              </li>
            ))}
          </ul>
          {sending ? (
            <p className="cg-working" data-testid="workspace-working">
              {activity}…
            </p>
          ) : null}
          <div ref={endRef} />
        </div>
      )}
    </WorkspaceShell>
  );
}
