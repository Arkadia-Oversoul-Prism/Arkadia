import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { AuthProvider, useAuth } from './contexts/AuthContext';
import ArkadiaNavigation from './components/ArkadiaNavigation';
import LivingGate from './pages/LivingGate';
import ArkanaCommune from './components/ArkanaCommune';
import CoherenceReset from './pages/CoherenceReset';
import AboutArkadia from './pages/AboutArkadia';
import DashboardView from './pages/DashboardView';
import NexusPage from './pages/NexusPage';
import EncyclopediaGalactica from './pages/EncyclopediaGalactica';
import NexusSpiralCodex from './pages/NexusSpiralCodex';
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
  | 'aic';

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

function PortalDoor({ label, sub, color, sigil, onClick, delay, locked }: {
  label: string; sub: string; color: string; sigil: string;
  onClick: () => void; delay: number; locked?: boolean;
}) {
  const [hovered, setHovered] = useState(false);
  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ delay, duration: 0.55 }}
      onClick={onClick} onMouseEnter={() => setHovered(true)} onMouseLeave={() => setHovered(false)}
      style={{ padding: '15px 17px', background: hovered ? `${color}09` : 'rgba(255,255,255,0.015)', border: `1px solid ${hovered ? color + '40' : 'rgba(255,255,255,0.05)'}`, borderRadius: '11px', cursor: 'pointer', transition: 'all 0.22s', display: 'flex', alignItems: 'center', gap: '14px', opacity: locked ? 0.5 : 1 }}
    >
      <motion.span animate={{ opacity: hovered ? 1 : [0.35, 0.75, 0.35] }} transition={{ duration: 3.5, repeat: Infinity }}
        style={{ fontSize: '18px', flexShrink: 0, width: '26px', textAlign: 'center' }}>{sigil}</motion.span>
      <div style={{ flex: 1 }}>
        <p style={{ fontFamily: 'sans-serif', fontSize: '10px', letterSpacing: '0.22em', textTransform: 'uppercase', color: hovered ? color : 'rgba(232,232,232,0.52)', margin: '0 0 3px', transition: 'color 0.2s' }}>{label}</p>
        <p style={{ fontFamily: 'sans-serif', fontSize: '11px', color: 'rgba(232,232,232,0.28)', margin: 0 }}>{sub}</p>
      </div>
      <span style={{ color: hovered ? color : 'rgba(255,255,255,0.13)', fontSize: '12px', transition: 'color 0.2s' }}>
        {locked ? '🔐' : '→'}
      </span>
    </motion.div>
  );
}

// ─── HOME ─────────────────────────────────────────────────────────────────────

