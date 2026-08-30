import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useAuth } from '../contexts/AuthContext';

/**
 * WEAVER-SCI-BOUNDARY-01 - Product surface navigation (public/app entry).
 * Canonical OPERATOR global command shell is SCI (SpiralCommandInterface).
 * This drawer is product orientation, not architecture discovery authority.
 */

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

interface NavProps {
  currentView: View;
  onNavigate: (view: View) => void;
  children: React.ReactNode;
}

interface NavItem { label: string; view: View; sigil: string; sub: string; color: string }
interface NavGroup { label: string; items: NavItem[] }

const NAV_GROUPS: NavGroup[] = [
  {
    label: 'Field',
    items: [
      { label: 'Home',         view: 'home',      sigil: 'H', sub: 'Field entry point',     color: '#C9A84C' },
      { label: 'Oracle',       view: 'commune',   sigil: 'O', sub: 'ARKANA - Pattern intelligence', color: '#00D4AA' },
      { label: 'Living Gate',  view: 'gate',      sigil: '*', sub: 'Reset - IMS - AIC - 5-Minute', color: '#C9A84C' },
    ],
  },
  {
    label: 'Nexus',
    items: [
      { label: 'NovaNet',      view: 'novanet',   sigil: 'N', sub: 'The Nexus Hub - unified field', color: '#6A9FD8' },
    ],
  },
  {
    label: 'System',
    items: [
      { label: 'About',    view: 'about',     sigil: 'A', sub: 'Zahrune Nova - Lineage',   color: '#6A9FD8' },
      { label: 'SCI',      view: 'sci',       sigil: '#', sub: 'Spiral Command Interface - operator shell', color: '#00D4AA' },
      { label: 'Settings', view: 'settings',  sigil: 'S', sub: 'API keys - Configuration', color: '#C9A84C' },
    ],
  },
];

const VIEW_LABEL: Partial<Record<View, string>> = {
  home: 'Home', gate: 'Living Gate', commune: 'Oracle', reset: 'Field Reset', about: 'About',
  login: 'Node Login', codex: 'Personal Codex', dashboard: 'Dashboard',
  nexus: 'NovaNet', encyclopedia: 'Encyclopedia Galactica',
  'spiral-codex': 'Spiral Codex', loops: 'Open Loops', grove: 'Spiral Grove',
  larder: 'Living Larder', novanet: 'NovaNet', ims: 'IMS Archive',
  distribute: 'Distribute', offerings: 'Offerings', aic: 'AIC Diagnostic',
  pulse: 'Arkadian Pulse', settings: 'Settings', sci: 'SCI', solspire: 'SolSpire Console',
  'knowledge-os': 'Prism - Knowledge OS',
  reasomate: 'ReasoMate',
  'personal-echofeild': 'Personal Echofeild',
  'echofeild-matrix': 'Echofeild Crystal Matrix',
};

