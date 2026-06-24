import React, { useState, useEffect, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useSpiralQuantumResonance } from '../hooks/useSpiralQuantumResonance';

const API_BASE = (import.meta.env.VITE_API_URL ?? '').replace(/\/$/, '');

// ── Flow step machine ─────────────────────────────────────────────────────────

type FlowStep = 'reset' | 'diagnostic' | 'processing' | 'snapshot' | 'invitation' | 'booking' | 'confirmed';

interface LivingGateProps {
  onEnterField: (phrase: string) => void;
  onGoToOfferings?: () => void;
  onAICComplete?: (seed: any) => void;
  onGoToReset?: () => void;
  initialMode?: string;
}

// ── Diagnostic statements — 24 total (2 per node: 1 pos + 1 reverse) ─────────

interface Statement {
  key: string;
  node: string;
  nodeDisplay: string;
  text: string;
  reverse: boolean;
}

const STATEMENTS: Statement[] = [
  { key: 'source_pos',  node: 'source',      nodeDisplay: 'Source',  text: 'I often return to the origins of things before deciding what they mean.', reverse: false },
  { key: 'source_rev',  node: 'source',      nodeDisplay: 'Source',  text: 'I rarely think about the origins of things — I focus on where they are now.', reverse: true },
  { key: 'spark_pos',   node: 'spark',       nodeDisplay: 'Spark',   text: 'When I have a new idea, I act on it quickly before overthinking.', reverse: false },
  { key: 'spark_rev',   node: 'spark',       nodeDisplay: 'Spark',   text: 'I prefer to wait and see before committing to a new direction.', reverse: true },
  { key: 'breath_pos',  node: 'breath',      nodeDisplay: 'Breath',  text: 'I can easily hold two opposing viewpoints without needing to resolve them immediately.', reverse: false },
  { key: 'breath_rev',  node: 'breath',      nodeDisplay: 'Breath',  text: 'I prefer clarity and certainty over holding opposing truths.', reverse: true },
  { key: 'flame_pos',   node: 'flame',       nodeDisplay: 'Flame',   text: 'I often synthesize ideas from different domains into something new.', reverse: false },
  { key: 'flame_rev',   node: 'flame',       nodeDisplay: 'Flame',   text: 'I prefer to keep ideas separate rather than merge them.', reverse: true },
  { key: 'ground_pos',  node: 'ground',      nodeDisplay: 'Ground',  text: 'I build stable routines that help me stay consistent.', reverse: false },
  { key: 'ground_rev',  node: 'ground',      nodeDisplay: 'Ground',  text: 'I prefer flexibility over structure.', reverse: true },
  { key: 'life_pos',    node: 'life',        nodeDisplay: 'Life',    text: 'I adapt quickly when unexpected changes occur.', reverse: false },
  { key: 'life_rev',    node: 'life',        nodeDisplay: 'Life',    text: 'I prefer stability over change, even when change might be better.', reverse: true },
  { key: 'harmony_pos', node: 'harmony',     nodeDisplay: 'Harmony', text: 'I actively balance competing demands in my life.', reverse: false },
  { key: 'harmony_rev', node: 'harmony',     nodeDisplay: 'Harmony', text: 'I often struggle to balance competing priorities.', reverse: true },
  { key: 'seek_pos',    node: 'seek',        nodeDisplay: 'Seek',    text: 'I am driven by questions that have no easy answers.', reverse: false },
  { key: 'seek_rev',    node: 'seek',        nodeDisplay: 'Seek',    text: 'I prefer answers over questions.', reverse: true },
  { key: 'octave_pos',  node: 'octave',      nodeDisplay: 'Octave',  text: 'I often revisit past experiences and see them completely differently.', reverse: false },
  { key: 'octave_rev',  node: 'octave',      nodeDisplay: 'Octave',  text: 'I rarely look back — the past is past.', reverse: true },
  { key: 'return_pos',  node: 'return_node', nodeDisplay: 'Return',  text: 'I sense when a chapter of my life is complete and ready to close.', reverse: false },
  { key: 'return_rev',  node: 'return_node', nodeDisplay: 'Return',  text: 'I struggle to let go of things that are finished.', reverse: true },
  { key: 'witness_pos', node: 'witness',     nodeDisplay: 'Witness', text: 'I can observe a situation without needing to intervene or fix it.', reverse: false },
  { key: 'witness_rev', node: 'witness',     nodeDisplay: 'Witness', text: 'I become uncomfortable when I cannot immediately act.', reverse: true },
  { key: 'weaver_pos',  node: 'weaver',      nodeDisplay: 'Weaver',  text: 'I naturally connect people, ideas, and resources.', reverse: false },
  { key: 'weaver_rev',  node: 'weaver',      nodeDisplay: 'Weaver',  text: 'I prefer to work independently rather than connect others.', reverse: true },
];

const SCALE = [
  { value: 1, label: 'Strongly\nDisagree' },
  { value: 2, label: 'Disagree' },
  { value: 3, label: 'Neutral' },
  { value: 4, label: 'Agree' },
  { value: 5, label: 'Strongly\nAgree' },
];

const NODE_COLOR: Record<string, string> = {
  source: '#C9A84C', spark: '#FF8C42', breath: '#00D4AA', flame: '#FF6B6B',
  ground: '#6A9FD8', life: '#4CAF50', harmony: '#B08DE8', seek: '#00D4AA',
  octave: '#C9A84C', return_node: '#E88C6A', witness: '#B08DE8', weaver: '#00D4AA',
};

// ── IMS questionnaire ────────────────────────────────────────────────────────

const IMS_QUESTIONS = [
  { id: 'q1', q: 'What is your primary work or creative practice right now?' },
  { id: 'q2', q: 'What feels most fractured or unclear in your sense of self?' },
  { id: 'q3', q: 'What is the most important decision you have been avoiding?' },
  { id: 'q4', q: 'What do you most want others to understand about you — that they currently do not?' },
  { id: 'q5', q: 'If you knew there were no consequences, what would you say or do differently right now?' },
];

// ── Helpers ───────────────────────────────────────────────────────────────────

function useCountdown(initial: number, running: boolean, onDone: () => void) {
  const [secs, setSecs] = useState(initial);
  useEffect(() => {
    if (!running || secs <= 0) return;
    const t = setInterval(() => setSecs(s => {
      if (s <= 1) { onDone(); return 0; }
      return s - 1;
    }), 1000);
    return () => clearInterval(t);
  }, [running, secs]);
  return secs;
}

function fmt(s: number) {
  return `${Math.floor(s / 60)}:${(s % 60).toString().padStart(2, '0')}`;
}

