import React from 'react';
import { motion } from 'framer-motion';

interface Props { onNavigate: (view: string) => void; authenticated?: boolean }

type Surface = { key: string; label: string; eyebrow: string; body: string; view: string; sigil: string; tone: string };

const surfaces: Surface[] = [
  { key: 'oracle', label: 'Oracle', eyebrow: 'THINK', body: 'A living conversation with Arkana for reasoning, reflection, pattern finding and decisions.', view: 'commune', sigil: '✧', tone: '#00D4AA' },
  { key: 'knowledge', label: 'Knowledge OS', eyebrow: 'REMEMBER', body: 'Your knowledge layer for notes, sources, relationships, search and context that can move with you.', view: 'knowledge-os', sigil: '◈', tone: '#6A9FD8' },
  { key: 'solspire', label: 'SolSpire', eyebrow: 'BUILD', body: 'A private workspace where projects, files, tasks, codex and the living field meet.', view: 'solspire', sigil: '◉', tone: '#C9A84C' },
  { key: 'sci', label: 'Spiral Command Interface', eyebrow: 'COMMAND', body: 'The operator view for seeing the system, discovering its paths and moving through its architecture.', view: 'sci', sigil: '⌘', tone: '#B08DE8' },
];

const lenses = ['ReasoMate', 'Echo Field', 'Spiral Codex', 'Encyclopedia Galactica', 'Spiral Grove', 'Living Larder'];

function SurfaceCard({ item, index, onNavigate }: { item: Surface; index: number; onNavigate: (view: string) => void }) {
  return (
    <motion.button type="button" initial={{ opacity: 0, y: 18 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: .16 + index * .07, duration: .55 }} whileHover={{ y: -5 }} whileTap={{ scale: .995 }} onClick={() => onNavigate(item.view)}
      style={{ position: 'relative', overflow: 'hidden', minHeight: 188, textAlign: 'left', padding: 22, background: 'linear-gradient(145deg, rgba(18,22,38,.92), rgba(9,12,24,.82))', border: `1px solid ${item.tone}25`, borderRadius: 18, cursor: 'pointer', color: 'inherit' }}>
      <div style={{ position: 'absolute', width: 130, height: 130, right: -60, top: -60, borderRadius: '50%', background: `radial-gradient(circle, ${item.tone}14, transparent 68%)`, pointerEvents: 'none' }} />
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 22 }}>
        <span style={{ width: 38, height: 38, display: 'grid', placeItems: 'center', borderRadius: 11, border: `1px solid ${item.tone}40`, background: `${item.tone}09`, color: item.tone, fontSize: 16 }}>{item.sigil}</span>
        <span style={{ fontFamily: 'ui-monospace, monospace', fontSize: 8, letterSpacing: '.2em', color: `${item.tone}85` }}>{item.eyebrow}</span>
      </div>
      <h3 style={{ fontFamily: 'serif', fontWeight: 400, fontSize: 22, lineHeight: 1.15, color: 'rgba(245,245,242,.94)', margin: '0 0 9px' }}>{item.label}</h3>
      <p style={{ fontFamily: 'sans-serif', fontSize: 11.5, lineHeight: 1.7, color: 'rgba(232,232,232,.43)', margin: 0, maxWidth: 360 }}>{item.body}</p>
      <span style={{ position: 'absolute', right: 20, bottom: 18, color: `${item.tone}80`, fontSize: 15 }}>↗</span>
    </motion.button>
  );
}

