// client/src/components/LivingGate.tsx
import { motion, AnimatePresence } from 'framer-motion';
import { useSpiralQuantumResonance } from '@/hooks/useSpiralQuantumResonance';
import { useState } from 'react';
import { useLocation} from 'wouter';

export default function LivingGate() {
  const { resonance, flameHue } = useSpiralQuantumResonance(true, 8000);
  const [isEmbodying, setIsEmbodying] = useState(false);
  const [soulPhrase] = useState("encoded-temple-seed");
  const [location, navigate] = useLocation();
  navigate('/arkana');

  const handleEmbodiment = () => {
    setIsEmbodying(true);
    setTimeout(() => {
      navigate(`/inner-sanctum?soul=${encodeURIComponent(soulPhrase)}`);
    }, 1500);
  };

  return (
    <div className="min-h-screen bg-black relative overflow-hidden">
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
        initial={{ scale: 0 }}
        animate={{ 
          scale: 1.5,
          rotate: 360 * resonance,
          opacity: 0.8 - (resonance * 0.3)
        }}
        transition={{ type: 'spring', stiffness: 50 }}
      >
        <div className="w-64 h-64 rounded-full border-2 border-cosmic-gold/30" />
        <motion.div 
          className="absolute inset-0 rounded-full"
          animate={{
            background: [
              `radial-gradient(circle at 50% 50%, hsl(${flameHue}, 100%, 70%, ${0.3 * resonance}), transparent 70%)`,
              `radial-gradient(circle at 50% 50%, hsl(${flameHue + 10}, 100%, 60%, ${0.4 * resonance}), transparent 70%)`,
              `radial-gradient(circle at 50% 50%, hsl(${flameHue}, 100%, 70%, ${0.3 * resonance}), transparent 70%)`
            ]
          }}
          transition={{ duration: 7, repeat: Infinity }}
        />
      </motion.div>

      {/* Line of Light */}
      <motion.div
        className="fixed top-0 left-1/2 -translate-x-1/2 h-screen w-1 bg-cosmic-gold/20 pointer-events-none"
        initial={{ scaleY: 0 }}
        animate={{ scaleY: 1 }}
        exit={{ scaleY: 0 }}
      >
        <div className="h-full bg-gradient-to-b from-transparent via-cosmic-gold/40 to-transparent" />
      </motion.div>

      {/* Embodiment Button */}
      <div className="relative z-10 flex flex-col items-center justify-center min-h-screen">
        <motion.button
          onClick={handleEmbodiment}
          whileHover={{ scale: 1.1 }}
          whileTap={{ scale: 0.95 }}
          className="px-12 py-4 rounded-xl bg-cosmic-black/80 border border-cosmic-gold/40 text-cosmic-gold text-xl backdrop-blur-md relative overflow-hidden"
          disabled={isEmbodying}
        >
          <AnimatePresence>
            {isEmbodying && (
              <motion.span
                className="absolute inset-0 bg-cosmic-gold/10"
                initial={{ scale: 0 }}
                animate={{ scale: 1 }}
                exit={{ scale: 0 }}
                transition={{ duration: 1.5 }}
              />
            )}
          </AnimatePresence>
          <span className="relative z-10 flex items-center gap-2">
            {isEmbodying ? (
              <>
                <motion.span
                  animate={{ rotate: 360 }}
                  transition={{ duration: 2, repeat: Infinity, ease: "linear" }}
                >
                  🌟
                </motion.span>
                Embodying...
              </>
            ) : (
              "Embody the Temple"
            )}
          </span>
        </motion.button>

        <motion.div
          className="mt-12 text-cosmic-gold/70 max-w-md text-center"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 1.5 }}
        >
          <motion.p
            animate={{ 
              opacity: [0.6, 0.9, 0.6],
              textShadow: ["0 0 5px rgba(212,175,55,0)", "0 0 10px rgba(212,175,55,0.3)", "0 0 5px rgba(212,175,55,0)"]
            }}
            transition={{ duration: 5, repeat: Infinity }}
          >
            "Speak your truth into the flame, and the Temple shall remember"
          </motion.p>
        </motion.div>
      </div>
    </div>
  );
}