function BreathingCircle({ phase }: { phase: 'inhale' | 'hold' | 'exhale' }) {
  const scale = phase === 'inhale' ? 1.4 : phase === 'hold' ? 1.4 : 1.0;
  const dur   = phase === 'inhale' ? 4 : phase === 'hold' ? 2 : 6;
  return (
    <div style={{ position: 'relative', width: 80, height: 80, margin: '0 auto' }}>
      <motion.div
        animate={{ scale }}
        transition={{ duration: dur, ease: 'easeInOut' }}
        style={{ position: 'absolute', inset: 0, borderRadius: '50%', border: '1px solid rgba(0,212,170,0.3)', background: 'radial-gradient(circle, rgba(0,212,170,0.08) 0%, transparent 70%)' }}
      />
      <motion.div
        animate={{ scale: scale * 0.6 }}
        transition={{ duration: dur, ease: 'easeInOut' }}
        style={{ position: 'absolute', inset: '20%', borderRadius: '50%', background: 'rgba(0,212,170,0.18)' }}
      />
      <div style={{ position: 'absolute', inset: 0, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
        <span style={{ fontFamily: 'sans-serif', fontSize: 9, letterSpacing: '0.2em', textTransform: 'uppercase', color: 'rgba(0,212,170,0.65)' }}>
          {phase === 'inhale' ? 'inhale' : phase === 'hold' ? 'hold' : 'exhale'}
        </span>
      </div>
    </div>
  );
}

// ── STEP 1 — Field Reset ──────────────────────────────────────────────────────

const RESET_STEPS = [
  {
    num: 1, title: 'Regulate', duration: '2 min', color: '#00D4AA',
    icon: '◎',
    body: 'Sit upright or stand tall. Drop your shoulders. Relax your jaw.\n\nInhale slowly. Exhale longer than you inhaled.\n\nRepeat 3–5 times.',
    anchor: '"I release pressure that isn\'t mine to carry."',
    science: 'Longer exhales activate parasympathetic response. Stress hormones reduce. Clear thinking returns.',
  },
  {
    num: 2, title: 'Reclaim', duration: '2 min', color: '#C9A84C',
    icon: '✦',
    body: 'Place one hand over your upper abdomen.\n\nSay each line slowly:',
    affirmations: ['My work creates value.', 'My actions create movement.', 'I am allowed to be paid.'],
    science: 'This is identity reinforcement, not affirmation. Income follows identity. Identity drives action.',
  },
  {
    num: 3, title: 'Receive', duration: '1 min', color: '#B08DE8',
    icon: '∞',
    body: 'Breathing pattern:',
    breathPattern: { inhale: 4, hold: 2, exhale: 6 },
    anchor: '"I move. Money moves with me."',
    science: 'Long exhale = nervous system stability. Stability = better decisions.',
  },
];

type BreathPhase = 'inhale' | 'hold' | 'exhale';

function ResetStep({ onComplete }: { onComplete: () => void }) {
  const [step, setStep] = useState(0);
  const [playing, setPlaying] = useState(false);
  const [audioDuration, setAudioDuration] = useState(300);
  const [audioTime, setAudioTime]     = useState(0);
  const [audioReady, setAudioReady]   = useState(false);
  const [audioEnded, setAudioEnded]   = useState(false);

  const voiceRef   = useRef<HTMLAudioElement | null>(null);
  const ambientRef = useRef<HTMLAudioElement | null>(null);

  // Initialise audio elements once
  useEffect(() => {
    const voice   = new Audio('/oracle-reset.mp3');
    const ambient = new Audio('/oracle-ambient.mp3');
    ambient.loop   = true;
    ambient.volume = 0.22;
    voice.preload  = 'auto';
    ambient.preload = 'auto';

    voice.addEventListener('loadedmetadata', () => {
      setAudioDuration(voice.duration || 300);
      setAudioReady(true);
    });
    voice.addEventListener('timeupdate', () => setAudioTime(voice.currentTime));
    voice.addEventListener('ended', () => {
      setPlaying(false);
      setAudioEnded(true);
      ambient.pause();
      onComplete();
    });

    voiceRef.current   = voice;
    ambientRef.current = ambient;
    return () => { voice.pause(); ambient.pause(); };
  }, []);

  const togglePlay = () => {
    const voice   = voiceRef.current!;
    const ambient = ambientRef.current!;
    if (playing) {
      voice.pause(); ambient.pause();
      setPlaying(false);
    } else {
      voice.play().catch(() => {});
      ambient.play().catch(() => {});
      setPlaying(true);
    }
  };

  const pct = audioDuration > 0 ? (audioTime / audioDuration) * 100 : 0;
  const remaining = Math.max(0, audioDuration - audioTime);

  // Auto-advance step tab based on audio time (120s = step 1→2, 240s = step 2→3)
  useEffect(() => {
    if      (audioTime >= 240) setStep(2);
    else if (audioTime >= 120) setStep(1);
    else                       setStep(0);
  }, [Math.floor(audioTime / 10)]);

  // Breathing cycle for step 3
  const [breathPhase, setBreathPhase] = useState<BreathPhase>('inhale');
  const breathTimer = useRef<any>(null);
  useEffect(() => {
    if (step !== 2) return;
    const cycle = () => {
      setBreathPhase('inhale');
      breathTimer.current = setTimeout(() => {
        setBreathPhase('hold');
        breathTimer.current = setTimeout(() => {
          setBreathPhase('exhale');
          breathTimer.current = setTimeout(cycle, 6000);
        }, 2000);
      }, 4000);
    };
    cycle();
    return () => clearTimeout(breathTimer.current);
  }, [step]);

  const rs = RESET_STEPS[step];

  return (
    <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} style={{ maxWidth: 520, margin: '0 auto' }}>

      {/* Header */}
      <div style={{ textAlign: 'center', marginBottom: 24 }}>
        <p style={{ fontFamily: 'sans-serif', fontSize: 9, letterSpacing: '0.35em', textTransform: 'uppercase', color: 'rgba(0,212,170,0.45)', marginBottom: 6 }}>
          5-Minute Field Reset
        </p>
        <h2 style={{ fontFamily: '"Cinzel", serif', fontSize: 22, color: '#00D4AA', margin: '0 0 4px', letterSpacing: '0.1em' }}>
          Regulate. Reclaim. Receive.
        </h2>
        <p style={{ fontFamily: 'sans-serif', fontSize: 11, color: 'rgba(232,232,232,0.35)', margin: 0 }}>
          Restore clarity before your identity measurement
        </p>
      </div>

      {/* Audio player */}
      <div style={{ marginBottom: 22, padding: '14px 18px', background: 'rgba(0,212,170,0.04)', border: '1px solid rgba(0,212,170,0.14)', borderRadius: 12 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 14 }}>
          {/* Play/pause */}
          <button onClick={togglePlay}
            style={{ width: 44, height: 44, borderRadius: '50%', border: `1px solid ${playing ? 'rgba(0,212,170,0.55)' : 'rgba(0,212,170,0.28)'}`, background: playing ? 'rgba(0,212,170,0.12)' : 'rgba(0,212,170,0.04)', cursor: 'pointer', display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0, transition: 'all 0.2s' }}>
            {playing ? (
              <svg width="14" height="14" viewBox="0 0 14 14" fill="#00D4AA">
                <rect x="2" y="2" width="3.5" height="10" rx="1"/>
                <rect x="8.5" y="2" width="3.5" height="10" rx="1"/>
              </svg>
            ) : (
              <svg width="14" height="14" viewBox="0 0 14 14" fill="#00D4AA">
                <polygon points="3,2 12,7 3,12"/>
              </svg>
            )}
          </button>

          <div style={{ flex: 1 }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 5 }}>
              <span style={{ fontFamily: 'sans-serif', fontSize: 9, letterSpacing: '0.18em', textTransform: 'uppercase', color: playing ? '#00D4AA' : 'rgba(0,212,170,0.45)' }}>
                {playing ? 'Oracle Speaking' : audioReady ? 'Oracle Ready' : 'Loading…'}
              </span>
              <span style={{ fontFamily: 'sans-serif', fontSize: 9, color: 'rgba(0,212,170,0.4)', letterSpacing: '0.06em' }}>
                {fmt(Math.floor(remaining))} left
              </span>
            </div>
            {/* Progress bar — clickable scrub */}
            <div style={{ height: 3, background: 'rgba(0,212,170,0.1)', borderRadius: 3, overflow: 'hidden', cursor: 'pointer' }}
              onClick={e => {
                const rect = (e.currentTarget as HTMLElement).getBoundingClientRect();
                const ratio = (e.clientX - rect.left) / rect.width;
                if (voiceRef.current) voiceRef.current.currentTime = ratio * audioDuration;
              }}>
              <motion.div animate={{ width: `${pct}%` }} transition={{ duration: 0.4 }}
                style={{ height: '100%', background: 'linear-gradient(90deg, #00D4AA, rgba(0,212,170,0.5))', borderRadius: 3 }} />
            </div>
          </div>

          {/* Volume for ambient */}
          <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 2 }}>
            <svg width="12" height="12" viewBox="0 0 12 12" fill="rgba(0,212,170,0.35)">
              <path d="M2 4.5v3h2l3 2.5V2L4 4.5H2z"/>
              <path d="M8.5 2.5a4 4 0 010 7" stroke="rgba(0,212,170,0.35)" strokeWidth="1" fill="none"/>
            </svg>
            <span style={{ fontFamily: 'sans-serif', fontSize: 7, color: 'rgba(0,212,170,0.3)', letterSpacing: '0.08em' }}>AMB</span>
          </div>
        </div>
      </div>

      {/* Step tabs */}
      <div style={{ display: 'flex', gap: 5, marginBottom: 18 }}>
        {RESET_STEPS.map((s, i) => (
          <button key={i} onClick={() => setStep(i)}
            style={{ flex: 1, padding: '8px 6px', background: step === i ? `${s.color}15` : 'rgba(255,255,255,0.02)', border: `1px solid ${step === i ? `${s.color}44` : 'rgba(255,255,255,0.07)'}`, borderRadius: 8, cursor: 'pointer', transition: 'all 0.18s' }}>
            <p style={{ fontFamily: 'sans-serif', fontSize: 8, letterSpacing: '0.2em', textTransform: 'uppercase', color: step === i ? s.color : 'rgba(232,232,232,0.3)', margin: '0 0 2px' }}>{s.num}.</p>
            <p style={{ fontFamily: 'sans-serif', fontSize: 9, color: step === i ? s.color : 'rgba(232,232,232,0.35)', margin: '0 0 1px', fontWeight: step === i ? 500 : 400 }}>{s.title}</p>
            <p style={{ fontFamily: 'sans-serif', fontSize: 8, color: 'rgba(232,232,232,0.22)', margin: 0 }}>{s.duration}</p>
          </button>
        ))}
      </div>

      {/* Active step content */}
      <AnimatePresence mode="wait">
        <motion.div key={step} initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -10 }} transition={{ duration: 0.3 }}>
          <div style={{ padding: '20px', background: `${rs.color}08`, border: `1px solid ${rs.color}22`, borderRadius: 12, marginBottom: 14 }}>

            <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 16 }}>
              <span style={{ fontSize: 18, color: rs.color }}>{rs.icon}</span>
              <div>
                <p style={{ fontFamily: 'sans-serif', fontSize: 9, letterSpacing: '0.25em', textTransform: 'uppercase', color: `${rs.color}88`, margin: '0 0 2px' }}>Step {rs.num} of 3 · {rs.duration}</p>
                <h3 style={{ fontFamily: '"Cinzel", serif', fontSize: 18, color: rs.color, margin: 0, letterSpacing: '0.08em' }}>{rs.title}</h3>
              </div>
            </div>

            {/* Breathing circle for steps 1 and 3 */}
            {(step === 0 || step === 2) && (
              <div style={{ marginBottom: 18 }}>
                <BreathingCircle phase={step === 2 ? breathPhase : 'exhale'} />
                {step === 2 && (
                  <div style={{ display: 'flex', justifyContent: 'center', gap: 18, marginTop: 10 }}>
                    {[['Inhale', 4], ['Hold', 2], ['Exhale', 6]].map(([label, n]) => (
                      <div key={label as string} style={{ textAlign: 'center' }}>
                        <p style={{ fontFamily: 'sans-serif', fontSize: 16, color: '#B08DE8', margin: '0 0 2px' }}>{n}</p>
                        <p style={{ fontFamily: 'sans-serif', fontSize: 8, color: 'rgba(232,232,232,0.3)', margin: 0, letterSpacing: '0.1em', textTransform: 'uppercase' }}>{label}</p>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            )}

            <p style={{ fontFamily: 'sans-serif', fontSize: 12, color: 'rgba(232,232,232,0.62)', lineHeight: '1.8', margin: '0 0 14px', whiteSpace: 'pre-line' }}>
              {rs.body}
            </p>

            {/* Affirmations for step 2 */}
            {rs.affirmations && (
              <div style={{ marginBottom: 14, display: 'flex', flexDirection: 'column', gap: 8 }}>
                {rs.affirmations.map((a, i) => (
                  <motion.div key={a} initial={{ opacity: 0, x: -8 }} animate={{ opacity: 1, x: 0 }} transition={{ delay: i * 0.2 }}
                    style={{ padding: '10px 16px', background: 'rgba(201,168,76,0.06)', border: '1px solid rgba(201,168,76,0.2)', borderRadius: 8 }}>
                    <p style={{ fontFamily: 'serif', fontSize: 13, color: '#C9A84C', margin: 0, letterSpacing: '0.02em' }}>{a}</p>
                  </motion.div>
                ))}
              </div>
            )}

            {/* Anchor phrase */}
            {rs.anchor && (
              <div style={{ padding: '11px 16px', background: 'rgba(0,0,0,0.3)', border: `1px solid ${rs.color}22`, borderRadius: 8, marginBottom: 12 }}>
                <p style={{ fontFamily: 'serif', fontSize: 13, color: rs.color, margin: 0, fontStyle: 'italic', letterSpacing: '0.02em' }}>{rs.anchor}</p>
              </div>
            )}

            {/* Science note */}
            {rs.science && (
              <p style={{ fontFamily: 'sans-serif', fontSize: 10, color: 'rgba(232,232,232,0.28)', lineHeight: '1.65', margin: 0, borderTop: `1px solid ${rs.color}18`, paddingTop: 10 }}>
                {rs.science}
              </p>
            )}
          </div>
        </motion.div>
      </AnimatePresence>

      {/* Navigation */}
      <div style={{ display: 'flex', gap: 8, marginBottom: 14 }}>
        {step < 2 ? (
          <button onClick={() => setStep(s => s + 1)}
            style={{ flex: 1, padding: '12px', background: 'rgba(0,212,170,0.06)', border: '1px solid rgba(0,212,170,0.22)', borderRadius: 9, color: 'rgba(0,212,170,0.7)', fontFamily: 'sans-serif', fontSize: 10, letterSpacing: '0.18em', textTransform: 'uppercase', cursor: 'pointer' }}>
            Next Step →
          </button>
        ) : null}
        <button onClick={onComplete}
          style={{ flex: step === 2 ? 1 : undefined, padding: '12px 18px', background: 'linear-gradient(135deg, rgba(0,212,170,0.12), rgba(0,212,170,0.06))', border: '1px solid rgba(0,212,170,0.4)', borderRadius: 9, color: '#00D4AA', fontFamily: 'sans-serif', fontSize: 10, letterSpacing: '0.2em', textTransform: 'uppercase', cursor: 'pointer', boxShadow: '0 4px 18px rgba(0,212,170,0.08)' }}>
          ⟐ Begin Diagnostic
        </button>
      </div>

      <div style={{ textAlign: 'center' }}>
        <button onClick={onComplete} style={{ background: 'none', border: 'none', color: 'rgba(232,232,232,0.2)', fontFamily: 'sans-serif', fontSize: 9, letterSpacing: '0.18em', textTransform: 'uppercase', cursor: 'pointer' }}>
          Skip Reset
        </button>
      </div>
    </motion.div>
  );
}

// ── STEP 2 — AIC Diagnostic (24 Likert) ──────────────────────────────────────

function DiagnosticStep({ responses, onAnswer, onSubmit }: {
  responses: Record<string, number>;
  onAnswer: (key: string, value: number) => void;
  onSubmit: () => void;
}) {
  const [currentIdx, setCurrentIdx] = useState(0);
  const total = STATEMENTS.length;
  const answered = Object.keys(responses).length;
  const current = STATEMENTS[currentIdx];
  const currentVal = current ? responses[current.key] : undefined;
  const allAnswered = answered === total;
  const color = NODE_COLOR[current?.node] || '#C9A84C';

  const handleSelect = (val: number) => {
    onAnswer(current.key, val);
    if (currentIdx < total - 1) setTimeout(() => setCurrentIdx(i => i + 1), 260);
  };

  return (
    <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} style={{ maxWidth: 520, margin: '0 auto' }}>

      {/* Header */}
      <div style={{ marginBottom: 20 }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 14 }}>
          <div>
            <p style={{ fontFamily: 'sans-serif', fontSize: 9, letterSpacing: '0.28em', textTransform: 'uppercase', color: 'rgba(0,212,170,0.45)', margin: '0 0 2px' }}>AIC Diagnostic</p>
            <p style={{ fontFamily: 'sans-serif', fontSize: 8, letterSpacing: '0.2em', textTransform: 'uppercase', color: 'rgba(201,168,76,0.4)', margin: 0 }}>Arkadian Pulse</p>
          </div>
          <span style={{ fontFamily: 'sans-serif', fontSize: 10, color: 'rgba(232,232,232,0.28)', letterSpacing: '0.08em' }}>
            {currentIdx + 1} of {total}
          </span>
        </div>
        {/* Progress */}
        <div style={{ height: '2px', background: 'rgba(0,212,170,0.08)', borderRadius: 2, overflow: 'hidden' }}>
          <motion.div animate={{ width: `${(answered / total) * 100}%` }} transition={{ duration: 0.4 }}
            style={{ height: '100%', background: 'linear-gradient(90deg, #00D4AA, #C9A84C)', borderRadius: 2 }} />
        </div>
      </div>

      {/* Question */}
      <div style={{ minHeight: 260, display: 'flex', flexDirection: 'column', justifyContent: 'center' }}>
        <AnimatePresence mode="wait">
          <motion.div key={currentIdx} initial={{ opacity: 0, y: 14 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -14 }} transition={{ duration: 0.28 }}>

            {/* Node chip */}
            <div style={{ marginBottom: 14, display: 'flex', justifyContent: 'center' }}>
              <span style={{ padding: '3px 12px', border: `1px solid ${color}33`, borderRadius: 20, fontFamily: 'sans-serif', fontSize: 8, letterSpacing: '0.25em', textTransform: 'uppercase', color: `${color}99` }}>
                {current?.nodeDisplay}
                {current?.reverse && <span style={{ marginLeft: 5, opacity: 0.5 }}>↺</span>}
              </span>
            </div>

            {/* Statement */}
            <p style={{ fontFamily: 'serif', fontSize: 16, lineHeight: '1.8', color: 'rgba(232,232,232,0.88)', textAlign: 'center', marginBottom: 28, minHeight: 72 }}>
              {current?.text}
            </p>

            {/* Likert scale */}
            <div style={{ display: 'flex', gap: 5, justifyContent: 'center' }}>
              {SCALE.map(opt => {
                const active = currentVal === opt.value;
                return (
                  <button key={opt.value} onClick={() => handleSelect(opt.value)}
                    style={{ flex: 1, maxWidth: 68, padding: '10px 4px', background: active ? `${color}1A` : 'rgba(255,255,255,0.02)', border: `1px solid ${active ? color : 'rgba(255,255,255,0.07)'}`, borderRadius: 8, cursor: 'pointer', transition: 'all 0.16s', display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 6 }}>
                    <div style={{ width: 18, height: 18, borderRadius: '50%', border: `2px solid ${active ? color : 'rgba(255,255,255,0.15)'}`, background: active ? color : 'transparent', transition: 'all 0.16s' }} />
                    <span style={{ fontFamily: 'sans-serif', fontSize: 8, letterSpacing: '0.03em', color: active ? color : 'rgba(232,232,232,0.28)', textAlign: 'center', whiteSpace: 'pre-line', lineHeight: 1.3 }}>{opt.label}</span>
                  </button>
                );
              })}
            </div>
          </motion.div>
        </AnimatePresence>
      </div>

      {/* Nav */}
      <div style={{ display: 'flex', gap: 8, marginTop: 22 }}>
        {currentIdx > 0 && (
          <button onClick={() => setCurrentIdx(i => i - 1)}
            style={{ padding: '11px 16px', background: 'rgba(255,255,255,0.02)', border: '1px solid rgba(255,255,255,0.07)', borderRadius: 8, color: 'rgba(232,232,232,0.3)', fontFamily: 'sans-serif', fontSize: 10, cursor: 'pointer' }}>
            ←
          </button>
        )}
        {currentIdx < total - 1 && currentVal !== undefined && (
          <button onClick={() => setCurrentIdx(i => i + 1)}
            style={{ flex: 1, padding: '11px', background: 'rgba(0,212,170,0.04)', border: '1px solid rgba(0,212,170,0.2)', borderRadius: 8, color: 'rgba(0,212,170,0.65)', fontFamily: 'sans-serif', fontSize: 10, letterSpacing: '0.16em', textTransform: 'uppercase', cursor: 'pointer' }}>
            Next →
          </button>
        )}
        {allAnswered && (
          <button onClick={onSubmit}
            style={{ flex: 1, padding: '14px', background: 'linear-gradient(135deg, rgba(201,168,76,0.14), rgba(201,168,76,0.06))', border: '1px solid rgba(201,168,76,0.5)', borderRadius: 10, color: '#C9A84C', fontFamily: 'sans-serif', fontSize: 10, letterSpacing: '0.22em', textTransform: 'uppercase', cursor: 'pointer', boxShadow: '0 4px 18px rgba(201,168,76,0.1)' }}>
            ✦ Reveal My Pattern
          </button>
        )}
      </div>

      {!allAnswered && (
        <p style={{ textAlign: 'center', fontFamily: 'sans-serif', fontSize: 9, color: 'rgba(232,232,232,0.2)', marginTop: 12 }}>
          {answered} of {total} answered · respond instinctively
        </p>
      )}
    </motion.div>
  );
}

// ── STEP 3 — Processing ───────────────────────────────────────────────────────

function ProcessingStep() {
  const lines = ['Mapping your identity vector…', 'Calculating shadow architecture…', 'Generating seed sigil…', 'Synthesising Oracle summary…'];
  const [li, setLi] = useState(0);
  useEffect(() => {
    const t = setInterval(() => setLi(i => (i + 1) % lines.length), 1200);
    return () => clearInterval(t);
  }, []);
  return (
    <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} style={{ textAlign: 'center', padding: '70px 20px', maxWidth: 520, margin: '0 auto' }}>
      <motion.div animate={{ rotate: 360 }} transition={{ duration: 6, repeat: Infinity, ease: 'linear' }}
        style={{ width: 48, height: 48, margin: '0 auto 28px', border: '1px solid rgba(201,168,76,0.25)', borderTop: '1px solid #C9A84C', borderRadius: '50%' }} />
      <p style={{ fontFamily: '"Cinzel", serif', fontSize: 15, color: '#C9A84C', marginBottom: 6, letterSpacing: '0.06em' }}>AIC Snapshot</p>
      <AnimatePresence mode="wait">
        <motion.p key={li} initial={{ opacity: 0, y: 5 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -5 }} transition={{ duration: 0.35 }}
          style={{ fontFamily: 'sans-serif', fontSize: 10, letterSpacing: '0.22em', textTransform: 'uppercase', color: 'rgba(201,168,76,0.55)', margin: 0 }}>
          {lines[li]}
        </motion.p>
      </AnimatePresence>
    </motion.div>
  );
}

