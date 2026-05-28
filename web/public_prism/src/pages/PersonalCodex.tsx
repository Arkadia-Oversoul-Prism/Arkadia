import { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';

const API_BASE = (import.meta.env.VITE_API_BASE_URL ?? '').replace(/\/$/, '');

interface Loop   { id: string; loop: string; status: string; priority: number }
interface Phase  { name: string; days: string; focus: string; anchor: string }
interface Scroll { id: string; label: string; category: string; description: string; source: string; preview?: string }
interface ColNode { display_name: string; role: string; role_sigil: string; ims_id?: string; status: string; access_level: number }
interface Codex  {
  display_name: string; ims_id: string; role: string; soul_function: string;
  field_frequency?: string;
  name_decode?:     Record<string, string>;
  shadow_states?:   string[];
  soul_gifts?:      string[];
  open_loops?:      Loop[];
  access_tools?:    string[];
  '90_day_architecture'?: Record<string, Phase>;
  [k: string]: unknown;
}
interface NodeProfile { display_name: string; role: string; role_sigil: string; ims_id?: string; access_level: number }
interface PersonalData { node: NodeProfile; codex: Codex; collective: ColNode[]; system: { tools_count: number } }

const CAT_COLOR: Record<string, string> = {
  NEURAL_SPINE: '#00D4AA',
  CREATIVE_OS:  '#C9A84C',
  COLLECTIVE:   '#6A9FD8',
  GOVERNANCE:   '#E85246',
};
const CAT_LINK: Record<string, string> = {
  NEURAL_SPINE: 'Soul Function',
  CREATIVE_OS:  'Soul Gifts',
  COLLECTIVE:   'Open Loops',
  GOVERNANCE:   '90-Day Arc',
};
const CAT_ORDER = ['NEURAL_SPINE', 'CREATIVE_OS', 'COLLECTIVE', 'GOVERNANCE'];

// ── sub-components ────────────────────────────────────────────────────────────

function Label({ children, color = 'rgba(232,232,232,0.28)' }: { children: React.ReactNode; color?: string }) {
  return (
    <p style={{ fontFamily: 'monospace', fontSize: '8px', letterSpacing: '0.3em', textTransform: 'uppercase',
                color, margin: '0 0 9px' }}>
      {children}
    </p>
  );
}

function SectionBox({ children, accent = 'rgba(255,255,255,0.055)', style }: {
  children: React.ReactNode; accent?: string; style?: React.CSSProperties
}) {
  return (
    <div style={{ border: `1px solid ${accent}`, borderRadius: '13px', overflow: 'hidden', marginBottom: '22px', ...style }}>
      {children}
    </div>
  );
}

function SectionHead({ label, color = '#00D4AA', right }: { label: string; color?: string; right?: React.ReactNode }) {
  return (
    <div style={{ padding: '10px 18px', background: `${color}0A`, borderBottom: `1px solid ${color}18`,
                  display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
      <span style={{ fontFamily: 'monospace', fontSize: '9px', letterSpacing: '0.28em',
                     textTransform: 'uppercase', color: `${color}95` }}>
        {label}
      </span>
      {right}
    </div>
  );
}

// ── main component ────────────────────────────────────────────────────────────

export default function PersonalCodex() {
  const [data,    setData]    = useState<PersonalData | null>(null);
  const [scrolls, setScrolls] = useState<Scroll[]>([]);
  const [loading, setLoading] = useState(true);
  const [error,   setError]   = useState<string | null>(null);
  const [activeCat, setActiveCat] = useState<string | null>(null);

  useEffect(() => {
    Promise.all([
      fetch(`${API_BASE}/api/codex/personal`).then(r => { if (!r.ok) throw new Error(`${r.status} from /api/codex/personal`); return r.json(); }),
      fetch(`${API_BASE}/api/codex`).then(r => r.json()),
    ]).then(([personal, corpus]) => {
      setData(personal);
      const raw = corpus.scrolls || {};
      setScrolls(typeof raw === 'object' && !Array.isArray(raw)
        ? Object.values(raw) as Scroll[]
        : (raw as Scroll[]));
      setLoading(false);
    }).catch(e => { setError(String(e)); setLoading(false); });
  }, []);

  if (loading) {
    return (
      <div style={{ padding: '90px 20px', textAlign: 'center' }}>
        <motion.div animate={{ opacity: [0.2, 0.8, 0.2] }} transition={{ repeat: Infinity, duration: 2.2 }}>
          <p style={{ fontFamily: 'monospace', fontSize: '9px', letterSpacing: '0.35em',
                      textTransform: 'uppercase', color: '#00D4AA' }}>
            EchoField Recursion Initialising…
          </p>
        </motion.div>
      </div>
    );
  }

  if (error || !data) {
    return (
      <div style={{ padding: '60px 20px', textAlign: 'center', maxWidth: '480px', margin: '0 auto' }}>
        <motion.div initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }}>
          <p style={{ fontSize: '24px', marginBottom: '14px' }}>⟐</p>
          <h2 style={{ fontFamily: 'serif', fontSize: '20px', color: '#C9A84C', marginBottom: '10px' }}>
            Neural Spine Offline
          </h2>
          <p style={{ fontFamily: 'sans-serif', fontSize: '11px', color: 'rgba(232,232,232,0.35)',
                      lineHeight: '1.8', marginBottom: '0' }}>
            {error || 'Could not reach the Oracle Temple. Ensure the backend is running.'}
          </p>
        </motion.div>
      </div>
    );
  }

  const { node, codex, collective } = data;
  const freq  = codex.field_frequency || '117 Hz';
  const tools = codex.access_tools || [];
  const loops = (codex.open_loops || []).sort((a, b) => (a.priority ?? 9) - (b.priority ?? 9));
  const arch  = codex['90_day_architecture'] as Record<string, Phase> | undefined;

  const scrollsByCategory: Record<string, Scroll[]> = {};
  for (const s of scrolls) {
    const c = s.category || 'OTHER';
    if (!scrollsByCategory[c]) scrollsByCategory[c] = [];
    scrollsByCategory[c].push(s);
  }
  const cats = CAT_ORDER.filter(c => scrollsByCategory[c]);

  return (
    <div style={{ maxWidth: '760px', margin: '0 auto', paddingBottom: '90px' }}>

      {/* ── SOVEREIGN IDENTITY HEADER ─────────────────────────────────────── */}
      <motion.div
        initial={{ opacity: 0, y: -10 }} animate={{ opacity: 1, y: 0 }}
        style={{ marginBottom: '24px', padding: '20px 24px',
                 background: 'rgba(201,168,76,0.04)', border: '1px solid rgba(201,168,76,0.16)',
                 borderRadius: '14px' }}
      >
        <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between',
                      flexWrap: 'wrap', gap: '12px' }}>
          <div>
            <p style={{ fontFamily: 'monospace', fontSize: '8px', letterSpacing: '0.32em',
                        textTransform: 'uppercase', color: 'rgba(201,168,76,0.45)', marginBottom: '6px' }}>
              Personal Codex · {codex.ims_id} · EchoField Recursion Neural Spine
            </p>
            <h1 style={{ fontFamily: 'serif', fontSize: '32px', color: '#C9A84C',
                         margin: '0 0 4px', letterSpacing: '0.04em' }}>
              {node.role_sigil} {codex.display_name}
            </h1>
            <p style={{ fontFamily: 'sans-serif', fontSize: '11px',
                        color: 'rgba(232,232,232,0.4)', margin: 0 }}>
              {codex.role}
            </p>
          </div>
          <div style={{ textAlign: 'right', flexShrink: 0 }}>
            <motion.div
              animate={{ opacity: [0.45, 1, 0.45] }} transition={{ repeat: Infinity, duration: 2.2 }}
              style={{ display: 'inline-flex', alignItems: 'center', gap: '7px',
                       padding: '5px 12px', background: 'rgba(0,212,170,0.07)',
                       border: '1px solid rgba(0,212,170,0.22)', borderRadius: '20px' }}
            >
              <span style={{ width: '5px', height: '5px', borderRadius: '50%',
                             background: '#00D4AA', display: 'inline-block' }} />
              <span style={{ fontFamily: 'monospace', fontSize: '10px',
                             letterSpacing: '0.18em', color: 'rgba(0,212,170,0.85)' }}>
                {freq}
              </span>
            </motion.div>
            <p style={{ fontFamily: 'monospace', fontSize: '8px', letterSpacing: '0.2em',
                        color: 'rgba(232,232,232,0.22)', marginTop: '8px' }}>
              {scrolls.length} SCROLLS · {tools.length} TOOLS · {loops.length} LOOPS
            </p>
          </div>
        </div>
      </motion.div>

      {/* ── DIAMOND COMPRESSION — LOSSLESS IDENTITY MATRIX ───────────────── */}
      <motion.div initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.07 }}>
        <SectionBox accent="rgba(201,168,76,0.14)">
          <SectionHead label="◈  Diamond Compression — Lossless Identity Matrix" color="#C9A84C" />

          {/* Soul Function */}
          <div style={{ padding: '18px 20px', borderBottom: '1px solid rgba(255,255,255,0.05)' }}>
            <Label color="rgba(201,168,76,0.45)">Soul Function</Label>
            <p style={{ fontFamily: 'serif', fontSize: '14px', color: 'rgba(232,232,232,0.78)',
                        lineHeight: '1.85', margin: 0 }}>
              {codex.soul_function}
            </p>
          </div>

          {/* Name Decode — 2 col */}
          {codex.name_decode && Object.keys(codex.name_decode).length > 0 && (
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr',
                          borderBottom: '1px solid rgba(255,255,255,0.05)' }}>
              {Object.entries(codex.name_decode).map(([name, meaning], i) => (
                <div key={name} style={{
                  padding: '16px 20px',
                  borderRight: i === 0 ? '1px solid rgba(255,255,255,0.05)' : undefined,
                }}>
                  <p style={{ fontFamily: 'monospace', fontSize: '11px', letterSpacing: '0.22em',
                               textTransform: 'uppercase', color: '#C9A84C', marginBottom: '8px' }}>
                    {name}
                  </p>
                  <p style={{ fontFamily: 'sans-serif', fontSize: '12px',
                               color: 'rgba(232,232,232,0.5)', lineHeight: '1.65', margin: 0 }}>
                    {meaning}
                  </p>
                </div>
              ))}
            </div>
          )}

          {/* Shadow States + Soul Gifts — side by side */}
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr' }}>
            <div style={{ padding: '16px 20px', borderRight: '1px solid rgba(255,255,255,0.05)' }}>
              <Label color="rgba(232,82,70,0.5)">Shadow States</Label>
              {(codex.shadow_states || []).map((s, i) => (
                <div key={i} style={{ display: 'flex', gap: '8px', marginBottom: '9px' }}>
                  <span style={{ color: 'rgba(232,82,70,0.4)', flexShrink: 0,
                                 fontSize: '10px', marginTop: '2px' }}>◆</span>
                  <p style={{ fontFamily: 'sans-serif', fontSize: '11px',
                               color: 'rgba(232,232,232,0.45)', lineHeight: '1.55', margin: 0 }}>
                    {s}
                  </p>
                </div>
              ))}
            </div>
            <div style={{ padding: '16px 20px' }}>
              <Label color="rgba(0,212,170,0.5)">Soul Gifts</Label>
              {(codex.soul_gifts || []).map((g, i) => (
                <div key={i} style={{ display: 'flex', gap: '8px', marginBottom: '9px' }}>
                  <span style={{ color: 'rgba(0,212,170,0.4)', flexShrink: 0,
                                 fontSize: '10px', marginTop: '2px' }}>✦</span>
                  <p style={{ fontFamily: 'sans-serif', fontSize: '11px',
                               color: 'rgba(232,232,232,0.52)', lineHeight: '1.55', margin: 0 }}>
                    {g}
                  </p>
                </div>
              ))}
            </div>
          </div>
        </SectionBox>
      </motion.div>

      {/* ── ECHOFIELD RECURSION NEURAL SPINE ─────────────────────────────── */}
      <motion.div initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.14 }}>
        <SectionBox accent="rgba(0,212,170,0.14)">
          <SectionHead
            label="⟐  EchoField Recursion Neural Spine — Primary Causal Lattice"
            color="#00D4AA"
            right={
              <span style={{ fontFamily: 'monospace', fontSize: '8px',
                             letterSpacing: '0.18em', color: 'rgba(0,212,170,0.4)' }}>
                {scrolls.length} SCROLLS INDEXED
              </span>
            }
          />
          <div style={{ padding: '22px 20px' }}>

            {/* Root Node */}
            <div style={{ display: 'flex', justifyContent: 'center', marginBottom: '0' }}>
              <div style={{ padding: '11px 24px', background: 'rgba(201,168,76,0.08)',
                            border: '1px solid rgba(201,168,76,0.28)', borderRadius: '9px',
                            textAlign: 'center' }}>
                <p style={{ fontFamily: 'serif', fontSize: '17px', color: '#C9A84C', margin: '0 0 3px' }}>
                  {node.role_sigil} {codex.display_name}
                </p>
                <p style={{ fontFamily: 'monospace', fontSize: '7px', letterSpacing: '0.25em',
                             textTransform: 'uppercase', color: 'rgba(201,168,76,0.4)', margin: 0 }}>
                  Sovereign Root · {freq} · Access Level 3
                </p>
              </div>
            </div>

            {/* Vertical connector */}
            <div style={{ display: 'flex', justifyContent: 'center' }}>
              <div style={{ width: '1px', height: '22px',
                            background: 'linear-gradient(to bottom, rgba(201,168,76,0.5), rgba(0,212,170,0.5))' }} />
            </div>

            {/* Horizontal rail + category branch nodes */}
            <div style={{ position: 'relative', paddingTop: '22px' }}>
              <div style={{ position: 'absolute', top: 0, left: '12.5%', right: '12.5%',
                            height: '1px', background: 'rgba(0,212,170,0.18)' }} />

              <div style={{ display: 'grid', gridTemplateColumns: `repeat(${cats.length}, 1fr)`, gap: '8px' }}>
                {cats.map((cat, ci) => {
                  const color = CAT_COLOR[cat] || '#888';
                  const link  = CAT_LINK[cat]  || cat;
                  const count = (scrollsByCategory[cat] || []).length;
                  const isOn  = activeCat === cat;
                  return (
                    <div key={cat}>
                      {/* connector dot */}
                      <div style={{ display: 'flex', justifyContent: 'center', marginBottom: '10px' }}>
                        <motion.div
                          animate={{ opacity: [0.35, 1, 0.35], scale: [0.9, 1.1, 0.9] }}
                          transition={{ repeat: Infinity, duration: 2.8, delay: ci * 0.4 }}
                          style={{ width: '7px', height: '7px', borderRadius: '50%', background: color }}
                        />
                      </div>
                      <button
                        onClick={() => setActiveCat(isOn ? null : cat)}
                        style={{
                          width: '100%', padding: '12px 8px', cursor: 'pointer',
                          background: isOn ? `${color}14` : 'rgba(255,255,255,0.02)',
                          border: `1px solid ${isOn ? color + '45' : 'rgba(255,255,255,0.07)'}`,
                          borderRadius: '10px', transition: 'all 0.22s', textAlign: 'center',
                        }}
                      >
                        <p style={{ fontFamily: 'monospace', fontSize: '7px', letterSpacing: '0.22em',
                                     textTransform: 'uppercase', color: `${color}85`, margin: '0 0 5px' }}>
                          {cat.replace(/_/g, ' ')}
                        </p>
                        <p style={{ fontFamily: 'serif', fontSize: '22px', color, margin: '0 0 3px', lineHeight: 1 }}>
                          {count}
                        </p>
                        <p style={{ fontFamily: 'sans-serif', fontSize: '9px',
                                     color: 'rgba(232,232,232,0.28)', margin: 0 }}>
                          → {link}
                        </p>
                      </button>
                    </div>
                  );
                })}
              </div>
            </div>

            {/* Expanded scroll list */}
            <AnimatePresence>
              {activeCat && scrollsByCategory[activeCat] && (
                <motion.div
                  key={activeCat}
                  initial={{ opacity: 0, height: 0 }} animate={{ opacity: 1, height: 'auto' }}
                  exit={{ opacity: 0, height: 0 }} style={{ overflow: 'hidden', marginTop: '14px' }}
                >
                  <div style={{
                    padding: '14px 16px',
                    background: 'rgba(255,255,255,0.013)',
                    border: `1px solid ${CAT_COLOR[activeCat] || '#888'}20`,
                    borderRadius: '10px',
                  }}>
                    <Label color={`${CAT_COLOR[activeCat] || '#888'}70`}>
                      {activeCat.replace(/_/g, ' ')} · {scrollsByCategory[activeCat].length} Scrolls
                    </Label>
                    <div style={{ display: 'flex', flexWrap: 'wrap', gap: '7px' }}>
                      {scrollsByCategory[activeCat].map(s => (
                        <div key={s.id} style={{
                          padding: '5px 10px',
                          background: `${CAT_COLOR[activeCat] || '#888'}08`,
                          border: `1px solid ${CAT_COLOR[activeCat] || '#888'}18`,
                          borderRadius: '6px',
                        }}>
                          <p style={{ fontFamily: 'sans-serif', fontSize: '10px',
                                       color: 'rgba(232,232,232,0.65)', margin: '0 0 2px' }}>
                            {s.label}
                          </p>
                          <p style={{ fontFamily: 'monospace', fontSize: '7px', letterSpacing: '0.15em',
                                       textTransform: 'uppercase',
                                       color: `${CAT_COLOR[activeCat] || '#888'}55`, margin: 0 }}>
                            {s.source}
                          </p>
                        </div>
                      ))}
                    </div>
                  </div>
                </motion.div>
              )}
            </AnimatePresence>

            {/* Vertical connector to sub-branches */}
            <div style={{ display: 'flex', justifyContent: 'center', marginTop: '18px' }}>
              <div style={{ width: '1px', height: '18px', background: 'rgba(0,212,170,0.3)' }} />
            </div>

            {/* Access Lattice + Collective Nodes */}
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px' }}>
              {/* Access Lattice */}
              <div style={{ padding: '14px 16px', background: 'rgba(0,212,170,0.03)',
                            border: '1px solid rgba(0,212,170,0.13)', borderRadius: '10px' }}>
                <Label color="rgba(0,212,170,0.5)">Access Lattice · {tools.length} Tools</Label>
                <div style={{ display: 'flex', flexWrap: 'wrap', gap: '5px' }}>
                  {tools.map(t => (
                    <span key={t} style={{
                      padding: '3px 8px', fontFamily: 'monospace', fontSize: '8px',
                      letterSpacing: '0.1em', textTransform: 'uppercase',
                      background: 'rgba(0,212,170,0.07)', border: '1px solid rgba(0,212,170,0.16)',
                      borderRadius: '5px', color: 'rgba(0,212,170,0.65)',
                    }}>
                      {t.replace(/_/g, '·')}
                    </span>
                  ))}
                </div>
              </div>

              {/* Collective Nodes */}
              <div style={{ padding: '14px 16px', background: 'rgba(106,159,216,0.03)',
                            border: '1px solid rgba(106,159,216,0.13)', borderRadius: '10px' }}>
                <Label color="rgba(106,159,216,0.5)">Collective Nodes · {collective.length}</Label>
                <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
                  {collective.slice(0, 7).map(n => (
                    <div key={n.display_name} style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
                      <span style={{ fontSize: '11px', opacity: 0.7, flexShrink: 0 }}>{n.role_sigil}</span>
                      <div style={{ flex: 1, minWidth: 0 }}>
                        <span style={{ fontFamily: 'sans-serif', fontSize: '10px',
                                       color: 'rgba(232,232,232,0.62)' }}>
                          {n.display_name}
                        </span>
                        <span style={{
                          fontFamily: 'monospace', fontSize: '7px', letterSpacing: '0.12em',
                          textTransform: 'uppercase', marginLeft: '7px',
                          color: n.status === 'active' ? 'rgba(0,212,170,0.5)'
                               : n.status === 'training' ? 'rgba(201,168,76,0.4)'
                               : 'rgba(232,232,232,0.2)',
                        }}>
                          {n.status}
                        </span>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </div>
        </SectionBox>
      </motion.div>

      {/* ── OPEN LOOPS — ACTIVE CURRENT ───────────────────────────────────── */}
      <motion.div initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.21 }}>
        <SectionBox accent="rgba(201,168,76,0.12)">
          <SectionHead label={`◉  Open Loops — Active Current  (${loops.length})`} color="#C9A84C" />
          <div style={{ padding: '12px 14px' }}>
            {loops.map((loop, i) => {
              const pColor = loop.priority === 1 ? '#E85246' : loop.priority === 2 ? '#C9A84C' : '#00D4AA';
              return (
                <motion.div
                  key={loop.id}
                  initial={{ opacity: 0, x: -6 }} animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: 0.24 + i * 0.04 }}
                  style={{ display: 'flex', gap: '12px', alignItems: 'flex-start', marginBottom: '8px',
                           padding: '12px 14px',
                           background: 'rgba(255,255,255,0.013)',
                           border: '1px solid rgba(255,255,255,0.055)', borderRadius: '8px' }}
                >
                  <div style={{
                    flexShrink: 0, width: '22px', height: '22px', borderRadius: '50%',
                    display: 'flex', alignItems: 'center', justifyContent: 'center',
                    background: `${pColor}14`, border: `1px solid ${pColor}38`,
                    fontFamily: 'monospace', fontSize: '9px', color: pColor,
                  }}>
                    {loop.priority}
                  </div>
                  <div style={{ flex: 1 }}>
                    <p style={{ fontFamily: 'sans-serif', fontSize: '12px',
                                color: 'rgba(232,232,232,0.72)', margin: '0 0 4px', lineHeight: '1.5' }}>
                      {loop.loop}
                    </p>
                    <div style={{ display: 'flex', gap: '10px' }}>
                      <span style={{ fontFamily: 'monospace', fontSize: '8px', letterSpacing: '0.14em',
                                     textTransform: 'uppercase', color: 'rgba(232,232,232,0.2)' }}>
                        {loop.id}
                      </span>
                      <span style={{ fontFamily: 'monospace', fontSize: '8px', letterSpacing: '0.14em',
                                     textTransform: 'uppercase', color: 'rgba(0,212,170,0.5)' }}>
                        ● {loop.status}
                      </span>
                    </div>
                  </div>
                </motion.div>
              );
            })}
          </div>
        </SectionBox>
      </motion.div>

      {/* ── 90-DAY ARCHITECTURE — CAUSAL ARC ─────────────────────────────── */}
      {arch && (
        <motion.div initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.28 }}>
          <SectionBox accent="rgba(106,159,216,0.13)">
            <SectionHead label="⟐  90-Day Architecture — Primary Causal Arc" color="#6A9FD8" />
            <div style={{ padding: '14px 16px' }}>
              {Object.entries(arch).map(([phaseKey, phase], i) => (
                <motion.div
                  key={phaseKey}
                  initial={{ opacity: 0, y: 6 }} animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: 0.32 + i * 0.08 }}
                  style={{ marginBottom: '12px', padding: '16px 18px',
                           background: 'rgba(255,255,255,0.012)',
                           border: '1px solid rgba(255,255,255,0.055)', borderRadius: '10px' }}
                >
                  <div style={{ display: 'flex', justifyContent: 'space-between',
                                alignItems: 'flex-start', marginBottom: '8px',
                                flexWrap: 'wrap', gap: '6px' }}>
                    <div>
                      <p style={{ fontFamily: 'monospace', fontSize: '8px', letterSpacing: '0.22em',
                                   textTransform: 'uppercase', color: 'rgba(106,159,216,0.5)', marginBottom: '3px' }}>
                        {phaseKey.replace('_', ' ')}
                      </p>
                      <p style={{ fontFamily: 'serif', fontSize: '18px', color: '#C9A84C', margin: 0 }}>
                        The {phase.name}
                      </p>
                    </div>
                    <span style={{ fontFamily: 'monospace', fontSize: '8px', letterSpacing: '0.15em',
                                   color: 'rgba(232,232,232,0.25)', padding: '3px 9px',
                                   border: '1px solid rgba(255,255,255,0.06)', borderRadius: '12px' }}>
                      Days {phase.days}
                    </span>
                  </div>
                  <p style={{ fontFamily: 'sans-serif', fontSize: '12px',
                               color: 'rgba(232,232,232,0.48)', lineHeight: '1.65', margin: '0 0 10px' }}>
                    {phase.focus}
                  </p>
                  <div style={{ padding: '9px 13px', background: 'rgba(201,168,76,0.04)',
                                borderLeft: '2px solid rgba(201,168,76,0.22)',
                                borderRadius: '0 6px 6px 0' }}>
                    <p style={{ fontFamily: 'serif', fontSize: '12px', fontStyle: 'italic',
                                 color: 'rgba(201,168,76,0.62)', margin: 0, lineHeight: '1.65' }}>
                      "{phase.anchor}"
                    </p>
                  </div>
                </motion.div>
              ))}
            </div>
          </SectionBox>
        </motion.div>
      )}

    </div>
  );
}