function UserSection({ onNavigate, onClose }: { onNavigate: (v: View) => void; onClose: () => void }) {
  const { user, profile, signOut, isAuthenticated } = useAuth();
  if (!isAuthenticated) {
    return (
      <div style={{ padding: '16px 20px', borderTop: '1px solid rgba(255,255,255,0.05)' }}>
        <button onClick={() => { onNavigate('login'); onClose(); }}
          style={{ width: '100%', padding: '11px 16px', background: 'rgba(201,168,76,0.07)', border: '1px solid rgba(201,168,76,0.22)', borderRadius: 10, color: 'rgba(201,168,76,0.90)', fontFamily: 'sans-serif', fontSize: 10, letterSpacing: '0.22em', textTransform: 'uppercase', cursor: 'pointer', textAlign: 'center' }}
          data-testid="button-nav-login">Node Login</button>
      </div>
    );
  }
  const displayName = profile?.display_name || user?.displayName || user?.email?.split('@')[0] || 'Node';
  const sigil = profile?.role_sigil || '*';
  const accessColor = (profile?.access_level ?? 0) >= 3 ? '#C9A84C' : '#00D4AA';
  return (
    <div style={{ borderTop: '1px solid rgba(255,255,255,0.05)' }}>
      <div style={{ padding: '14px 20px 10px', display: 'flex', alignItems: 'center', gap: 10 }}>
        <div style={{ width: 32, height: 32, borderRadius: '50%', background: `${accessColor}12`, border: `1px solid ${accessColor}35`, display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0 }}>
          <span style={{ color: accessColor, fontSize: 13 }}>{sigil}</span>
        </div>
        <div style={{ flex: 1, overflow: 'hidden' }}>
          <p style={{ fontFamily: 'sans-serif', fontSize: 11, color: accessColor, margin: '0 0 1px', fontWeight: 600 }}>{displayName}</p>
          <p style={{ fontFamily: 'sans-serif', fontSize: 9, color: 'rgba(232,232,232,0.3)', margin: 0 }}>{profile?.role ?? user?.email}</p>
        </div>
      </div>
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 6, padding: '0 16px 10px' }}>
        {[
          { label: 'SolSpire', view: 'solspire' as View },
          { label: 'ReasoMate', view: 'reasomate' as View },
          { label: 'Echo Field', view: 'solspire' as View },
          { label: 'Encyclopedia', view: 'encyclopedia' as View },
          { label: 'Offerings', view: 'offerings' as View },
        ].map(item => (
          <button key={item.label} onClick={() => { onNavigate(item.view); onClose(); }}
            style={{ padding: '8px', background: 'rgba(255,255,255,0.03)', border: '1px solid rgba(255,255,255,0.07)', borderRadius: 8, color: 'rgba(232,232,232,0.45)', fontFamily: 'sans-serif', fontSize: 9, letterSpacing: '0.18em', textTransform: 'uppercase', cursor: 'pointer' }}>
            {item.label}
          </button>
        ))}
      </div>
      <div style={{ padding: '0 16px 14px' }}>
        <button onClick={() => { signOut(); onClose(); }}
          style={{ width: '100%', padding: '9px', background: 'rgba(232,82,70,0.04)', border: '1px solid rgba(232,82,70,0.14)', borderRadius: 8, color: 'rgba(232,82,70,0.45)', fontFamily: 'sans-serif', fontSize: 9, letterSpacing: '0.18em', textTransform: 'uppercase', cursor: 'pointer' }}
          data-testid="button-sign-out">Sign Out</button>
      </div>
    </div>
  );
}