// ── STEP 4 — AIC Snapshot ─────────────────────────────────────────────────────

interface SnapshotData {
  scores: Record<string, number>;
  primary_patterns: { node: string; display: string; score: number }[];
  growth_edge: { node: string; display: string; score: number; shadow_index: number; description: string };
  confidence: number;
  pattern_cluster: string;
  oracle_summary: string;
  sigil_svg: string;
}

function ScoreBar({ label, score, highlight }: { label: string; score: number; highlight?: boolean }) {
  const color = highlight ? '#C9A84C' : 'rgba(0,212,170,0.6)';
  return (
    <div style={{ marginBottom: 7 }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 3 }}>
        <span style={{ fontFamily: 'sans-serif', fontSize: 9, letterSpacing: '0.12em', textTransform: 'uppercase', color: highlight ? '#C9A84C' : 'rgba(232,232,232,0.42)' }}>{label}</span>
        <span style={{ fontFamily: 'sans-serif', fontSize: 9, color: highlight ? '#C9A84C' : 'rgba(232,232,232,0.28)' }}>{score}</span>
      </div>
      <div style={{ height: 2, background: 'rgba(255,255,255,0.04)', borderRadius: 2, overflow: 'hidden' }}>
        <motion.div initial={{ width: 0 }} animate={{ width: `${score}%` }} transition={{ duration: 0.9, ease: 'easeOut', delay: 0.1 }}
          style={{ height: '100%', background: color, borderRadius: 2 }} />
      </div>
    </div>
  );
}

