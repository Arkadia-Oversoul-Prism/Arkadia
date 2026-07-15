import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useAuth } from '../contexts/AuthContext';

type View =
  | 'home' | 'gate' | 'commune' | 'reset' | 'about' | 'login' | 'codex' | 'dashboard'
  | 'nexus'
  | 'encyclopedia'
  | 'spiral-codex'
  | 'codex-feed'
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

interface NavProps {
  currentView: View;
  onNavigate: (view: View) => void;
  children: React.ReactNode;
}

interface NavItem { label: string; view: View; sigil: string; sub: string; color: string }
interface NavGroup { label: string; items: NavItem[] }

const NAV_GROUPS: NavGroup[] = [
  {
    label: 'Core',
    items: [
      { label: 'Home',         view: 'home',      sigil: '⌂', sub: 'Field entry point',                             color: '#C9A84C' },
      { label: 'Oracle',       view: 'commune',   sigil: '⟐', sub: 'ARKANA · Pattern intelligence',                  color: '#00D4AA' },
      { label: 'Living Gate',  view: 'gate',      sigil: '✦', sub: 'Reset · IMS · AIC Diagnostic · 5-Minute',        color: '#C9A84C' },
    ],
  },
  {
    label: 'Intelligence',
    items: [
      { label: 'Nexus Hub',              view: 'nexus',         sigil: '☥', sub: 'Codex · IMS · Grove · Larder · NovaNet · Distribute', color: '#C9A84C' },
      { label: 'SolSpire Console',       view: 'solspire',      sigil: '◉', sub: 'Projects · Knowledge · Operations · Codex',        color: '#C9A84C' },
    ],
  },
  {
    label: 'Modules',
    items: [
      { label: 'Offerings',    view: 'offerings', sigil: '✦', sub: 'Sessions · Products · Book Now',    color: '#C9A84C' },
      { label: 'Distribute',   view: 'distribute', sigil: '⟁', sub: 'Sovereign music distribution',     color: '#C9A84C' },
    ],
  },
  {
    label: 'System',
    items: [
      { label: 'Settings',  view: 'settings', sigil: '⚙', sub: 'API keys · Configuration', color: '#C9A84C' },
      { label: 'About',    view: 'about',     sigil: '✦', sub: 'Zahrune Nova · Lineage',      color: '#6A9FD8' },
    ],
  },
];

const VIEW_LABEL: Partial<Record<View, string>> = {
  home: 'Home', gate: 'Living Gate', commune: 'Oracle', reset: 'Field Reset', about: 'About',
  login: 'Node Login', codex: 'Personal Codex', dashboard: 'Dashboard',
  nexus: 'Nexus Hub', encyclopedia: 'Encyclopedia Galactica',
  'spiral-codex': 'Spiral Codex', 'codex-feed': 'Codex Feed', loops: 'Open Loops', grove: 'Spiral Grove',
  larder: 'Living Larder', novanet: 'NovaNet', ims: 'IMS Archive',
  distribute: 'Distribute', offerings: 'Offerings', aic: 'AIC Diagnostic',
  pulse: 'Arkadian Pulse', settings: 'Settings', solspire: 'SolSpire Console',
  'knowledge-os': 'Prism — Knowledge OS',
};

