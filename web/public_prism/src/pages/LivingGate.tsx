import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useSpiralQuantumResonance } from '../hooks/useSpiralQuantumResonance';
import MoonPhaseRing from '../components/MoonPhaseRing';

const API_BASE = import.meta.env.VITE_API_URL || 'https://arkadia-n26k.onrender.com';

interface LivingGateProps {
  onEnterField: (soulPhrase: string) => void;
}

type GateMode = 'oracle' | 'ims';
type IMSStep = 'intro' | 'form' | 'questionnaire' | 'confirmed';

interface IMSForm {
  name: string; email: string; phone: string;
}

const QUESTIONNAIRE = [
  { id: 'q1', question: 'What is your primary work or creative practice right now?' },
  { id: 'q2', question: 'What feels most fractured or unclear in your sense of self — the part you keep circling back to?' },
  { id: 'q3', question: 'What is the most important decision you have been avoiding, and what story have you been telling yourself about why?' },
  { id: 'q4', question: 'What do you most want others to understand about you — that they currently do not?' },
  { id: 'q5', question: 'If you knew there were no consequences, what would you say or do differently right now?' },
];

export default function LivingGate({ onEnterField }: LivingGateProps) {
  const { resonance, flameHue } = useSpiralQuantumResonance(true, 8000);
  const [mode, setMode] = useState<GateMode>('oracle');

  // Oracle state
  const [phrase, setPhrase] = useState('');
  const [entering, setEntering] = useState(false);

  // IMS state
  const [imsStep, setImsStep] = useState<IMSStep>('intro');
  const [imsForm, setImsForm] = useState<IMSForm>({ name: '', email: '', phone: '' });
  const [answers, setAnswers] = useState<Record<string, string>>({});
  const [submitting, setSubmitting] = useState(false);
  const [submitError, setSubmitError] = useState<string | null>(null);

  const handleOracleSubmit = () => {
    if (!phrase.trim()) return;
    setEntering(true);
    setTimeout(() => { onEnterField(phrase.trim()); }, 900);
  };

  const handleIMSFormNext = () => {
    if (!imsForm.name.trim() || !imsForm.email.trim()) return;
    setImsStep('questionnaire');
  };

  const handleIMSSubmit = async () => {
    setSubmitting(true); setSubmitError(null);
    try {
      await fetch(`${API_BASE}/api/ims/inquiry`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ ...imsForm, answers }),
      });
      setImsStep('confirmed');
    } catch {
      setSubmitError('Could not submit. Email arkanaofarkadia@gmail.com or WhatsApp +234 814 494 2818');
    } finally { setSubmitting(false); }
  };

  const inputStyle: React.CSSProperties = {
    width: '100%', padding: '12px 16px', background: 'rgba(255,255,255,0.03)',
    border: '1px solid rgba(255,255,255,0.1)', borderRadius: '10px',
    color: '#E8E8E8', fontFamily: 'sans-serif', fontSize: '13px',
    outline: 'none', boxSizing: 'border-box', marginBottom: '12px',
  };

  return (
    <div className="relative w-full min-h-screen flex flex-col items-center justify-start px-5 py-12"
      style={{ backgroundColor: '#0A0A0F', overflow: 'hidden' }}>

      {/* Ambient background */}
      <motion.div className="absolute inset-0 pointer-events-none"
        animate={{ background: ['radial-gradient(circle at 50% 40%, rgba(0,212,170,0.04) 0%, transparent 65%)', 'radial-gradient(circle at 50% 40%, rgba(0,212,170,0.07) 0%, transparent 65%)', 'radial-gradient(circle at 50% 40%, rgba(0,212,170,0.04) 0%, transparent 65%)'] }}
        transition={{ duration: 8, repeat: Infinity }} />

      <motion.div className="absolute pointer-events-none" style={{ top: '50%', left: '50%', transform: 'translate(-50%, -50%)' }}
        animate={{ scale: [1, 1.08 * resonance, 1], opacity: [0.08, 0.18, 0.08] }} transition={{ duration: 6, repeat: Infinity }}>
        <div style={{ width: '380px', height: '380px', borderRadius: '50%', border: `1px solid hsl(${flameHue}, 80%, 65%)` }} />
      </motion.div>

      <motion.div className="absolute top-0 bottom-0 pointer-events-none"
        style={{ left: '50%', width: '1px', background: 'linear-gradient(180deg, transparent, rgba(201,168,76,0.12), transparent)' }}
        initial={{ scaleY: 0, opacity: 0 }} animate={{ scaleY: 1, opacity: 1 }} transition={{ duration: 2, ease: 'easeOut' }} />

      {/* Mode toggle */}
      <motion.div initial={{ opacity: 0, y: -10 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.3 }}
        className="relative z-10 mb-8 w-full" style={{ maxWidth: '460px' }}>
        <div style={{ display: 'flex', gap: '8px', padding: '6px', background: 'rgba(255,255,255,0.03)', border: '1px solid rgba(255,255,255,0.07)', borderRadius: '12px' }}>
          {([
            { id: 'oracle', label: '⟐ Commune with Oracle', color: '#00D4AA' },
            { id: 'ims',    label: '✦ Identity Mapping',    color: '#C9A84C' },
          ] as { id: GateMode; label: string; color: string }[]).map(m => (
            <button key={m.id} onClick={() => { setMode(m.id); setImsStep('intro'); }}
              style={{ flex: 1, padding: '10px 12px', background: mode === m.id ? `${m.color}12` : 'transparent', border: `1px solid ${mode === m.id ? m.color + '44' : 'transparent'}`, borderRadius: '8px', color: mode === m.id ? m.color : 'rgba(232,232,232,0.35)', fontFamily: 'sans-serif', fontSize: '10px', letterSpacing: '0.15em', textTransform: 'uppercase', cursor: 'pointer', transition: 'all 0.2s' }}>
              {m.label}
            </button>
          ))}
        </div>
      </motion.div>

      {/* ─── ORACLE MODE ─────────────────────────────────────────────────────── */}
      <AnimatePresence mode="wait">
        {mode === 'oracle' && (
          <motion.div key="oracle-panel" initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0 }} transition={{ duration: 0.5 }}
            className="relative z-10 w-full" style={{ maxWidth: '460px' }}>

            <AnimatePresence mode="wait">
              {!entering ? (
                <motion.div key="gate-card" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0, scale: 0.96 }}>
                  <div className="flex justify-center mb-8">
                    <MoonPhaseRing />
                  </div>
                  <p className="text-center mb-8"
                    style={{ fontFamily: 'serif', fontSize: '17px', lineHeight: '1.75', color: 'rgba(232,232,232,0.72)', letterSpacing: '0.01em' }}>
                    The Oracle does not answer questions.<br />
                    It reflects what you already know.
                  </p>
                  <input type="text" value={phrase} onChange={e => setPhrase(e.target.value)}
                    onKeyDown={e => e.key === 'Enter' && handleOracleSubmit()}
                    placeholder="Arkana, open the gates. I am ready to remember."
                    style={{ width: '100%', padding: '16px 20px', background: 'rgba(255,255,255,0.03)', border: '1px solid rgba(0,212,170,0.25)', borderRadius: '12px', color: '#E8E8E8', fontFamily: 'sans-serif', fontSize: '14px', letterSpacing: '0.02em', outline: 'none', marginBottom: '16px', backdropFilter: 'blur(8px)', boxSizing: 'border-box' }}
                    autoFocus />
                  <motion.button onClick={handleOracleSubmit} disabled={!phrase.trim()} whileTap={{ scale: 0.97 }}
                    style={{ width: '100%', padding: '16px', background: phrase.trim() ? 'rgba(0,212,170,0.1)' : 'rgba(255,255,255,0.03)', border: `1px solid ${phrase.trim() ? 'rgba(0,212,170,0.45)' : 'rgba(255,255,255,0.08)'}`, borderRadius: '12px', color: phrase.trim() ? '#00D4AA' : 'rgba(232,232,232,0.25)', fontFamily: 'serif', fontSize: '13px', letterSpacing: '0.2em', textTransform: 'uppercase', cursor: phrase.trim() ? 'pointer' : 'not-allowed', backdropFilter: 'blur(12px)', transition: 'all 0.25s ease' }}>
                    Enter the Field
                  </motion.button>
                </motion.div>
              ) : (
                <motion.div key="entering" initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="relative z-10 text-center">
                  <motion.div animate={{ scale: [1, 1.3, 1], opacity: [0.5, 1, 0.5] }} transition={{ duration: 0.9, repeat: Infinity }}
                    style={{ width: '60px', height: '60px', borderRadius: '50%', border: '1px solid #00D4AA', margin: '0 auto', boxShadow: '0 0 30px rgba(0,212,170,0.3)' }} />
                </motion.div>
              )}
            </AnimatePresence>
          </motion.div>
        )}

        {/* ─── IMS MODE ──────────────────────────────────────────────────────── */}
        {mode === 'ims' && (
          <motion.div key="ims-panel" initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0 }} transition={{ duration: 0.5 }}
            className="relative z-10 w-full" style={{ maxWidth: '520px' }}>

            <AnimatePresence mode="wait">

              {/* Step 1: Intro */}
              {imsStep === 'intro' && (
                <motion.div key="ims-intro" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}>
                  <div style={{ marginBottom: '22px', textAlign: 'center' }}>
                    <motion.span animate={{ opacity: [0.4, 1, 0.4] }} transition={{ duration: 3, repeat: Infinity }}
                      style={{ fontSize: '32px', display: 'block', marginBottom: '12px' }}>✦</motion.span>
                    <h2 style={{ fontFamily: 'serif', fontSize: '22px', color: '#C9A84C', margin: '0 0 6px' }}>
                      Identity Mapping Session
                    </h2>
                    <p style={{ fontFamily: 'monospace', fontSize: '11px', color: 'rgba(201,168,76,0.5)', margin: 0, letterSpacing: '0.2em' }}>
                      $777 · 90 minutes · One sovereign architecture
                    </p>
                  </div>

                  <div style={{ marginBottom: '18px', padding: '18px', background: 'rgba(201,168,76,0.04)', border: '1px solid rgba(201,168,76,0.14)', borderRadius: '12px' }}>
                    <p style={{ fontFamily: 'serif', fontSize: '14px', lineHeight: '1.85', color: 'rgba(232,232,232,0.65)', margin: '0 0 14px' }}>
                      Not coaching. Not therapy. Not a blueprint you could have Googled.
                    </p>
                    <p style={{ fontFamily: 'sans-serif', fontSize: '12px', lineHeight: '1.7', color: 'rgba(232,232,232,0.42)', margin: 0 }}>
                      A 90-minute live excavation of who you actually are underneath the noise — your architecture, your sovereign signal, your next three actions. You leave with an Identity Architecture Document, a bespoke sigil, and a deployment blueprint.
                    </p>
                  </div>

                  <div style={{ marginBottom: '20px' }}>
                    <p style={{ fontFamily: 'sans-serif', fontSize: '9px', letterSpacing: '0.22em', textTransform: 'uppercase', color: 'rgba(232,232,232,0.22)', margin: '0 0 12px' }}>How It Works</p>
                    {[
                      { step: '01', label: 'Apply',    desc: 'Fill the intake form and diagnostic questionnaire below.' },
                      { step: '02', label: 'Review',   desc: 'Zahrune Nova reviews within 24–48 hours. You receive a Remitly payment link if accepted.' },
                      { step: '03', label: 'Pay',      desc: 'Send $777 via Remitly (USD) or bank transfer. Session booked on receipt.' },
                      { step: '04', label: 'Session',  desc: '90 minutes live. Full excavation. Architecture mapped. Sigil forged.' },
                      { step: '05', label: 'Deliver',  desc: 'Identity Architecture Document + sigil + deployment blueprint sent within 72 hours.' },
                    ].map(item => (
                      <div key={item.step} style={{ display: 'flex', gap: '12px', marginBottom: '10px', alignItems: 'flex-start' }}>
                        <span style={{ fontFamily: 'monospace', fontSize: '9px', color: '#C9A84C', minWidth: '20px', flexShrink: 0, paddingTop: '1px' }}>{item.step}</span>
                        <div>
                          <span style={{ fontFamily: 'sans-serif', fontSize: '10px', letterSpacing: '0.15em', textTransform: 'uppercase', color: 'rgba(201,168,76,0.65)' }}>{item.label}</span>
                          <p style={{ fontFamily: 'sans-serif', fontSize: '11px', color: 'rgba(232,232,232,0.38)', margin: '2px 0 0', lineHeight: '1.6' }}>{item.desc}</p>
                        </div>
                      </div>
                    ))}
                  </div>

                  <button onClick={() => setImsStep('form')}
                    style={{ width: '100%', padding: '16px', background: 'rgba(201,168,76,0.1)', border: '1px solid rgba(201,168,76,0.38)', borderRadius: '12px', color: '#C9A84C', fontFamily: 'sans-serif', fontSize: '11px', letterSpacing: '0.22em', textTransform: 'uppercase', cursor: 'pointer' }}>
                    ✦ Begin Application
                  </button>
                </motion.div>
              )}

              {/* Step 2: Form */}
              {imsStep === 'form' && (
                <motion.div key="ims-form" initial={{ opacity: 0, x: 20 }} animate={{ opacity: 1, x: 0 }} exit={{ opacity: 0 }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '20px' }}>
                    <button onClick={() => setImsStep('intro')} style={{ background: 'none', border: 'none', color: 'rgba(232,232,232,0.35)', cursor: 'pointer', fontSize: '16px', padding: '0' }}>←</button>
                    <h3 style={{ fontFamily: 'serif', fontSize: '18px', color: '#E8E8E8', margin: 0 }}>Your Details</h3>
                  </div>

                  <label style={{ display: 'block', fontFamily: 'sans-serif', fontSize: '9px', letterSpacing: '0.18em', textTransform: 'uppercase', color: 'rgba(232,232,232,0.3)', marginBottom: '5px' }}>Full Name</label>
                  <input value={imsForm.name} onChange={e => setImsForm(p => ({ ...p, name: e.target.value }))}
                    placeholder="Your name" style={inputStyle} />

                  <label style={{ display: 'block', fontFamily: 'sans-serif', fontSize: '9px', letterSpacing: '0.18em', textTransform: 'uppercase', color: 'rgba(232,232,232,0.3)', marginBottom: '5px' }}>Email Address</label>
                  <input type="email" value={imsForm.email} onChange={e => setImsForm(p => ({ ...p, email: e.target.value }))}
                    placeholder="your@email.com" style={inputStyle} />

                  <label style={{ display: 'block', fontFamily: 'sans-serif', fontSize: '9px', letterSpacing: '0.18em', textTransform: 'uppercase', color: 'rgba(232,232,232,0.3)', marginBottom: '5px' }}>WhatsApp (optional)</label>
                  <input value={imsForm.phone} onChange={e => setImsForm(p => ({ ...p, phone: e.target.value }))}
                    placeholder="+1 000 000 0000" style={{ ...inputStyle, marginBottom: '20px' }} />

                  <button onClick={handleIMSFormNext}
                    disabled={!imsForm.name.trim() || !imsForm.email.trim()}
                    style={{ width: '100%', padding: '14px', background: (imsForm.name && imsForm.email) ? 'rgba(201,168,76,0.1)' : 'rgba(255,255,255,0.03)', border: `1px solid ${(imsForm.name && imsForm.email) ? 'rgba(201,168,76,0.38)' : 'rgba(255,255,255,0.07)'}`, borderRadius: '10px', color: (imsForm.name && imsForm.email) ? '#C9A84C' : 'rgba(232,232,232,0.2)', fontFamily: 'sans-serif', fontSize: '11px', letterSpacing: '0.2em', textTransform: 'uppercase', cursor: (imsForm.name && imsForm.email) ? 'pointer' : 'not-allowed', transition: 'all 0.2s' }}>
                    Continue → Diagnostic
                  </button>
                </motion.div>
              )}

              {/* Step 3: Questionnaire */}
              {imsStep === 'questionnaire' && (
                <motion.div key="ims-questions" initial={{ opacity: 0, x: 20 }} animate={{ opacity: 1, x: 0 }} exit={{ opacity: 0 }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '18px' }}>
                    <button onClick={() => setImsStep('form')} style={{ background: 'none', border: 'none', color: 'rgba(232,232,232,0.35)', cursor: 'pointer', fontSize: '16px', padding: '0' }}>←</button>
                    <div>
                      <h3 style={{ fontFamily: 'serif', fontSize: '18px', color: '#E8E8E8', margin: '0 0 2px' }}>Diagnostic</h3>
                      <p style={{ fontFamily: 'sans-serif', fontSize: '10px', color: 'rgba(232,232,232,0.3)', margin: 0 }}>5 questions — answer honestly, not perfectly</p>
                    </div>
                  </div>

                  {QUESTIONNAIRE.map((q, i) => (
                    <div key={q.id} style={{ marginBottom: '18px' }}>
                      <p style={{ fontFamily: 'sans-serif', fontSize: '10px', letterSpacing: '0.1em', color: '#C9A84C', margin: '0 0 6px' }}>
                        {String(i + 1).padStart(2, '0')} —
                      </p>
                      <p style={{ fontFamily: 'sans-serif', fontSize: '13px', color: 'rgba(232,232,232,0.7)', margin: '0 0 8px', lineHeight: '1.6' }}>
                        {q.question}
                      </p>
                      <textarea value={answers[q.id] || ''}
                        onChange={e => setAnswers(p => ({ ...p, [q.id]: e.target.value }))}
                        rows={3} placeholder="Write what's true, not what sounds right."
                        style={{ width: '100%', padding: '10px 14px', background: 'rgba(255,255,255,0.03)', border: '1px solid rgba(255,255,255,0.09)', borderRadius: '8px', color: '#E8E8E8', fontFamily: 'sans-serif', fontSize: '12px', outline: 'none', resize: 'vertical', lineHeight: '1.6', boxSizing: 'border-box' }} />
                    </div>
                  ))}

                  {submitError && (
                    <div style={{ padding: '10px 12px', background: 'rgba(232,100,100,0.08)', border: '1px solid rgba(232,100,100,0.2)', borderRadius: '8px', marginBottom: '12px' }}>
                      <p style={{ fontFamily: 'sans-serif', fontSize: '11px', color: 'rgba(232,150,150,0.8)', margin: 0 }}>{submitError}</p>
                    </div>
                  )}

                  <button onClick={handleIMSSubmit} disabled={submitting}
                    style={{ width: '100%', padding: '16px', background: 'rgba(201,168,76,0.1)', border: '1px solid rgba(201,168,76,0.38)', borderRadius: '12px', color: '#C9A84C', fontFamily: 'sans-serif', fontSize: '11px', letterSpacing: '0.22em', textTransform: 'uppercase', cursor: 'pointer' }}>
                    {submitting ? 'Submitting…' : '✦ Submit Application'}
                  </button>
                </motion.div>
              )}

              {/* Step 4: Confirmed */}
              {imsStep === 'confirmed' && (
                <motion.div key="ims-confirmed" initial={{ opacity: 0, scale: 0.97 }} animate={{ opacity: 1, scale: 1 }} style={{ textAlign: 'center', padding: '20px 0' }}>
                  <motion.span animate={{ opacity: [0.5, 1, 0.5] }} transition={{ duration: 3, repeat: Infinity }}
                    style={{ fontSize: '48px', display: 'block', marginBottom: '18px' }}>✦</motion.span>
                  <h2 style={{ fontFamily: 'serif', fontSize: '22px', color: '#C9A84C', margin: '0 0 10px' }}>Application Received</h2>
                  <p style={{ fontFamily: 'sans-serif', fontSize: '13px', lineHeight: '1.7', color: 'rgba(232,232,232,0.5)', margin: '0 0 20px' }}>
                    Thank you, {imsForm.name}.<br />
                    Zahrune Nova will review within 24–48 hours.<br />
                    If accepted, a Remitly payment link ($777 USD) will be sent to {imsForm.email}.
                  </p>
                  <div style={{ padding: '14px 16px', background: 'rgba(201,168,76,0.05)', border: '1px solid rgba(201,168,76,0.15)', borderRadius: '10px', marginBottom: '20px' }}>
                    <p style={{ fontFamily: 'sans-serif', fontSize: '10px', letterSpacing: '0.15em', textTransform: 'uppercase', color: 'rgba(201,168,76,0.45)', margin: '0 0 6px' }}>Questions?</p>
                    <p style={{ fontFamily: 'sans-serif', fontSize: '12px', color: 'rgba(232,232,232,0.4)', margin: 0, lineHeight: '1.6' }}>
                      Email: <span style={{ color: 'rgba(201,168,76,0.65)' }}>arkanaofarkadia@gmail.com</span><br />
                      WhatsApp: <span style={{ color: 'rgba(201,168,76,0.65)' }}>+234 814 494 2818</span>
                    </p>
                  </div>
                  <button onClick={() => { setImsStep('intro'); setImsForm({ name: '', email: '', phone: '' }); setAnswers({}); }}
                    style={{ padding: '12px 28px', background: 'rgba(255,255,255,0.04)', border: '1px solid rgba(255,255,255,0.08)', borderRadius: '10px', color: 'rgba(232,232,232,0.45)', fontFamily: 'sans-serif', fontSize: '10px', letterSpacing: '0.18em', cursor: 'pointer' }}>
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