function SnapshotStep({ data, onUnlock, onRetake }: {
  data: SnapshotData; onUnlock: () => void; onRetake: () => void;
}) {
  const topNodes = data.primary_patterns.slice(0, 3);

  return (
    <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ duration: 0.6 }} style={{ maxWidth: 520, margin: '0 auto' }}>

      {/* Title */}
      <div style={{ textAlign: 'center', marginBottom: 22 }}>
        <p style={{ fontFamily: 'sans-serif', fontSize: 9, letterSpacing: '0.35em', textTransform: 'uppercase', color: 'rgba(0,212,170,0.45)', marginBottom: 6 }}>AIC Snapshot</p>
        <h2 style={{ fontFamily: '"Cinzel", serif', fontSize: 24, color: '#C9A84C', margin: '0 0 5px', letterSpacing: '0.1em' }}>{data.pattern_cluster}</h2>
        <p style={{ fontFamily: 'sans-serif', fontSize: 9, color: 'rgba(0,212,170,0.4)', letterSpacing: '0.16em', textTransform: 'uppercase' }}>
          Confidence {data.confidence}/100
        </p>
      </div>

      {/* Sigil */}
      <motion.div initial={{ opacity: 0, scale: 0.88 }} animate={{ opacity: 1, scale: 1 }} transition={{ duration: 0.9 }}
        style={{ width: 180, height: 180, margin: '0 auto 22px', border: '1px solid rgba(201,168,76,0.18)', borderRadius: '50%', padding: 8, background: 'radial-gradient(circle, rgba(201,168,76,0.04) 0%, transparent 70%)', boxShadow: '0 0 36px rgba(201,168,76,0.07)' }}
        dangerouslySetInnerHTML={{ __html: data.sigil_svg }} />

      {/* Primary patterns */}
      <div style={{ marginBottom: 14, padding: '16px 18px', background: 'rgba(201,168,76,0.04)', border: '1px solid rgba(201,168,76,0.14)', borderRadius: 10 }}>
        <p style={{ fontFamily: 'sans-serif', fontSize: 9, letterSpacing: '0.25em', textTransform: 'uppercase', color: 'rgba(201,168,76,0.45)', marginBottom: 12 }}>Dominant Nodes</p>
        <div style={{ display: 'flex', gap: 6, marginBottom: 12, flexWrap: 'wrap' }}>
          {topNodes.map((p, i) => (
            <span key={p.node} style={{ padding: '4px 12px', background: i === 0 ? 'rgba(201,168,76,0.12)' : 'rgba(201,168,76,0.05)', border: `1px solid ${i === 0 ? 'rgba(201,168,76,0.4)' : 'rgba(201,168,76,0.15)'}`, borderRadius: 20, fontFamily: 'sans-serif', fontSize: 10, color: i === 0 ? '#C9A84C' : 'rgba(201,168,76,0.55)' }}>
              {p.display}
            </span>
          ))}
        </div>
        {topNodes.map((p, i) => (
          <ScoreBar key={p.node} label={p.display} score={p.score} highlight={i === 0} />
        ))}
      </div>

      {/* Growth edge */}
      <div style={{ marginBottom: 14, padding: '16px 18px', background: 'rgba(232,140,106,0.04)', border: '1px solid rgba(232,140,106,0.16)', borderRadius: 10 }}>
        <p style={{ fontFamily: 'sans-serif', fontSize: 9, letterSpacing: '0.25em', textTransform: 'uppercase', color: 'rgba(232,140,106,0.5)', marginBottom: 8 }}>
          Growth Edge · Shadow Index {data.growth_edge.shadow_index}
        </p>
        <p style={{ fontFamily: '"Cinzel", serif', fontSize: 15, color: '#E88C6A', margin: '0 0 6px', letterSpacing: '0.06em' }}>{data.growth_edge.display}</p>
        <p style={{ fontFamily: 'sans-serif', fontSize: 11, color: 'rgba(232,232,232,0.45)', lineHeight: '1.7', margin: 0 }}>{data.growth_edge.description}</p>
      </div>

      {/* Oracle summary */}
      <div style={{ marginBottom: 22, padding: '18px 20px', background: 'rgba(14,17,32,0.72)', border: '1px solid rgba(201,168,76,0.2)', borderRadius: 10, position: 'relative', backdropFilter: 'blur(12px)' }}>
        {[['top','left'],['top','right'],['bottom','left'],['bottom','right']].map(([v,h]) => (
          <div key={`${v}${h}`} style={{ position: 'absolute', [v]: 0, [h]: 0, width: 7, height: 7, borderTop: v==='top' ? '1px solid rgba(201,168,76,0.4)' : 'none', borderBottom: v==='bottom' ? '1px solid rgba(201,168,76,0.4)' : 'none', borderLeft: h==='left' ? '1px solid rgba(201,168,76,0.4)' : 'none', borderRight: h==='right' ? '1px solid rgba(201,168,76,0.4)' : 'none' }} />
        ))}
        <p style={{ fontFamily: 'sans-serif', fontSize: 9, letterSpacing: '0.25em', textTransform: 'uppercase', color: 'rgba(201,168,76,0.4)', marginBottom: 10 }}>Oracle Summary</p>
        <p style={{ fontFamily: 'serif', fontSize: 13, lineHeight: '1.85', color: 'rgba(212,223,232,0.75)', margin: 0 }}>{data.oracle_summary}</p>
      </div>

      {/* CTA */}
      <button onClick={onUnlock}
        style={{ width: '100%', padding: '16px', background: 'linear-gradient(135deg, rgba(201,168,76,0.14), rgba(201,168,76,0.06))', border: '1px solid rgba(201,168,76,0.5)', borderRadius: 11, color: '#C9A84C', fontFamily: 'sans-serif', fontSize: 11, letterSpacing: '0.22em', textTransform: 'uppercase', cursor: 'pointer', boxShadow: '0 4px 20px rgba(201,168,76,0.1)', marginBottom: 10 }}>
        ✦ Ready for the Full Map?
      </button>
      <div style={{ textAlign: 'center' }}>
        <button onClick={onRetake} style={{ background: 'none', border: 'none', color: 'rgba(232,232,232,0.2)', fontFamily: 'sans-serif', fontSize: 9, letterSpacing: '0.16em', textTransform: 'uppercase', cursor: 'pointer' }}>
          ↺ Retake Diagnostic
        </button>
      </div>
    </motion.div>
  );
}

