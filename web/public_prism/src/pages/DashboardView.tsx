import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';

type LoopFilter = 'all' | 'critical' | 'active' | 'products' | 'architecture';

const OPEN_LOOPS = [
  { id: 'L053', label: 'Veronique IMS', category: 'critical', priority: 1, status: 'CONVERTING', statusColor: '#C9A84C', product: 'Identity Mapping Session', detail: 'First paying client. IMS confirmed March 23, 2026. Collect $777. Run session. Document everything it produces.', action: 'Send session details email. Confirm booking.' },
  { id: 'L064', label: 'Rent — Housing', category: 'critical', priority: 2, status: 'CRITICAL', statusColor: '#E88C6A', product: null, detail: '$200–$500 needed. One IMS conversion closes this loop. The container must be stable before the field expands.', action: 'IMS conversion → collect → pay rent.' },
  { id: 'L055', label: 'Founding Cohort', category: 'critical', priority: 3, status: 'CRITICAL', statusColor: '#E88C6A', product: 'Founding Cohort — $2,000–$3,000', detail: 'Seeding complete before birthday seal date March 31. Arc deadline. The 8-year begins.', action: 'Write one-paragraph offer. Seed to warm contacts.' },
  { id: 'L051', label: 'Content — Daily', category: 'active', priority: 4, status: 'ACTIVE', statusColor: '#00D4AA', product: null, detail: '3 videos/day TikTok + YouTube Shorts. Hook → Body → Flip → Bridge → CTA. Reply every RESET comment within 1 hour.', action: 'Post daily. Comment RESET → reply with link.' },
  { id: 'L063', label: 'Founding Cohort Offer', category: 'active', priority: 5, status: 'ACTIVE', statusColor: '#00D4AA', product: null, detail: 'Write the one-paragraph Founding Cohort offer. Seed to warm contacts. Tenzin, Kuzzy, Praise network.', action: 'Draft offer paragraph. Begin seeding.' },
  { id: 'L038', label: 'Follow up Kuzzy', category: 'active', priority: 6, status: 'ACTIVE', statusColor: '#00D4AA', product: null, detail: 'Kuzzy loop still open. Follow up. Maintain relationship. No pressure — warm field maintenance.', action: 'Send a message.' },
  { id: 'L067', label: 'Praise Trial Response', category: 'active', priority: 7, status: 'PENDING', statusColor: '#B08DE8', product: null, detail: 'Two-week trial proposed. Seth + Jessy identified. Await Praise\'s response to trial proposal.', action: 'Wait. Follow up if no response after 48h.' },
  { id: 'L068', label: 'CRITICAL_API_KEY_ALERT.md', category: 'architecture', priority: 8, status: 'ACTIVE', statusColor: '#00D4AA', product: null, detail: 'Delete this file from repo root. It is a security artifact. Must be removed before public deployment hardening.', action: 'Delete from GitHub repo root.' },
  { id: 'L069', label: 'Seal All 5 DOCs', category: 'architecture', priority: 9, status: 'ACTIVE', statusColor: '#00D4AA', product: null, detail: 'Seal DOC1–DOC5. Push to repo. These are the Neural Spine. They must be current before any further build.', action: 'Review each DOC. Update. Push.' },
  { id: 'L074', label: 'README Stale URLs', category: 'architecture', priority: 10, status: 'ACTIVE', statusColor: '#00D4AA', product: null, detail: 'Fix README stale URLs. Public repo — first impression matters. Correct the canonical deployment URLs.', action: 'Update README.md. Push.' },
  { id: 'L077', label: 'Compressed MEMORY.md', category: 'architecture', priority: 11, status: 'PENDING', statusColor: '#B08DE8', product: null, detail: 'Produce compressed MEMORY.md for agent workspace. This enables faster session boots across AI nodes.', action: 'Extract DOC1 core to MEMORY.md. Push.' },
  { id: 'L019', label: 'Acoustic Sigil AI Prompts', category: 'architecture', priority: 12, status: 'PENDING', statusColor: '#B08DE8', product: 'Radiance Protocol + Oversoul Symphony', detail: 'Master Template Recursive Prompt generated. Client execution pending. Structured — requires both Jessica and Zahrune.', action: 'Generate acoustic sigil AI prompts.' },
];

