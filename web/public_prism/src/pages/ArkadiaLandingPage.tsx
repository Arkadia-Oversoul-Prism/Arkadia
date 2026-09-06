import React from 'react';
import { motion } from 'framer-motion';

interface Props { onNavigate: (view: string) => void; authenticated?: boolean }

type Node = {
  key: string;
  label: string;
  sub: string;
  view: string;
  sigil: string;
  tone: string;
};

const nodes: Node[] = [
  { key: 'oracle', label: 'Oracle', sub: 'Think with Arkana', view: 'commune', sigil: 'O', tone: '#00D4AA' },
  { key: 'knowledge', label: 'Knowledge OS', sub: 'Remember · search · connect', view: 'knowledge-os', sigil: 'K', tone: '#6A9FD8' },
  { key: 'solspire', label: 'SolSpire', sub: 'Your private workspace', view: 'solspire', sigil: 'S', tone: '#C9A84C' },
  { key: 'sci', label: 'Spiral Command', sub: 'See the whole system', view: 'sci', sigil: '⌘', tone: '#B08DE8' },
];

function NodeCard({ node, onNavigate }: { node: Node; onNavigate: (view: string) => void }) {
  return (
    <motion.button
      type="button"
      whileHover={{ y: -2 }}
      whileTap={{ scale: 0.99 }}
      onClick={() => onNavigate(node.view)}
      style={{
        textAlign: 'left', width: '100%', padding: '16px', background: 'rgba(14,17,32,.72)',
        border: `1px solid ${node.tone}22`, borderRadius: 14, color: 'inherit', cursor: 'pointer',
        display: 'flex', alignItems: 'center', gap: 13,
      }}
    >
      <span style={{ width: 34, height: 34, display: 'grid', placeItems: 'center', borderRadius: 9,
        border: `1px solid ${node.tone}38`, color: node.tone, background: `${node.tone}09`,
        fontFamily: 'ui-monospace, monospace', fontSize: 12, flexShrink: 0 }}>{node.sigil}</span>
      <span style={{ flex: 1, minWidth: 0 }}>
        <span style={{ display: 'block', fontFamily: 'sans-serif', fontSize: 10, letterSpacing: '.18em',
          textTransform: 'uppercase', color: 'rgba(232,232,232,.82)', marginBottom: 4 }}>{node.label}</span>
        <span style={{ display: 'block', fontFamily: 'sans-serif', fontSize: 11, color: 'rgba(232,232,232,.36)' }}>{node.sub}</span>
      </span>
      <span style={{ color: `${node.tone}90`, fontSize: 15 }}>→</span>
    </motion.button>
  );
}

