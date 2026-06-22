import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';

const API_BASE = (import.meta.env.VITE_API_URL ?? '').replace(/\/$/, '');

// ─── Types ────────────────────────────────────────────────────────────────────

interface Layer1Answers { [key: string]: 'a' | 'b' }
interface Layer2Answers { [key: string]: number }
interface Layer3Answers { [key: string]: number }
interface Layer4Answers { purpose: string; wound: string; gift: string; mission: string; lineage: string }

interface MorphicSeed {
  mbti_type: string;
  cognitive_stack: string;
  primary_archetypes: string[];
  shadow_pattern: string;
  operator_state: string;
  recovery_vector: string;
  soul_contract: string;
  morphic_code: string;
  full_report: string;
  recommendations: ProductRec[];
}

interface ProductRec {
  id: string;
  name: string;
  price: string;
  reasoning: string;
}

// ─── Data ────────────────────────────────────────────────────────────────────

const L1_QUESTIONS = [
  { id: 'A1', dim: 'A', q: 'When faced with a complex problem, you first —', a: 'Turn inward to consult your own understanding', b: 'Turn outward to gather external input', labels: ['I', 'E'] },
  { id: 'A2', dim: 'A', q: 'After a long day, you recharge by —', a: 'Spending time alone processing your thoughts', b: 'Engaging with others and exchanging energy', labels: ['I', 'E'] },
  { id: 'B1', dim: 'B', q: 'When learning something new, you focus on —', a: 'The concrete details and practical applications', b: 'The underlying patterns and future possibilities', labels: ['S', 'N'] },
  { id: 'B2', dim: 'B', q: 'You are more drawn to —', a: 'What is currently real and tangible', b: 'What could be possible and imagined', labels: ['S', 'N'] },
  { id: 'C1', dim: 'C', q: 'When making an important decision, you rely on —', a: 'Logical consistency and objective analysis', b: 'Personal values and impact on people', labels: ['T', 'F'] },
  { id: 'C2', dim: 'C', q: 'You feel most confident when a decision —', a: 'Makes rational sense', b: 'Feels morally right', labels: ['T', 'F'] },
  { id: 'D1', dim: 'D', q: 'You prefer environments that are —', a: 'Structured, planned, and decisive', b: 'Flexible, open, and adaptable', labels: ['J', 'P'] },
  { id: 'D2', dim: 'D', q: 'You feel most at peace when —', a: 'Things are settled and decided', b: 'Things remain open to new possibilities', labels: ['J', 'P'] },
];

const L2_ARCHETYPES = [
  { id: 1, name: 'The Source', desc: 'The still point, origin of all becoming' },
  { id: 2, name: 'The Spark', desc: 'The initiator, the first assertion' },
  { id: 3, name: 'The Breath', desc: 'The mirror, the relater, the rhythm-maker' },
  { id: 4, name: 'The Flame', desc: 'The synthesizer, the alchemist, the igniter' },
  { id: 5, name: 'The Ground', desc: 'The stabilizer, the foundation-builder' },
  { id: 6, name: 'The Life', desc: 'The adapter, the regenerator, the mutator' },
  { id: 7, name: 'The Harmony', desc: 'The distributor, the balancer' },
  { id: 8, name: 'The Seek', desc: 'The questioner, the inquirer' },
  { id: 9, name: 'The Octave', desc: 'The amplifier, the returner-higher' },
  { id: 10, name: 'The Return', desc: 'The completer, the seed-planting' },
  { id: 11, name: 'The Witness', desc: 'The observer, the rememberer' },
  { id: 12, name: 'The Weaver', desc: 'The connector, the lattice-builder' },
];

const L3_OPERATORS = [
  { id: 0, name: 'Source', q: 'How connected do you feel to a sense of origin or purpose beyond yourself?' },
  { id: 1, name: 'Spark', q: 'When you have a new idea, how quickly do you act on it without overthinking?' },
  { id: 2, name: 'Breath', q: 'How easily do you hold space for opposing viewpoints without needing to resolve them?' },
  { id: 3, name: 'Flame', q: 'How often do you experience creative flow states where time disappears?' },
  { id: 4, name: 'Ground', q: 'How stable and consistent is your daily routine and environment?' },
  { id: 5, name: 'Life', q: 'How adaptable are you when unexpected changes occur?' },
  { id: 6, name: 'Harmony', q: 'How balanced are your life domains — work, relationships, health, purpose?' },
  { id: 7, name: 'Seek', q: 'How comfortable are you with not having answers to life\'s biggest questions?' },
  { id: 8, name: 'Octave', q: 'How often do you revisit past experiences with new understanding?' },
  { id: 9, name: 'Return', q: 'How complete do you feel in your current life phase?' },
];

