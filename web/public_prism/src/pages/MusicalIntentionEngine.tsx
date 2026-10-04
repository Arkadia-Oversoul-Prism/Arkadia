import React, { useEffect, useMemo, useRef, useState } from 'react';

type Capture = {
  id: string;
  kind: 'original' | 'derived';
  label: string;
  note: string;
  hz: number;
  parentId?: string;
  transformation?: string;
};

const seed: Capture[] = [
  { id: 'capture-001', kind: 'original', label: 'CAPTURE 001', note: 'A4', hz: 440 },
  { id: 'capture-001-derivative', kind: 'derived', label: 'CAPTURE 001 · OCTAVE UP', note: 'A5', hz: 880, parentId: 'capture-001', transformation: 'octave_up' },
];

const panel: React.CSSProperties = {
  background: 'rgba(14,17,32,0.72)',
  border: '1px solid rgba(201,168,76,0.16)',
  borderRadius: 14,
  padding: 18,
};

export default function MusicalIntentionEngine() {
  const [captures, setCaptures] = useState<Capture[]>(seed);
  const [selected, setSelected] = useState(seed[0]);
  const [playing, setPlaying] = useState<string | null>(null);
  const [repeat, setRepeat] = useState<string | null>(null);
  const [paused, setPaused] = useState<string | null>(null);
  const timer = useRef<number | null>(null);
  const selectedJson = useMemo(() => JSON.stringify(selected, null, 2), [selected]);

  useEffect(() => () => { if (timer.current) window.clearTimeout(timer.current); }, []);

  const stopAll = () => {
    if (timer.current) window.clearTimeout(timer.current);
    timer.current = null;
    setPlaying(null);
    setPaused(null);
  };

  const play = (capture: Capture, preserveRepeat = false) => {
    const armed = repeat;
    stopAll();
    if (preserveRepeat && armed) setRepeat(armed); else if (!preserveRepeat) setRepeat(null);

    const AudioCtx = window.AudioContext || (window as typeof window & { webkitAudioContext?: typeof AudioContext }).webkitAudioContext;
    if (AudioCtx) {
      const ctx = new AudioCtx();
      const osc = ctx.createOscillator();
      const gain = ctx.createGain();
      osc.frequency.value = capture.hz;
      osc.type = 'sine';
      gain.gain.value = 0.035;
      osc.connect(gain).connect(ctx.destination);
      osc.start();
      osc.stop(ctx.currentTime + 0.35);
      window.setTimeout(() => void ctx.close(), 500);
    }

    setSelected(capture);
    setPlaying(capture.id);
    setPaused(null);
    timer.current = window.setTimeout(() => {
      setPlaying(current => current === capture.id ? null : current);
      if (repeat === capture.id) play(capture, true);
    }, 420);
  };

  const pause = (capture: Capture) => {
    if (playing === capture.id) {
      if (timer.current) window.clearTimeout(timer.current);
      setPlaying(null);
      setPaused(capture.id);
    } else if (paused === capture.id) {
      play(capture);
    }
  };

  const toggleRepeat = (capture: Capture) => {
    const next = repeat === capture.id ? null : capture.id;
    setRepeat(next);
    if (next && playing !== capture.id) play(capture, true);
  };

  const octaveUp = (source: Capture) => {
    if (source.kind === 'derived') return;
    const derivative: Capture = {
      id: crypto.randomUUID(),
      kind: 'derived',
      label: source.label + ' · OCTAVE UP',
      note: source.note === 'A4' ? 'A5' : source.note,
      hz: source.hz * 2,
      parentId: source.id,
      transformation: 'octave_up',
    };
    setCaptures(items => [...items, derivative]);
    setSelected(derivative);
  };

  const addCapture = () => {
    const id = crypto.randomUUID();
    const next: Capture = {
      id,
      kind: 'original',
      label: 'CAPTURE ' + String(captures.filter(c => c.kind === 'original').length + 1).padStart(3, '0'),
      note: 'A4',
      hz: 440,
    };
    setCaptures(items => [...items, next]);
    setSelected(next);
  };

  const button: React.CSSProperties = {
    border: '1px solid rgba(232,232,232,0.12)',
    background: 'rgba(255,255,255,0.035)',
    color: 'rgba(232,232,232,0.78)',
    borderRadius: 9,
    padding: '9px 12px',
    fontSize: 9,
    letterSpacing: '0.16em',
    textTransform: 'uppercase',
    cursor: 'pointer',
  };

  return (
    <div style={{ minHeight: 'calc(100vh - 57px)', padding: '30px 16px 70px', color: '#E8E8E8' }}>
      <div style={{ maxWidth: 1100, margin: '0 auto' }}>
        <div style={{ ...panel, marginBottom: 14, display: 'flex', justifyContent: 'space-between', gap: 20, alignItems: 'flex-start', flexWrap: 'wrap' }}>
          <div>
            <div style={{ fontSize: 9, letterSpacing: '0.28em', color: '#00D4AA', textTransform: 'uppercase' }}>MUSICAL INTENTION ENGINE · PRISM UI</div>
            <h1 style={{ fontFamily: 'serif', fontSize: 34, fontWeight: 400, letterSpacing: '0.04em', margin: '10px 0 8px', color: '#C9A84C' }}>Make the sound rememberable.</h1>
            <p style={{ margin: 0, maxWidth: 680, color: 'rgba(232,232,232,0.58)', fontSize: 13, lineHeight: 1.6 }}>
              Gate 05 visual proving ground. Capture an idea, change it, compare the result, then keep or revise. The native Android implementation remains the execution authority.
            </p>
          </div>
          <div style={{ padding: '10px 12px', border: '1px solid rgba(0,212,170,0.24)', borderRadius: 10, color: '#00D4AA', fontSize: 9, letterSpacing: '0.16em', textTransform: 'uppercase' }}>
            GATE 05 · CHANGE LOOP
          </div>
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit,minmax(300px,1fr))', gap: 14 }}>
          <section style={panel}>
            <div style={{ fontSize: 9, letterSpacing: '0.2em', color: 'rgba(201,168,76,0.7)', textTransform: 'uppercase' }}>01 · Memory</div>
            <button onClick={addCapture} style={{ ...button, marginTop: 16, borderColor: 'rgba(0,212,170,0.35)', color: '#00D4AA' }}>+ Capture</button>
            <div style={{ marginTop: 18, display: 'flex', gap: 22 }}>
              <div><strong style={{ fontSize: 22 }}>{captures.filter(c => c.kind === 'original').length}</strong><div style={{ fontSize: 9, color: 'rgba(232,232,232,0.42)', letterSpacing: '0.12em' }}>ORIGINALS</div></div>
              <div><strong style={{ fontSize: 22 }}>{captures.length}</strong><div style={{ fontSize: 9, color: 'rgba(232,232,232,0.42)', letterSpacing: '0.12em' }}>REMEMBERED OBJECTS</div></div>
            </div>
            <p style={{ fontSize: 11, lineHeight: 1.55, color: 'rgba(232,232,232,0.42)', marginTop: 20 }}>
              Browser playback uses deterministic tones for rapid interface testing. Microphone capture, filesystem persistence, and native playback remain Android responsibilities.
            </p>
          </section>

          <section style={panel}>
            <div style={{ fontSize: 9, letterSpacing: '0.2em', color: 'rgba(201,168,76,0.7)', textTransform: 'uppercase' }}>02 · Selected Object</div>
            <div style={{ marginTop: 16, padding: 16, borderRadius: 11, background: 'rgba(0,0,0,0.16)', border: '1px solid rgba(255,255,255,0.06)' }}>
              <div style={{ fontSize: 9, letterSpacing: '0.18em', color: selected.kind === 'derived' ? '#B08DE8' : '#00D4AA' }}>{selected.kind === 'derived' ? 'DERIVED · OCTAVE UP' : 'ORIGINAL'}</div>
              <div style={{ fontFamily: 'serif', fontSize: 48, marginTop: 4, color: '#E8E8E8' }}>{selected.note}</div>
              <div style={{ fontSize: 12, color: 'rgba(232,232,232,0.52)' }}>{selected.hz.toFixed(1)} Hz · {selected.label}</div>
              {selected.parentId && <div style={{ marginTop: 10, fontSize: 9, color: 'rgba(232,232,232,0.4)' }}>PARENT <code>{selected.parentId.slice(0, 16)}…</code></div>}
              {selected.transformation && <div style={{ marginTop: 5, fontSize: 9, color: 'rgba(232,232,232,0.4)' }}>TRANSFORMATION <code>{selected.transformation}</code></div>}
            </div>
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: 7, marginTop: 12 }}>
              <button style={button} onClick={() => play(selected)}>▶ Play</button>
              <button style={button} onClick={() => pause(selected)}>⏸ {paused === selected.id ? 'Resume' : 'Pause'}</button>
              <button style={{ ...button, ...(repeat === selected.id ? { color: '#00D4AA', borderColor: 'rgba(0,212,170,0.35)' } : {}) }} onClick={() => toggleRepeat(selected)}>↻ {repeat === selected.id ? 'Repeat On' : 'Repeat'}</button>
              <button disabled={selected.kind === 'derived'} style={{ ...button, opacity: selected.kind === 'derived' ? 0.3 : 1 }} onClick={() => octaveUp(selected)}>↗ Octave Up</button>
            </div>
            <details style={{ marginTop: 14, color: 'rgba(232,232,232,0.5)', fontSize: 10 }}>
              <summary style={{ cursor: 'pointer', letterSpacing: '0.12em' }}>INSPECT RAW JSON</summary>
              <pre style={{ overflow: 'auto', padding: 12, background: 'rgba(0,0,0,0.2)', borderRadius: 8 }}>{selectedJson}</pre>
            </details>
          </section>
        </div>

        <section style={{ ...panel, marginTop: 14 }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', gap: 12, flexWrap: 'wrap', fontSize: 9, letterSpacing: '0.18em', color: 'rgba(201,168,76,0.7)' }}>
            <span>03 · Memory / Playback</span><span>{captures.length} OBJECTS · EVERY OBJECT PLAYS INDEPENDENTLY</span>
          </div>
          <div style={{ display: 'grid', gap: 8, marginTop: 14 }}>
            {captures.map(capture => (
              <article key={capture.id} onClick={() => setSelected(capture)} style={{ display: 'grid', gridTemplateColumns: '1fr auto', gap: 12, alignItems: 'center', padding: 13, borderRadius: 10, background: selected.id === capture.id ? 'rgba(0,212,170,0.06)' : 'rgba(255,255,255,0.02)', border: selected.id === capture.id ? '1px solid rgba(0,212,170,0.25)' : '1px solid rgba(255,255,255,0.06)', cursor: 'pointer' }}>
                <div>
                  <div style={{ fontSize: 9, letterSpacing: '0.14em', color: capture.kind === 'derived' ? '#B08DE8' : '#00D4AA' }}>{capture.kind === 'derived' ? 'DERIVED' : 'ORIGINAL'}</div>
                  <strong style={{ display: 'block', marginTop: 3, fontSize: 12 }}>{capture.label}</strong>
                  <span style={{ display: 'block', marginTop: 3, fontSize: 10, color: 'rgba(232,232,232,0.45)' }}>{capture.note} · {capture.hz.toFixed(1)} Hz</span>
                  {capture.parentId && <small style={{ color: 'rgba(232,232,232,0.3)' }}>parent: {capture.parentId.slice(0, 12)}…</small>}
                </div>
                <div style={{ display: 'flex', alignItems: 'center', gap: 5 }} onClick={event => event.stopPropagation()}>
                  <button style={button} onClick={() => play(capture)}>▶</button>
                  <button style={button} onClick={() => pause(capture)}>⏸</button>
                  <button style={{ ...button, ...(repeat === capture.id ? { color: '#00D4AA', borderColor: 'rgba(0,212,170,0.35)' } : {}) }} onClick={() => toggleRepeat(capture)}>↻</button>
                </div>
              </article>
            ))}
          </div>
        </section>
      </div>
    </div>
  );
}
