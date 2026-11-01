import { useEffect, useRef, useState } from "react";
import { streamArkana, type ArkanaMessage } from "../lib/arkana";
import type { ArkanaProvenance } from "../components/arkana/arkanaProvenanceContract";
import { ArkanaProvenancePanel } from "../components/arkana/ArkanaProvenancePanel";
import { ApiError, apiRequest } from "../lib/apiClient";
import { endpoints } from "../lib/endpoints";
import { isKnowledgeSearchData, recordDetail, recordTitle } from "./knowledge/knowledgeContracts";
import type { KnowledgeSearchData } from "./knowledge/knowledgeContracts";
import { ArkanaThreadHistory } from "../components/arkana/ArkanaThreadHistory";
import { ReadAloud } from "../components/ReadAloud";
import MarkdownViewer from "../components/arkana/MarkdownViewer";
import { ArkanaShell } from "../components/arkana/shell/ArkanaShell";

type ArkanaMode = "research" | "reason" | "create" | "plan";
interface ResearchEvidence { id: string; mode: string; title: string; detail: string; }
interface Turn extends ArkanaMessage {
  id: number;
  mode: ArkanaMode;
  resonance?: number;
  provenance?: ArkanaProvenance;
  status?: string;
  researchEvidence?: ResearchEvidence[];
}

const MODES: Array<{id: ArkanaMode; label: string; description: string; placeholder: string}> = [
  { id: "research", label: "Research", description: "Search and synthesize the accessible Knowledge OS corpus, with retrieved evidence kept visible.", placeholder: "What should Arkana research in the Knowledge OS?" },
  { id: "reason", label: "Reason", description: "Examine assumptions, compare alternatives, and explain the logic behind a question.", placeholder: "What should Arkana reason through?" },
  { id: "create", label: "Create", description: "Shape an idea into clear writing, structured content, or a practical artifact.", placeholder: "What should Arkana create?" },
  { id: "plan", label: "Plan", description: "Turn an objective into sequenced steps, dependencies, and measurable milestones.", placeholder: "What should Arkana plan?" },
];
const RESEARCH_SEARCH_MODES = ["semantic", "fulltext", "tag", "timeline", "project", "people", "reference"];
const MODE_GUIDANCE: Record<Exclude<ArkanaMode, "research">, string> = {
  reason: "Operate in REASON mode. Analyze the question, make assumptions explicit, distinguish evidence from inference, and explain trade-offs. Do not claim external research or tool execution.",
  create: "Operate in CREATE mode. Produce the requested artifact directly, with clear structure and usable language. Do not claim that an artifact was saved, published, or executed.",
  plan: "Operate in PLAN mode. Produce an actionable sequence with dependencies, decision points, and verification criteria. Distinguish recommendations from authorized execution.",
};

function buildResearchPrompt(question: string, evidence: ResearchEvidence[]): string {
  return [
    "ARKANA OPERATING MODE: RESEARCH",
    "Synthesize only from the retrieved Knowledge OS evidence below. Do not invent external sources.",
    "Question: " + question,
    "Evidence:",
    JSON.stringify(evidence.map(({id, mode, title, detail}) => ({id, mode, title, detail}))),
  ].join("\n\n");
}

function extractResearchEvidence(data: KnowledgeSearchData): ResearchEvidence[] {
  let sequence = 0;
  return Object.entries(data).flatMap(([mode, records]) => records.map((record) => {
    sequence += 1;
    const detail = recordDetail(record);
    return { id: "R" + sequence, mode, title: recordTitle(record, mode, sequence - 1), detail: detail.length > 1400 ? detail.slice(0, 1400) + "…" : detail };
  }));
}

function isAbortError(error: unknown): boolean {
  if (error instanceof DOMException && error.name === "AbortError") return true;
  if (error instanceof Error && error.name === "AbortError") return true;
  return false;
}

