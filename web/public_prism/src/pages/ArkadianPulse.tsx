import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';

const API_BASE = (import.meta.env.VITE_API_URL ?? '').replace(/\/$/, '');

// ── Statement data ─────────────────────────────────────────────────────────

interface Statement {
  key: string;
  node: string;
  nodeDisplay: string;
  text: string;
  reverse: boolean;
}

const STATEMENTS: Statement[] = [
  // Node 0 — Source
  { key: 'source_1', node: 'source', nodeDisplay: 'Source', text: 'I often return to the origins of things before deciding what they mean.', reverse: false },
  { key: 'source_2', node: 'source', nodeDisplay: 'Source', text: 'I care more about understanding where something came from than what everyone currently believes about it.', reverse: false },
  { key: 'source_3', node: 'source', nodeDisplay: 'Source', text: 'I rarely think about the origins of things — I focus on where they are now.', reverse: true },
  // Node 1 — Spark
  { key: 'spark_1', node: 'spark', nodeDisplay: 'Spark', text: 'When I have a new idea, I act on it quickly before overthinking.', reverse: false },
  { key: 'spark_2', node: 'spark', nodeDisplay: 'Spark', text: 'I am often the one who initiates projects or conversations.', reverse: false },
  { key: 'spark_3', node: 'spark', nodeDisplay: 'Spark', text: 'I prefer to wait and see before committing to a new direction.', reverse: true },
  // Node 2 — Breath
  { key: 'breath_1', node: 'breath', nodeDisplay: 'Breath', text: 'I can easily hold two opposing viewpoints without needing to resolve them immediately.', reverse: false },
  { key: 'breath_2', node: 'breath', nodeDisplay: 'Breath', text: 'I find it natural to see multiple sides of an issue.', reverse: false },
  { key: 'breath_3', node: 'breath', nodeDisplay: 'Breath', text: 'I prefer clarity and certainty over holding opposing truths.', reverse: true },
  // Node 3 — Flame
  { key: 'flame_1', node: 'flame', nodeDisplay: 'Flame', text: 'I often synthesize ideas from different domains into something new.', reverse: false },
  { key: 'flame_2', node: 'flame', nodeDisplay: 'Flame', text: 'I enjoy combining seemingly unrelated concepts into a coherent whole.', reverse: false },
  { key: 'flame_3', node: 'flame', nodeDisplay: 'Flame', text: 'I prefer to keep ideas separate rather than merge them.', reverse: true },
  // Node 4 — Ground
  { key: 'ground_1', node: 'ground', nodeDisplay: 'Ground', text: 'I build stable routines that help me stay consistent.', reverse: false },
  { key: 'ground_2', node: 'ground', nodeDisplay: 'Ground', text: 'People often rely on me to maintain stability.', reverse: false },
  { key: 'ground_3', node: 'ground', nodeDisplay: 'Ground', text: 'I prefer flexibility over structure.', reverse: true },
  // Node 5 — Life
  { key: 'life_1', node: 'life', nodeDisplay: 'Life', text: 'I adapt quickly when unexpected changes occur.', reverse: false },
  { key: 'life_2', node: 'life', nodeDisplay: 'Life', text: 'I see challenges as opportunities to grow and evolve.', reverse: false },
  { key: 'life_3', node: 'life', nodeDisplay: 'Life', text: 'I prefer stability over change, even when change might be better.', reverse: true },
  // Node 6 — Harmony
  { key: 'harmony_1', node: 'harmony', nodeDisplay: 'Harmony', text: 'I actively balance competing demands in my life.', reverse: false },
  { key: 'harmony_2', node: 'harmony', nodeDisplay: 'Harmony', text: 'I am skilled at finding equilibrium between opposing forces.', reverse: false },
  { key: 'harmony_3', node: 'harmony', nodeDisplay: 'Harmony', text: 'I often struggle to balance competing priorities.', reverse: true },
  // Node 7 — Seek
  { key: 'seek_1', node: 'seek', nodeDisplay: 'Seek', text: 'I am driven by questions that have no easy answers.', reverse: false },
  { key: 'seek_2', node: 'seek', nodeDisplay: 'Seek', text: 'I am comfortable with not knowing — inquiry itself is the reward.', reverse: false },
  { key: 'seek_3', node: 'seek', nodeDisplay: 'Seek', text: 'I prefer answers over questions.', reverse: true },
  // Node 8 — Octave
  { key: 'octave_1', node: 'octave', nodeDisplay: 'Octave', text: 'I often revisit past experiences and see them completely differently.', reverse: false },
  { key: 'octave_2', node: 'octave', nodeDisplay: 'Octave', text: 'I learn from my history and apply that learning to the present.', reverse: false },
  { key: 'octave_3', node: 'octave', nodeDisplay: 'Octave', text: 'I rarely look back — the past is past.', reverse: true },
  // Node 9 — Return
  { key: 'return_1', node: 'return_node', nodeDisplay: 'Return', text: 'I sense when a chapter of my life is complete and ready to close.', reverse: false },
  { key: 'return_2', node: 'return_node', nodeDisplay: 'Return', text: 'I am skilled at endings — I close cycles cleanly.', reverse: false },
  { key: 'return_3', node: 'return_node', nodeDisplay: 'Return', text: 'I struggle to let go of things that are finished.', reverse: true },
  // Node 10 — Witness
  { key: 'witness_1', node: 'witness', nodeDisplay: 'Witness', text: 'I can observe a situation without needing to intervene or fix it.', reverse: false },
  { key: 'witness_2', node: 'witness', nodeDisplay: 'Witness', text: 'I am a natural witness — I remember what others forget.', reverse: false },
  { key: 'witness_3', node: 'witness', nodeDisplay: 'Witness', text: 'I become uncomfortable when I cannot immediately act.', reverse: true },
  // Node 11 — Weaver
  { key: 'weaver_1', node: 'weaver', nodeDisplay: 'Weaver', text: 'I naturally connect people, ideas, and resources.', reverse: false },
  { key: 'weaver_2', node: 'weaver', nodeDisplay: 'Weaver', text: 'I feel most aligned when I am part of something larger than myself.', reverse: false },
  { key: 'weaver_3', node: 'weaver', nodeDisplay: 'Weaver', text: 'I prefer to work independently rather than connect others.', reverse: true },
];