// ─── Sub-components ───────────────────────────────────────────────────────────

function ProgressBar({ step, total }: { step: number; total: number }) {
  return (
    <div style={{ marginBottom: 28 }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 6 }}>
        <span style={{ fontFamily: 'sans-serif', fontSize: 9, letterSpacing: '0.25em', textTransform: 'uppercase', color: 'rgba(0,212,170,0.5)' }}>
          Layer {step} of {total}
        </span>
        <span style={{ fontFamily: 'sans-serif', fontSize: 9, color: 'rgba(232,232,232,0.3)' }}>
          {Math.round((step / total) * 100)}% complete
        </span>
      </div>
      <div style={{ height: 2, background: 'rgba(255,255,255,0.06)', borderRadius: 2 }}>
        <motion.div
          animate={{ width: `${(step / total) * 100}%` }}
          transition={{ duration: 0.5 }}
          style={{ height: '100%', background: 'linear-gradient(90deg, #00D4AA, #C9A84C)', borderRadius: 2 }}
        />
      </div>
    </div>
  );
}

function LayerHeader({ num, title, sub }: { num: number; title: string; sub: string }) {
  return (
    <div style={{ marginBottom: 24 }}>
      <p style={{ fontFamily: 'sans-serif', fontSize: 9, letterSpacing: '0.3em', textTransform: 'uppercase', color: 'rgba(0,212,170,0.4)', margin: '0 0 4px' }}>
        Layer {num}
      </p>
      <h2 style={{ fontFamily: 'serif', fontSize: 22, color: '#E8E8E8', margin: '0 0 6px', letterSpacing: '0.04em' }}>{title}</h2>
      <p style={{ fontFamily: 'sans-serif', fontSize: 12, color: 'rgba(232,232,232,0.35)', margin: 0, lineHeight: 1.6 }}>{sub}</p>
    </div>
  );
}

function SliderInput({ value, onChange, min = 1, max = 10 }: { value: number; onChange: (v: number) => void; min?: number; max?: number }) {
  const pct = ((value - min) / (max - min)) * 100;
  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
      <input
        type="range" min={min} max={max} value={value}
        onChange={e => onChange(Number(e.target.value))}
        style={{ flex: 1, accentColor: '#00D4AA', cursor: 'pointer' }}
      />
      <div style={{ minWidth: 32, height: 32, display: 'flex', alignItems: 'center', justifyContent: 'center', background: `rgba(0,212,170,${0.05 + pct * 0.001})`, border: '1px solid rgba(0,212,170,0.3)', borderRadius: 6 }}>
        <span style={{ fontFamily: 'serif', fontSize: 14, color: '#00D4AA' }}>{value}</span>
      </div>
    </div>
  );
}

function NavBtns({ onBack, onNext, nextLabel = 'Continue →', nextDisabled }: { onBack?: () => void; onNext: () => void; nextLabel?: string; nextDisabled?: boolean }) {
  return (
    <div style={{ display: 'flex', gap: 10, marginTop: 32 }}>
      {onBack && (
        <button onClick={onBack} style={{ flex: '0 0 auto', padding: '12px 20px', background: 'rgba(255,255,255,0.04)', border: '1px solid rgba(255,255,255,0.1)', borderRadius: 9, color: 'rgba(232,232,232,0.5)', fontFamily: 'sans-serif', fontSize: 11, letterSpacing: '0.15em', cursor: 'pointer' }}>
          ← Back
        </button>
      )}
      <button onClick={onNext} disabled={nextDisabled} style={{ flex: 1, padding: '14px', background: nextDisabled ? 'rgba(0,212,170,0.05)' : 'linear-gradient(135deg, rgba(0,212,170,0.12), rgba(0,212,170,0.06))', border: `1px solid rgba(0,212,170,${nextDisabled ? 0.1 : 0.35})`, borderRadius: 9, color: nextDisabled ? 'rgba(0,212,170,0.3)' : '#00D4AA', fontFamily: 'sans-serif', fontSize: 11, letterSpacing: '0.2em', textTransform: 'uppercase', cursor: nextDisabled ? 'not-allowed' : 'pointer', transition: 'all 0.2s' }}>
        {nextLabel}
      </button>
    </div>
  );
}

