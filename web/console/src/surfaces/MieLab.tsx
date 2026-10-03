import { useEffect, useMemo, useRef, useState } from "react";

type Capture = {
  id: string;
  kind: "original" | "derived";
  label: string;
  note: string;
  hz: number;
  parentId?: string;
  transformation?: string;
};

const seed: Capture[] = [
  { id: "capture-001", kind: "original", label: "CAPTURE 001", note: "A4", hz: 440 },
  { id: "capture-001-derivative", kind: "derived", label: "CAPTURE 001 · OCTAVE UP", note: "A5", hz: 880, parentId: "capture-001", transformation: "octave_up" },
];

export function MieLab() {
  const [captures, setCaptures] = useState<Capture[]>(seed);
  const [selected, setSelected] = useState(seed[0]);
  const [playing, setPlaying] = useState<string | null>(null);
  const [repeat, setRepeat] = useState<string | null>(null);
  const [paused, setPaused] = useState<string | null>(null);
  const timer = useRef<number | null>(null);
  const selectedJson = useMemo(() => JSON.stringify(selected, null, 2), [selected]);

  useEffect(() => () => { if (timer.current) window.clearTimeout(timer.current); }, []);

  function stopAll() {
    if (timer.current) window.clearTimeout(timer.current);
    timer.current = null;
    setPlaying(null);
    setPaused(null);
  }

  function play(capture: Capture) {
    stopAll();
    const AudioCtx = window.AudioContext || (window as typeof window & { webkitAudioContext?: typeof AudioContext }).webkitAudioContext;
    if (AudioCtx) {
      const ctx = new AudioCtx();
      const osc = ctx.createOscillator();
      const gain = ctx.createGain();
      osc.frequency.value = capture.hz;
      osc.type = "sine";
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
      setPlaying((current) => current === capture.id ? null : current);
      if (repeat === capture.id) play(capture);
    }, 420);
  }

  function pause(capture: Capture) {
    if (playing === capture.id) {
      if (timer.current) window.clearTimeout(timer.current);
      setPlaying(null);
      setPaused(capture.id);
    } else if (paused === capture.id) {
      play(capture);
    }
  }

  function toggleRepeat(capture: Capture) {
    const next = repeat === capture.id ? null : capture.id;
    setRepeat(next);
    if (next && playing !== capture.id) play(capture);
  }

  function octaveUp(source: Capture) {
    if (source.kind === "derived") return;
    const derivative: Capture = {
      id: crypto.randomUUID(),
      kind: "derived",
      label: source.label + " · OCTAVE UP",
      note: "A5",
      hz: source.hz * 2,
      parentId: source.id,
      transformation: "octave_up",
    };
    setCaptures((items) => [...items, derivative]);
    setSelected(derivative);
  }

  function addCapture() {
    const id = crypto.randomUUID();
    const next: Capture = { id, kind: "original", label: "CAPTURE " + String(captures.filter((c) => c.kind === "original").length + 1).padStart(3, "0"), note: "A4", hz: 440 };
    setCaptures((items) => [...items, next]);
    setSelected(next);
  }

  return (
    <div className="mie-lab">
      <div className="mie-lab-header">
        <div>
          <div className="mie-eyebrow">MUSICAL INTENTION ENGINE · WEB LAB</div>
          <h1>Make the sound <span>rememberable.</span></h1>
          <p>Rapid interaction proving ground for Gate 04. This is the interface laboratory, not the native execution substrate.</p>
        </div>
        <div className="mie-gate"><span>GATE 04</span><strong>REMEMBER → TRANSFORM</strong></div>
      </div>

      <div className="mie-lab-grid">
        <section className="mie-panel mie-capture">
          <div className="mie-panel-label">01 · MEMORY</div>
          <div className="mie-capture-core">
            <button className="mie-capture-button" onClick={addCapture}>+ CAPTURE</button>
            <div><strong>{captures.filter((c) => c.kind === "original").length} originals</strong><span>{captures.length} remembered objects</span></div>
          </div>
          <div className="mie-note">Browser lab uses deterministic demo tones for rapid playback-state testing. Native Android remains authoritative for microphone and filesystem proof.</div>
        </section>

        <section className="mie-panel">
          <div className="mie-panel-label">02 · SELECTED OBJECT</div>
          <div className="mie-object-hero">
            <div className="mie-object-kind">{selected.kind === "original" ? "ORIGINAL" : "DERIVED · OCTAVE UP"}</div>
            <h2>{selected.note}</h2>
            <div className="mie-object-meta">{selected.hz.toFixed(1)} Hz · {selected.label}</div>
            {selected.parentId && <div className="mie-parent">PARENT <code>{selected.parentId}</code></div>}
            {selected.transformation && <div className="mie-parent">TRANSFORMATION <code>{selected.transformation}</code></div>}
          </div>
          <div className="mie-actions">
            <button className="mie-primary" onClick={() => play(selected)}>▶ PLAY</button>
            <button onClick={() => pause(selected)}>⏸ {paused === selected.id ? "RESUME" : "PAUSE"}</button>
            <button className={repeat === selected.id ? "active" : ""} onClick={() => toggleRepeat(selected)}>↻ {repeat === selected.id ? "REPEAT ON" : "REPEAT"}</button>
            <button disabled={selected.kind === "derived"} onClick={() => octaveUp(selected)}>↗ OCTAVE UP</button>
          </div>
          <details className="mie-json"><summary>INSPECT RAW JSON</summary><pre>{selectedJson}</pre></details>
        </section>

        <section className="mie-panel mie-history-panel">
          <div className="mie-panel-label">03 · MEMORY / PLAYBACK</div>
          <div className="mie-history-head"><span>{captures.length} OBJECTS</span><span>EVERY OBJECT PLAYS INDEPENDENTLY</span></div>
          <div className="mie-history">
            {captures.map((capture) => (
              <article key={capture.id} className={selected.id === capture.id ? "mie-memory selected" : "mie-memory"} onClick={() => setSelected(capture)}>
                <div className="mie-memory-main">
                  <div className={capture.kind === "derived" ? "mie-kind derived" : "mie-kind"}>{capture.kind === "derived" ? "DERIVED" : "ORIGINAL"}</div>
                  <strong>{capture.label}</strong>
                  <span>{capture.note} · {capture.hz.toFixed(1)} Hz</span>
                  {capture.parentId && <small>parent: {capture.parentId.slice(0, 12)}…</small>}
                </div>
                <div className="mie-memory-controls" onClick={(event) => event.stopPropagation()}>
                  <button onClick={() => play(capture)}>▶</button>
                  <button onClick={() => pause(capture)}>⏸</button>
                  <button className={repeat === capture.id ? "active" : ""} onClick={() => toggleRepeat(capture)}>↻</button>
                </div>
                <div className="mie-state">{playing === capture.id ? "PLAYING" : paused === capture.id ? "PAUSED" : repeat === capture.id ? "REPEAT ARMED" : "READY"}</div>
              </article>
            ))}
          </div>
        </section>
      </div>
    </div>
  );
}
