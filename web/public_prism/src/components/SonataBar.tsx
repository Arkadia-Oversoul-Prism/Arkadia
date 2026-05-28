/**
 * SonataBar — persistent floating voice player bar.
 * Mounts once at the app root; survives page navigation.
 * Subscribes to audioManager (timing) + voiceContext (label/text).
 */
import React, { useState, useEffect, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Play, Pause, SkipBack, SkipForward, X, ChevronUp, ChevronDown } from 'lucide-react';
import { audioManager, AudioState } from '../lib/audioManager';
import { voiceContext, VoicePayload } from '../lib/voiceContext';

// ── Helpers ───────────────────────────────────────────────────────────────────
function fmt(s: number): string {
  if (!isFinite(s) || s <= 0) return '0:00';
  const m = Math.floor(s / 60);
  return `${m}:${Math.floor(s % 60).toString().padStart(2, '0')}`;
}

// ── Waveform ──────────────────────────────────────────────────────────────────
const Waveform: React.FC<{ playing: boolean }> = ({ playing }) => (
  <div style={{ display: 'flex', alignItems: 'center', gap: 2, height: 18, flexShrink: 0 }}>
    {[0, 0.12, 0.24, 0.36, 0.48].map((delay, i) => (
      <motion.div
        key={i}
        animate={playing
          ? { scaleY: [0.25, 1, 0.4, 0.85, 0.25] }
          : { scaleY: 0.2 }
        }
        transition={playing
          ? { duration: 0.85, repeat: Infinity, delay, ease: 'easeInOut' }
          : { duration: 0.25 }
        }
        style={{
          width: 3,
          height: 14,
          borderRadius: 2,
          background: '#00D4AA',
          transformOrigin: 'center',
          opacity: playing ? 0.9 : 0.3,
        }}
      />
    ))}
  </div>
);

// ── Seek slider ───────────────────────────────────────────────────────────────
const SeekBar: React.FC<{ state: AudioState }> = ({ state }) => {
  const pct = state.duration > 0 ? (state.currentTime / state.duration) * 100 : 0;
  return (
    <div style={{ position: 'relative', width: '100%', height: 3, borderRadius: 2, background: 'rgba(255,255,255,0.07)', cursor: 'pointer' }}>
      <div style={{
        position: 'absolute', left: 0, top: 0, bottom: 0,
        width: `${pct}%`, background: '#00D4AA', borderRadius: 2,
        transition: 'width 0.25s linear',
      }} />
      <input
        type="range" min={0} max={state.duration || 100}
        value={state.currentTime} step={0.5}
        onChange={e => audioManager.seek(parseFloat(e.target.value))}
        style={{ position: 'absolute', inset: 0, width: '100%', height: '100%', opacity: 0, cursor: 'pointer', margin: 0, padding: 0 }}
      />
    </div>
  );
};

// ── Control button ────────────────────────────────────────────────────────────
const Btn: React.FC<{
  onClick: () => void;
  title?: string;
  children: React.ReactNode;
  style?: React.CSSProperties;
}> = ({ onClick, title, children, style }) => (
  <button
    onClick={onClick}
    title={title}
    style={{
      display: 'flex', alignItems: 'center', justifyContent: 'center',
      background: 'none', border: 'none', cursor: 'pointer',
      color: 'rgba(232,232,232,0.65)', padding: '4px 6px', borderRadius: 6,
      transition: 'color 0.15s',
      ...style,
    }}
    onMouseEnter={e => (e.currentTarget.style.color = '#00D4AA')}
    onMouseLeave={e => (e.currentTarget.style.color = 'rgba(232,232,232,0.65)')}
  >
    {children}
  </button>
);