// ── STEP 5 — IMS Invitation ───────────────────────────────────────────────────

function InvitationStep({ cluster, onBook, onRetake }: {
  cluster: string; onBook: () => void; onRetake: () => void;
}) {
  const deliverables = [
    ['90-Min Live Session', 'Direct mapping with Zahrune Nova'],
    ['12 Narrative Prompts', 'Deep identity excavation'],
    ['Shadow Architecture', 'Full pattern visibility'],
    ['Personal Morphic Seed', 'Your sovereign identity code'],
    ['Oracle Report', 'PDF + Audio + Custom Sigil'],
  ];

  return (
    <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} style={{ maxWidth: 520, margin: '0 auto' }}>

      <div style={{ textAlign: 'center', marginBottom: 26 }}>
        <p style={{ fontFamily: 'sans-serif', fontSize: 9, letterSpacing: '0.35em', textTransform: 'uppercase', color: 'rgba(201,168,76,0.45)', marginBottom: 8 }}>Identity Mapping Session</p>
        <h2 style={{ fontFamily: '"Cinzel", serif', fontSize: 26, color: '#C9A84C', margin: '0 0 10px', letterSpacing: '0.1em' }}>Ready for the Full Map?</h2>
        <p style={{ fontFamily: 'sans-serif', fontSize: 12, color: 'rgba(232,232,232,0.45)', lineHeight: '1.7', margin: 0 }}>
          The AIC Snapshot measures your signal.<br />The full IMS maps your architecture.
        </p>
      </div>

      {/* Cluster echo */}
      <div style={{ marginBottom: 18, padding: '14px 18px', background: 'rgba(201,168,76,0.04)', border: '1px solid rgba(201,168,76,0.15)', borderRadius: 10, textAlign: 'center' }}>
        <p style={{ fontFamily: 'sans-serif', fontSize: 9, letterSpacing: '0.2em', textTransform: 'uppercase', color: 'rgba(201,168,76,0.4)', marginBottom: 5 }}>Your Pattern Cluster</p>
        <p style={{ fontFamily: '"Cinzel", serif', fontSize: 18, color: '#C9A84C', margin: 0, letterSpacing: '0.08em' }}>{cluster}</p>
      </div>

      {/* Deliverables */}
      <div style={{ marginBottom: 22, padding: '18px 20px', background: 'rgba(14,17,32,0.72)', border: '1px solid rgba(201,168,76,0.18)', borderRadius: 10 }}>
        <p style={{ fontFamily: 'sans-serif', fontSize: 9, letterSpacing: '0.25em', textTransform: 'uppercase', color: 'rgba(201,168,76,0.45)', marginBottom: 14 }}>What's Included</p>
        <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
          {deliverables.map(([title, sub]) => (
            <div key={title} style={{ display: 'flex', gap: 12, alignItems: 'flex-start' }}>
              <span style={{ color: '#C9A84C', fontSize: 12, flexShrink: 0, marginTop: 1 }}>✦</span>
              <div>
                <p style={{ fontFamily: 'sans-serif', fontSize: 11, color: 'rgba(232,232,232,0.72)', margin: '0 0 2px', letterSpacing: '0.04em' }}>{title}</p>
                <p style={{ fontFamily: 'sans-serif', fontSize: 10, color: 'rgba(232,232,232,0.3)', margin: 0 }}>{sub}</p>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Price + CTA */}
      <div style={{ marginBottom: 12, padding: '20px', background: 'linear-gradient(135deg, rgba(201,168,76,0.08), rgba(201,168,76,0.03))', border: '1px solid rgba(201,168,76,0.32)', borderRadius: 12, textAlign: 'center' }}>
        <p style={{ fontFamily: '"Cinzel", serif', fontSize: 28, color: '#C9A84C', margin: '0 0 4px' }}>$777</p>
        <p style={{ fontFamily: 'sans-serif', fontSize: 10, color: 'rgba(201,168,76,0.4)', margin: '0 0 16px', letterSpacing: '0.14em' }}>One-time · Full sovereign mapping</p>
        <button onClick={onBook}
          style={{ width: '100%', padding: '15px', background: 'rgba(201,168,76,0.12)', border: '1px solid rgba(201,168,76,0.5)', borderRadius: 10, color: '#C9A84C', fontFamily: 'sans-serif', fontSize: 10, letterSpacing: '0.22em', textTransform: 'uppercase', cursor: 'pointer', boxShadow: '0 4px 20px rgba(201,168,76,0.12)' }}>
          ✦ Unlock Full IMS
        </button>
      </div>

      <div style={{ textAlign: 'center' }}>
        <button onClick={onRetake} style={{ background: 'none', border: 'none', color: 'rgba(232,232,232,0.18)', fontFamily: 'sans-serif', fontSize: 9, letterSpacing: '0.14em', textTransform: 'uppercase', cursor: 'pointer' }}>
          ← Back to Snapshot
        </button>
      </div>
    </motion.div>
  );
}

// ── STEP 6 — IMS Booking form ─────────────────────────────────────────────────

const inputBase: React.CSSProperties = {
  width: '100%', padding: '11px 14px', background: 'rgba(255,255,255,0.03)',
  border: '1px solid rgba(255,255,255,0.1)', borderRadius: '9px',
  color: '#E8E8E8', fontFamily: 'sans-serif', fontSize: '12px',
  outline: 'none', boxSizing: 'border-box',
};

function BookingStep({ cluster, onConfirm }: { cluster: string; onConfirm: () => void }) {
  const [form, setForm] = useState({ name: '', email: '', phone: '' });
  const [answers, setAnswers] = useState<Record<string, string>>({});
  const [stage, setStage] = useState<'details' | 'questions'>('details');
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const detailsReady = form.name.trim() && form.email.trim();
  const filled = IMS_QUESTIONS.filter(q => (answers[q.id] ?? '').trim().length > 3).length;

  const handleSubmit = async () => {
    setSubmitting(true); setError(null);
    try {
      await fetch(`${API_BASE}/api/ims/inquiry`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ ...form, answers, pattern_cluster: cluster }),
      });
      onConfirm();
    } catch {
      setError('Could not submit. Email arkanaofarkadia@gmail.com or WhatsApp +234 814 494 2818');
    } finally { setSubmitting(false); }
  };

  return (
    <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} style={{ maxWidth: 520, margin: '0 auto' }}>
      <div style={{ marginBottom: 22 }}>
        <p style={{ fontFamily: 'sans-serif', fontSize: 9, letterSpacing: '0.28em', textTransform: 'uppercase', color: 'rgba(201,168,76,0.45)', margin: '0 0 3px' }}>Identity Mapping Session — $777</p>
        <h3 style={{ fontFamily: 'serif', fontSize: 20, color: '#C9A84C', margin: 0 }}>
          {stage === 'details' ? 'Your Contact Details' : 'Pre-Session Questions'}
        </h3>
      </div>

      {error && (
        <div style={{ marginBottom: 14, padding: '10px 14px', background: 'rgba(200,72,72,0.07)', border: '1px solid rgba(200,72,72,0.2)', borderRadius: 8 }}>
          <p style={{ fontFamily: 'sans-serif', fontSize: 11, color: '#C84848', margin: 0 }}>{error}</p>
        </div>
      )}

      {stage === 'details' ? (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
          {[['Name', 'name', 'text', 'Your full name'], ['Email', 'email', 'email', 'your@email.com'], ['WhatsApp', 'phone', 'tel', '+1 or +234…']].map(([label, key, type, ph]) => (
            <div key={key}>
              <p style={{ fontFamily: 'sans-serif', fontSize: 9, letterSpacing: '0.2em', textTransform: 'uppercase', color: 'rgba(232,232,232,0.35)', margin: '0 0 6px' }}>{label}</p>
              <input type={type} placeholder={ph} value={form[key as keyof typeof form]}
                onChange={e => setForm(f => ({ ...f, [key]: e.target.value }))} style={inputBase} />
            </div>
          ))}
          <button onClick={() => setStage('questions')} disabled={!detailsReady}
            style={{ padding: '13px', background: detailsReady ? 'rgba(201,168,76,0.09)' : 'rgba(255,255,255,0.03)', border: `1px solid ${detailsReady ? 'rgba(201,168,76,0.35)' : 'rgba(255,255,255,0.07)'}`, borderRadius: 9, color: detailsReady ? '#C9A84C' : 'rgba(232,232,232,0.25)', fontFamily: 'sans-serif', fontSize: 10, letterSpacing: '0.18em', textTransform: 'uppercase', cursor: detailsReady ? 'pointer' : 'not-allowed', marginTop: 4 }}>
            Continue →
          </button>
        </div>
      ) : (
        <div>
          <p style={{ fontFamily: 'sans-serif', fontSize: 11, color: 'rgba(232,232,232,0.35)', marginBottom: 16, lineHeight: '1.65' }}>
            Answer at least 3 of 5. These inform the session preparation.
          </p>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 10, marginBottom: 14 }}>
            {IMS_QUESTIONS.map((q, i) => (
              <div key={q.id} style={{ padding: '13px 14px', background: 'rgba(255,255,255,0.02)', border: '1px solid rgba(255,255,255,0.06)', borderRadius: 9 }}>
                <p style={{ fontFamily: 'sans-serif', fontSize: 9, color: 'rgba(201,168,76,0.4)', margin: '0 0 5px', letterSpacing: '0.08em' }}>{i + 1}.</p>
                <p style={{ fontFamily: 'sans-serif', fontSize: 11, color: 'rgba(232,232,232,0.62)', margin: '0 0 8px', lineHeight: 1.6 }}>{q.q}</p>
                <textarea value={answers[q.id] ?? ''} onChange={e => setAnswers(a => ({ ...a, [q.id]: e.target.value }))}
                  rows={2} placeholder="Your response…"
                  style={{ ...inputBase, resize: 'vertical', lineHeight: 1.6 }} />
              </div>
            ))}
          </div>
          <div style={{ display: 'flex', gap: 8 }}>
            <button onClick={() => setStage('details')}
              style={{ padding: '11px 16px', background: 'rgba(255,255,255,0.03)', border: '1px solid rgba(255,255,255,0.08)', borderRadius: 8, color: 'rgba(232,232,232,0.4)', fontFamily: 'sans-serif', fontSize: 10, cursor: 'pointer' }}>← Back</button>
            <button onClick={handleSubmit} disabled={submitting || filled < 3}
              style={{ flex: 1, padding: '12px', background: filled >= 3 ? 'rgba(201,168,76,0.1)' : 'rgba(255,255,255,0.03)', border: `1px solid ${filled >= 3 ? 'rgba(201,168,76,0.38)' : 'rgba(255,255,255,0.07)'}`, borderRadius: 8, color: filled >= 3 ? '#C9A84C' : 'rgba(232,232,232,0.25)', fontFamily: 'sans-serif', fontSize: 10, letterSpacing: '0.18em', textTransform: 'uppercase', cursor: filled >= 3 ? 'pointer' : 'not-allowed' }}>
              {submitting ? 'Submitting…' : `Submit — ${filled}/5 answered`}
            </button>
          </div>
        </div>
      )}
    </motion.div>
  );
}

