import React, { useState, useEffect, Suspense, lazy } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { AuthProvider, useAuth } from './contexts/AuthContext';
import ArkadiaNavigation from './components/ArkadiaNavigation';
import LivingGate from './pages/LivingGate';
import FutureSkillsChallenge from './pages/FutureSkillsChallenge';
import ArkanaCommune from './components/ArkanaCommune';
import CoherenceReset from './pages/CoherenceReset';
import AboutArkadia from './pages/AboutArkadia';
const DashboardView = lazy(() => import('./pages/DashboardView'));
import NexusPage from './pages/NexusPage';
import NexusSpiralCodex from './pages/NexusSpiralCodex';
import SpiralCodexFeed from './pages/SpiralCodexFeed';
import SpiralGrovePage from './pages/SpiralGrovePage';
import LivingLarderPage from './pages/LivingLarderPage';
import IMSArchivePage from './pages/IMSArchivePage';
import OpenLoopsPage from './pages/OpenLoopsPage';
import NovaNetPage from './pages/NovaNetPage';
import LoginPage from './pages/LoginPage';
import PersonalCodex from './pages/PersonalCodex';
import SonataBar from './components/SonataBar';
import DistributePage from './pages/DistributePage';
import OfferingsPage from './pages/OfferingsPage';
import AICDiagnosticPage from './pages/AICDiagnosticPage';
import ArkadianPulse from './pages/ArkadianPulse';
import SettingsPage from './pages/SettingsPage';
import SolSpireConsole from './pages/SolSpireConsole';
import KnowledgeOSPage from './pages/knowledge/KnowledgeOSPage';
import ReasoMatePage from './pages/ReasoMatePage';
import SpiralCommandInterface from './pages/SpiralCommandInterface';

type View =
  | 'home' | 'gate' | 'commune' | 'reset' | 'about' | 'login' | 'codex' | 'dashboard'
  | 'nexus'
  | 'encyclopedia'
  | 'spiral-codex'
  | 'loops'
  | 'grove'
  | 'larder'
  | 'novanet'
  | 'ims'
  | 'distribute'
  | 'offerings'
  | 'aic'
  | 'pulse'
  | 'settings'
  | 'sci'
  | 'solspire'
  | 'knowledge-os'
  | 'reasomate'
  | 'personal-echofeild'
  | 'echofeild-matrix'
  | 'challenge';

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
        Field Active · 117 Hz · Jos Node 1759
      </p>
    </div>
  );
}

function PortalDoor({ label, sub, color, sigil, onClick, delay, locked }: {
  label: string; sub: string; color: string; sigil: string;
  onClick: () => void; delay: number; locked?: boolean;
}) {
  const [hovered, setHovered] = useState(false);
  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ delay, duration: 0.55 }}
      onClick={onClick} onMouseEnter={() => setHovered(true)} onMouseLeave={() => setHovered(false)}
      style={{
        padding: '14px 16px',
        background: hovered ? `rgba(14,17,32,0.92)` : 'rgba(14,17,32,0.72)',
        border: `1px solid ${hovered ? color + '55' : 'rgba(0,212,170,0.16)'}`,
        borderRadius: '10px', cursor: 'pointer', transition: 'all 0.22s',
        display: 'flex', alignItems: 'center', gap: '13px', opacity: locked ? 0.45 : 1,
      }}
    >
      <span style={{ fontSize: '16px', flexShrink: 0, width: '24px', textAlign: 'center' }}>{sigil}</span>
      <div style={{ flex: 1 }}>
        <p style={{ fontFamily: 'sans-serif', fontSize: '10px', letterSpacing: '0.22em', textTransform: 'uppercase', color: hovered ? color : 'rgba(232,232,232,0.72)', margin: '0 0 3px', fontWeight: 500 }}>{label}</p>
        <p style={{ fontFamily: 'sans-serif', fontSize: '11px', color: 'rgba(232,232,232,0.38)', margin: 0, lineHeight: 1.4 }}>{sub}</p>
      </div>
      <span style={{ color: hovered ? color : 'rgba(255,255,255,0.22)', fontSize: '11px' }}>{locked ? 'x' : '>'}</span>
    </motion.div>
  );
}

