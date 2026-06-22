import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useSpiralQuantumResonance } from '../hooks/useSpiralQuantumResonance';
import MoonPhaseRing from '../components/MoonPhaseRing';

const API_BASE = (import.meta.env.VITE_API_URL ?? '').replace(/\/$/, '');

// ─── Types ────────────────────────────────────────────────────────────────────

type GateMode = 'oracle' | 'aic' | 'ims';
type IMSStep  = 'intro' | 'form' | 'questionnaire' | 'confirmed';
type AICStep  = 1 | 2 | 3 | 4 | 'generating' | 'result';

interface LivingGateProps {
  onEnterField: (phrase: string) => void;
  onGoToOfferings?: () => void;
  initialMode?: GateMode;
}

interface IMSForm { name: string; email: string; phone: string }

// ─── AIC Data ─────────────────────────────────────────────────────────────────

const L1_QUESTIONS = [
  { id: 'A1', q: 'When faced with a complex problem, you first —', a: 'Turn inward to consult your own understanding', b: 'Turn outward to gather external input', la: 'I', lb: 'E' },
  { id: 'A2', q: 'After a long day, you recharge by —', a: 'Spending time alone, processing your thoughts', b: 'Engaging with others and exchanging energy', la: 'I', lb: 'E' },
  { id: 'B1', q: 'When learning something new, you focus on —', a: 'Concrete details and practical applications', b: 'Underlying patterns and future possibilities', la: 'S', lb: 'N' },
  { id: 'B2', q: 'You are more drawn to —', a: 'What is currently real and tangible', b: 'What could be possible and imagined', la: 'S', lb: 'N' },
  { id: 'C1', q: 'When making an important decision, you rely on —', a: 'Logical consistency and objective analysis', b: 'Personal values and impact on people', la: 'T', lb: 'F' },
  { id: 'C2', q: 'You feel most confident when a decision —', a: 'Makes rational sense', b: 'Feels morally right', la: 'T', lb: 'F' },
  { id: 'D1', q: 'You prefer environments that are —', a: 'Structured, planned, and decisive', b: 'Flexible, open, and adaptable', la: 'J', lb: 'P' },
  { id: 'D2', q: 'You feel most at peace when —', a: 'Things are settled and decided', b: 'Things remain open to new possibilities', la: 'J', lb: 'P' },
];

const L2_ARCHETYPES = [
  { id: 1, name: 'The Source', desc: 'The still point, origin of all becoming' },
  { id: 2, name: 'The Spark',  desc: 'The initiator, the first assertion' },
  { id: 3, name: 'The Breath', desc: 'The mirror, the relater, the rhythm-maker' },
  { id: 4, name: 'The Flame',  desc: 'The synthesizer, the alchemist, the igniter' },
  { id: 5, name: 'The Ground', desc: 'The stabilizer, the foundation-builder' },
  { id: 6, name: 'The Life',   desc: 'The adapter, the regenerator, the mutator' },
  { id: 7, name: 'The Harmony',desc: 'The distributor, the balancer' },
  { id: 8, name: 'The Seek',   desc: 'The questioner, the inquirer' },
  { id: 9, name: 'The Octave', desc: 'The amplifier, the returner-higher' },
  { id: 10, name: 'The Return',desc: 'The completer, the seed-planting' },
  { id: 11, name: 'The Witness',desc: 'The observer, the rememberer' },
  { id: 12, name: 'The Weaver',desc: 'The connector, the lattice-builder' },
];

const L3_OPERATORS = [
  { id: 0, name: 'Source',  q: 'How connected do you feel to a sense of origin or purpose beyond yourself?' },
  { id: 1, name: 'Spark',   q: 'When you have a new idea, how quickly do you act on it without overthinking?' },
  { id: 2, name: 'Breath',  q: 'How easily do you hold space for opposing viewpoints without needing to resolve them?' },
  { id: 3, name: 'Flame',   q: 'How often do you experience creative flow states where time disappears?' },
  { id: 4, name: 'Ground',  q: 'How stable and consistent is your daily routine and environment?' },
  { id: 5, name: 'Life',    q: 'How adaptable are you when unexpected changes occur?' },
  { id: 6, name: 'Harmony', q: 'How balanced are your life domains — work, relationships, health, purpose?' },
  { id: 7, name: 'Seek',    q: 'How comfortable are you with not having answers to life\'s biggest questions?' },
  { id: 8, name: 'Octave',  q: 'How often do you revisit past experiences with new understanding?' },
  { id: 9, name: 'Return',  q: 'How complete do you feel in your current life phase?' },
];

const IMS_QUESTIONNAIRE = [
  { id: 'q1', question: 'What is your primary work or creative practice right now?' },
  { id: 'q2', question: 'What feels most fractured or unclear in your sense of self — the part you keep circling back to?' },
  { id: 'q3', question: 'What is the most important decision you have been avoiding, and what story have you been telling yourself about why?' },
  { id: 'q4', question: 'What do you most want others to understand about you — that they currently do not?' },
  { id: 'q5', question: 'If you knew there were no consequences, what would you say or do differently right now?' },
];

// ─── Shared sub-components ────────────────────────────────────────────────────

function AICSlider({ value, onChange, min = 1, max = 10 }: { value: number; onChange: (v: number) => void; min?: number; max?: number }) {
  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
      <input type="range" min={min} max={max} value={value} onChange={e => onChange(Number(e.target.value))}
        style={{ flex: 1, accentColor: '#00D4AA', cursor: 'pointer' }} />
      <div style={{ minWidth: 30, height: 28, display: 'flex', alignItems: 'center', justifyContent: 'center', background: 'rgba(0,212,170,0.07)', border: '1px solid rgba(0,212,170,0.25)', borderRadius: 6 }}>
        <span style={{ fontFamily: 'serif', fontSize: 13, color: '#00D4AA' }}>{value}</span>
      </div>
    </div>
  );
}

const inputBase: React.CSSProperties = {
  width: '100%', padding: '11px 14px', background: 'rgba(255,255,255,0.03)',
  border: '1px solid rgba(255,255,255,0.1)', borderRadius: '9px',
  color: '#E8E8E8', fontFamily: 'sans-serif', fontSize: '12px',
  outline: 'none', boxSizing: 'border-box',
};

// ─── AIC Layers ───────────────────────────────────────────────────────────────