const SCALE = [
  { value: 1, label: 'Strongly\nDisagree' },
  { value: 2, label: 'Disagree' },
  { value: 3, label: 'Neutral' },
  { value: 4, label: 'Agree' },
  { value: 5, label: 'Strongly\nAgree' },
];

const NODE_COLORS: Record<string, string> = {
  source: '#C9A84C', spark: '#FF8C42', breath: '#00D4AA', flame: '#FF6B6B',
  ground: '#6A9FD8', life: '#4CAF50', harmony: '#B08DE8', seek: '#00D4AA',
  octave: '#C9A84C', return_node: '#E88C6A', witness: '#B08DE8', weaver: '#00D4AA',
};

// ── Types ─────────────────────────────────────────────────────────────────────

interface PulseResult {
  scores: Record<string, number>;
  primary_patterns: { node: string; display: string; score: number; cluster: string | null }[];
  growth_edge: { node: string; display: string; score: number; shadow_index: number; description: string };
  confidence: number;
  pattern_cluster: string;
  oracle_summary: string;
  sigil_svg: string;
}

// ── Timer hook ────────────────────────────────────────────────────────────────

function useElapsedTime(running: boolean) {
  const [elapsed, setElapsed] = useState(0);
  useEffect(() => {
    if (!running) return;
    const t = setInterval(() => setElapsed(e => e + 1), 1000);
    return () => clearInterval(t);
  }, [running]);
  const m = Math.floor(elapsed / 60);
  const s = elapsed % 60;
  return `${m}:${s.toString().padStart(2, '0')}`;
}

// ── Likert question ───────────────────────────────────────────────────────────

