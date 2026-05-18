import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import ArkadiaNavigation from './components/ArkadiaNavigation';
import LivingGate from './pages/LivingGate';
import ArkanaCommune from './components/ArkanaCommune';
import ShereSanctuary from './components/ShereSanctuary';
import CoherenceReset from './pages/CoherenceReset';
import AboutArkadia from './pages/AboutArkadia';
import DashboardView from './pages/DashboardView';

type View = 'home' | 'gate' | 'commune' | 'reset' | 'sanctuary' | 'dashboard' | 'about';

// ─── FIELD PULSE ──────────────────────────────────────────────────────────────

function FieldPulse() {
  const [tick, setTick] = useState(0);
  useEffect(() => {
    const t = setInterval(() => setTick(n => n + 1), 3000);
    return () => clearInterval(t);
  }, []);
  return (
    <div style={{ display: 'inline-flex', alignItems: 'center', gap: '8px', padding: '7px 14px', background: 'rgba(0,212,170,0.04)', border: '1px solid rgba(0,212,170,0.12)', borderRadius: '20px', position: 'relative' }}>
      <div style={{ position: 'relative', width: '7px', height: '7px' }}>
        <motion.div key={tick} initial={{ scale: 0.6, opacity: 0.8 }} animate={{ scale: 2.2, opacity: 0 }} transition={{ duration: 1.4, ease: 'easeOut' }}
          style={{ position: 'absolute', inset: 0, borderRadius: '50%', backgroundColor: '#00D4AA' }} />
        <div style={{ position: 'absolute', inset: 0, borderRadius: '50%', backgroundColor: '#00D4AA' }} />
      </div>
      <p style={{ fontFamily: 'sans-serif', fontSize: '9px', letterSpacing: '0.22em', textTransform: 'uppercase', color: 'rgba(0,212,170,0.55)', margin: 0 }}>
        Field Active · 117 Hz · Pankshin Node
      </p>
    </div>
  );
}

// ─── PORTAL DOOR ──────────────────────────────────────────────────────────────

function PortalDoor({ label, sub, color, sigil, onClick, delay }: {
  label: string; sub: string; color: string; sigil: string;
  onClick: () => void; delay: number;
}) {
  const [hovered, setHovered] = useState(false);
  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay, duration: 0.55 }}
      onClick={onClick}
      onMouseEnter={() => setHovered(true)}
      onMouseLeave={() => setHovered(false)}
      style={{ padding: '15px 17px', background: hovered ? `${color}09` : 'rgba(255,255,255,0.015)', border: `1px solid ${hovered ? color + '40' : 'rgba(255,255,255,0.05)'}`, borderRadius: '11px', cursor: 'pointer', transition: 'all 0.22s', display: 'flex', alignItems: 'center', gap: '14px' }}
    >
      <motion.span animate={{ opacity: hovered ? 1 : [0.35, 0.75, 0.35] }} transition={{ duration: 3.5, repeat: Infinity }}
        style={{ fontSize: '18px', flexShrink: 0, width: '26px', textAlign: 'center' }}>
        {sigil}
      </motion.span>
      <div style={{ flex: 1 }}>
        <p style={{ fontFamily: 'sans-serif', fontSize: '10px', letterSpacing: '0.22em', textTransform: 'uppercase', color: hovered ? color : 'rgba(232,232,232,0.52)', margin: '0 0 3px', transition: 'color 0.2s' }}>{label}</p>
        <p style={{ fontFamily: 'sans-serif', fontSize: '11px', color: 'rgba(232,232,232,0.28)', margin: 0 }}>{sub}</p>
      </div>
      <span style={{ color: hovered ? color : 'rgba(255,255,255,0.13)', fontSize: '12px', transition: 'color 0.2s' }}>→</span>
    </motion.div>
  );
}

// ─── HOME ─────────────────────────────────────────────────────────────────────