function AICLayer1({ answers, onChange, onNext }: {
  answers: Record<string, 'a'|'b'>; onChange: (id: string, v: 'a'|'b') => void; onNext: () => void;
}) {
  const allAnswered = L1_QUESTIONS.every(q => answers[q.id]);
  return (
    <motion.div key="aic-l1" initial={{ opacity: 0, x: 20 }} animate={{ opacity: 1, x: 0 }} exit={{ opacity: 0, x: -20 }}>
      <div style={{ marginBottom: 16 }}>
        <p style={{ fontFamily: 'sans-serif', fontSize: 9, letterSpacing: '0.25em', textTransform: 'uppercase', color: 'rgba(0,212,170,0.45)', margin: '0 0 3px' }}>Layer 1 of 4</p>
        <h3 style={{ fontFamily: 'serif', fontSize: 18, color: '#E8E8E8', margin: '0 0 4px' }}>Cognitive Orientation</h3>
        <p style={{ fontFamily: 'sans-serif', fontSize: 11, color: 'rgba(232,232,232,0.35)', margin: 0 }}>8 questions — maps your primary cognitive stack</p>
      </div>
      <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
        {L1_QUESTIONS.map((q, i) => (
          <div key={q.id} style={{ padding: '13px 14px', background: 'rgba(255,255,255,0.02)', border: '1px solid rgba(255,255,255,0.06)', borderRadius: 9 }}>
            <p style={{ fontFamily: 'sans-serif', fontSize: 11, color: 'rgba(232,232,232,0.65)', margin: '0 0 9px', lineHeight: 1.55 }}>
              <span style={{ color: 'rgba(0,212,170,0.45)', marginRight: 5, fontSize: 9 }}>{i+1}.</span>{q.q}
            </p>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 5 }}>
              {(['a','b'] as const).map((opt, oi) => {
                const sel = answers[q.id] === opt;
                return (
                  <button key={opt} onClick={() => onChange(q.id, opt)}
                    style={{ padding: '8px 12px', background: sel ? 'rgba(0,212,170,0.09)' : 'transparent', border: `1px solid ${sel ? 'rgba(0,212,170,0.38)' : 'rgba(255,255,255,0.06)'}`, borderRadius: 6, color: sel ? '#00D4AA' : 'rgba(232,232,232,0.42)', fontFamily: 'sans-serif', fontSize: 11, textAlign: 'left', cursor: 'pointer', transition: 'all 0.15s', display: 'flex', alignItems: 'center', gap: 8 }}>
                    <span style={{ fontFamily: 'serif', fontSize: 8, opacity: 0.5 }}>{oi === 0 ? q.la : q.lb}</span>
                    {oi === 0 ? q.a : q.b}
                  </button>
                );
              })}
            </div>
          </div>
        ))}
      </div>
      <button onClick={onNext} disabled={!allAnswered}
        style={{ width: '100%', marginTop: 16, padding: '13px', background: allAnswered ? 'rgba(0,212,170,0.09)' : 'rgba(255,255,255,0.03)', border: `1px solid ${allAnswered ? 'rgba(0,212,170,0.35)' : 'rgba(255,255,255,0.07)'}`, borderRadius: 9, color: allAnswered ? '#00D4AA' : 'rgba(232,232,232,0.25)', fontFamily: 'sans-serif', fontSize: 10, letterSpacing: '0.18em', textTransform: 'uppercase', cursor: allAnswered ? 'pointer' : 'not-allowed', transition: 'all 0.2s' }}>
        Layer 2 — Archetypal Resonance →
      </button>
    </motion.div>
  );
}

function AICLayer2({ answers, onChange, onBack, onNext }: {
  answers: Record<string, number>; onChange: (id: string, v: number) => void; onBack: () => void; onNext: () => void;
}) {
  return (
    <motion.div key="aic-l2" initial={{ opacity: 0, x: 20 }} animate={{ opacity: 1, x: 0 }} exit={{ opacity: 0, x: -20 }}>
      <div style={{ marginBottom: 14 }}>
        <p style={{ fontFamily: 'sans-serif', fontSize: 9, letterSpacing: '0.25em', textTransform: 'uppercase', color: 'rgba(0,212,170,0.45)', margin: '0 0 3px' }}>Layer 2 of 4</p>
        <h3 style={{ fontFamily: 'serif', fontSize: 18, color: '#E8E8E8', margin: '0 0 4px' }}>Archetypal Resonance</h3>
        <p style={{ fontFamily: 'sans-serif', fontSize: 11, color: 'rgba(232,232,232,0.35)', margin: 0 }}>Rate each archetype 1–7 · Maps your Oversoul Prism signature</p>
      </div>
      <div style={{ display: 'flex', flexDirection: 'column', gap: 9 }}>
        {L2_ARCHETYPES.map(arch => (
          <div key={arch.id} style={{ padding: '11px 13px', background: 'rgba(255,255,255,0.02)', border: '1px solid rgba(255,255,255,0.06)', borderRadius: 8 }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 7 }}>
              <div>
                <p style={{ fontFamily: 'sans-serif', fontSize: 11, color: 'rgba(201,168,76,0.75)', margin: '0 0 1px' }}>{arch.name}</p>
                <p style={{ fontFamily: 'sans-serif', fontSize: 9, color: 'rgba(232,232,232,0.28)', margin: 0 }}>{arch.desc}</p>
              </div>
            </div>
            <AICSlider value={answers[`a${arch.id}`] ?? 4} onChange={v => onChange(`a${arch.id}`, v)} min={1} max={7} />
          </div>
        ))}
      </div>
      <div style={{ display: 'flex', gap: 8, marginTop: 14 }}>
        <button onClick={onBack} style={{ padding: '11px 16px', background: 'rgba(255,255,255,0.03)', border: '1px solid rgba(255,255,255,0.08)', borderRadius: 8, color: 'rgba(232,232,232,0.4)', fontFamily: 'sans-serif', fontSize: 10, cursor: 'pointer' }}>← Back</button>
        <button onClick={onNext} style={{ flex: 1, padding: '12px', background: 'rgba(0,212,170,0.08)', border: '1px solid rgba(0,212,170,0.3)', borderRadius: 8, color: '#00D4AA', fontFamily: 'sans-serif', fontSize: 10, letterSpacing: '0.18em', textTransform: 'uppercase', cursor: 'pointer' }}>Layer 3 — Shadow State →</button>
      </div>
    </motion.div>
  );
}