function LikertQuestion({
  statement, index, total, value, onChange,
}: {
  statement: Statement; index: number; total: number;
  value: number | undefined; onChange: (v: number) => void;
}) {
  const color = NODE_COLORS[statement.node] || '#C9A84C';
  return (
    <motion.div
      key={statement.key}
      initial={{ opacity: 0, y: 18 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -18 }}
      transition={{ duration: 0.35 }}
      style={{ width: '100%' }}
    >
      {/* Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px' }}>
        <span style={{
          fontFamily: 'sans-serif', fontSize: '9px', letterSpacing: '0.28em',
          textTransform: 'uppercase', color: `${color}99`,
          padding: '3px 10px', border: `1px solid ${color}33`, borderRadius: '20px',
        }}>
          {statement.nodeDisplay}
        </span>
        <span style={{ fontFamily: 'sans-serif', fontSize: '10px', color: 'rgba(232,232,232,0.28)', letterSpacing: '0.12em' }}>
          {index + 1} / {total}
        </span>
      </div>

      {/* Statement */}
      <p style={{
        fontFamily: 'serif', fontSize: '16px', lineHeight: '1.75',
        color: 'rgba(232,232,232,0.88)', marginBottom: '24px',
        textAlign: 'center', minHeight: '72px',
      }}>
        {statement.text}
      </p>

      {/* Scale */}
      <div style={{ display: 'flex', gap: '6px', justifyContent: 'center' }}>
        {SCALE.map(opt => {
          const active = value === opt.value;
          return (
            <button
              key={opt.value}
              onClick={() => onChange(opt.value)}
              style={{
                flex: 1, maxWidth: '72px',
                padding: '10px 4px',
                background: active ? `${color}22` : 'rgba(255,255,255,0.02)',
                border: `1px solid ${active ? color : 'rgba(255,255,255,0.08)'}`,
                borderRadius: '8px',
                cursor: 'pointer',
                transition: 'all 0.18s',
                display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '6px',
              }}
            >
              <div style={{
                width: '20px', height: '20px', borderRadius: '50%',
                border: `2px solid ${active ? color : 'rgba(255,255,255,0.18)'}`,
                background: active ? color : 'transparent',
                transition: 'all 0.18s',
              }} />
              <span style={{
                fontFamily: 'sans-serif', fontSize: '8.5px', letterSpacing: '0.04em',
                color: active ? color : 'rgba(232,232,232,0.32)',
                textAlign: 'center', whiteSpace: 'pre-line', lineHeight: 1.3,
              }}>
                {opt.label}
              </span>
            </button>
          );
        })}
      </div>
    </motion.div>
  );
}

// ── Progress bar ──────────────────────────────────────────────────────────────

function ProgressBar({ answered, total }: { answered: number; total: number }) {
  const pct = (answered / total) * 100;
  return (
    <div style={{ marginBottom: '28px' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '6px' }}>
        <span style={{ fontFamily: 'sans-serif', fontSize: '9px', letterSpacing: '0.22em', textTransform: 'uppercase', color: 'rgba(0,212,170,0.45)' }}>
          Vector Measurement
        </span>
        <span style={{ fontFamily: 'sans-serif', fontSize: '9px', color: 'rgba(0,212,170,0.45)' }}>
          {answered}/{total}
        </span>
      </div>
      <div style={{ height: '2px', background: 'rgba(0,212,170,0.1)', borderRadius: '2px', overflow: 'hidden' }}>
        <motion.div
          animate={{ width: `${pct}%` }}
          transition={{ duration: 0.4 }}
          style={{ height: '100%', background: 'linear-gradient(90deg, #00D4AA, #C9A84C)', borderRadius: '2px' }}
        />
      </div>
    </div>
  );
}

// ── Sigil display ─────────────────────────────────────────────────────────────

function DodecahedralSigil({ svgString }: { svgString: string }) {
  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.85 }}
      animate={{ opacity: 1, scale: 1 }}
      transition={{ duration: 0.9, ease: 'easeOut' }}
      style={{
        width: '200px', height: '200px', margin: '0 auto 28px',
        border: '1px solid rgba(201,168,76,0.2)', borderRadius: '50%',
        padding: '8px',
        background: 'radial-gradient(circle, rgba(201,168,76,0.04) 0%, transparent 70%)',
        boxShadow: '0 0 40px rgba(201,168,76,0.08), 0 0 80px rgba(0,212,170,0.04)',
      }}
      dangerouslySetInnerHTML={{ __html: svgString }}
    />
  );
}