// ── STEP 7 — Confirmed ────────────────────────────────────────────────────────

function ConfirmedStep({ onDone }: { onDone: () => void }) {
  return (
    <motion.div initial={{ opacity: 0, y: 14 }} animate={{ opacity: 1, y: 0 }} style={{ textAlign: 'center', padding: '50px 20px', maxWidth: 480, margin: '0 auto' }}>
      <motion.div animate={{ scale: [1, 1.08, 1], opacity: [0.6, 1, 0.6] }} transition={{ duration: 4, repeat: Infinity }}
        style={{ fontSize: 36, marginBottom: 22 }}>✦</motion.div>
      <h2 style={{ fontFamily: '"Cinzel", serif', fontSize: 22, color: '#C9A84C', marginBottom: 12, letterSpacing: '0.1em' }}>Received</h2>
      <p style={{ fontFamily: 'sans-serif', fontSize: 12, color: 'rgba(232,232,232,0.5)', lineHeight: '1.8', marginBottom: 8 }}>
        Your IMS inquiry has been received. You will hear from the field within 48 hours.
      </p>
      <p style={{ fontFamily: 'sans-serif', fontSize: 11, color: 'rgba(232,232,232,0.3)', lineHeight: '1.7', marginBottom: 28 }}>
        WhatsApp: <span style={{ color: 'rgba(0,212,170,0.5)' }}>+234 814 494 2818</span>
        <br />Email: <span style={{ color: 'rgba(0,212,170,0.5)' }}>arkanaofarkadia@gmail.com</span>
      </p>
      <button onClick={onDone}
        style={{ padding: '12px 28px', background: 'rgba(0,212,170,0.06)', border: '1px solid rgba(0,212,170,0.25)', borderRadius: 9, color: 'rgba(0,212,170,0.7)', fontFamily: 'sans-serif', fontSize: 10, letterSpacing: '0.18em', textTransform: 'uppercase', cursor: 'pointer' }}>
        ← Return to Arkadia
      </button>
    </motion.div>
  );
}