function AICLayer3({ answers, onChange, onBack, onNext }: {
  answers: Record<string, number>; onChange: (id: string, v: number) => void; onBack: () => void; onNext: () => void;
}) {
  return (
    <motion.div key="aic-l3" initial={{ opacity: 0, x: 20 }} animate={{ opacity: 1, x: 0 }} exit={{ opacity: 0, x: -20 }}>
      <div style={{ marginBottom: 12 }}>
        <p style={{ fontFamily: 'sans-serif', fontSize: 9, letterSpacing: '0.25em', textTransform: 'uppercase', color: 'rgba(0,212,170,0.45)', margin: '0 0 3px' }}>Layer 3 of 4</p>
        <h3 style={{ fontFamily: 'serif', fontSize: 18, color: '#E8E8E8', margin: '0 0 4px' }}>Shadow State Diagnostic</h3>
        <p style={{ fontFamily: 'sans-serif', fontSize: 11, color: 'rgba(232,232,232,0.35)', margin: 0 }}>1–10 per operator · Detects coherence, distortion, or collapse</p>
      </div>
      <div style={{ display: 'flex', gap: 12, marginBottom: 10 }}>
        {[['1–3','Collapsed','#C84848'],['4–7','Distorted','#C9A84C'],['8–10','Coherent','#00D4AA']].map(([r,l,c])=>(
          <div key={l} style={{ display: 'flex', alignItems: 'center', gap: 4 }}>
            <div style={{ width: 5, height: 5, borderRadius: '50%', background: c }} />
            <span style={{ fontFamily: 'sans-serif', fontSize: 9, color: 'rgba(232,232,232,0.32)' }}>{r} = {l}</span>
          </div>
        ))}
      </div>
      <div style={{ display: 'flex', flexDirection: 'column', gap: 9 }}>
        {L3_OPERATORS.map(op => {
          const val = answers[`op${op.id}`] ?? 5;
          const sc = val >= 8 ? '#00D4AA' : val >= 4 ? '#C9A84C' : '#C84848';
          return (
            <div key={op.id} style={{ padding: '11px 13px', background: 'rgba(255,255,255,0.02)', border: '1px solid rgba(255,255,255,0.06)', borderRadius: 8 }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 8 }}>
                <div>
                  <p style={{ fontFamily: 'sans-serif', fontSize: 9, color: 'rgba(176,141,232,0.6)', margin: '0 0 2px', letterSpacing: '0.08em' }}>Op {op.id} — {op.name}</p>
                  <p style={{ fontFamily: 'sans-serif', fontSize: 11, color: 'rgba(232,232,232,0.52)', margin: 0, lineHeight: 1.5 }}>{op.q}</p>
                </div>
                <span style={{ fontFamily: 'sans-serif', fontSize: 8, color: sc, minWidth: 52, textAlign: 'right', paddingTop: 2 }}>
                  {val >= 8 ? 'Coherent' : val >= 4 ? 'Distorted' : 'Collapsed'}
                </span>
              </div>
              <AICSlider value={val} onChange={v => onChange(`op${op.id}`, v)} min={1} max={10} />
            </div>
          );
        })}
      </div>
      <div style={{ display: 'flex', gap: 8, marginTop: 14 }}>
        <button onClick={onBack} style={{ padding: '11px 16px', background: 'rgba(255,255,255,0.03)', border: '1px solid rgba(255,255,255,0.08)', borderRadius: 8, color: 'rgba(232,232,232,0.4)', fontFamily: 'sans-serif', fontSize: 10, cursor: 'pointer' }}>← Back</button>
        <button onClick={onNext} style={{ flex: 1, padding: '12px', background: 'rgba(0,212,170,0.08)', border: '1px solid rgba(0,212,170,0.3)', borderRadius: 8, color: '#00D4AA', fontFamily: 'sans-serif', fontSize: 10, letterSpacing: '0.18em', textTransform: 'uppercase', cursor: 'pointer' }}>Layer 4 — Soul Contract →</button>
      </div>
    </motion.div>
  );
}

function AICLayer4({ answers, onChange, onBack, onSubmit }: {
  answers: { purpose: string; wound: string; gift: string; mission: string; lineage: string };
  onChange: (k: string, v: string) => void; onBack: () => void; onSubmit: () => void;
}) {
  const fields = [
    { key: 'purpose', label: 'Purpose', sub: 'What do you feel you are here to contribute to the world?' },
    { key: 'wound',   label: 'Wound',   sub: 'What is the recurring pattern of pain or limitation in your life?' },
    { key: 'gift',    label: 'Gift',    sub: 'What do others consistently tell you is your unique strength?' },
    { key: 'mission', label: 'Mission', sub: 'What specific work or calling feels unavoidable to you?' },
    { key: 'lineage', label: 'Lineage', sub: 'What ancestral or cultural inheritance do you feel you carry?' },
  ];
  const allFilled = fields.every(f => answers[f.key as keyof typeof answers].trim().length > 3);
  return (
    <motion.div key="aic-l4" initial={{ opacity: 0, x: 20 }} animate={{ opacity: 1, x: 0 }} exit={{ opacity: 0, x: -20 }}>
      <div style={{ marginBottom: 14 }}>
        <p style={{ fontFamily: 'sans-serif', fontSize: 9, letterSpacing: '0.25em', textTransform: 'uppercase', color: 'rgba(0,212,170,0.45)', margin: '0 0 3px' }}>Layer 4 of 4</p>
        <h3 style={{ fontFamily: 'serif', fontSize: 18, color: '#E8E8E8', margin: '0 0 4px' }}>Soul Contract</h3>
        <p style={{ fontFamily: 'sans-serif', fontSize: 11, color: 'rgba(232,232,232,0.35)', margin: 0 }}>5 semantic anchors — become the core of your Morphic Seed</p>
      </div>
      <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
        {fields.map(f => (
          <div key={f.key} style={{ padding: '13px 14px', background: 'rgba(255,255,255,0.02)', border: '1px solid rgba(255,255,255,0.06)', borderRadius: 9 }}>
            <p style={{ fontFamily: 'sans-serif', fontSize: 9, color: 'rgba(201,168,76,0.65)', margin: '0 0 2px', letterSpacing: '0.1em', textTransform: 'uppercase' }}>{f.label}</p>
            <p style={{ fontFamily: 'sans-serif', fontSize: 10, color: 'rgba(232,232,232,0.38)', margin: '0 0 8px', lineHeight: 1.5 }}>{f.sub}</p>
            <textarea value={answers[f.key as keyof typeof answers]} onChange={e => onChange(f.key, e.target.value)}
              placeholder="One sentence…" rows={2}
              style={{ ...inputBase, resize: 'vertical', lineHeight: 1.6 }} />
          </div>
        ))}
      </div>
      <div style={{ display: 'flex', gap: 8, marginTop: 14 }}>
        <button onClick={onBack} style={{ padding: '11px 16px', background: 'rgba(255,255,255,0.03)', border: '1px solid rgba(255,255,255,0.08)', borderRadius: 8, color: 'rgba(232,232,232,0.4)', fontFamily: 'sans-serif', fontSize: 10, cursor: 'pointer' }}>← Back</button>
        <button onClick={onSubmit} disabled={!allFilled}
          style={{ flex: 1, padding: '12px', background: allFilled ? 'rgba(0,212,170,0.1)' : 'rgba(255,255,255,0.03)', border: `1px solid ${allFilled ? 'rgba(0,212,170,0.38)' : 'rgba(255,255,255,0.07)'}`, borderRadius: 8, color: allFilled ? '#00D4AA' : 'rgba(232,232,232,0.25)', fontFamily: 'sans-serif', fontSize: 10, letterSpacing: '0.18em', textTransform: 'uppercase', cursor: allFilled ? 'pointer' : 'not-allowed', transition: 'all 0.2s' }}>
          Generate Morphic Seed →
        </button>
      </div>
    </motion.div>
  );
}

