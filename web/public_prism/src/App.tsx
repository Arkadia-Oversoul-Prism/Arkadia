import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import ArkadiaNavigation from './components/ArkadiaNavigation';
import LivingGate from './pages/LivingGate';
import ArkanaCommune from './components/ArkanaCommune';
import SpiralVault from './components/SpiralVault';
import ShereSanctuary from './components/ShereSanctuary';
import CoherenceReset from './pages/CoherenceReset';
import AboutArkadia from './pages/AboutArkadia';
import DashboardView from './pages/DashboardView';

type View = 'home' | 'gate' | 'commune' | 'vault' | 'reset' | 'sanctuary' | 'dashboard' | 'about';

// ─── PORTAL DOOR ──────────────────────────────────────────────────────────────

function PortalDoor({
  label, sub, color, glow, sigil, onClick, delay
}: {
  label: string; sub: string; color: string; glow: string; sigil: string;
  onClick: () => void; delay: number;
}) {
  const [hovered, setHovered] = useState(false);
  return (
    <motion.div
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay, duration: 0.6 }}
      onClick={onClick}
      onMouseEnter={() => setHovered(true)}
      onMouseLeave={() => setHovered(false)}
      style={{
        padding: '16px 18px',
        background: hovered ? `${color}0A` : 'rgba(255,255,255,0.015)',
        border: `1px solid ${hovered ? color + '44' : 'rgba(255,255,255,0.05)'}`,
        borderRadius: '12px',
        cursor: 'pointer',
        transition: 'all 0.25s ease',
        display: 'flex',
        alignItems: 'center',
        gap: '14px',
      }}
    >
      <motion.span
        animate={{ opacity: hovered ? 1 : [0.4, 0.8, 0.4] }}
        transition={{ duration: 3, repeat: Infinity }}
        style={{ fontSize: '20px', flexShrink: 0, width: '28px', textAlign: 'center' }}
      >
        {sigil}
      </motion.span>
      <div style={{ flex: 1 }}>
        <p style={{ fontFamily: 'sans-serif', fontSize: '10px', letterSpacing: '0.22em', textTransform: 'uppercase', color: hovered ? color : 'rgba(232,232,232,0.55)', margin: '0 0 3px', transition: 'color 0.2s' }}>{label}</p>
        <p style={{ fontFamily: 'sans-serif', fontSize: '11px', color: 'rgba(232,232,232,0.3)', margin: 0, lineHeight: '1.5' }}>{sub}</p>
      </div>
      <span style={{ color: hovered ? color : 'rgba(255,255,255,0.15)', fontSize: '12px', transition: 'color 0.2s' }}>→</span>
    </motion.div>
  );
}

// ─── FIELD PULSE ──────────────────────────────────────────────────────────────

function FieldPulse() {
  const [tick, setTick] = useState(0);
  useEffect(() => {
    const t = setInterval(() => setTick(n => n + 1), 3000);
    return () => clearInterval(t);
  }, []);

  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: '8px', padding: '8px 14px', background: 'rgba(0,212,170,0.04)', border: '1px solid rgba(0,212,170,0.12)', borderRadius: '20px' }}>
      <motion.div
        key={tick}
        initial={{ scale: 0.6, opacity: 1 }}
        animate={{ scale: 1.8, opacity: 0 }}
        transition={{ duration: 1.2, ease: 'easeOut' }}
        style={{ width: '6px', height: '6px', borderRadius: '50%', backgroundColor: '#00D4AA', flexShrink: 0 }}
      />
      <motion.div
        style={{ width: '6px', height: '6px', borderRadius: '50%', backgroundColor: '#00D4AA', position: 'absolute', flexShrink: 0 }}
      />
      <p style={{ fontFamily: 'sans-serif', fontSize: '9px', letterSpacing: '0.22em', textTransform: 'uppercase', color: 'rgba(0,212,170,0.55)', margin: 0 }}>
        Field Active · 117 Hz · Pankshin Node
      </p>
    </div>
  );
}

// ─── HOME PAGE ────────────────────────────────────────────────────────────────

