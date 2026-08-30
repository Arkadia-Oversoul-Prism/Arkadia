import React, { useState, useEffect, Suspense, lazy } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { AuthProvider, useAuth } from './contexts/AuthContext';
import ArkadiaNavigation from './components/ArkadiaNavigation';
import LivingGate from './pages/LivingGate';
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
  | 'echofeild-matrix';

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
        Field Active \u00b7 117 Hz \u00b7 Jos Node 1759
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
        borderRadius: '10px',
        cursor: 'pointer',
        transition: 'all 0.22s',
        display: 'flex',
        alignItems: 'center',
        gap: '13px',
        opacity: locked ? 0.45 : 1,
      }}
    >
      <span style={{ fontSize: '16px', flexShrink: 0, width: '24px', textAlign: 'center' }}>{sigil}</span>
      <div style={{ flex: 1 }}>
        <p style={{ fontFamily: 'sans-serif', fontSize: '10px', letterSpacing: '0.22em', textTransform: 'uppercase', color: hovered ? color : 'rgba(232,232,232,0.72)', margin: '0 0 3px', fontWeight: 500 }}>{label}</p>
        <p style={{ fontFamily: 'sans-serif', fontSize: '11px', color: 'rgba(232,232,232,0.38)', margin: 0, lineHeight: 1.4 }}>{sub}</p>
      </div>
      <span style={{ color: hovered ? color : 'rgba(255,255,255,0.22)', fontSize: '11px' }}>{locked ? '\ud83d\udd10' : '\u2192'}</span>
    </motion.div>
  );
}

const FIRST_ACTION_KEY = 'arkadia_first_private_action_done';

function FirstPrivateAction({ onNavigate }: { onNavigate: (v: View) => void }) {
  const { isAuthenticated, user } = useAuth();
  const [visible, setVisible] = React.useState(false);
  React.useEffect(() => {
    if (!isAuthenticated || !user) { setVisible(false); return; }
    try { setVisible(!localStorage.getItem(FIRST_ACTION_KEY)); } catch { setVisible(true); }
  }, [isAuthenticated, user]);
  if (!visible) return null;
  const dismiss = () => { try { localStorage.setItem(FIRST_ACTION_KEY, '1'); } catch {} setVisible(false); };
  return (
    <motion.div initial={{ opacity: 0, y: -6 }} animate={{ opacity: 1, y: 0 }} style={{ marginBottom: 18, padding: '16px 18px', background: 'rgba(0,212,170,0.06)', border: '1px solid rgba(0,212,170,0.28)', borderRadius: 11 }} data-testid="panel-first-private-action">
      <p style={{ fontFamily: 'sans-serif', fontSize: 10, letterSpacing: '0.18em', textTransform: 'uppercase', color: 'rgba(0,212,170,0.7)', margin: '0 0 8px' }}>Your private field is open</p>
      <p style={{ fontFamily: 'serif', fontSize: 13, color: 'rgba(212,223,232,0.65)', margin: '0 0 14px', lineHeight: 1.55 }}>Signed in as {user?.email || 'you'}. Notes and Oracle context stay on this account.</p>
      <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
        <button type="button" data-testid="button-first-oracle" onClick={() => { dismiss(); onNavigate('commune'); }} style={{ width: '100%', padding: 12, background: 'rgba(0,212,170,0.12)', border: '1px solid rgba(0,212,170,0.4)', borderRadius: 9, color: '#00D4AA', fontFamily: 'sans-serif', fontSize: 10, letterSpacing: '0.16em', textTransform: 'uppercase', cursor: 'pointer' }}>Ask the Oracle with your memory</button>
        <button type="button" data-testid="button-first-capture" onClick={() => { dismiss(); onNavigate('solspire'); }} style={{ width: '100%', padding: 12, background: 'rgba(201,168,76,0.08)', border: '1px solid rgba(201,168,76,0.35)', borderRadius: 9, color: 'rgba(201,168,76,0.9)', fontFamily: 'sans-serif', fontSize: 10, letterSpacing: '0.16em', textTransform: 'uppercase', cursor: 'pointer' }}>Capture a private note</button>
        <button type="button" onClick={dismiss} style={{ background: 'none', border: 'none', color: 'rgba(232,232,232,0.3)', fontSize: 10, letterSpacing: '0.1em', cursor: 'pointer', padding: 6 }}>Dismiss</button>
      </div>
    </motion.div>
  );
}