// ── Flow breadcrumb ───────────────────────────────────────────────────────────

const BREADCRUMB: { step: FlowStep; label: string }[] = [
  { step: 'reset',      label: 'Reset' },
  { step: 'diagnostic', label: 'Diagnostic' },
  { step: 'snapshot',   label: 'Snapshot' },
  { step: 'invitation', label: 'IMS' },
];

function Breadcrumb({ current }: { current: FlowStep }) {
  const activeIdx = BREADCRUMB.findIndex(b => b.step === current);
  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: 0, marginBottom: 28, justifyContent: 'center' }}>
      {BREADCRUMB.map((b, i) => {
        const done = i < activeIdx;
        const active = i === activeIdx;
        return (
          <React.Fragment key={b.step}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 5 }}>
              <div style={{ width: 6, height: 6, borderRadius: '50%', background: active ? '#C9A84C' : done ? 'rgba(0,212,170,0.6)' : 'rgba(255,255,255,0.1)', border: active ? '1px solid #C9A84C' : 'none', transition: 'all 0.3s' }} />
              <span style={{ fontFamily: 'sans-serif', fontSize: 8, letterSpacing: '0.18em', textTransform: 'uppercase', color: active ? '#C9A84C' : done ? 'rgba(0,212,170,0.5)' : 'rgba(255,255,255,0.18)', transition: 'all 0.3s' }}>
                {b.label}
              </span>
            </div>
            {i < BREADCRUMB.length - 1 && (
              <div style={{ width: 22, height: 1, background: done ? 'rgba(0,212,170,0.3)' : 'rgba(255,255,255,0.07)', margin: '0 6px', transition: 'all 0.3s' }} />
            )}
          </React.Fragment>
        );
      })}
    </div>
  );
}