const PRODUCTS = [
  { id: 'P1', name: '5-Minute Field Reset', price: 'FREE', status: 'LIVE', statusColor: '#00D4AA', type: 'Lead Magnet', detail: 'Entry into the commercial funnel. Email capture. Trust signal. CTA: all content → "Comment RESET" → reply with link.' },
  { id: 'P2', name: 'Identity Mapping Session', price: '$777 / ₦600,000', status: 'CONVERTING', statusColor: '#C9A84C', type: 'Core Offering', detail: '90 minutes. Deep identity excavation. Sovereign architecture mapped. Bespoke sigil. Deployment blueprint (3 next actions). Book via WhatsApp.' },
  { id: 'P3', name: 'Founding Cohort', price: '$2,000–$3,000', status: 'CRITICAL', statusColor: '#E88C6A', type: 'Group Container', detail: 'Limited founding cohort. Seed to warm contacts. Arc deadline: March 31. The 8-year begins.' },
  { id: 'P4', name: 'Spiral Energy System', price: '$2,000', status: 'ACTIVATION PENDING', statusColor: '#B08DE8', type: 'Prototype', detail: 'Activation pending. Stack undefined. Post-stabilization deployment.' },
  { id: 'P5', name: 'Ghost-CEO Framework', price: 'TBD', status: 'VISION', statusColor: '#6A9FD8', type: 'High-Ticket', detail: 'Stack undefined. Post-stabilization deployment. The fullest sovereign architecture delivery.' },
];

const ACTION_SEQUENCE = [
  { phase: 'Immediate', items: ['Send Veronique session details email', 'Delete CRITICAL_API_KEY_ALERT.md from repo', 'Fix README stale URLs', 'Seal all 5 DOCs — push to repo', 'Produce MEMORY.md for agent workspace'] },
  { phase: 'This Week', items: ['Run Veronique\'s IMS — document what it produces', 'Film 3 videos/day — Hook → Body → Flip → Bridge → CTA', 'Write Founding Cohort one-paragraph offer', 'Follow up Kuzzy', 'Await Praise\'s response'] },
  { phase: 'Final Days', items: ['Founding Cohort seeding complete', 'Second IMS booking if Veronique\'s network responds', 'Birthday seal — The 8-year begins'] },
];