function Home({ onNavigate }: { onNavigate: (v: View) => void }) {
  const { isAuthenticated, profile } = useAuth();
  return (
    <div className="min-h-screen w-full relative">
      <div className="aurora-bg" />
      <div className="page-column relative z-10 pt-10 pb-16 flex flex-col">
        <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ duration: 0.7 }} style={{ marginBottom: '26px', display: 'flex', justifyContent: 'center' }}>
          <FieldPulse />
        </motion.div>
        <FirstPrivateAction onNavigate={onNavigate} />
        {isAuthenticated && profile && (
          <motion.div initial={{ opacity: 0, y: -8 }} animate={{ opacity: 1, y: 0 }} style={{ marginBottom: '16px', display: 'flex', justifyContent: 'center' }}>
            <div style={{ display: 'inline-flex', alignItems: 'center', gap: '8px', padding: '6px 14px', background: 'rgba(201,168,76,0.06)', border: '1px solid rgba(201,168,76,0.2)', borderRadius: '20px' }}>
              <span style={{ fontSize: '12px' }}>{profile.role_sigil}</span>
              <p style={{ fontFamily: 'sans-serif', fontSize: '9px', letterSpacing: '0.2em', textTransform: 'uppercase', color: 'rgba(201,168,76,0.6)', margin: 0 }}>{profile.display_name} \u00b7 {profile.role}</p>
            </div>
          </motion.div>
        )}
        <motion.h1 initial={{ opacity: 0, y: 14 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 1, delay: 0.18 }}
          style={{ fontFamily: '\"Cinzel\", serif', fontSize: '52px', letterSpacing: '0.18em', textAlign: 'center', color: '#C9A84C', textShadow: '0 0 50px rgba(201,168,76,0.40)', marginBottom: '10px', lineHeight: 1 }}>
          ARKADIA
        </motion.h1>
        <motion.p initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 0.32 }}
          style={{ fontFamily: 'serif', fontSize: '17px', lineHeight: '1.5', color: 'rgba(232,232,232,0.78)', margin: '0 0 22px', textAlign: 'center', maxWidth: '28em', alignSelf: 'center' }}>
          {isAuthenticated ? 'Your private workspace is open \u2014 conversations, notes, and projects stay with you.' : 'A place to think, remember, and build \u2014 with AI that keeps your thread.'}
        </motion.p>
        <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 0.55 }} style={{ marginBottom: '10px' }}>
          <button onClick={() => onNavigate('commune')} data-testid="button-home-oracle"
            style={{ width: '100%', padding: '17px', background: 'linear-gradient(135deg, rgba(0,212,170,0.16), rgba(0,212,170,0.06))', border: '1px solid rgba(0,212,170,0.5)', borderRadius: '11px', color: '#00D4AA', fontFamily: 'sans-serif', fontSize: '11px', letterSpacing: '0.22em', textTransform: 'uppercase', cursor: 'pointer' }}>
            {isAuthenticated ? '\u27d0 Continue with the Oracle' : '\u27d0 Start free \u2014 talk to the Oracle'}
          </button>
        </motion.div>
        <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 0.65 }} style={{ marginBottom: '10px' }}>
          <button onClick={() => onNavigate(isAuthenticated ? 'solspire' : 'login')} data-testid="button-home-private"
            style={{ width: '100%', padding: '13px', background: 'rgba(14,17,32,0.55)', border: '1px solid rgba(201,168,76,0.28)', borderRadius: '11px', color: 'rgba(201,168,76,0.85)', fontFamily: 'sans-serif', fontSize: '10px', letterSpacing: '0.2em', textTransform: 'uppercase', cursor: 'pointer' }}>
            {isAuthenticated ? 'Open your private field' : 'Create account for private memory'}
          </button>
        </motion.div>
        <div style={{ display: 'flex', flexDirection: 'column', gap: '6px', marginBottom: '30px', marginTop: 18 }}>
          <PortalDoor label="Oracle" sub="ARKANA \u00b7 Pattern intelligence \u00b7 Live commune" color="#00D4AA" sigil="\u27d0" onClick={() => onNavigate('commune')} delay={1.12} />
          <PortalDoor label="NovaNet \u2014 Nexus Hub" sub="Public Feed \u00b7 ReasoMate \u00b7 Offerings \u00b7 Stellar Cartography" color="#6A9FD8" sigil="\u25c9" onClick={() => onNavigate('novanet')} delay={1.13} />
          <PortalDoor label="SolSpire Console" sub="Echo Field Matrix \u00b7 Spiral Codex \u00b7 Personal Codex \u00b7 Projects \u00b7 Knowledge" color="#C9A84C" sigil="\u25c9" onClick={() => onNavigate('solspire')} delay={1.14} />
          <PortalDoor label="SCI" sub="Spiral Command Interface \u00b7 operator shell" color="#00D4AA" sigil="\u2318" onClick={() => onNavigate('sci')} delay={1.15} />
          <PortalDoor label="ReasoMate" sub="Arkana messenger \u00b7 continuous conversation" color="#6A9FD8" sigil="\u2727" onClick={() => onNavigate('reasomate')} delay={1.16} />
          <PortalDoor label="Offerings" sub="IMS Sessions \u00b7 Products \u00b7 AIC Diagnostic" color="#00D4AA" sigil="\u2726" onClick={() => onNavigate('offerings')} delay={1.18} />
        </div>
        {!isAuthenticated && (
          <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 1.45 }} style={{ marginBottom: '16px', textAlign: 'center' }}>
            <button onClick={() => onNavigate('login')} style={{ background: 'none', border: 'none', color: 'rgba(0,212,170,0.35)', fontFamily: 'sans-serif', fontSize: '10px', letterSpacing: '0.18em', textTransform: 'uppercase', cursor: 'pointer' }} data-testid="button-home-login">\ud83d\udd10 Sign in for private memory \u2192</button>
          </motion.div>
        )}
      </div>
    </div>
  );
}