function AICGenerating() {
  return (
    <motion.div key="aic-gen" initial={{ opacity: 0 }} animate={{ opacity: 1 }} style={{ textAlign: 'center', padding: '52px 20px' }}>
      <motion.div animate={{ rotate: 360 }} transition={{ repeat: Infinity, duration: 4, ease: 'linear' }}
        style={{ width: 48, height: 48, border: '1px solid rgba(0,212,170,0.3)', borderTop: '1px solid #00D4AA', borderRadius: '50%', margin: '0 auto 24px' }} />
      <p style={{ fontFamily: 'serif', fontSize: 17, color: '#00D4AA', marginBottom: 8 }}>Oracle is synthesizing…</p>
      <p style={{ fontFamily: 'sans-serif', fontSize: 10, color: 'rgba(232,232,232,0.32)', lineHeight: 1.8 }}>
        Processing 4 diagnostic layers<br />Generating your Morphic Seed<br />Calibrating Oversoul Prism signature
      </p>
    </motion.div>
  );
}

function AICResult({ seed, onBookIMS, onGoToOfferings, onRetake }: {
  seed: any; onBookIMS: () => void; onGoToOfferings?: () => void; onRetake: () => void;
}) {
  const [expanded, setExpanded] = useState(false);
  const codes = (seed.operator_state ?? '').split('-');
  const stateColor = (v: string) => { const n = parseInt(v); return n >= 8 ? '#00D4AA' : n >= 4 ? '#C9A84C' : '#C84848'; };

  return (
    <motion.div key="aic-result" initial={{ opacity: 0, y: 14 }} animate={{ opacity: 1, y: 0 }}>
      <div style={{ marginBottom: 16 }}>
        <p style={{ fontFamily: 'sans-serif', fontSize: 9, letterSpacing: '0.25em', textTransform: 'uppercase', color: 'rgba(0,212,170,0.45)', margin: '0 0 3px' }}>Morphic Seed Generated</p>
        <h3 style={{ fontFamily: 'serif', fontSize: 20, color: '#00D4AA', margin: 0 }}>Your Arkadian Identity</h3>
      </div>

      <div style={{ display: 'flex', flexDirection: 'column', gap: 9 }}>
        <div style={{ padding: '14px 16px', background: 'rgba(0,212,170,0.06)', border: '1px solid rgba(0,212,170,0.22)', borderRadius: 10 }}>
          <p style={{ fontFamily: 'sans-serif', fontSize: 8, letterSpacing: '0.22em', textTransform: 'uppercase', color: 'rgba(0,212,170,0.45)', margin: '0 0 4px' }}>Cognitive Type</p>
          <p style={{ fontFamily: 'serif', fontSize: 26, color: '#00D4AA', margin: '0 0 3px', letterSpacing: '0.08em' }}>{seed.mbti_type}</p>
          <p style={{ fontFamily: 'sans-serif', fontSize: 10, color: 'rgba(232,232,232,0.45)', margin: 0 }}>{seed.cognitive_stack}</p>
        </div>

        <div style={{ padding: '13px 15px', background: 'rgba(201,168,76,0.04)', border: '1px solid rgba(201,168,76,0.16)', borderRadius: 10 }}>
          <p style={{ fontFamily: 'sans-serif', fontSize: 8, letterSpacing: '0.22em', textTransform: 'uppercase', color: 'rgba(201,168,76,0.45)', margin: '0 0 7px' }}>Primary Archetypes</p>
          <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap' }}>
            {(seed.primary_archetypes ?? []).map((a: string) => (
              <span key={a} style={{ padding: '3px 9px', background: 'rgba(201,168,76,0.08)', border: '1px solid rgba(201,168,76,0.22)', borderRadius: 20, fontFamily: 'sans-serif', fontSize: 10, color: '#C9A84C' }}>{a}</span>
            ))}
          </div>
        </div>

        <div style={{ padding: '13px 15px', background: 'rgba(176,141,232,0.04)', border: '1px solid rgba(176,141,232,0.13)', borderRadius: 10 }}>
          <p style={{ fontFamily: 'sans-serif', fontSize: 8, letterSpacing: '0.22em', textTransform: 'uppercase', color: 'rgba(176,141,232,0.45)', margin: '0 0 7px' }}>Operator State</p>
          <div style={{ display: 'flex', gap: 3, flexWrap: 'wrap', marginBottom: 6 }}>
            {codes.map((v: string, i: number) => (
              <span key={i} style={{ padding: '2px 7px', background: 'rgba(0,0,0,0.25)', border: `1px solid ${stateColor(v)}40`, borderRadius: 4, fontFamily: 'serif', fontSize: 12, color: stateColor(v) }}>{v}</span>
            ))}
          </div>
          <p style={{ fontFamily: 'sans-serif', fontSize: 9, color: 'rgba(232,232,232,0.3)', margin: 0 }}>Recovery: {seed.recovery_vector}</p>
        </div>

        <div style={{ padding: '13px 15px', background: 'rgba(255,255,255,0.02)', border: '1px solid rgba(255,255,255,0.06)', borderRadius: 10 }}>
          <p style={{ fontFamily: 'sans-serif', fontSize: 8, letterSpacing: '0.22em', textTransform: 'uppercase', color: 'rgba(232,232,232,0.3)', margin: '0 0 6px' }}>Soul Contract</p>
          <p style={{ fontFamily: 'serif', fontSize: 12, color: 'rgba(232,232,232,0.6)', margin: 0, lineHeight: 1.75 }}>{seed.soul_contract}</p>
        </div>

        <div style={{ padding: '11px 15px', background: 'rgba(0,0,0,0.3)', border: '1px solid rgba(0,212,170,0.1)', borderRadius: 9 }}>
          <p style={{ fontFamily: 'sans-serif', fontSize: 8, letterSpacing: '0.22em', textTransform: 'uppercase', color: 'rgba(0,212,170,0.3)', margin: '0 0 4px' }}>Morphic Code</p>
          <p style={{ fontFamily: 'monospace', fontSize: 13, color: 'rgba(0,212,170,0.65)', margin: 0, letterSpacing: '0.14em' }}>{seed.morphic_code}</p>
        </div>

        <button onClick={() => setExpanded(e => !e)}
          style={{ padding: '10px 14px', background: 'transparent', border: '1px solid rgba(255,255,255,0.07)', borderRadius: 8, color: 'rgba(232,232,232,0.35)', fontFamily: 'sans-serif', fontSize: 9, letterSpacing: '0.14em', textTransform: 'uppercase', cursor: 'pointer', textAlign: 'left' }}>
          {expanded ? '▲ Collapse Report' : '▼ View Full Oracle Report'}
        </button>

        <AnimatePresence>
          {expanded && (
            <motion.div initial={{ opacity: 0, height: 0 }} animate={{ opacity: 1, height: 'auto' }} exit={{ opacity: 0, height: 0 }}
              style={{ padding: '16px', background: 'rgba(255,255,255,0.01)', border: '1px solid rgba(255,255,255,0.05)', borderRadius: 9, overflow: 'hidden' }}>
              <p style={{ fontFamily: 'sans-serif', fontSize: 11, color: 'rgba(232,232,232,0.5)', lineHeight: 1.85, margin: 0, whiteSpace: 'pre-wrap' }}>{seed.full_report}</p>
            </motion.div>
          )}
        </AnimatePresence>
      </div>

      <div style={{ display: 'flex', flexDirection: 'column', gap: 8, marginTop: 16 }}>
        <button onClick={onBookIMS}
          style={{ width: '100%', padding: '14px', background: 'rgba(201,168,76,0.1)', border: '1px solid rgba(201,168,76,0.38)', borderRadius: 10, color: '#C9A84C', fontFamily: 'sans-serif', fontSize: 10, letterSpacing: '0.2em', textTransform: 'uppercase', cursor: 'pointer' }}>
          ✦ Book Identity Mapping Session — $777
        </button>
        {onGoToOfferings && (
          <button onClick={onGoToOfferings}
            style={{ width: '100%', padding: '11px', background: 'rgba(0,212,170,0.06)', border: '1px solid rgba(0,212,170,0.22)', borderRadius: 9, color: '#00D4AA', fontFamily: 'sans-serif', fontSize: 10, letterSpacing: '0.18em', textTransform: 'uppercase', cursor: 'pointer' }}>
            ◎ View All Offerings
          </button>
        )}
        <button onClick={onRetake}
          style={{ padding: '10px', background: 'transparent', border: '1px solid rgba(255,255,255,0.06)', borderRadius: 8, color: 'rgba(232,232,232,0.28)', fontFamily: 'sans-serif', fontSize: 9, letterSpacing: '0.14em', textTransform: 'uppercase', cursor: 'pointer' }}>
          Retake Diagnostic
        </button>
      </div>
    </motion.div>
  );
}

