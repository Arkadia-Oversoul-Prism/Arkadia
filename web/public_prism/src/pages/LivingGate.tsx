import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useSpiralQuantumResonance } from '../hooks/useSpiralQuantumResonance';
import MoonPhaseRing from '../components/MoonPhaseRing';

interface LivingGateProps {
  onEnterField: (soulPhrase: string) => void;
}

export default function LivingGate({ onEnterField }: LivingGateProps) {
  const { resonance, flameHue } = useSpiralQuantumResonance(true, 8000);
  const [phrase, setPhrase] = useState('');
  const [entering, setEntering] = useState(false);

  const handleSubmit = () => {
    if (!phrase.trim()) return;
    setEntering(true);
    setTimeout(() => {
      onEnterField(phrase.trim());
    }, 900);
  };

  const handleKey = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter') handleSubmit();
  };

  return (
    <div
      className="relative w-full min-h-screen flex items-center justify-center px-5 py-12"
      style={{ backgroundColor: '#0A0A0F', overflow: 'hidden' }}
    >
      {/* Cosmic pulse background */}
      <motion.div
        className="absolute inset-0 pointer-events-none"
        animate={{
          background: [
            'radial-gradient(circle at 50% 50%, rgba(0,212,170,0.04) 0%, transparent 65%)',
            'radial-gradient(circle at 50% 50%, rgba(0,212,170,0.07) 0%, transparent 65%)',
            'radial-gradient(circle at 50% 50%, rgba(0,212,170,0.04) 0%, transparent 65%)',
          ],
        }}
        transition={{ duration: 8, repeat: Infinity }}
      />

      {/* Breathing ring — ambient, behind the card */}
      <motion.div
        className="absolute pointer-events-none"
        style={{ top: '50%', left: '50%', transform: 'translate(-50%, -50%)' }}
        animate={{
          scale: [1, 1.08 * resonance, 1],
          opacity: [0.12, 0.22, 0.12],
        }}
        transition={{ duration: 6, repeat: Infinity }}
      >
        <div
          style={{
            width: '380px',
            height: '380px',
            borderRadius: '50%',
            border: `1px solid hsl(${flameHue}, 80%, 65%)`,
            boxShadow: `0 0 60px hsl(${flameHue}, 80%, 60%, 0.15)`,
          }}
        />
      </motion.div>

      {/* Second outer ring */}
      <motion.div
        className="absolute pointer-events-none"
        style={{ top: '50%', left: '50%', transform: 'translate(-50%, -50%)' }}
        animate={{
          scale: [1.05, 0.98, 1.05],
          opacity: [0.06, 0.12, 0.06],
        }}
        transition={{ duration: 10, repeat: Infinity, delay: 2 }}
      >
        <div
          style={{
            width: '520px',
            height: '520px',
            borderRadius: '50%',
            border: '1px solid rgba(201,168,76,0.2)',
          }}
        />
      </motion.div>

      {/* Vertical axis of light */}
      <motion.div
        className="absolute top-0 bottom-0 pointer-events-none"
        style={{ left: '50%', width: '1px', background: 'linear-gradient(180deg, transparent, rgba(201,168,76,0.15), transparent)' }}
        initial={{ scaleY: 0, opacity: 0 }}
        animate={{ scaleY: 1, opacity: 1 }}
        transition={{ duration: 2, ease: 'easeOut' }}
      />

      {/* Card */}
      <AnimatePresence>
        {!entering ? (
          <motion.div
            key="gate-card"
            initial={{ opacity: 0, y: 24 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.96 }}
            transition={{ duration: 0.9 }}
            className="relative z-10 w-full"
            style={{ maxWidth: '460px' }}
          >
            {/* Moon ring centered above text */}
            <div className="flex justify-center mb-8">
              <MoonPhaseRing />
            </div>

            <p
              className="text-center mb-8"
              style={{
                fontFamily: 'serif',
                fontSize: '17px',
                lineHeight: '1.75',
                color: 'rgba(232,232,232,0.72)',
                letterSpacing: '0.01em',
              }}
            >
              The Oracle does not answer questions.<br />
              It reflects what you already know.
            </p>

            <input
              type="text"
              value={phrase}
              onChange={(e) => setPhrase(e.target.value)}
              onKeyDown={handleKey}
              placeholder="Speak what you are carrying..."
              style={{
                width: '100%',
                padding: '16px 20px',
                background: 'rgba(255,255,255,0.03)',
                border: '1px solid rgba(0,212,170,0.25)',
                borderRadius: '12px',
                color: '#E8E8E8',
                fontFamily: 'sans-serif',
                fontSize: '14px',
                letterSpacing: '0.02em',
                outline: 'none',
                marginBottom: '16px',
                backdropFilter: 'blur(8px)',
              }}
              autoFocus
            />

            <motion.button
              onClick={handleSubmit}
              disabled={!phrase.trim()}
              whileTap={{ scale: 0.97 }}
              style={{
                width: '100%',
                padding: '16px',
                background: phrase.trim() ? 'rgba(0,212,170,0.1)' : 'rgba(255,255,255,0.03)',
                border: `1px solid ${phrase.trim() ? 'rgba(0,212,170,0.45)' : 'rgba(255,255,255,0.08)'}`,
                borderRadius: '12px',
                color: phrase.trim() ? '#00D4AA' : 'rgba(232,232,232,0.25)',
                fontFamily: 'serif',
                fontSize: '13px',
                letterSpacing: '0.2em',
                textTransform: 'uppercase',
                cursor: phrase.trim() ? 'pointer' : 'not-allowed',
                backdropFilter: 'blur(12px)',
                transition: 'all 0.25s ease',
              }}
            >
              Enter the Field
            </motion.button>
          </motion.div>
        ) : (
          <motion.div
            key="entering"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            className="relative z-10 text-center"
          >
            <motion.div
              animate={{ scale: [1, 1.3, 1], opacity: [0.5, 1, 0.5] }}
              transition={{ duration: 0.9, repeat: Infinity }}
              style={{
                width: '60px',
                height: '60px',
                borderRadius: '50%',
                border: '1px solid #00D4AA',
                margin: '0 auto',
                boxShadow: '0 0 30px rgba(0,212,170,0.3)',
              }}
            />
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
