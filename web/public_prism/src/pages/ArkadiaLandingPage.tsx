import React from 'react';
import { motion } from 'framer-motion';

interface Props { onNavigate: (view: string) => void; authenticated?: boolean }

const doors = [
  ['Oracle', 'Think with Arkana · live conversation', 'commune'],
  ['NovaNet', 'Public knowledge · ReasoMate · offerings', 'novanet'],
  ['SolSpire', 'Your private field · projects · knowledge', 'solspire'],
  ['Spiral Grove', 'A.I.S capability map · learn · build · prove', 'grove'],
];

export default function ArkadiaLandingPage({ onNavigate, authenticated }: Props) {
  return <main className="min-h-screen w-full relative" data-testid="arkadia-home-landing">
    <div className="aurora-bg" />
    <div className="page-column relative z-10 pt-10 pb-20 flex flex-col">
      <div style={{ textAlign: 'center', marginBottom: 24 }}>
        <p style={{ fontFamily: 'sans-serif', fontSize: 9, letterSpacing: '.3em', textTransform: 'uppercase', color: 'rgba(0,212,170,.55)', margin: '0 0 12px' }}>ARKADIA · AI operating field</p>
        <h1 style={{ fontFamily: 'serif', fontSize: 'clamp(42px,9vw,68px)', letterSpacing: '.16em', color: '#C9A84C', margin: 0, lineHeight: 1 }}>ARKADIA</h1>
        <p style={{ fontFamily: 'serif', fontSize: 18, lineHeight: 1.55, color: 'rgba(232,232,232,.72)', maxWidth: 620, margin: '16px auto 0' }}>A place to think, remember, build, and become more capable with AI.</p>
      </div>

      <section style={{ padding: '22px 20px', marginBottom: 12, background: 'rgba(14,17,32,.78)', border: '1px solid rgba(0,212,170,.18)', borderRadius: 14 }}>
        <p style={{ fontFamily: 'sans-serif', fontSize: 9, letterSpacing: '.28em', textTransform: 'uppercase', color: 'rgba(0,212,170,.55)', margin: '0 0 8px' }}>A.I.S · Future Builder</p>
        <h2 style={{ fontFamily: 'serif', fontSize: 27, fontWeight: 400, color: '#E8E8E8', margin: '0 0 10px' }}>Learn. Build. Prove. Launch.</h2>
        <p style={{ fontFamily: 'sans-serif', fontSize: 12, lineHeight: 1.75, color: 'rgba(232,232,232,.48)', margin: '0 0 17px' }}>Discover what you can actually do, turn it into a capability portfolio, and enter the Spiral Grove with a clear next step. The first door is free.</p>
        <button type="button" data-testid="button-home-ais-diagnostic" onClick={() => onNavigate('gate')} style={{ width: '100%', padding: 15, background: 'linear-gradient(135deg,rgba(0,212,170,.18),rgba(0,212,170,.06))', border: '1px solid rgba(0,212,170,.55)', borderRadius: 11, color: '#00D4AA', fontFamily: 'sans-serif', fontSize: 10, letterSpacing: '.22em', textTransform: 'uppercase', cursor: 'pointer' }}>Build my free A.I.S capability profile →</button>
      </section>

      <section style={{ padding: '17px 18px', marginBottom: 22, background: 'rgba(201,168,76,.035)', border: '1px solid rgba(201,168,76,.13)', borderRadius: 12 }}>
        <p style={{ fontFamily: 'sans-serif', fontSize: 9, letterSpacing: '.2em', textTransform: 'uppercase', color: 'rgba(201,168,76,.55)', margin: '0 0 9px' }}>What your profile maps</p>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2,minmax(0,1fr))', gap: 7 }}>
          {['Identity','Capability Map','Builds','Evidence','Projects','Offer','Credentials','Growth Map'].map(item => <div key={item} style={{ padding: '10px 11px', background: 'rgba(255,255,255,.02)', borderRadius: 8, color: 'rgba(232,232,232,.56)', fontFamily: 'sans-serif', fontSize: 10 }}>{item}</div>)}
        </div>
      </section>

      <div style={{ display: 'grid', gap: 7 }}>
        {doors.map(([label, sub, view], i) => <motion.button key={label} type="button" initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: i * .05 }} onClick={() => onNavigate(view)} style={{ textAlign: 'left', padding: '14px 15px', background: 'rgba(14,17,32,.68)', border: '1px solid rgba(255,255,255,.07)', borderRadius: 10, color: 'inherit', cursor: 'pointer' }}><span style={{ display: 'block', fontFamily: 'sans-serif', fontSize: 10, letterSpacing: '.2em', textTransform: 'uppercase', color: '#00D4AA', marginBottom: 4 }}>{label}</span><span style={{ fontFamily: 'sans-serif', fontSize: 11, color: 'rgba(232,232,232,.38)' }}>{sub}</span><span style={{ float: 'right', color: 'rgba(232,232,232,.2)' }}>→</span></motion.button>)}
      </div>

      <div style={{ display: 'flex', gap: 8, marginTop: 20 }}>
        <button type="button" onClick={() => onNavigate(authenticated ? 'solspire' : 'login')} style={{ flex: 1, padding: 12, background: 'rgba(255,255,255,.02)', border: '1px solid rgba(201,168,76,.2)', borderRadius: 9, color: 'rgba(201,168,76,.75)', fontFamily: 'sans-serif', fontSize: 9, letterSpacing: '.16em', textTransform: 'uppercase', cursor: 'pointer' }}>{authenticated ? 'Open private field' : 'Create account'}</button>
        <button type="button" onClick={() => onNavigate('commune')} style={{ flex: 1, padding: 12, background: 'rgba(0,212,170,.04)', border: '1px solid rgba(0,212,170,.2)', borderRadius: 9, color: 'rgba(0,212,170,.7)', fontFamily: 'sans-serif', fontSize: 9, letterSpacing: '.16em', textTransform: 'uppercase', cursor: 'pointer' }}>Talk to Arkana</button>
      </div>
    </div>
  </main>;
}