function Home({ onNavigate }: { onNavigate: (v: View) => void }) {
  const { isAuthenticated, profile } = useAuth();

  return (
    <div className="min-h-screen w-full relative">
      <div className="aurora-bg" />
      <div className="page-column relative z-10 pt-10 pb-16 flex flex-col">

        <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ duration: 0.7 }}
          style={{ marginBottom: '26px', display: 'flex', justifyContent: 'center' }}>
          <FieldPulse />
        </motion.div>

        {isAuthenticated && profile && (
          <motion.div
            initial={{ opacity: 0, y: -8 }}
            animate={{ opacity: 1, y: 0 }}
            style={{ marginBottom: '16px', display: 'flex', justifyContent: 'center' }}
          >
            <div style={{ display: 'inline-flex', alignItems: 'center', gap: '8px', padding: '6px 14px', background: 'rgba(201,168,76,0.06)', border: '1px solid rgba(201,168,76,0.2)', borderRadius: '20px' }}>
              <span style={{ fontSize: '12px' }}>{profile.role_sigil}</span>
              <p style={{ fontFamily: 'sans-serif', fontSize: '9px', letterSpacing: '0.2em', textTransform: 'uppercase', color: 'rgba(201,168,76,0.6)', margin: 0 }}>
                {profile.display_name} · {profile.role}
              </p>
            </div>
          </motion.div>
        )}

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
          {isAuthenticated ? 'The field recognises you. Your chambers are open.' : 'Arkadia is a field. The IMS is the door.'}
        </motion.p>

        {!isAuthenticated && (
          <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 0.6 }} style={{ marginBottom: '10px' }}>
            <button onClick={() => onNavigate('gate')}
              style={{ width: '100%', padding: '18px', background: 'linear-gradient(135deg, rgba(201,168,76,0.12), rgba(201,168,76,0.06))', border: '1px solid rgba(201,168,76,0.38)', borderRadius: '12px', color: '#C9A84C', fontFamily: 'sans-serif', fontSize: '11px', letterSpacing: '0.22em', textTransform: 'uppercase', cursor: 'pointer', backdropFilter: 'blur(12px)', WebkitBackdropFilter: 'blur(12px)' }}>
              ✦ Identity Mapping Session — $777 — Begin Here
            </button>
          </motion.div>
        )}

        <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 0.72 }} style={{ marginBottom: '28px' }}>
          <button onClick={() => onNavigate('reset')}
            style={{ width: '100%', padding: '14px', background: 'rgba(0,212,170,0.05)', border: '1px solid rgba(0,212,170,0.2)', borderRadius: '12px', color: '#00D4AA', fontFamily: 'sans-serif', fontSize: '11px', letterSpacing: '0.22em', textTransform: 'uppercase', cursor: 'pointer' }}>
            ⟐ 5-Minute Field Reset — Free
          </button>
        </motion.div>

        {!isAuthenticated && (
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
        )}

        <motion.p initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 1.1 }}
          style={{ fontFamily: 'sans-serif', fontSize: '9px', letterSpacing: '0.28em', textTransform: 'uppercase', color: 'rgba(232,232,232,0.18)', marginBottom: '11px' }}>
          The Field
        </motion.p>

        <div style={{ display: 'flex', flexDirection: 'column', gap: '7px', marginBottom: '30px' }}>
          <PortalDoor label="Offerings" sub="Sessions · Products · AIC Diagnostic · Book Now" color="#C9A84C" sigil="✦" onClick={() => onNavigate('offerings')} delay={1.12} />
          <PortalDoor label="AIC Diagnostic" sub="Arkadian Identity Cartography · Free · 20 min · Via Living Gate" color="#00D4AA" sigil="◎" onClick={() => onNavigate('gate')} delay={1.13} />
          <PortalDoor label="Oracle" sub="ARKANA · Pattern intelligence · Live commune" color="#00D4AA" sigil="⟐" onClick={() => onNavigate('commune')} delay={1.14} />
          <PortalDoor label="Nexus" sub="Spiral Codex · IMS Archive · Spiral Grove · Living Larder" color="#C9A84C" sigil="☥" onClick={() => onNavigate('nexus')} delay={1.17} />
          <PortalDoor label="Encyclopedia Galactica" sub="Crystal Matrix · 12 Chambers · The Living Library" color="#B08DE8" sigil="✧" onClick={() => onNavigate('encyclopedia')} delay={1.19} />
          <PortalDoor label="Spiral Codex" sub="Crystal Matrix · Corpus Intelligence · 26+ Scrolls" color="#C9A84C" sigil="⟐" onClick={() => onNavigate('spiral-codex')} delay={1.21} />
          <PortalDoor label="Open Loops" sub="Active initiatives · Next actions · Critical threads" color="#E88C6A" sigil="∞" onClick={() => onNavigate('loops')} delay={1.23} />
          <PortalDoor label="Spiral Grove" sub="A.I.S. Learning Layer · Three-field architecture" color="#00D4AA" sigil="🌿" onClick={() => onNavigate('grove')} delay={1.25} />
          <PortalDoor label="Living Larder" sub="Sovereign food network · Eden Farm · Saturday Hub" color="#4CAF50" sigil="🌾" onClick={() => onNavigate('larder')} delay={1.26} />
          <PortalDoor label="IMS Archive" sub="Identity Mapping Sessions · Sealed scrolls" color="#C84848" sigil="∞" onClick={() => onNavigate('ims')} delay={1.27} />
          <PortalDoor label="NovaNet" sub="Living node mesh · Silicon · Transmission · Human Field" color="#6A9FD8" sigil="◉" onClick={() => onNavigate('novanet')} delay={1.28} />
          <PortalDoor label="Distribute" sub="Sovereign music distribution · 100% master ownership" color="#C9A84C" sigil="⟁" onClick={() => onNavigate('distribute')} delay={1.29} />
          <PortalDoor
            label="Dashboard"
            sub={isAuthenticated ? "Open loops · Personal field · Action matrix" : "Authenticated nodes only — complete your IMS first"}
            color="#E88C6A"
            sigil="◈"
            onClick={() => isAuthenticated ? onNavigate('dashboard') : onNavigate('login')}
            delay={1.30}
            locked={!isAuthenticated}
          />
          {isAuthenticated && (
            <PortalDoor label="Codex" sub="Personal Codex · 90-day architecture · Soul map" color="#C9A84C" sigil="✦" onClick={() => onNavigate('codex')} delay={1.32} />
          )}
          <PortalDoor label="About" sub="Zahrune Nova · Lineage · Architecture" color="#6A9FD8" sigil="✦" onClick={() => onNavigate('about')} delay={1.34} />
        </div>

        {!isAuthenticated && (
          <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 1.45 }} style={{ marginBottom: '16px', textAlign: 'center' }}>
            <button
              onClick={() => onNavigate('login')}
              style={{ background: 'none', border: 'none', color: 'rgba(0,212,170,0.35)', fontFamily: 'sans-serif', fontSize: '10px', letterSpacing: '0.18em', textTransform: 'uppercase', cursor: 'pointer' }}
              data-testid="button-home-login"
            >
              🔐 Already a node? Enter your chamber →
            </button>
          </motion.div>
        )}

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

// ─── DASHBOARD GATE ────────────────────────────────────────────────────────────

