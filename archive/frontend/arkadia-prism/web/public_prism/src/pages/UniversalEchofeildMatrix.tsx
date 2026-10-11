/**
 * Universal EchoField Crystal Matrix.
 *
 * Public Spiral Codex and authenticated Personal Codex · EchoField are two
 * views over their existing substrates. The personal side has one canonical
 * root: Master Profile / longitudinal identity spine.
 */
import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import SpiralCodexFeed from './SpiralCodexFeed';
import MasterProfile from './MasterProfile';
import { useAuth } from '../contexts/AuthContext';

type View = 'home' | 'gate' | 'commune' | 'reset' | 'about' | 'login' | 'codex' | 'dashboard' | 'nexus' | 'encyclopedia' | 'spiral-codex' | 'loops' | 'grove' | 'larder' | 'novanet' | 'ims' | 'distribute' | 'offerings' | 'aic' | 'pulse' | 'settings' | 'solspire' | 'knowledge-os' | 'reasomate' | 'personal-echofeild' | 'echofeild-matrix';
type Mode = 'public' | 'personal';

export default function UniversalEchofeildMatrix({ onNavigate }: { onNavigate: (v: View) => void }) {
  const { isAuthenticated } = useAuth();
  const [mode, setMode] = useState<Mode>('personal');
  return <div style={{ minHeight: '60vh', background: 'transparent' }} data-testid="echofeild-matrix">
    <div style={{ position: 'sticky', top: 0, zIndex: 10, background: 'rgba(6,7,13,.88)', backdropFilter: 'blur(12px)', borderBottom: '1px solid rgba(255,255,255,.05)' }}>
      <div style={{ maxWidth: 1100, margin: '0 auto', padding: '14px 20px', display: 'flex', alignItems: 'center', gap: 14, flexWrap: 'wrap' }}>
        <div><p style={{ fontFamily: 'monospace', fontSize: 8.5, letterSpacing: '.28em', textTransform: 'uppercase', color: 'rgba(176,141,232,.5)', margin: 0 }}>⬡ Personal Field</p><h1 style={{ fontFamily: 'serif', fontSize: 19, fontWeight: 400, color: '#E8E8E8', margin: '2px 0 0' }}>Codex · EchoField</h1></div>
        <div style={{ flex: 1 }} />
        <div style={{ display: 'flex', gap: 4, padding: 3, background: 'rgba(255,255,255,.03)', borderRadius: 9, border: '1px solid rgba(255,255,255,.05)' }}>
          <button onClick={() => setMode('public')} style={{ padding: '8px 16px', borderRadius: 7, cursor: 'pointer', background: mode === 'public' ? 'rgba(201,168,76,.08)' : 'transparent', border: 'none', fontFamily: 'monospace', fontSize: 9, letterSpacing: '.15em', textTransform: 'uppercase', color: mode === 'public' ? '#C9A84C' : 'rgba(232,232,232,.4)' }}>◈ Spiral Codex Live</button>
          <button onClick={() => isAuthenticated && setMode('personal')} disabled={!isAuthenticated} style={{ padding: '8px 16px', borderRadius: 7, cursor: isAuthenticated ? 'pointer' : 'not-allowed', background: mode === 'personal' ? 'rgba(0,212,170,.1)' : 'transparent', border: 'none', fontFamily: 'monospace', fontSize: 9, letterSpacing: '.15em', textTransform: 'uppercase', color: mode === 'personal' ? '#00D4AA' : 'rgba(232,232,232,.4)', opacity: isAuthenticated ? 1 : .5 }}>✦ Personal Codex · EchoField</button>
        </div>
      </div>
    </div>
    <AnimatePresence mode="wait">
      {mode === 'public' ? <motion.div key="public" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} transition={{ duration: .25 }}><SpiralCodexFeed onBack={() => onNavigate('home')} /></motion.div> : <motion.div key="personal" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} transition={{ duration: .25 }}><MasterProfile /></motion.div>}
    </AnimatePresence>
  </div>;
}
