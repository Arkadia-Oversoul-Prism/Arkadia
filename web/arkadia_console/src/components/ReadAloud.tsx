/**
 * ReadAloud — listen to any scroll, note, or reply content.
 *
 * Recovers the archived Prism's read-aloud capability
 * (`ScrollListenButton.tsx`, `OracleVoicePlayer.tsx`, `SonataBar.tsx` — 3
 * components, all reaching `POST /api/tts`) on top of the current console. The
 * backend contract is live and anonymously readable; the console simply never
 * called it.
 *
 * What this deliberately does **not** do:
 *
 *  - It does not offer a voice the active engine cannot deliver. `aetheria` is
 *    declared `requires_elevenlabs` by `kernel/tts.py`; without a key the
 *    backend substitutes the Edge voice. The option is shown as locked with the
 *    reason, rather than presented as honoured.
 *  - It does not report success from an empty or failed synthesis. A failure is
 *    surfaced with the backend's own detail.
 *  - It does not autoplay. Synthesis is a real backend call; it happens on an
 *    explicit user action.
 */
import { useCallback, useEffect, useRef, useState } from "react";
import { Panel } from "./ui";
import { ApiError } from "../lib/apiClient";
import {
  fetchTtsStatus,
  fetchVoiceCatalog,
  synthesiseSpeech,
  speakableText,
  voiceIsDeliverable,
  type TtsStatus,
  type VoiceDef,
} from "../lib/voice";

type PlayerState = "idle" | "synthesising" | "playing" | "error";

const PREF_KEY = "arkadia_voice_pref";

/** The persisted voice choice, shared by every read-aloud control. */
function readVoicePref(fallback: string): string {
  if (typeof window === "undefined") return fallback;
  return window.localStorage.getItem(PREF_KEY) || fallback;
}

function writeVoicePref(voice: string): void {
  if (typeof window === "undefined") return;
  window.localStorage.setItem(PREF_KEY, voice);
}

export function ReadAloud({
  text,
  label = "Read aloud",
  testId = "read-aloud",
}: {
  text: string;
  label?: string;
  testId?: string;
}) {
  const [state, setState] = useState<PlayerState>("idle");
  const [error, setError] = useState<string | null>(null);
  const [engine, setEngine] = useState<string | null>(null);
  const [catalog, setCatalog] = useState<Record<string, VoiceDef>>({});
  const [status, setStatus] = useState<TtsStatus | null>(null);
  const [voice, setVoice] = useState<string>(() => readVoicePref("aria"));
  const [showVoices, setShowVoices] = useState(false);
  const audioRef = useRef<HTMLAudioElement | null>(null);
  const urlRef = useRef<string | null>(null);

  // Read the two read-only voice contracts once. Both are anonymous-readable;
  // if either is unavailable the control still works with the backend default
  // rather than inventing a catalogue.
  useEffect(() => {
    const controller = new AbortController();
    Promise.all([fetchVoiceCatalog(controller.signal), fetchTtsStatus(controller.signal)])
      .then(([cat, st]) => {
        setCatalog(cat.voices ?? {});
        setStatus(st);
        setVoice((current) => (current in (cat.voices ?? {}) ? current : cat.default || "aria"));
      })
      .catch(() => {
        /* The catalogue is an enhancement; synthesis reports its own failures. */
      });
    return () => controller.abort();
  }, []);

  const release = useCallback(() => {
    if (urlRef.current) {
      URL.revokeObjectURL(urlRef.current);
      urlRef.current = null;
    }
    if (audioRef.current) {
      audioRef.current.pause();
      audioRef.current = null;
    }
  }, []);

  // Object URLs and the audio element outlive the component otherwise.
  useEffect(() => release, [release]);

  const stop = useCallback(() => {
    release();
    setState("idle");
  }, [release]);

  const play = useCallback(async () => {
    const spoken = speakableText(text);
    if (!spoken) {
      setError("There is no speakable text in this content.");
      setState("error");
      return;
    }
    setError(null);
    setState("synthesising");
    try {
      const { blob, engine: usedEngine } = await synthesiseSpeech(spoken, voice);
      const url = URL.createObjectURL(blob);
      urlRef.current = url;
      setEngine(usedEngine);
      const audio = new Audio(url);
      audioRef.current = audio;
      audio.onended = () => {
        release();
        setState("idle");
      };
      audio.onerror = () => {
        release();
        setError("The audio the backend returned could not be played.");
        setState("error");
      };
      await audio.play();
      setState("playing");
    } catch (caught) {
      release();
      setError(caught instanceof ApiError ? caught.message : "Read aloud failed.");
      setState("error");
    }
  }, [release, text, voice]);

  const selected = catalog[voice];
  const deliverable = voiceIsDeliverable(selected, status);
  const voiceEntries = Object.entries(catalog);

  return (
    <div data-testid={testId} className="mt-3">
      <div className="flex flex-wrap items-center gap-2">
        <button
          type="button"
          onClick={() => (state === "playing" ? stop() : void play())}
          disabled={state === "synthesising"}
          data-testid={`${testId}-button`}
          aria-pressed={state === "playing"}
          className="rounded border border-azure/40 px-3 py-1.5 font-mono text-[11px] uppercase tracking-widest text-azure disabled:opacity-40"
        >
          {state === "playing" ? "Stop" : state === "synthesising" ? "Synthesising…" : label}
        </button>

        {voiceEntries.length > 0 && (
          <button
            type="button"
            onClick={() => setShowVoices((v) => !v)}
            aria-expanded={showVoices}
            data-testid={`${testId}-voice-toggle`}
            className="rounded border border-white/15 px-2 py-1 font-mono text-[10px] uppercase tracking-widest text-white/50 hover:text-white/80"
          >
            {selected?.name ?? voice}
            {!deliverable && " 🔒"}
          </button>
        )}

        {engine && (
          <span className="font-mono text-[10px] uppercase tracking-widest text-white/35" data-testid={`${testId}-engine`}>
            engine · {engine}
          </span>
        )}
      </div>

      {showVoices && (
        <ul className="mt-2 flex flex-wrap gap-2" data-testid={`${testId}-voices`}>
          {voiceEntries.map(([key, def]) => {
            const usable = voiceIsDeliverable(def, status);
            return (
              <li key={key}>
                <button
                  type="button"
                  disabled={!usable}
                  onClick={() => {
                    setVoice(key);
                    writeVoicePref(key);
                    setShowVoices(false);
                  }}
                  aria-pressed={key === voice}
                  data-testid={`${testId}-voice-${key}`}
                  className={`rounded px-2 py-1 font-mono text-[10px] uppercase tracking-widest ${
                    usable
                      ? "border border-white/15 text-white/60 hover:text-white/90"
                      : "cursor-not-allowed border border-dashed border-white/20 text-white/30"
                  }`}
                >
                  {def.name}
                  {!usable && " 🔒"}
                </button>
              </li>
            );
          })}
        </ul>
      )}

      {showVoices && !deliverable && selected && (
        <p className="mt-2 text-xs text-white/40" data-testid={`${testId}-locked-reason`}>
          {selected.name} is delivered by the ElevenLabs engine only. This deployment has no
          ElevenLabs key configured, so the request would fall back to a different voice — the
          option is locked rather than substituted silently.
        </p>
      )}

      {error && (
        <Panel className="mt-2 border-gold/30">
          <p className="font-mono text-[11px] uppercase tracking-widest text-gold">Read aloud unavailable</p>
          <p className="mt-1 text-sm text-white/60" data-testid={`${testId}-error`}>{error}</p>
        </Panel>
      )}
    </div>
  );
}