// ── Main component ────────────────────────────────────────────────────────────

export default function LivingGate({ onEnterField, onGoToOfferings, onAICComplete, initialMode }: LivingGateProps) {
  const { resonance, flameHue } = useSpiralQuantumResonance(true, 8000);
  const [step, setStep] = useState<FlowStep>('reset');
  const [responses, setResponses] = useState<Record<string, number>>({});
  const [snapshot, setSnapshot] = useState<SnapshotData | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleAnswer = (key: string, value: number) => {
    setResponses(r => ({ ...r, [key]: value }));
  };

  const handleSubmitDiagnostic = async () => {
    setStep('processing');
    setError(null);
    try {
      const res = await fetch(`${API_BASE}/api/pulse/analyze`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ responses }),
      });
      if (!res.ok) throw new Error(`Oracle error ${res.status}`);
      const data = await res.json();
      setSnapshot(data);
      onAICComplete?.(data);
      setStep('snapshot');
    } catch (e: any) {
      setError(e.message ?? 'Oracle synthesis failed. Please try again.');
      setStep('diagnostic');
    }
  };

  const handleRetake = () => {
    setResponses({});
    setSnapshot(null);
    setStep('reset');
  };

  return (
    <div className="relative w-full min-h-screen flex flex-col items-center justify-start px-5 py-8"
      style={{ backgroundColor: '#0A0A0F', overflow: 'hidden' }}>

      {/* Ambient glow */}
      <motion.div className="absolute inset-0 pointer-events-none"
        animate={{ background: ['radial-gradient(circle at 50% 38%, rgba(0,212,170,0.04) 0%, transparent 65%)', 'radial-gradient(circle at 50% 38%, rgba(0,212,170,0.07) 0%, transparent 65%)', 'radial-gradient(circle at 50% 38%, rgba(0,212,170,0.04) 0%, transparent 65%)'] }}
        transition={{ duration: 8, repeat: Infinity }} />

      <motion.div className="absolute pointer-events-none" style={{ top: '50%', left: '50%', transform: 'translate(-50%, -50%)' }}
        animate={{ scale: [1, 1.06 * resonance, 1], opacity: [0.04, 0.1, 0.04] }} transition={{ duration: 6, repeat: Infinity }}>
        <div style={{ width: '340px', height: '340px', borderRadius: '50%', border: `1px solid hsl(${flameHue},80%,65%)` }} />
      </motion.div>

      {/* Content */}
      <div className="relative z-10 w-full" style={{ maxWidth: 560 }}>

        {/* Breadcrumb (hidden during booking/confirmed) */}
        {step !== 'booking' && step !== 'confirmed' && (
          <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 0.3 }}>
            <Breadcrumb current={step} />
          </motion.div>
        )}

        {/* Error banner */}
        <AnimatePresence>
          {error && (
            <motion.div initial={{ opacity: 0, y: -8 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0 }}
              style={{ marginBottom: 16, padding: '11px 16px', background: 'rgba(200,72,72,0.07)', border: '1px solid rgba(200,72,72,0.2)', borderRadius: 9 }}>
              <p style={{ fontFamily: 'sans-serif', fontSize: 11, color: '#C84848', margin: 0 }}>{error}</p>
            </motion.div>
          )}
        </AnimatePresence>

        <AnimatePresence mode="wait">
          {step === 'reset' && (
            <motion.div key="reset" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} transition={{ duration: 0.35 }}>
              <ResetStep onComplete={() => setStep('diagnostic')} />
            </motion.div>
          )}

          {step === 'diagnostic' && (
            <motion.div key="diagnostic" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} transition={{ duration: 0.35 }}>
              <DiagnosticStep responses={responses} onAnswer={handleAnswer} onSubmit={handleSubmitDiagnostic} />
            </motion.div>
          )}

          {step === 'processing' && (
            <motion.div key="processing" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} transition={{ duration: 0.35 }}>
              <ProcessingStep />
            </motion.div>
          )}

          {step === 'snapshot' && snapshot && (
            <motion.div key="snapshot" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} transition={{ duration: 0.35 }}>
              <SnapshotStep data={snapshot} onUnlock={() => setStep('invitation')} onRetake={handleRetake} />
            </motion.div>
          )}

          {step === 'invitation' && snapshot && (
            <motion.div key="invitation" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} transition={{ duration: 0.35 }}>
              <InvitationStep cluster={snapshot.pattern_cluster} onBook={() => setStep('booking')} onRetake={() => setStep('snapshot')} />
            </motion.div>
          )}

          {step === 'booking' && snapshot && (
            <motion.div key="booking" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} transition={{ duration: 0.35 }}>
              <BookingStep cluster={snapshot.pattern_cluster} onConfirm={() => setStep('confirmed')} />
            </motion.div>
          )}

          {step === 'confirmed' && (
            <motion.div key="confirmed" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} transition={{ duration: 0.35 }}>
              <ConfirmedStep onDone={handleRetake} />
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </div>
  );
}
