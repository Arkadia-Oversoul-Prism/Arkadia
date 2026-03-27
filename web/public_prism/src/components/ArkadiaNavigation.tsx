import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';

type View = 'home' | 'gate' | 'commune' | 'vault' | 'reset' | 'sanctuary';

interface NavProps {
  currentView: View;
  onNavigate: (view: View) => void;
  children: React.ReactNode;
}

const navItems: { label: string; view: View }[] = [
  { label: 'Home', view: 'home' },
  { label: 'Gate', view: 'gate' },
  { label: 'Oracle', view: 'commune' },
  { label: 'Reset', view: 'reset' },
  { label: 'Vault', view: 'vault' },
  { label: 'Sanctuary', view: 'sanctuary' },
];

const ArkadiaNavigation: React.FC<NavProps> = ({ currentView, onNavigate, children }) => {
  const [menuOpen, setMenuOpen] = useState(false);

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
          <motion.span
            animate={{ opacity: [0.3, 1, 0.3] }}
            transition={{ duration: 4, repeat: Infinity }}
            style={{ color: '#C9A84C', fontSize: '16px' }}
          >
            ☥
          </motion.span>
          <motion.span
            animate={{ opacity: [0.3, 1, 0.3] }}
            transition={{ duration: 4, repeat: Infinity, delay: 0.5 }}
            style={{ color: '#00D4AA', fontSize: '14px' }}
          >
            ⟐
          </motion.span>
          <motion.span
            animate={{ opacity: [0.3, 1, 0.3] }}
            transition={{ duration: 4, repeat: Infinity, delay: 1 }}
            style={{ color: '#C9A84C', fontSize: '12px' }}
          >
            ✦
          </motion.span>
          <span
            className="ml-2"
            style={{
              fontFamily: 'serif',
              fontSize: '10px',
              letterSpacing: '0.35em',
              textTransform: 'uppercase',
              color: 'rgba(201,168,76,0.7)',
            }}
          >
            ARKADIA
          </span>
        </div>

        <div className="flex items-center gap-6">
          {navItems.map((item) => {
            const active = currentView === item.view;
            return (
              <button
                key={item.view}
                onClick={() => onNavigate(item.view)}
                style={{
                  fontFamily: 'sans-serif',
                  fontSize: '10px',
                  letterSpacing: '0.25em',
                  textTransform: 'uppercase',
                  color: active ? '#00D4AA' : 'rgba(232,232,232,0.45)',
                  background: 'none',
                  border: 'none',
                  cursor: 'pointer',
                  paddingBottom: '4px',
                  borderBottom: active ? '1px solid #00D4AA' : '1px solid transparent',
                  transition: 'color 0.2s, border-color 0.2s',
                }}
              >
                {item.label}
              </button>
            );
          })}
        </div>
      </nav>

      {/* Mobile top bar */}
      <nav
        className="fixed top-0 left-0 w-full z-40 flex md:hidden items-center justify-between px-5 py-4"
        style={{
          backdropFilter: 'blur(20px)',
          WebkitBackdropFilter: 'blur(20px)',
          borderBottom: '1px solid rgba(201,168,76,0.12)',
          backgroundColor: 'rgba(10,10,15,0.85)',
        }}
      >
        <div className="flex items-center gap-2">
          <span style={{ color: '#C9A84C', fontSize: '14px' }}>☥</span>
          <span
            style={{
              fontFamily: 'serif',
              fontSize: '9px',
              letterSpacing: '0.3em',
              textTransform: 'uppercase',
              color: 'rgba(201,168,76,0.7)',
            }}
          >
            ARKADIA
          </span>
        </div>
        <button
          onClick={() => setMenuOpen(!menuOpen)}
          style={{ background: 'none', border: 'none', cursor: 'pointer', color: 'rgba(232,232,232,0.6)', fontSize: '20px' }}
        >
          {menuOpen ? '✕' : '☰'}
        </button>
      </nav>

      {/* Mobile dropdown menu */}
      <AnimatePresence>
        {menuOpen && (
          <motion.div
            key="mobile-menu"
            initial={{ opacity: 0, y: -8 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -8 }}
            transition={{ duration: 0.2 }}
            className="fixed top-[57px] left-0 w-full z-40 md:hidden"
            style={{
              backgroundColor: 'rgba(10,10,15,0.97)',
              borderBottom: '1px solid rgba(201,168,76,0.12)',
              backdropFilter: 'blur(20px)',
            }}
          >
            {navItems.map((item) => {
              const active = currentView === item.view;
              return (
                <button
                  key={item.view}
                  onClick={() => { onNavigate(item.view); setMenuOpen(false); }}
                  style={{
                    display: 'block',
                    width: '100%',
                    textAlign: 'left',
                    padding: '14px 24px',
                    fontFamily: 'sans-serif',
                    fontSize: '11px',
                    letterSpacing: '0.22em',
                    textTransform: 'uppercase',
                    color: active ? '#00D4AA' : 'rgba(232,232,232,0.55)',
                    background: active ? 'rgba(0,212,170,0.05)' : 'none',
                    border: 'none',
                    borderLeft: active ? '2px solid #00D4AA' : '2px solid transparent',
                    cursor: 'pointer',
                  }}
                >
                  {item.label}
                </button>
              );
            })}
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
