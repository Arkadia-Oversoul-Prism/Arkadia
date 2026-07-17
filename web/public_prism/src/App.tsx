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
import ArkadianPulse from './pages/ArkadianPulse';
import SettingsPage from './pages/SettingsPage';
import SolSpireConsole from './pages/SolSpireConsole';
import KnowledgeOSPage from './pages/knowledge/KnowledgeOSPage';

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
  | 'solspire'
  | 'knowledge-os';

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
        Field Active · 117 Hz · Jos Node 1759
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
        backdropFilter: 'blur(16px)',
        WebkitBackdropFilter: 'blur(16px)',
        boxShadow: hovered
          ? `0 4px 24px rgba(0,0,0,0.55), 0 0 0 1px ${color}22, inset 0 1px 0 rgba(255,255,255,0.06)`
          : '0 2px 12px rgba(0,0,0,0.35), inset 0 1px 0 rgba(255,255,255,0.03)',
      }}
    >
      <motion.span animate={{ opacity: hovered ? 1 : [0.5, 0.85, 0.5] }} transition={{ duration: 3.5, repeat: Infinity }}
        style={{ fontSize: '16px', flexShrink: 0, width: '24px', textAlign: 'center' }}>{sigil}</motion.span>
      <div style={{ flex: 1 }}>
        <p style={{ fontFamily: 'sans-serif', fontSize: '10px', letterSpacing: '0.22em', textTransform: 'uppercase', color: hovered ? color : 'rgba(232,232,232,0.72)', margin: '0 0 3px', transition: 'color 0.2s', fontWeight: 500 }}>{label}</p>
        <p style={{ fontFamily: 'sans-serif', fontSize: '11px', color: 'rgba(232,232,232,0.38)', margin: 0, lineHeight: 1.4 }}>{sub}</p>
      </div>
      <span style={{ color: hovered ? color : 'rgba(255,255,255,0.22)', fontSize: '11px', transition: 'color 0.2s', flexShrink: 0 }}>
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

        {/* Geometric ornament divider */}
        <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 0.08 }}
          style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '18px' }}>
          <div style={{ flex: 1, height: '1px', background: 'linear-gradient(90deg, transparent, rgba(201,168,76,0.30))' }} />
          <div style={{ width: '7px', height: '7px', border: '1px solid rgba(201,168,76,0.55)', transform: 'rotate(45deg)', backgroundColor: '#0C0D18' }} />
          <div style={{ flex: 1, height: '1px', background: 'linear-gradient(270deg, transparent, rgba(201,168,76,0.30))' }} />
        </motion.div>

        <motion.p initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 0.12 }}
          style={{ fontFamily: 'sans-serif', fontSize: '9px', letterSpacing: '0.35em', textTransform: 'uppercase', color: 'rgba(201,168,76,0.65)', marginBottom: '9px', textAlign: 'center' }}>
          Cognitive Sovereignty Framework
        </motion.p>

        <motion.h1 initial={{ opacity: 0, y: 14 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 1, delay: 0.18 }}
          style={{ fontFamily: '"Cinzel", serif', fontSize: '52px', letterSpacing: '0.18em', textAlign: 'center', color: '#C9A84C', textShadow: '0 0 50px rgba(201,168,76,0.40), 0 0 120px rgba(201,168,76,0.15)', marginBottom: '10px', lineHeight: 1 }}>
          ARKADIA
        </motion.h1>

        <motion.p initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 0.42 }}
          style={{ fontFamily: 'serif', fontSize: '13px', lineHeight: '1.9', color: 'rgba(212,223,232,0.55)', margin: '0 0 28px', textAlign: 'center', letterSpacing: '0.02em' }}>
          {isAuthenticated ? 'The field recognises you. Your chambers are open.' : 'Arkadia is a field. The IMS is the door.'}
        </motion.p>

        <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 0.6 }} style={{ marginBottom: '18px' }}>
          <button onClick={() => onNavigate('gate')}
            style={{ width: '100%', padding: '17px', background: 'linear-gradient(135deg, rgba(0,212,170,0.12), rgba(0,212,170,0.05))', border: '1px solid rgba(0,212,170,0.45)', borderRadius: '11px', color: '#00D4AA', fontFamily: 'sans-serif', fontSize: '11px', letterSpacing: '0.22em', textTransform: 'uppercase', cursor: 'pointer', backdropFilter: 'blur(16px)', WebkitBackdropFilter: 'blur(16px)', boxShadow: '0 4px 24px rgba(0,212,170,0.08), inset 0 1px 0 rgba(255,255,255,0.06)' }}>
            ⟐ Begin Your 5-Minute Reset
          </button>
        </motion.div>

        {!isAuthenticated && (
          <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 0.88 }}
            style={{ marginBottom: '24px', padding: '18px 20px', background: 'rgba(14,17,32,0.72)', border: '1px solid rgba(201,168,76,0.20)', borderRadius: '10px', backdropFilter: 'blur(16px)', WebkitBackdropFilter: 'blur(16px)', boxShadow: '0 2px 16px rgba(0,0,0,0.40), inset 0 1px 0 rgba(255,255,255,0.04)', position: 'relative' }}>
            {/* Corner ornaments */}
            <div style={{ position: 'absolute', top: 0, left: 0, width: 8, height: 8, borderTop: '1px solid rgba(201,168,76,0.55)', borderLeft: '1px solid rgba(201,168,76,0.55)' }} />
            <div style={{ position: 'absolute', top: 0, right: 0, width: 8, height: 8, borderTop: '1px solid rgba(201,168,76,0.55)', borderRight: '1px solid rgba(201,168,76,0.55)' }} />
            <div style={{ position: 'absolute', bottom: 0, left: 0, width: 8, height: 8, borderBottom: '1px solid rgba(201,168,76,0.55)', borderLeft: '1px solid rgba(201,168,76,0.55)' }} />
            <div style={{ position: 'absolute', bottom: 0, right: 0, width: 8, height: 8, borderBottom: '1px solid rgba(201,168,76,0.55)', borderRight: '1px solid rgba(201,168,76,0.55)' }} />
            {[
              'There is a version of you that already knows what to charge.',
              'Already knows what to say when someone asks what you do.',
              'Already knows how to walk into a room and not shrink.',
            ].map((line, i) => (
              <motion.p key={i} initial={{ opacity: 0, x: -6 }} animate={{ opacity: 1, x: 0 }} transition={{ delay: 0.96 + i * 0.1 }}
                style={{ fontFamily: 'sans-serif', fontSize: '13px', color: i === 0 ? 'rgba(212,223,232,0.72)' : 'rgba(212,223,232,0.48)', margin: i < 2 ? '0 0 8px' : 0, lineHeight: '1.65' }}>
                {line}
              </motion.p>
            ))}
            <motion.p initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 1.28 }}
              style={{ fontFamily: 'serif', fontSize: '13px', color: 'rgba(212,223,232,0.50)', margin: '14px 0 0', lineHeight: '1.9', borderTop: '1px solid rgba(201,168,76,0.12)', paddingTop: '13px' }}>
              That version isn't waiting for more information.<br />
              It's waiting for the ground beneath it to stop shifting.
            </motion.p>
          </motion.div>
        )}

        {/* Portal grid divider */}
        <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 1.08 }}
          style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '14px' }}>
          <div style={{ flex: 1, height: '1px', background: 'linear-gradient(90deg, transparent, rgba(0,212,170,0.25))' }} />
          <div style={{ width: '5px', height: '5px', border: '1px solid rgba(0,212,170,0.45)', transform: 'rotate(45deg)', backgroundColor: '#0C0D18' }} />
          <span style={{ fontFamily: '"Cinzel", serif', fontSize: '8px', letterSpacing: '0.35em', textTransform: 'uppercase', color: 'rgba(0,212,170,0.55)', whiteSpace: 'nowrap' }}>The Field</span>
          <div style={{ width: '5px', height: '5px', border: '1px solid rgba(0,212,170,0.45)', transform: 'rotate(45deg)', backgroundColor: '#0C0D18' }} />
          <div style={{ flex: 1, height: '1px', background: 'linear-gradient(270deg, transparent, rgba(0,212,170,0.25))' }} />
        </motion.div>

        <div style={{ display: 'flex', flexDirection: 'column', gap: '6px', marginBottom: '30px' }}>
          <PortalDoor label="Oracle" sub="ARKANA · Pattern intelligence · Live commune" color="#00D4AA" sigil="⟐" onClick={() => onNavigate('commune')} delay={1.12} />
          <PortalDoor label="Nexus Hub" sub="IMS · Encyclopedia Galactica · Spiral Codex · Grove · Larder · Distribute" color="#C9A84C" sigil="☥" onClick={() => onNavigate('nexus')} delay={1.14} />
          <PortalDoor label="SolSpire Console" sub="Personal Codex · Knowledge OS · Projects · Operational Console" color="#C9A84C" sigil="◉" onClick={() => onNavigate('solspire')} delay={1.16} />
          <PortalDoor label="Offerings" sub="IMS Sessions · Products · AIC Diagnostic" color="#00D4AA" sigil="✦" onClick={() => onNavigate('offerings')} delay={1.18} />
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
          {['Zahrune Nova', '117 Hz', 'Jos Node 1759'].map((txt, i) => (
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

  return (
    <Suspense fallback={
      <div style={{ padding: '80px 20px', textAlign: 'center' }}>
        <motion.p animate={{ opacity: [0.3, 0.7, 0.3] }} transition={{ repeat: Infinity, duration: 2 }}
          style={{ fontFamily: 'sans-serif', fontSize: '10px', letterSpacing: '0.28em', textTransform: 'uppercase', color: 'rgba(0,212,170,0.4)' }}>
          Loading chamber…
        </motion.p>
      </div>
    }>
      <DashboardView />
    </Suspense>
  );
}

// ─── APP ──────────────────────────────────────────────────────────────────────

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
            <LivingGate
              onEnterField={handleEnterField}
              onGoToOfferings={() => handleNavigate('offerings')}
              onAICComplete={setAicSeed}
              onGoToReset={() => handleNavigate('reset')}
            />
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
            <NexusSpiralCodex />
          </motion.div>
        )}

        {view === 'spiral-codex' && (
          <motion.div key="spiral-codex" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} transition={{ duration: 0.45 }}>
            <EncyclopediaGalactica />
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
            <OfferingsPage onGoToAIC={() => handleNavigate('gate')} aicSeed={aicSeed} />
          </motion.div>
        )}

        {view === 'aic' && (
          <motion.div key="aic" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} transition={{ duration: 0.45 }}>
            <LivingGate
              onEnterField={handleEnterField}
              onGoToOfferings={() => handleNavigate('offerings')}
              onAICComplete={setAicSeed}
              initialMode="aic"
            />
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

        {view === 'solspire' && (
          <motion.div key="solspire" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} transition={{ duration: 0.35 }}>
            <SolSpireConsole />
          </motion.div>
        )}

        {view === 'knowledge-os' && (
          <motion.div key="knowledge-os" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} transition={{ duration: 0.35 }}>
            <KnowledgeOSPage />
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
