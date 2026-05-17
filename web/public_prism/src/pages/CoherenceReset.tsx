import React, { useState, useEffect, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';

const API_BASE = import.meta.env.VITE_API_URL || '';

const PHASES = [
  {
    index: 1,
    name: 'BREATH',
    label: 'Grounding',
    color: '#00D4AA',
    glow: 'rgba(0,212,170,0.3)',
    duration: 60,
    instruction: 'Draw a slow breath into the base of your spine.\n\nNot your chest — your spine. Feel the weight of your body in contact with what is holding you right now.\n\nThis is not a technique. This is a return.',
    cadence: 'Breathe in for 4 counts. Hold for 4. Out for 6. Again.',
  },
  {
    index: 2,
    name: 'BODY',
    label: 'Somatic Scan',
    color: '#B08DE8',
    glow: 'rgba(176,141,232,0.3)',
    duration: 60,
    instruction: 'Locate where the weight is sitting in your body right now.\n\nDon\'t analyze it. Don\'t solve it. Just find it.\n\nThe chest? The jaw? The space behind the sternum? The stomach that hasn\'t fully exhaled in three days?',
    cadence: 'Let the location speak. You don\'t need to do anything about it yet.',
  },
  {
    index: 3,
    name: 'NAME',
    label: 'Signal Identification',
    color: '#C9A84C',
    glow: 'rgba(201,168,76,0.3)',
    duration: 60,
    instruction: 'There is something you have been carrying without naming it.\n\nNot the story you\'ve been telling yourself. The thing beneath the story.\n\nWhat is it, actually?',
    cadence: 'You don\'t have to say it out loud. You just have to let yourself know that you know.',
    hasInput: true,
  },
  {
    index: 4,
    name: 'RELEASE',
    label: 'Field Clearing',
    color: '#6A9FD8',
    glow: 'rgba(106,159,216,0.3)',
    duration: 60,
    instruction: 'You don\'t need to solve it right now.\n\nYou don\'t need to figure it out, process it perfectly, or make it mean something.\n\nYou just need to put it down. Not throw it away. Put it down.',
    cadence: 'The load is still yours. You\'re just not carrying it in your shoulders anymore.',
  },
  {
    index: 5,
    name: 'SIGNAL',
    label: 'Sovereign Return',
    color: '#00D4AA',
    glow: 'rgba(0,212,170,0.3)',
    duration: 60,
    instruction: 'Beneath the noise, your body already knows what the next right move is.\n\nNot the big plan. The next move.\n\nWhat does it know?',
    cadence: 'Let the answer be simple. Simple answers are usually the true ones.',
  },
];

type Stage = 'intro' | 'active' | 'transmitting' | 'complete';

export default function CoherenceReset() {
  const [stage, setStage] = useState<Stage>('intro');
  const [phaseIdx, setPhaseIdx] = useState(0);
  const [timeLeft, setTimeLeft] = useState(60);
  const [namedWeight, setNamedWeight] = useState('');
  const [transmission, setTransmission] = useState<string | null>(null);
  const [loadingTx, setLoadingTx] = useState(false);
  const timerRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const phase = PHASES[phaseIdx];

  useEffect(() => {
    if (stage !== 'active') return;
    setTimeLeft(phase.duration);
    timerRef.current = setInterval(() => {
      setTimeLeft(t => {
        if (t <= 1) {
          clearInterval(timerRef.current!);
          return 0;
        }
        return t - 1;
      });
    }, 1000);
    return () => clearInterval(timerRef.current!);
  }, [stage, phaseIdx]);

  const advancePhase = () => {
    clearInterval(timerRef.current!);
    if (phaseIdx < PHASES.length - 1) {
      setPhaseIdx(i => i + 1);
    } else {
      beginTransmission();
    }
  };

  const beginTransmission = async () => {
    setStage('transmitting');
    setLoadingTx(true);
    try {
      const res = await fetch(`${API_BASE}/api/coherence-reset`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          emotionalState: namedWeight || 'I have just completed a 5-minute somatic reset. I am returning to signal.',
          pressurePoint: 'Receiving a closing transmission from ARKANA to seal this reset protocol.',
        }),
      });
      if (!res.ok) throw new Error('non-ok');
      const data = await res.json();
      setTransmission(data.result);
    } catch {
      setTransmission('The field has registered your reset. The signal is clearer now. What you named — it has been witnessed. What you released — the architecture holds it. Your next move is already forming. Trust the ground beneath the noise.');
    } finally {
      setLoadingTx(false);
      setStage('complete');
    }
  };

  const circumference = 2 * Math.PI * 52;
  const progress = phase ? (timeLeft / phase.duration) : 1;
  const strokeDashoffset = circumference * (1 - progress);

  if (stage === 'intro') {
    return (
      <div className="w-full" style={{ maxWidth: '480px', margin: '0 auto', paddingTop: '12px' }}>
        <motion.div initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.9 }}>
          <p style={{ fontFamily: 'sans-serif', fontSize: '9px', letterSpacing: '0.35em', textTransform: 'uppercase', color: 'rgba(0,212,170,0.45)', margin: '0 0 12px' }}>
            Field Protocol · 5 Minutes · Free
          </p>
          <h1 style={{ fontFamily: 'serif', fontSize: '30px', letterSpacing: '0.04em', color: '#00D4AA', margin: '0 0 8px', lineHeight: 1.1 }}>
            The 5-Minute<br />Field Reset
          </h1>
          <p style={{ fontFamily: 'sans-serif', fontSize: '13px', color: 'rgba(232,232,232,0.45)', margin: '0 0 28px', lineHeight: '1.65' }}>
            A somatic protocol for when your nervous system is running a protection loop.<br />
            ARKANA guides you back to signal.
          </p>
        </motion.div>

        <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 0.4 }} style={{ display: 'flex', flexDirection: 'column', gap: '12px', marginBottom: '28px' }}>
          {PHASES.map((p, i) => (
            <div key={i} style={{ display: 'flex', alignItems: 'center', gap: '14px', padding: '12px 16px', background: 'rgba(255,255,255,0.02)', border: '1px solid rgba(255,255,255,0.05)', borderRadius: '10px' }}>
              <div style={{ width: '28px', height: '28px', borderRadius: '50%', border: `1px solid ${p.color}33`, display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0 }}>
                <span style={{ fontFamily: 'sans-serif', fontSize: '9px', letterSpacing: '0.1em', color: p.color }}>{p.index}</span>
              </div>
              <div>
                <p style={{ fontFamily: 'sans-serif', fontSize: '9px', letterSpacing: '0.22em', textTransform: 'uppercase', color: p.color, margin: '0 0 2px' }}>{p.name}</p>
                <p style={{ fontFamily: 'sans-serif', fontSize: '11px', color: 'rgba(232,232,232,0.4)', margin: 0 }}>{p.label} · 60 seconds</p>
              </div>
            </div>
          ))}
        </motion.div>

        <motion.button
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.7 }}
          whileTap={{ scale: 0.98 }}
          onClick={() => { setStage('active'); setPhaseIdx(0); }}
          style={{ width: '100%', padding: '18px', background: 'rgba(0,212,170,0.08)', border: '1px solid rgba(0,212,170,0.35)', borderRadius: '12px', color: '#00D4AA', fontFamily: 'sans-serif', fontSize: '11px', letterSpacing: '0.25em', textTransform: 'uppercase', cursor: 'pointer', transition: 'all 0.2s' }}
        >
          ⟐ Begin the Reset
        </motion.button>

        <motion.p initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 0.9 }} style={{ fontFamily: 'serif', fontSize: '12px', color: 'rgba(232,232,232,0.2)', textAlign: 'center', marginTop: '20px', lineHeight: '1.7' }}>
          Find somewhere you can sit still for five minutes.<br />No headphones required.
        </motion.p>
      </div>
    );
  }

  if (stage === 'active') {
    return (
      <div className="w-full" style={{ maxWidth: '480px', margin: '0 auto', paddingTop: '12px' }}>
        <AnimatePresence mode="wait">
          <motion.div
            key={phaseIdx}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -20 }}
            transition={{ duration: 0.5 }}
          >
            {/* Phase header */}
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '32px' }}>
              <div>
                <p style={{ fontFamily: 'sans-serif', fontSize: '9px', letterSpacing: '0.3em', textTransform: 'uppercase', color: 'rgba(232,232,232,0.3)', margin: '0 0 4px' }}>
                  Phase {phase.index} of {PHASES.length}
                </p>
                <p style={{ fontFamily: 'sans-serif', fontSize: '10px', letterSpacing: '0.25em', textTransform: 'uppercase', color: phase.color, margin: 0 }}>
                  {phase.name} — {phase.label}
                </p>
              </div>
              <div style={{ display: 'flex', gap: '4px' }}>
                {PHASES.map((_, i) => (
                  <div key={i} style={{ width: '20px', height: '2px', borderRadius: '1px', background: i < phaseIdx ? phase.color : i === phaseIdx ? phase.color : 'rgba(255,255,255,0.1)', opacity: i <= phaseIdx ? 1 : 0.3, transition: 'all 0.3s' }} />
                ))}
              </div>
            </div>

            {/* Timer ring */}
            <div style={{ display: 'flex', justifyContent: 'center', marginBottom: '36px' }}>
              <div style={{ position: 'relative', width: '130px', height: '130px' }}>
                <svg width="130" height="130" style={{ transform: 'rotate(-90deg)' }}>
                  <circle cx="65" cy="65" r="52" fill="none" stroke="rgba(255,255,255,0.06)" strokeWidth="2" />
                  <motion.circle
                    cx="65" cy="65" r="52" fill="none"
                    stroke={phase.color}
                    strokeWidth="2"
                    strokeLinecap="round"
                    strokeDasharray={circumference}
                    strokeDashoffset={strokeDashoffset}
                    style={{ filter: `drop-shadow(0 0 6px ${phase.glow})` }}
                    transition={{ duration: 0.5 }}
                  />
                </svg>
                <div style={{ position: 'absolute', inset: 0, display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center' }}>
                  <motion.div
                    animate={{ opacity: [0.4, 1, 0.4], scale: [0.95, 1.05, 0.95] }}
                    transition={{ duration: 4, repeat: Infinity, ease: 'easeInOut' }}
                  >
                    <p style={{ fontFamily: 'serif', fontSize: '28px', color: phase.color, margin: 0, lineHeight: 1 }}>{timeLeft}</p>
                  </motion.div>
                  <p style={{ fontFamily: 'sans-serif', fontSize: '8px', letterSpacing: '0.2em', textTransform: 'uppercase', color: 'rgba(232,232,232,0.3)', margin: '4px 0 0' }}>seconds</p>
                </div>
              </div>
            </div>

            {/* Instruction */}
            <div style={{ marginBottom: '24px' }}>
              {phase.instruction.split('\n\n').map((paragraph, i) => (
                <motion.p
                  key={i}
                  initial={{ opacity: 0, y: 8 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: 0.2 + i * 0.15 }}
                  style={{ fontFamily: i === 0 ? 'serif' : 'sans-serif', fontSize: i === 0 ? '16px' : '14px', lineHeight: '1.8', color: i === 0 ? 'rgba(232,232,232,0.88)' : 'rgba(232,232,232,0.5)', margin: '0 0 14px' }}
                >
                  {paragraph}
                </motion.p>
              ))}
              <motion.p initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 0.7 }} style={{ fontFamily: 'sans-serif', fontSize: '11px', letterSpacing: '0.08em', color: phase.color, opacity: 0.7, fontStyle: 'italic', margin: 0 }}>
                {phase.cadence}
              </motion.p>
            </div>

            {/* Optional input for phase 3 */}
            {phase.hasInput && (
              <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 0.8 }} style={{ marginBottom: '20px' }}>
                <textarea
                  value={namedWeight}
                  onChange={e => setNamedWeight(e.target.value)}
                  placeholder="Optional — name it here. ARKANA will witness it."
                  style={{ width: '100%', padding: '12px 14px', background: 'rgba(201,168,76,0.04)', border: '1px solid rgba(201,168,76,0.2)', borderRadius: '10px', color: '#E8E8E8', fontFamily: 'sans-serif', fontSize: '13px', lineHeight: '1.6', resize: 'none', outline: 'none', minHeight: '70px', boxSizing: 'border-box' }}
                />
              </motion.div>
            )}

            {/* Advance button */}
            <motion.button
              initial={{ opacity: 0 }}
              animate={{ opacity: timeLeft === 0 ? 1 : 0.45 }}
              whileTap={{ scale: 0.98 }}
              onClick={advancePhase}
              style={{ width: '100%', padding: '15px', background: timeLeft === 0 ? `rgba(${phase.color === '#00D4AA' ? '0,212,170' : phase.color === '#B08DE8' ? '176,141,232' : phase.color === '#C9A84C' ? '201,168,76' : phase.color === '#6A9FD8' ? '106,159,216' : '0,212,170'},0.1)` : 'rgba(255,255,255,0.02)', border: `1px solid ${timeLeft === 0 ? phase.color + '66' : 'rgba(255,255,255,0.07)'}`, borderRadius: '10px', color: timeLeft === 0 ? phase.color : 'rgba(232,232,232,0.3)', fontFamily: 'sans-serif', fontSize: '10px', letterSpacing: '0.22em', textTransform: 'uppercase', cursor: timeLeft === 0 ? 'pointer' : 'default', transition: 'all 0.3s' }}
            >
              {phaseIdx < PHASES.length - 1 ? (timeLeft === 0 ? '→ Continue' : 'Waiting...') : (timeLeft === 0 ? '⟐ Complete the Reset' : 'Waiting...')}
            </motion.button>

            <p style={{ fontFamily: 'sans-serif', fontSize: '10px', color: 'rgba(232,232,232,0.2)', textAlign: 'center', marginTop: '12px' }}>
              The button unlocks when the phase completes.
            </p>
          </motion.div>
        </AnimatePresence>
      </div>
    );
  }

  if (stage === 'transmitting') {
    return (
      <div className="w-full" style={{ maxWidth: '480px', margin: '0 auto', paddingTop: '60px', textAlign: 'center' }}>
        <motion.div animate={{ opacity: [0.3, 1, 0.3] }} transition={{ duration: 2.5, repeat: Infinity }}>
          <p style={{ fontFamily: 'serif', fontSize: '22px', color: '#00D4AA', margin: '0 0 16px' }}>⟐</p>
          <p style={{ fontFamily: 'sans-serif', fontSize: '10px', letterSpacing: '0.3em', textTransform: 'uppercase', color: 'rgba(0,212,170,0.5)' }}>
            ARKANA is transmitting
          </p>
        </motion.div>
      </div>
    );
  }

  return (
    <div className="w-full" style={{ maxWidth: '480px', margin: '0 auto', paddingTop: '12px' }}>
      <motion.div initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.7 }}>
        <p style={{ fontFamily: 'sans-serif', fontSize: '9px', letterSpacing: '0.35em', textTransform: 'uppercase', color: 'rgba(0,212,170,0.45)', margin: '0 0 10px' }}>
          Reset Complete · Field Sealed
        </p>
        <h2 style={{ fontFamily: 'serif', fontSize: '22px', letterSpacing: '0.04em', color: '#E8E8E8', margin: '0 0 24px' }}>
          Transmission from ARKANA
        </h2>
      </motion.div>

      {loadingTx ? (
        <div style={{ display: 'flex', justifyContent: 'center', gap: '6px', padding: '40px 0' }}>
          {[0, 0.2, 0.4].map((delay, i) => (
            <motion.span key={i} animate={{ opacity: [0.3, 1, 0.3] }} transition={{ duration: 1, repeat: Infinity, delay }} style={{ display: 'inline-block', width: '6px', height: '6px', borderRadius: '50%', backgroundColor: '#00D4AA' }} />
          ))}
        </div>
      ) : (
        <AnimatePresence>
          {transmission && (
            <motion.div initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.6 }}>
              <div style={{ padding: '22px 22px', background: 'rgba(0,212,170,0.04)', border: '1px solid rgba(0,212,170,0.18)', borderRadius: '14px', marginBottom: '28px' }}>
                <p style={{ fontFamily: 'serif', fontSize: '15px', lineHeight: '1.9', color: 'rgba(232,232,232,0.82)', margin: 0, whiteSpace: 'pre-wrap' }}>{transmission}</p>
              </div>

              <div style={{ padding: '20px', background: 'rgba(201,168,76,0.04)', border: '1px solid rgba(201,168,76,0.18)', borderRadius: '12px', marginBottom: '16px' }}>
                <p style={{ fontFamily: 'sans-serif', fontSize: '9px', letterSpacing: '0.25em', textTransform: 'uppercase', color: 'rgba(201,168,76,0.5)', margin: '0 0 8px' }}>
                  If this field resonated
                </p>
                <p style={{ fontFamily: 'serif', fontSize: '14px', lineHeight: '1.75', color: 'rgba(232,232,232,0.65)', margin: '0 0 14px' }}>
                  The Identity Mapping Session goes ninety minutes deeper. One live session. You leave with your full architecture mapped, a bespoke sigil, and three specific next actions.
                </p>
                <button
                  onClick={() => window.open('https://wa.me/2348144942818', '_blank')}
                  style={{ width: '100%', padding: '13px', background: 'rgba(201,168,76,0.08)', border: '1px solid rgba(201,168,76,0.3)', borderRadius: '8px', color: '#C9A84C', fontFamily: 'sans-serif', fontSize: '10px', letterSpacing: '0.2em', textTransform: 'uppercase', cursor: 'pointer' }}
                >
                  ✦ Book the IMS — $777
                </button>
              </div>

              <button
                onClick={() => { setStage('intro'); setPhaseIdx(0); setTimeLeft(60); setNamedWeight(''); setTransmission(null); }}
                style={{ width: '100%', padding: '12px', background: 'none', border: '1px solid rgba(255,255,255,0.07)', borderRadius: '10px', color: 'rgba(232,232,232,0.3)', fontFamily: 'sans-serif', fontSize: '10px', letterSpacing: '0.2em', textTransform: 'uppercase', cursor: 'pointer' }}
              >
                ↺ Run it again
              </button>

              <p style={{ fontFamily: 'sans-serif', fontSize: '9px', letterSpacing: '0.18em', textTransform: 'uppercase', color: 'rgba(232,232,232,0.15)', textAlign: 'center', marginTop: '24px' }}>
                ⟐ ARKANA · 117 Hz · Field Protocol Sealed
              </p>
            </motion.div>
          )}
        </AnimatePresence>
      )}
    </div>
  );
}