// ── SonataBar ─────────────────────────────────────────────────────────────────
const SonataBar: React.FC = () => {
  const [audioState, setAudioState] = useState<AudioState>(audioManager.getState());
  const [payload, setPayload]       = useState<VoicePayload | null>(voiceContext.get());
  const [expanded, setExpanded]     = useState(false);
  const [dismissed, setDismissed]   = useState(false);

  useEffect(() => audioManager.subscribe(setAudioState), []);
  useEffect(() => voiceContext.subscribe(setPayload), []);

  // Reset dismiss when new content loads
  const prevSrc = useRef<string | null>(null);
  useEffect(() => {
    if (audioState.src && audioState.src !== prevSrc.current) {
      prevSrc.current = audioState.src;
      setDismissed(false);
    }
  }, [audioState.src]);

  const visible = !dismissed && (audioState.playing || !!audioState.src) && !!payload;

  const handleDismiss = () => {
    audioManager.stop();
    setDismissed(true);
    setExpanded(false);
  };

  const label = payload?.label ?? 'ORACLE TRANSMISSION';
  const truncLabel = label.length > 40 ? label.slice(0, 38) + '…' : label;

  return (
    <AnimatePresence>
      {visible && (
        <motion.div
          key="sonata-bar"
          initial={{ y: 80, opacity: 0 }}
          animate={{ y: 0, opacity: 1 }}
          exit={{ y: 80, opacity: 0 }}
          transition={{ type: 'spring', stiffness: 340, damping: 34 }}
          style={{
            position: 'fixed',
            bottom: 0, left: 0, right: 0,
            zIndex: 300,
            background: 'rgba(8,8,13,0.97)',
            borderTop: '1px solid rgba(0,212,170,0.16)',
            backdropFilter: 'blur(24px)',
            WebkitBackdropFilter: 'blur(24px)',
            boxShadow: '0 -8px 40px rgba(0,0,0,0.5)',
          }}
        >
          {/* ── Seek bar (top edge) ── */}
          <div style={{ padding: '0 0 0 0' }}>
            <SeekBar state={audioState} />
          </div>

          {/* ── Main row ── */}
          <div style={{
            display: 'flex', alignItems: 'center', gap: 10,
            padding: '10px 16px 12px',
          }}>
            {/* Waveform */}
            <Waveform playing={audioState.playing} />

            {/* Label + times */}
            <div style={{ flex: 1, minWidth: 0 }}>
              <p style={{
                fontFamily: 'monospace', fontSize: 8.5,
                letterSpacing: '0.22em', textTransform: 'uppercase',
                color: 'rgba(0,212,170,0.55)', margin: '0 0 1px',
                whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis',
              }}>
                {truncLabel}
              </p>
              {expanded && audioState.duration > 0 && (
                <p style={{
                  fontFamily: 'monospace', fontSize: 8,
                  color: 'rgba(232,232,232,0.28)', margin: 0,
                }}>
                  {fmt(audioState.currentTime)} · {fmt(audioState.duration)}
                </p>
              )}
            </div>

            {/* Controls */}
            <div style={{ display: 'flex', alignItems: 'center', gap: 2, flexShrink: 0 }}>
              {/* ← 15s */}
              <Btn onClick={() => audioManager.skip(-15)} title="Back 15s">
                <SkipBack size={14} />
              </Btn>

              {/* Play / Pause */}
              <button
                onClick={() => audioState.playing ? audioManager.pause() : audioManager.play()}
                style={{
                  display: 'flex', alignItems: 'center', justifyContent: 'center',
                  width: 34, height: 34, borderRadius: '50%',
                  background: '#00D4AA', border: 'none', cursor: 'pointer',
                  color: '#000', flexShrink: 0,
                  boxShadow: '0 0 14px rgba(0,212,170,0.35)',
                  transition: 'transform 0.12s, box-shadow 0.12s',
                }}
                onMouseEnter={e => (e.currentTarget.style.transform = 'scale(1.08)')}
                onMouseLeave={e => (e.currentTarget.style.transform = 'scale(1)')}
                title={audioState.playing ? 'Pause' : 'Play'}
              >
                {audioState.playing
                  ? <Pause size={14} />
                  : <Play  size={14} />
                }
              </button>

              {/* +15s */}
              <Btn onClick={() => audioManager.skip(15)} title="Forward 15s">
                <SkipForward size={14} />
              </Btn>

              {/* Expand / collapse */}
              <Btn onClick={() => setExpanded(x => !x)} title={expanded ? 'Collapse' : 'Expand'}>
                {expanded ? <ChevronDown size={13} /> : <ChevronUp size={13} />}
              </Btn>

              {/* Dismiss */}
              <Btn onClick={handleDismiss} title="Close" style={{ marginLeft: 2 }}>
                <X size={13} />
              </Btn>
            </div>
          </div>
        </motion.div>
      )}
    </AnimatePresence>
  );
};

export default SonataBar;
