/**
 * OracleVoicePlayer — inline audio player for an Oracle message.
 * Edge TTS neural voices (primary) · Web Speech API (fallback)
 * Publishes to voiceContext → SonataBar shows globally.
 */
import React, { useState, useEffect, useRef, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Play, Pause, Square, SkipBack, SkipForward,
  Volume2, Loader2, AlertCircle, ChevronDown, ChevronUp,
} from 'lucide-react';
import { audioManager, AudioState } from '../lib/audioManager';
import { cacheGet, cachePut, audioCacheKey } from '../lib/audioCache';
import { voiceContext } from '../lib/voiceContext';

// ─── constants ────────────────────────────────────────────────────────────────
const API_BASE   = import.meta.env.VITE_API_URL || '';
const SPEEDS     = [0.75, 1, 1.25, 1.5] as const;
const RESUME_KEY = 'arkadia_voice_resume';

// Available voices (matches backend kernel/tts.py VOICES)
const VOICE_OPTIONS = [
  { key: 'aria',        name: 'Aria',        desc: 'Warm, expressive female',    gender: 'F', accent: 'US' },
  { key: 'jenny',       name: 'Jenny',       desc: 'Natural, clear female',      gender: 'F', accent: 'US' },
  { key: 'sonia',       name: 'Sonia',       desc: 'Eloquent British female',    gender: 'F', accent: 'UK' },
  { key: 'christopher', name: 'Christopher', desc: 'Rich, warm American male',   gender: 'M', accent: 'US' },
  { key: 'george',      name: 'George',      desc: 'Authoritative British male', gender: 'M', accent: 'UK' },
  { key: 'ryan',        name: 'Ryan',        desc: 'Casual American male',       gender: 'M', accent: 'US' },
];

// ─── helpers ──────────────────────────────────────────────────────────────────
function fmt(s: number): string {
  if (!isFinite(s) || s <= 0) return '0:00';
  const m = Math.floor(s / 60);
  return `${m}:${Math.floor(s % 60).toString().padStart(2, '0')}`;
}