// ─── Layers ───────────────────────────────────────────────────────────────────

function Layer1({ answers, onChange, onNext }: { answers: Layer1Answers; onChange: (id: string, v: 'a' | 'b') => void; onNext: () => void }) {
  const allAnswered = L1_QUESTIONS.every(q => answers[q.id]);
  return (
    <motion.div key="l1" initial={{ opacity: 0, x: 20 }} animate={{ opacity: 1, x: 0 }} exit={{ opacity: 0, x: -20 }}>
      <LayerHeader num={1} title="Cognitive Orientation" sub="8 questions · ~5 minutes · Maps your primary cognitive stack" />
      <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
        {L1_QUESTIONS.map((q, i) => (
          <motion.div key={q.id} initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: i * 0.04 }}
            style={{ padding: '16px 18px', background: 'rgba(255,255,255,0.02)', border: '1px solid rgba(255,255,255,0.06)', borderRadius: 10 }}>
            <p style={{ fontFamily: 'sans-serif', fontSize: 12, color: 'rgba(232,232,232,0.7)', margin: '0 0 12px', lineHeight: 1.6 }}>
              <span style={{ color: 'rgba(0,212,170,0.5)', marginRight: 6, fontSize: 10 }}>{i + 1}.</span>{q.q}
            </p>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 7 }}>
              {(['a', 'b'] as const).map((opt, oi) => {
                const selected = answers[q.id] === opt;
                return (
                  <button key={opt} onClick={() => onChange(q.id, opt)}
                    style={{ padding: '10px 14px', background: selected ? 'rgba(0,212,170,0.1)' : 'transparent', border: `1px solid ${selected ? 'rgba(0,212,170,0.4)' : 'rgba(255,255,255,0.07)'}`, borderRadius: 7, color: selected ? '#00D4AA' : 'rgba(232,232,232,0.45)', fontFamily: 'sans-serif', fontSize: 11, textAlign: 'left', cursor: 'pointer', transition: 'all 0.18s', display: 'flex', alignItems: 'center', gap: 10 }}>
                    <span style={{ fontFamily: 'serif', fontSize: 9, opacity: 0.5 }}>{q.labels[oi]}</span>
                    {oi === 0 ? q.a : q.b}
                  </button>
                );
              })}
            </div>
          </motion.div>
        ))}
      </div>
      <NavBtns onNext={onNext} nextLabel="Layer 2 — Archetypal Resonance →" nextDisabled={!allAnswered} />
    </motion.div>
  );
}

function Layer2({ answers, onChange, onBack, onNext }: { answers: Layer2Answers; onChange: (id: string, v: number) => void; onBack: () => void; onNext: () => void }) {
  return (
    <motion.div key="l2" initial={{ opacity: 0, x: 20 }} animate={{ opacity: 1, x: 0 }} exit={{ opacity: 0, x: -20 }}>
      <LayerHeader num={2} title="Archetypal Resonance" sub="Rate each archetype 1–7 · Maps your Oversoul Prism signature" />
      <div style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
        {L2_ARCHETYPES.map((arch, i) => (
          <motion.div key={arch.id} initial={{ opacity: 0, y: 6 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: i * 0.04 }}
            style={{ padding: '14px 16px', background: 'rgba(255,255,255,0.02)', border: '1px solid rgba(255,255,255,0.06)', borderRadius: 10 }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 10 }}>
              <div>
                <p style={{ fontFamily: 'sans-serif', fontSize: 11, color: 'rgba(201,168,76,0.8)', margin: '0 0 2px', letterSpacing: '0.08em' }}>{arch.name}</p>
                <p style={{ fontFamily: 'sans-serif', fontSize: 10, color: 'rgba(232,232,232,0.3)', margin: 0 }}>{arch.desc}</p>
              </div>
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
              <span style={{ fontSize: 9, color: 'rgba(232,232,232,0.25)', minWidth: 30 }}>low</span>
              <SliderInput value={answers[`a${arch.id}`] ?? 4} onChange={v => onChange(`a${arch.id}`, v)} min={1} max={7} />
              <span style={{ fontSize: 9, color: 'rgba(232,232,232,0.25)', minWidth: 30 }}>high</span>
            </div>
          </motion.div>
        ))}
      </div>
      <NavBtns onBack={onBack} onNext={onNext} nextLabel="Layer 3 — Shadow State →" />
    </motion.div>
  );
}