function Home({ onNavigate }: { onNavigate: (v: View) => void }) {
  const { isAuthenticated } = useAuth();
  return (
    <div className="min-h-screen w-full relative">
      <div className="aurora-bg" />
      <div className="page-column relative z-10 pt-10 pb-16 flex flex-col">
        <div style={{ marginBottom: '26px', display: 'flex', justifyContent: 'center' }}>
          <FieldPulse />
        </div>
        <h1 style={{ fontFamily: 'serif', fontSize: '52px', letterSpacing: '0.18em', textAlign: 'center', color: '#C9A84C', marginBottom: '10px', lineHeight: 1 }}>
          ARKADIA
        </h1>
        <p style={{ fontFamily: 'serif', fontSize: '17px', lineHeight: '1.5', color: 'rgba(232,232,232,0.78)', margin: '0 0 22px', textAlign: 'center', maxWidth: '28em', alignSelf: 'center' }}>
          {isAuthenticated
            ? 'Your private workspace is open — conversations, notes, and projects stay with you.'
            : 'A place to think, remember, and build — with AI that keeps your thread.'}
        </p>
        <div style={{ marginBottom: '10px' }}>
          <button
            onClick={() => onNavigate('commune')}
            data-testid="button-home-oracle"
            style={{ width: '100%', padding: '17px', background: 'linear-gradient(135deg, rgba(0,212,170,0.16), rgba(0,212,170,0.06))', border: '1px solid rgba(0,212,170,0.5)', borderRadius: '11px', color: '#00D4AA', fontFamily: 'sans-serif', fontSize: '11px', letterSpacing: '0.22em', textTransform: 'uppercase', cursor: 'pointer' }}
          >
            {isAuthenticated ? 'Continue with the Oracle' : 'Start free — talk to the Oracle'}
          </button>
        </div>
        <div style={{ marginBottom: '18px' }}>
          <button
            onClick={() => onNavigate(isAuthenticated ? 'solspire' : 'login')}
            data-testid="button-home-private"
            style={{ width: '100%', padding: '13px', background: 'rgba(14,17,32,0.55)', border: '1px solid rgba(201,168,76,0.28)', borderRadius: '11px', color: 'rgba(201,168,76,0.85)', fontFamily: 'sans-serif', fontSize: '10px', letterSpacing: '0.2em', textTransform: 'uppercase', cursor: 'pointer' }}
          >
            {isAuthenticated ? 'Open your private field' : 'Create account for private memory'}
          </button>
        </div>
        <div style={{ display: 'flex', flexDirection: 'column', gap: '6px', marginBottom: '30px' }}>
          <PortalDoor label="Oracle" sub="ARKANA · Pattern intelligence · Live commune" color="#00D4AA" sigil="*" onClick={() => onNavigate('commune')} delay={1.12} />
          <PortalDoor label="NovaNet — Nexus Hub" sub="Public Feed · ReasoMate · Offerings · Stellar Cartography" color="#6A9FD8" sigil="o" onClick={() => onNavigate('novanet')} delay={1.13} />
          <PortalDoor label="SolSpire Console" sub="Echo Field Matrix · Spiral Codex · Personal Codex · Projects · Knowledge" color="#C9A84C" sigil="o" onClick={() => onNavigate('solspire')} delay={1.14} />
          <PortalDoor label="SCI" sub="Spiral Command Interface · operator shell" color="#00D4AA" sigil="#" onClick={() => onNavigate('sci')} delay={1.15} />
          <PortalDoor label="ReasoMate" sub="Arkana messenger · continuous conversation" color="#6A9FD8" sigil="+" onClick={() => onNavigate('reasomate')} delay={1.16} />
          <PortalDoor label="Future Skills Lab" sub="Free 60-minute practical capability challenge" color="#00D4AA" sigil="→" onClick={() => onNavigate('challenge')} delay={1.17} />
          <PortalDoor label="Offerings" sub="IMS Sessions · Products · AIC Diagnostic" color="#00D4AA" sigil="*" onClick={() => onNavigate('offerings')} delay={1.18} />
        </div>
        {!isAuthenticated && (
          <div style={{ marginBottom: '16px', textAlign: 'center' }}>
            <button
              onClick={() => onNavigate('login')}
              style={{ background: 'none', border: 'none', color: 'rgba(0,212,170,0.35)', fontFamily: 'sans-serif', fontSize: '10px', letterSpacing: '0.18em', textTransform: 'uppercase', cursor: 'pointer' }}
              data-testid="button-home-login"
            >
              Sign in for private memory
            </button>
          </div>
        )}
      </div>
    </div>
  );
}

