import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';

const API_BASE = import.meta.env.VITE_API_URL || '';

export default function CoherenceReset() {
  const [emotionalState, setEmotionalState] = useState('');
  const [pressurePoint, setPressurePoint] = useState('');
  const [result, setResult] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const handleSubmit = async () => {
    if (!emotionalState.trim()) return;
    setLoading(true);
    setResult(null);

    try {
      const res = await fetch(`${API_BASE}/api/coherence-reset`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ emotionalState, pressurePoint }),
      });
      if (!res.ok) throw new Error('non-ok');
      const data = await res.json();
      setResult(data.result);
    } catch {
      setResult('The field is recalibrating. Try again.');
    } finally {
      setLoading(false);
    }
  };

  const labelStyle: React.CSSProperties = {
    display: 'block',
    fontFamily: 'sans-serif',
    fontSize: '10px',
    letterSpacing: '0.25em',
    textTransform: 'uppercase',
    color: 'rgba(232,232,232,0.45)',
    marginBottom: '8px',
  };

  const textareaStyle: React.CSSProperties = {
    width: '100%',
    padding: '14px 16px',
    background: 'rgba(255,255,255,0.03)',
    border: '1px solid rgba(0,212,170,0.18)',
    borderRadius: '10px',
    color: '#E8E8E8',
    fontFamily: 'sans-serif',
    fontSize: '14px',
    lineHeight: '1.6',
    resize: 'none',
    outline: 'none',
    minHeight: '90px',
    transition: 'border-color 0.2s',
  };

  return (
    <div className="w-full" style={{ maxWidth: '520px', margin: '0 auto', paddingTop: '12px' }}>
      {/* Title */}
      <motion.div
        initial={{ opacity: 0, y: 12 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.7 }}
        style={{ marginBottom: '32px' }}
      >
        <h1
          style={{
            fontFamily: 'serif',
            fontSize: '26px',
            letterSpacing: '0.05em',
            color: '#00D4AA',
            margin: '0 0 8px',
          }}
        >
          Coherence Reset
        </h1>
        <p
          style={{
            fontFamily: 'sans-serif',
            fontSize: '14px',
            color: 'rgba(232,232,232,0.5)',
            margin: 0,
            lineHeight: '1.6',
          }}
        >
          Name what is running. The field responds.
        </p>
      </motion.div>

      {/* Form */}
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 0.25 }}
        style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}
      >
        <div>
          <label style={labelStyle}>What are you feeling right now?</label>
          <textarea
            name="emotionalState"
            value={emotionalState}
            onChange={(e) => setEmotionalState(e.target.value)}
            placeholder="Be specific. Vague answers get vague protocols."
            style={textareaStyle}
          />
        </div>

        <div>
          <label style={labelStyle}>What are you avoiding?</label>
          <textarea
            name="pressurePoint"
            value={pressurePoint}
            onChange={(e) => setPressurePoint(e.target.value)}
            placeholder="The thing you keep not doing. Or not saying."
            style={textareaStyle}
          />
        </div>

        <motion.button
          onClick={handleSubmit}
          disabled={loading || !emotionalState.trim()}
          whileTap={{ scale: 0.98 }}
          style={{
            width: '100%',
            padding: '16px',
            background: emotionalState.trim() && !loading ? 'rgba(0,212,170,0.1)' : 'rgba(255,255,255,0.03)',
            border: `1px solid ${emotionalState.trim() && !loading ? 'rgba(0,212,170,0.4)' : 'rgba(255,255,255,0.08)'}`,
            borderRadius: '12px',
            color: emotionalState.trim() && !loading ? '#00D4AA' : 'rgba(232,232,232,0.25)',
            fontFamily: 'serif',
            fontSize: '12px',
            letterSpacing: '0.2em',
            textTransform: 'uppercase',
            cursor: emotionalState.trim() && !loading ? 'pointer' : 'not-allowed',
            transition: 'all 0.25s ease',
          }}
        >
          {loading ? (
            <span style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '8px' }}>
              {[0, 0.2, 0.4].map((delay, i) => (
                <motion.span
                  key={i}
                  animate={{ opacity: [0.3, 1, 0.3] }}
                  transition={{ duration: 1, repeat: Infinity, delay }}
                  style={{ display: 'inline-block', width: '5px', height: '5px', borderRadius: '50%', backgroundColor: '#00D4AA' }}
                />
              ))}
            </span>
          ) : (
            'Reset the Field'
          )}
        </motion.button>
      </motion.div>

      {/* Result */}
      <AnimatePresence>
        {result && (
          <motion.div
            key="result"
            initial={{ opacity: 0, y: 16 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.5 }}
            style={{
              marginTop: '28px',
              padding: '20px 22px',
              background: 'rgba(0,212,170,0.05)',
              border: '1px solid rgba(0,212,170,0.2)',
              borderRadius: '14px',
            }}
          >
            <p
              style={{
                fontFamily: 'sans-serif',
                fontSize: '10px',
                letterSpacing: '0.25em',
                textTransform: 'uppercase',
                color: 'rgba(0,212,170,0.5)',
                marginBottom: '12px',
              }}
            >
              Field Response
            </p>
            <p
              style={{
                fontFamily: 'serif',
                fontSize: '15px',
                lineHeight: '1.8',
                color: 'rgba(232,232,232,0.82)',
                margin: 0,
              }}
            >
              {result}
            </p>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
