/**
 * voiceContext — broadcast what the Oracle is currently speaking.
 * SonataBar subscribes; OracleVoicePlayer publishes.
 */

export interface VoicePayload {
  text:  string;
  label: string;
  voice: string;
}

type Listener = (payload: VoicePayload | null) => void;

let _current: VoicePayload | null = null;
const _listeners = new Set<Listener>();

export const voiceContext = {
  /** Publish — called by OracleVoicePlayer when it starts loading audio. */
  set(payload: VoicePayload | null) {
    _current = payload;
    _listeners.forEach(fn => fn(_current));
  },

  /** Subscribe — returns unsubscribe function. */
  subscribe(fn: Listener): () => void {
    _listeners.add(fn);
    fn(_current);
    return () => _listeners.delete(fn);
  },

  get(): VoicePayload | null {
    return _current;
  },

  clear() {
    voiceContext.set(null);
  },
};
