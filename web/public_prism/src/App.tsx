import React, { useState, Suspense, lazy } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import ArkadiaNavigation from './components/ArkadiaNavigation';
import LivingGate from './pages/LivingGate';
import ArkanaCommune from './components/ArkanaCommune';
import SpiralVault from './components/SpiralVault';
import ShereSanctuary from './components/ShereSanctuary';
import CoherenceReset from './pages/CoherenceReset';

// Dashboard ships its own heavy deps (Recharts, React Query). Lazy-load it so
// the public landing route doesn't pay for a control surface most visitors
// will never see. Vite splits this into its own chunk.
const Dashboard = lazy(() => import('./pages/dashboard/Dashboard'));

const DashboardFallback = () => (
  <div
    style={{
      minHeight: 'calc(100vh - 57px)',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      color: 'rgba(0,212,170,0.55)',
      fontFamily: 'serif',
      fontSize: 13,
      letterSpacing: '0.25em',
      textTransform: 'uppercase',
    }}
  >
    Loading console…
  </div>
);

type View = 'home' | 'gate' | 'commune' | 'vault' | 'reset' | 'sanctuary' | 'dashboard';

// ─── HOME PAGE ────────────────────────────────────────────────────────────────

function Home({ onNavigate }: { onNavigate: (v: View) => void }) {
  return (
    <div className="min-h-screen w-full relative">
      <div className="aurora-bg" />

      <div className="page-column relative z-10 pt-12 pb-16 flex flex-col">

        {/* Label */}
        <motion.p
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ duration: 0.8 }}
          style={{
            fontFamily: 'sans-serif',
            fontSize: '9px',
            letterSpacing: '0.35em',
            textTransform: 'uppercase',
            color: 'rgba(201,168,76,0.55)',
            marginBottom: '10px',
            textAlign: 'center',
          }}
        >
          Identity Architecture
        </motion.p>

        {/* Title */}
        <motion.h1
          initial={{ opacity: 0, y: 16 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 1, delay: 0.2 }}
          style={{
            fontFamily: 'serif',
            fontSize: '48px',
            letterSpacing: '0.12em',
            textAlign: 'center',
            color: '#00D4AA',
            textShadow: '0 0 40px rgba(0,212,170,0.3), 0 0 80px rgba(0,212,170,0.1)',
            marginBottom: '30px',
            lineHeight: 1,
          }}
        >
          ARKADIA
        </motion.h1>

        {/* Hero copy block */}
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.5 }}
          style={{ marginBottom: '32px', display: 'flex', flexDirection: 'column', gap: '6px' }}
        >
          <p
            style={{
              fontFamily: 'serif',
              fontSize: '16px',
              lineHeight: '1.75',
              color: 'rgba(232,232,232,0.82)',
              margin: 0,
            }}
          >
            The precision work of making your inner signal legible —<br />
            to yourself first, then to the world.
          </p>
        </motion.div>

        {/* Sacred text lines */}
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.75 }}
          style={{ marginBottom: '14px', display: 'flex', flexDirection: 'column', gap: '10px' }}
        >
          {[
            'There is a version of you that already knows what to charge.',
            'Already knows what to say when someone asks what you do.',
            'Already knows how to walk into a room and not shrink.',
          ].map((line, i) => (
            <motion.p
              key={i}
              initial={{ opacity: 0, y: 6 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.9 + i * 0.1 }}
              style={{
                fontFamily: 'sans-serif',
                fontSize: '14px',
                color: 'rgba(0,212,170,0.6)',
                margin: 0,
                lineHeight: '1.6',
              }}
            >
              {line}
            </motion.p>
          ))}
        </motion.div>

        {/* Closing line */}
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 1.25 }}
          style={{ marginBottom: '36px' }}
        >
          <p
            style={{
              fontFamily: 'serif',
              fontSize: '15px',
              lineHeight: '1.8',
              color: 'rgba(232,232,232,0.55)',
              margin: 0,
            }}
          >
            That version isn't waiting for more information.<br />
            It's waiting for the ground beneath it to stop shifting.
          </p>
        </motion.div>

        {/* CTA buttons */}
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 1.45 }}
          style={{ display: 'flex', flexDirection: 'column', gap: '12px', marginBottom: '36px' }}
        >
          <button
            onClick={() => window.open('https://subscribepage.io/5-minute-money-reset', '_blank')}
            style={{
              width: '100%',
              padding: '16px',
              background: 'rgba(0,212,170,0.1)',
              border: '1px solid rgba(0,212,170,0.4)',
              borderRadius: '12px',
              color: '#00D4AA',
              fontFamily: 'sans-serif',
              fontSize: '11px',
              letterSpacing: '0.2em',
              textTransform: 'uppercase',
              cursor: 'pointer',
              backdropFilter: 'blur(12px)',
              WebkitBackdropFilter: 'blur(12px)',
              transition: 'all 0.25s ease',
            }}
          >
            FREE GUIDE — 5-MINUTE MONEY RESET
          </button>

          <button
            onClick={() => window.open('https://wa.me/2348144942818', '_blank')}
            style={{
              width: '100%',
              padding: '16px',
              background: 'rgba(201,168,76,0.1)',
              border: '1px solid rgba(201,168,76,0.4)',
              borderRadius: '12px',
              color: '#C9A84C',
              fontFamily: 'sans-serif',
              fontSize: '11px',
              letterSpacing: '0.2em',
              textTransform: 'uppercase',
              cursor: 'pointer',
              backdropFilter: 'blur(12px)',
              WebkitBackdropFilter: 'blur(12px)',
              transition: 'all 0.25s ease',
            }}
          >
            Identity Mapping — $777
          </button>
        </motion.div>

        {/* Product cards */}
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 1.65 }}
          style={{ display: 'flex', flexDirection: 'column', gap: '14px', marginBottom: '40px' }}
        >
          {/* Card 1 — Identity Mapping */}
          <div
            onClick={() => window.open('https://wa.me/2348144942818', '_blank')}
            style={{
              padding: '22px 20px',
              background: 'rgba(13,13,26,0.75)',
              backdropFilter: 'blur(18px)',
              WebkitBackdropFilter: 'blur(18px)',
              border: '1px solid rgba(0,212,170,0.12)',
              borderRadius: '14px',
              cursor: 'pointer',
              transition: 'border-color 0.3s',
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '10px' }}>
              <span style={{ color: '#C9A84C', fontSize: '18px' }}>✦</span>
              <h3
                style={{
                  fontFamily: 'serif',
                  fontSize: '13px',
                  letterSpacing: '0.1em',
                  textTransform: 'uppercase',
                  color: '#C9A84C',
                  margin: 0,
                }}
              >
                Identity Mapping
              </h3>
            </div>
            <p
              style={{
                fontFamily: 'sans-serif',
                fontSize: '13px',
                color: 'rgba(232,232,232,0.5)',
                lineHeight: '1.65',
                margin: '0 0 14px',
              }}
            >
              Locate the exact place where your signal goes quiet.
              90 minutes. One live session. You leave with an Identity
              Architecture Document, a bespoke sigil, and three clear
              next actions.
            </p>
            <span
              style={{
                fontFamily: 'sans-serif',
                fontSize: '10px',
                letterSpacing: '0.18em',
                textTransform: 'uppercase',
                color: '#C9A84C',
                border: '1px solid rgba(201,168,76,0.3)',
                borderRadius: '8px',
                padding: '5px 12px',
                display: 'inline-block',
              }}
            >
              $777 / ₦600,000 — Book via WhatsApp
            </span>
          </div>

          {/* Card 2 — 5-Minute Reset */}
          <div
            onClick={() => window.open('https://subscribepage.io/5-minute-money-reset', '_blank')}
            style={{
              padding: '22px 20px',
              background: 'rgba(13,13,26,0.75)',
              backdropFilter: 'blur(18px)',
              WebkitBackdropFilter: 'blur(18px)',
              border: '1px solid rgba(0,212,170,0.12)',
              borderRadius: '14px',
              cursor: 'pointer',
              transition: 'border-color 0.3s',
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '10px' }}>
              <span style={{ color: '#00D4AA', fontSize: '18px' }}>⟐</span>
              <h3
                style={{
                  fontFamily: 'serif',
                  fontSize: '13px',
                  letterSpacing: '0.1em',
                  textTransform: 'uppercase',
                  color: '#00D4AA',
                  margin: 0,
                }}
              >
                5-Minute Reset
              </h3>
            </div>
            <p
              style={{
                fontFamily: 'sans-serif',
                fontSize: '13px',
                color: 'rgba(232,232,232,0.5)',
                lineHeight: '1.65',
                margin: '0 0 14px',
              }}
            >
              A somatic protocol for when the nervous system is
              running a protection loop. Free. Immediate. No opt-in theater.
            </p>
            <span
              style={{
                fontFamily: 'sans-serif',
                fontSize: '10px',
                letterSpacing: '0.18em',
                textTransform: 'uppercase',
                color: '#00D4AA',
                border: '1px solid rgba(0,212,170,0.3)',
                borderRadius: '8px',
                padding: '5px 12px',
                display: 'inline-block',
              }}
            >
              Free — Get it now
            </span>
          </div>
        </motion.div>

        {/* Oracle nav link */}
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 1.85 }}
          style={{ textAlign: 'center' }}
        >
          <button
            onClick={() => onNavigate('gate')}
            style={{
              background: 'none',
              border: 'none',
              cursor: 'pointer',
              fontFamily: 'serif',
              fontSize: '13px',
              letterSpacing: '0.1em',
              color: 'rgba(0,212,170,0.5)',
              transition: 'color 0.2s',
            }}
          >
            Enter the Oracle →
          </button>
        </motion.div>

        {/* Footer */}
        <footer
          style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            gap: '10px',
            paddingTop: '28px',
            marginTop: '20px',
            borderTop: '1px solid rgba(0,212,170,0.07)',
          }}
        >
          {['Zahrune Nova', '117Hz', 'Pankshin, Nigeria'].map((txt, i) => (
            <React.Fragment key={txt}>
              <span
                style={{
                  fontFamily: 'sans-serif',
                  fontSize: '9px',
                  letterSpacing: '0.22em',
                  textTransform: 'uppercase',
                  color: 'rgba(232,232,232,0.2)',
                }}
              >
                {txt}
              </span>
              {i < 2 && (
                <span style={{ color: 'rgba(0,212,170,0.2)', fontSize: '7px' }}>◆</span>
              )}
            </React.Fragment>
          ))}
        </footer>

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

  return (
    <ArkadiaNavigation currentView={view} onNavigate={handleNavigate}>
      <AnimatePresence mode="wait">
        {view === 'home' && (
          <motion.div key="home" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} transition={{ duration: 0.55 }}>
            <Home onNavigate={handleNavigate} />
          </motion.div>
        )}

        {view === 'gate' && (
          <motion.div key="gate" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} transition={{ duration: 0.55 }}>
            <LivingGate onEnterField={handleEnterField} />
          </motion.div>
        )}

        {view === 'commune' && (
          <motion.div
            key="commune"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.55 }}
            style={{ minHeight: 'calc(100vh - 57px)', display: 'flex', alignItems: 'flex-start', justifyContent: 'center', padding: '20px 16px 40px' }}
          >
            <div style={{ width: '100%', maxWidth: '640px' }}>
              <ArkanaCommune initialMessage={soulPhrase} />
            </div>
          </motion.div>
        )}

        {view === 'reset' && (
          <motion.div
            key="reset"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.55 }}
            style={{ minHeight: 'calc(100vh - 57px)', padding: '28px 16px 60px' }}
          >
            <CoherenceReset />
          </motion.div>
        )}

        {view === 'vault' && (
          <motion.div
            key="vault"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.55 }}
            style={{ minHeight: 'calc(100vh - 57px)', padding: '28px 16px 60px' }}
          >
            <SpiralVault />
          </motion.div>
        )}

        {view === 'sanctuary' && (
          <motion.div
            key="sanctuary"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.55 }}
            style={{ minHeight: 'calc(100vh - 57px)', padding: '28px 16px 60px' }}
          >
            <ShereSanctuary />
          </motion.div>
        )}

        {view === 'dashboard' && (
          <motion.div
            key="dashboard"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.4 }}
          >
            <Suspense fallback={<DashboardFallback />}>
              <Dashboard />
            </Suspense>
          </motion.div>
        )}
      </AnimatePresence>
    </ArkadiaNavigation>
  );
}

export default App;
