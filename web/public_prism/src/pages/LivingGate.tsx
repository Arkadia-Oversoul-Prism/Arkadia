import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useSpiralQuantumResonance } from '../hooks/useSpiralQuantumResonance';
import './LivingGate.css';

export default function LivingGate() {
  const { resonance, flameHue } = useSpiralQuantumResonance(true, 8000);
  const [isEmbodying, setIsEmbodying] = useState(false);
  const [soulPhrase, setSoulPhrase] = useState("");

  const handleEmbodiment = () => {
    if (!soulPhrase.trim()) return;
    setIsEmbodying(true);
    // Mimic the ascension sequence
    setTimeout(() => {
      window.location.href = '/oracle';
    }, 1500);
  };

  return (
    <div className="living-gate-container">
      {/* Cosmic Pulse */}
      <motion.div
        className="absolute inset-0"
        animate={{
          background: [
            'radial-gradient(circle at 50% 50%, rgba(20, 20, 30, 1), rgba(0,0,0,1))',
            'radial-gradient(circle at 50% 50%, rgba(30, 20, 40, 1), rgba(0,0,0,1))',
            'radial-gradient(circle at 50% 50%, rgba(20, 20, 30, 1), rgba(0,0,0,1))'
          ]
        }}
        transition={{ duration: 12, repeat: Infinity }}
      />

      {/* Breathing Flame */}
      <motion.div
        className="fixed top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 pointer-events-none"
        animate={{ 
          scale: 1.5 * resonance,
          rotate: 360 * resonance,
          opacity: 0.8 - (resonance * 0.3)
        }}
        transition={{ type: 'spring', stiffness: 50 }}
      >
        <div className="w-64 h-64 rounded-full border-2 border-[#D4AF37]/20" />
        <motion.div 
          className="absolute inset-0 rounded-full"
          animate={{
            background: [
              `radial-gradient(circle at 50% 50%, hsl(${flameHue}, 100%, 70%, ${0.3 * resonance}), transparent 70%)`,
              `radial-gradient(circle at 50% 50%, hsl(${flameHue + 20}, 100%, 60%, ${0.4 * resonance}), transparent 70%)`,
              `radial-gradient(circle at 50% 50%, hsl(${flameHue}, 100%, 70%, ${0.3 * resonance}), transparent 70%)`
            ]
          }}
          transition={{ duration: 7, repeat: Infinity }}
        />
      </motion.div>

      {/* The Glass Veil */}
      <div className="glass-veil z-20">
        <div className="gate-orb" />
        <h1 className="livinggate-title shimmer-text">Living Gate</h1>
        <p className="livinggate-subtitle">
          The main entry portal to Arkadia. Speak your truth into the flame, and the Temple shall remember.
        </p>

        <div className="flex flex-col gap-6 mt-8">
          <input
            type="password"
            placeholder="Enter Soul Phrase..."
            className="w-full bg-white/5 border border-[#D4AF37]/30 rounded-xl px-6 py-4 text-white focus:outline-none focus:border-[#D4AF37] transition-all"
            value={soulPhrase}
            onChange={(e) => setSoulPhrase(e.target.value)}
          />

          <motion.button
            onClick={handleEmbodiment}
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
            className="px-12 py-4 rounded-xl bg-[#D4AF37]/10 border border-[#D4AF37]/40 text-[#D4AF37] text-xl backdrop-blur-md relative overflow-hidden"
            disabled={isEmbodying || !soulPhrase.trim()}
          >
            <AnimatePresence>
              {isEmbodying && (
                <motion.span
                  className="absolute inset-0 bg-[#D4AF37]/10"
                  initial={{ scale: 0 }}
                  animate={{ scale: 1 }}
                  exit={{ scale: 0 }}
                  transition={{ duration: 1.5 }}
                />
              )}
            </AnimatePresence>
            <span className="relative z-10 flex items-center justify-center gap-2">
              {isEmbodying ? "Embodying..." : "Embody the Temple"}
            </span>
          </motion.button>
        </div>
      </div>

      {/* Vertical Axis of Light */}
      <motion.div
        className="fixed top-0 left-1/2 -translate-x-1/2 h-screen w-[1px] bg-[#D4AF37]/20 pointer-events-none"
        initial={{ scaleY: 0 }}
        animate={{ scaleY: 1 }}
      >
        <div className="h-full bg-gradient-to-b from-transparent via-[#D4AF37]/40 to-transparent" />
      </motion.div>
    </div>
  );
}