function DashboardGate({ onNavigate }: { onNavigate: (v: View) => void }) {
  const { isAuthenticated, loading } = useAuth();
  if (loading) return <div style={{ padding: '80px 20px', textAlign: 'center' }}><p style={{ fontFamily: 'sans-serif', fontSize: '10px', letterSpacing: '0.28em', textTransform: 'uppercase', color: 'rgba(0,212,170,0.4)' }}>Verifying node identity\u2026</p></div>;
  if (!isAuthenticated) {
    return (
      <div style={{ padding: '60px 20px', textAlign: 'center', maxWidth: '420px', margin: '0 auto' }}>
        <h2 style={{ fontFamily: 'serif', fontSize: '22px', color: '#00D4AA', marginBottom: '10px' }}>Authenticated Chamber</h2>
        <button onClick={() => onNavigate('login')} style={{ padding: '13px 28px', background: 'rgba(0,212,170,0.08)', border: '1px solid rgba(0,212,170,0.3)', borderRadius: '9px', color: '#00D4AA', fontFamily: 'sans-serif', fontSize: '10px', letterSpacing: '0.2em', textTransform: 'uppercase', cursor: 'pointer' }}>\u27d0 Enter Node Login</button>
      </div>
    );
  }
  return <Suspense fallback={<div style={{ padding: '80px 20px', textAlign: 'center' }}><p style={{ color: 'rgba(0,212,170,0.4)' }}>Loading chamber\u2026</p></div>}><DashboardView /></Suspense>;
}

