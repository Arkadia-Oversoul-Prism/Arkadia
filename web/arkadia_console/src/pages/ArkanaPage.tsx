import { useEffect, useRef, useState } from "react";
import type { FormEvent, KeyboardEvent } from "react";
import { askArkana, type ArkanaMessage } from "../lib/arkana";
import type { ArkanaProvenance } from "../components/arkana/arkanaProvenanceContract";
import { ArkanaProvenancePanel } from "../components/arkana/ArkanaProvenancePanel";
import { ApiError } from "../lib/apiClient";
import { ArkanaThreadHistory } from "../components/arkana/ArkanaThreadHistory";
import { ReadAloud } from "../components/ReadAloud";

interface Turn extends ArkanaMessage {
  id: number;
  resonance?: number;
  provenance?: ArkanaProvenance;
}

const prompts = [
  { label: "Think something through", text: "Help me think through an idea…", symbol: "◌" },
  { label: "Understand a topic", text: "Explain a topic clearly…", symbol: "⌕" },
  { label: "Shape a piece of writing", text: "Help me shape a piece of writing…", symbol: "↗" },
];

export function ArkanaPage() {
  const [turns, setTurns] = useState<Turn[]>([]);
  const [draft, setDraft] = useState("");
  const [sending, setSending] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [historyOpen, setHistoryOpen] = useState(false);
  const [modeOpen, setModeOpen] = useState(false);
  const [mode, setMode] = useState("Auto");
  const nextId = useRef(0);
  const inputRef = useRef<HTMLTextAreaElement>(null);
  const endRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: "smooth", block: "end" });
  }, [turns, sending]);

  async function send(event?: FormEvent) {
    event?.preventDefault();
    const message = draft.trim();
    if (!message || sending) return;
    setDraft("");
    setError(null);
    setSending(true);
    const history: ArkanaMessage[] = turns.map(({ role, content }) => ({ role, content }));
    const userTurn: Turn = { id: nextId.current++, role: "user", content: message };
    setTurns((prev) => [...prev, userTurn]);
    try {
      const result = await askArkana(message, history);
      setTurns((prev) => [
        ...prev,
        { id: nextId.current++, role: "assistant", content: result.reply, resonance: result.resonance, provenance: result.provenance },
      ]);
    } catch (caught) {
      const detail = caught instanceof ApiError ? caught.message : "Arkana could not respond.";
      setError(detail);
      setTurns((prev) => prev.filter((turn) => turn.id !== userTurn.id));
      setDraft(message);
      requestAnimationFrame(() => inputRef.current?.focus());
    } finally {
      setSending(false);
    }
  }

  function onComposerKeyDown(event: KeyboardEvent<HTMLTextAreaElement>) {
    if (event.key === "Enter" && !event.shiftKey) {
      event.preventDefault();
      void send();
    }
  }

  return (
    <main className="arkana-shell" data-testid="arkana-page">
      <aside className={`arkana-rail ${historyOpen ? "arkana-rail-open" : ""}`} aria-label="Conversation navigation">
        <a className="arkana-brand" href="/arkana" aria-label="Arkana home">
          <span className="arkana-brand-mark" aria-hidden="true">a</span>
          <span>arkana</span>
        </a>
        <button
          type="button"
          onClick={() => { setTurns([]); setError(null); setHistoryOpen(false); }}
          className="arkana-new-button"
          data-testid="arkana-new-conversation"
        >
          <span aria-hidden="true">＋</span> New conversation
        </button>
        <div className="arkana-rail-divider" />
        <div className="arkana-history-heading">
          <span>Recent conversations</span>
          <button className="arkana-history-lock" type="button" title="Open conversation history" aria-label="Open conversation history" onClick={() => setHistoryOpen(true)}>⌕</button>
        </div>
        <div className="arkana-history-content">
          <ArkanaThreadHistory />
        </div>
        <div className="arkana-rail-footer">
          <span className="arkana-status-dot" />
          <span>Connected to Arkadia</span>
        </div>
      </aside>

      {historyOpen && <button className="arkana-mobile-scrim" aria-label="Close conversation navigation" onClick={() => setHistoryOpen(false)} />}

      <section className="arkana-main">
        <header className="arkana-topbar">
          <button className="arkana-mobile-menu" type="button" aria-label="Open conversation navigation" onClick={() => setHistoryOpen(true)}>☰</button>
          <div className="arkana-topbar-title">
            <span className="arkana-topbar-product">Arkana</span>
            <span className="arkana-topbar-context">Intelligence, in conversation</span>
          </div>
          <div className="arkana-topbar-actions">
            <span className="arkana-model-caption">Model</span>
            <div className="arkana-popover-wrap">
              <button type="button" className="arkana-model-button" aria-expanded={modeOpen} onClick={() => setModeOpen((open) => !open)}>
                <span className="arkana-model-spark">✳</span> {mode} <span className="arkana-chevron">⌄</span>
              </button>
              {modeOpen && (
                <div className="arkana-mode-popover" role="status">
                  <strong>Automatic selection</strong>
                  <p>Requests currently use Arkadia’s Gemini conversation path. Model routing is not yet available.</p>
                  <button type="button" onClick={() => { setMode("Auto"); setModeOpen(false); }}>Understood</button>
                </div>
              )}
            </div>
          </div>
        </header>

        <div className={`arkana-content ${turns.length ? "arkana-content-active" : "arkana-content-empty"}`}>
          {turns.length === 0 ? (
            <section className="arkana-welcome" aria-labelledby="arkana-welcome-title">
              <div className="arkana-orbit" aria-hidden="true"><span /><i /><b /></div>
              <p className="arkana-welcome-kicker">A clearer space to think</p>
              <h1 id="arkana-welcome-title">Where shall we begin?</h1>
              <p className="arkana-welcome-copy">Bring a question, an idea, or something you’re working through.</p>
              <div className="arkana-suggestions" aria-label="Start with an idea">
                {prompts.map((prompt) => (
                  <button key={prompt.label} type="button" onClick={() => { setDraft(prompt.text); inputRef.current?.focus(); }}>
                    <span className="arkana-suggestion-symbol" aria-hidden="true">{prompt.symbol}</span>
                    <span>{prompt.label}</span>
                  </button>
                ))}
              </div>
            </section>
          ) : (
            <section className="arkana-conversation" aria-label="Conversation">
              <ol className="arkana-turn-list" aria-live="polite" aria-relevant="additions">
                {turns.map((turn, index) => (
                  <li key={turn.id} className={`arkana-turn arkana-turn-${turn.role}`} data-testid={`arkana-turn-${turn.role}`}>
                    {turn.role === "assistant" && <span className="arkana-assistant-mark" aria-hidden="true">a</span>}
                    <div className="arkana-turn-body">
                      <p className="arkana-turn-label">{turn.role === "user" ? "You" : "Arkana"}</p>
                      <p className="arkana-turn-text">{turn.content}</p>
                      {turn.role === "assistant" && (
                        <div className="arkana-turn-tools">
                          <ReadAloud text={turn.content} label="Listen" testId={`arkana-listen-${index}`} />
                          {turn.resonance !== undefined && <span className="arkana-response-note">Response complete</span>}
                        </div>
                      )}
                      {turn.provenance && <ArkanaProvenancePanel provenance={turn.provenance} />}
                    </div>
                  </li>
                ))}
                {sending && (
                  <li className="arkana-turn arkana-turn-assistant" role="status" aria-label="Arkana is preparing a response">
                    <span className="arkana-assistant-mark" aria-hidden="true">a</span>
                    <div className="arkana-turn-body"><p className="arkana-turn-label">Arkana</p><p className="arkana-thinking"><span /><span /><span /></p></div>
                  </li>
                )}
              </ol>
              <div ref={endRef} />
            </section>
          )}

          {error && (
            <div className="arkana-error" role="alert">
              <span className="arkana-error-icon" aria-hidden="true">!</span>
              <div><strong>Your message wasn’t sent</strong><p>{error} Your draft is still here; you can try again.</p></div>
            </div>
          )}

          <form className="arkana-composer-wrap" onSubmit={(event) => void send(event)}>
            <div className="arkana-composer">
              <textarea
                ref={inputRef}
                value={draft}
                onChange={(event) => setDraft(event.target.value)}
                onKeyDown={onComposerKeyDown}
                rows={1}
                placeholder="Message Arkana"
                aria-label="Message Arkana"
                data-testid="arkana-input"
                className="arkana-composer-input"
              />
              <div className="arkana-composer-footer">
                <span className="arkana-composer-hint">Enter to send <span>·</span> Shift + Enter for a new line</span>
                <button type="submit" className="arkana-send-button" disabled={sending || !draft.trim()} data-testid="arkana-send" aria-label="Send message">
                  <span>Send</span><span aria-hidden="true">↑</span>
                </button>
              </div>
            </div>
            <p className="arkana-disclaimer">Arkana can make mistakes. Check important information.</p>
          </form>
        </div>
      </section>
    </main>
  );
}