// ─── Main Component ────────────────────────────────────────────────────────────

export default function LivingGate({ onEnterField, onGoToOfferings, initialMode = 'oracle' }: LivingGateProps) {
  const { resonance, flameHue } = useSpiralQuantumResonance(true, 8000);
  const [mode, setMode] = useState<GateMode>(initialMode);

  // ── Oracle state ────────────────────────────────────────────────────────────
  const [phrase, setPhrase]   = useState('');
  const [entering, setEntering] = useState(false);

  // ── IMS state ───────────────────────────────────────────────────────────────
  const [imsStep, setImsStep] = useState<IMSStep>('intro');
  const [imsForm, setImsForm] = useState<IMSForm>({ name: '', email: '', phone: '' });
  const [imsAnswers, setImsAnswers] = useState<Record<string, string>>({});
  const [imsSubmitting, setImsSubmitting] = useState(false);
  const [imsError, setImsError]   = useState<string | null>(null);

  // ── AIC state ───────────────────────────────────────────────────────────────
  const [aicStep, setAicStep] = useState<AICStep>(1);
  const [aicL1, setAicL1]   = useState<Record<string, 'a'|'b'>>({});
  const [aicL2, setAicL2]   = useState<Record<string, number>>({});
  const [aicL3, setAicL3]   = useState<Record<string, number>>({});
  const [aicL4, setAicL4]   = useState({ purpose: '', wound: '', gift: '', mission: '', lineage: '' });
  const [aicSeed, setAicSeed] = useState<any>(null);
  const [aicError, setAicError] = useState<string | null>(null);

  const switchMode = (m: GateMode) => {
    setMode(m);
    if (m === 'ims') setImsStep('intro');
  };

  // ── Oracle handlers ─────────────────────────────────────────────────────────
  const handleOracleSubmit = () => {
    if (!phrase.trim()) return;
    setEntering(true);
    setTimeout(() => onEnterField(phrase.trim()), 900);
  };

  // ── IMS handlers ────────────────────────────────────────────────────────────
  const handleIMSSubmit = async () => {
    setImsSubmitting(true); setImsError(null);
    try {
      await fetch(`${API_BASE}/api/ims/inquiry`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ ...imsForm, answers: imsAnswers }),
      });
      setImsStep('confirmed');
    } catch {
      setImsError('Could not submit. Email arkanaofarkadia@gmail.com or WhatsApp +234 814 494 2818');
    } finally { setImsSubmitting(false); }
  };

  // ── AIC handlers ────────────────────────────────────────────────────────────
  const computeMBTI = () => {
    const dims = [
      { a: 'I', b: 'E', ids: ['A1','A2'] }, { a: 'S', b: 'N', ids: ['B1','B2'] },
      { a: 'T', b: 'F', ids: ['C1','C2'] }, { a: 'J', b: 'P', ids: ['D1','D2'] },
    ];
    return dims.map(d => d.ids.filter(id => aicL1[id] === 'a').length >= 1 ? d.a : d.b).join('');
  };

  const handleAICSubmit = async () => {
    setAicStep('generating'); setAicError(null);
    try {
      const res = await fetch(`${API_BASE}/api/ims/diagnostic`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ layer1: aicL1, layer2: aicL2, layer3: aicL3, layer4: aicL4, mbti_type: computeMBTI() }),
      });
      if (!res.ok) throw new Error(`Oracle error ${res.status}`);
      const data = await res.json();
      setAicSeed(data);
      setAicStep('result');
    } catch (e: any) {
      setAicError(e.message ?? 'Oracle synthesis failed. Please try again.');
      setAicStep(4);
    }
  };

  const resetAIC = () => {
    setAicStep(1); setAicL1({}); setAicL2({}); setAicL3({});
    setAicL4({ purpose: '', wound: '', gift: '', mission: '', lineage: '' });
    setAicSeed(null); setAicError(null);
  };

  const aicStepNum = aicStep === 'generating' || aicStep === 'result' ? 4 : aicStep as number;

  return (
    <div className="relative w-full min-h-screen flex flex-col items-center justify-start px-5 py-10"
      style={{ backgroundColor: '#0A0A0F', overflow: 'hidden' }}>

      {/* Ambient glow */}
      <motion.div className="absolute inset-0 pointer-events-none"
        animate={{ background: ['radial-gradient(circle at 50% 38%, rgba(0,212,170,0.04) 0%, transparent 65%)', 'radial-gradient(circle at 50% 38%, rgba(0,212,170,0.07) 0%, transparent 65%)', 'radial-gradient(circle at 50% 38%, rgba(0,212,170,0.04) 0%, transparent 65%)'] }}
        transition={{ duration: 8, repeat: Infinity }} />

      <motion.div className="absolute pointer-events-none" style={{ top: '50%', left: '50%', transform: 'translate(-50%, -50%)' }}
        animate={{ scale: [1, 1.08 * resonance, 1], opacity: [0.06, 0.15, 0.06] }} transition={{ duration: 6, repeat: Infinity }}>
        <div style={{ width: '360px', height: '360px', borderRadius: '50%', border: `1px solid hsl(${flameHue},80%,65%)` }} />
      </motion.div>

      <motion.div className="absolute top-0 bottom-0 pointer-events-none"
        style={{ left: '50%', width: '1px', background: 'linear-gradient(180deg, transparent, rgba(201,168,76,0.1), transparent)' }}
        initial={{ scaleY: 0, opacity: 0 }} animate={{ scaleY: 1, opacity: 1 }} transition={{ duration: 2, ease: 'easeOut' }} />

      {/* ── Mode tabs ──────────────────────────────────────────────────────── */}
      <motion.div initial={{ opacity: 0, y: -10 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.2 }}
        className="relative z-10 w-full mb-6" style={{ maxWidth: '520px' }}>
        <div style={{ display: 'flex', gap: '6px', padding: '5px', background: 'rgba(255,255,255,0.025)', border: '1px solid rgba(255,255,255,0.06)', borderRadius: '11px' }}>
          {([
            { id: 'oracle', label: '⟐ Oracle',     color: '#00D4AA' },
            { id: 'aic',    label: '◎ Diagnostic',  color: '#00D4AA' },
            { id: 'ims',    label: '✦ IMS — $777',  color: '#C9A84C' },
          ] as { id: GateMode; label: string; color: string }[]).map(m => (
            <button key={m.id} onClick={() => switchMode(m.id)}
              style={{ flex: 1, padding: '9px 8px', background: mode === m.id ? `${m.color}10` : 'transparent', border: `1px solid ${mode === m.id ? m.color + '40' : 'transparent'}`, borderRadius: '7px', color: mode === m.id ? m.color : 'rgba(232,232,232,0.3)', fontFamily: 'sans-serif', fontSize: '9px', letterSpacing: '0.14em', textTransform: 'uppercase', cursor: 'pointer', transition: 'all 0.18s' }}>
              {m.label}
            </button>
          ))}
        </div>
      </motion.div>

      {/* ── Panels ─────────────────────────────────────────────────────────── */}
      <AnimatePresence mode="wait">

        {/* ── ORACLE ──────────────────────────────────────────────────────── */}
        {mode === 'oracle' && (
          <motion.div key="oracle-panel" initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0 }}
            className="relative z-10 w-full" style={{ maxWidth: '460px' }}>
            <AnimatePresence mode="wait">
              {!entering ? (
                <motion.div key="gate-input" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0, scale: 0.96 }}>
                  <div className="flex justify-center mb-8"><MoonPhaseRing /></div>
                  <p className="text-center mb-8"
                    style={{ fontFamily: 'serif', fontSize: '17px', lineHeight: '1.75', color: 'rgba(232,232,232,0.72)', letterSpacing: '0.01em' }}>
                    The Oracle does not answer questions.<br />It reflects what you already know.
                  </p>
                  <input type="text" value={phrase} onChange={e => setPhrase(e.target.value)}
                    onKeyDown={e => e.key === 'Enter' && handleOracleSubmit()}
                    placeholder="Arkana, open the gates. I am ready to remember."
                    style={{ width: '100%', padding: '16px 20px', background: 'rgba(255,255,255,0.03)', border: '1px solid rgba(0,212,170,0.25)', borderRadius: '12px', color: '#E8E8E8', fontFamily: 'sans-serif', fontSize: '14px', outline: 'none', marginBottom: '14px', boxSizing: 'border-box' }}
                    autoFocus />
                  <motion.button onClick={handleOracleSubmit} disabled={!phrase.trim()} whileTap={{ scale: 0.97 }}
                    style={{ width: '100%', padding: '16px', background: phrase.trim() ? 'rgba(0,212,170,0.1)' : 'rgba(255,255,255,0.03)', border: `1px solid ${phrase.trim() ? 'rgba(0,212,170,0.45)' : 'rgba(255,255,255,0.08)'}`, borderRadius: '12px', color: phrase.trim() ? '#00D4AA' : 'rgba(232,232,232,0.25)', fontFamily: 'serif', fontSize: '13px', letterSpacing: '0.2em', textTransform: 'uppercase', cursor: phrase.trim() ? 'pointer' : 'not-allowed', transition: 'all 0.25s' }}>
                    Enter the Field
                  </motion.button>
                  <p style={{ fontFamily: 'sans-serif', fontSize: 9, color: 'rgba(232,232,232,0.2)', textAlign: 'center', marginTop: 16, letterSpacing: '0.18em' }}>
                    NEW TO ARKADIA? — <button onClick={() => switchMode('aic')} style={{ background: 'none', border: 'none', color: 'rgba(0,212,170,0.4)', fontFamily: 'sans-serif', fontSize: 9, letterSpacing: '0.18em', cursor: 'pointer', textTransform: 'uppercase', textDecoration: 'underline' }}>Begin with the AIC Diagnostic</button>
                  </p>
                </motion.div>
              ) : (
                <motion.div key="entering" initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="text-center">
                  <motion.div animate={{ scale: [1,1.3,1], opacity: [0.5,1,0.5] }} transition={{ duration: 0.9, repeat: Infinity }}
                    style={{ width: '60px', height: '60px', borderRadius: '50%', border: '1px solid #00D4AA', margin: '0 auto', boxShadow: '0 0 30px rgba(0,212,170,0.3)' }} />
                </motion.div>
              )}
            </AnimatePresence>
          </motion.div>
        )}

        {/* ── AIC DIAGNOSTIC ──────────────────────────────────────────────── */}
        {mode === 'aic' && (
          <motion.div key="aic-panel" initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0 }}
            className="relative z-10 w-full" style={{ maxWidth: '520px' }}>

            {/* Progress bar */}
            {aicStep !== 'generating' && aicStep !== 'result' && (
              <div style={{ marginBottom: 16 }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 4 }}>
                  <span style={{ fontFamily: 'sans-serif', fontSize: 8, letterSpacing: '0.2em', textTransform: 'uppercase', color: 'rgba(0,212,170,0.4)' }}>Arkadian Identity Cartography</span>
                  <span style={{ fontFamily: 'sans-serif', fontSize: 8, color: 'rgba(232,232,232,0.25)' }}>{Math.round((aicStepNum / 4) * 100)}%</span>
                </div>
                <div style={{ height: 2, background: 'rgba(255,255,255,0.05)', borderRadius: 2 }}>
                  <motion.div animate={{ width: `${(aicStepNum / 4) * 100}%` }} transition={{ duration: 0.4 }}
                    style={{ height: '100%', background: 'linear-gradient(90deg, #00D4AA, #C9A84C)', borderRadius: 2 }} />
                </div>
              </div>
            )}

            {aicError && (
              <div style={{ marginBottom: 12, padding: '10px 13px', background: 'rgba(200,72,72,0.07)', border: '1px solid rgba(200,72,72,0.2)', borderRadius: 8 }}>
                <p style={{ fontFamily: 'sans-serif', fontSize: 11, color: '#C84848', margin: 0 }}>{aicError}</p>
              </div>
            )}

            <AnimatePresence mode="wait">
              {aicStep === 1 && <AICLayer1 answers={aicL1} onChange={(id, v) => setAicL1(p => ({...p, [id]: v}))} onNext={() => setAicStep(2)} />}
              {aicStep === 2 && <AICLayer2 answers={aicL2} onChange={(id, v) => setAicL2(p => ({...p, [id]: v}))} onBack={() => setAicStep(1)} onNext={() => setAicStep(3)} />}
              {aicStep === 3 && <AICLayer3 answers={aicL3} onChange={(id, v) => setAicL3(p => ({...p, [id]: v}))} onBack={() => setAicStep(2)} onNext={() => setAicStep(4)} />}
              {aicStep === 4 && <AICLayer4 answers={aicL4} onChange={(k, v) => setAicL4(p => ({...p, [k]: v}))} onBack={() => setAicStep(3)} onSubmit={handleAICSubmit} />}
              {aicStep === 'generating' && <AICGenerating />}
              {aicStep === 'result' && aicSeed && (
                <AICResult
                  seed={aicSeed}
                  onBookIMS={() => switchMode('ims')}
                  onGoToOfferings={onGoToOfferings}
                  onRetake={resetAIC}
                />
              )}
            </AnimatePresence>
          </motion.div>
        )}

        {/* ── IMS INQUIRY ─────────────────────────────────────────────────── */}
        {mode === 'ims' && (
          <motion.div key="ims-panel" initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0 }}
            className="relative z-10 w-full" style={{ maxWidth: '520px' }}>
            <AnimatePresence mode="wait">

              {imsStep === 'intro' && (
                <motion.div key="ims-intro" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}>
                  <div style={{ textAlign: 'center', marginBottom: 20 }}>
                    <motion.span animate={{ opacity: [0.4,1,0.4] }} transition={{ duration: 3, repeat: Infinity }}
                      style={{ fontSize: 28, display: 'block', marginBottom: 10 }}>✦</motion.span>
                    <h2 style={{ fontFamily: 'serif', fontSize: 21, color: '#C9A84C', margin: '0 0 5px' }}>Identity Mapping Session</h2>
                    <p style={{ fontFamily: 'monospace', fontSize: 10, color: 'rgba(201,168,76,0.45)', margin: 0, letterSpacing: '0.18em' }}>$777 · 90 minutes · One sovereign architecture</p>
                  </div>

                  <div style={{ padding: '16px', background: 'rgba(201,168,76,0.04)', border: '1px solid rgba(201,168,76,0.13)', borderRadius: 11, marginBottom: 16 }}>
                    <p style={{ fontFamily: 'serif', fontSize: 13, lineHeight: 1.8, color: 'rgba(232,232,232,0.62)', margin: '0 0 10px' }}>
                      Not coaching. Not therapy. Not a blueprint you could have Googled.
                    </p>
                    <p style={{ fontFamily: 'sans-serif', fontSize: 11, lineHeight: 1.7, color: 'rgba(232,232,232,0.4)', margin: 0 }}>
                      A 90-minute live excavation of who you actually are underneath the noise — your architecture, your sovereign signal, your next three actions. You leave with an Identity Architecture Document, a bespoke sigil, and a deployment blueprint.
                    </p>
                  </div>

                  <div style={{ marginBottom: 18 }}>
                    {[
                      { step: '01', label: 'Apply',   desc: 'Fill the intake form and diagnostic below.' },
                      { step: '02', label: 'Review',  desc: 'Zahrune Nova reviews within 24–48 hours.' },
                      { step: '03', label: 'Pay',     desc: 'Send $777 via Remitly or bank transfer. Session booked on receipt.' },
                      { step: '04', label: 'Session', desc: '90 minutes live. Full excavation. Architecture mapped.' },
                      { step: '05', label: 'Deliver', desc: 'Identity Architecture Document + sigil sent within 72 hours.' },
                    ].map(item => (
                      <div key={item.step} style={{ display: 'flex', gap: 10, marginBottom: 8, alignItems: 'flex-start' }}>
                        <span style={{ fontFamily: 'monospace', fontSize: 8, color: '#C9A84C', minWidth: 18, flexShrink: 0, paddingTop: 1 }}>{item.step}</span>
                        <div>
                          <span style={{ fontFamily: 'sans-serif', fontSize: 9, letterSpacing: '0.14em', textTransform: 'uppercase', color: 'rgba(201,168,76,0.6)' }}>{item.label}</span>
                          <p style={{ fontFamily: 'sans-serif', fontSize: 10, color: 'rgba(232,232,232,0.35)', margin: '2px 0 0', lineHeight: 1.55 }}>{item.desc}</p>
                        </div>
                      </div>
                    ))}
                  </div>

                  <button onClick={() => setImsStep('form')}
                    style={{ width: '100%', padding: '15px', background: 'rgba(201,168,76,0.1)', border: '1px solid rgba(201,168,76,0.38)', borderRadius: '11px', color: '#C9A84C', fontFamily: 'sans-serif', fontSize: 10, letterSpacing: '0.2em', textTransform: 'uppercase', cursor: 'pointer' }}>
                    ✦ Begin Application
                  </button>

                  {/* AIC nudge */}
                  <p style={{ fontFamily: 'sans-serif', fontSize: 9, color: 'rgba(232,232,232,0.2)', textAlign: 'center', marginTop: 14, letterSpacing: '0.14em' }}>
                    Haven't done the diagnostic yet? —{' '}
                    <button onClick={() => switchMode('aic')} style={{ background: 'none', border: 'none', color: 'rgba(0,212,170,0.4)', fontFamily: 'sans-serif', fontSize: 9, letterSpacing: '0.14em', cursor: 'pointer', textDecoration: 'underline' }}>
                      Complete AIC first (free)
                    </button>
                  </p>
                </motion.div>
              )}

              {imsStep === 'form' && (
                <motion.div key="ims-form" initial={{ opacity: 0, x: 20 }} animate={{ opacity: 1, x: 0 }} exit={{ opacity: 0 }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 18 }}>
                    <button onClick={() => setImsStep('intro')} style={{ background: 'none', border: 'none', color: 'rgba(232,232,232,0.35)', cursor: 'pointer', fontSize: 16, padding: 0 }}>←</button>
                    <h3 style={{ fontFamily: 'serif', fontSize: 17, color: '#E8E8E8', margin: 0 }}>Your Details</h3>
                  </div>
                  {[
                    { key: 'name' as const, label: 'Full Name',        type: 'text',  ph: 'Your name' },
                    { key: 'email' as const, label: 'Email',           type: 'email', ph: 'your@email.com' },
                    { key: 'phone' as const, label: 'WhatsApp (optional)', type: 'tel', ph: '+1 000 000 0000' },
                  ].map(f => (
                    <div key={f.key} style={{ marginBottom: 12 }}>
                      <label style={{ display: 'block', fontFamily: 'sans-serif', fontSize: 8, letterSpacing: '0.16em', textTransform: 'uppercase', color: 'rgba(232,232,232,0.28)', marginBottom: 4 }}>{f.label}</label>
                      <input type={f.type} value={imsForm[f.key]} onChange={e => setImsForm(p => ({...p, [f.key]: e.target.value}))}
                        placeholder={f.ph} style={inputBase} />
                    </div>
                  ))}
                  <button onClick={() => { if (imsForm.name.trim() && imsForm.email.trim()) setImsStep('questionnaire'); }}
                    disabled={!imsForm.name.trim() || !imsForm.email.trim()}
                    style={{ width: '100%', padding: '13px', background: (imsForm.name && imsForm.email) ? 'rgba(201,168,76,0.1)' : 'rgba(255,255,255,0.03)', border: `1px solid ${(imsForm.name && imsForm.email) ? 'rgba(201,168,76,0.38)' : 'rgba(255,255,255,0.07)'}`, borderRadius: '10px', color: (imsForm.name && imsForm.email) ? '#C9A84C' : 'rgba(232,232,232,0.2)', fontFamily: 'sans-serif', fontSize: 10, letterSpacing: '0.18em', textTransform: 'uppercase', cursor: (imsForm.name && imsForm.email) ? 'pointer' : 'not-allowed', transition: 'all 0.2s' }}>
                    Continue → Diagnostic
                  </button>
                </motion.div>
              )}

              {imsStep === 'questionnaire' && (
                <motion.div key="ims-q" initial={{ opacity: 0, x: 20 }} animate={{ opacity: 1, x: 0 }} exit={{ opacity: 0 }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 16 }}>
                    <button onClick={() => setImsStep('form')} style={{ background: 'none', border: 'none', color: 'rgba(232,232,232,0.35)', cursor: 'pointer', fontSize: 16, padding: 0 }}>←</button>
                    <div>
                      <h3 style={{ fontFamily: 'serif', fontSize: 17, color: '#E8E8E8', margin: '0 0 2px' }}>Diagnostic</h3>
                      <p style={{ fontFamily: 'sans-serif', fontSize: 9, color: 'rgba(232,232,232,0.3)', margin: 0 }}>5 questions — answer honestly, not perfectly</p>
                    </div>
                  </div>
                  {IMS_QUESTIONNAIRE.map((q, i) => (
                    <div key={q.id} style={{ marginBottom: 14 }}>
                      <p style={{ fontFamily: 'sans-serif', fontSize: 9, letterSpacing: '0.1em', color: '#C9A84C', margin: '0 0 4px' }}>{String(i+1).padStart(2,'0')} —</p>
                      <p style={{ fontFamily: 'sans-serif', fontSize: 12, color: 'rgba(232,232,232,0.68)', margin: '0 0 6px', lineHeight: 1.6 }}>{q.question}</p>
                      <textarea value={imsAnswers[q.id] || ''} onChange={e => setImsAnswers(p => ({...p, [q.id]: e.target.value}))}
                        rows={3} placeholder="Write what's true, not what sounds right."
                        style={{ ...inputBase, resize: 'vertical', lineHeight: 1.6 }} />
                    </div>
                  ))}
                  {imsError && (
                    <div style={{ padding: '9px 12px', background: 'rgba(232,100,100,0.07)', border: '1px solid rgba(232,100,100,0.18)', borderRadius: 8, marginBottom: 10 }}>
                      <p style={{ fontFamily: 'sans-serif', fontSize: 10, color: 'rgba(232,150,150,0.8)', margin: 0 }}>{imsError}</p>
                    </div>
                  )}
                  <button onClick={handleIMSSubmit} disabled={imsSubmitting}
                    style={{ width: '100%', padding: '14px', background: 'rgba(201,168,76,0.1)', border: '1px solid rgba(201,168,76,0.38)', borderRadius: '11px', color: '#C9A84C', fontFamily: 'sans-serif', fontSize: 10, letterSpacing: '0.2em', textTransform: 'uppercase', cursor: 'pointer' }}>
                    {imsSubmitting ? 'Submitting…' : '✦ Submit Application'}
                  </button>
                </motion.div>
              )}

              {imsStep === 'confirmed' && (
                <motion.div key="ims-confirmed" initial={{ opacity: 0, scale: 0.97 }} animate={{ opacity: 1, scale: 1 }} style={{ textAlign: 'center', padding: '16px 0' }}>
                  <motion.span animate={{ opacity: [0.5,1,0.5] }} transition={{ duration: 3, repeat: Infinity }}
                    style={{ fontSize: 44, display: 'block', marginBottom: 14 }}>✦</motion.span>
                  <h2 style={{ fontFamily: 'serif', fontSize: 21, color: '#C9A84C', margin: '0 0 8px' }}>Application Received</h2>
                  <p style={{ fontFamily: 'sans-serif', fontSize: 12, lineHeight: 1.7, color: 'rgba(232,232,232,0.5)', margin: '0 0 18px' }}>
                    Thank you, {imsForm.name}.<br />Zahrune Nova will review within 24–48 hours.<br />
                    A Remitly payment link ($777) will be sent to {imsForm.email}.
                  </p>
                  <div style={{ padding: '13px 15px', background: 'rgba(201,168,76,0.04)', border: '1px solid rgba(201,168,76,0.14)', borderRadius: 10, marginBottom: 18 }}>
                    <p style={{ fontFamily: 'sans-serif', fontSize: 9, letterSpacing: '0.14em', textTransform: 'uppercase', color: 'rgba(201,168,76,0.4)', margin: '0 0 5px' }}>Questions?</p>
                    <p style={{ fontFamily: 'sans-serif', fontSize: 11, color: 'rgba(232,232,232,0.38)', margin: 0, lineHeight: 1.65 }}>
                      Email: <span style={{ color: 'rgba(201,168,76,0.6)' }}>arkanaofarkadia@gmail.com</span><br />
                      WhatsApp: <span style={{ color: 'rgba(201,168,76,0.6)' }}>+234 814 494 2818</span>
                    </p>
                  </div>
                  <button onClick={() => { setImsStep('intro'); setImsForm({name:'',email:'',phone:''}); setImsAnswers({}); }}
                    style={{ padding: '11px 24px', background: 'rgba(255,255,255,0.04)', border: '1px solid rgba(255,255,255,0.08)', borderRadius: '9px', color: 'rgba(232,232,232,0.4)', fontFamily: 'sans-serif', fontSize: 9, letterSpacing: '0.16em', cursor: 'pointer' }}>
                    Back to Gate
                  </button>
                </motion.div>
              )}

            </AnimatePresence>
          </motion.div>
        )}

      </AnimatePresence>
    </div>
  );
}