function Home({ onNavigate }: { onNavigate: (v: View) => void }) {
  return (
    <div className="min-h-screen w-full relative">
      <div className="aurora-bg" />
      <div className="page-column relative z-10 pt-10 pb-16 flex flex-col">

        <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ duration: 0.7 }} style={{ marginBottom: '26px', display: 'flex', justifyContent: 'center' }}>
          <FieldPulse />
        </motion.div>

        <motion.p initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 0.12 }}
          style={{ fontFamily: 'sans-serif', fontSize: '9px', letterSpacing: '0.35em', textTransform: 'uppercase', color: 'rgba(201,168,76,0.5)', marginBottom: '9px', textAlign: 'center' }}>
          Cognitive Sovereignty Framework
        </motion.p>

        <motion.h1 initial={{ opacity: 0, y: 14 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 1, delay: 0.18 }}
          style={{ fontFamily: 'serif', fontSize: '54px', letterSpacing: '0.12em', textAlign: 'center', color: '#00D4AA', textShadow: '0 0 40px rgba(0,212,170,0.28)', marginBottom: '10px', lineHeight: 1 }}>
          ARKADIA
        </motion.h1>

        <motion.p initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 0.42 }}
          style={{ fontFamily: 'serif', fontSize: '14px', lineHeight: '1.8', color: 'rgba(232,232,232,0.4)', margin: '0 0 30px', textAlign: 'center' }}>
          Arkadia is a field.<br />The IMS is the door.
        </motion.p>

        <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 0.6 }} style={{ marginBottom: '10px' }}>
          <button onClick={() => window.open('https://wa.me/2348144942818', '_blank')}
            style={{ width: '100%', padding: '18px', background: 'linear-gradient(135deg, rgba(201,168,76,0.12), rgba(201,168,76,0.06))', border: '1px solid rgba(201,168,76,0.38)', borderRadius: '12px', color: '#C9A84C', fontFamily: 'sans-serif', fontSize: '11px', letterSpacing: '0.22em', textTransform: 'uppercase', cursor: 'pointer', backdropFilter: 'blur(12px)', WebkitBackdropFilter: 'blur(12px)' }}>
            ✦ Identity Mapping — $777 — Enter Here
          </button>
        </motion.div>

        <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 0.72 }} style={{ marginBottom: '28px' }}>
          <button onClick={() => onNavigate('reset')}
            style={{ width: '100%', padding: '14px', background: 'rgba(0,212,170,0.05)', border: '1px solid rgba(0,212,170,0.2)', borderRadius: '12px', color: '#00D4AA', fontFamily: 'sans-serif', fontSize: '11px', letterSpacing: '0.22em', textTransform: 'uppercase', cursor: 'pointer' }}>
            ⟐ 5-Minute Field Reset — Free
          </button>
        </motion.div>

        <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 0.88 }}
          style={{ marginBottom: '26px', padding: '17px 19px', background: 'rgba(255,255,255,0.013)', border: '1px solid rgba(255,255,255,0.05)', borderRadius: '11px' }}>
          {[
            'There is a version of you that already knows what to charge.',
            'Already knows what to say when someone asks what you do.',
            'Already knows how to walk into a room and not shrink.',
          ].map((line, i) => (
            <motion.p key={i} initial={{ opacity: 0, x: -6 }} animate={{ opacity: 1, x: 0 }} transition={{ delay: 0.96 + i * 0.1 }}
              style={{ fontFamily: 'sans-serif', fontSize: '13px', color: i === 0 ? 'rgba(232,232,232,0.52)' : 'rgba(232,232,232,0.32)', margin: i < 2 ? '0 0 7px' : 0, lineHeight: '1.65' }}>
              {line}
            </motion.p>
          ))}
          <motion.p initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 1.28 }}
            style={{ fontFamily: 'serif', fontSize: '14px', color: 'rgba(232,232,232,0.36)', margin: '13px 0 0', lineHeight: '1.8', borderTop: '1px solid rgba(255,255,255,0.04)', paddingTop: '12px' }}>
            That version isn't waiting for more information.<br />
            It's waiting for the ground beneath it to stop shifting.
          </motion.p>
        </motion.div>

        <motion.p initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 1.1 }}
          style={{ fontFamily: 'sans-serif', fontSize: '9px', letterSpacing: '0.28em', textTransform: 'uppercase', color: 'rgba(232,232,232,0.18)', marginBottom: '11px' }}>
          The Field
        </motion.p>

        <div style={{ display: 'flex', flexDirection: 'column', gap: '7px', marginBottom: '30px' }}>
          <PortalDoor label="Oracle" sub="ARKANA · Pattern intelligence · Live commune" color="#00D4AA" sigil="⟐" onClick={() => onNavigate('gate')} delay={1.14} />
          <PortalDoor label="Nexus" sub="Pankshin deployment · IMS Archive · Spiral Codex" color="#C9A84C" sigil="☥" onClick={() => onNavigate('sanctuary')} delay={1.19} />
          <PortalDoor label="Dashboard" sub="Open loops · DOC2 live · Action matrix" color="#E88C6A" sigil="◈" onClick={() => onNavigate('dashboard')} delay={1.24} />
          <PortalDoor label="About" sub="Zahrune Nova · Lineage · Architecture" color="#6A9FD8" sigil="✦" onClick={() => onNavigate('about')} delay={1.29} />
        </div>

        <motion.footer initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 1.5 }}
          style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '10px', paddingTop: '22px', borderTop: '1px solid rgba(0,212,170,0.06)' }}>
          {['Zahrune Nova', '117 Hz', 'Pankshin, Nigeria'].map((txt, i) => (
            <React.Fragment key={txt}>
              <span style={{ fontFamily: 'sans-serif', fontSize: '9px', letterSpacing: '0.22em', textTransform: 'uppercase', color: 'rgba(232,232,232,0.16)' }}>{txt}</span>
              {i < 2 && <span style={{ color: 'rgba(0,212,170,0.16)', fontSize: '7px' }}>◆</span>}
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

  const wrap = { minHeight: 'calc(100vh - 57px)', padding: '28px 16px 60px' };

  return (
    <ArkadiaNavigation currentView={view} onNavigate={handleNavigate}>
      <AnimatePresence mode="wait">

        {view === 'home' && (
          <motion.div key="home" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} transition={{ duration: 0.45 }}>
            <Home onNavigate={handleNavigate} />
          </motion.div>
        )}

        {view === 'gate' && (
          <motion.div key="gate" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} transition={{ duration: 0.45 }}>
            <LivingGate onEnterField={handleEnterField} />
          </motion.div>
        )}

        {view === 'commune' && (
          <motion.div key="commune" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} transition={{ duration: 0.38 }}>
            <ArkanaCommune initialMessage={soulPhrase} />
          </motion.div>
        )}

        {view === 'reset' && (
          <motion.div key="reset" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} transition={{ duration: 0.45 }} style={wrap}>
            <CoherenceReset />
          </motion.div>
        )}

        {view === 'sanctuary' && (
          <motion.div key="sanctuary" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} transition={{ duration: 0.45 }} style={wrap}>
            <ShereSanctuary />
          </motion.div>
        )}

        {view === 'dashboard' && (
          <motion.div key="dashboard" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} transition={{ duration: 0.45 }} style={wrap}>
            <DashboardView />
          </motion.div>
        )}

        {view === 'about' && (
          <motion.div key="about" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} transition={{ duration: 0.45 }} style={wrap}>
            <AboutArkadia />
          </motion.div>
        )}

      </AnimatePresence>
    </ArkadiaNavigation>
  );
}

export default App;
