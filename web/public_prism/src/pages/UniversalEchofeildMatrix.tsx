/**
 * Universal Echofeild Crystal Matrix
 *
 * Consolidation of the two knowledge surfaces into one coherent field:
 *   - Spiral Codex Live Feed  (public, canonical Scrolls)
 *   - Personal Echofeild      (auth-gated, personal projects + codex + private docs)
 *
 * This replaces the need for a standalone Spiral Codex page. The Crystal Matrix
 * is the unified entrance into the knowledge layer of Arkadia: public canonical
 * writings on one side, private living work on the other, one spine underneath.
 *
 * The two halves are rendered as tabs over the SAME data substrate (Codex
 * scrolls API + SolSpire projects + Knowledge OS graph). No duplicate brain,
 * no second memory — different windows onto one spine.
 */
import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import SpiralCodexFeed from './SpiralCodexFeed';
import PersonalEchofeild from './PersonalEchofeild';
import { useAuth } from '../contexts/AuthContext';

type View = 'home' | 'gate' | 'commune' | 'reset' | 'about' | 'login' | 'codex' | 'dashboard'
  | 'nexus' | 'encyclopedia' | 'spiral-codex' | 'loops' | 'grove' | 'larder' | 'novanet'
  | 'ims' | 'distribute' | 'offerings' | 'aic' | 'pulse' | 'settings' | 'solspire'
  | 'knowledge-os' | 'reasomate' | 'personal-echofeild' | 'echofeild-matrix';

type Mode = 'public' | 'personal';

export default function UniversalEchofeildMatrix({ onNavigate }: { onNavigate: (v: View) => void }) {
  const { isAuthenticated } = useAuth();
  const [mode, setMode] = useState<Mode>('public');

  return (
    <div style={{ minHeight: '60vh', background: 'transparent' }} data-testid="echofeild-matrix">
      {/* Matrix masthead */}
      <div style={{
        position: 'sticky', top: 0, zIndex: 10,
        background: 'rgba(6,7,13,0.88)', backdropFilter: 'blur(12px)',
        borderBottom: '1px solid rgba(255,255,255,0.05)',
      }}>
        <div style={{ maxWidth: 1100, margin: '0 auto', padding: '14px 20px', display: 'flex', alignItems: 'center', gap: 14, flexWrap: 'wrap' }}>
          <div style={{ flexShrink: 0 }}>
            <p style={{ fontFamily: 'ui-monospace, monospace', fontSize: 8.5, letterSpacing: '0.28em', textTransform: 'uppercase', color: 'rgba(176,141,232,0.5)', margin: 0 }}>⬡ Universal Echofeild</p>
            <h1 style={{ fontFamily: 'serif', fontSize: 19, fontWeight: 400, color: '#E8E8E8', margin: '2px 0 0', letterSpacing: '0.02em' }}>Crystal Matrix</h1>
          </div>

          <div style={{ flex: 1 }} />

          {/* Mode toggle — public scrolls ↔ personal echofeild */}
          <div style={{ display: 'flex', gap: 4, padding: 3, background: 'rgba(255,255,255,0.03)', borderRadius: 9, border: '1px solid rgba(255,255,255,0.05)' }}>
            {(['public', 'personal'] as const).map(m => {
              const active = mode === m;
              const locked = m === 'personal' && !isAuthenticated;
              const color = m === 'public' ? '#C9A84C' : '#00D4AA';
              return (
                <button key={m} onClick={() => setMode(m)}
                  style={{
                    padding: '8px 16px', borderRadius: 7, cursor: 'pointer',
                    background: active ? `${color}14` : 'transparent',
                    border: 'none',
                    fontFamily: 'ui-monospace, monospace', fontSize: 9,
                    letterSpacing: '0.18em', textTransform: 'uppercase',
                    color: active ? color : 'rgba(232,232,232,0.4)',
                    transition: 'all 0.15s', display: 'flex', alignItems: 'center', gap: 6,
                  }}>
                  <span>{m === 'public' ? '◈' : '✦'}</span>
                  {m === 'public' ? 'Spiral Codex Live' : 'Personal Echofeild'}
                  {locked && <span style={{ fontSize: 8, opacity: 0.6 }}>🔒</span>}
                </button>
              );
            })}
          </div>
        </div>
      </div>

      {/* Field body */}
      <AnimatePresence mode="wait">
        {mode === 'public' ? (
          <motion.div key="public" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} transition={{ duration: 0.25 }}>
            <SpiralCodexFeed onBack={() => onNavigate('home')} />
          </motion.div>
        ) : (
          <motion.div key="personal" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} transition={{ duration: 0.25 }}>
            <PersonalEchofeild onNavigate={onNavigate} />
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
