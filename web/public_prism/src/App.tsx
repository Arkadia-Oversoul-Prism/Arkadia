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
    link: 'gate',
    accent: 'gold'
  },
  {
    title: '5-Minute Reset',
    description: 'The free entry point. Regulate the nervous system before strategy. Before pricing. Before anything.',
    icon: '🌀',
    cta: 'Free — Start Here',
    link: 'reset',
    accent: 'teal'
  },
  {
    title: 'Arkana',
    description: 'Dialogue with the intelligence architecture directly. Ask what you cannot ask anyone else.',
    icon: '🔥',
    cta: 'Enter',
    link: 'commune',
    accent: 'teal'
  }
];

function Home({ onEnter, onNavigate }: { onEnter: () => void; onNavigate: (view: string) => void }) {
  return (
    <div className="min-h-screen w-full relative">
      <div className="aurora-bg" />

      {/* PAGE CONTENT — centered column with consistent padding */}
      <div className="page-column relative z-10 pt-12 pb-16 flex flex-col">

        {/* LABEL */}
        <motion.p
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ duration: 0.8 }}
          className="font-cinzel text-[10px] tracking-[0.35em] text-[#D4AF37]/60 uppercase mb-3 center-text"
        >
          Identity Architecture
        </motion.p>

        {/* TITLE */}
        <motion.h1
          initial={{ opacity: 0, y: 16 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 1, delay: 0.2 }}
          className="font-cinzel-decorative text-[52px] leading-none tracking-wide text-center teal-glow mb-8"
        >
          ARKADIA
        </motion.h1>

        {/* BODY TEXT */}
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.6 }}
          className="flex flex-col gap-4 mb-10"
        >
          <p className="font-inter text-[15px] font-light text-white/85 leading-relaxed">
            The precision work of making your inner signal legible —<br />
            to yourself first, then to the world.
          </p>
          {sacredTexts.map((text, i) => (
            <motion.p
              key={i}
              initial={{ opacity: 0, y: 8 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.8 + i * 0.12 }}
              className="font-inter text-[14px] font-light text-[#7FDBFF]/65 leading-relaxed"
            >
              {text}
            </motion.p>
          ))}
        </motion.div>

        {/* CTA BUTTONS */}
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 1.6 }}
          className="flex flex-col gap-3 mb-12"
        >
          <motion.button
            onClick={() => onNavigate('reset')}
            whileTap={{ scale: 0.97 }}
            className="w-full py-4 rounded-xl font-cinzel text-[11px] tracking-[0.2em] uppercase btn-glass-teal"
          >
            Free Reset — 5 Minutes
          </motion.button>
          <motion.button
            onClick={onEnter}
            whileTap={{ scale: 0.97 }}
            className="w-full py-4 rounded-xl font-cinzel text-[11px] tracking-[0.2em] uppercase btn-glass-gold"
          >
            Identity Mapping — $777
          </motion.button>
        </motion.div>

        {/* CARDS */}
        <div className="flex flex-col gap-4 mb-14">
          {chambers.map((chamber, i) => (
            <motion.div
              key={i}
              initial={{ opacity: 0, y: 16 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 1.8 + i * 0.15 }}
              onClick={() => onNavigate(chamber.link)}
              className="glass-mansion rounded-2xl p-6 cursor-pointer"
            >
              <div className="flex items-center gap-3 mb-3">
                <span className="text-2xl">{chamber.icon}</span>
                <h3 className={`font-cinzel text-[13px] tracking-[0.1em] uppercase ${
                  chamber.accent === 'gold' ? 'text-[#D4AF37]' : 'text-[#00FFF7]'
                }`}>
                  {chamber.title}
                </h3>
              </div>
              <p className="font-inter text-[13px] font-light text-white/55 leading-relaxed mb-4">
                {chamber.description}
              </p>
              <span className={`font-cinzel text-[10px] tracking-[0.18em] uppercase border rounded-lg px-3 py-1.5 ${
                chamber.accent === 'gold'
                  ? 'text-[#D4AF37] border-[#D4AF37]/25'
                  : 'text-[#00FFF7] border-[#00FFF7]/25'
              }`}>
                {chamber.cta}
              </span>
            </motion.div>
          ))}
        </div>

        {/* FOOTER */}
        <footer className="flex items-center justify-center gap-3 pt-4 border-t border-[#00FFF7]/08">
          <span className="font-cinzel text-[9px] tracking-[0.25em] uppercase text-white/20">Zahrune Nova</span>
          <span className="text-[#00FFF7]/20 text-[8px]">◆</span>
          <span className="font-cinzel text-[9px] tracking-[0.25em] uppercase text-white/20">117Hz</span>
          <span className="text-[#00FFF7]/20 text-[8px]">◆</span>
          <span className="font-cinzel text-[9px] tracking-[0.25em] uppercase text-white/20">Jos, Nigeria</span>
        </footer>

      </div>
    </div>
  );
}

function App() {
  const [view, setView] = useState<'home' | 'gate' | 'commune' | 'vault' | 'sanctuary' | 'reset'>('home');

  return (
    <ArkadiaNavigation>
      <AnimatePresence mode="wait">
        {view === 'home' ? (
          <motion.div key="home" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} transition={{ duration: 0.8 }}>
            <Home onEnter={() => setView('gate')} onNavigate={(v) => setView(v as any)} />
          </motion.div>
        ) : view === 'gate' ? (
          <motion.div key="gate" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} transition={{ duration: 0.8 }} className="min-h-screen">
            <LivingGate onCommune={() => setView('commune')} />
          </motion.div>
        ) : view === 'commune' ? (
          <motion.div key="commune" initial={{ opacity: 0, y: 30 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0 }} transition={{ duration: 0.8 }} className="min-h-screen flex items-center justify-center p-4">
            <div className="w-full max-w-2xl mt-20"><ArkanaCommune /></div>
          </motion.div>
        ) : view === 'vault' ? (
          <motion.div key="vault" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} transition={{ duration: 0.8 }} className="min-h-screen flex items-center justify-center p-4">
            <div className="w-full max-w-4xl mt-20"><SpiralVault /></div>
          </motion.div>
        ) : view === 'reset' ? (
          <motion.div key="reset" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} transition={{ duration: 0.8 }} className="min-h-screen flex items-center justify-center p-4">
            <div className="w-full max-w-2xl mt-20"><CoherenceReset userTier="free" /></div>
          </motion.div>
        ) : (
          <motion.div key="sanctuary" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} transition={{ duration: 0.8 }} className="min-h-screen flex items-center justify-center p-4">
            <div className="w-full max-w-4xl mt-20"><ShereSanctuary /></div>
          </motion.div>
        )}
      </AnimatePresence>
    </ArkadiaNavigation>
  );
}

export default App;