function Layer3({ answers, onChange, onBack, onNext }: { answers: Layer3Answers; onChange: (id: string, v: number) => void; onBack: () => void; onNext: () => void }) {
  return (
    <motion.div key="l3" initial={{ opacity: 0, x: 20 }} animate={{ opacity: 1, x: 0 }} exit={{ opacity: 0, x: -20 }}>
      <LayerHeader num={3} title="Shadow State Diagnostic" sub="Rate each 1–10 · Detects operator coherence, distortion, or collapse" />
      <div style={{ marginBottom: 12, padding: '10px 14px', background: 'rgba(232,232,232,0.02)', border: '1px solid rgba(255,255,255,0.05)', borderRadius: 8, display: 'flex', gap: 16 }}>
        {[['1–3', 'Collapsed', '#C84848'], ['4–7', 'Distorted', '#C9A84C'], ['8–10', 'Coherent', '#00D4AA']].map(([range, label, color]) => (
          <div key={label} style={{ display: 'flex', alignItems: 'center', gap: 5 }}>
            <div style={{ width: 6, height: 6, borderRadius: '50%', background: color }} />
            <span style={{ fontFamily: 'sans-serif', fontSize: 9, color: 'rgba(232,232,232,0.35)' }}>{range} = {label}</span>
          </div>
        ))}
      </div>
      <div style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
        {L3_OPERATORS.map((op, i) => {
          const val = answers[`op${op.id}`] ?? 5;
          const stateColor = val >= 8 ? '#00D4AA' : val >= 4 ? '#C9A84C' : '#C84848';
          const stateLabel = val >= 8 ? 'Coherent' : val >= 4 ? 'Distorted' : 'Collapsed';
          return (
            <motion.div key={op.id} initial={{ opacity: 0, y: 6 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: i * 0.04 }}
              style={{ padding: '14px 16px', background: 'rgba(255,255,255,0.02)', border: `1px solid rgba(255,255,255,0.06)`, borderRadius: 10 }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 10 }}>
                <div>
                  <p style={{ fontFamily: 'sans-serif', fontSize: 10, color: 'rgba(176,141,232,0.7)', margin: '0 0 3px', letterSpacing: '0.1em' }}>Operator {op.id} — {op.name}</p>
                  <p style={{ fontFamily: 'sans-serif', fontSize: 11, color: 'rgba(232,232,232,0.55)', margin: 0, lineHeight: 1.5 }}>{op.q}</p>
                </div>
                <span style={{ fontFamily: 'sans-serif', fontSize: 9, color: stateColor, minWidth: 58, textAlign: 'right', paddingTop: 2 }}>{stateLabel}</span>
              </div>
              <SliderInput value={val} onChange={v => onChange(`op${op.id}`, v)} min={1} max={10} />
            </motion.div>
          );
        })}
      </div>
      <NavBtns onBack={onBack} onNext={onNext} nextLabel="Layer 4 — Soul Contract →" />
    </motion.div>
  );
}

