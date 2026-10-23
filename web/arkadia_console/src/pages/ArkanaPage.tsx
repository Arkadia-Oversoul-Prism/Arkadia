import { useState } from "react";
import { Page, Panel } from "../components/ui";
import { askArkana, type ArkanaMessage } from "../lib/arkana";
import { ApiError } from "../lib/apiClient";
import { ArkanaThreadHistory } from "../components/arkana/ArkanaThreadHistory";
import { ReadAloud } from "../components/ReadAloud";

interface Turn extends ArkanaMessage {
  resonance?: number;
}

export function ArkanaPage() {
  const [turns, setTurns] = useState<Turn[]>([]);
  const [draft, setDraft] = useState("");
  const [sending, setSending] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function send() {
    const message = draft.trim();
    if (!message || sending) return;
    setDraft("");
    setError(null);
    setSending(true);
    const history: ArkanaMessage[] = turns.map((t) => ({ role: t.role, content: t.content }));
    setTurns((prev) => [...prev, { role: "user", content: message }]);
    try {
      const result = await askArkana(message, history);
      setTurns((prev) => [...prev, { role: "assistant", content: result.reply, resonance: result.resonance }]);
    } catch (caught) {
      // A real failure is shown as a real failure — never a fabricated reply.
      const detail = caught instanceof ApiError ? caught.message : "Arkana could not respond.";
      setError(detail);
      setTurns((prev) => prev.slice(0, -1));
    } finally {
      setSending(false);
    }
  }

  return (
    <Page title="Arkana" subtitle="Conversational intelligence and synthesis over the shared Oracle spine.">
      <ArkanaThreadHistory />

      <Panel className="mb-4 min-h-[20rem]">
        {turns.length === 0 && <p className="text-sm text-white/40">No messages yet. Ask Arkana a question to begin.</p>}
        <ul className="flex flex-col gap-4">
          {turns.map((turn, i) => (
            <li key={i} className="whitespace-pre-wrap text-sm">
              <p className="font-mono text-[10px] uppercase tracking-widest text-white/35">
                {turn.role === "user" ? "you" : "arkana"}
                {turn.resonance !== undefined && ` · resonance ${turn.resonance}`}
              </p>
              <p className={turn.role === "assistant" ? "text-emerald/90" : "text-white/85"}>{turn.content}</p>
              {turn.role === "assistant" && (
                <ReadAloud
                  text={turn.content}
                  label="Listen"
                  testId={`arkana-listen-${i}`}
                />
              )}
            </li>
          ))}
        </ul>
        {sending && <p className="mt-4 animate-pulse font-mono text-xs uppercase tracking-widest text-white/40">Synthesising…</p>}
      </Panel>

      {error && (
        <Panel className="mb-4 border-gold/30">
          <p className="font-mono text-[11px] uppercase tracking-widest text-gold">Request failed</p>
          <p className="mt-1 text-sm text-white/60">{error}</p>
        </Panel>
      )}

      <div className="flex gap-2">
        <textarea
          value={draft}
          onChange={(e) => setDraft(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === "Enter" && !e.shiftKey) {
              e.preventDefault();
              void send();
            }
          }}
          rows={3}
          placeholder="Ask Arkana…"
          data-testid="arkana-input"
          className="min-w-0 flex-1 rounded-lg border border-line bg-panel/60 p-3 text-sm text-white outline-none focus:border-emerald/50"
        />
        <button
          onClick={() => void send()}
          disabled={sending || !draft.trim()}
          data-testid="arkana-send"
          className="rounded-lg border border-emerald/50 px-5 font-mono text-[11px] uppercase tracking-widest text-emerald disabled:opacity-40"
        >
          Send
        </button>
      </div>
    </Page>
  );
}
