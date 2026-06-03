import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useAuth } from '../contexts/AuthContext';

type View =
  | 'home' | 'gate' | 'commune' | 'reset' | 'about' | 'login' | 'codex' | 'dashboard'
  | 'nexus'
  | 'encyclopedia'
  | 'spiral-codex'
  | 'loops'
  | 'grove'
  | 'larder'
  | 'novanet'
  | 'ims';

interface NavProps {
  currentView: View;
  onNavigate: (view: View) => void;
  children: React.ReactNode;
}

const navItems: { label: string; view: View }[] = [
  { label: 'Home',                  view: 'home' },
  { label: 'Gate',                  view: 'gate' },
  { label: 'Oracle',                view: 'commune' },
  { label: 'Reset',                 view: 'reset' },
  { label: 'Nexus',                 view: 'nexus' },
  { label: 'Encyclopedia',          view: 'encyclopedia' },
  { label: 'Spiral Codex',          view: 'spiral-codex' },
  { label: 'Open Loops',            view: 'loops' },
  { label: 'Spiral Grove',          view: 'grove' },
  { label: 'Living Larder',         view: 'larder' },
  { label: 'IMS Archive',           view: 'ims' },
  { label: 'NovaNet',               view: 'novanet' },
  { label: 'Dashboard',             view: 'dashboard' },
  { label: 'About',                 view: 'about' },
];