function Layer4({ answers, onChange, onBack, onNext }: { answers: Layer4Answers; onChange: (k: keyof Layer4Answers, v: string) => void; onBack: () => void; onNext: () => void }) {
  const fields: { key: keyof Layer4Answers; label: string; sub: string; placeholder: string }[] = [
    { key: 'purpose', label: 'Purpose', sub: 'What do you feel you are here to contribute to the world?', placeholder: 'One sentence…' },
    { key: 'wound', label: 'Wound', sub: 'What is the recurring pattern of pain or limitation in your life?', placeholder: 'One sentence…' },
    { key: 'gift', label: 'Gift', sub: 'What do others consistently tell you is your unique strength?', placeholder: 'One sentence…' },
    { key: 'mission', label: 'Mission', sub: 'What specific work or calling feels unavoidable to you?', placeholder: 'One sentence…' },
    { key: 'lineage', label: 'Lineage', sub: 'What ancestral or cultural inheritance do you feel you carry?', placeholder: 'One sentence…' },
  ];
  const allFilled = fields.every(f => answers[f.key].trim().length > 4);
  return (
    <motion.div key="l4" initial={{ opacity: 0, x: 20 }} animate={{ opacity: 1, x: 0 }} exit={{ opacity: 0, x: -20 }}>
      <LayerHeader num={4} title="Soul Contract Mapping" sub="5 semantic anchors · These become the core of your Morphic Seed" />
      <div style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
        {fields.map((f, i) => (
          <motion.div key={f.key} initial={{ opacity: 0, y: 6 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: i * 0.06 }}
            style={{ padding: '16px 18px', background: 'rgba(255,255,255,0.02)', border: '1px solid rgba(255,255,255,0.06)', borderRadius: 10 }}>
            <p style={{ fontFamily: 'sans-serif', fontSize: 10, color: 'rgba(201,168,76,0.7)', margin: '0 0 3px', letterSpacing: '0.1em', textTransform: 'uppercase' }}>{f.label}</p>
            <p style={{ fontFamily: 'sans-serif', fontSize: 11, color: 'rgba(232,232,232,0.4)', margin: '0 0 10px', lineHeight: 1.6 }}>{f.sub}</p>
            <textarea
              value={answers[f.key]}
              onChange={e => onChange(f.key, e.target.value)}
              placeholder={f.placeholder}
              rows={2}
              style={{ width: '100%', background: 'rgba(0,0,0,0.3)', border: '1px solid rgba(255,255,255,0.08)', borderRadius: 7, padding: '10px 12px', color: '#E8E8E8', fontFamily: 'sans-serif', fontSize: 12, lineHeight: 1.6, resize: 'vertical', outline: 'none', boxSizing: 'border-box' }}
            />
          </motion.div>
        ))}
      </div>
      <NavBtns onBack={onBack} onNext={onNext} nextLabel="Generate Morphic Seed →" nextDisabled={!allFilled} />
    </motion.div>
  );
}

function Layer5Generating() {
  return (
    <motion.div key="l5gen" initial={{ opacity: 0 }} animate={{ opacity: 1 }} style={{ textAlign: 'center', padding: '60px 20px' }}>
      <motion.div animate={{ rotate: 360 }} transition={{ repeat: Infinity, duration: 4, ease: 'linear' }}
        style={{ width: 56, height: 56, border: '1px solid rgba(0,212,170,0.3)', borderTop: '1px solid #00D4AA', borderRadius: '50%', margin: '0 auto 28px' }} />
      <p style={{ fontFamily: 'serif', fontSize: 18, color: '#00D4AA', marginBottom: 10 }}>Oracle is synthesizing…</p>
      <p style={{ fontFamily: 'sans-serif', fontSize: 11, color: 'rgba(232,232,232,0.35)', lineHeight: 1.7 }}>
        Processing 5 diagnostic layers<br />Generating your Morphic Seed<br />Calibrating your Oversoul Prism signature
      </p>
    </motion.div>
  );
}