export default function ArkadiaLandingPage({ onNavigate, authenticated }: Props) {
  return (
    <main className="min-h-screen w-full relative overflow-hidden" data-testid="arkadia-home-landing">
      <div className="aurora-bg" />
      <div className="page-column relative z-10 pt-8 pb-20 flex flex-col">
        <header style={{ textAlign: 'center', padding: '8px 8px 30px' }}>
          <div style={{ display: 'inline-flex', alignItems: 'center', gap: 9, padding: '7px 12px', border: '1px solid rgba(0,212,170,.16)', borderRadius: 999, background: 'rgba(0,212,170,.035)', marginBottom: 20 }}>
            <span style={{ width: 6, height: 6, borderRadius: '50%', background: '#00D4AA', boxShadow: '0 0 12px rgba(0,212,170,.65)' }} />
            <span style={{ fontFamily: 'sans-serif', fontSize: 8, letterSpacing: '.28em', textTransform: 'uppercase', color: 'rgba(0,212,170,.62)' }}>ARKADIA · ONE SYSTEM</span>
          </div>
          <h1 style={{ fontFamily: 'serif', fontSize: 'clamp(44px,11vw,74px)', fontWeight: 400, letterSpacing: '.19em', color: '#C9A84C', margin: '0 0 14px', lineHeight: .95, paddingLeft: '.19em' }}>ARKADIA</h1>
          <p style={{ fontFamily: 'serif', fontSize: 'clamp(17px,4vw,21px)', lineHeight: 1.48, color: 'rgba(232,232,232,.76)', maxWidth: 610, margin: '0 auto' }}>
            Think with it. Remember through it. Build inside it. Command it.
          </p>
        </header>

        <section style={{ padding: '22px 20px', marginBottom: 14, background: 'linear-gradient(145deg,rgba(15,22,35,.94),rgba(10,13,24,.78))', border: '1px solid rgba(0,212,170,.18)', borderRadius: 17 }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 12, marginBottom: 12 }}>
            <div>
              <p style={{ fontFamily: 'sans-serif', fontSize: 8, letterSpacing: '.28em', textTransform: 'uppercase', color: 'rgba(0,212,170,.62)', margin: '0 0 5px' }}>The field</p>
              <h2 style={{ fontFamily: 'serif', fontWeight: 400, fontSize: 24, color: '#F0F0EE', margin: 0 }}>One system, four faces.</h2>
            </div>
            <span style={{ fontFamily: 'ui-monospace, monospace', fontSize: 9, color: 'rgba(232,232,232,.28)' }}>PRISM</span>
          </div>
          <p style={{ fontFamily: 'sans-serif', fontSize: 12, lineHeight: 1.75, color: 'rgba(232,232,232,.48)', margin: 0 }}>
            Oracle is the conversation. Knowledge OS is the memory and knowledge layer. SolSpire is the private workspace. Spiral Command is the operator view. They are not separate products: they are different surfaces over the same Arkadia system.
          </p>
        </section>

        <section style={{ display: 'grid', gap: 7, marginBottom: 16 }}>
          {nodes.map((node, i) => (
            <motion.div key={node.key} initial={{ opacity: 0, y: 6 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: i * .045 }}>
              <NodeCard node={node} onNavigate={onNavigate} />
            </motion.div>
          ))}
        </section>

        <section style={{ padding: '18px', marginBottom: 16, background: 'rgba(201,168,76,.025)', border: '1px solid rgba(201,168,76,.12)', borderRadius: 14 }}>
          <p style={{ fontFamily: 'sans-serif', fontSize: 8, letterSpacing: '.28em', textTransform: 'uppercase', color: 'rgba(201,168,76,.58)', margin: '0 0 12px' }}>A.I.S · your entry point</p>
          <h3 style={{ fontFamily: 'serif', fontWeight: 400, fontSize: 20, color: 'rgba(240,240,238,.88)', margin: '0 0 8px' }}>Discover what you can build here.</h3>
          <p style={{ fontFamily: 'sans-serif', fontSize: 11, lineHeight: 1.65, color: 'rgba(232,232,232,.38)', margin: '0 0 14px' }}>
            The capability diagnostic is an onboarding doorway into the same field, not a separate application.
          </p>
          <button type="button" data-testid="button-home-ais-diagnostic" onClick={() => onNavigate('gate')} style={{ width: '100%', padding: '13px 16px', background: 'rgba(0,212,170,.07)', border: '1px solid rgba(0,212,170,.34)', borderRadius: 10, color: '#00D4AA', fontFamily: 'sans-serif', fontSize: 9, letterSpacing: '.18em', textTransform: 'uppercase', cursor: 'pointer' }}>
            Open A.I.S capability onboarding →
          </button>
        </section>

        <div style={{ display: 'flex', gap: 8 }}>
          <button type="button" onClick={() => onNavigate(authenticated ? 'solspire' : 'login')} style={{ flex: 1, padding: 11, background: 'rgba(255,255,255,.018)', border: '1px solid rgba(201,168,76,.16)', borderRadius: 9, color: 'rgba(201,168,76,.7)', fontFamily: 'sans-serif', fontSize: 8, letterSpacing: '.15em', textTransform: 'uppercase', cursor: 'pointer' }}>
            {authenticated ? 'Open private field' : 'Enter private field'}
          </button>
          <button type="button" onClick={() => onNavigate('commune')} style={{ flex: 1, padding: 11, background: 'rgba(0,212,170,.025)', border: '1px solid rgba(0,212,170,.16)', borderRadius: 9, color: 'rgba(0,212,170,.62)', fontFamily: 'sans-serif', fontSize: 8, letterSpacing: '.15em', textTransform: 'uppercase', cursor: 'pointer' }}>
            Talk to Arkana
          </button>
        </div>
      </div>
    </main>
  );
}