function stripMarkdown(s: string): string {
  return s
    .replace(/```[\s\S]*?```/g, ' ')
    .replace(/`([^`]+)`/g, '$1')
    .replace(/!\[[^\]]*\]\([^)]+\)/g, '')
    .replace(/\[([^\]]+)\]\([^)]+\)/g, '$1')
    .replace(/^\s{0,3}#{1,6}\s+/gm, '')
    .replace(/^\s*[-*+]\s+/gm, '')
    .replace(/^\s*\d+\.\s+/gm, '')
    .replace(/^\s*>\s?/gm, '')
    .replace(/(\*\*|__)(.*?)\1/g, '$2')
    .replace(/(\*|_)(.*?)\1/g, '$2')
    .replace(/[⟐✦◆☥⟁◎⧫⚝]/g, '')
    .replace(/\|[^\n]+\|/g, '')
    .replace(/\n{2,}/g, '. ')
    .replace(/\s+/g, ' ')
    .trim();
}

// ─── Web Speech fallback ──────────────────────────────────────────────────────
function pickBestVoice(voices: SpeechSynthesisVoice[]): SpeechSynthesisVoice | null {
  if (!voices.length) return null;
  const tests = [
    (v: SpeechSynthesisVoice) => /microsoft.*(aria|jenny|sonia)/i.test(v.name),
    (v: SpeechSynthesisVoice) => /google.*english.*female/i.test(v.name),
    (v: SpeechSynthesisVoice) => /google.*uk.*female/i.test(v.name),
    (v: SpeechSynthesisVoice) => /google.*us.*female/i.test(v.name),
    (v: SpeechSynthesisVoice) => /google.*english/i.test(v.name),
    (v: SpeechSynthesisVoice) => /microsoft.*online/i.test(v.name),
    (v: SpeechSynthesisVoice) => /samantha|karen|moira|fiona|serena/i.test(v.name),
    (v: SpeechSynthesisVoice) => v.lang.startsWith('en') && !v.localService,
    (v: SpeechSynthesisVoice) => v.lang.startsWith('en'),
  ];
  for (const t of tests) { const m = voices.find(t); if (m) return m; }
  return voices[0];
}

function getVoicesAsync(): Promise<SpeechSynthesisVoice[]> {
  if (!('speechSynthesis' in window)) return Promise.resolve([]);
  const immediate = window.speechSynthesis.getVoices();
  if (immediate.length) return Promise.resolve(immediate);
  return new Promise(resolve => {
    const timer = setTimeout(() => resolve(window.speechSynthesis.getVoices()), 1500);
    window.speechSynthesis.onvoiceschanged = () => { clearTimeout(timer); resolve(window.speechSynthesis.getVoices()); };
  });
}

// ─── Waveform animation ───────────────────────────────────────────────────────
const WaveformBars: React.FC<{ playing: boolean; accent: string }> = ({ playing, accent }) => (
  <div style={{ display: 'flex', alignItems: 'center', gap: 2, height: 20 }}>
    {[0, 0.15, 0.3, 0.45, 0.6].map((delay, i) => (
      <motion.div key={i}
        animate={playing ? { scaleY: [0.3, 1, 0.5, 0.9, 0.3] } : { scaleY: 0.25 }}
        transition={playing ? { duration: 0.9, repeat: Infinity, delay, ease: 'easeInOut' } : { duration: 0.2 }}
        style={{ width: 3, height: 16, borderRadius: 2, background: accent, transformOrigin: 'center', opacity: playing ? 0.85 : 0.3 }}
      />
    ))}
  </div>
);

// ─── Toast ────────────────────────────────────────────────────────────────────
const Toast: React.FC<{ msg: string; onDone: () => void }> = ({ msg, onDone }) => {
  useEffect(() => { const t = setTimeout(onDone, 3500); return () => clearTimeout(t); }, [onDone]);
  return (
    <motion.div initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: 8 }}
      style={{ position: 'fixed', bottom: 100, left: '50%', transform: 'translateX(-50%)', background: 'rgba(18,18,26,0.95)', border: '1px solid rgba(255,255,255,0.1)', borderRadius: 10, padding: '8px 16px', zIndex: 9999, fontFamily: 'monospace', fontSize: 11, color: 'rgba(232,232,232,0.7)', backdropFilter: 'blur(12px)', letterSpacing: '0.06em', display: 'flex', alignItems: 'center', gap: 7, boxShadow: '0 8px 32px rgba(0,0,0,0.5)' }}>
      <AlertCircle size={12} style={{ color: '#F97316', flexShrink: 0 }} />
      {msg}
    </motion.div>
  );
};

// ─── Control button ───────────────────────────────────────────────────────────
const ControlBtn: React.FC<{
  onClick: () => void; accent: string; title: string; disabled?: boolean; children: React.ReactNode;
}> = ({ onClick, accent, title, disabled, children }) => (
  <button onClick={onClick} disabled={disabled} title={title}
    style={{ display: 'flex', alignItems: 'center', gap: 2, padding: '5px 9px', background: 'transparent', border: `1px solid rgba(255,255,255,0.08)`, borderRadius: 7, color: disabled ? 'rgba(232,232,232,0.18)' : `${accent}88`, cursor: disabled ? 'not-allowed' : 'pointer', fontFamily: 'monospace', fontSize: 10, transition: 'all 0.15s' }}
    onMouseEnter={e => { if (!disabled) (e.currentTarget as HTMLButtonElement).style.borderColor = `${accent}44`; }}
    onMouseLeave={e => { (e.currentTarget as HTMLButtonElement).style.borderColor = 'rgba(255,255,255,0.08)'; }}
  >
    {children}
  </button>
);

// ─── Main component ───────────────────────────────────────────────────────────
interface OracleVoicePlayerProps {
  text:      string | null;
  accent?:   string;
  autoPlay?: boolean;
  label?:    string;
}

const OracleVoicePlayer: React.FC<OracleVoicePlayerProps> = ({
  text,
  accent    = '#00D4AA',
  autoPlay  = false,
  label     = 'ORACLE TRANSMISSION',
}) => {
  const [audioState, setAudioState]     = useState<AudioState>(audioManager.getState());
  const [speed, setSpeed]               = useState<number>(1);
  const [voice, setVoice]               = useState<string>('aria');
  const [showVoices, setShowVoices]     = useState(false);
  const [generating, setGenerating]     = useState(false);
  const [toast, setToast]               = useState<string | null>(null);
  const [collapsed, setCollapsed]       = useState(false);
  const [blobUrl, setBlobUrl]           = useState<string | null>(null);
  const [usedFallback, setUsedFallback] = useState(false);

  const utterRef   = useRef<SpeechSynthesisUtterance | null>(null);
  const [wsFallbackPlaying, setWsFallbackPlaying] = useState(false);
  const [wsFallbackPos, setWsFallbackPos]         = useState(0);
  const wsTimerRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const prevBlobRef = useRef<string | null>(null);

  useEffect(() => audioManager.subscribe(setAudioState), []);
  useEffect(() => { return () => { if (prevBlobRef.current) URL.revokeObjectURL(prevBlobRef.current); }; }, []);
  useEffect(() => { audioManager.setSpeed(speed); }, [speed]);

  // ── Generate via Edge TTS ──────────────────────────────────────────────────
  const generateEdge = useCallback(async (plain: string): Promise<Blob | null> => {
    try {
      const res = await fetch(`${API_BASE}/api/tts`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ text: plain, speed, voice }),
      });
      if (!res.ok) return null;
      const blob = await res.blob();
      return blob.size > 500 ? blob : null;
    } catch {
      return null;
    }
  }, [speed, voice]);

  // ── Load + play ────────────────────────────────────────────────────────────
  const loadAndPlay = useCallback(async (rawText: string, auto: boolean) => {
    if (!rawText.trim()) return;
    const plain = stripMarkdown(rawText);
    if (!plain) return;

    if ('speechSynthesis' in window) window.speechSynthesis.cancel();
    setWsFallbackPlaying(false);
    setUsedFallback(false);

    // Publish to global bar
    voiceContext.set({ text: plain, label, voice });

    // Check IndexedDB cache
    const key    = audioCacheKey(plain, `edge_${voice}`, speed);
    const cached = await cacheGet(key);
    if (cached) {
      const url = URL.createObjectURL(cached);
      if (prevBlobRef.current) URL.revokeObjectURL(prevBlobRef.current);
      prevBlobRef.current = url;
      setBlobUrl(url);
      await audioManager.load(url);
      if (auto || audioState.playing) audioManager.play();
      return;
    }

    // Generate via Edge TTS
    setGenerating(true);
    try {
      const blob = await generateEdge(plain);
      if (blob) {
        await cachePut(key, blob);
        const url = URL.createObjectURL(blob);
        if (prevBlobRef.current) URL.revokeObjectURL(prevBlobRef.current);
        prevBlobRef.current = url;
        setBlobUrl(url);
        await audioManager.load(url);
        if (auto) audioManager.play();
        try { localStorage.setItem(RESUME_KEY, JSON.stringify({ text: rawText.slice(0, 200), key })); } catch {}
        return;
      }
    } finally {
      setGenerating(false);
    }

    // Fallback: Web Speech API
    setUsedFallback(true);
    setToast('Edge TTS unavailable — using browser voice as fallback.');
    const voices = await getVoicesAsync();
    const wsVoice = pickBestVoice(voices);
    const utt = new SpeechSynthesisUtterance(plain);
    if (wsVoice) utt.voice = wsVoice;
    utt.rate   = speed * 0.88;
    utt.pitch  = 0.97;
    utt.volume = 1.0;
    utterRef.current = utt;

    let elapsed = 0;
    const estDur = Math.max(5, plain.length / 14 / speed);
    if (wsTimerRef.current) clearInterval(wsTimerRef.current);
    wsTimerRef.current = setInterval(() => {
      elapsed += 0.5;
      setWsFallbackPos(Math.min(elapsed / estDur, 0.99));
      if (elapsed >= estDur) clearInterval(wsTimerRef.current!);
    }, 500);

    utt.onstart = () => setWsFallbackPlaying(true);
    utt.onend   = () => { setWsFallbackPlaying(false); setWsFallbackPos(0); clearInterval(wsTimerRef.current!); };
    utt.onerror = () => { setWsFallbackPlaying(false); clearInterval(wsTimerRef.current!); };
    window.speechSynthesis.speak(utt);
  }, [speed, voice, label, audioState.playing, generateEdge]);

  // Auto-generate when text changes
  const prevTextRef = useRef<string | null>(null);
  useEffect(() => {
    if (!text || text === prevTextRef.current) return;
    prevTextRef.current = text;
    if (autoPlay) loadAndPlay(text, true);
  }, [text, autoPlay, loadAndPlay]);

  // ── Derived ───────────────────────────────────────────────────────────────
  const isPlaying   = usedFallback ? wsFallbackPlaying : audioState.playing;
  const progress    = usedFallback ? wsFallbackPos : audioState.duration > 0 ? audioState.currentTime / audioState.duration : 0;
  const currentTime = usedFallback ? wsFallbackPos * 120 : audioState.currentTime;
  const duration    = usedFallback ? 0 : audioState.duration;
  const isLoading   = generating || (!usedFallback && audioState.loading);

  const handlePlayPause = () => {
    if (!text) return;
    if (usedFallback) {
      if (wsFallbackPlaying) { window.speechSynthesis.pause(); setWsFallbackPlaying(false); }
      else if (utterRef.current) { window.speechSynthesis.resume(); setWsFallbackPlaying(true); }
      else loadAndPlay(text, true);
      return;
    }
    if (!blobUrl && !audioState.src) { loadAndPlay(text, true); return; }
    if (isPlaying) audioManager.pause(); else audioManager.play();
  };

  const handleStop = () => {
    if (usedFallback) { window.speechSynthesis.cancel(); setWsFallbackPlaying(false); setWsFallbackPos(0); return; }
    audioManager.stop();
  };

  const handleSeek = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (usedFallback) return;
    audioManager.seek(parseFloat(e.target.value));
  };

  if (!text) return null;

  const accentFaint  = accent === '#C9A84C' ? 'rgba(201,168,76,0.08)' : 'rgba(0,212,170,0.07)';
  const accentBorder = accent === '#C9A84C' ? 'rgba(201,168,76,0.2)'  : 'rgba(0,212,170,0.18)';

  return (
    <>
      <AnimatePresence>{toast && <Toast msg={toast} onDone={() => setToast(null)} />}</AnimatePresence>

      <motion.div
        initial={{ opacity: 0, y: 6 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: 6 }}
        transition={{ duration: 0.22 }}
        style={{ marginTop: 12, background: accentFaint, border: `1px solid ${accentBorder}`, borderRadius: 12, padding: collapsed ? '8px 14px' : '12px 14px', transition: 'padding 0.2s' }}
      >
        {/* Header row */}
        <div style={{ display: 'flex', alignItems: 'center', gap: 8, justifyContent: 'space-between' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
            <WaveformBars playing={isPlaying} accent={accent} />
            <span style={{ fontFamily: 'monospace', fontSize: 8.5, letterSpacing: '0.22em', textTransform: 'uppercase', color: `${accent}88` }}>
              ORACLE · {VOICE_OPTIONS.find(v => v.key === voice)?.name ?? 'ARIA'}
            </span>
            {usedFallback && (
              <span style={{ fontFamily: 'monospace', fontSize: 8, color: 'rgba(249,115,22,0.6)', letterSpacing: '0.1em' }}>
                · BROWSER VOICE
              </span>
            )}
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
            {isLoading && <Loader2 size={12} style={{ color: accent, animation: 'spin 1s linear infinite' }} />}
            <button onClick={() => setCollapsed(c => !c)}
              style={{ background: 'none', border: 'none', color: `${accent}66`, cursor: 'pointer', padding: 2, display: 'flex' }}>
              {collapsed ? <ChevronUp size={13} /> : <ChevronDown size={13} />}
            </button>
          </div>
        </div>

        {/* Expanded controls */}
        <AnimatePresence>
          {!collapsed && (
            <motion.div initial={{ opacity: 0, height: 0 }} animate={{ opacity: 1, height: 'auto' }} exit={{ opacity: 0, height: 0 }} transition={{ duration: 0.18 }} style={{ overflow: 'hidden' }}>

              {/* Progress bar */}
              <div style={{ marginTop: 10, display: 'flex', alignItems: 'center', gap: 8 }}>
                <span style={{ fontFamily: 'monospace', fontSize: 9, color: `${accent}66`, minWidth: 30 }}>{fmt(currentTime)}</span>
                <div style={{ flex: 1, position: 'relative', height: 4, borderRadius: 2, background: 'rgba(255,255,255,0.07)', cursor: usedFallback ? 'default' : 'pointer' }}>
                  <div style={{ position: 'absolute', left: 0, top: 0, bottom: 0, width: `${progress * 100}%`, background: accent, borderRadius: 2, transition: 'width 0.3s linear' }} />
                  {!usedFallback && (
                    <input type="range" min={0} max={duration || 100} value={audioState.currentTime} step={0.5} onChange={handleSeek}
                      style={{ position: 'absolute', inset: 0, width: '100%', height: '100%', opacity: 0, cursor: 'pointer', margin: 0, padding: 0 }} />
                  )}
                </div>
                <span style={{ fontFamily: 'monospace', fontSize: 9, color: `${accent}55`, minWidth: 30, textAlign: 'right' }}>{duration > 0 ? fmt(duration) : '--:--'}</span>
              </div>

              {/* Playback controls */}
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 8, marginTop: 10 }}>
                <ControlBtn onClick={() => !usedFallback && audioManager.skip(-10)} disabled={usedFallback} accent={accent} title="Back 10s">
                  <SkipBack size={13} /><span style={{ fontSize: 8, fontFamily: 'monospace' }}>10</span>
                </ControlBtn>

                <button onClick={handlePlayPause} disabled={isLoading && !isPlaying} title={isPlaying ? 'Pause' : 'Play'}
                  style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', width: 36, height: 36, borderRadius: '50%', background: accent, border: 'none', cursor: 'pointer', color: '#000', flexShrink: 0, boxShadow: `0 0 12px ${accent}44`, opacity: isLoading && !isPlaying ? 0.5 : 1, transition: 'opacity 0.15s, box-shadow 0.15s' }}>
                  {isLoading && !isPlaying ? <Loader2 size={15} style={{ animation: 'spin 1s linear infinite' }} /> : isPlaying ? <Pause size={15} /> : <Play size={15} />}
                </button>

                <ControlBtn onClick={handleStop} accent={accent} title="Stop"><Square size={12} /></ControlBtn>

                <ControlBtn onClick={() => !usedFallback && audioManager.skip(10)} disabled={usedFallback} accent={accent} title="Forward 10s">
                  <SkipForward size={13} /><span style={{ fontSize: 8, fontFamily: 'monospace' }}>10</span>
                </ControlBtn>
              </div>

              {/* Speed + voice selector + generate */}
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginTop: 10, gap: 8 }}>
                {/* Speed */}
                <div style={{ display: 'flex', gap: 4 }}>
                  {SPEEDS.map(s => (
                    <button key={s} onClick={() => setSpeed(s)}
                      style={{ padding: '3px 7px', borderRadius: 5, background: speed === s ? `${accent}22` : 'transparent', border: `1px solid ${speed === s ? accent : 'rgba(255,255,255,0.08)'}`, color: speed === s ? accent : 'rgba(232,232,232,0.35)', fontFamily: 'monospace', fontSize: 9, cursor: 'pointer', transition: 'all 0.15s' }}>
                      {s}×
                    </button>
                  ))}
                </div>

                {/* Generate */}
                <button onClick={() => text && loadAndPlay(text, true)} disabled={generating}
                  style={{ display: 'flex', alignItems: 'center', gap: 5, padding: '4px 10px', borderRadius: 7, background: 'transparent', border: `1px solid ${accentBorder}`, color: `${accent}99`, fontFamily: 'monospace', fontSize: 9, letterSpacing: '0.12em', textTransform: 'uppercase', cursor: generating ? 'not-allowed' : 'pointer', opacity: generating ? 0.5 : 1, transition: 'opacity 0.15s' }}>
                  <Volume2 size={10} />
                  {generating ? 'Generating…' : 'Listen'}
                </button>
              </div>

              {/* Voice selector */}
              <div style={{ marginTop: 10 }}>
                <button onClick={() => setShowVoices(v => !v)}
                  style={{ background: 'none', border: 'none', color: `${accent}55`, fontFamily: 'monospace', fontSize: 8, letterSpacing: '0.16em', textTransform: 'uppercase', cursor: 'pointer', padding: '2px 0' }}>
                  {showVoices ? '▲ Hide voices' : '▼ Change voice'}
                </button>
                <AnimatePresence>
                  {showVoices && (
                    <motion.div initial={{ opacity: 0, height: 0 }} animate={{ opacity: 1, height: 'auto' }} exit={{ opacity: 0, height: 0 }} transition={{ duration: 0.15 }} style={{ overflow: 'hidden' }}>
                      <div style={{ display: 'flex', flexWrap: 'wrap', gap: 5, marginTop: 8 }}>
                        {VOICE_OPTIONS.map(v => (
                          <button key={v.key}
                            onClick={() => { setVoice(v.key); setShowVoices(false); setBlobUrl(null); }}
                            style={{ padding: '4px 9px', borderRadius: 6, background: voice === v.key ? `${accent}18` : 'transparent', border: `1px solid ${voice === v.key ? accent : 'rgba(255,255,255,0.1)'}`, color: voice === v.key ? accent : 'rgba(232,232,232,0.45)', fontFamily: 'monospace', fontSize: 9, cursor: 'pointer', transition: 'all 0.15s' }}>
                            {v.name}
                            <span style={{ opacity: 0.45, fontSize: 8, marginLeft: 4 }}>{v.accent} {v.gender}</span>
                          </button>
                        ))}
                      </div>
                    </motion.div>
                  )}
                </AnimatePresence>
              </div>

            </motion.div>
          )}
        </AnimatePresence>
      </motion.div>

      <style>{`@keyframes spin { from { transform: rotate(0deg); } to { transform: rotate(360deg); } }`}</style>
    </>
  );
};

export default OracleVoicePlayer;