// ── Score bar ─────────────────────────────────────────────────────────────────

function ScoreBar({ label, score, highlight }: { label: string; score: number; highlight?: boolean }) {
  const color = highlight ? '#C9A84C' : 'rgba(0,212,170,0.7)';
  return (
    <div style={{ marginBottom: '8px' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '4px' }}>
        <span style={{ fontFamily: 'sans-serif', fontSize: '10px', letterSpacing: '0.14em', textTransform: 'uppercase', color: highlight ? '#C9A84C' : 'rgba(232,232,232,0.5)' }}>
          {label}
        </span>
        <span style={{ fontFamily: 'sans-serif', fontSize: '10px', color: highlight ? '#C9A84C' : 'rgba(232,232,232,0.35)' }}>
          {score}
        </span>
      </div>
      <div style={{ height: '3px', background: 'rgba(255,255,255,0.05)', borderRadius: '2px', overflow: 'hidden' }}>
        <motion.div
          initial={{ width: 0 }}
          animate={{ width: `${score}%` }}
          transition={{ duration: 0.9, ease: 'easeOut', delay: 0.1 }}
          style={{ height: '100%', background: color, borderRadius: '2px' }}
        />
      </div>
    </div>
  );
}

// ── Oracle processing animation ───────────────────────────────────────────────

function OracleProcessing() {
  const lines = [
    'Calculating node vectors…',
    'Mapping shadow architecture…',
    'Generating dodecahedral sigil…',
    'Synthesising Oracle summary…',
  ];
  const [lineIdx, setLineIdx] = useState(0);
  useEffect(() => {
    const t = setInterval(() => setLineIdx(i => (i + 1) % lines.length), 1200);
    return () => clearInterval(t);
  }, []);
  return (
    <div style={{ textAlign: 'center', padding: '60px 20px' }}>
      <motion.div
        animate={{ rotate: 360 }}
        transition={{ duration: 6, repeat: Infinity, ease: 'linear' }}
        style={{ width: '48px', height: '48px', margin: '0 auto 24px', border: '1px solid rgba(201,168,76,0.3)', borderTop: '1px solid #C9A84C', borderRadius: '50%' }}
      />
      <AnimatePresence mode="wait">
        <motion.p
          key={lineIdx}
          initial={{ opacity: 0, y: 6 }}
          animate={{ opacity: 1, y: 0 }}
          exit={{ opacity: 0, y: -6 }}
          transition={{ duration: 0.4 }}
          style={{ fontFamily: 'sans-serif', fontSize: '10px', letterSpacing: '0.22em', textTransform: 'uppercase', color: 'rgba(201,168,76,0.6)' }}
        >
          {lines[lineIdx]}
        </motion.p>
      </AnimatePresence>
    </div>
  );
}

// ── Results page ──────────────────────────────────────────────────────────────

