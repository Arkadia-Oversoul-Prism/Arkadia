import React, { useEffect, useMemo, useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';

interface Props { onNavigate: (view: string) => void }

interface ChallengeState {
  version: 1;
  startedAt: string;
  answers: Record<string, string>;
  completedAt?: string;
}

const PROMPTS = [
  { id: 'problem', eyebrow: '01 · THINK', title: 'Find the useful problem.', prompt: 'Choose a real person, business, community, or project. What problem could you help solve?', helper: 'Be specific. A small real problem is better than a grand imaginary one.' },
  { id: 'research', eyebrow: '02 · RESEARCH', title: 'Get signal before you build.', prompt: 'What do you need to find out before proposing a solution, and where would you look?', helper: 'Name the questions, sources, people, or tools you would use.' },
  { id: 'solution', eyebrow: '03 · BUILD', title: 'Design the first useful version.', prompt: 'What would you actually create or do to solve the problem?', helper: 'Think workflow, artifact, prototype, service, content system, or decision brief.' },
  { id: 'proof', eyebrow: '04 · PROVE', title: 'Show the evidence.', prompt: 'What would you produce so someone else could tell whether your solution works?', helper: 'Name the artifact, demonstration, result, test, or feedback you would use.' },
  { id: 'value', eyebrow: '05 · LAUNCH', title: 'Make the value legible.', prompt: 'Who would benefit from this, and what useful outcome could you offer them?', helper: 'Finish the thought: “I help ___ achieve ___ by ___.”' },
];

const STORAGE_KEY = 'arkadia.ais.future-skills-challenge.v1';
const LIMIT_MS = 60 * 60 * 1000;

function readState(): ChallengeState | null {
  try {
    const raw = sessionStorage.getItem(STORAGE_KEY);
    return raw ? JSON.parse(raw) as ChallengeState : null;
  } catch { return null; }
}

export default function FutureSkillsChallenge({ onNavigate }: Props) {
  const existing = readState();
  const [startedAt, setStartedAt] = useState(existing?.startedAt ?? '');
  const [index, setIndex] = useState(existing ? Math.min(Object.keys(existing.answers).length, PROMPTS.length - 1) : -1);
  const [answers, setAnswers] = useState<Record<string, string>>(existing?.answers ?? {});
  const [remaining, setRemaining] = useState(() => existing ? Math.max(0, LIMIT_MS - (Date.now() - Date.parse(existing.startedAt))) : LIMIT_MS);
  const [complete, setComplete] = useState(Boolean(existing?.completedAt));

  useEffect(() => {
    if (!startedAt || complete) return;
    const timer = window.setInterval(() => setRemaining(Math.max(0, LIMIT_MS - (Date.now() - Date.parse(startedAt)))), 1000);
    return () => window.clearInterval(timer);
  }, [startedAt, complete]);

  useEffect(() => {
    if (!startedAt || complete) return;
    try { sessionStorage.setItem(STORAGE_KEY, JSON.stringify({ version: 1, startedAt, answers })); } catch {}
  }, [answers, startedAt, complete]);

  const minutes = Math.floor(remaining / 60000);
  const seconds = Math.floor((remaining % 60000) / 1000).toString().padStart(2, '0');
  const current = index >= 0 ? PROMPTS[index] : null;
  const canNext = current ? answers[current.id]?.trim().length > 0 : false;
  const progress = useMemo(() => index < 0 ? 0 : Math.round(((index + 1) / PROMPTS.length) * 100), [index]);

  const start = () => {
    const now = new Date().toISOString();
    setStartedAt(now);
    setRemaining(LIMIT_MS);
    setIndex(0);
    try { sessionStorage.setItem(STORAGE_KEY, JSON.stringify({ version: 1, startedAt: now, answers: {} })); } catch {}
  };

  const updateAnswer = (value: string) => current && setAnswers(prev => ({ ...prev, [current.id]: value }));

  const next = () => {
    if (!current || !canNext) return;
    if (index === PROMPTS.length - 1) {
      const completedAt = new Date().toISOString();
      const state: ChallengeState = { version: 1, startedAt, answers, completedAt };
      try { sessionStorage.setItem(STORAGE_KEY, JSON.stringify(state)); } catch {}
      setComplete(true);
      return;
    }
    setIndex(value => value + 1);
  };

  const reset = () => {
    try { sessionStorage.removeItem(STORAGE_KEY); } catch {}
    setStartedAt(''); setIndex(-1); setAnswers({}); setRemaining(LIMIT_MS); setComplete(false);
  };

  if (complete) return (
    <main className="min-h-screen w-full relative overflow-hidden" data-testid="future-skills-challenge-complete">
      <div className="aurora-bg" />
      <div className="page-column relative z-10 pt-12 pb-20">
        <motion.section initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} style={{ maxWidth: 640, margin: '0 auto', padding: '30px 24px', background: 'rgba(14,17,32,.82)', border: '1px solid rgba(0,212,170,.2)', borderRadius: 18 }}>
          <p style={{ fontFamily: 'sans-serif', fontSize: 8, letterSpacing: '.3em', textTransform: 'uppercase', color: 'rgba(0,212,170,.65)', margin: '0 0 10px' }}>Challenge complete</p>
          <h1 style={{ fontFamily: 'serif', fontWeight: 400, fontSize: 34, color: '#F0F0EE', margin: '0 0 12px' }}>You made the signal visible.</h1>
          <p style={{ fontFamily: 'sans-serif', fontSize: 12, lineHeight: 1.75, color: 'rgba(232,232,232,.55)', margin: '0 0 22px' }}>Your work is saved locally for this session. The next step is to turn what you just demonstrated into your A.I.S Capability Portfolio.</p>
          <div style={{ display: 'grid', gap: 7, marginBottom: 22 }}>
            {PROMPTS.map((item, i) => <div key={item.id} style={{ padding: '11px 13px', border: '1px solid rgba(255,255,255,.06)', borderRadius: 9, background: 'rgba(255,255,255,.018)' }}><span style={{ fontFamily: 'sans-serif', fontSize: 8, letterSpacing: '.15em', color: 'rgba(201,168,76,.55)' }}>{item.eyebrow}</span><p style={{ fontFamily: 'sans-serif', fontSize: 11, lineHeight: 1.5, color: 'rgba(232,232,232,.62)', margin: '4px 0 0' }}>{answers[item.id] || 'Completed'}</p></div>)}
          </div>
          <button type="button" data-testid="challenge-to-diagnostic" onClick={() => onNavigate('gate')} style={{ width: '100%', padding: 15, background: 'linear-gradient(135deg,rgba(0,212,170,.18),rgba(0,212,170,.06))', border: '1px solid rgba(0,212,170,.55)', borderRadius: 10, color: '#00D4AA', fontFamily: 'sans-serif', fontSize: 9, letterSpacing: '.2em', textTransform: 'uppercase', cursor: 'pointer' }}>Build my free A.I.S capability profile →</button>
          <button type="button" onClick={reset} style={{ width: '100%', marginTop: 8, padding: 11, background: 'transparent', border: '0', color: 'rgba(232,232,232,.3)', fontFamily: 'sans-serif', fontSize: 9, cursor: 'pointer' }}>Run the challenge again</button>
        </motion.section>
      </div>
    </main>
  );

  if (index < 0) return (
    <main className="min-h-screen w-full relative overflow-hidden" data-testid="future-skills-challenge">
      <div className="aurora-bg" />
      <div className="page-column relative z-10 pt-12 pb-20">
        <motion.section initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} style={{ maxWidth: 640, margin: '0 auto', textAlign: 'center', padding: '24px 20px' }}>
          <p style={{ fontFamily: 'sans-serif', fontSize: 8, letterSpacing: '.32em', textTransform: 'uppercase', color: 'rgba(0,212,170,.62)', margin: '0 0 12px' }}>A.I.S · Future Skills Lab</p>
          <h1 style={{ fontFamily: 'serif', fontWeight: 400, fontSize: 'clamp(34px,8vw,50px)', lineHeight: 1.05, color: '#F0F0EE', margin: '0 0 14px' }}>Can you solve a real problem with AI?</h1>
          <p style={{ fontFamily: 'sans-serif', fontSize: 12, lineHeight: 1.8, color: 'rgba(232,232,232,.52)', maxWidth: 520, margin: '0 auto 22px' }}>A self-guided 60-minute challenge. Think, research, design, prove, and explain a useful solution. No lecture. No certificate. Just a practical signal of what you can do.</p>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(5,minmax(0,1fr))', gap: 6, marginBottom: 24 }}>{['Think','Research','Build','Prove','Launch'].map((label, i) => <div key={label} style={{ padding: '10px 4px', border: '1px solid rgba(255,255,255,.06)', borderRadius: 8 }}><span style={{ display: 'block', fontFamily: 'sans-serif', fontSize: 7, color: 'rgba(201,168,76,.5)', marginBottom: 4 }}>0{i + 1}</span><span style={{ fontFamily: 'sans-serif', fontSize: 8, color: 'rgba(232,232,232,.48)' }}>{label}</span></div>)}</div>
          <button type="button" data-testid="start-future-skills-challenge" onClick={start} style={{ width: '100%', padding: 16, background: 'linear-gradient(135deg,rgba(0,212,170,.18),rgba(0,212,170,.06))', border: '1px solid rgba(0,212,170,.55)', borderRadius: 11, color: '#00D4AA', fontFamily: 'sans-serif', fontSize: 9, letterSpacing: '.2em', textTransform: 'uppercase', cursor: 'pointer' }}>Start the 60-minute challenge →</button>
          <button type="button" onClick={() => onNavigate('gate')} style={{ marginTop: 12, background: 'transparent', border: 0, color: 'rgba(232,232,232,.32)', fontFamily: 'sans-serif', fontSize: 9, cursor: 'pointer' }}>Skip straight to my A.I.S profile</button>
        </motion.section>
      </div>
    </main>
  );

  return (
    <main className="min-h-screen w-full relative overflow-hidden" data-testid="future-skills-challenge-active">
      <div className="aurora-bg" />
      <div className="page-column relative z-10 pt-10 pb-20">
        <div style={{ maxWidth: 640, margin: '0 auto' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'end', marginBottom: 18 }}>
            <div><p style={{ fontFamily: 'sans-serif', fontSize: 8, letterSpacing: '.28em', textTransform: 'uppercase', color: 'rgba(0,212,170,.58)', margin: '0 0 6px' }}>Future Skills Lab</p><p style={{ fontFamily: 'sans-serif', fontSize: 9, color: 'rgba(232,232,232,.3)', margin: 0 }}>{index + 1} / {PROMPTS.length}</p></div>
            <span data-testid="challenge-timer" style={{ fontFamily: 'monospace', fontSize: 14, color: remaining < 300000 ? '#C9A84C' : 'rgba(232,232,232,.5)' }}>{minutes}:{seconds}</span>
          </div>
          <div style={{ height: 2, background: 'rgba(255,255,255,.06)', marginBottom: 24 }}><motion.div animate={{ width: `${progress}%` }} style={{ height: '100%', background: 'linear-gradient(90deg,#00D4AA,#C9A84C)' }} /></div>
          <AnimatePresence mode="wait"><motion.section key={current?.id} initial={{ opacity: 0, x: 14 }} animate={{ opacity: 1, x: 0 }} exit={{ opacity: 0, x: -14 }} style={{ padding: '25px 21px', background: 'rgba(14,17,32,.78)', border: '1px solid rgba(255,255,255,.07)', borderRadius: 15 }}>
            <p style={{ fontFamily: 'sans-serif', fontSize: 8, letterSpacing: '.28em', textTransform: 'uppercase', color: '#C9A84C', margin: '0 0 9px' }}>{current?.eyebrow}</p>
            <h1 style={{ fontFamily: 'serif', fontWeight: 400, fontSize: 28, color: '#F0F0EE', margin: '0 0 9px' }}>{current?.title}</h1>
            <p style={{ fontFamily: 'sans-serif', fontSize: 12, lineHeight: 1.7, color: 'rgba(232,232,232,.62)', margin: '0 0 8px' }}>{current?.prompt}</p>
            <p style={{ fontFamily: 'sans-serif', fontSize: 9, lineHeight: 1.6, color: 'rgba(232,232,232,.3)', margin: '0 0 16px' }}>{current?.helper}</p>
            <textarea autoFocus value={current ? answers[current.id] ?? '' : ''} onChange={event => updateAnswer(event.target.value)} placeholder="Write your thinking here…" style={{ width: '100%', minHeight: 170, boxSizing: 'border-box', resize: 'vertical', padding: 14, borderRadius: 10, border: '1px solid rgba(255,255,255,.09)', background: 'rgba(255,255,255,.025)', color: '#E8E8E8', fontFamily: 'sans-serif', fontSize: 12, lineHeight: 1.7, outline: 'none' }} />
          </motion.section></AnimatePresence>
          <div style={{ display: 'flex', gap: 8, marginTop: 10 }}>
            {index > 0 && <button type="button" onClick={() => setIndex(value => value - 1)} style={{ padding: '12px 16px', background: 'rgba(255,255,255,.02)', border: '1px solid rgba(255,255,255,.07)', borderRadius: 9, color: 'rgba(232,232,232,.35)', cursor: 'pointer' }}>←</button>}
            <button type="button" disabled={!canNext} onClick={next} style={{ flex: 1, padding: 13, background: canNext ? 'rgba(0,212,170,.1)' : 'rgba(255,255,255,.02)', border: `1px solid ${canNext ? 'rgba(0,212,170,.45)' : 'rgba(255,255,255,.07)'}`, borderRadius: 9, color: canNext ? '#00D4AA' : 'rgba(232,232,232,.22)', fontFamily: 'sans-serif', fontSize: 9, letterSpacing: '.18em', textTransform: 'uppercase', cursor: canNext ? 'pointer' : 'not-allowed' }}>{index === PROMPTS.length - 1 ? 'Complete challenge →' : 'Next →'}</button>
          </div>
          <p style={{ textAlign: 'center', fontFamily: 'sans-serif', fontSize: 8, color: 'rgba(232,232,232,.18)', marginTop: 12 }}>Self-guided · session-only · no reviewer required</p>
        </div>
      </div>
    </main>
  );
}
