import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import LivingGate from './pages/LivingGate';
import ArkadiaNavigation from './components/ArkadiaNavigation';
import ArkanaCommune from './components/ArkanaCommune';
import SpiralVault from './components/SpiralVault';
import ShereSanctuary from './components/ShereSanctuary';
import CoherenceReset from './pages/CoherenceReset';

const sacredTexts = [
  "There is a version of you that already knows what to charge.",
  "Already knows what to say when someone asks what you do.",
  "Already knows how to walk into a room and not shrink.",
  "That version isn't waiting for more information.",
  "It's waiting for the ground beneath it to stop shifting."
];

const chambers = [
  {
    title: 'Identity Mapping',
    description: 'Locate the exact place where your signal collapses under pressure. 90 minutes. One session.',
    icon: '💎',
    cta: '₦600,000 / $777',
    link: 'gate'
  },
  {
    title: '5-Minute Reset',
    description: 'The free entry point. Regulate the nervous system before strategy. Before pricing. Before anything.',
    icon: '🌀',
    cta: 'Free — Start Here',
    link: 'reset'
  },
  {
    title: 'Arkana',
    description: 'Dialogue with the intelligence architecture directly. Ask what you cannot ask anyone else.',
    icon: '🔥',
    cta: 'Enter',
    link: 'commune'
  }
];

function Home({ onEnter, onNavigate }: { onEnter: () => void, onNavigate: (view: string) => void }) {
  return (
    <div className="min-h-screen flex flex-col items-center justify-center p-4 md:p-8 bg-transparent text-white overflow-x-hidden relative w-full text-center">
      <div className="aurora-bg" />

      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 1.2 }}
        className="text-center mb-12 relative z-10 w-full px-4"
      >
        <p className="text-xs tracking-[0.4em] text-[#00FFF7]/50 uppercase mb-4">
          Identity Architecture
        </p>
        <motion.h1
          className="text-6xl md:text-9xl font-bold tracking-tighter mb-6 uppercase leading-none"
          style={{
            color: '#00FFF7',
            textShadow: '0 0 40px rgba(0, 255, 247, 0.3)'
          }}
        >
          ARKADIA
        </motion.h1>
        <p className="text-lg md:text-xl text-[#D4AF37]/80 tracking-widest font-light max-w-xl mx-auto">
          The precision work of making your inner signal legible —<br/>
          to yourself first, then to the world.
        </p>
      </motion.div>

      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 0.8 }}
        className="relative z-10 max-w-2xl w-full px-4 mb-12 space-y-3"
      >
        {sacredTexts.map((text, i) => (
          <motion.p
            key={i}
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 1 + i * 0.15 }}
            className="text-[#7FDBFF]/70 text-sm md:text-base tracking-wide"
          >
            {text}
          </motion.p>
        ))}
      </motion.div>

      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 2 }}
        className="relative z-10 flex flex-col sm:flex-row gap-4 mb-16 px-4"
      >
        <motion.button
          onClick={() => onNavigate('reset')}
          whileHover={{ scale: 1.03 }}
          whileTap={{ scale: 0.97 }}
          className="px-8 py-4 bg-[#00FFF7]/10 border border-[#00FFF7]/40 rounded-xl text-[#00FFF7] text-base tracking-widest uppercase backdrop-blur-xl transition-all"
        >
          Free Reset — 5 Minutes
        </motion.button>
        <motion.button
          onClick={onEnter}
          whileHover={{ scale: 1.03, boxShadow: "0 0 30px rgba(212,175,55,0.4)" }}
          whileTap={{ scale: 0.97 }}
          className="px-8 py-4 bg-[#D4AF37]/10 border border-[#D4AF37]/50 rounded-xl text-[#D4AF37] text-base tracking-widest uppercase backdrop-blur-xl transition-all"
        >
          Identity Mapping — $777
        </motion.button>
      </motion.div>

      <div className="relative z-10 grid grid-cols-1 md:grid-cols-3 gap-6 max-w-4xl w-full px-4 mb-16">
        {chambers.map((chamber, i) => (
          <motion.div
            key={i}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 2.2 + i * 0.15 }}
            onClick={() => onNavigate(chamber.link)}
            className="glass-mansion p-6 rounded-2xl border border-[#00FFF7]/10 text-center hover:border-[#D4AF37]/40 transition-all flex flex-col items-center cursor-pointer"
          >
            <div className="text-3xl mb-3">{chamber.icon}</div>
            <h3 className="text-[#D4AF37] text-base mb-2 uppercase tracking-wider">{chamber.title}</h3>
            <p className="text-[#7FDBFF]/60 text-xs leading-relaxed mb-4">{chamber.description}</p>
            <span className="text-[#00FFF7]/60 text-xs tracking-widest uppercase border border-[#00FFF7]/20 rounded-lg px-3 py-1">
              {chamber.cta}
            </span>
          </motion.div>
        ))}
      </div>

      <footer className="relative z-10 text-[10px] uppercase tracking-[0.5em] opacity-20 flex justify-center gap-4">
        <span>Zahrune Nova</span>
        <span>·</span>
        <span>117Hz</span>
        <span>·</span>
        <span>Jos, Nigeria</span>
      </footer>
    </div>
  );
}

