/**
 * ScrollListenButton — read-aloud for any scroll/note content.
 *
 * Uses the SAME audio infrastructure as the Oracle Chat (audioManager +
 * voiceContext + audioCache) so the global SonataBar surfaces across every
 * surface: public scrolls, personal scrolls, the Encyclopedia, the Codex.
 *
 * One button: idle → generating → playing (toggle). Compact + themeable via
 * `accent`. Pass the raw markdown `text`; markdown is stripped before TTS.
 */
import React, { useState, useEffect, useCallback, useRef } from 'react';
import { Volume2, Loader2, Square } from 'lucide-react';
import { audioManager, AudioState } from '../lib/audioManager';
import { cacheGet, cachePut, audioCacheKey } from '../lib/audioCache';
import { voiceContext } from '../lib/voiceContext';
import { API_BASE } from '../lib/apiConfig';

// Mirror of OracleVoicePlayer.stripMarkdown so scroll text is speakable.
function stripMarkdown(s: string): string {
  s = s.replace(/```[\s\S]*?```/g, ' ');
  s = s.replace(/`([^`]+)`/g, '$1');
  s = s.replace(/<[^>]+>/g, ' ');
  s = s.replace(/!\[[^\]]*\]\([^)]+\)/g, '');
  s = s.replace(/\[([^\]]+)\]\([^)]+\)/g, '$1');
  s = s.replace(/^\s{0,3}#{1,6}\s+/gm, '');
  s = s.replace(/^\s*[-*+]\s+/gm, '');
  s = s.replace(/^\s*\d+\.\s+/gm, '');
  s = s.replace(/^\s*>\s?/gm, '');
  s = s.replace(/(\*\*|__)(.*?)\1/g, '$2');
  s = s.replace(/(\*|_)(.*?)\1/g, '$2');
  s = s.replace(/[⟐✦◆☥⟁◎⧫⚝•··⋯⋮⸮«»‹›「」『』【】〔〕〘〙〚〛〈〉《》≫◀▶]+/g, '');
  s = s.replace(/\|[^\n]*\|/g, (m) => {
    const cells = m.split('|').filter((_, i) => i > 0 && i < m.split('|').length - 1);
    return cells.join(' ');
  });
  s = s.replace(/^[\s|=-]+$/gm, '');
  s = s.replace(/\{[^{}]*\}/g, ' ');
  s = s.replace(/\[[^\[\]]*\]/g, ' ');
  s = s.replace(/https?:\/\/[^\s]+/g, ' ');
  s = s.replace(/\\[nrt\\*_`#[\]{}|]/g, ' ');
  s = s.replace(/[\x00-\x1F\x7F]/g, ' ');
  s = s.replace(/\$\$?[^$]+\$\$?/g, ' ');
  s = s.replace(/\n{3,}/g, '. ');
  s = s.replace(/\n{2,}/g, '. ');
  s = s.replace(/\s{2,}/g, ' ');
  s = s.replace(/[|\\]/g, ' ');
  s = s.replace(/\s{2,}/g, ' ');
  return s.trim();
}

interface Props {
  text: string;
  label?: string;
  accent?: string;
  voice?: string;
}

export default function ScrollListenButton({
  text,
  label = 'SCROLL TRANSMISSION',
  accent = '#00D4AA',
  voice = 'aria',
}: Props) {
  const [audioState, setAudioState] = useState<AudioState>(audioManager.getState());
  const [generating, setGenerating] = useState(false);
  const [active, setActive] = useState(false);
  const blobRef = useRef<string | null>(null);
  const textKeyRef = useRef<string>('');

  useEffect(() => audioManager.subscribe(setAudioState), []);
  useEffect(() => () => { if (blobRef.current) URL.revokeObjectURL(blobRef.current); }, []);

  // When this button's audio is what's loaded, reflect playing state.
  useEffect(() => {
    if (active && audioState.src === blobRef.current) {
      // still our source — keep active
    } else if (active && audioState.src && audioState.src !== blobRef.current) {
      // something else took over the singleton audio
      setActive(false);
    }
    if (!audioState.src) setActive(false);
  }, [audioState.src, active]);

  const stop = useCallback(() => {
    audioManager.stop();
    voiceContext.clear();
    setActive(false);
  }, []);

  const play = useCallback(async () => {
    const plain = stripMarkdown(text);
    if (!plain) return;

    // If currently playing our content, toggle to stop.
    if (active && audioState.src === blobRef.current) {
      if (audioState.playing) { audioManager.pause(); return; }
      audioManager.play();
      return;
    }

    textKeyRef.current = plain;
    voiceContext.set({ text: plain, label, voice });

    // Cache check
    const key = audioCacheKey(plain, `edge_${voice}`, 1);
    const cached = await cacheGet(key);
    if (cached) {
      const url = URL.createObjectURL(cached);
      if (blobRef.current) URL.revokeObjectURL(blobRef.current);
      blobRef.current = url;
      setActive(true);
      await audioManager.load(url);
      audioManager.play();
      return;
    }

    setGenerating(true);
    try {
      const res = await fetch(`${API_BASE}/api/tts`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ text: plain, speed: 1, voice }),
      });
      if (!res.ok) throw new Error(`TTS ${res.status}`);
      const blob = await res.blob();
      if (blob.size <= 500) throw new Error('empty audio');
      await cachePut(key, blob);
      const url = URL.createObjectURL(blob);
      if (blobRef.current) URL.revokeObjectURL(blobRef.current);
      blobRef.current = url;
      setActive(true);
      await audioManager.load(url);
      audioManager.play();
    } catch {
      // silent fail — button returns to idle
      setActive(false);
      voiceContext.clear();
    } finally {
      setGenerating(false);
    }
  }, [text, label, voice, active, audioState.src, audioState.playing]);

  const isPlaying = active && audioState.src === blobRef.current && audioState.playing;
  const isPaused = active && audioState.src === blobRef.current && !audioState.playing;

  return (
    <button
      onClick={() => (active ? (audioState.playing ? audioManager.pause() : audioManager.play()) : play())}
      disabled={generating}
      title={isPlaying ? 'Pause read-aloud' : isPaused ? 'Resume' : 'Read aloud'}
      style={{
        display: 'inline-flex',
        alignItems: 'center',
        gap: 5,
        padding: '4px 9px',
        background: active ? `${accent}18` : 'transparent',
        border: `1px solid ${active ? accent : 'rgba(255,255,255,0.08)'}`,
        borderRadius: 6,
        color: active ? accent : 'rgba(232,232,232,0.45)',
        fontFamily: 'monospace',
        fontSize: 9,
        letterSpacing: '0.1em',
        textTransform: 'uppercase',
        cursor: generating ? 'wait' : 'pointer',
        opacity: generating ? 0.7 : 1,
        transition: 'all 0.15s',
      }}
    >
      {generating
        ? <Loader2 size={11} style={{ animation: 'spin 1s linear infinite' }} />
        : active
          ? <Square size={11} />
          : <Volume2 size={11} />}
      {generating ? 'Generating…' : active ? (isPlaying ? 'Pause' : 'Resume') : 'Listen'}
      <style>{`@keyframes spin { from { transform: rotate(0deg); } to { transform: rotate(360deg); } }`}</style>
    </button>
  );
}