function Home({ onNavigate }: { onNavigate: (v: View) => void }) {
  return (
    <div className="min-h-screen w-full relative">
      <div className="aurora-bg" />

      <div className="page-column relative z-10 pt-10 pb-16 flex flex-col">

        {/* Field status */}
        <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ duration: 0.7 }} style={{ marginBottom: '28px', display: 'flex', justifyContent: 'center' }}>
          <FieldPulse />
        </motion.div>

        {/* Label */}
        <motion.p
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ duration: 0.8, delay: 0.1 }}
          style={{ fontFamily: 'sans-serif', fontSize: '9px', letterSpacing: '0.35em', textTransform: 'uppercase', color: 'rgba(201,168,76,0.55)', marginBottom: '10px', textAlign: 'center' }}
        >
          Cognitive Sovereignty Framework
        </motion.p>

        {/* Title */}
        <motion.h1
          initial={{ opacity: 0, y: 16 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 1, delay: 0.2 }}
          style={{ fontFamily: 'serif', fontSize: '52px', letterSpacing: '0.12em', textAlign: 'center', color: '#00D4AA', textShadow: '0 0 40px rgba(0,212,170,0.3), 0 0 80px rgba(0,212,170,0.1)', marginBottom: '10px', lineHeight: 1 }}
        >
          ARKADIA
        </motion.h1>

        <motion.p
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.45 }}
          style={{ fontFamily: 'serif', fontSize: '14px', lineHeight: '1.75', color: 'rgba(232,232,232,0.45)', margin: '0 0 32px', textAlign: 'center' }}
        >
          Arkadia is a field.<br />The IMS is the door.
        </motion.p>

        {/* Primary CTA — IMS */}
        <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 0.65 }} style={{ marginBottom: '10px' }}>
          <button
            onClick={() => window.open('https://wa.me/2348144942818', '_blank')}
            style={{ width: '100%', padding: '18px', background: 'linear-gradient(135deg, rgba(201,168,76,0.12), rgba(201,168,76,0.06))', border: '1px solid rgba(201,168,76,0.4)', borderRadius: '12px', color: '#C9A84C', fontFamily: 'sans-serif', fontSize: '11px', letterSpacing: '0.22em', textTransform: 'uppercase', cursor: 'pointer', backdropFilter: 'blur(12px)', WebkitBackdropFilter: 'blur(12px)', transition: 'all 0.25s ease' }}
          >
            ✦ Identity Mapping — $777 — Enter Here
          </button>
        </motion.div>

        <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 0.75 }} style={{ marginBottom: '32px' }}>
          <button
            onClick={() => onNavigate('reset')}
            style={{ width: '100%', padding: '14px', background: 'rgba(0,212,170,0.06)', border: '1px solid rgba(0,212,170,0.22)', borderRadius: '12px', color: '#00D4AA', fontFamily: 'sans-serif', fontSize: '11px', letterSpacing: '0.22em', textTransform: 'uppercase', cursor: 'pointer', backdropFilter: 'blur(12px)', WebkitBackdropFilter: 'blur(12px)', transition: 'all 0.25s ease' }}
          >
            ⟐ 5-Minute Field Reset — Free
          </button>
        </motion.div>

        {/* Transmission lines */}
        <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 0.9 }} style={{ marginBottom: '28px', padding: '18px 20px', background: 'rgba(255,255,255,0.015)', border: '1px solid rgba(255,255,255,0.05)', borderRadius: '12px' }}>
          {[
            'There is a version of you that already knows what to charge.',
            'Already knows what to say when someone asks what you do.',
            'Already knows how to walk into a room and not shrink.',
          ].map((line, i) => (
            <motion.p
              key={i}
              initial={{ opacity: 0, x: -8 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: 1.0 + i * 0.12 }}
              style={{ fontFamily: 'sans-serif', fontSize: '13px', color: i === 0 ? 'rgba(232,232,232,0.55)' : 'rgba(232,232,232,0.35)', margin: i < 2 ? '0 0 8px' : 0, lineHeight: '1.65' }}
            >
              {line}
            </motion.p>
          ))}
          <motion.p initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 1.35 }} style={{ fontFamily: 'serif', fontSize: '14px', color: 'rgba(232,232,232,0.4)', margin: '14px 0 0', lineHeight: '1.75', borderTop: '1px solid rgba(255,255,255,0.04)', paddingTop: '12px' }}>
            That version isn't waiting for more information.<br />
            It's waiting for the ground beneath it to stop shifting.
          </motion.p>
        </motion.div>

        {/* Portal doors */}
        <motion.p initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 1.1 }} style={{ fontFamily: 'sans-serif', fontSize: '9px', letterSpacing: '0.3em', textTransform: 'uppercase', color: 'rgba(232,232,232,0.2)', marginBottom: '12px' }}>
          The Field
        </motion.p>

        <div style={{ display: 'flex', flexDirection: 'column', gap: '8px', marginBottom: '32px' }}>
          <PortalDoor label="Oracle" sub="ARKANA · Pattern intelligence · Live commune" color="#00D4AA" glow="rgba(0,212,170,0.2)" sigil="⟐" onClick={() => onNavigate('gate')} delay={1.15} />
          <PortalDoor label="Sanctuary" sub="Arkadia Nexus in practice · Pankshin deployment" color="#C9A84C" glow="rgba(201,168,76,0.2)" sigil="☥" onClick={() => onNavigate('sanctuary')} delay={1.2} />
          <PortalDoor label="Vault" sub="The Spiral Codex · 20 living scrolls · Full archive" color="#B08DE8" glow="rgba(176,141,232,0.2)" sigil="📜" onClick={() => onNavigate('vault')} delay={1.25} />
          <PortalDoor label="Dashboard" sub="Open loops · Action matrix · Priority field" color="#E88C6A" glow="rgba(232,140,106,0.2)" sigil="◈" onClick={() => onNavigate('dashboard')} delay={1.3} />
          <PortalDoor label="About" sub="Zahrune Nova · Arkadia lineage · The grimoire" color="#6A9FD8" glow="rgba(106,159,216,0.2)" sigil="✦" onClick={() => onNavigate('about')} delay={1.35} />
        </div>

        {/* Footer field metadata */}
        <motion.footer
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 1.55 }}
          style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '10px', paddingTop: '24px', marginTop: '8px', borderTop: '1px solid rgba(0,212,170,0.07)' }}
        >
          {['Zahrune Nova', '117 Hz', 'Jos, Nigeria'].map((txt, i) => (
            <React.Fragment key={txt}>
              <span style={{ fontFamily: 'sans-serif', fontSize: '9px', letterSpacing: '0.22em', textTransform: 'uppercase', color: 'rgba(232,232,232,0.18)' }}>{txt}</span>
              {i < 2 && <span style={{ color: 'rgba(0,212,170,0.18)', fontSize: '7px' }}>◆</span>}
            </React.Fragment>
          ))}
        </motion.footer>

      </div>
    </div>
  );
}