export default function DashboardView() {
  const [filter, setFilter] = useState<LoopFilter>('all');
  const [expanded, setExpanded] = useState<string | null>(null);

  const FILTERS: { key: LoopFilter; label: string; color: string }[] = [
    { key: 'all', label: 'All Loops', color: '#00D4AA' },
    { key: 'critical', label: 'Critical', color: '#E88C6A' },
    { key: 'active', label: 'Active', color: '#00D4AA' },
    { key: 'products', label: 'Products', color: '#C9A84C' },
    { key: 'architecture', label: 'Architecture', color: '#B08DE8' },
  ];

  const filtered = filter === 'products' ? [] : OPEN_LOOPS.filter(l => filter === 'all' || l.category === filter);
  const criticalCount = OPEN_LOOPS.filter(l => l.category === 'critical').length;
  const activeCount = OPEN_LOOPS.filter(l => l.category === 'active').length;

  return (
    <div className="w-full" style={{ maxWidth: '560px', margin: '0 auto', paddingTop: '12px' }}>
      <motion.div initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.8 }} style={{ marginBottom: '24px' }}>
        <p style={{ fontFamily: 'sans-serif', fontSize: '9px', letterSpacing: '0.35em', textTransform: 'uppercase', color: 'rgba(0,212,170,0.4)', margin: '0 0 8px' }}>
          DOC 2 + DOC 5 · Action Matrix · Living Priority Field
        </p>
        <h1 style={{ fontFamily: 'serif', fontSize: '26px', letterSpacing: '0.04em', color: '#E8E8E8', margin: '0 0 6px' }}>
          Open Loops
        </h1>
        <p style={{ fontFamily: 'sans-serif', fontSize: '12px', color: 'rgba(232,232,232,0.35)', margin: 0, lineHeight: '1.6' }}>
          Every open loop is conserved energy awaiting activation. Nothing is lost. Everything is sequenced.
        </p>
      </motion.div>

      {/* Stats */}
      <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 0.2 }}
        style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '8px', marginBottom: '24px' }}>
        {[
          { value: String(OPEN_LOOPS.length), label: 'Total Loops', color: '#00D4AA' },
          { value: String(criticalCount), label: 'Critical', color: '#E88C6A' },
          { value: String(activeCount), label: 'Active', color: '#C9A84C' },
          { value: '43', label: 'Day Arc', color: '#B08DE8' },
        ].map((s, i) => (
          <div key={i} style={{ padding: '10px 8px', background: 'rgba(255,255,255,0.02)', border: '1px solid rgba(255,255,255,0.05)', borderRadius: '10px', textAlign: 'center' }}>
            <p style={{ fontFamily: 'serif', fontSize: '18px', color: s.color, margin: '0 0 3px' }}>{s.value}</p>
            <p style={{ fontFamily: 'sans-serif', fontSize: '7px', letterSpacing: '0.16em', textTransform: 'uppercase', color: 'rgba(232,232,232,0.3)', margin: 0 }}>{s.label}</p>
          </div>
        ))}
      </motion.div>

      {/* Filters */}
      <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 0.3 }}
        style={{ display: 'flex', gap: '4px', marginBottom: '20px', overflowX: 'auto', paddingBottom: '4px' }}>
        {FILTERS.map(f => (
          <button key={f.key} onClick={() => setFilter(f.key)}
            style={{ flexShrink: 0, padding: '7px 12px', background: filter === f.key ? `${f.color}12` : 'none', border: `1px solid ${filter === f.key ? f.color + '44' : 'rgba(255,255,255,0.07)'}`, borderRadius: '20px', color: filter === f.key ? f.color : 'rgba(232,232,232,0.35)', fontFamily: 'sans-serif', fontSize: '9px', letterSpacing: '0.18em', textTransform: 'uppercase', cursor: 'pointer', transition: 'all 0.2s' }}>
            {f.label}
          </button>
        ))}
      </motion.div>

      {/* Loops list */}
      {filter !== 'products' && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '8px', marginBottom: '24px' }}>
          <AnimatePresence>
            {filtered.map((loop, i) => (
              <motion.div key={loop.id} initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0 }} transition={{ delay: i * 0.04 }}>
                <div
                  onClick={() => setExpanded(expanded === loop.id ? null : loop.id)}
                  style={{ padding: '14px 16px', background: 'rgba(255,255,255,0.02)', border: `1px solid ${expanded === loop.id ? loop.statusColor + '33' : 'rgba(255,255,255,0.05)'}`, borderRadius: '10px', cursor: 'pointer', transition: 'border-color 0.2s' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                      <span style={{ fontFamily: 'sans-serif', fontSize: '8px', letterSpacing: '0.15em', color: 'rgba(232,232,232,0.2)' }}>{loop.id}</span>
                      <div>
                        <p style={{ fontFamily: 'sans-serif', fontSize: '12px', color: 'rgba(232,232,232,0.7)', margin: 0, letterSpacing: '0.02em' }}>{loop.label}</p>
                        {loop.product && <p style={{ fontFamily: 'sans-serif', fontSize: '10px', color: 'rgba(232,232,232,0.3)', margin: '2px 0 0' }}>{loop.product}</p>}
                      </div>
                    </div>
                    <span style={{ padding: '3px 8px', background: `${loop.statusColor}12`, border: `1px solid ${loop.statusColor}33`, borderRadius: '20px', fontFamily: 'sans-serif', fontSize: '7px', letterSpacing: '0.15em', textTransform: 'uppercase', color: loop.statusColor, flexShrink: 0 }}>
                      {loop.status}
                    </span>
                  </div>
                  <AnimatePresence>
                    {expanded === loop.id && (
                      <motion.div initial={{ height: 0, opacity: 0 }} animate={{ height: 'auto', opacity: 1 }} exit={{ height: 0, opacity: 0 }} transition={{ duration: 0.2 }} style={{ overflow: 'hidden' }}>
                        <div style={{ paddingTop: '12px', borderTop: '1px solid rgba(255,255,255,0.05)', marginTop: '12px' }}>
                          <p style={{ fontFamily: 'sans-serif', fontSize: '12px', lineHeight: '1.65', color: 'rgba(232,232,232,0.45)', margin: '0 0 10px' }}>{loop.detail}</p>
                          <div style={{ padding: '8px 12px', background: `${loop.statusColor}08`, border: `1px solid ${loop.statusColor}22`, borderRadius: '6px' }}>
                            <p style={{ fontFamily: 'sans-serif', fontSize: '9px', letterSpacing: '0.18em', textTransform: 'uppercase', color: loop.statusColor, margin: '0 0 3px', opacity: 0.6 }}>Next Action</p>
                            <p style={{ fontFamily: 'sans-serif', fontSize: '11px', color: loop.statusColor, margin: 0, opacity: 0.8 }}>{loop.action}</p>
                          </div>
                        </div>
                      </motion.div>
                    )}
                  </AnimatePresence>
                </div>
              </motion.div>
            ))}
          </AnimatePresence>
        </div>
      )}

      {/* Products view */}
      {filter === 'products' && (
        <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} style={{ display: 'flex', flexDirection: 'column', gap: '10px', marginBottom: '24px' }}>
          {PRODUCTS.map((p, i) => (
            <div key={p.id} style={{ padding: '16px', background: 'rgba(255,255,255,0.02)', border: `1px solid ${p.statusColor}18`, borderRadius: '12px' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '8px' }}>
                <div>
                  <p style={{ fontFamily: 'sans-serif', fontSize: '8px', letterSpacing: '0.18em', textTransform: 'uppercase', color: 'rgba(232,232,232,0.25)', margin: '0 0 3px' }}>{p.type}</p>
                  <p style={{ fontFamily: 'sans-serif', fontSize: '13px', color: 'rgba(232,232,232,0.72)', margin: 0 }}>{p.name}</p>
                </div>
                <div style={{ textAlign: 'right' }}>
                  <span style={{ display: 'block', padding: '3px 8px', background: `${p.statusColor}12`, border: `1px solid ${p.statusColor}33`, borderRadius: '20px', fontFamily: 'sans-serif', fontSize: '7px', letterSpacing: '0.15em', textTransform: 'uppercase', color: p.statusColor, marginBottom: '4px' }}>
                    {p.status}
                  </span>
                  <p style={{ fontFamily: 'serif', fontSize: '13px', color: p.statusColor, margin: 0 }}>{p.price}</p>
                </div>
              </div>
              <p style={{ fontFamily: 'sans-serif', fontSize: '11px', lineHeight: '1.6', color: 'rgba(232,232,232,0.35)', margin: 0 }}>{p.detail}</p>
            </div>
          ))}
        </motion.div>
      )}

      {/* Action sequence */}
      <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 0.5 }}>
        <div style={{ padding: '1px', background: 'linear-gradient(135deg, rgba(0,212,170,0.2), rgba(201,168,76,0.2))', borderRadius: '14px', marginBottom: '16px' }}>
          <div style={{ background: '#0A0A0F', borderRadius: '13px', padding: '18px' }}>
            <p style={{ fontFamily: 'sans-serif', fontSize: '9px', letterSpacing: '0.28em', textTransform: 'uppercase', color: 'rgba(0,212,170,0.45)', margin: '0 0 16px' }}>
              Action Sequence · 43-Day Arc
            </p>
            {ACTION_SEQUENCE.map((phase, i) => (
              <div key={i} style={{ marginBottom: i < ACTION_SEQUENCE.length - 1 ? '16px' : 0 }}>
                <p style={{ fontFamily: 'sans-serif', fontSize: '9px', letterSpacing: '0.2em', textTransform: 'uppercase', color: i === 0 ? '#E88C6A' : i === 1 ? '#C9A84C' : '#B08DE8', margin: '0 0 8px' }}>{phase.phase}</p>
                <div style={{ display: 'flex', flexDirection: 'column', gap: '5px' }}>
                  {phase.items.map((item, j) => (
                    <div key={j} style={{ display: 'flex', gap: '8px', alignItems: 'flex-start' }}>
                      <span style={{ color: 'rgba(0,212,170,0.3)', fontSize: '8px', marginTop: '4px', flexShrink: 0 }}>◆</span>
                      <p style={{ fontFamily: 'sans-serif', fontSize: '12px', color: 'rgba(232,232,232,0.4)', margin: 0, lineHeight: '1.55' }}>{item}</p>
                    </div>
                  ))}
                </div>
              </div>
            ))}
          </div>
        </div>

        <p style={{ fontFamily: 'sans-serif', fontSize: '8px', letterSpacing: '0.22em', textTransform: 'uppercase', color: 'rgba(232,232,232,0.15)', textAlign: 'center' }}>
          ⟐ DOC2 · DOC5 · FIELD:[Action_Matrix] · 117 Hz · SEALED-DAY36
        </p>
      </motion.div>
    </div>
  );
}