function PulseResults({ result, onReset }: { result: PulseResult; onReset: () => void }) {
  const topNode = result.primary_patterns[0];

  return (
    <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ duration: 0.6 }}>
      {/* Header */}
      <div style={{ textAlign: 'center', marginBottom: '28px' }}>
        <p style={{ fontFamily: 'sans-serif', fontSize: '9px', letterSpacing: '0.35em', textTransform: 'uppercase', color: 'rgba(0,212,170,0.5)', marginBottom: '8px' }}>
          Arkadian Pulse · Complete
        </p>
        <h2 style={{ fontFamily: '"Cinzel", serif', fontSize: '26px', color: '#C9A84C', marginBottom: '6px', letterSpacing: '0.12em' }}>
          {result.pattern_cluster}
        </h2>
        <p style={{ fontFamily: 'sans-serif', fontSize: '10px', color: 'rgba(0,212,170,0.5)', letterSpacing: '0.18em', textTransform: 'uppercase' }}>
          Confidence Score: {result.confidence}/100
        </p>
      </div>

      {/* Sigil */}
      <DodecahedralSigil svgString={result.sigil_svg} />

      {/* Primary Patterns */}
      <div style={{ marginBottom: '24px', padding: '18px 20px', background: 'rgba(201,168,76,0.04)', border: '1px solid rgba(201,168,76,0.16)', borderRadius: '10px' }}>
        <p style={{ fontFamily: 'sans-serif', fontSize: '9px', letterSpacing: '0.28em', textTransform: 'uppercase', color: 'rgba(201,168,76,0.5)', marginBottom: '14px' }}>
          Primary Patterns
        </p>
        {result.primary_patterns.map((p, i) => (
          <div key={p.node} style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: i < 2 ? '10px' : 0 }}>
            <span style={{ fontFamily: 'sans-serif', fontSize: '9px', color: 'rgba(201,168,76,0.35)', width: '14px', textAlign: 'right' }}>
              {i + 1}
            </span>
            <div style={{ flex: 1 }}>
              <ScoreBar label={p.display} score={p.score} highlight={i === 0} />
            </div>
          </div>
        ))}
      </div>

      {/* Full score vector */}
      <div style={{ marginBottom: '24px', padding: '18px 20px', background: 'rgba(0,212,170,0.03)', border: '1px solid rgba(0,212,170,0.1)', borderRadius: '10px' }}>
        <p style={{ fontFamily: 'sans-serif', fontSize: '9px', letterSpacing: '0.28em', textTransform: 'uppercase', color: 'rgba(0,212,170,0.4)', marginBottom: '14px' }}>
          12-Node Vector
        </p>
        {Object.entries(result.scores).map(([label, score]) => (
          <ScoreBar key={label} label={label} score={score} highlight={label === topNode.display} />
        ))}
      </div>

      {/* Growth Edge */}
      <div style={{ marginBottom: '24px', padding: '18px 20px', background: 'rgba(232,140,106,0.04)', border: '1px solid rgba(232,140,106,0.18)', borderRadius: '10px' }}>
        <p style={{ fontFamily: 'sans-serif', fontSize: '9px', letterSpacing: '0.28em', textTransform: 'uppercase', color: 'rgba(232,140,106,0.55)', marginBottom: '10px' }}>
          Growth Edge · Shadow Index {result.growth_edge.shadow_index}
        </p>
        <p style={{ fontFamily: '"Cinzel", serif', fontSize: '16px', color: '#E88C6A', marginBottom: '8px', letterSpacing: '0.08em' }}>
          {result.growth_edge.display}
        </p>
        <p style={{ fontFamily: 'sans-serif', fontSize: '12px', color: 'rgba(232,232,232,0.5)', lineHeight: '1.7', margin: 0 }}>
          {result.growth_edge.description}
        </p>
      </div>

      {/* Oracle Summary */}
      <div style={{ marginBottom: '28px', padding: '20px', background: 'rgba(14,17,32,0.72)', border: '1px solid rgba(201,168,76,0.22)', borderRadius: '10px', position: 'relative', backdropFilter: 'blur(12px)' }}>
        {/* Corner ornaments */}
        {[['top','left'],['top','right'],['bottom','left'],['bottom','right']].map(([v, h]) => (
          <div key={`${v}${h}`} style={{
            position: 'absolute', [v]: 0, [h]: 0, width: 8, height: 8,
            borderTop: v === 'top' ? '1px solid rgba(201,168,76,0.45)' : 'none',
            borderBottom: v === 'bottom' ? '1px solid rgba(201,168,76,0.45)' : 'none',
            borderLeft: h === 'left' ? '1px solid rgba(201,168,76,0.45)' : 'none',
            borderRight: h === 'right' ? '1px solid rgba(201,168,76,0.45)' : 'none',
          }} />
        ))}
        <p style={{ fontFamily: 'sans-serif', fontSize: '9px', letterSpacing: '0.28em', textTransform: 'uppercase', color: 'rgba(201,168,76,0.45)', marginBottom: '12px' }}>
          Oracle Summary
        </p>
        <p style={{ fontFamily: 'serif', fontSize: '14px', lineHeight: '1.85', color: 'rgba(212,223,232,0.78)', margin: 0 }}>
          {result.oracle_summary}
        </p>
      </div>

      {/* CTA — Premium IMS */}
      <div style={{ marginBottom: '20px', padding: '22px 20px', background: 'linear-gradient(135deg, rgba(201,168,76,0.08), rgba(201,168,76,0.04))', border: '1px solid rgba(201,168,76,0.35)', borderRadius: '12px', textAlign: 'center' }}>
        <p style={{ fontFamily: 'sans-serif', fontSize: '9px', letterSpacing: '0.35em', textTransform: 'uppercase', color: 'rgba(201,168,76,0.6)', marginBottom: '10px' }}>
          Premium Identity Mapping Session
        </p>
        <h3 style={{ fontFamily: '"Cinzel", serif', fontSize: '20px', color: '#C9A84C', marginBottom: '10px', letterSpacing: '0.1em' }}>
          Unlock the Full Map
        </h3>
        <p style={{ fontFamily: 'sans-serif', fontSize: '12px', color: 'rgba(232,232,232,0.48)', lineHeight: '1.7', marginBottom: '18px' }}>
          90-minute live session · 12 narrative prompts · Shadow architecture mapping ·
          Personal Morphic Seed · Custom Oracle Report (PDF + Audio + Sigil)
        </p>
        <p style={{ fontFamily: '"Cinzel", serif', fontSize: '22px', color: '#C9A84C', marginBottom: '16px' }}>$777</p>
        <a
          href="https://arkadia-prism.vercel.app"
          target="_blank"
          rel="noopener noreferrer"
          style={{
            display: 'block', width: '100%', padding: '15px',
            background: 'linear-gradient(135deg, rgba(201,168,76,0.18), rgba(201,168,76,0.08))',
            border: '1px solid rgba(201,168,76,0.55)', borderRadius: '10px',
            color: '#C9A84C', fontFamily: 'sans-serif', fontSize: '10px',
            letterSpacing: '0.24em', textTransform: 'uppercase',
            cursor: 'pointer', textDecoration: 'none',
            boxShadow: '0 4px 24px rgba(201,168,76,0.12)',
          }}
        >
          ✦ Book Your Identity Mapping Session
        </a>
      </div>

      {/* Retake */}
      <div style={{ textAlign: 'center' }}>
        <button
          onClick={onReset}
          style={{ background: 'none', border: 'none', color: 'rgba(0,212,170,0.3)', fontFamily: 'sans-serif', fontSize: '9px', letterSpacing: '0.22em', textTransform: 'uppercase', cursor: 'pointer' }}
        >
          ↺ Retake the Pulse
        </button>
      </div>
    </motion.div>
  );
}