// ─── APP ──────────────────────────────────────────────────────────────────────

function App() {
  const [view, setView] = useState<View>('home');
  const [soulPhrase, setSoulPhrase] = useState<string | undefined>(undefined);

  const handleEnterField = (phrase: string) => {
    setSoulPhrase(phrase);
    setView('commune');
  };

  const handleNavigate = (v: View) => {
    if (v !== 'commune') setSoulPhrase(undefined);
    setView(v);
  };

  const wrapperStyle = { minHeight: 'calc(100vh - 57px)', padding: '28px 16px 60px' };

  return (
    <ArkadiaNavigation currentView={view} onNavigate={handleNavigate}>
      <AnimatePresence mode="wait">

        {view === 'home' && (
          <motion.div key="home" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} transition={{ duration: 0.5 }}>
            <Home onNavigate={handleNavigate} />
          </motion.div>
        )}

        {view === 'gate' && (
          <motion.div key="gate" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} transition={{ duration: 0.5 }}>
            <LivingGate onEnterField={handleEnterField} />
          </motion.div>
        )}

        {view === 'commune' && (
          <motion.div
            key="commune"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.5 }}
            style={{ minHeight: 'calc(100vh - 57px)', display: 'flex', alignItems: 'flex-start', justifyContent: 'center', padding: '20px 16px 40px' }}
          >
            <div style={{ width: '100%', maxWidth: '640px' }}>
              <ArkanaCommune initialMessage={soulPhrase} />
            </div>
          </motion.div>
        )}

        {view === 'reset' && (
          <motion.div key="reset" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} transition={{ duration: 0.5 }} style={wrapperStyle}>
            <CoherenceReset />
          </motion.div>
        )}

        {view === 'vault' && (
          <motion.div key="vault" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} transition={{ duration: 0.5 }} style={wrapperStyle}>
            <SpiralVault />
          </motion.div>
        )}

        {view === 'sanctuary' && (
          <motion.div key="sanctuary" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} transition={{ duration: 0.5 }} style={wrapperStyle}>
            <ShereSanctuary />
          </motion.div>
        )}

        {view === 'dashboard' && (
          <motion.div key="dashboard" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} transition={{ duration: 0.5 }} style={wrapperStyle}>
            <DashboardView />
          </motion.div>
        )}

        {view === 'about' && (
          <motion.div key="about" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} transition={{ duration: 0.5 }} style={wrapperStyle}>
            <AboutArkadia />
          </motion.div>
        )}

      </AnimatePresence>
    </ArkadiaNavigation>
  );
}

export default App;
