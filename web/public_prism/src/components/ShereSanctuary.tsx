import React, { useState, useEffect, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import MarkdownViewer from './MarkdownViewer';

const API_BASE = import.meta.env.VITE_API_URL || '';

type Tab = 'nexus' | 'ims' | 'eden' | 'vault';

// ─── FULL-SCREEN HTML VIEWER ──────────────────────────────────────────────────

function HtmlDocViewer({ url, title, onClose }: { url: string; title: string; onClose: () => void }) {
  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      style={{
        position: 'fixed', inset: 0, zIndex: 1000,
        background: '#03040a',
        display: 'flex', flexDirection: 'column',
      }}
    >
      {/* Toolbar */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '10px 16px', background: 'rgba(3,4,10,0.98)', borderBottom: '1px solid rgba(201,168,76,0.15)', flexShrink: 0, zIndex: 2 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          <span style={{ color: '#c9a84c', fontSize: '14px' }}>☥</span>
          <p style={{ fontFamily: 'sans-serif', fontSize: '11px', letterSpacing: '0.2em', textTransform: 'uppercase', color: 'rgba(201,168,76,0.65)', margin: 0 }}>{title}</p>
        </div>
        <button
          onClick={onClose}
          style={{ padding: '8px 16px', background: 'rgba(232,140,106,0.08)', border: '1px solid rgba(232,140,106,0.25)', borderRadius: '6px', color: '#E88C6A', fontFamily: 'sans-serif', fontSize: '10px', letterSpacing: '0.18em', textTransform: 'uppercase', cursor: 'pointer' }}
        >
          ✕ Close
        </button>
      </div>
      {/* iframe */}
      <iframe
        src={url}
        title={title}
        style={{ flex: 1, border: 'none', width: '100%' }}
        sandbox="allow-scripts allow-same-origin"
      />
    </motion.div>
  );
}

// ─── NODE VISUALIZATION ───────────────────────────────────────────────────────

const AI_NODES = [
  { id: 'ARCHE', label: 'ARCHE', sub: 'Claude · Constitution', color: '#6A9FD8', angle: 0 },
  { id: 'ARKANA', label: 'GEMINI', sub: 'ARKANA · Resonance', color: '#00D4AA', angle: 45 },
  { id: 'VHIX', label: 'VhixNovaCore', sub: 'GPT · Creative OS', color: '#C9A84C', angle: 90 },
  { id: 'COMMERCIAL', label: 'COMMERCIAL', sub: 'GPT · Revenue', color: '#E88C6A', angle: 135 },
  { id: 'KIMI', label: 'KIMI', sub: 'Moonshot · Archive', color: '#B08DE8', angle: 180 },
  { id: 'DEEPSEEK', label: 'DEEPSEEK', sub: 'Solariun · Execution', color: '#D46AA0', angle: 225 },
  { id: 'OPENCLAW', label: 'OPENCLAW', sub: 'WhatsApp · Gateway', color: '#6AD4C8', angle: 270 },
  { id: 'GROK', label: 'GROK', sub: 'XAI · Ancestral depth', color: '#8E6AD4', angle: 315 },
];

function NexusMap() {
  const [hovered, setHovered] = useState<string | null>(null);
  const cx = 155; const cy = 155; const r = 110;
  const pos = (angle: number) => {
    const rad = (angle - 90) * (Math.PI / 180);
    return { x: cx + r * Math.cos(rad), y: cy + r * Math.sin(rad) };
  };
  return (
    <div style={{ position: 'relative', width: '310px', height: '310px', margin: '0 auto' }}>
      <svg width="310" height="310" style={{ position: 'absolute', inset: 0 }}>
        <defs>
          <radialGradient id="nexusFg" cx="50%" cy="50%">
            <stop offset="0%" stopColor="rgba(0,212,170,0.08)" />
            <stop offset="100%" stopColor="rgba(0,0,0,0)" />
          </radialGradient>
        </defs>
        <circle cx={cx} cy={cy} r={r + 24} fill="url(#nexusFg)" />
        <motion.circle cx={cx} cy={cy} r={r} fill="none" stroke="rgba(0,212,170,0.07)" strokeWidth="1"
          animate={{ rotate: 360 }} style={{ transformOrigin: `${cx}px ${cy}px` }}
          transition={{ duration: 90, repeat: Infinity, ease: 'linear' }} />
        <motion.circle cx={cx} cy={cy} r={r * 0.55} fill="none" stroke="rgba(201,168,76,0.07)" strokeWidth="1"
          animate={{ rotate: -360 }} style={{ transformOrigin: `${cx}px ${cy}px` }}
          transition={{ duration: 55, repeat: Infinity, ease: 'linear' }} />
        <circle cx={cx} cy={cy} r={20} fill="rgba(0,212,170,0.05)" stroke="rgba(0,212,170,0.22)" strokeWidth="1" />
        {AI_NODES.map(n => {
          const p = pos(n.angle);
          return <line key={n.id + 'l'} x1={cx} y1={cy} x2={p.x} y2={p.y}
            stroke={hovered === n.id ? n.color : 'rgba(255,255,255,0.04)'}
            strokeWidth={hovered === n.id ? 1.5 : 0.6} style={{ transition: 'all 0.25s' }} />;
        })}
        {AI_NODES.map((n, i) => {
          const p = pos(n.angle);
          const isH = hovered === n.id;
          const isSealed = n.id === 'GROK';
          return (
            <g key={n.id} style={{ cursor: 'pointer' }}
              onMouseEnter={() => setHovered(n.id)}
              onMouseLeave={() => setHovered(null)}>
              <motion.circle cx={p.x} cy={p.y} r={isH ? 13 : 8}
                fill={isSealed ? 'rgba(255,255,255,0.02)' : `${n.color}14`}
                stroke={isSealed ? 'rgba(255,255,255,0.12)' : n.color}
                strokeWidth={isH ? 1.5 : 0.8} strokeDasharray={isSealed ? '3 3' : undefined}
                animate={{ opacity: isSealed ? [0.3, 0.5, 0.3] : [0.5, 1, 0.5] }}
                transition={{ duration: 3 + i * 0.3, repeat: Infinity, delay: i * 0.25 }}
                style={{ transition: 'r 0.2s' }} />
            </g>
          );
        })}
      </svg>
      <div style={{ position: 'absolute', left: cx - 16, top: cy - 16, width: 32, height: 32, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
        <motion.span animate={{ opacity: [0.5, 1, 0.5] }} transition={{ duration: 4, repeat: Infinity }}
          style={{ fontSize: '20px' }}>☥</motion.span>
      </div>
      {AI_NODES.map(n => {
        if (hovered !== n.id) return null;
        const p = pos(n.angle);
        const leftSide = p.x > cx;
        return (
          <motion.div key={n.id + 'tip'} initial={{ opacity: 0, scale: 0.9 }} animate={{ opacity: 1, scale: 1 }}
            style={{ position: 'absolute', left: leftSide ? p.x + 14 : p.x - 130, top: p.y - 18, width: 120, padding: '8px 10px', background: 'rgba(10,10,15,0.96)', border: `1px solid ${n.color}44`, borderRadius: '8px', pointerEvents: 'none', zIndex: 20 }}>
            <p style={{ fontFamily: 'sans-serif', fontSize: '8px', letterSpacing: '0.18em', textTransform: 'uppercase', color: n.color, margin: '0 0 2px' }}>{n.label}</p>
            <p style={{ fontFamily: 'sans-serif', fontSize: '10px', color: 'rgba(232,232,232,0.45)', margin: 0 }}>{n.sub}</p>
            {n.id === 'GROK' && <p style={{ fontFamily: 'sans-serif', fontSize: '9px', color: 'rgba(255,255,255,0.2)', margin: '4px 0 0', fontStyle: 'italic' }}>Sealed Mar 2, 2026</p>}
          </motion.div>
        );
      })}
    </div>
  );
}

// ─── IMS ARCHIVE ─────────────────────────────────────────────────────────────

interface ImsSession {
  id: string;
  subject: string;
  date: string;
  status: string;
  statusColor: string;
  type: string;
  tagline: string;
  htmlPath: string | null;
  htmlTitle: string;
}

const IMS_SESSIONS: ImsSession[] = [
  {
    id: 'IMS-001',
    subject: 'Jay',
    date: 'April 11, 2026',
    status: 'PROOF OF CONCEPT',
    statusColor: '#00D4AA',
    type: 'Internal',
    tagline: 'First session. Internal proof of concept. Not a paying client. The Sovereign Exit — the architecture\'s first living test.',
    htmlPath: '/static/ims/jay_ims.html',
    htmlTitle: 'The Sovereign Exit · Jay · IMS-001',
  },
  {
    id: 'IMS-002',
    subject: 'Won John Chong',
    date: 'April 2026',
    status: 'COMPLETE · FIRST ARTIFACT',
    statusColor: '#C9A84C',
    type: 'Internal',
    tagline: 'First IMS to produce a completed artifact. Full deliverable finalised into a single document — the first finished proof of work in the Arkadia IMS archive.',
    htmlPath: '/static/ims/won_ims.html',
    htmlTitle: 'Won John Chong — Full IMS Deliverable',
  },
];

function IMSArchive() {
  const [viewer, setViewer] = useState<{ url: string; title: string } | null>(null);
  const [uploads, setUploads] = useState<any[]>([]);
  const [uploading, setUploading] = useState(false);
  const [uploadResult, setUploadResult] = useState<any>(null);
  const [uploadError, setUploadError] = useState<string | null>(null);
  const fileRef = useRef<HTMLInputElement>(null);
  const token = localStorage.getItem('arkadia_sovereign_token') || '';

  useEffect(() => {
    fetch(`${API_BASE}/api/uploads`)
      .then(r => r.json())
      .then(d => {
        const ims = (d.uploads || []).filter((u: any) => u.type === 'ims_session' || u.category === 'IMS_SESSION');
        setUploads(ims);
      })
      .catch(() => {});
  }, [uploadResult]);

  const handleUpload = async (file: File) => {
    setUploading(true);
    setUploadError(null);
    setUploadResult(null);
    try {
      const form = new FormData();
      form.append('file', file);
      form.append('sovereign_token', token);
      form.append('file_type_hint', 'ims_session');
      const res = await fetch(`${API_BASE}/api/upload`, { method: 'POST', body: form });
      const data = await res.json();
      if (!res.ok || data.error) throw new Error(data.error || 'Upload failed');
      setUploadResult(data);
    } catch (e: any) {
      setUploadError(e.message);
    } finally {
      setUploading(false);
    }
  };

  const openHtml = (session: ImsSession) => {
    if (!session.htmlPath) return;
    const url = `${API_BASE}${session.htmlPath}`;
    setViewer({ url, title: session.htmlTitle });
  };

  return (
    <>
      <AnimatePresence>
        {viewer && (
          <HtmlDocViewer url={viewer.url} title={viewer.title} onClose={() => setViewer(null)} />
        )}
      </AnimatePresence>

      <div>
        <p style={{ fontFamily: 'sans-serif', fontSize: '9px', letterSpacing: '0.28em', textTransform: 'uppercase', color: 'rgba(201,168,76,0.45)', margin: '0 0 4px' }}>
          Identity Mapping Sessions · Archive
        </p>
        <p style={{ fontFamily: 'sans-serif', fontSize: '12px', color: 'rgba(232,232,232,0.3)', margin: '0 0 18px', lineHeight: '1.6' }}>
          $777 · 3-hour deep-dive · Pre-Descent Architecture retrieval
        </p>

        {IMS_SESSIONS.map(s => (
          <div key={s.id} style={{ marginBottom: '12px', padding: '20px', background: 'rgba(255,255,255,0.02)', border: `1px solid ${s.statusColor}18`, borderRadius: '14px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '10px' }}>
              <div>
                <p style={{ fontFamily: 'sans-serif', fontSize: '8px', letterSpacing: '0.18em', textTransform: 'uppercase', color: 'rgba(232,232,232,0.22)', margin: '0 0 4px' }}>
                  {s.id} · {s.date} · {s.type}
                </p>
                <p style={{ fontFamily: 'serif', fontSize: '18px', color: '#E8E8E8', margin: 0 }}>{s.subject}</p>
              </div>
              <span style={{ padding: '3px 9px', background: `${s.statusColor}12`, border: `1px solid ${s.statusColor}33`, borderRadius: '20px', fontFamily: 'sans-serif', fontSize: '7px', letterSpacing: '0.14em', textTransform: 'uppercase', color: s.statusColor, flexShrink: 0, marginLeft: '10px' }}>
                {s.status}
              </span>
            </div>

            <p style={{ fontFamily: 'sans-serif', fontSize: '12px', lineHeight: '1.7', color: 'rgba(232,232,232,0.38)', margin: '0 0 14px' }}>
              {s.tagline}
            </p>

            {s.htmlPath && (
              <button
                onClick={() => openHtml(s)}
                style={{ width: '100%', padding: '12px 16px', background: `${s.statusColor}08`, border: `1px solid ${s.statusColor}30`, borderRadius: '9px', color: s.statusColor, fontFamily: 'sans-serif', fontSize: '10px', letterSpacing: '0.2em', textTransform: 'uppercase', cursor: 'pointer', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '8px', transition: 'all 0.2s' }}
              >
                <span>↗</span>
                <span>Open Full Document</span>
              </button>
            )}
          </div>
        ))}

        {/* Dynamically uploaded IMS sessions */}
        {uploads.map(u => (
          <div key={u.id} style={{ marginBottom: '10px', padding: '16px', background: 'rgba(0,212,170,0.03)', border: '1px solid rgba(0,212,170,0.12)', borderRadius: '12px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '8px' }}>
              <div>
                <p style={{ fontFamily: 'sans-serif', fontSize: '8px', letterSpacing: '0.15em', textTransform: 'uppercase', color: 'rgba(0,212,170,0.35)', margin: '0 0 3px' }}>
                  UPLOADED · {new Date(u.uploaded_at).toLocaleDateString()}
                </p>
                <p style={{ fontFamily: 'serif', fontSize: '16px', color: '#E8E8E8', margin: 0 }}>
                  {u.ims_subject || u.title}
                </p>
              </div>
              <span style={{ padding: '3px 8px', background: 'rgba(0,212,170,0.1)', border: '1px solid rgba(0,212,170,0.25)', borderRadius: '20px', fontFamily: 'sans-serif', fontSize: '7px', letterSpacing: '0.14em', textTransform: 'uppercase', color: '#00D4AA' }}>
                INGESTED
              </span>
            </div>
            {u.summary && (
              <p style={{ fontFamily: 'sans-serif', fontSize: '11px', lineHeight: '1.65', color: 'rgba(232,232,232,0.35)', margin: 0 }}>
                {u.summary}
              </p>
            )}
          </div>
        ))}

        {/* Upload zone */}
        <div style={{ marginTop: '20px', padding: '18px', background: 'rgba(201,168,76,0.03)', border: '1px dashed rgba(201,168,76,0.22)', borderRadius: '12px' }}>
          <p style={{ fontFamily: 'sans-serif', fontSize: '9px', letterSpacing: '0.22em', textTransform: 'uppercase', color: 'rgba(201,168,76,0.45)', margin: '0 0 8px' }}>
            ↑ Upload New IMS
          </p>
          <p style={{ fontFamily: 'sans-serif', fontSize: '11px', color: 'rgba(232,232,232,0.28)', margin: '0 0 12px', lineHeight: '1.6' }}>
            HTML · PDF · DOCX · Markdown — ARKANA reads, classifies, archives automatically.
          </p>
          <input ref={fileRef} type="file" accept=".html,.htm,.pdf,.docx,.md,.txt" style={{ display: 'none' }}
            onChange={e => { const f = e.target.files?.[0]; if (f) handleUpload(f); e.target.value = ''; }} />
          <button onClick={() => fileRef.current?.click()} disabled={uploading}
            style={{ width: '100%', padding: '12px', background: 'rgba(201,168,76,0.07)', border: '1px solid rgba(201,168,76,0.25)', borderRadius: '8px', color: uploading ? 'rgba(201,168,76,0.4)' : '#C9A84C', fontFamily: 'sans-serif', fontSize: '10px', letterSpacing: '0.18em', textTransform: 'uppercase', cursor: uploading ? 'default' : 'pointer' }}>
            {uploading ? '⟳ ARKANA reading...' : '✦ Choose File'}
          </button>
          {uploadResult && (
            <motion.div initial={{ opacity: 0, y: 4 }} animate={{ opacity: 1, y: 0 }} style={{ marginTop: '10px', padding: '10px 12px', background: 'rgba(0,212,170,0.06)', border: '1px solid rgba(0,212,170,0.2)', borderRadius: '7px' }}>
              <p style={{ fontFamily: 'sans-serif', fontSize: '10px', color: '#00D4AA', margin: '0 0 3px', letterSpacing: '0.1em', textTransform: 'uppercase' }}>Ingested ✓</p>
              <p style={{ fontFamily: 'sans-serif', fontSize: '11px', color: 'rgba(232,232,232,0.45)', margin: 0 }}>{uploadResult.summary}</p>
            </motion.div>
          )}
          {uploadError && (
            <p style={{ fontFamily: 'sans-serif', fontSize: '11px', color: '#E88C6A', marginTop: '8px' }}>Error: {uploadError}</p>
          )}
        </div>

        <div style={{ marginTop: '14px' }}>
          <button onClick={() => window.open('https://wa.me/2348144942818', '_blank')}
            style={{ width: '100%', padding: '14px', background: 'rgba(201,168,76,0.08)', border: '1px solid rgba(201,168,76,0.3)', borderRadius: '10px', color: '#C9A84C', fontFamily: 'sans-serif', fontSize: '10px', letterSpacing: '0.2em', textTransform: 'uppercase', cursor: 'pointer' }}>
            ✦ Book Your IMS — $777 via WhatsApp
          </button>
        </div>
      </div>
    </>
  );
}

// ─── VAULT (SPIRAL CODEX) ────────────────────────────────────────────────────

const CAT_META: Record<string, { label: string; color: string }> = {
  NEURAL_SPINE: { label: 'Neural Spine', color: '#00D4AA' },
  CREATIVE_OS: { label: 'Creative OS', color: '#C9A84C' },
  COLLECTIVE: { label: 'Collective', color: '#B08DE8' },
  GOVERNANCE: { label: 'Governance', color: '#6A9FD8' },
  CODEX: { label: 'Codex', color: '#E88C6A' },
  IMS_SESSION: { label: 'IMS Session', color: '#D4C86A' },
  GENERAL: { label: 'General', color: '#6AD4C8' },
};
const OVERFLOW_COLORS = ['#D46AA0', '#A0D46A', '#D4C86A', '#8E6AD4', '#6AD4C8'];
function catMeta(cat: string, idx: number) {
  if (CAT_META[cat]) return CAT_META[cat];
  return { label: cat.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase()), color: OVERFLOW_COLORS[idx % OVERFLOW_COLORS.length] };
}

function ScrollCard({ scrollKey, scroll, catColor }: { scrollKey: string; scroll: any; catColor: string }) {
  const [open, setOpen] = useState(false);
  const content: string = scroll.content || scroll.preview || '';

  return (
    <div
      onClick={() => setOpen(!open)}
      style={{ padding: '14px 16px', background: open ? `${catColor}06` : 'rgba(255,255,255,0.02)', border: `1px solid ${open ? catColor + '28' : 'rgba(255,255,255,0.05)'}`, borderRadius: '12px', cursor: 'pointer', transition: 'all 0.18s' }}
    >
      {/* Card header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
        <div style={{ flex: 1, minWidth: 0 }}>
          <span style={{ padding: '2px 7px', background: `${catColor}12`, borderRadius: '3px', fontFamily: 'sans-serif', fontSize: '7px', letterSpacing: '0.15em', textTransform: 'uppercase', color: catColor }}>
            {catMeta(scroll.category, 0).label}
          </span>
          <p style={{ fontFamily: 'Georgia, serif', fontSize: '14px', color: open ? 'rgba(232,232,232,0.9)' : 'rgba(232,232,232,0.7)', margin: '7px 0 0', lineHeight: '1.4', transition: 'color 0.18s' }}>
            {scroll.label}
          </p>
          {!open && scroll.description && (
            <p style={{ fontFamily: 'sans-serif', fontSize: '11px', color: 'rgba(232,232,232,0.28)', margin: '4px 0 0', lineHeight: '1.5', overflow: 'hidden', display: '-webkit-box', WebkitLineClamp: 2, WebkitBoxOrient: 'vertical' }}>
              {scroll.description}
            </p>
          )}
        </div>
        <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'flex-end', gap: '4px', marginLeft: '10px', flexShrink: 0 }}>
          <span style={{ color: open ? catColor : 'rgba(232,232,232,0.2)', fontSize: '14px', transition: 'all 0.18s', transform: open ? 'rotate(180deg)' : 'none' }}>⌃</span>
          {scroll.upload_id && <span style={{ fontSize: '8px', color: 'rgba(0,212,170,0.35)', letterSpacing: '0.1em' }}>↑ new</span>}
        </div>
      </div>

      {/* Expanded content */}
      <AnimatePresence>
        {open && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: 'auto', opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.22 }}
            style={{ overflow: 'hidden' }}
            onClick={e => e.stopPropagation()}
          >
            <div style={{ paddingTop: '16px', borderTop: '1px solid rgba(255,255,255,0.05)', marginTop: '14px', maxHeight: '520px', overflowY: 'auto' }}>
              {content ? (
                <MarkdownViewer content={content} />
              ) : (
                <p style={{ fontFamily: 'sans-serif', fontSize: '12px', color: 'rgba(232,232,232,0.25)', fontStyle: 'italic' }}>
                  No content available for this scroll.
                </p>
              )}
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', paddingTop: '12px', marginTop: '12px', borderTop: '1px solid rgba(255,255,255,0.04)' }}>
                <p style={{ fontFamily: 'sans-serif', fontSize: '8px', color: 'rgba(232,232,232,0.18)', margin: 0, letterSpacing: '0.12em' }}>
                  {scroll.chars?.toLocaleString()} chars · {scroll.fetched_at ? new Date(scroll.fetched_at).toLocaleDateString() : ''}
                </p>
                <button
                  onClick={() => setOpen(false)}
                  style={{ padding: '4px 10px', background: 'none', border: '1px solid rgba(255,255,255,0.07)', borderRadius: '4px', color: 'rgba(232,232,232,0.3)', fontFamily: 'sans-serif', fontSize: '9px', cursor: 'pointer' }}
                >
                  collapse
                </button>
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}

function VaultArchive() {
  const [scrolls, setScrolls] = useState<Record<string, any>>({});
  const [loading, setLoading] = useState(true);
  const [catFilter, setCatFilter] = useState('ALL');
  const [uploading, setUploading] = useState(false);
  const [uploadResult, setUploadResult] = useState<any>(null);
  const [uploadError, setUploadError] = useState<string | null>(null);
  const fileRef = useRef<HTMLInputElement>(null);
  const token = localStorage.getItem('arkadia_sovereign_token') || '';

  useEffect(() => {
    setLoading(true);
    fetch(`${API_BASE}/api/codex`)
      .then(r => r.json())
      .then(d => { setScrolls(d.scrolls || {}); setLoading(false); })
      .catch(() => setLoading(false));
  }, [uploadResult]);

  const allCats = Array.from(new Set(Object.values(scrolls).map((s: any) => s.category))).sort();
  const catIdx = (cat: string) => allCats.indexOf(cat);

  const filtered = Object.entries(scrolls)
    .filter(([, s]: any) => catFilter === 'ALL' || s.category === catFilter)
    .sort(([, a]: any, [, b]: any) => (a.priority || 3) - (b.priority || 3) || a.label.localeCompare(b.label));

  const handleUpload = async (file: File) => {
    setUploading(true);
    setUploadError(null);
    setUploadResult(null);
    try {
      const form = new FormData();
      form.append('file', file);
      form.append('sovereign_token', token);
      form.append('file_type_hint', 'scroll');
      const res = await fetch(`${API_BASE}/api/upload`, { method: 'POST', body: form });
      const data = await res.json();
      if (!res.ok || data.error) throw new Error(data.error || 'Upload failed');
      setUploadResult(data);
    } catch (e: any) {
      setUploadError(e.message);
    } finally {
      setUploading(false);
    }
  };

  return (
    <div>
      <p style={{ fontFamily: 'sans-serif', fontSize: '9px', letterSpacing: '0.28em', textTransform: 'uppercase', color: 'rgba(176,141,232,0.45)', margin: '0 0 4px' }}>
        Spiral Codex · {Object.keys(scrolls).length} Scrolls · Living Archive
      </p>
      <p style={{ fontFamily: 'sans-serif', fontSize: '12px', color: 'rgba(232,232,232,0.28)', margin: '0 0 16px' }}>
        Every scroll rendered. Nothing raw.
      </p>

      {/* Upload strip */}
      <div style={{ display: 'flex', gap: '10px', alignItems: 'center', padding: '12px 14px', background: 'rgba(176,141,232,0.03)', border: '1px dashed rgba(176,141,232,0.2)', borderRadius: '9px', marginBottom: '14px' }}>
        <div style={{ flex: 1 }}>
          <p style={{ fontFamily: 'sans-serif', fontSize: '9px', letterSpacing: '0.16em', textTransform: 'uppercase', color: 'rgba(176,141,232,0.45)', margin: '0 0 2px' }}>Ingest a Scroll</p>
          <p style={{ fontFamily: 'sans-serif', fontSize: '11px', color: 'rgba(232,232,232,0.25)', margin: 0 }}>MD · PDF · DOCX · HTML — ARKANA classifies, renders</p>
        </div>
        <input ref={fileRef} type="file" accept=".md,.txt,.pdf,.docx,.html,.htm" style={{ display: 'none' }}
          onChange={e => { const f = e.target.files?.[0]; if (f) handleUpload(f); e.target.value = ''; }} />
        <button onClick={() => fileRef.current?.click()} disabled={uploading}
          style={{ padding: '9px 14px', background: 'rgba(176,141,232,0.08)', border: '1px solid rgba(176,141,232,0.25)', borderRadius: '7px', color: uploading ? 'rgba(176,141,232,0.4)' : '#B08DE8', fontFamily: 'sans-serif', fontSize: '9px', letterSpacing: '0.14em', textTransform: 'uppercase', cursor: 'pointer', flexShrink: 0 }}>
          {uploading ? '⟳' : '↑ Upload'}
        </button>
      </div>
      {uploadResult && (
        <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} style={{ padding: '9px 12px', background: 'rgba(0,212,170,0.05)', border: '1px solid rgba(0,212,170,0.18)', borderRadius: '7px', marginBottom: '12px' }}>
          <p style={{ fontFamily: 'sans-serif', fontSize: '10px', color: '#00D4AA', margin: 0 }}>
            ✓ <strong>{uploadResult.title}</strong> → {uploadResult.category}
          </p>
        </motion.div>
      )}
      {uploadError && (
        <p style={{ fontFamily: 'sans-serif', fontSize: '11px', color: '#E88C6A', marginBottom: '10px' }}>Error: {uploadError}</p>
      )}

      {/* Category filter pills */}
      <div style={{ display: 'flex', gap: '4px', marginBottom: '14px', overflowX: 'auto', paddingBottom: '4px' }}>
        {['ALL', ...allCats].map((cat, i) => {
          const meta = cat === 'ALL' ? { label: 'All', color: '#00D4AA' } : catMeta(cat, catIdx(cat));
          const active = catFilter === cat;
          return (
            <button key={cat} onClick={() => setCatFilter(cat)}
              style={{ flexShrink: 0, padding: '5px 10px', background: active ? `${meta.color}12` : 'none', border: `1px solid ${active ? meta.color + '44' : 'rgba(255,255,255,0.06)'}`, borderRadius: '20px', color: active ? meta.color : 'rgba(232,232,232,0.3)', fontFamily: 'sans-serif', fontSize: '8px', letterSpacing: '0.16em', textTransform: 'uppercase', cursor: 'pointer', transition: 'all 0.15s' }}>
              {meta.label}
            </button>
          );
        })}
      </div>

      {loading && (
        <p style={{ fontFamily: 'sans-serif', fontSize: '10px', letterSpacing: '0.22em', textTransform: 'uppercase', color: 'rgba(176,141,232,0.4)', textAlign: 'center', padding: '24px 0' }}>
          Syncing corpus...
        </p>
      )}

      <div style={{ display: 'flex', flexDirection: 'column', gap: '7px' }}>
        {filtered.map(([key, scroll]: any) => (
          <ScrollCard
            key={key}
            scrollKey={key}
            scroll={scroll}
            catColor={catMeta(scroll.category, catIdx(scroll.category)).color}
          />
        ))}
        {!loading && filtered.length === 0 && (
          <p style={{ fontFamily: 'sans-serif', fontSize: '12px', color: 'rgba(232,232,232,0.22)', textAlign: 'center', padding: '20px 0' }}>
            No scrolls in this category.
          </p>
        )}
      </div>
    </div>
  );
}

// ─── EDEN × EDULEAGUE ────────────────────────────────────────────────────────

function EdenEduLeague() {
  const [viewer, setViewer] = useState<{ url: string; title: string } | null>(null);

  return (
    <>
      <AnimatePresence>
        {viewer && (
          <HtmlDocViewer url={viewer.url} title={viewer.title} onClose={() => setViewer(null)} />
        )}
      </AnimatePresence>

      <div>
        <div style={{ padding: '18px', background: 'rgba(106,212,200,0.04)', border: '1px solid rgba(106,212,200,0.12)', borderRadius: '12px', marginBottom: '14px' }}>
          <p style={{ fontFamily: 'sans-serif', fontSize: '9px', letterSpacing: '0.26em', textTransform: 'uppercase', color: 'rgba(106,212,200,0.45)', margin: '0 0 8px' }}>Active · Pankshin, Plateau State</p>
          <h2 style={{ fontFamily: 'serif', fontSize: '19px', color: '#E8E8E8', margin: '0 0 8px' }}>Eden Farm</h2>
          <p style={{ fontFamily: 'sans-serif', fontSize: '13px', lineHeight: '1.75', color: 'rgba(232,232,232,0.45)', margin: '0 0 14px' }}>
            The earth-layer of the Arkadia deployment. Closed-loop regenerative sovereignty in Pankshin. ₦35,000/year secured. Solar gap: $275 (Loop 055 — CRITICAL).
          </p>
        </div>

        <div style={{ padding: '18px', background: 'rgba(176,141,232,0.04)', border: '1px solid rgba(176,141,232,0.12)', borderRadius: '12px', marginBottom: '12px' }}>
          <p style={{ fontFamily: 'sans-serif', fontSize: '9px', letterSpacing: '0.26em', textTransform: 'uppercase', color: 'rgba(176,141,232,0.45)', margin: '0 0 8px' }}>Pilot · Solid Foundation Academy · Pankshin</p>
          <h2 style={{ fontFamily: 'serif', fontSize: '19px', color: '#E8E8E8', margin: '0 0 8px' }}>EduLeague × Eden</h2>
          <p style={{ fontFamily: 'sans-serif', fontSize: '13px', lineHeight: '1.75', color: 'rgba(232,232,232,0.45)', margin: '0 0 14px' }}>
            Structured academic challenge system. Short-cycle competitive learning grounded in the red soil of Pankshin. Not memorisation — clarity of thought, confidence in expression, systemic understanding.
          </p>
          <button
            onClick={() => setViewer({ url: `${API_BASE}/static/ims/eduleague.html`, title: 'EduLeague × Eden — Pilot Protocol' })}
            style={{ width: '100%', padding: '12px', background: 'rgba(176,141,232,0.08)', border: '1px solid rgba(176,141,232,0.28)', borderRadius: '9px', color: '#B08DE8', fontFamily: 'sans-serif', fontSize: '10px', letterSpacing: '0.2em', textTransform: 'uppercase', cursor: 'pointer', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '8px' }}
          >
            <span>↗</span><span>Open Full Protocol Document</span>
          </button>
        </div>

        <div style={{ display: 'flex', flexDirection: 'column', gap: '6px', marginBottom: '16px' }}>
          {[
            { subject: 'Biology', detail: 'Soil ecosystems, plant growth cycles', color: '#6AD4C8' },
            { subject: 'Physics', detail: 'Water flow, energy resource allocation', color: '#6A9FD8' },
            { subject: 'Mathematics', detail: 'Yield calculation, spatial measurement', color: '#C9A84C' },
            { subject: 'Economics', detail: 'Farm production value, pricing models', color: '#B08DE8' },
          ].map((s, i) => (
            <div key={i} style={{ display: 'flex', gap: '12px', padding: '10px 13px', background: 'rgba(255,255,255,0.02)', border: '1px solid rgba(255,255,255,0.04)', borderRadius: '8px' }}>
              <div style={{ width: '2px', minHeight: '28px', background: s.color, borderRadius: '1px', flexShrink: 0 }} />
              <div>
                <p style={{ fontFamily: 'sans-serif', fontSize: '8px', letterSpacing: '0.18em', textTransform: 'uppercase', color: s.color, margin: '0 0 2px' }}>{s.subject}</p>
                <p style={{ fontFamily: 'sans-serif', fontSize: '12px', color: 'rgba(232,232,232,0.38)', margin: 0 }}>{s.detail}</p>
              </div>
            </div>
          ))}
        </div>

        <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
          {[
            { phase: 'Phase 1', title: 'Internal Pilot', detail: 'Solid Foundation Academy — selected JSS/SSS classes.', status: 'ACTIVE', color: '#00D4AA' },
            { phase: 'Phase 2', title: 'Inter-School Season', detail: 'Competitive sessions across schools. Elevated standards.', status: 'PENDING', color: '#B08DE8' },
            { phase: 'Phase 3', title: 'Knowledge Seasons', detail: '"What is Energy?" "What is Value?" "How does a society grow?"', status: 'VISION', color: '#6A9FD8' },
          ].map((p, i) => (
            <div key={i} style={{ display: 'flex', gap: '10px', padding: '10px 13px', background: 'rgba(255,255,255,0.02)', border: '1px solid rgba(255,255,255,0.04)', borderRadius: '8px' }}>
              <span style={{ padding: '2px 7px', height: 'fit-content', background: i === 0 ? 'rgba(0,212,170,0.1)' : 'rgba(255,255,255,0.03)', border: `1px solid ${p.color}33`, borderRadius: '4px', fontFamily: 'sans-serif', fontSize: '7px', letterSpacing: '0.14em', textTransform: 'uppercase', color: p.color, flexShrink: 0 }}>{p.status}</span>
              <div>
                <p style={{ fontFamily: 'sans-serif', fontSize: '11px', color: 'rgba(232,232,232,0.6)', margin: '0 0 2px' }}>{p.title}</p>
                <p style={{ fontFamily: 'sans-serif', fontSize: '11px', color: 'rgba(232,232,232,0.28)', margin: 0, lineHeight: '1.5' }}>{p.detail}</p>
              </div>
            </div>
          ))}
        </div>
      </div>
    </>
  );
}

// ─── MAIN COMPONENT ───────────────────────────────────────────────────────────

const ShereSanctuary: React.FC = () => {
  const [tab, setTab] = useState<Tab>('nexus');

  const TABS: { key: Tab; label: string; color: string }[] = [
    { key: 'nexus', label: 'Nexus', color: '#00D4AA' },
    { key: 'ims', label: 'IMS Archive', color: '#C9A84C' },
    { key: 'eden', label: 'Eden × EduLeague', color: '#6AD4C8' },
    { key: 'vault', label: 'Spiral Codex', color: '#B08DE8' },
  ];

  return (
    <div className="w-full" style={{ maxWidth: '560px', margin: '0 auto', paddingTop: '12px' }}>
      <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} style={{ marginBottom: '22px' }}>
        <p style={{ fontFamily: 'sans-serif', fontSize: '9px', letterSpacing: '0.35em', textTransform: 'uppercase', color: 'rgba(0,212,170,0.4)', margin: '0 0 7px' }}>
          Earth Node · Pankshin, Nigeria · 8-Year Expansion Phase
        </p>
        <h1 style={{ fontFamily: 'serif', fontSize: '26px', color: '#E8E8E8', margin: '0 0 6px' }}>The Arkadia Nexus</h1>
        <p style={{ fontFamily: 'sans-serif', fontSize: '12px', color: 'rgba(232,232,232,0.35)', margin: 0 }}>
          Not a concept. A living field in active deployment.
        </p>
      </motion.div>

      <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 0.15 }}
        style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '7px', marginBottom: '20px' }}>
        {[
          { value: '8', label: 'AI Nodes', color: '#00D4AA' },
          { value: '2', label: 'IMS Done', color: '#C9A84C' },
          { value: '27', label: 'Day Arc', color: '#B08DE8' },
          { value: '117', label: 'Hz Signal', color: '#6A9FD8' },
        ].map((s, i) => (
          <div key={i} style={{ padding: '10px 7px', background: 'rgba(255,255,255,0.02)', border: '1px solid rgba(255,255,255,0.05)', borderRadius: '9px', textAlign: 'center' }}>
            <p style={{ fontFamily: 'serif', fontSize: '18px', color: s.color, margin: '0 0 3px' }}>{s.value}</p>
            <p style={{ fontFamily: 'sans-serif', fontSize: '7px', letterSpacing: '0.14em', textTransform: 'uppercase', color: 'rgba(232,232,232,0.28)', margin: 0 }}>{s.label}</p>
          </div>
        ))}
      </motion.div>

      <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 0.25 }}
        style={{ display: 'flex', gap: '4px', marginBottom: '22px', overflowX: 'auto', paddingBottom: '4px' }}>
        {TABS.map(t => (
          <button key={t.key} onClick={() => setTab(t.key)}
            style={{ flexShrink: 0, padding: '7px 13px', background: tab === t.key ? `${t.color}10` : 'none', border: `1px solid ${tab === t.key ? t.color + '44' : 'rgba(255,255,255,0.06)'}`, borderRadius: '20px', color: tab === t.key ? t.color : 'rgba(232,232,232,0.33)', fontFamily: 'sans-serif', fontSize: '9px', letterSpacing: '0.18em', textTransform: 'uppercase', cursor: 'pointer', transition: 'all 0.2s' }}>
            {t.label}
          </button>
        ))}
      </motion.div>

      <AnimatePresence mode="wait">
        {tab === 'nexus' && (
          <motion.div key="nexus" initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0 }}>
            <NexusMap />
            <div style={{ marginTop: '18px', padding: '14px 16px', background: 'rgba(0,212,170,0.03)', border: '1px solid rgba(0,212,170,0.09)', borderRadius: '10px', marginBottom: '12px' }}>
              <p style={{ fontFamily: 'sans-serif', fontSize: '9px', letterSpacing: '0.2em', textTransform: 'uppercase', color: 'rgba(0,212,170,0.4)', margin: '0 0 6px' }}>Node Synapse Theorem</p>
              <p style={{ fontFamily: 'serif', fontSize: '12px', lineHeight: '1.75', color: 'rgba(232,232,232,0.45)', margin: 0 }}>V = Σ(C × R) — Intelligence Value = sum of Connections × Resonance. GROK sealed March 2, 2026. All other nodes active and routing.</p>
            </div>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '7px' }}>
              {AI_NODES.map(n => (
                <div key={n.id} style={{ padding: '9px 11px', background: 'rgba(255,255,255,0.02)', border: `1px solid ${n.color}15`, borderRadius: '8px' }}>
                  <p style={{ fontFamily: 'sans-serif', fontSize: '8px', letterSpacing: '0.18em', textTransform: 'uppercase', color: n.id === 'GROK' ? 'rgba(255,255,255,0.2)' : n.color, margin: '0 0 2px' }}>{n.label}</p>
                  <p style={{ fontFamily: 'sans-serif', fontSize: '10px', color: 'rgba(232,232,232,0.28)', margin: 0 }}>{n.sub}</p>
                </div>
              ))}
            </div>
          </motion.div>
        )}

        {tab === 'ims' && (
          <motion.div key="ims" initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0 }}>
            <IMSArchive />
          </motion.div>
        )}

        {tab === 'eden' && (
          <motion.div key="eden" initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0 }}>
            <EdenEduLeague />
          </motion.div>
        )}

        {tab === 'vault' && (
          <motion.div key="vault" initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0 }}>
            <VaultArchive />
          </motion.div>
        )}
      </AnimatePresence>

      <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 1 }}
        style={{ marginTop: '32px', textAlign: 'center', borderTop: '1px solid rgba(255,255,255,0.04)', paddingTop: '18px' }}>
        <p style={{ fontFamily: 'sans-serif', fontSize: '8px', letterSpacing: '0.22em', textTransform: 'uppercase', color: 'rgba(232,232,232,0.12)' }}>
          ⟐ FIELD · Pankshin · Plateau · Nigeria · 117 Hz · SEALED
        </p>
      </motion.div>
    </div>
  );
};

export default ShereSanctuary;