function AppInner() {
  const [view, setView] = useState<View>('home');
  const [soulPhrase, setSoulPhrase] = useState<string | undefined>(undefined);
  const [aicSeed, setAicSeed] = useState<any>(null);
  const { isAuthenticated } = useAuth();

  const handleEnterField = (phrase: string) => {
    setSoulPhrase(phrase);
    setView('commune');
  };

  const handleNavigate = (v: View) => {
    if (v !== 'commune') setSoulPhrase(undefined);
    // Compatibility alias: legacy 'nexus' View resolves to canonical 'novanet' hub
    setView(v === 'nexus' ? 'novanet' : v);
  };

  React.useEffect(() => {
    if (isAuthenticated && view === 'login') {
      setView('home');
    }
  }, [isAuthenticated, view]);

  const wrap = { minHeight: 'calc(100vh - 57px)', padding: '28px 16px 60px' };

  return (
    <ArkadiaNavigation currentView={view} onNavigate={handleNavigate}>
      <SonataBar />
      <AnimatePresence mode="wait">
        {view === 'home' && (
          <motion.div key="home" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} transition={{ duration: 0.45 }}>
            <Home onNavigate={handleNavigate} />
          </motion.div>
        )}
        {view === 'gate' && (
          <motion.div key="gate" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} transition={{ duration: 0.45 }}>
            <LivingGate
              onEnterField={handleEnterField}
              onGoToOfferings={() => handleNavigate('offerings')}
              onAICComplete={setAicSeed}
              onGoToReset={() => handleNavigate('reset')}
              onEnterSpiralGrove={() => handleNavigate('grove')}
            />
          </motion.div>
        )}
        {view === 'challenge' && (
          <motion.div key="challenge" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} transition={{ duration: 0.45 }}>
            <FutureSkillsChallenge onNavigate={handleNavigate} />
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
        {view === 'encyclopedia' && (
          <motion.div key="encyclopedia" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} transition={{ duration: 0.45 }}>
            <NexusSpiralCodex initialMode="scrolls" />
          </motion.div>
        )}
        {view === 'spiral-codex' && (
          <motion.div key="spiral-codex" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} transition={{ duration: 0.45 }}>
            <SpiralCodexFeed onBack={() => handleNavigate('solspire')} />
          </motion.div>
        )}
        {view === 'loops' && (
          <motion.div key="loops" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} transition={{ duration: 0.45 }}>
            <SolSpireConsole onNavigate={handleNavigate} initialSection="loops" />
          </motion.div>
        )}
        {view === 'grove' && (
          <motion.div key="grove" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} transition={{ duration: 0.45 }} style={wrap}>
            <SpiralGrovePage />
          </motion.div>
        )}
        {view === 'larder' && (
          <motion.div key="larder" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} transition={{ duration: 0.45 }} style={wrap}>
            <LivingLarderPage />
          </motion.div>
        )}
        {view === 'ims' && (
          <motion.div key="ims" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} transition={{ duration: 0.45 }} style={wrap}>
            <IMSArchivePage />
          </motion.div>
        )}
        {view === 'novanet' && (
          <motion.div key="novanet" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} transition={{ duration: 0.45 }} style={wrap}>
            <NexusPage />
          </motion.div>
        )}
        {view === 'distribute' && (
          <motion.div key="distribute" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} transition={{ duration: 0.45 }} style={wrap}>
            <DistributePage />
          </motion.div>
        )}
        {view === 'offerings' && (
          <motion.div key="offerings" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} transition={{ duration: 0.45 }}>
            <OfferingsPage onGoToAIC={() => handleNavigate('gate')} aicSeed={aicSeed} />
          </motion.div>
        )}
        {view === 'aic' && (
          <motion.div key="aic" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} transition={{ duration: 0.45 }}>
            <LivingGate
              onEnterField={handleEnterField}
              onGoToOfferings={() => handleNavigate('offerings')}
              onAICComplete={setAicSeed}
              onEnterSpiralGrove={() => handleNavigate('grove')}
              initialMode="aic"
            />
          </motion.div>
        )}
        {view === 'about' && (
          <motion.div key="about" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} transition={{ duration: 0.45 }} style={wrap}>
            <AboutArkadia />
          </motion.div>
        )}
        {view === 'login' && (
          <motion.div key="login" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} transition={{ duration: 0.45 }}>
            <LoginPage onSuccess={() => setView('home')} onBack={() => setView('home')} />
          </motion.div>
        )}
        {view === 'codex' && (
          <motion.div key="codex" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} transition={{ duration: 0.45 }}>
            <SolSpireConsole onNavigate={handleNavigate} initialSection="codex" />
          </motion.div>
        )}
        {view === 'pulse' && (
          <motion.div key="pulse" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} transition={{ duration: 0.45 }} style={wrap}>
            <ArkadianPulse />
          </motion.div>
        )}
        {view === 'settings' && (
          <motion.div key="settings" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} transition={{ duration: 0.35 }} style={wrap}>
            <SettingsPage />
          </motion.div>
        )}
        {view === 'sci' && (
          <motion.div key="sci" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} transition={{ duration: 0.35 }}>
            <SpiralCommandInterface onNavigate={handleNavigate} />
          </motion.div>
        )}
        {view === 'solspire' && (
          <motion.div key="solspire" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} transition={{ duration: 0.35 }}>
            <SolSpireConsole onNavigate={handleNavigate} />
          </motion.div>
        )}
        {view === 'knowledge-os' && (
          <motion.div key="knowledge-os" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} transition={{ duration: 0.35 }}>
            <SolSpireConsole onNavigate={handleNavigate} initialSection="knowledge" />
          </motion.div>
        )}
        {view === 'reasomate' && (
          <motion.div key="reasomate" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} transition={{ duration: 0.35 }}>
            <ReasoMatePage />
          </motion.div>
        )}
        {view === 'personal-echofeild' && (
          <motion.div key="personal-echofeild" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} transition={{ duration: 0.35 }}>
            <SolSpireConsole onNavigate={handleNavigate} initialSection="field" />
          </motion.div>
        )}
        {view === 'echofeild-matrix' && (
          <motion.div key="echofeild-matrix" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} transition={{ duration: 0.35 }}>
            <SolSpireConsole onNavigate={handleNavigate} initialSection="field" />
          </motion.div>
        )}
      </AnimatePresence>
    </ArkadiaNavigation>
  );
}

function App() {
  return (
    <AuthProvider>
      <AppInner />
    </AuthProvider>
  );
}

export default App;