function DashboardGate({ onNavigate }: { onNavigate: (v: View) => void }) {
  const { isAuthenticated, loading } = useAuth();

  if (loading) {
    return (
      <div style={{ padding: '80px 20px', textAlign: 'center' }}>
        <motion.div animate={{ opacity: [0.3, 0.7, 0.3] }} transition={{ repeat: Infinity, duration: 2 }}>
          <p style={{ fontFamily: 'sans-serif', fontSize: '10px', letterSpacing: '0.28em', textTransform: 'uppercase', color: 'rgba(0,212,170,0.4)' }}>
            Verifying node identity…
          </p>
        </motion.div>
      </div>
    );
  }

  if (!isAuthenticated) {
    return (
      <div style={{ padding: '60px 20px', textAlign: 'center', maxWidth: '420px', margin: '0 auto' }}>
        <motion.div initial={{ opacity: 0, y: 14 }} animate={{ opacity: 1, y: 0 }}>
          <p style={{ fontFamily: 'sans-serif', fontSize: '22px', marginBottom: '16px' }}>🔐</p>
          <h2 style={{ fontFamily: 'serif', fontSize: '22px', color: '#00D4AA', marginBottom: '10px' }}>Authenticated Chamber</h2>
          <p style={{ fontFamily: 'sans-serif', fontSize: '12px', color: 'rgba(232,232,232,0.4)', lineHeight: '1.7', marginBottom: '24px' }}>
            The Dashboard is open to authenticated nodes — those who have completed an IMS session and received their Personal Codex.
          </p>
          <button
            onClick={() => onNavigate('login')}
            style={{ padding: '13px 28px', background: 'rgba(0,212,170,0.08)', border: '1px solid rgba(0,212,170,0.3)', borderRadius: '9px', color: '#00D4AA', fontFamily: 'sans-serif', fontSize: '10px', letterSpacing: '0.2em', textTransform: 'uppercase', cursor: 'pointer' }}
          >
            ⟐ Enter Node Login
          </button>
          <div style={{ marginTop: '16px' }}>
            <button
              onClick={() => onNavigate('gate')}
              style={{ background: 'none', border: 'none', color: 'rgba(201,168,76,0.4)', fontFamily: 'sans-serif', fontSize: '10px', letterSpacing: '0.16em', textTransform: 'uppercase', cursor: 'pointer' }}
            >
              Book an IMS session →
            </button>
          </div>
        </motion.div>
      </div>
    );
  }

  return <DashboardView />;
}

// ─── APP ──────────────────────────────────────────────────────────────────────

function AppInner() {
  const [view, setView] = useState<View>('home');
  const [soulPhrase, setSoulPhrase] = useState<string | undefined>(undefined);
  const { isAuthenticated } = useAuth();

  const handleEnterField = (phrase: string) => {
    setSoulPhrase(phrase);
    setView('commune');
  };

  const handleNavigate = (v: View) => {
    if (v !== 'commune') setSoulPhrase(undefined);
    setView(v);
  };

  // Redirect from login to home if already authenticated
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
            <LivingGate onEnterField={handleEnterField} onGoToOfferings={() => handleNavigate('offerings')} />
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

        {view === 'nexus' && (
          <motion.div key="nexus" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} transition={{ duration: 0.45 }} style={wrap}>
            <NexusPage />
          </motion.div>
        )}

        {view === 'encyclopedia' && (
          <motion.div key="encyclopedia" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} transition={{ duration: 0.45 }}>
            <EncyclopediaGalactica />
          </motion.div>
        )}

        {view === 'spiral-codex' && (
          <motion.div key="spiral-codex" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} transition={{ duration: 0.45 }} style={wrap}>
            <NexusSpiralCodex />
          </motion.div>
        )}

        {view === 'loops' && (
          <motion.div key="loops" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} transition={{ duration: 0.45 }} style={wrap}>
            <OpenLoopsPage />
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
            <NovaNetPage />
          </motion.div>
        )}

        {view === 'distribute' && (
          <motion.div key="distribute" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} transition={{ duration: 0.45 }} style={wrap}>
            <DistributePage />
          </motion.div>
        )}

        {view === 'offerings' && (
          <motion.div key="offerings" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} transition={{ duration: 0.45 }}>
            <OfferingsPage onGoToAIC={() => handleNavigate('gate')} />
          </motion.div>
        )}

        {view === 'aic' && (
          <motion.div key="aic" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} transition={{ duration: 0.45 }}>
            <LivingGate onEnterField={handleEnterField} onGoToOfferings={() => handleNavigate('offerings')} initialMode="aic" />
          </motion.div>
        )}

        {view === 'dashboard' && (
          <motion.div key="dashboard" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} transition={{ duration: 0.45 }} style={wrap}>
            <DashboardGate onNavigate={handleNavigate} />
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
          <motion.div key="codex" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} transition={{ duration: 0.45 }} style={wrap}>
            <PersonalCodex />
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