function UserSection({ onNavigate, onClose }: { onNavigate: (v: View) => void; onClose: () => void }) {
  const { user, profile, signOut, isAuthenticated } = useAuth();

  if (!isAuthenticated) {
    return (
      <div style={{ padding: '16px 20px', borderTop: '1px solid rgba(255,255,255,0.05)' }}>
        <button
          onClick={() => { onNavigate('login'); onClose(); }}
          style={{
            width: '100%', padding: '11px 16px',
            background: 'rgba(201,168,76,0.07)',
            border: '1px solid rgba(201,168,76,0.22)',
            borderRadius: 10,
            color: 'rgba(201,168,76,0.90)',
            fontFamily: 'sans-serif', fontSize: 10,
            letterSpacing: '0.22em', textTransform: 'uppercase',
            cursor: 'pointer', textAlign: 'center',
          }}
          data-testid="button-nav-login"
        >
          🔐 Node Login
        </button>
      </div>
    );
  }

  const displayName = profile?.display_name || user?.displayName || user?.email?.split('@')[0] || 'Node';
  const sigil = profile?.role_sigil || '◈';
  const accessColor = (profile?.access_level ?? 0) >= 3 ? '#C9A84C' : '#00D4AA';

  return (
    <div style={{ borderTop: '1px solid rgba(255,255,255,0.05)' }}>
      {/* User identity */}
      <div style={{ padding: '14px 20px 10px', display: 'flex', alignItems: 'center', gap: 10 }}>
        <div style={{
          width: 32, height: 32, borderRadius: '50%',
          background: `${accessColor}12`,
          border: `1px solid ${accessColor}35`,
          display: 'flex', alignItems: 'center', justifyContent: 'center',
          flexShrink: 0,
        }}>
          <span style={{ color: accessColor, fontSize: 13 }}>{sigil}</span>
        </div>
        <div style={{ flex: 1, overflow: 'hidden' }}>
          <p style={{ fontFamily: 'sans-serif', fontSize: 11, color: accessColor, margin: '0 0 1px', fontWeight: 600, letterSpacing: '0.06em', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
            {displayName}
          </p>
          <p style={{ fontFamily: 'sans-serif', fontSize: 9, color: 'rgba(232,232,232,0.3)', margin: 0, letterSpacing: '0.08em', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
            {profile?.role ?? user?.email}
          </p>
        </div>
      </div>

      {/* Quick links */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 6, padding: '0 16px 10px' }}>
        {[
          { label: '☥ Nexus', view: 'nexus' as View },
          { label: '◉ SolSpire', view: 'solspire' as View },
        ].map(item => (
          <button key={item.view} onClick={() => { onNavigate(item.view); onClose(); }}
            style={{
              padding: '8px', background: 'rgba(255,255,255,0.03)',
              border: '1px solid rgba(255,255,255,0.07)', borderRadius: 8,
              color: 'rgba(232,232,232,0.45)', fontFamily: 'sans-serif',
              fontSize: 9, letterSpacing: '0.18em', textTransform: 'uppercase',
              cursor: 'pointer', transition: 'all 0.15s',
            }}
          >
            {item.label}
          </button>
        ))}
      </div>

      <div style={{ padding: '0 16px 14px' }}>
        <button
          onClick={() => { signOut(); onClose(); }}
          style={{
            width: '100%', padding: '9px',
            background: 'rgba(232,82,70,0.04)',
            border: '1px solid rgba(232,82,70,0.14)',
            borderRadius: 8,
            color: 'rgba(232,82,70,0.45)',
            fontFamily: 'sans-serif', fontSize: 9,
            letterSpacing: '0.18em', textTransform: 'uppercase',
            cursor: 'pointer', textAlign: 'center',
          }}
          data-testid="button-sign-out"
        >
          ← Sign Out
        </button>
      </div>
    </div>
  );
}

const ArkadiaNavigation: React.FC<NavProps> = ({ currentView, onNavigate, children }) => {
  const [drawerOpen, setDrawerOpen] = useState(false);
  const { isAuthenticated } = useAuth();

  const currentLabel = VIEW_LABEL[currentView] ?? 'Arkadia';

  const handleNavigate = (v: View) => {
    onNavigate(v);
    setDrawerOpen(false);
  };

  return (
    <div className="relative min-h-screen" style={{ backgroundColor: '#0C0D18' }}>

      {/* ── Shimmer line ── */}
      <div className="fixed top-0 left-0 w-full h-px z-50 overflow-hidden">
        <motion.div
          className="h-full w-1/2"
          style={{ background: 'linear-gradient(90deg, transparent, #C9A84C, transparent)' }}
          animate={{ x: ['-100%', '200%'] }}
          transition={{ duration: 4, repeat: Infinity, ease: 'linear' }}
        />
      </div>

      {/* ── Top bar ── */}
      <nav
        className="fixed top-0 left-0 w-full z-40"
        style={{
          display: 'flex', alignItems: 'center', justifyContent: 'space-between',
          padding: '0 16px',
          height: 52,
          backdropFilter: 'blur(24px)',
          WebkitBackdropFilter: 'blur(24px)',
          borderBottom: '1px solid rgba(201,168,76,0.18)',
          backgroundColor: 'rgba(12,13,24,0.94)',
        }}
      >
        {/* Logo — click to go home */}
        <button
          onClick={() => handleNavigate('home')}
          style={{
            display: 'flex', alignItems: 'center', gap: 8,
            background: 'none', border: 'none', cursor: 'pointer', padding: 0,
          }}
        >
          <motion.span animate={{ opacity: [0.4, 1, 0.4] }} transition={{ duration: 4, repeat: Infinity }}
            style={{ color: '#C9A84C', fontSize: 15 }}>☥</motion.span>
          <motion.span animate={{ opacity: [0.4, 1, 0.4] }} transition={{ duration: 4, repeat: Infinity, delay: 0.6 }}
            style={{ color: '#00D4AA', fontSize: 13 }}>⟐</motion.span>
          <span style={{ fontFamily: 'serif', fontSize: 10, letterSpacing: '0.38em', textTransform: 'uppercase', color: 'rgba(201,168,76,0.90)', marginLeft: 2 }}>
            ARKADIA
          </span>
        </button>

        {/* Current view label */}
        <AnimatePresence mode="wait">
          <motion.span
            key={currentView}
            initial={{ opacity: 0, y: 3 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -3 }}
            transition={{ duration: 0.25 }}
            style={{
              fontFamily: 'sans-serif', fontSize: 9, letterSpacing: '0.3em',
              textTransform: 'uppercase', color: 'rgba(232,232,232,0.62)',
              position: 'absolute', left: '50%', transform: 'translateX(-50%)',
              pointerEvents: 'none', whiteSpace: 'nowrap',
            }}
          >
            {currentLabel}
          </motion.span>
        </AnimatePresence>

        {/* Menu toggle */}
        <button
          onClick={() => setDrawerOpen(o => !o)}
          style={{
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            width: 36, height: 36,
            background: drawerOpen ? 'rgba(201,168,76,0.08)' : 'rgba(255,255,255,0.03)',
            border: `1px solid ${drawerOpen ? 'rgba(201,168,76,0.3)' : 'rgba(255,255,255,0.07)'}`,
            borderRadius: 9,
            cursor: 'pointer', transition: 'all 0.2s',
            flexShrink: 0,
          }}
          aria-label="Toggle navigation"
        >
          <div style={{ display: 'flex', flexDirection: 'column', gap: 4, alignItems: 'center' }}>
            <motion.div
              animate={{ rotate: drawerOpen ? 45 : 0, y: drawerOpen ? 6 : 0 }}
              transition={{ duration: 0.22 }}
              style={{ width: 14, height: 1, background: drawerOpen ? '#C9A84C' : 'rgba(232,232,232,0.55)', transformOrigin: 'center', borderRadius: 1 }}
            />
            <motion.div
              animate={{ opacity: drawerOpen ? 0 : 1 }}
              transition={{ duration: 0.15 }}
              style={{ width: 10, height: 1, background: 'rgba(232,232,232,0.35)', borderRadius: 1 }}
            />
            <motion.div
              animate={{ rotate: drawerOpen ? -45 : 0, y: drawerOpen ? -6 : 0 }}
              transition={{ duration: 0.22 }}
              style={{ width: 14, height: 1, background: drawerOpen ? '#C9A84C' : 'rgba(232,232,232,0.55)', transformOrigin: 'center', borderRadius: 1 }}
            />
          </div>
        </button>
      </nav>

      {/* ── Backdrop ── */}
      <AnimatePresence>
        {drawerOpen && (
          <motion.div
            key="backdrop"
            initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}
            transition={{ duration: 0.25 }}
            onClick={() => setDrawerOpen(false)}
            style={{
              position: 'fixed', inset: 0, zIndex: 45,
              background: 'rgba(2,3,8,0.65)',
              backdropFilter: 'blur(4px)',
              WebkitBackdropFilter: 'blur(4px)',
            }}
          />
        )}
      </AnimatePresence>

      {/* ── Drawer ── */}
      <AnimatePresence>
        {drawerOpen && (
          <motion.div
            key="drawer"
            initial={{ x: '-100%' }} animate={{ x: 0 }} exit={{ x: '-100%' }}
            transition={{ type: 'spring', stiffness: 340, damping: 38, mass: 0.9 }}
            style={{
              position: 'fixed', top: 0, left: 0, bottom: 0,
              width: 288,
              zIndex: 50,
              display: 'flex', flexDirection: 'column',
              background: 'rgba(9,10,22,0.97)',
              borderRight: '1px solid rgba(201,168,76,0.18)',
              backdropFilter: 'blur(32px)',
              WebkitBackdropFilter: 'blur(32px)',
              boxShadow: '4px 0 40px rgba(0,0,0,0.6), 1px 0 0 rgba(201,168,76,0.06)',
            }}
          >
            {/* Drawer header */}
            <div style={{
              display: 'flex', alignItems: 'center', justifyContent: 'space-between',
              padding: '0 18px',
              height: 52,
              borderBottom: '1px solid rgba(201,168,76,0.16)',
              flexShrink: 0,
            }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 7 }}>
                <motion.span animate={{ opacity: [0.4, 1, 0.4] }} transition={{ duration: 4, repeat: Infinity }}
                  style={{ color: '#C9A84C', fontSize: 14 }}>☥</motion.span>
                <span style={{ fontFamily: 'serif', fontSize: 9.5, letterSpacing: '0.38em', textTransform: 'uppercase', color: 'rgba(201,168,76,0.88)' }}>
                  ARKADIA
                </span>
              </div>
              <button
                onClick={() => setDrawerOpen(false)}
                style={{
                  background: 'none', border: 'none', cursor: 'pointer',
                  color: 'rgba(232,232,232,0.58)', fontSize: 16,
                  padding: '4px 6px', borderRadius: 6,
                  transition: 'color 0.15s',
                }}
              >
                ✕
              </button>
            </div>

            {/* Nav groups — scrollable */}
            <div style={{ flex: 1, overflowY: 'auto', padding: '12px 12px 8px' }}>
              {NAV_GROUPS.map(group => {
                const visibleItems = group.label === 'System' && !isAuthenticated
                  ? group.items.filter(i => i.view !== 'dashboard')
                  : group.items;

                return (
                  <div key={group.label} style={{ marginBottom: 18 }}>
                    {/* Group label */}
                    <p style={{
                      fontFamily: 'sans-serif', fontSize: 7.5,
                      letterSpacing: '0.4em', textTransform: 'uppercase',
                      color: 'rgba(201,168,76,0.55)',
                      margin: '0 8px 6px',
                    }}>
                      {group.label}
                    </p>

                    {/* Items */}
                    <div style={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
                      {visibleItems.map(item => {
                        const active = currentView === item.view;
                        return (
                          <button
                            key={item.view}
                            onClick={() => handleNavigate(item.view)}
                            style={{
                              display: 'flex', alignItems: 'center', gap: 11,
                              padding: '9px 10px',
                              background: active ? `${item.color}0d` : 'transparent',
                              border: active ? `1px solid ${item.color}28` : '1px solid transparent',
                              borderRadius: 10,
                              cursor: 'pointer', textAlign: 'left',
                              transition: 'all 0.16s',
                            }}
                          >
                            {/* Sigil */}
                            <motion.span
                              animate={active ? { opacity: [0.7, 1, 0.7] } : {}}
                              transition={{ duration: 3, repeat: Infinity }}
                              style={{
                                fontSize: 13, flexShrink: 0,
                                width: 22, textAlign: 'center',
                                color: active ? item.color : 'rgba(232,232,232,0.52)',
                              }}
                            >
                              {item.sigil}
                            </motion.span>

                            {/* Labels */}
                            <div style={{ flex: 1, overflow: 'hidden' }}>
                              <p style={{
                                fontFamily: 'sans-serif', fontSize: 11,
                                color: active ? item.color : 'rgba(232,232,232,0.82)',
                                margin: '0 0 1px', fontWeight: active ? 600 : 400,
                                letterSpacing: '0.04em',
                                whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis',
                              }}>
                                {item.label}
                              </p>
                              <p style={{
                                fontFamily: 'sans-serif', fontSize: 9,
                                color: active ? `${item.color}90` : 'rgba(232,232,232,0.50)',
                                margin: 0, letterSpacing: '0.04em',
                                whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis',
                              }}>
                                {item.sub}
                              </p>
                            </div>

                            {/* Active indicator */}
                            {active && (
                              <motion.div
                                layoutId="nav-active-dot"
                                style={{
                                  width: 4, height: 4, borderRadius: '50%',
                                  background: item.color, flexShrink: 0,
                                }}
                              />
                            )}
                          </button>
                        );
                      })}
                    </div>
                  </div>
                );
              })}

              {/* Authenticated Codex link */}
              {isAuthenticated && (
                <div style={{ marginBottom: 8 }}>
                  <button
                    onClick={() => handleNavigate('codex')}
                    style={{
                      display: 'flex', alignItems: 'center', gap: 11,
                      width: '100%', padding: '9px 10px',
                      background: currentView === 'codex' ? 'rgba(201,168,76,0.08)' : 'transparent',
                      border: currentView === 'codex' ? '1px solid rgba(201,168,76,0.28)' : '1px solid transparent',
                      borderRadius: 10, cursor: 'pointer', textAlign: 'left',
                      transition: 'all 0.16s',
                    }}
                  >
                    <span style={{ fontSize: 13, flexShrink: 0, width: 22, textAlign: 'center', color: currentView === 'codex' ? '#C9A84C' : 'rgba(232,232,232,0.52)' }}>✦</span>
                    <div style={{ flex: 1, overflow: 'hidden' }}>
                      <p style={{ fontFamily: 'sans-serif', fontSize: 11, color: currentView === 'codex' ? '#C9A84C' : 'rgba(232,232,232,0.6)', margin: '0 0 1px', fontWeight: currentView === 'codex' ? 600 : 400, letterSpacing: '0.04em' }}>
                        Personal Codex
                      </p>
                      <p style={{ fontFamily: 'sans-serif', fontSize: 9, color: 'rgba(232,232,232,0.50)', margin: 0, letterSpacing: '0.04em' }}>
                        90-day architecture · soul map
                      </p>
                    </div>
                  </button>
                </div>
              )}
            </div>

            {/* Footer: user section */}
            <UserSection onNavigate={onNavigate} onClose={() => setDrawerOpen(false)} />
          </motion.div>
        )}
      </AnimatePresence>

      {/* ── Page content ── */}
      <div style={{ paddingTop: 52 }}>
        {children}
      </div>
    </div>
  );
};

export default ArkadiaNavigation;