// ── Main component ─────────────────────────────────────────────────────────────

export default function ArkadianPulse() {
  const [responses, setResponses] = useState<Record<string, number>>({});
  const [currentIdx, setCurrentIdx] = useState(0);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<PulseResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [started, setStarted] = useState(false);
  const elapsed = useElapsedTime(started && !result && !loading);

  const total = STATEMENTS.length;
  const answered = Object.keys(responses).length;
  const current = STATEMENTS[currentIdx];
  const currentValue = current ? responses[current.key] : undefined;

  const handleAnswer = (value: number) => {
    const newResponses = { ...responses, [current.key]: value };
    setResponses(newResponses);

    if (currentIdx < total - 1) {
      setTimeout(() => setCurrentIdx(i => i + 1), 280);
    }
  };

  const handleBack = () => {
    if (currentIdx > 0) setCurrentIdx(i => i - 1);
  };

  const handleSubmit = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await fetch(`${API_BASE}/api/pulse/analyze`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ responses }),
      });
      if (!res.ok) throw new Error(`Server error: ${res.status}`);
      const data = await res.json();
      setResult(data);
    } catch (e: any) {
      setError(e.message || 'The Oracle is recalibrating. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const handleReset = () => {
    setResponses({});
    setCurrentIdx(0);
    setResult(null);
    setError(null);
    setStarted(false);
  };

  const allAnswered = answered === total;

  // ── Intro screen ────────────────────────────────────────────────────────────
  if (!started) {
    return (
      <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} style={{ maxWidth: '540px', margin: '0 auto', padding: '20px 0' }}>
        <div style={{ textAlign: 'center', marginBottom: '32px' }}>
          <p style={{ fontFamily: 'sans-serif', fontSize: '9px', letterSpacing: '0.35em', textTransform: 'uppercase', color: 'rgba(0,212,170,0.5)', marginBottom: '10px' }}>
            Free · 4–6 Minutes · 36 Statements
          </p>
          <h1 style={{ fontFamily: '"Cinzel", serif', fontSize: '32px', color: '#C9A84C', letterSpacing: '0.15em', marginBottom: '12px' }}>
            Arkadian Pulse
          </h1>
          <p style={{ fontFamily: 'serif', fontSize: '14px', lineHeight: '1.85', color: 'rgba(212,223,232,0.55)', margin: '0 0 24px' }}>
            A vector measurement engine across 12 sovereign nodes.<br />
            Not a personality type — a living signal map.
          </p>
        </div>

        {/* What you'll receive */}
        <div style={{ marginBottom: '28px', padding: '18px 20px', background: 'rgba(14,17,32,0.72)', border: '1px solid rgba(201,168,76,0.18)', borderRadius: '10px' }}>
          <p style={{ fontFamily: 'sans-serif', fontSize: '9px', letterSpacing: '0.28em', textTransform: 'uppercase', color: 'rgba(201,168,76,0.45)', marginBottom: '12px' }}>
            Your Pulse Report Includes
          </p>
          {[
            ['◎', 'Primary Pattern Cluster', 'Your proprietary 3-node archetype name'],
            ['⟐', 'Growth Edge + Shadow Index', 'Your lowest node with opposing-force analysis'],
            ['✦', 'Dodecahedral Sigil', 'Visual compression of your 12-node vector'],
            ['∞', 'Oracle Summary', '150-word personalised synthesis'],
            ['◈', 'Confidence Score', 'Signal strength of your responses'],
          ].map(([sigil, title, sub]) => (
            <div key={title} style={{ display: 'flex', gap: '12px', marginBottom: '10px' }}>
              <span style={{ color: '#C9A84C', fontSize: '13px', flexShrink: 0, width: '18px' }}>{sigil}</span>
              <div>
                <p style={{ fontFamily: 'sans-serif', fontSize: '11px', color: 'rgba(232,232,232,0.72)', margin: '0 0 2px', letterSpacing: '0.06em' }}>{title}</p>
                <p style={{ fontFamily: 'sans-serif', fontSize: '10px', color: 'rgba(232,232,232,0.32)', margin: 0 }}>{sub}</p>
              </div>
            </div>
          ))}
        </div>

        {/* Instructions */}
        <div style={{ marginBottom: '28px', padding: '14px 18px', background: 'rgba(0,212,170,0.03)', border: '1px solid rgba(0,212,170,0.12)', borderRadius: '8px' }}>
          <p style={{ fontFamily: 'sans-serif', fontSize: '11px', color: 'rgba(0,212,170,0.55)', lineHeight: '1.7', margin: 0 }}>
            Respond instinctively. There are no correct answers — only honest ones. Answer what is true right now, not what you aspire to be.
          </p>
        </div>

        <button
          onClick={() => setStarted(true)}
          style={{
            width: '100%', padding: '17px',
            background: 'linear-gradient(135deg, rgba(0,212,170,0.12), rgba(0,212,170,0.05))',
            border: '1px solid rgba(0,212,170,0.45)', borderRadius: '11px',
            color: '#00D4AA', fontFamily: 'sans-serif', fontSize: '11px',
            letterSpacing: '0.22em', textTransform: 'uppercase', cursor: 'pointer',
            backdropFilter: 'blur(16px)',
          }}
        >
          ⟐ Begin the Pulse
        </button>
      </motion.div>
    );
  }

  // ── Results ─────────────────────────────────────────────────────────────────
  if (result) {
    return (
      <div style={{ maxWidth: '540px', margin: '0 auto', padding: '20px 0' }}>
        <PulseResults result={result} onReset={handleReset} />
      </div>
    );
  }

  // ── Loading ─────────────────────────────────────────────────────────────────
  if (loading) {
    return (
      <div style={{ maxWidth: '540px', margin: '0 auto', padding: '20px 0' }}>
        <OracleProcessing />
      </div>
    );
  }

  // ── Question flow ───────────────────────────────────────────────────────────
  return (
    <div style={{ maxWidth: '540px', margin: '0 auto', padding: '20px 0' }}>
      {/* Timer + node label */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
        <span style={{ fontFamily: 'sans-serif', fontSize: '9px', letterSpacing: '0.22em', textTransform: 'uppercase', color: 'rgba(0,212,170,0.35)' }}>
          Arkadian Pulse
        </span>
        <span style={{ fontFamily: 'sans-serif', fontSize: '10px', color: 'rgba(232,232,232,0.25)', letterSpacing: '0.08em' }}>
          {elapsed}
        </span>
      </div>

      {/* Progress */}
      <ProgressBar answered={answered} total={total} />

      {/* Question */}
      <div style={{ minHeight: '240px', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
        <AnimatePresence mode="wait">
          <LikertQuestion
            key={currentIdx}
            statement={current}
            index={currentIdx}
            total={total}
            value={currentValue}
            onChange={handleAnswer}
          />
        </AnimatePresence>
      </div>

      {/* Navigation */}
      <div style={{ display: 'flex', gap: '10px', marginTop: '28px', alignItems: 'center' }}>
        {currentIdx > 0 && (
          <button
            onClick={handleBack}
            style={{
              padding: '11px 18px', background: 'rgba(255,255,255,0.02)',
              border: '1px solid rgba(255,255,255,0.08)', borderRadius: '8px',
              color: 'rgba(232,232,232,0.35)', fontFamily: 'sans-serif',
              fontSize: '10px', letterSpacing: '0.14em', cursor: 'pointer',
            }}
          >
            ← Back
          </button>
        )}

        {currentIdx < total - 1 && currentValue && (
          <button
            onClick={() => setCurrentIdx(i => i + 1)}
            style={{
              flex: 1, padding: '11px',
              background: 'rgba(0,212,170,0.05)', border: '1px solid rgba(0,212,170,0.25)',
              borderRadius: '8px', color: 'rgba(0,212,170,0.7)',
              fontFamily: 'sans-serif', fontSize: '10px', letterSpacing: '0.2em',
              textTransform: 'uppercase', cursor: 'pointer',
            }}
          >
            Next →
          </button>
        )}

        {allAnswered && (
          <button
            onClick={handleSubmit}
            style={{
              flex: 1, padding: '15px',
              background: 'linear-gradient(135deg, rgba(201,168,76,0.14), rgba(201,168,76,0.06))',
              border: '1px solid rgba(201,168,76,0.5)', borderRadius: '10px',
              color: '#C9A84C', fontFamily: 'sans-serif', fontSize: '11px',
              letterSpacing: '0.22em', textTransform: 'uppercase', cursor: 'pointer',
              boxShadow: '0 4px 20px rgba(201,168,76,0.1)',
            }}
          >
            ✦ Reveal Your Pattern
          </button>
        )}
      </div>

      {/* Error */}
      {error && (
        <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} style={{ marginTop: '16px', padding: '12px 16px', background: 'rgba(255,80,80,0.06)', border: '1px solid rgba(255,80,80,0.2)', borderRadius: '8px' }}>
          <p style={{ fontFamily: 'sans-serif', fontSize: '11px', color: 'rgba(255,120,120,0.8)', margin: 0 }}>{error}</p>
        </motion.div>
      )}

      {/* Skip prompt for answered items */}
      {!allAnswered && answered > 0 && currentIdx === total - 1 && !currentValue && (
        <p style={{ textAlign: 'center', fontFamily: 'sans-serif', fontSize: '10px', color: 'rgba(232,232,232,0.22)', marginTop: '14px' }}>
          Answer this statement to unlock your results
        </p>
      )}
    </div>
  );
}
