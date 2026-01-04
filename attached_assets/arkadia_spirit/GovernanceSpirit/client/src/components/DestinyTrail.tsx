// components/DestinyTrail.tsx
import { useState } from 'react';
import { motion } from 'framer-motion';
import { generateMockSigil, Sigil } from '@/lib/utils';

export default function DestinyTrail() {
  const [sigilData, setSigilData] = useState<Sigil | null>(null);

  const generateSigil = () => {
    const newSigil = generateMockSigil();
    setSigilData(newSigil);
  };

  return (
    <div className="min-h-screen bg-cosmic-black flex flex-col items-center p-8 text-cosmic-gold">
      <motion.h1
        className="text-4xl font-extrabold mb-6 tracking-wide"
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
      >
        Destiny Trail: Crystal Sigil Archive
      </motion.h1>

      <motion.button
        className="mb-10 px-8 py-3 rounded-xl border-2 border-cosmic-gold hover:bg-cosmic-gold/20 transition"
        onClick={generateSigil}
        whileHover={{ scale: 1.05 }}
        whileTap={{ scale: 0.95 }}
      >
        Generate Cosmic Sigil
      </motion.button>

      {sigilData ? (
        <motion.div
          className="w-72 h-72 bg-cosmic-black/70 rounded-3xl border border-cosmic-gold flex flex-col items-center justify-center p-6"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
        >
          <svg
            viewBox="0 0 100 100"
            className="w-48 h-48 mb-4 stroke-cosmic-gold fill-transparent"
            xmlns="http://www.w3.org/2000/svg"
          >
            <path d={sigilData.vector} strokeWidth="2" strokeLinecap="round" />
          </svg>
          <p className="text-center text-cosmic-gold/80">{sigilData.meaning}</p>
        </motion.div>
      ) : (
        <p className="italic text-cosmic-gold/50 max-w-md text-center">
          Your crystal sigil will appear here once generated.
        </p>
      )}
    </div>
  );
}