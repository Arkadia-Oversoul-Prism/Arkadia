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

// ── Lyrics for the oracle-reset meditation (7:22 = 442s) ─────────────────────
// Timestamps are estimates — they auto-sync to the actual audio via timeupdate.
// Adjust the `t` values here if any line feels early or late.

type LyricType = 'normal' | 'breath' | 'affirmation' | 'count';
interface ResetLyric { t: number; text: string; type?: LyricType }

const RESET_LYRICS: ResetLyric[] = [
  { t: 0,   text: 'Welcome.' },
  { t: 4,   text: 'For the next few minutes, allow yourself to pause.' },
  { t: 11,  text: 'There is nothing to solve.' },
  { t: 15,  text: 'Nothing to chase.' },
  { t: 18,  text: 'Nothing to force.' },
  { t: 21,  text: 'Simply arrive here.' },
  { t: 27,  text: 'Take a slow breath in...', type: 'breath' },
  { t: 35,  text: 'And a longer breath out.', type: 'breath' },
  { t: 44,  text: 'Again.' },
  { t: 48,  text: 'Inhale gently...', type: 'breath' },
  { t: 55,  text: 'Exhale completely.', type: 'breath' },
  { t: 63,  text: 'One more time.' },
  { t: 67,  text: 'Breathing in...', type: 'breath' },
  { t: 74,  text: 'And breathing out.', type: 'breath' },
  { t: 82,  text: 'Allow your shoulders to soften.' },
  { t: 87,  text: 'Relax your jaw.' },
  { t: 91,  text: 'Unclench your hands.' },
  { t: 95,  text: 'Let your body know that, for this moment, it is safe to slow down.' },
  { t: 103, text: 'When we are stressed, financial decisions feel heavy.' },
  { t: 109, text: 'We hesitate.' },
  { t: 112, text: 'We overthink.' },
  { t: 115, text: 'We delay.' },
  { t: 118, text: 'We question our value.' },
  { t: 122, text: 'But when we are regulated, decisions become simpler.' },
  { t: 128, text: 'Action becomes easier.' },
  { t: 132, text: 'Receiving becomes natural.' },
  { t: 136, text: 'Today, we begin with regulation.' },
  { t: 142, text: 'Take a slow breath in.', type: 'breath' },
  { t: 149, text: 'And an even slower breath out.', type: 'breath' },
  { t: 158, text: 'Again.' },
  { t: 162, text: 'Inhale.', type: 'breath' },
  { t: 169, text: 'Exhale.', type: 'breath' },
  { t: 177, text: 'Allow each exhale to be longer than the inhale.' },
  { t: 183, text: 'With every breath out, release what you no longer need to carry.' },
  { t: 191, text: 'Quietly repeat:' },
  { t: 196, text: 'I release pressure that is not mine to carry.', type: 'affirmation' },
  { t: 205, text: 'Again.' },
  { t: 209, text: 'I release pressure that is not mine to carry.', type: 'affirmation' },
  { t: 218, text: 'And once more.' },
  { t: 222, text: 'I release pressure that is not mine to carry.', type: 'affirmation' },
  { t: 231, text: 'Feel your body becoming lighter.' },
  { t: 237, text: 'Your mind becoming clearer.' },
  { t: 242, text: 'Your breathing becoming steadier.' },
  { t: 248, text: 'Now place one hand gently over your upper abdomen.' },
  { t: 255, text: 'Feel the warmth of your own presence.' },
  { t: 260, text: 'Feel yourself here.' },
  { t: 266, text: 'And slowly repeat:' },
  { t: 271, text: 'My work creates value.', type: 'affirmation' },
  { t: 278, text: 'My work creates value.', type: 'affirmation' },
  { t: 284, text: 'My actions create movement.', type: 'affirmation' },
  { t: 291, text: 'My actions create movement.', type: 'affirmation' },
  { t: 297, text: 'I am allowed to be paid.', type: 'affirmation' },
  { t: 304, text: 'I am allowed to be paid.', type: 'affirmation' },
  { t: 311, text: 'There is no force here.' },
  { t: 316, text: 'No proving.' },
  { t: 319, text: 'No chasing.' },
  { t: 322, text: 'Simply recognition.' },
  { t: 327, text: 'Your work creates value.' },
  { t: 332, text: 'Your actions create movement.' },
  { t: 337, text: 'And movement creates opportunity.' },
  { t: 342, text: 'Take a deeper breath now.', type: 'breath' },
  { t: 349, text: 'Feel your posture rise naturally.' },
  { t: 354, text: 'Not from effort.' },
  { t: 357, text: 'From certainty.' },
  { t: 361, text: 'Now we enter the final phase.' },
  { t: 367, text: 'Receiving.' },
  { t: 372, text: 'Breathe in for four.', type: 'breath' },
  { t: 375, text: 'Two...', type: 'count' },
  { t: 377, text: 'Three...', type: 'count' },
  { t: 379, text: 'Four...', type: 'count' },
  { t: 381, text: 'Hold.', type: 'breath' },
  { t: 383, text: 'Two.', type: 'count' },
  { t: 385, text: 'And exhale.', type: 'breath' },
  { t: 387, text: 'Two...', type: 'count' },
  { t: 389, text: 'Three...', type: 'count' },
  { t: 391, text: 'Four...', type: 'count' },
  { t: 393, text: 'Five...', type: 'count' },
  { t: 395, text: 'Six.', type: 'count' },
  { t: 397, text: 'Again.' },
  { t: 400, text: 'Inhale.', type: 'breath' },
  { t: 402, text: 'Two...', type: 'count' },
  { t: 404, text: 'Three...', type: 'count' },
  { t: 406, text: 'Four.', type: 'count' },
  { t: 408, text: 'Hold.', type: 'breath' },
  { t: 410, text: 'Two.', type: 'count' },
  { t: 412, text: 'Exhale.', type: 'breath' },
  { t: 414, text: 'Two...', type: 'count' },
  { t: 416, text: 'Three...', type: 'count' },
  { t: 418, text: 'Four...', type: 'count' },
  { t: 420, text: 'Five...', type: 'count' },
  { t: 422, text: 'Six.', type: 'count' },
  { t: 424, text: 'One final round.' },
  { t: 427, text: 'Inhale.', type: 'breath' },
  { t: 429, text: 'Two...', type: 'count' },
  { t: 431, text: 'Three...', type: 'count' },
  { t: 433, text: 'Four.', type: 'count' },
  { t: 435, text: 'Hold.', type: 'breath' },
  { t: 437, text: 'Two.', type: 'count' },
  { t: 438, text: 'Exhale.', type: 'breath' },
  { t: 439, text: 'Two...', type: 'count' },
  { t: 440, text: 'Three...', type: 'count' },
  { t: 441, text: 'Four...', type: 'count' },
  { t: 442, text: 'Five...', type: 'count' },
  { t: 443, text: 'Six.', type: 'count' },
  { t: 446, text: 'Good.' },
  { t: 449, text: 'Notice the calm that is available when you stop fighting yourself.' },
  { t: 454, text: 'Notice the clarity that appears when pressure leaves.' },
  { t: 458, text: 'Notice the space that opens when you trust your own value.' },
  { t: 463, text: 'Remember this:' },
  { t: 466, text: 'Self-belief creates action.' },
  { t: 469, text: 'Action creates receiving.' },
  { t: 472, text: 'Receiving strengthens self-belief.' },
  { t: 476, text: 'The cycle continues.' },
  { t: 479, text: 'If momentum feels slow today, keep it simple.' },
  { t: 483, text: 'One message.' },
  { t: 485, text: 'One offer.' },
  { t: 487, text: 'One post.' },
  { t: 489, text: 'One conversation.' },
  { t: 491, text: 'One action.' },
  { t: 493, text: 'Movement creates momentum.' },
  { t: 496, text: 'Momentum creates opportunity.' },
  { t: 499, text: 'And opportunity grows through consistent action.' },
  { t: 503, text: 'Take one final breath in.', type: 'breath' },
  { t: 508, text: 'And slowly let it go.', type: 'breath' },
  { t: 514, text: 'As we close, repeat softly:' },
  { t: 518, text: 'I move.', type: 'affirmation' },
  { t: 523, text: 'Money moves with me.', type: 'affirmation' },
  { t: 528, text: 'Again.' },
  { t: 531, text: 'I move.', type: 'affirmation' },
  { t: 535, text: 'Money moves with me.', type: 'affirmation' },
  { t: 540, text: 'One last time.' },
  { t: 543, text: 'I move.', type: 'affirmation' },
  { t: 547, text: 'Money moves with me.', type: 'affirmation' },
  { t: 553, text: 'Carry this feeling with you.' },
  { t: 557, text: 'Clear.' },
  { t: 560, text: 'Grounded.' },
  { t: 563, text: 'Open.' },
  { t: 566, text: 'Ready to act.' },
  { t: 569, text: 'Ready to receive.' },
  { t: 572, text: 'And ready to move forward.' },
  { t: 578, text: 'When you are ready, gently open your eyes.' },
  { t: 584, text: 'And begin.' },
];