function UserIndicator({ onNavigate }: { onNavigate: (v: View) => void }) {
  const { user, profile, signOut, isAuthenticated } = useAuth();
  const [open, setOpen] = useState(false);

  if (!isAuthenticated) {
    return (
      <button
        onClick={() => onNavigate('login')}
        style={{
          padding: '5px 12px',
          background: 'rgba(201,168,76,0.07)',
          border: '1px solid rgba(201,168,76,0.22)',
          borderRadius: '6px',
          color: 'rgba(201,168,76,0.65)',
          fontFamily: 'sans-serif',
          fontSize: '9px',
          letterSpacing: '0.2em',
          textTransform: 'uppercase',
          cursor: 'pointer',
          transition: 'all 0.2s',
        }}
        data-testid="button-nav-login"
      >
        🔐 Node Login
      </button>
    );
  }

  const displayName = profile?.display_name || user?.displayName || user?.email?.split('@')[0] || 'Node';
  const sigil = profile?.role_sigil || '◈';
  const accessColor = (profile?.access_level ?? 0) >= 3 ? '#C9A84C' : '#00D4AA';

  return (
    <div style={{ position: 'relative' }}>
      <button
        onClick={() => setOpen(o => !o)}
        style={{
          display: 'flex', alignItems: 'center', gap: '7px',
          padding: '5px 12px',
          background: `${accessColor}09`,
          border: `1px solid ${accessColor}30`,
          borderRadius: '6px',
          color: accessColor,
          fontFamily: 'sans-serif', fontSize: '9px', letterSpacing: '0.18em', textTransform: 'uppercase',
          cursor: 'pointer', transition: 'all 0.2s',
        }}
        data-testid="button-user-menu"
      >
        <span>{sigil}</span>
        <span>{displayName}</span>
      </button>

      <AnimatePresence>
        {open && (
          <motion.div
            initial={{ opacity: 0, y: -6 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -6 }}
            transition={{ duration: 0.15 }}
            style={{
              position: 'absolute', top: 'calc(100% + 8px)', right: 0,
              background: 'rgba(10,10,15,0.97)',
              border: '1px solid rgba(255,255,255,0.08)',
              borderRadius: '10px',
              overflow: 'hidden',
              minWidth: '160px',
              zIndex: 100,
              backdropFilter: 'blur(20px)',
            }}
          >
            <div style={{ padding: '10px 14px', borderBottom: '1px solid rgba(255,255,255,0.05)' }}>
              <p style={{ fontFamily: 'sans-serif', fontSize: '9px', letterSpacing: '0.16em', textTransform: 'uppercase', color: accessColor, margin: '0 0 2px' }}>
                {profile?.role ?? 'Authenticated Node'}
              </p>
              <p style={{ fontFamily: 'sans-serif', fontSize: '10px', color: 'rgba(232,232,232,0.4)', margin: 0 }}>
                {user?.email}
              </p>
            </div>
            {[
              { label: '✦ Personal Codex', action: () => { onNavigate('codex'); setOpen(false); } },
              { label: '◈ Dashboard', action: () => { onNavigate('dashboard'); setOpen(false); } },
            ].map(item => (
              <button
                key={item.label}
                onClick={item.action}
                style={{
                  display: 'block', width: '100%', textAlign: 'left',
                  padding: '10px 14px',
                  background: 'none', border: 'none',
                  color: 'rgba(232,232,232,0.55)',
                  fontFamily: 'sans-serif', fontSize: '10px', letterSpacing: '0.14em', textTransform: 'uppercase',
                  cursor: 'pointer', transition: 'color 0.15s',
                }}
              >
                {item.label}
              </button>
            ))}
            <div style={{ borderTop: '1px solid rgba(255,255,255,0.05)' }}>
              <button
                onClick={() => { signOut(); setOpen(false); }}
                style={{
                  display: 'block', width: '100%', textAlign: 'left',
                  padding: '10px 14px',
                  background: 'none', border: 'none',
                  color: 'rgba(232,82,70,0.5)',
                  fontFamily: 'sans-serif', fontSize: '10px', letterSpacing: '0.14em', textTransform: 'uppercase',
                  cursor: 'pointer',
                }}
                data-testid="button-sign-out"
              >
                ← Sign Out
              </button>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}

const ArkadiaNavigation: React.FC<NavProps> = ({ currentView, onNavigate, children }) => {
  const [menuOpen, setMenuOpen] = useState(false);
  const { isAuthenticated, profile } = useAuth();

  return (
    <div className="relative min-h-screen" style={{ backgroundColor: '#0A0A0F' }}>
      {/* Top shimmer line */}
      <div className="fixed top-0 left-0 w-full h-px z-50 overflow-hidden">
        <motion.div
          className="h-full w-1/2"
          style={{ background: 'linear-gradient(90deg, transparent, #C9A84C, transparent)' }}
          animate={{ x: ['-100%', '200%'] }}
          transition={{ duration: 4, repeat: Infinity, ease: 'linear' }}
        />
      </div>

      {/* Desktop nav */}
      <nav
        className="fixed top-0 left-0 w-full z-40 hidden md:flex items-center justify-between px-8 py-4"
        style={{
          backdropFilter: 'blur(20px)',
          WebkitBackdropFilter: 'blur(20px)',
          borderBottom: '1px solid rgba(201,168,76,0.12)',
          backgroundColor: 'rgba(10,10,15,0.85)',
        }}
      >
        <div className="flex items-center gap-3">
          <motion.span animate={{ opacity: [0.3, 1, 0.3] }} transition={{ duration: 4, repeat: Infinity }}
            style={{ color: '#C9A84C', fontSize: '16px' }}>☥</motion.span>
          <motion.span animate={{ opacity: [0.3, 1, 0.3] }} transition={{ duration: 4, repeat: Infinity, delay: 0.5 }}
            style={{ color: '#00D4AA', fontSize: '14px' }}>⟐</motion.span>
          <motion.span animate={{ opacity: [0.3, 1, 0.3] }} transition={{ duration: 4, repeat: Infinity, delay: 1 }}
            style={{ color: '#C9A84C', fontSize: '12px' }}>✦</motion.span>
          <span className="ml-2" style={{ fontFamily: 'serif', fontSize: '10px', letterSpacing: '0.35em', textTransform: 'uppercase', color: 'rgba(201,168,76,0.7)' }}>
            ARKADIA
          </span>
        </div>

        <div className="flex items-center gap-6">
          {navItems.map((item) => {
            const active = currentView === item.view;
            return (
              <button key={item.view} onClick={() => onNavigate(item.view)}
                style={{ fontFamily: 'sans-serif', fontSize: '10px', letterSpacing: '0.25em', textTransform: 'uppercase', color: active ? '#00D4AA' : 'rgba(232,232,232,0.45)', background: 'none', border: 'none', cursor: 'pointer', paddingBottom: '4px', borderBottom: active ? '1px solid #00D4AA' : '1px solid transparent', transition: 'color 0.2s, border-color 0.2s' }}>
                {item.label}
              </button>
            );
          })}
          {isAuthenticated && profile && (
            <button
              onClick={() => onNavigate('codex')}
              style={{
                fontFamily: 'sans-serif', fontSize: '10px', letterSpacing: '0.25em', textTransform: 'uppercase',
                color: currentView === 'codex' ? '#C9A84C' : 'rgba(201,168,76,0.5)',
                background: 'none', border: 'none', cursor: 'pointer', paddingBottom: '4px',
                borderBottom: currentView === 'codex' ? '1px solid #C9A84C' : '1px solid transparent',
                transition: 'color 0.2s, border-color 0.2s',
              }}
            >
              Codex
            </button>
          )}
          <UserIndicator onNavigate={onNavigate} />
        </div>
      </nav>

      {/* Mobile top bar */}
      <nav
        className="fixed top-0 left-0 w-full z-40 flex md:hidden items-center justify-between px-5 py-4"
        style={{ backdropFilter: 'blur(20px)', WebkitBackdropFilter: 'blur(20px)', borderBottom: '1px solid rgba(201,168,76,0.12)', backgroundColor: 'rgba(10,10,15,0.85)' }}
      >
        <div className="flex items-center gap-2">
          <span style={{ color: '#C9A84C', fontSize: '14px' }}>☥</span>
          <span style={{ fontFamily: 'serif', fontSize: '9px', letterSpacing: '0.3em', textTransform: 'uppercase', color: 'rgba(201,168,76,0.7)' }}>
            ARKADIA
          </span>
        </div>
        <button onClick={() => setMenuOpen(!menuOpen)}
          style={{ background: 'none', border: 'none', cursor: 'pointer', color: 'rgba(232,232,232,0.6)', fontSize: '20px' }}>
          {menuOpen ? '✕' : '☰'}
        </button>
      </nav>

      {/* Mobile dropdown menu */}
      <AnimatePresence>
        {menuOpen && (
          <motion.div key="mobile-menu" initial={{ opacity: 0, y: -8 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -8 }} transition={{ duration: 0.2 }}
            className="fixed top-[57px] left-0 w-full z-40 md:hidden"
            style={{ backgroundColor: 'rgba(10,10,15,0.97)', borderBottom: '1px solid rgba(201,168,76,0.12)', backdropFilter: 'blur(20px)' }}>
            {navItems.map((item) => {
              const active = currentView === item.view;
              return (
                <button key={item.view} onClick={() => { onNavigate(item.view); setMenuOpen(false); }}
                  style={{ display: 'block', width: '100%', textAlign: 'left', padding: '14px 24px', fontFamily: 'sans-serif', fontSize: '11px', letterSpacing: '0.22em', textTransform: 'uppercase', color: active ? '#00D4AA' : 'rgba(232,232,232,0.55)', background: active ? 'rgba(0,212,170,0.05)' : 'none', border: 'none', borderLeft: active ? '2px solid #00D4AA' : '2px solid transparent', cursor: 'pointer' }}>
                  {item.label}
                </button>
              );
            })}
            {isAuthenticated && (
              <button onClick={() => { onNavigate('codex'); setMenuOpen(false); }}
                style={{ display: 'block', width: '100%', textAlign: 'left', padding: '14px 24px', fontFamily: 'sans-serif', fontSize: '11px', letterSpacing: '0.22em', textTransform: 'uppercase', color: currentView === 'codex' ? '#C9A84C' : 'rgba(201,168,76,0.55)', background: 'none', border: 'none', borderLeft: '2px solid transparent', cursor: 'pointer' }}>
                ✦ Codex
              </button>
            )}
            <div style={{ padding: '12px 24px', borderTop: '1px solid rgba(255,255,255,0.04)' }}>
              <UserIndicator onNavigate={(v) => { onNavigate(v); setMenuOpen(false); }} />
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Page content */}
      <div className="md:pt-[57px] pt-[57px]">
        {children}
      </div>
    </div>
  );
};

export default ArkadiaNavigation;
