/**
 * Arkana — conversation-first intelligence interface (A1 shell + A1.1 rail).
 *
 * Preserves the existing non-streaming resonance contract (`askArkana`).
 * Streaming is A2.
 */
import { useEffect, useRef, useState } from "react";
import { askArkana, type ArkanaMessage } from "../lib/arkana";
import type { ArkanaProvenance } from "../components/arkana/arkanaProvenanceContract";
import { ArkanaProvenancePanel } from "../components/arkana/ArkanaProvenancePanel";
import { ApiError } from "../lib/apiClient";
import { ArkanaThreadHistory } from "../components/arkana/ArkanaThreadHistory";
import { ReadAloud } from "../components/ReadAloud";
import { ArkanaShell } from "../components/arkana/shell/ArkanaShell";

interface Turn extends ArkanaMessage {
  resonance?: number;
  provenance?: ArkanaProvenance;
}

const SUGGESTIONS = [
  {
    label: "Research",
    prompt: "Investigate the current Arkadia substrate boundaries and summarise what is already production-verified.",
  },
  {
    label: "Reason",
    prompt: "Explain the difference between authorization, execution, and verification in the Arkadia architecture.",
  },
  {
    label: "Create",
    prompt: "Draft a concise product brief for Arkana as a conversation-first intelligence interface.",
  },
  {
    label: "Plan",
    prompt: "Propose the smallest next vertical slice after the Arkana conversational core.",
  },
] as const;

export function ArkanaPage() {
  const [turns, setTurns] = useState<Turn[]>([]);
  const [draft, setDraft] = useState("");
  const [sending, setSending] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const bottomRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ block: "end" });
  }, [turns, sending]);

  async function send(messageOverride?: string) {
    const message = (messageOverride ?? draft).trim();
    if (!message || sending) return;
    if (!messageOverride) setDraft("");
    setError(null);
    setSending(true);
    const history: ArkanaMessage[] = turns.map((t) => ({ role: t.role, content: t.content }));
    setTurns((prev) => [...prev, { role: "user", content: message }]);
    try {
      const result = await askArkana(message, history);
      setTurns((prev) => [
        ...prev,
        {
          role: "assistant",
          content: result.reply,
          resonance: result.resonance,
          provenance: result.provenance,
        },
      ]);
    } catch (caught) {
      const detail = caught instanceof ApiError ? caught.message : "Arkana could not respond.";
      setError(detail);
      setTurns((prev) => prev.slice(0, -1));
    } finally {
      setSending(false);
      inputRef.current?.focus();
    }
  }

  const empty = turns.length === 0 && !sending;

  const composer = (
    <div className="arkana-composer-box">
      <label className="sr-only" htmlFor="arkana-composer-input">
        Message Arkana
      </label>
      <textarea
        id="arkana-composer-input"
        ref={inputRef}
        value={draft}
        onChange={(e) => setDraft(e.target.value)}
        onKeyDown={(e) => {
          if (e.key === "Enter" && !e.shiftKey) {
            e.preventDefault();
            void send();
          }
        }}
        rows={2}
        placeholder="Ask anything, create something, or get something done…"
        data-testid="arkana-input"
        className="arkana-composer-input"
        disabled={sending}
      />
      <div className="arkana-composer-toolbar">
        <div className="flex flex-wrap items-center gap-2">
          <span className="arkana-mode-chip" title="Automatic model selection (Gemini via Oracle spine)">
            <span className="inline-block h-1.5 w-1.5 rounded-full bg-emerald/80" aria-hidden />
            Auto
          </span>
          <span className="hidden font-mono text-[10px] uppercase tracking-widest text-white/30 sm:inline">
            Shift+Enter for newline
          </span>
        </div>
        <button
          type="button"
          onClick={() => void send()}
          disabled={sending || !draft.trim()}
          data-testid="arkana-send"
          className="arkana-send"
        >
          {sending ? "Sending…" : "Send"}
        </button>
      </div>
      {error ? (
        <div className="rounded-lg border border-gold/30 bg-gold/5 px-3 py-2" data-testid="arkana-error">
          <p className="font-mono text-[10px] uppercase tracking-widest text-gold">Request failed</p>
          <p className="mt-1 text-sm text-white/65">{error}</p>
          <button
            type="button"
            className="mt-2 font-mono text-[10px] uppercase tracking-widest text-gold/90 underline-offset-2 hover:underline"
            onClick={() => setError(null)}
          >
            Dismiss
          </button>
        </div>
      ) : null}
    </div>
  );

  return (
    <ArkanaShell
      brand="Arkana"
      statusLabel={sending ? "Synthesising" : "Online"}
      sidebar={<ArkanaThreadHistory compact />}
      topTrailing={
        <span className="hidden font-mono text-[10px] uppercase tracking-widest text-white/35 sm:inline">
          Intelligence interface
        </span>
      }
      composer={composer}
    >
      {empty ? (
        <div className="arkana-empty" data-testid="arkana-empty">
          <div className="arkana-mark" aria-hidden>
            <span className="font-display text-lg tracking-[0.12em] text-emerald/90">A</span>
          </div>
          <h2 className="mt-5 font-display text-2xl tracking-[0.12em] text-white/90 sm:text-3xl">
            What are we thinking?
          </h2>
          <p className="mt-2 max-w-md text-sm text-white/50">
            Intelligence, creation, and synthesis in one place — powered by the Arkadia substrate.
          </p>
          <div className="mt-8 grid w-full max-w-xl grid-cols-1 gap-2 sm:grid-cols-2">
            {SUGGESTIONS.map((item) => (
              <button
                key={item.label}
                type="button"
                className="arkana-suggestion"
                data-testid={`arkana-suggestion-${item.label.toLowerCase()}`}
                disabled={sending}
                onClick={() => void send(item.prompt)}
              >
                <span className="font-mono text-[10px] uppercase tracking-widest text-emerald/75">{item.label}</span>
                <span className="mt-1 block text-xs leading-relaxed text-white/55">{item.prompt}</span>
              </button>
            ))}
          </div>
        </div>
      ) : (
        <div className="arkana-messages">
          <div className="arkana-messages-inner">
            <ul className="flex flex-col gap-4">
              {turns.map((turn, i) => (
                <li key={i} className={`arkana-bubble ${turn.role === "user" ? "arkana-bubble-user" : "arkana-bubble-assistant"}`}>
                  <p className="font-mono text-[10px] uppercase tracking-widest text-white/35">
                    {turn.role === "user" ? "you" : "arkana"}
                    {turn.resonance !== undefined ? ` · resonance ${turn.resonance}` : ""}
                  </p>
                  <p
                    className={`mt-2 whitespace-pre-wrap text-sm leading-relaxed ${
                      turn.role === "assistant" ? "text-emerald/90" : "text-white/85"
                    }`}
                  >
                    {turn.content}
                  </p>
                  {turn.role === "assistant" ? (
                    <div className="mt-3 flex flex-wrap items-center gap-3">
                      <ReadAloud text={turn.content} label="Listen" testId={`arkana-listen-${i}`} />
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
              <p className="mt-4 animate-pulse font-mono text-xs uppercase tracking-widest text-white/40" data-testid="arkana-synthesising">
                Synthesising…
              </p>
            ) : null}
            <div ref={bottomRef} />
          </div>
        </div>
      )}
    </ArkanaShell>
  );
}