function ResetStep({ onComplete }: { onComplete: () => void }) {
  const [playing, setPlaying]             = useState(false);
  const [audioDuration, setAudioDuration] = useState(442);
  const [audioTime, setAudioTime]         = useState(0);
  const [audioFinished, setAudioFinished] = useState(false);

  const voiceRef      = useRef<HTMLAudioElement | null>(null);
  const ambientRef    = useRef<HTMLAudioElement | null>(null);
  const onCompleteRef = useRef(onComplete);
  const scrollRef     = useRef<HTMLDivElement>(null);
  const lineRefs      = useRef<(HTMLDivElement | null)[]>([]);

  useEffect(() => { onCompleteRef.current = onComplete; }, [onComplete]);

  useEffect(() => {
    const voice   = new Audio('/oracle-reset.mp3');
    const ambient = new Audio('/oracle-ambient.mp3');
    ambient.loop    = true;
    ambient.volume  = 0.22;
    voice.preload   = 'auto';
    ambient.preload = 'auto';

    voice.addEventListener('loadedmetadata', () => {
      setAudioDuration(voice.duration > 0 ? voice.duration : 442);
    });
    voice.addEventListener('timeupdate', () => setAudioTime(voice.currentTime));
    voice.addEventListener('ended', () => {
      setPlaying(false);
      setAudioFinished(true);
      ambient.pause();
    });
    voice.addEventListener('error', () => {}); // silent — UI still usable

    voiceRef.current   = voice;
    ambientRef.current = ambient;
    return () => { voice.pause(); ambient.pause(); };
  }, []);

  const togglePlay = () => {
    const voice   = voiceRef.current!;
    const ambient = ambientRef.current!;
    if (playing) {
      voice.pause(); ambient.pause(); setPlaying(false);
    } else {
      voice.play().catch(() => {});
      ambient.play().catch(() => {});
      setPlaying(true);
    }
  };

  // ── Calibration mode — tap-mark exact timestamps against the real audio ────
  const [calibrating, setCalibrating]         = useState(false);
  const [calibrateIdx, setCalibrateIdx]       = useState(0);
  const [calibratedTimes, setCalibratedTimes] = useState<(number | null)[]>(() => RESET_LYRICS.map(() => null));
  const [showExport, setShowExport]           = useState(false);
  const [copied, setCopied]                   = useState(false);

  const startCalibration = () => {
    setCalibrating(true);
    setShowExport(false);
    setCalibrateIdx(0);
    setCalibratedTimes(RESET_LYRICS.map(() => null));
    if (voiceRef.current) {
      voiceRef.current.currentTime = 0;
      voiceRef.current.play().catch(() => {});
    }
    ambientRef.current?.play().catch(() => {});
    setPlaying(true);
  };

  const stopCalibration = () => {
    setCalibrating(false);
    setShowExport(false);
    if (voiceRef.current) { voiceRef.current.pause(); }
    ambientRef.current?.pause();
    setPlaying(false);
  };

  const markLine = () => {
    const t = voiceRef.current ? voiceRef.current.currentTime : audioTime;
    setCalibratedTimes(prev => {
      const next = [...prev];
      next[calibrateIdx] = Math.round(t * 10) / 10;
      return next;
    });
    if (calibrateIdx < RESET_LYRICS.length - 1) {
      setCalibrateIdx(i => i + 1);
    } else {
      voiceRef.current?.pause();
      ambientRef.current?.pause();
      setPlaying(false);
      setShowExport(true);
    }
  };

  const goBackLine = () => setCalibrateIdx(i => Math.max(0, i - 1));

  useEffect(() => {
    if (!calibrating || showExport) return;
    const handler = (e: KeyboardEvent) => {
      if (e.code === 'Space')     { e.preventDefault(); markLine(); }
      if (e.code === 'ArrowLeft') { e.preventDefault(); goBackLine(); }
    };
    window.addEventListener('keydown', handler);
    return () => window.removeEventListener('keydown', handler);
  }, [calibrating, showExport, calibrateIdx]);

  const exportText = RESET_LYRICS.map((line, i) => {
    const tv = calibratedTimes[i] !== null ? calibratedTimes[i] : line.t;
    const typeStr = line.type ? `, type: '${line.type}'` : '';
    return `  { t: ${tv}, text: ${JSON.stringify(line.text)}${typeStr} },`;
  }).join('\n');

  const handleCopy = () => {
    navigator.clipboard.writeText(exportText).then(() => {
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    });
  };

  // Active lyric index
  const activeIdx = RESET_LYRICS.reduce((acc, line, i) => line.t <= audioTime ? i : acc, 0);
  const activeLine = RESET_LYRICS[activeIdx];

  // Scroll active line to centre
  useEffect(() => {
    const container = scrollRef.current;
    const el = lineRefs.current[activeIdx];
    if (!container || !el) return;
    const target = el.offsetTop - container.clientHeight / 2 + el.offsetHeight / 2;
    container.scrollTo({ top: Math.max(0, target), behavior: 'smooth' });
  }, [activeIdx]);

  const pct = audioDuration > 0 ? (audioTime / audioDuration) * 100 : 0;

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      style={{ maxWidth: 520, margin: '0 auto', display: 'flex', flexDirection: 'column', height: 'calc(100vh - 180px)', minHeight: 500 }}
    >
      {/* Tiny header badge */}
      <div style={{ textAlign: 'center', marginBottom: 12, flexShrink: 0, position: 'relative' }}>
        <div style={{ display: 'inline-flex', alignItems: 'center', gap: 7 }}>
          <motion.div
            animate={{ opacity: [0.4, 1, 0.4] }}
            transition={{ duration: playing ? 2 : 99, repeat: Infinity }}
            style={{ width: 5, height: 5, borderRadius: '50%', background: calibrating ? '#B08DE8' : '#00D4AA', boxShadow: `0 0 5px ${calibrating ? '#B08DE8' : '#00D4AA'}` }}
          />
          <span style={{ fontFamily: 'monospace', fontSize: 8, letterSpacing: '0.3em', textTransform: 'uppercase', color: calibrating ? 'rgba(176,141,232,0.5)' : 'rgba(0,212,170,0.35)' }}>
            {calibrating ? 'Calibration Mode' : playing ? 'Field Calibration Active' : 'Field Calibration · 7 min'}
          </span>
        </div>
        <button
          onClick={() => (calibrating ? stopCalibration() : startCalibration())}
          style={{
            position: 'absolute', right: 0, top: -2,
            background: 'none',
            border: `1px solid ${calibrating ? 'rgba(176,141,232,0.4)' : 'rgba(255,255,255,0.08)'}`,
            borderRadius: 6, padding: '3px 8px',
            color: calibrating ? '#B08DE8' : 'rgba(232,232,232,0.22)',
            fontFamily: 'monospace', fontSize: 8, letterSpacing: '0.08em', textTransform: 'uppercase', cursor: 'pointer',
          }}
        >
          {calibrating ? '✕ Exit' : '⚙ Calibrate'}
        </button>
      </div>

      {calibrating ? (
        <div style={{ flex: 1, display: 'flex', flexDirection: 'column' }}>
          {!showExport ? (
            <>
              <div style={{ flex: 1, display: 'flex', flexDirection: 'column', justifyContent: 'center', alignItems: 'center', padding: '0 20px' }}>
                <p style={{ fontFamily: 'monospace', fontSize: 9, color: 'rgba(176,141,232,0.5)', letterSpacing: '0.2em', marginBottom: 14 }}>
                  LINE {calibrateIdx + 1} / {RESET_LYRICS.length}
                </p>
                <p style={{
                  fontFamily: RESET_LYRICS[calibrateIdx].type === 'count' ? 'ui-monospace, monospace' : 'serif',
                  fontSize: 24, textAlign: 'center', color: '#EAEAEA', lineHeight: 1.5, maxWidth: 440, margin: 0,
                }}>
                  {RESET_LYRICS[calibrateIdx].text}
                </p>
                {calibratedTimes[calibrateIdx] !== null && (
                  <p style={{ fontFamily: 'monospace', fontSize: 10, color: '#00D4AA', marginTop: 14 }}>
                    marked @ {fmt(Math.floor(calibratedTimes[calibrateIdx]!))}
                  </p>
                )}
              </div>

              <div style={{ padding: '14px 0' }}>
                <div style={{ height: 2, background: 'rgba(255,255,255,0.07)', borderRadius: 1, marginBottom: 14 }}>
                  <motion.div
                    animate={{ width: `${pct}%` }}
                    transition={{ duration: 0.3, ease: 'linear' }}
                    style={{ height: '100%', borderRadius: 1, background: '#B08DE8' }}
                  />
                </div>

                <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', gap: 10, marginBottom: 12 }}>
                  <button
                    onClick={togglePlay}
                    style={{ width: 44, height: 44, borderRadius: '50%', border: '1px solid rgba(176,141,232,0.3)', background: 'rgba(176,141,232,0.06)', color: '#B08DE8', cursor: 'pointer', fontSize: 14 }}
                  >
                    {playing ? '⏸' : '▶'}
                  </button>
                  <button
                    onClick={markLine}
                    style={{ padding: '0 26px', height: 44, borderRadius: 22, border: '1px solid rgba(176,141,232,0.5)', background: 'rgba(176,141,232,0.14)', color: '#B08DE8', fontFamily: 'sans-serif', fontSize: 11, letterSpacing: '0.1em', textTransform: 'uppercase', cursor: 'pointer', fontWeight: 600 }}
                  >
                    ⏱ Mark (Space)
                  </button>
                  <button
                    onClick={goBackLine}
                    disabled={calibrateIdx === 0}
                    style={{ width: 44, height: 44, borderRadius: '50%', border: '1px solid rgba(255,255,255,0.1)', background: 'rgba(255,255,255,0.02)', color: 'rgba(232,232,232,0.4)', cursor: calibrateIdx === 0 ? 'default' : 'pointer', opacity: calibrateIdx === 0 ? 0.3 : 1 }}
                  >
                    ←
                  </button>
                </div>
                <p style={{ textAlign: 'center', fontFamily: 'sans-serif', fontSize: 9, color: 'rgba(232,232,232,0.2)', letterSpacing: '0.06em' }}>
                  Play the audio, tap Mark the instant this line is spoken.
                </p>
              </div>
            </>
          ) : (
            <div style={{ flex: 1, display: 'flex', flexDirection: 'column', padding: '10px 0' }}>
              <p style={{ fontFamily: 'sans-serif', fontSize: 11, color: '#00D4AA', letterSpacing: '0.12em', textTransform: 'uppercase', marginBottom: 10, textAlign: 'center' }}>
                ✓ Calibration Complete — {RESET_LYRICS.length} lines
              </p>
              <textarea
                readOnly
                value={exportText}
                style={{ flex: 1, minHeight: 200, background: 'rgba(0,0,0,0.3)', border: '1px solid rgba(176,141,232,0.2)', borderRadius: 8, color: 'rgba(232,232,232,0.7)', fontFamily: 'ui-monospace, monospace', fontSize: 10, padding: 12, resize: 'none', marginBottom: 12 }}
              />
              <div style={{ display: 'flex', gap: 8 }}>
                <button
                  onClick={handleCopy}
                  style={{ flex: 1, padding: 12, background: 'rgba(176,141,232,0.1)', border: '1px solid rgba(176,141,232,0.4)', borderRadius: 8, color: '#B08DE8', fontFamily: 'sans-serif', fontSize: 10, letterSpacing: '0.12em', textTransform: 'uppercase', cursor: 'pointer' }}
                >
                  {copied ? '✓ Copied' : 'Copy Array'}
                </button>
                <a
                  href={`data:text/plain;charset=utf-8,${encodeURIComponent(exportText)}`}
                  download="reset-lyrics-calibrated.txt"
                  style={{ flex: 1, padding: 12, textAlign: 'center', background: 'rgba(255,255,255,0.03)', border: '1px solid rgba(255,255,255,0.1)', borderRadius: 8, color: 'rgba(232,232,232,0.5)', fontFamily: 'sans-serif', fontSize: 10, letterSpacing: '0.12em', textTransform: 'uppercase', textDecoration: 'none' }}
                >
                  Download
                </a>
              </div>
              <button
                onClick={stopCalibration}
                style={{ marginTop: 10, background: 'none', border: 'none', color: 'rgba(232,232,232,0.2)', fontFamily: 'sans-serif', fontSize: 9, letterSpacing: '0.12em', textTransform: 'uppercase', cursor: 'pointer' }}
              >
                Exit Calibration
              </button>
            </div>
          )}
        </div>
      ) : (
        <>
          {/* ── Lyrics scroll ── */}
          <div
            ref={scrollRef}
            className="hide-scrollbar"
            style={{
              flex: 1,
              overflowY: 'auto',
              paddingTop: '35%',
              paddingBottom: '35%',
              WebkitOverflowScrolling: 'touch',
            }}
          >
            {RESET_LYRICS.map((line, i) => {
              const dist     = i - activeIdx;
              const isActive = dist === 0;
              const isNear   = Math.abs(dist) === 1;
              const isFar    = Math.abs(dist) === 2;
              const type     = line.type;

              let color = '#EAEAEA';
              if (type === 'breath')      color = '#00D4AA';
              if (type === 'affirmation') color = '#C9A84C';
              if (type === 'count')       color = '#B08DE8';

              const opacity  = isActive ? 1 : isNear ? 0.22 : isFar ? 0.1 : 0.04;
              const fontSize = isActive ? (type === 'count' ? 26 : 21) : isNear ? 14 : 12;

              return (
                <div
                  key={i}
                  ref={el => { lineRefs.current[i] = el; }}
                  style={{ padding: `${isActive ? 9 : 4}px 20px`, textAlign: 'center' }}
                >
                  <motion.p
                    animate={{ opacity, fontSize }}
                    transition={{ duration: 0.45, ease: 'easeOut' }}
                    style={{
                      fontFamily: type === 'count' ? 'ui-monospace, monospace' : 'serif',
                      color,
                      margin: '0 auto',
                      lineHeight: 1.4,
                      letterSpacing: isActive ? '0.04em' : '0.01em',
                      maxWidth: 480,
                      cursor: 'default',
                      userSelect: 'none',
                    }}
                  >
                    {line.text}
                  </motion.p>
                </div>
              );
            })}
          </div>

          {/* ── Bottom controls ── */}
          <div style={{ flexShrink: 0, paddingTop: 14 }}>

            {/* Progress bar */}
            <div
              style={{ marginBottom: 10, cursor: 'pointer' }}
              onClick={e => {
                const rect = (e.currentTarget as HTMLElement).getBoundingClientRect();
                const t = ((e.clientX - rect.left) / rect.width) * audioDuration;
                if (voiceRef.current) voiceRef.current.currentTime = t;
              }}
            >
              <div style={{ height: 2, background: 'rgba(255,255,255,0.07)', borderRadius: 1 }}>
                <motion.div
                  animate={{ width: `${pct}%` }}
                  transition={{ duration: 0.35, ease: 'linear' }}
                  style={{
                    height: '100%',
                    borderRadius: 1,
                    background: activeLine?.type === 'affirmation' ? '#C9A84C'
                      : activeLine?.type === 'breath' ? '#00D4AA'
                      : activeLine?.type === 'count' ? '#B08DE8'
                      : 'rgba(232,232,232,0.45)',
                    transition: 'background 1.2s ease',
                  }}
                />
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between', marginTop: 5 }}>
                <span style={{ fontFamily: 'monospace', fontSize: 9, color: 'rgba(232,232,232,0.18)' }}>
                  {fmt(Math.floor(audioTime))}
                </span>
                <span style={{ fontFamily: 'monospace', fontSize: 9, color: 'rgba(232,232,232,0.18)' }}>
                  {fmt(Math.floor(audioDuration))}
                </span>
              </div>
            </div>

            {/* Play / pause */}
            <div style={{ display: 'flex', justifyContent: 'center', marginBottom: 14 }}>
              <motion.button
                onClick={togglePlay}
                whileTap={{ scale: 0.92 }}
                style={{
                  width: 50, height: 50, borderRadius: '50%',
                  background: 'rgba(255,255,255,0.04)',
                  border: `1px solid ${playing ? 'rgba(0,212,170,0.35)' : 'rgba(255,255,255,0.1)'}`,
                  color: playing ? '#00D4AA' : 'rgba(232,232,232,0.7)',
                  display: 'flex', alignItems: 'center', justifyContent: 'center',
                  cursor: 'pointer', transition: 'border-color 0.3s, color 0.3s',
                }}
              >
                {playing ? (
                  <svg width="14" height="14" viewBox="0 0 14 14" fill="currentColor">
                    <rect x="2" y="2" width="3.5" height="10" rx="1"/>
                    <rect x="8.5" y="2" width="3.5" height="10" rx="1"/>
                  </svg>
                ) : (
                  <svg width="14" height="14" viewBox="0 0 14 14" fill="currentColor">
                    <path d="M3 2l9 5-9 5V2z"/>
                  </svg>
                )}
              </motion.button>
            </div>

            {/* CTA after audio finishes */}
            <AnimatePresence>
              {audioFinished && (
                <motion.div
                  initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.5 }}
                  style={{ marginBottom: 12, padding: '16px 20px', background: 'linear-gradient(135deg, rgba(0,212,170,0.1), rgba(0,212,170,0.04))', border: '1px solid rgba(0,212,170,0.45)', borderRadius: 10, textAlign: 'center' }}
                >
                  <p style={{ fontFamily: 'sans-serif', fontSize: 9, letterSpacing: '0.22em', textTransform: 'uppercase', color: 'rgba(0,212,170,0.55)', margin: '0 0 10px' }}>
                    Reset Complete
                  </p>
                  <button
                    onClick={() => onCompleteRef.current()}
                    style={{ width: '100%', padding: '13px', background: 'rgba(0,212,170,0.1)', border: '1px solid rgba(0,212,170,0.5)', borderRadius: 8, color: '#00D4AA', fontFamily: 'sans-serif', fontSize: 10, letterSpacing: '0.22em', textTransform: 'uppercase', cursor: 'pointer' }}
                  >
                    ⟐ Begin Diagnostic
                  </button>
                </motion.div>
              )}
            </AnimatePresence>

            {/* Skip links */}
            <div style={{ textAlign: 'center', paddingBottom: 8 }}>
              {!playing && audioTime === 0 && !audioFinished && (
                <button
                  onClick={() => onCompleteRef.current()}
                  style={{ background: 'none', border: 'none', color: 'rgba(232,232,232,0.2)', fontFamily: 'sans-serif', fontSize: 9, letterSpacing: '0.16em', textTransform: 'uppercase', cursor: 'pointer' }}
                >
                  Skip Reset → Begin Diagnostic
                </button>
              )}
              {(playing || audioTime > 0) && !audioFinished && (
                <button
                  onClick={() => onCompleteRef.current()}
                  style={{ background: 'none', border: 'none', color: 'rgba(232,232,232,0.12)', fontFamily: 'sans-serif', fontSize: 9, letterSpacing: '0.16em', textTransform: 'uppercase', cursor: 'pointer' }}
                >
                  Skip — go to diagnostic
                </button>
              )}
            </div>
          </div>
        </>
      )}
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
