// components/FlameGlyph.tsx
import { motion } from 'framer-motion';

interface FlameGlyphProps {
  seed: string | null;
}

export function FlameGlyph({ seed }: FlameGlyphProps) {
  const glyph = seed ? seed.split('-').join(' • ') : '•••';

  return (
    <motion.div 
      className="w-56 h-56 rounded-full border-4 border-white/30 flex items-center justify-center text-xl text-white font-light backdrop-blur-lg bg-white/5 shadow-[0_0_40px_rgba(255,255,255,0.1)]"
      initial={{ scale: 0.8, opacity: 0 }}
      animate={{ scale: 1, opacity: 1 }}
      transition={{ duration: 1.4 }}
    >
      {glyph}
    </motion.div>
  );
}