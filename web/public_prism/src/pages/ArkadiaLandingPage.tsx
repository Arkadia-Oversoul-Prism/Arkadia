import React from 'react';
import { motion } from 'framer-motion';

interface Props { onNavigate: (view: string) => void; authenticated?: boolean }

const portfolio = [
  ['01', 'Identity', 'Who am I?'],
  ['02', 'Capability Map', 'What can I do?'],
  ['03', 'Builds', 'What have I created?'],
  ['04', 'Evidence', 'Can I demonstrate it?'],
  ['05', 'Projects', 'Where have I applied it?'],
  ['06', 'Offer', 'What value can I provide?'],
  ['07', 'Credentials', 'What have I demonstrated?'],
  ['08', 'Growth Map', 'What should I learn next?'],
];

const doors = [
  ['Oracle', 'Think with Arkana · live conversation', 'commune'],
  ['NovaNet', 'Public knowledge · ReasoMate · offerings', 'novanet'],
  ['SolSpire', 'Private field · projects · knowledge', 'solspire'],
  ['Spiral Grove', 'A.I.S capability map · learn · build · prove', 'grove'],
];

export default function ArkadiaLandingPage({ onNavigate, authenticated }: Props) {
  return (
    <main className="min-h-screen w-full relative overflow-hidden" data-testid="arkadia-home-landing">
      <div className="aurora-bg" />
      <div className="page-column relative z-10 pt-8 pb-20 flex flex-col">
        <header style={{ textAlign: 'center', padding: '10px 8px 34px' }}>
          <div style={{ display: 'inline-flex', alignItems: 'center', gap: 9, padding: '7px 12px', border: '1px solid rgba(0,212,170,.16)', borderRadius: 999, background: 'rgba(0,212,170,.035)', marginBottom: 22 }}>
            <span style={{ width: 6, height: 6, borderRadius: '50%', background: '#00D4AA', boxShadow: '0 0 12px rgba(0,212,170,.65)' }} />
            <span style={{ fontFamily: 'sans-serif', fontSize: 8, letterSpacing: '.28em', textTransform: 'uppercase', color: 'rgba(0,212,170,.62)' }}>ARKADIA · AI OPERATING FIELD</span>
          </div>
          <h1 style={{ fontFamily: 'serif', fontSize: 'clamp(44px,11vw,74px)', fontWeight: 400, letterSpacing: '.19em', color: '#C9A84C', margin: '0 0 14px 0', lineHeight: .95, paddingLeft: '.19em' }}>ARKADIA</h1>
          <p style={{ fontFamily: 'serif', fontSize: 'clamp(17px,4vw,21px)', lineHeight: 1.48, color: 'rgba(232,232,232,.76)', maxWidth: 590, margin: '0 auto', textWrap: 'balance' as any }}>
            A place to think, remember, build,<br className="hidden sm:block" /> and become more capable with AI.
          </p>
        </header>

        <section style={{ position: 'relative', padding: '28px 24px 24px', marginBottom: 14, background: 'linear-gradient(145deg,rgba(15,22,35,.94),rgba(10,13,24,.78))', border: '1px solid rgba(0,212,170,.22)', borderRadius: 18, boxShadow: '0 20px 70px rgba(0,0,0,.22), inset 0 1px 0 rgba(255,255,255,.035)' }}>
          <div style={{ position: 'absolute', top: 0, left: 24, width: 74, height: 1, background: 'linear-gradient(90deg,#00D4AA,transparent)' }} />
          <p style={{ fontFamily: 'sans-serif', fontSize: 8, letterSpacing: '.3em', textTransform: 'uppercase', color: 'rgba(0,212,170,.68)', margin: '0 0 14px' }}>A.I.S · FUTURE BUILDER</p>
          <h2 style={{ fontFamily: 'serif', fontSize: 'clamp(28px,7vw,39px)', fontWeight: 400, lineHeight: 1.08, color: '#F0F0EE', letterSpacing: '.01em', margin: '0 0 14px', textWrap: 'balance' as any }}>Learn. Build. Prove. Launch.</h2>
          <p style={{ fontFamily: 'sans-serif', fontSize: 12, lineHeight: 1.8, color: 'rgba(232,232,232,.56)', maxWidth: 570, margin: '0 0 22px' }}>
            Discover what you can actually do. Turn scattered experience into a clear capability profile, then enter the Grove with a practical next step.
          </p>
          <button type="button" data-testid="button-home-ais-diagnostic" onClick={() => onNavigate('gate')} style={{ width: '100%', padding: '16px 18px', background: 'linear-gradient(135deg,rgba(0,212,170,.20),rgba(0,212,170,.07))', border: '1px solid rgba(0,212,170,.58)', borderRadius: 11, color: '#00D4AA', fontFamily: 'sans-serif', fontSize: 9, fontWeight: 600, letterSpacing: '.21em', textTransform: 'uppercase', cursor: 'pointer', boxShadow: '0 8px 30px rgba(0,212,170,.07)' }}>Build my free A.I.S capability profile <span style={{ fontSize: 13, marginLeft: 7 }}>→</span></button>
          <p style={{ fontFamily: 'sans-serif', fontSize: 8, letterSpacing: '.13em', textTransform: 'uppercase', textAlign: 'center', color: 'rgba(232,232,232,.27)', margin: '11px 0 0' }}>Free · takes a few minutes · no old-school form</p>
        </section>

        <section style={{ padding: '21px 20px 20px', marginBottom: 24, background: 'rgba(201,168,76,.028)', border: '1px solid rgba(201,168,76,.12)', borderRadius: 15 }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'baseline', gap: 12, marginBottom: 14 }}>
            <div>
              <p style={{ fontFamily: 'sans-serif', fontSize: 8, letterSpacing: '.27em', textTransform: 'uppercase', color: 'rgba(201,168,76,.6)', margin: '0 0 5px' }}>Your first Arkadia artifact</p>
              <h3 style={{ fontFamily: 'serif', fontWeight: 400, fontSize: 19, color: 'rgba(240,240,238,.86)', margin: 0 }}>A.I.S Capability Portfolio</h3>
            </div>
            <span style={{ fontFamily: 'sans-serif', fontSize: 8, letterSpacing: '.16em', color: 'rgba(201,168,76,.36)', whiteSpace: 'nowrap' }}>8 DIMENSIONS</span>
          </div>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2,minmax(0,1fr))', gap: 6 }}>
            {portfolio.map(([num, title, question]) => (
              <div key={title} style={{ minWidth: 0, padding: '10px 10px 9px', background: 'rgba(255,255,255,.018)', border: '1px solid rgba(255,255,255,.045)', borderRadius: 9 }}>
                <div style={{ display: 'flex', gap: 7, alignItems: 'baseline', marginBottom: 4 }}>
                  <span style={{ fontFamily: 'sans-serif', fontSize: 7, letterSpacing: '.12em', color: 'rgba(201,168,76,.38)' }}>{num}</span>
                  <span style={{ fontFamily: 'sans-serif', fontSize: 9, fontWeight: 500, letterSpacing: '.08em', color: 'rgba(232,232,232,.65)' }}>{title}</span>
                </div>
                <span style={{ fontFamily: 'sans-serif', fontSize: 8, lineHeight: 1.35, color: 'rgba(232,232,232,.29)' }}>{question}</span>
              </div>
            ))}
          </div>
        </section>

        <div style={{ display: 'flex', alignItems: 'center', gap: 12, margin: '0 2px 12px' }}>
          <span style={{ fontFamily: 'sans-serif', fontSize: 8, letterSpacing: '.28em', textTransform: 'uppercase', color: 'rgba(232,232,232,.28)' }}>Enter Arkadia</span>
          <span style={{ height: 1, flex: 1, background: 'linear-gradient(90deg,rgba(255,255,255,.08),transparent)' }} />
        </div>

        <div style={{ display: 'grid', gap: 7 }}>
          {doors.map(([label, sub, view], i) => (
            <motion.button key={label} type="button" initial={{ opacity: 0, y: 7 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: i * .045, duration: .4 }} onClick={() => onNavigate(view)} style={{ textAlign: 'left', padding: '14px 15px', background: 'rgba(14,17,32,.62)', border: '1px solid rgba(255,255,255,.065)', borderRadius: 11, color: 'inherit', cursor: 'pointer', display: 'flex', alignItems: 'center', gap: 13 }}>
              <span style={{ width: 25, height: 25, display: 'grid', placeItems: 'center', border: '1px solid rgba(255,255,255,.07)', borderRadius: 7, fontFamily: 'serif', fontSize: 12, color: 'rgba(201,168,76,.62)' }}>{i + 1}</span>
              <span style={{ flex: 1, minWidth: 0 }}><span style={{ display: 'block', fontFamily: 'sans-serif', fontSize: 9, fontWeight: 500, letterSpacing: '.18em', textTransform: 'uppercase', color: 'rgba(232,232,232,.7)', marginBottom: 4 }}>{label}</span><span style={{ display: 'block', fontFamily: 'sans-serif', fontSize: 10, lineHeight: 1.4, color: 'rgba(232,232,232,.34)' }}>{sub}</span></span>
              <span style={{ color: 'rgba(0,212,170,.34)', fontSize: 13 }}>→</span>
            </motion.button>
          ))}
        </div>

        <div style={{ display: 'flex', gap: 8, marginTop: 18 }}>
          <button type="button" onClick={() => onNavigate(authenticated ? 'solspire' : 'login')} style={{ flex: 1, padding: 12, background: 'rgba(255,255,255,.018)', border: '1px solid rgba(201,168,76,.16)', borderRadius: 9, color: 'rgba(201,168,76,.7)', fontFamily: 'sans-serif', fontSize: 8, letterSpacing: '.15em', textTransform: 'uppercase', cursor: 'pointer' }}>{authenticated ? 'Open private field' : 'Create account'}</button>
          <button type="button" onClick={() => onNavigate('commune')} style={{ flex: 1, padding: 12, background: 'rgba(0,212,170,.025)', border: '1px solid rgba(0,212,170,.16)', borderRadius: 9, color: 'rgba(0,212,170,.62)', fontFamily: 'sans-serif', fontSize: 8, letterSpacing: '.15em', textTransform: 'uppercase', cursor: 'pointer' }}>Talk to Arkana</button>
        </div>
      </div>
    </main>
  );
}