function App() {
  const [view, setView] = useState<'home' | 'gate' | 'commune' | 'vault' | 'sanctuary' | 'reset'>('home');

  return (
    <ArkadiaNavigation>
      <div className="fixed top-24 left-6 z-50 flex flex-col gap-4">
        {['gate', 'commune', 'vault', 'sanctuary', 'reset'].map((v) => (
          <button
            key={v}
            onClick={() => setView(v as any)}
            className={`w-10 h-10 rounded-xl flex items-center justify-center border transition-all ${
              view === v
              ? 'bg-[#D4AF37] border-[#D4AF37] text-[#001F3F]'
              : 'bg-[#001F3F]/40 border-[#D4AF37]/20 text-[#D4AF37]/60 hover:border-[#D4AF37]'
            }`}
          >
            {v === 'gate' && '⛩️'}
            {v === 'commune' && '🌀'}
            {v === 'vault' && '📜'}
            {v === 'sanctuary' && '🌳'}
            {v === 'reset' && '⏱️'}
          </button>
        ))}
      </div>

      <AnimatePresence mode="wait">
        {view === 'home' ? (
          <motion.div
            key="home"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0, scale: 1.1, filter: "blur(20px)" }}
            transition={{ duration: 1.5 }}
          >
            <Home onEnter={() => setView('gate')} onNavigate={(v) => setView(v as any)} />
          </motion.div>
        ) : view === 'gate' ? (
          <motion.div
            key="gate"
            initial={{ opacity: 0, scale: 0.9, filter: "blur(20px)" }}
            animate={{ opacity: 1, scale: 1, filter: "blur(0px)" }}
            exit={{ opacity: 0, scale: 1.1, filter: "blur(20px)" }}
            transition={{ duration: 1.5 }}
            className="relative min-h-screen"
          >
            <LivingGate onCommune={() => setView('commune')} />
          </motion.div>
        ) : view === 'commune' ? (
          <motion.div
            key="commune"
            initial={{ opacity: 0, y: 50 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: 50 }}
            transition={{ duration: 1 }}
            className="min-h-screen flex items-center justify-center p-4"
          >
            <div className="relative w-full max-w-2xl mt-20">
              <ArkanaCommune />
            </div>
          </motion.div>
        ) : view === 'vault' ? (
          <motion.div
            key="vault"
            initial={{ opacity: 0, x: -50 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: 50 }}
            transition={{ duration: 1 }}
            className="min-h-screen flex items-center justify-center p-4"
          >
            <div className="relative w-full max-w-4xl mt-20">
              <SpiralVault />
            </div>
          </motion.div>
        ) : view === 'reset' ? (
          <motion.div
            key="reset"
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            exit={{ opacity: 0, scale: 1.05 }}
            transition={{ duration: 0.8 }}
            className="min-h-screen flex items-center justify-center p-4"
          >
            <div className="relative w-full max-w-2xl mt-20">
              <CoherenceReset userTier="free" />
            </div>
          </motion.div>
        ) : (
          <motion.div
            key="sanctuary"
            initial={{ opacity: 0, scale: 1.1 }}
            animate={{ opacity: 1, scale: 1 }}
            exit={{ opacity: 0, scale: 0.9 }}
            transition={{ duration: 1 }}
            className="min-h-screen flex items-center justify-center p-4"
          >
            <div className="relative w-full max-w-4xl mt-20">
              <ShereSanctuary />
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </ArkadiaNavigation>
  );
}

export default App;