export function ArkanaPage() {
  const [turns, setTurns] = useState<Turn[]>([]);
  const [draft, setDraft] = useState("");
  const [activeMode, setActiveMode] = useState<ArkanaMode | null>(null);
  const [sending, setSending] = useState(false);
  const [activityLabel, setActivityLabel] = useState("Online");
  const [error, setError] = useState<string | null>(null);
  const [copiedId, setCopiedId] = useState<number | null>(null);
  const nextId = useRef(0);
  const inputRef = useRef<HTMLTextAreaElement>(null);
  const endRef = useRef<HTMLDivElement>(null);
  const abortRef = useRef<AbortController | null>(null);

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: "smooth", block: "end" });
  }, [turns, sending]);

  function activateMode(mode: ArkanaMode) {
    if (sending) return;
    setActiveMode(mode);
    setError(null);
    requestAnimationFrame(() => inputRef.current?.focus());
  }

  function stopGeneration() {
    abortRef.current?.abort();
    abortRef.current = null;
    setSending(false);
    setActivityLabel("Online");
  }

  async function copyTurn(turn: Turn) {
    if (!turn.content.trim()) return;
    try {
      await navigator.clipboard.writeText(turn.content);
      setCopiedId(turn.id);
      window.setTimeout(() => setCopiedId((id) => (id === turn.id ? null : id)), 1600);
    } catch {
      setError("Clipboard unavailable in this browser context.");
    }
  }

  /** Run a turn for an explicit user message (composer, regenerate). */
  async function runTurn(message: string, mode: ArkanaMode, priorTurns: Turn[]) {
    setError(null);
    setSending(true);
    setActivityLabel(mode === "research" ? "Searching Knowledge OS" : mode + " mode");

    const history: ArkanaMessage[] = priorTurns.map(({ role, content }) => ({ role, content }));
    const userTurn: Turn = { id: nextId.current++, role: "user", content: message, mode };
    const assistantId = nextId.current++;
    setTurns([...priorTurns, userTurn, { id: assistantId, role: "assistant", content: "", mode }]);

    const controller = new AbortController();
    abortRef.current = controller;

    try {
      let runtimeMessage: string;
      if (mode === "research") {
        const payload = await apiRequest<unknown>(endpoints.knowledgeSearch, {
          method: "POST",
          body: JSON.stringify({ query: message, modes: RESEARCH_SEARCH_MODES, top_k: 12 }),
          signal: controller.signal,
        });
        if (
          !isKnowledgeSearchData(payload) ||
          !Object.values(payload).every((records) =>
            records.every((record) => typeof record === "object" && record !== null && !Array.isArray(record)),
          )
        ) {
          throw new ApiError("The Knowledge OS search contract returned an unrecognised shape.", {
            kind: "UNKNOWN",
            path: endpoints.knowledgeSearch,
          });
        }
        const evidence = extractResearchEvidence(payload);
        if (evidence.length === 0) {
          setTurns((prev) =>
            prev.map((turn) =>
              turn.id === assistantId
                ? {
                    ...turn,
                    content:
                      "No records were returned by the accessible Knowledge OS corpus for this query. No research synthesis was generated.",
                    status: "No corpus records",
                    researchEvidence: [],
                  }
                : turn,
            ),
          );
          return;
        }
        setActivityLabel("Synthesising retrieved evidence");
        setTurns((prev) =>
          prev.map((turn) =>
            turn.id === assistantId
              ? { ...turn, status: "Retrieved Knowledge OS evidence", researchEvidence: evidence }
              : turn,
          ),
        );
        runtimeMessage = buildResearchPrompt(message, evidence);
      } else {
        runtimeMessage = [
          "ARKANA OPERATING MODE: " + mode.toUpperCase(),
          MODE_GUIDANCE[mode],
          "Task: " + message,
        ].join("\n\n");
      }

      const result = await streamArkana(
        runtimeMessage,
        history,
        {
          onStatus: (label) => setActivityLabel(label),
          onDelta: (delta) =>
            setTurns((prev) =>
              prev.map((turn) =>
                turn.id === assistantId ? { ...turn, content: turn.content + delta } : turn,
              ),
            ),
          signal: controller.signal,
        },
      );
      setTurns((prev) =>
        prev.map((turn) =>
          turn.id === assistantId
            ? {
                ...turn,
                content: result.reply,
                resonance: result.resonance,
                provenance: result.provenance,
                status: undefined,
              }
            : turn,
        ),
      );
    } catch (caught) {
      if (isAbortError(caught)) {
        setTurns((prev) =>
          prev.map((turn) =>
            turn.id === assistantId
              ? {
                  ...turn,
                  status: turn.content.trim() ? "Stopped" : "Cancelled",
                }
              : turn,
          ),
        );
        return;
      }
      const detail = caught instanceof ApiError ? caught.message : "Arkana could not complete this request.";
      setError(detail);
      setTurns((prev) => prev.filter((turn) => turn.id !== userTurn.id && turn.id !== assistantId));
      setDraft(message);
      requestAnimationFrame(() => inputRef.current?.focus());
    } finally {
      if (abortRef.current === controller) abortRef.current = null;
      setSending(false);
      setActivityLabel("Online");
      inputRef.current?.focus();
    }
  }

  async function send() {
    const message = draft.trim();
    const mode = activeMode;
    if (!message || !mode || sending) return;
    setDraft("");
    await runTurn(message, mode, turns);
  }

  /** Re-run the last user turn (Oracle canvas regenerate). */
  async function regenerate(assistantTurnId: number) {
    if (sending) return;
    const assistantIndex = turns.findIndex((t) => t.id === assistantTurnId && t.role === "assistant");
    if (assistantIndex <= 0) return;
    const userTurn = turns[assistantIndex - 1];
    if (!userTurn || userTurn.role !== "user") return;
    const prior = turns.slice(0, assistantIndex - 1);
    await runTurn(userTurn.content, userTurn.mode, prior);
  }

  const empty = turns.length === 0 && !sending;
  const selectedMode = MODES.find((mode) => mode.id === activeMode);
  const modeSwitcher = (
    <nav className="arkana-mode-switcher" aria-label="Arkana operating modes" data-testid="arkana-mode-switcher">
      {MODES.map((mode) => (
        <button
          key={mode.id}
          type="button"
          className={"arkana-mode-option " + (activeMode === mode.id ? "is-active" : "")}
          aria-pressed={activeMode === mode.id}
          data-testid={"arkana-mode-" + mode.id}
          disabled={sending}
          onClick={() => activateMode(mode.id)}
        >
          {mode.label}
        </button>
      ))}
    </nav>
  );

  const composer = (
    <div className="arkana-composer-box">
      <label className="sr-only" htmlFor="arkana-composer-input">
        Message Arkana
      </label>
      <textarea
        id="arkana-composer-input"
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
        placeholder={selectedMode?.placeholder ?? "Choose an operating mode above to begin…"}
        data-testid="arkana-input"
        className="arkana-composer-input"
        disabled={sending || !activeMode}
      />
      <div className="arkana-composer-toolbar">
        <div className="flex flex-wrap items-center gap-2">
          <span className="arkana-mode-chip" data-testid="arkana-active-mode">
            <span className="inline-block h-1.5 w-1.5 rounded-full bg-emerald/80" aria-hidden />
            {selectedMode ? selectedMode.label + " mode" : "Select mode"}
          </span>
          {activeMode === "research" ? (
            <span className="font-mono text-[10px] uppercase tracking-widest text-white/35">Knowledge OS corpus</span>
          ) : null}
          <span className="font-mono text-[10px] uppercase tracking-widest text-white/30">Shift+Enter for newline</span>
        </div>
        <div className="flex items-center gap-2">
          {sending ? (
            <button
              type="button"
              className="arkana-action-btn arkana-action-btn-danger"
              data-testid="arkana-stop"
              onClick={stopGeneration}
            >
              Stop
            </button>
          ) : null}
          <button
            type="button"
            className="arkana-send"
            data-testid="arkana-send"
            disabled={sending || !activeMode || !draft.trim()}
            onClick={() => void send()}
          >
            {sending ? "Sending…" : "Send"}
          </button>
        </div>
      </div>
      {error ? (
        <p className="mt-2 text-xs text-gold/90" data-testid="arkana-error" role="alert">
          {error}
        </p>
      ) : null}
    </div>
  );

  return (
    <ArkanaShell
      history={<ArkanaThreadHistory compact />}
      composer={composer}
      statusLabel={sending ? activityLabel : selectedMode ? selectedMode.label + " mode active" : "Choose a mode"}
    >
      {empty ? (
        <div className="arkana-empty" data-testid="arkana-empty">
          <div className="arkana-mark" aria-hidden>
            A
          </div>
          <h1 className="arkana-empty-title">
            {selectedMode ? selectedMode.label + " mode" : "What are we thinking?"}
          </h1>
          <p className="arkana-empty-sub">
            {selectedMode
              ? selectedMode.description
              : "Choose how Arkana should work. Selecting a mode activates its workspace; it does not submit a task."}
          </p>
          {modeSwitcher}
          {activeMode === "research" ? (
            <p className="mt-4 max-w-md text-center text-xs text-white/40">
              Research V1 searches the accessible Knowledge OS corpus. External web research is not enabled in this mode.
            </p>
          ) : null}
          {!activeMode ? (
            <div className="arkana-starters">
              {MODES.map((mode) => (
                <button
                  key={mode.id}
                  type="button"
                  className="arkana-starter"
                  data-testid={"arkana-select-" + mode.id}
                  onClick={() => activateMode(mode.id)}
                >
                  <span className="font-mono text-[10px] uppercase tracking-widest text-emerald/75">{mode.label}</span>
                  <span className="mt-1 block text-left text-xs text-white/55">{mode.description}</span>
                </button>
              ))}
            </div>
          ) : null}
        </div>
      ) : (
        <div className="arkana-thread" data-testid="arkana-thread">
          <div className="mb-4 flex flex-wrap items-center justify-between gap-2">
            {modeSwitcher}
          </div>
          <div className="arkana-thread-scroll">
            <ul className="flex flex-col gap-4">
              {turns.map((turn) => (
                <li
                  key={turn.id}
                  className={"arkana-bubble " + (turn.role === "user" ? "arkana-bubble-user" : "arkana-bubble-assistant")}
                >
                  <p className="font-mono text-[10px] uppercase tracking-widest text-white/35">
                    {turn.role === "user" ? "you" : "arkana"} · {turn.mode}
                    {turn.resonance !== undefined ? " · resonance " + turn.resonance : ""}
                    {turn.status ? " · " + turn.status : ""}
                  </p>
                  <div className="mt-2">
                    {turn.content ? (
                      <MarkdownViewer content={turn.content} compact presentationMode="denseConversation" />
                    ) : (
                      <p className="animate-pulse text-sm text-white/45">Working…</p>
                    )}
                  </div>
                  {turn.researchEvidence?.length ? (
                    <section className="arkana-research-evidence" data-testid="arkana-research-evidence">
                      <p className="mb-2 font-mono text-[10px] uppercase tracking-widest text-emerald/65">
                        Knowledge OS evidence · {turn.researchEvidence.length} retrieved record(s)
                      </p>
                      <ol className="flex flex-col gap-2">
                        {turn.researchEvidence.map((item) => (
                          <li key={item.id} className="border-l border-emerald/25 pl-3">
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
                  {turn.role === "assistant" && turn.content ? (
                    <div className="arkana-message-actions mt-3" data-testid={"arkana-actions-" + turn.id}>
                      <button
                        type="button"
                        className="arkana-action-btn"
                        data-testid={"arkana-copy-" + turn.id}
                        onClick={() => void copyTurn(turn)}
                      >
                        {copiedId === turn.id ? "Copied" : "Copy"}
                      </button>
                      <button
                        type="button"
                        className="arkana-action-btn"
                        data-testid={"arkana-regenerate-" + turn.id}
                        disabled={sending}
                        onClick={() => void regenerate(turn.id)}
                      >
                        Regenerate
                      </button>
                      <ReadAloud text={turn.content} label="Listen" testId={"arkana-listen-" + turn.id} />
                    </div>
                  ) : null}
                  {turn.provenance ? (
                    <div className="mt-3">
                      <ArkanaProvenancePanel provenance={turn.provenance} />
                    </div>
                  ) : null}
                </li>
              ))}
            </ul>
            {sending ? (
              <p
                className="mt-4 animate-pulse font-mono text-xs uppercase tracking-widest text-white/40"
                data-testid="arkana-synthesising"
              >
                {activityLabel}…
              </p>
            ) : null}
            <div ref={endRef} />
          </div>
        </div>
      )}
    </ArkanaShell>
  );
}