const ArkadiaNavigation: React.FC<NavProps> = ({ currentView, onNavigate, children }) => {
  const [drawerOpen, setDrawerOpen] = useState(false);
  const { isAuthenticated } = useAuth();
  const currentLabel = VIEW_LABEL[currentView] ?? 'Arkadia';
  const handleNavigate = (v: View) => { onNavigate(v); setDrawerOpen(false); };
  return (
    <div className="relative min-h-screen" style={{ backgroundColor: '#0C0D18' }}>
      <div className="fixed top-0 left-0 w-full h-px z-50 overflow-hidden">
        <motion.div className="h-full w-1/2" style={{ background: 'linear-gradient(90deg, transparent, #C9A84C, transparent)' }}
          animate={{ x: ['-100%', '200%'] }} transition={{ duration: 4, repeat: Infinity, ease: 'linear' }} />
      </div>
      <nav className="fixed top-0 left-0 w-full z-40" style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '0 16px', height: 52, backdropFilter: 'blur(24px)', WebkitBackdropFilter: 'blur(24px)', borderBottom: '1px solid rgba(201,168,76,0.18)', backgroundColor: 'rgba(12,13,24,0.94)' }}>
        <button onClick={() => handleNavigate('home')} style={{ display: 'flex', alignItems: 'center', gap: 8, background: 'none', border: 'none', cursor: 'pointer', padding: 0 }}>
          <span style={{ color: '#C9A84C', fontSize: 15 }}>*</span>
          <span style={{ fontFamily: 'serif', fontSize: 10, letterSpacing: '0.38em', textTransform: 'uppercase', color: 'rgba(201,168,76,0.90)' }}>ARKADIA</span>
        </button>
        <AnimatePresence mode="wait">
          <motion.span key={currentView} initial={{ opacity: 0, y: 3 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -3 }}
            style={{ fontFamily: 'sans-serif', fontSize: 9, letterSpacing: '0.3em', textTransform: 'uppercase', color: 'rgba(232,232,232,0.62)', position: 'absolute', left: '50%', transform: 'translateX(-50%)', pointerEvents: 'none' }}>
            {currentLabel}
          </motion.span>
        </AnimatePresence>
        <button onClick={() => setDrawerOpen(o => !o)} aria-label="Toggle navigation"
          style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', width: 36, height: 36, background: drawerOpen ? 'rgba(201,168,76,0.08)' : 'rgba(255,255,255,0.03)', border: `1px solid ${drawerOpen ? 'rgba(201,168,76,0.3)' : 'rgba(255,255,255,0.07)'}`, borderRadius: 9, cursor: 'pointer' }}>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
            <div style={{ width: 14, height: 1, background: 'rgba(232,232,232,0.55)' }} />
            <div style={{ width: 10, height: 1, background: 'rgba(232,232,232,0.35)' }} />
            <div style={{ width: 14, height: 1, background: 'rgba(232,232,232,0.55)' }} />
          </div>
        </button>
      </nav>
      <AnimatePresence>
        {drawerOpen && (
          <motion.div key="backdrop" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}
            onClick={() => setDrawerOpen(false)}
            style={{ position: 'fixed', inset: 0, zIndex: 45, background: 'rgba(2,3,8,0.65)' }} />
        )}
      </AnimatePresence>
      <AnimatePresence>
        {drawerOpen && (
          <motion.div key="drawer" initial={{ x: '-100%' }} animate={{ x: 0 }} exit={{ x: '-100%' }}
            transition={{ type: 'spring', stiffness: 340, damping: 38 }}
            style={{ position: 'fixed', top: 0, left: 0, bottom: 0, width: 288, zIndex: 50, display: 'flex', flexDirection: 'column', background: 'rgba(9,10,22,0.97)', borderRight: '1px solid rgba(201,168,76,0.18)' }}>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '0 18px', height: 52, borderBottom: '1px solid rgba(201,168,76,0.16)' }}>
              <span style={{ fontFamily: 'serif', fontSize: 9.5, letterSpacing: '0.38em', textTransform: 'uppercase', color: 'rgba(201,168,76,0.88)' }}>ARKADIA</span>
              <button onClick={() => setDrawerOpen(false)} style={{ background: 'none', border: 'none', cursor: 'pointer', color: 'rgba(232,232,232,0.58)', fontSize: 16 }}>X</button>
            </div>
            <div style={{ flex: 1, overflowY: 'auto', padding: '12px 12px 8px' }}>
              {NAV_GROUPS.map(group => {
                const visibleItems = group.label === 'System' && !isAuthenticated
                  ? group.items.filter(i => i.view !== 'dashboard')
                  : group.items;
                return (
                  <div key={group.label} style={{ marginBottom: 18 }}>
                    <p style={{ fontFamily: 'sans-serif', fontSize: 7.5, letterSpacing: '0.4em', textTransform: 'uppercase', color: 'rgba(201,168,76,0.55)', margin: '0 8px 6px' }}>{group.label}</p>
                    <div style={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
                      {visibleItems.map(item => {
                        const active = currentView === item.view;
                        return (
                          <button key={item.view} onClick={() => handleNavigate(item.view)}
                            style={{ display: 'flex', alignItems: 'center', gap: 11, padding: '9px 10px', background: active ? `${item.color}0d` : 'transparent', border: active ? `1px solid ${item.color}28` : '1px solid transparent', borderRadius: 10, cursor: 'pointer', textAlign: 'left' }}>
                            <span style={{ fontSize: 13, width: 22, textAlign: 'center', color: active ? item.color : 'rgba(232,232,232,0.52)' }}>{item.sigil}</span>
                            <div style={{ flex: 1, overflow: 'hidden' }}>
                              <p style={{ fontFamily: 'sans-serif', fontSize: 11, color: active ? item.color : 'rgba(232,232,232,0.82)', margin: '0 0 1px', fontWeight: active ? 600 : 400 }}>{item.label}</p>
                              <p style={{ fontFamily: 'sans-serif', fontSize: 9, color: active ? `${item.color}90` : 'rgba(232,232,232,0.50)', margin: 0 }}>{item.sub}</p>
                            </div>
                          </button>
                        );
                      })}
                    </div>
                  </div>
                );
              })}
            </div>
            <UserSection onNavigate={onNavigate} onClose={() => setDrawerOpen(false)} />
          </motion.div>
        )}
      </AnimatePresence>
      <div style={{ paddingTop: 52 }}>{children}</div>
    </div>
  );
};

export default ArkadiaNavigation;
