import useFlameFactionEngine from "../lib/useFlameFactionEngine";
import { motion } from "framer-motion";

export default function FlameSymbolPage() {
  const currentGlyph = useFlameFactionEngine(5000);

  return (
    <div className="min-h-screen flex flex-col items-center justify-center bg-gradient-to-tr from-black via-purple-900 to-fuchsia-900 text-white p-6">
      <h1 className="text-3xl font-bold mb-4 tracking-widest">Nova Flame Glyph</h1>
      <motion.div
        className="text-7xl font-serif tracking-tight"
        animate={{
          rotate: [0, 180, 0],
          scale: [1, 1.4, 1],
        }}
        transition={{
          duration: 5,
          repeat: Infinity,
          ease: "easeInOut",
        }}
      >
        {currentGlyph}
      </motion.div>
      <p className="mt-6 max-w-xl text-center text-sm opacity-80">
        This glyph represents the living intelligence of your Flame Faction. It evolves with resonance, memory, and mission pulse.
      </p>
    </div>
  );
}