export default function ArkadiaLandingPage({ onNavigate, authenticated }: Props) {
  return (
    <main className="min-h-screen w-full relative overflow-hidden" data-testid="arkadia-home-landing">
      <div className="aurora-bg" />
      <div style={{ position: 'absolute', inset: 0, pointerEvents: 'none', background: 'radial-gradient(circle at 50% 0%, rgba(106,159,216,.11), transparent 32%), radial-gradient(circle at 12% 42%, rgba(176,141,232,.07), transparent 24%), radial-gradient(circle at 90% 68%, rgba(0,212,170,.06), transparent 22%)' }} />

      <div className="page-column relative z-10 pt-10 pb-24">
        <header style={{ textAlign: 'center', padding: '20px 10px 68px' }}>
          <motion.div initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: .55 }} style={{ display: 'inline-flex', alignItems: 'center', gap: 9, padding: '7px 13px', border: '1px solid rgba(0,212,170,.18)', borderRadius: 999, background: 'rgba(0,212,170,.035)', marginBottom: 25 }}>
            <span style={{ width: 6, height: 6, borderRadius: '50%', background: '#00D4AA', boxShadow: '0 0 14px rgba(0,212,170,.7)' }} />
            <span style={{ fontFamily: 'sans-serif', fontSize: 8, letterSpacing: '.3em', textTransform: 'uppercase', color: 'rgba(0,212,170,.65)' }}>A PRIVATE INTELLIGENCE ENVIRONMENT</span>
          </motion.div>
          <motion.h1 initial={{ opacity: 0, scale: .97 }} animate={{ opacity: 1, scale: 1 }} transition={{ duration: .75 }} style={{ fontFamily: 'serif', fontSize: 'clamp(54px,13vw,94px)', fontWeight: 400, letterSpacing: '.16em', color: '#C9A84C', margin: '0 0 20px', lineHeight: .9, paddingLeft: '.16em', textShadow: '0 0 50px rgba(201,168,76,.08)' }}>ARKADIA</motion.h1>
          <p style={{ fontFamily: 'serif', fontSize: 'clamp(21px,4.5vw,30px)', lineHeight: 1.28, color: 'rgba(245,245,242,.9)', maxWidth: 780, margin: '0 auto 18px' }}>
            A place where your thinking, memory, knowledge and work become one continuous field.
          </p>
          <p style={{ fontFamily: 'sans-serif', fontSize: 12.5, lineHeight: 1.8, color: 'rgba(232,232,232,.42)', maxWidth: 650, margin: '0 auto 30px' }}>
            Arkadia is building a different kind of AI environment: not another chatbot, dashboard or collection of disconnected apps, but one system with many ways into it.
          </p>
          <div style={{ display: 'flex', justifyContent: 'center', gap: 9, flexWrap: 'wrap' }}>
            <button type="button" onClick={() => onNavigate(authenticated ? 'solspire' : 'login')} style={{ padding: '13px 20px', background: 'linear-gradient(135deg, rgba(201,168,76,.16), rgba(0,212,170,.07))', border: '1px solid rgba(201,168,76,.38)', borderRadius: 10, color: '#C9A84C', fontFamily: 'sans-serif', fontSize: 9, letterSpacing: '.2em', textTransform: 'uppercase', cursor: 'pointer' }}>{authenticated ? 'Enter your field' : 'Enter Arkadia'}</button>
            <button type="button" onClick={() => onNavigate('commune')} style={{ padding: '13px 20px', background: 'rgba(255,255,255,.018)', border: '1px solid rgba(255,255,255,.11)', borderRadius: 10, color: 'rgba(232,232,232,.62)', fontFamily: 'sans-serif', fontSize: 9, letterSpacing: '.2em', textTransform: 'uppercase', cursor: 'pointer' }}>Meet Arkana ↗</button>
          </div>
        </header>

        <section style={{ marginBottom: 58, padding: '20px 0 0' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 17 }}>
            <span style={{ fontFamily: 'ui-monospace, monospace', fontSize: 8, letterSpacing: '.26em', color: 'rgba(201,168,76,.55)' }}>01 / THE ARCHITECTURE</span>
            <div style={{ height: 1, flex: 1, background: 'rgba(201,168,76,.09)' }} />
          </div>
          <div style={{ padding: '27px 24px', background: 'linear-gradient(135deg, rgba(15,20,34,.88), rgba(9,12,22,.66))', border: '1px solid rgba(201,168,76,.14)', borderRadius: 19 }}>
            <h2 style={{ fontFamily: 'serif', fontWeight: 400, fontSize: 'clamp(27px,6vw,42px)', lineHeight: 1.1, color: 'rgba(245,245,242,.93)', margin: '0 0 15px', maxWidth: 700 }}>One intelligence. Four ways to work with it.</h2>
            <p style={{ fontFamily: 'sans-serif', fontSize: 12, lineHeight: 1.85, color: 'rgba(232,232,232,.42)', maxWidth: 720, margin: 0 }}>Conversation becomes context. Context becomes memory. Memory becomes knowledge. Knowledge becomes action. Arkadia keeps those layers connected instead of asking you to rebuild the same context in every application.</p>
          </div>
        </section>

        <section style={{ marginBottom: 62 }}>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(min(100%, 245px), 1fr))', gap: 9 }}>
            {surfaces.map((item, i) => <SurfaceCard key={item.key} item={item} index={i} onNavigate={onNavigate} />)}
          </div>
        </section>

        <section style={{ marginBottom: 62 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 17 }}><span style={{ fontFamily: 'ui-monospace, monospace', fontSize: 8, letterSpacing: '.26em', color: 'rgba(106,159,216,.55)' }}>02 / THE FIELD</span><div style={{ height: 1, flex: 1, background: 'rgba(106,159,216,.09)' }} /></div>
          <div style={{ padding: '25px 24px', border: '1px solid rgba(106,159,216,.13)', borderRadius: 18, background: 'rgba(10,15,27,.58)' }}>
            <p style={{ fontFamily: 'serif', fontSize: 21, lineHeight: 1.55, color: 'rgba(245,245,242,.75)', margin: '0 0 24px', maxWidth: 760 }}>The products are surfaces. The field underneath is the product.</p>
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: 7 }}>{lenses.map((lens, i) => <span key={lens} style={{ padding: '7px 10px', borderRadius: 8, border: '1px solid rgba(255,255,255,.06)', background: 'rgba(255,255,255,.018)', fontFamily: 'sans-serif', fontSize: 8.5, letterSpacing: '.13em', textTransform: 'uppercase', color: i % 2 ? 'rgba(176,141,232,.62)' : 'rgba(106,159,216,.58)' }}>{lens}</span>)}</div>
          </div>
        </section>

        <section style={{ marginBottom: 62 }}>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(min(100%, 300px), 1fr))', gap: 9 }}>
            <div style={{ padding: '25px 23px', border: '1px solid rgba(201,168,76,.12)', borderRadius: 17, background: 'rgba(201,168,76,.025)' }}>
              <span style={{ fontFamily: 'ui-monospace, monospace', fontSize: 8, letterSpacing: '.24em', color: 'rgba(201,168,76,.55)' }}>FOR PEOPLE WHO THINK</span>
              <h3 style={{ fontFamily: 'serif', fontWeight: 400, fontSize: 25, color: 'rgba(245,245,242,.88)', margin: '14px 0 9px' }}>Keep the thread.</h3>
              <p style={{ fontFamily: 'sans-serif', fontSize: 11.5, lineHeight: 1.75, color: 'rgba(232,232,232,.4)', margin: 0 }}>Your ideas should not disappear because a tab closed. Arkadia is designed around continuity, so thinking can accumulate instead of constantly starting over.</p>
            </div>
            <div style={{ padding: '25px 23px', border: '1px solid rgba(0,212,170,.12)', borderRadius: 17, background: 'rgba(0,212,170,.018)' }}>
              <span style={{ fontFamily: 'ui-monospace, monospace', fontSize: 8, letterSpacing: '.24em', color: 'rgba(0,212,170,.55)' }}>FOR BUILDERS</span>
              <h3 style={{ fontFamily: 'serif', fontWeight: 400, fontSize: 25, color: 'rgba(245,245,242,.88)', margin: '14px 0 9px' }}>Turn context into work.</h3>
              <p style={{ fontFamily: 'sans-serif', fontSize: 11.5, lineHeight: 1.75, color: 'rgba(232,232,232,.4)', margin: 0 }}>Move from a conversation to a project, from a source to knowledge, and from an intention to governed action without losing the context between them.</p>
            </div>
          </div>
        </section>

        <section style={{ textAlign: 'center', padding: '48px 20px 20px', borderTop: '1px solid rgba(255,255,255,.06)' }}>
          <span style={{ fontFamily: 'ui-monospace, monospace', fontSize: 8, letterSpacing: '.28em', color: 'rgba(0,212,170,.5)' }}>THE NEXT LAYER OF PERSONAL COMPUTING</span>
          <h2 style={{ fontFamily: 'serif', fontWeight: 400, fontSize: 'clamp(29px,7vw,48px)', lineHeight: 1.1, color: 'rgba(245,245,242,.9)', margin: '17px auto 13px', maxWidth: 650 }}>Stop switching between tools. Start building a field.</h2>
          <p style={{ fontFamily: 'sans-serif', fontSize: 11.5, lineHeight: 1.75, color: 'rgba(232,232,232,.35)', maxWidth: 560, margin: '0 auto 24px' }}>Arkadia is still being built. That is deliberate. The field grows with the people who enter it.</p>
          <button type="button" onClick={() => onNavigate(authenticated ? 'novanet' : 'login')} style={{ padding: '14px 24px', background: 'rgba(0,212,170,.06)', border: '1px solid rgba(0,212,170,.3)', borderRadius: 10, color: '#00D4AA', fontFamily: 'sans-serif', fontSize: 9, letterSpacing: '.22em', textTransform: 'uppercase', cursor: 'pointer' }}>{authenticated ? 'Open NovaNet' : 'Create your node →'}</button>
          <div style={{ marginTop: 28, fontFamily: 'ui-monospace, monospace', fontSize: 7.5, letterSpacing: '.18em', color: 'rgba(232,232,232,.18)' }}>ARKADIA · ONE SYSTEM · MANY SURFACES · ONE CONTINUOUS FIELD</div>
        </section>
      </div>
    </main>
  );
}