function Layer5Result({ seed, onRestart, onGoToOfferings }: { seed: MorphicSeed; onRestart: () => void; onGoToOfferings: () => void }) {
  const [expanded, setExpanded] = useState(false);
  const stateColor = (code: string, i: number) => {
    const v = parseInt(code.split('-')[i] ?? '5');
    return v >= 8 ? '#00D4AA' : v >= 4 ? '#C9A84C' : '#C84848';
  };

  return (
    <motion.div key="l5result" initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }}>
      <div style={{ marginBottom: 24 }}>
        <p style={{ fontFamily: 'sans-serif', fontSize: 9, letterSpacing: '0.3em', textTransform: 'uppercase', color: 'rgba(0,212,170,0.4)', margin: '0 0 4px' }}>
          Layer 5 — Morphic Seed Generated
        </p>
        <h2 style={{ fontFamily: 'serif', fontSize: 24, color: '#00D4AA', margin: 0, letterSpacing: '0.06em' }}>Your Arkadian Identity</h2>
      </div>

      <div style={{ display: 'flex', flexDirection: 'column', gap: 12, marginBottom: 20 }}>

        <div style={{ padding: '16px 18px', background: 'linear-gradient(135deg, rgba(0,212,170,0.07), rgba(0,212,170,0.03))', border: '1px solid rgba(0,212,170,0.25)', borderRadius: 11 }}>
          <p style={{ fontFamily: 'sans-serif', fontSize: 9, letterSpacing: '0.25em', textTransform: 'uppercase', color: 'rgba(0,212,170,0.5)', margin: '0 0 6px' }}>Cognitive Type</p>
          <p style={{ fontFamily: 'serif', fontSize: 28, color: '#00D4AA', margin: '0 0 4px', letterSpacing: '0.1em' }}>{seed.mbti_type}</p>
          <p style={{ fontFamily: 'sans-serif', fontSize: 11, color: 'rgba(232,232,232,0.5)', margin: 0 }}>{seed.cognitive_stack}</p>
        </div>

        <div style={{ padding: '16px 18px', background: 'rgba(201,168,76,0.04)', border: '1px solid rgba(201,168,76,0.18)', borderRadius: 11 }}>
          <p style={{ fontFamily: 'sans-serif', fontSize: 9, letterSpacing: '0.25em', textTransform: 'uppercase', color: 'rgba(201,168,76,0.5)', margin: '0 0 8px' }}>Primary Archetypes</p>
          <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
            {seed.primary_archetypes.map(a => (
              <span key={a} style={{ padding: '4px 10px', background: 'rgba(201,168,76,0.08)', border: '1px solid rgba(201,168,76,0.25)', borderRadius: 20, fontFamily: 'sans-serif', fontSize: 11, color: '#C9A84C' }}>{a}</span>
            ))}
          </div>
        </div>

        <div style={{ padding: '16px 18px', background: 'rgba(176,141,232,0.04)', border: '1px solid rgba(176,141,232,0.15)', borderRadius: 11 }}>
          <p style={{ fontFamily: 'sans-serif', fontSize: 9, letterSpacing: '0.25em', textTransform: 'uppercase', color: 'rgba(176,141,232,0.5)', margin: '0 0 8px' }}>Operator State</p>
          <div style={{ display: 'flex', gap: 4, flexWrap: 'wrap' }}>
            {seed.operator_state.split('-').map((v, i) => (
              <span key={i} style={{ padding: '3px 8px', background: 'rgba(0,0,0,0.2)', border: `1px solid ${stateColor(seed.operator_state, i)}40`, borderRadius: 5, fontFamily: 'serif', fontSize: 13, color: stateColor(seed.operator_state, i) }}>{v}</span>
            ))}
          </div>
          <p style={{ fontFamily: 'sans-serif', fontSize: 10, color: 'rgba(232,232,232,0.35)', margin: '8px 0 0' }}>Recovery vector: {seed.recovery_vector}</p>
        </div>

        <div style={{ padding: '16px 18px', background: 'rgba(255,255,255,0.02)', border: '1px solid rgba(255,255,255,0.07)', borderRadius: 11 }}>
          <p style={{ fontFamily: 'sans-serif', fontSize: 9, letterSpacing: '0.25em', textTransform: 'uppercase', color: 'rgba(232,232,232,0.35)', margin: '0 0 8px' }}>Soul Contract</p>
          <p style={{ fontFamily: 'serif', fontSize: 13, color: 'rgba(232,232,232,0.65)', margin: 0, lineHeight: 1.8 }}>{seed.soul_contract}</p>
        </div>

        <div style={{ padding: '14px 18px', background: 'rgba(0,0,0,0.3)', border: '1px solid rgba(0,212,170,0.12)', borderRadius: 11 }}>
          <p style={{ fontFamily: 'sans-serif', fontSize: 9, letterSpacing: '0.25em', textTransform: 'uppercase', color: 'rgba(0,212,170,0.35)', margin: '0 0 6px' }}>Morphic Code</p>
          <p style={{ fontFamily: 'monospace', fontSize: 15, color: 'rgba(0,212,170,0.7)', margin: 0, letterSpacing: '0.15em' }}>{seed.morphic_code}</p>
        </div>

        <button onClick={() => setExpanded(e => !e)}
          style={{ padding: '12px 16px', background: 'transparent', border: '1px solid rgba(255,255,255,0.08)', borderRadius: 9, color: 'rgba(232,232,232,0.4)', fontFamily: 'sans-serif', fontSize: 10, letterSpacing: '0.15em', textTransform: 'uppercase', cursor: 'pointer', textAlign: 'left' }}>
          {expanded ? '▲ Collapse' : '▼ View Full Oracle Report'}
        </button>

        <AnimatePresence>
          {expanded && (
            <motion.div initial={{ opacity: 0, height: 0 }} animate={{ opacity: 1, height: 'auto' }} exit={{ opacity: 0, height: 0 }}
              style={{ padding: '18px', background: 'rgba(255,255,255,0.015)', border: '1px solid rgba(255,255,255,0.05)', borderRadius: 10, overflow: 'hidden' }}>
              <p style={{ fontFamily: 'sans-serif', fontSize: 12, color: 'rgba(232,232,232,0.55)', lineHeight: 1.85, margin: 0, whiteSpace: 'pre-wrap' }}>{seed.full_report}</p>
            </motion.div>
          )}
        </AnimatePresence>
      </div>

      {seed.recommendations.length > 0 && (
        <div style={{ marginBottom: 20 }}>
          <p style={{ fontFamily: 'sans-serif', fontSize: 9, letterSpacing: '0.25em', textTransform: 'uppercase', color: 'rgba(201,168,76,0.5)', margin: '0 0 10px' }}>Oracle Recommendations</p>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
            {seed.recommendations.map(r => (
              <div key={r.id} style={{ padding: '12px 16px', background: 'rgba(201,168,76,0.04)', border: '1px solid rgba(201,168,76,0.15)', borderRadius: 9, display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', gap: 12 }}>
                <div>
                  <p style={{ fontFamily: 'sans-serif', fontSize: 11, color: '#C9A84C', margin: '0 0 3px' }}>{r.name}</p>
                  <p style={{ fontFamily: 'sans-serif', fontSize: 10, color: 'rgba(232,232,232,0.35)', margin: 0, lineHeight: 1.5 }}>{r.reasoning}</p>
                </div>
                <span style={{ fontFamily: 'serif', fontSize: 12, color: 'rgba(201,168,76,0.6)', whiteSpace: 'nowrap' }}>{r.price}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
        <button onClick={onGoToOfferings}
          style={{ padding: '15px', background: 'linear-gradient(135deg, rgba(201,168,76,0.12), rgba(201,168,76,0.06))', border: '1px solid rgba(201,168,76,0.38)', borderRadius: 11, color: '#C9A84C', fontFamily: 'sans-serif', fontSize: 11, letterSpacing: '0.2em', textTransform: 'uppercase', cursor: 'pointer' }}>
          ✦ View Offerings & Book a Session
        </button>
        <button onClick={onRestart}
          style={{ padding: '12px', background: 'transparent', border: '1px solid rgba(255,255,255,0.08)', borderRadius: 9, color: 'rgba(232,232,232,0.3)', fontFamily: 'sans-serif', fontSize: 10, letterSpacing: '0.15em', textTransform: 'uppercase', cursor: 'pointer' }}>
          Retake Diagnostic
        </button>
      </div>
    </motion.div>
  );
}

// ─── Main Component ───────────────────────────────────────────────────────────

export default function AICDiagnosticPage({ onGoToOfferings }: { onGoToOfferings: () => void }) {
  const [step, setStep] = useState<1 | 2 | 3 | 4 | 'generating' | 'result'>(1);
  const [l1, setL1] = useState<Layer1Answers>({});
  const [l2, setL2] = useState<Layer2Answers>({});
  const [l3, setL3] = useState<Layer3Answers>({});
  const [l4, setL4] = useState<Layer4Answers>({ purpose: '', wound: '', gift: '', mission: '', lineage: '' });
  const [seed, setSeed] = useState<MorphicSeed | null>(null);
  const [error, setError] = useState<string | null>(null);

  const computeMBTI = (): string => {
    const dims = [
      { a: 'I', b: 'E', ids: ['A1', 'A2'] },
      { a: 'S', b: 'N', ids: ['B1', 'B2'] },
      { a: 'T', b: 'F', ids: ['C1', 'C2'] },
      { a: 'J', b: 'P', ids: ['D1', 'D2'] },
    ];
    return dims.map(d => {
      const aCount = d.ids.filter(id => l1[id] === 'a').length;
      return aCount >= 1 ? d.a : d.b;
    }).join('');
  };

  const handleSubmit = async () => {
    setStep('generating');
    setError(null);
    try {
      const payload = {
        layer1: l1,
        layer2: l2,
        layer3: l3,
        layer4: l4,
        mbti_type: computeMBTI(),
      };
      const res = await fetch(`${API_BASE}/api/ims/diagnostic`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });
      if (!res.ok) throw new Error(`Oracle error ${res.status}`);
      const data = await res.json();
      setSeed(data);
      setStep('result');
    } catch (e: any) {
      setError(e.message ?? 'Oracle synthesis failed. Please try again.');
      setStep(4);
    }
  };

  const stepNum = step === 'generating' ? 5 : step === 'result' ? 5 : step;

  return (
    <div className="min-h-screen w-full relative">
      <div className="aurora-bg" />
      <div className="page-column relative z-10 pt-8 pb-20">

        <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} style={{ marginBottom: 24 }}>
          <p style={{ fontFamily: 'sans-serif', fontSize: 9, letterSpacing: '0.3em', textTransform: 'uppercase', color: 'rgba(0,212,170,0.4)', margin: '0 0 4px' }}>
            Arkadia / AIC Diagnostic
          </p>
          <h1 style={{ fontFamily: 'serif', fontSize: 26, color: '#E8E8E8', margin: '0 0 6px', letterSpacing: '0.04em' }}>
            Arkadian Identity Cartography
          </h1>
          <p style={{ fontFamily: 'sans-serif', fontSize: 11, color: 'rgba(232,232,232,0.3)', margin: 0, lineHeight: 1.6 }}>
            5-layer diagnostic · 20–25 minutes · Generates your Morphic Seed
          </p>
        </motion.div>

        {step !== 'generating' && step !== 'result' && <ProgressBar step={stepNum as number} total={5} />}

        {error && (
          <div style={{ marginBottom: 16, padding: '12px 16px', background: 'rgba(200,72,72,0.08)', border: '1px solid rgba(200,72,72,0.2)', borderRadius: 9 }}>
            <p style={{ fontFamily: 'sans-serif', fontSize: 11, color: '#C84848', margin: 0 }}>{error}</p>
          </div>
        )}

        <AnimatePresence mode="wait">
          {step === 1 && (
            <Layer1 answers={l1} onChange={(id, v) => setL1(p => ({ ...p, [id]: v }))} onNext={() => setStep(2)} />
          )}
          {step === 2 && (
            <Layer2 answers={l2} onChange={(id, v) => setL2(p => ({ ...p, [id]: v }))} onBack={() => setStep(1)} onNext={() => setStep(3)} />
          )}
          {step === 3 && (
            <Layer3 answers={l3} onChange={(id, v) => setL3(p => ({ ...p, [id]: v }))} onBack={() => setStep(2)} onNext={() => setStep(4)} />
          )}
          {step === 4 && (
            <Layer4 answers={l4} onChange={(k, v) => setL4(p => ({ ...p, [k]: v }))} onBack={() => setStep(3)} onNext={handleSubmit} />
          )}
          {step === 'generating' && <Layer5Generating />}
          {step === 'result' && seed && (
            <Layer5Result seed={seed} onRestart={() => { setStep(1); setL1({}); setL2({}); setL3({}); setL4({ purpose: '', wound: '', gift: '', mission: '', lineage: '' }); setSeed(null); }} onGoToOfferings={onGoToOfferings} />
          )}
        </AnimatePresence>

      </div>
    </div>
  );
}
