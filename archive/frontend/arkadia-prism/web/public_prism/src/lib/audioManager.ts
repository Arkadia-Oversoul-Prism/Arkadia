/**
 * Singleton audio manager — survives React re-renders and page navigation
 * within the SPA. One Audio element, one source at a time.
 */

export type AudioState = {
  playing: boolean;
  currentTime: number;
  duration: number;
  loading: boolean;
  error: string | null;
  src: string | null;
};

type Listener = (state: AudioState) => void;

const el: HTMLAudioElement = (() => {
  const a = document.createElement('audio');
  a.preload = 'auto';
  return a;
})();

let _src: string | null    = null;
let _loading               = false;
let _error: string | null  = null;
const _listeners           = new Set<Listener>();

function getState(): AudioState {
  return {
    playing:     !el.paused,
    currentTime: el.currentTime,
    duration:    isFinite(el.duration) ? el.duration : 0,
    loading:     _loading,
    error:       _error,
    src:         _src,
  };
}

function notify() {
  const s = getState();
  _listeners.forEach(fn => fn(s));
}

el.addEventListener('timeupdate',  notify);
el.addEventListener('durationchange', notify);
el.addEventListener('ended',       notify);
el.addEventListener('pause',       notify);
el.addEventListener('play',        notify);
el.addEventListener('error',       () => { _error = 'Playback error'; _loading = false; notify(); });
el.addEventListener('canplay',     () => { _loading = false; notify(); });
el.addEventListener('waiting',     () => { _loading = true;  notify(); });

export const audioManager = {
  subscribe(fn: Listener) {
    _listeners.add(fn);
    fn(getState());
    return () => _listeners.delete(fn);
  },

  async load(blobUrl: string) {
    if (_src === blobUrl) return;
    el.pause();
    _src     = blobUrl;
    _loading = true;
    _error   = null;
    el.src   = blobUrl;
    el.load();
    notify();
  },

  play() {
    if (!_src) return;
    el.play().catch(() => {});
  },

  pause() { el.pause(); },

  stop() {
    el.pause();
    el.currentTime = 0;
    notify();
  },

  seek(t: number) {
    el.currentTime = Math.max(0, Math.min(t, el.duration || 0));
    notify();
  },

  skip(delta: number) {
    audioManager.seek(el.currentTime + delta);
  },

  setSpeed(rate: number) {
    el.playbackRate = rate;
    notify();
  },

  setVolume(v: number) {
    el.volume = Math.max(0, Math.min(1, v));
    notify();
  },

  getState,
};
