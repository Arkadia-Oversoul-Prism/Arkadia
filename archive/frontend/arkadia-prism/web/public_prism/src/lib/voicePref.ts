/**
 * voicePref — persistent global voice preference.
 *
 * One source of truth for "which voice should the Oracle speak in" across
 * OracleVoicePlayer, ScrollListenButton, SonataBar, ReasoMate, etc. Persists
 * to localStorage so a selection sticks across pages and reloads.
 *
 * The preference is a voice KEY (e.g. 'aetheria', 'aria'); the backend
 * kernel/tts.py maps it to the right ElevenLabs / Edge voice id.
 */

export type VoiceKey = string;

const STORAGE_KEY = 'arkadia_voice_pref';
const listeners = new Set<(v: VoiceKey) => void>();

let _current: VoiceKey = loadInitial();

function loadInitial(): VoiceKey {
  try {
    const v = localStorage.getItem(STORAGE_KEY);
    if (v && typeof v === 'string') return v;
  } catch { /* noop */ }
  return 'aria';
}

export const voicePref = {
  get(): VoiceKey { return _current; },

  set(v: VoiceKey) {
    if (!v || v === _current) return;
    _current = v;
    try { localStorage.setItem(STORAGE_KEY, v); } catch { /* noop */ }
    listeners.forEach(fn => fn(v));
  },

  subscribe(fn: (v: VoiceKey) => void): () => void {
    listeners.add(fn);
    fn(_current);
    return () => listeners.delete(fn);
  },
};