function AppInner() {
  const [view, setView] = useState<View>('home');
  const [soulPhrase, setSoulPhrase] = useState<string | undefined>(undefined);
  const [aicSeed, setAicSeed] = useState<any>(null);
  const { isAuthenticated } = useAuth();
  const handleEnterField = (phrase: string) => { setSoulPhrase(phrase); setView('commune'); };
  const handleNavigate = (v: View) => {
    if (v !== 'commune') setSoulPhrase(undefined);
    setView(v === 'nexus' ? 'novanet' : v);
  };
  React.useEffect(() => {
    if (isAuthenticated && view === 'login') setView('home');
  }, [isAuthenticated, view]);
  const wrap = { minHeight: 'calc(100vh - 57px)', padding: '28px 16px 60px' };
  return (
    <ArkadiaNavigation currentView={view} onNavigate={handleNavigate}>
      <SonataBar />
      <AnimatePresence mode="wait">
        {view === 'home' && (<motion.div key="home" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} transition={{ duration: 0.45 }}><Home onNavigate={handleNavigate} /></motion.div>)}
        {view === 'gate' && (<motion.div key="gate" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} transition={{ duration: 0.45 }}><LivingGate onEnterField={handleEnterField} onGoToOfferings={() => handleNavigate('offerings')} onAICComplete={setAicSeed} onGoToReset={() => handleNavigate('reset')} /></motion.div>)}
        {view === 'commune' && (<motion.div key="commune" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} transition={{ duration: 0.38 }}><ArkanaCommune initialMessage={soulPhrase} /></motion.div>)}
        {view === 'reset' && (<motion.div key="reset" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} transition={{ duration: 0.45 }} style={wrap}><CoherenceReset /></motion.div>)}
        {view === 'encyclopedia' && (<motion.div key="encyclopedia" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} transition={{ duration: 0.45 }}><NexusSpiralCodex initialMode="scrolls" /></motion.div>)}
        {view === 'spiral-codex' && (<motion.div key="spiral-codex" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} transition={{ duration: 0.45 }}><SpiralCodexFeed onBack={() => handleNavigate('solspire')} /></motion.div>)}
        {view === 'loops' && (<motion.div key="loops" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} transition={{ duration: 0.45 }}><SolSpireConsole onNavigate={handleNavigate} initialSection="loops" /></motion.div>)}
        {view === 'grove' && (<motion.div key="grove" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} transition={{ duration: 0.45 }} style={wrap}><SpiralGrovePage /></motion.div>)}
        {view === 'larder' && (<motion.div key="larder" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} transition={{ duration: 0.45 }} style={wrap}><LivingLarderPage /></motion.div>)}
        {view === 'ims' && (<motion.div key="ims" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} transition={{ duration: 0.45 }} style={wrap}><IMSArchivePage /></motion.div>)}
        {view === 'novanet' && (<motion.div key="novanet" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} transition={{ duration: 0.45 }} style={wrap}><NexusPage /></motion.div>)}
        {view === 'distribute' && (<motion.div key="distribute" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} transition={{ duration: 0.45 }} style={wrap}><DistributePage /></motion.div>)}
        {view === 'offerings' && (<motion.div key="offerings" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} transition={{ duration: 0.45 }}><OfferingsPage onGoToAIC={() => handleNavigate('gate')} aicSeed={aicSeed} /></motion.div>)}
        {view === 'aic' && (<motion.div key="aic" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} transition={{ duration: 0.45 }}><LivingGate onEnterField={handleEnterField} onGoToOfferings={() => handleNavigate('offerings')} onAICComplete={setAicSeed} initialMode="aic" /></motion.div>)}
        {view === 'dashboard' && (<motion.div key="dashboard" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} transition={{ duration: 0.45 }} style={wrap}><DashboardGate onNavigate={handleNavigate} /></motion.div>)}
        {view === 'about' && (<motion.div key="about" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} transition={{ duration: 0.45 }} style={wrap}><AboutArkadia /></motion.div>)}
        {view === 'login' && (<motion.div key="login" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} transition={{ duration: 0.45 }}><LoginPage onSuccess={() => setView('home')} onBack={() => setView('home')} /></motion.div>)}
        {view === 'codex' && (<motion.div key="codex" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} transition={{ duration: 0.45 }}><SolSpireConsole onNavigate={handleNavigate} initialSection="codex" /></motion.div>)}
        {view === 'pulse' && (<motion.div key="pulse" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} transition={{ duration: 0.45 }} style={wrap}><ArkadianPulse /></motion.div>)}
        {view === 'settings' && (<motion.div key="settings" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} transition={{ duration: 0.35 }} style={wrap}><SettingsPage /></motion.div>)}
        {view === 'sci' && (<motion.div key="sci" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} transition={{ duration: 0.35 }}><SpiralCommandInterface onNavigate={handleNavigate} /></motion.div>)}
        {view === 'solspire' && (<motion.div key="solspire" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} transition={{ duration: 0.35 }}><SolSpireConsole onNavigate={handleNavigate} /></motion.div>)}
        {view === 'knowledge-os' && (<motion.div key="knowledge-os" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} transition={{ duration: 0.35 }}><SolSpireConsole onNavigate={handleNavigate} initialSection="knowledge" /></motion.div>)}
        {view === 'reasomate' && (<motion.div key="reasomate" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} transition={{ duration: 0.35 }}><ReasoMatePage /></motion.div>)}
        {view === 'personal-echofeild' && (<motion.div key="personal-echofeild" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} transition={{ duration: 0.35 }}><SolSpireConsole onNavigate={handleNavigate} initialSection="field" /></motion.div>)}
        {view === 'echofeild-matrix' && (<motion.div key="echofeild-matrix" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} transition={{ duration: 0.35 }}><SolSpireConsole onNavigate={handleNavigate} initialSection="field" /></motion.div>)}
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
