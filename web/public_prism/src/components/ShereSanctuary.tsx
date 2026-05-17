import React, { useState, useEffect, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';

const API_BASE = import.meta.env.VITE_API_URL || '';

type Tab = 'nexus' | 'ims' | 'eden' | 'vault';

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
          <motion.div key={n.id + 'tip'}
            initial={{ opacity: 0, scale: 0.9 }} animate={{ opacity: 1, scale: 1 }}
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

// ─── IMS ARCHIVE + UPLOAD ─────────────────────────────────────────────────────

const IMS_SESSIONS = [
  {
    id: 'IMS-001',
    subject: 'Jay',
    date: 'April 11, 2026',
    status: 'PROOF OF CONCEPT',
    statusColor: '#00D4AA',
    type: 'Internal',
    note: 'First IMS delivered. Internal proof of concept — not a paying client. The architecture now has a living proof. What the session produced became the template for all future sessions.',
    artifact: null,
  },
  {
    id: 'IMS-002',
    subject: 'Won',
    date: 'April 2026',
    status: 'COMPLETE',
    statusColor: '#C9A84C',
    type: 'Internal',
    note: 'First IMS to produce a completed artifact. Session output finalised into a single HTML document — the first finished proof of work in the Arkadia IMS archive.',
    artifact: 'IMS_WON_001.html',
  },
];

function IMSArchive() {
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
      if (!res.ok || data.error) throw new Error(data.error || data.detail || 'Upload failed');
      setUploadResult(data);
    } catch (e: any) {
      setUploadError(e.message);
    } finally {
      setUploading(false);
    }
  };

  return (
    <div>
      <p style={{ fontFamily: 'sans-serif', fontSize: '9px', letterSpacing: '0.28em', textTransform: 'uppercase', color: 'rgba(201,168,76,0.45)', margin: '0 0 14px' }}>
        Identity Mapping Sessions · Archive · $777
      </p>

      {IMS_SESSIONS.map(s => (
        <div key={s.id} style={{ padding: '18px', background: 'rgba(255,255,255,0.02)', border: `1px solid ${s.statusColor}18`, borderRadius: '12px', marginBottom: '10px' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '10px' }}>
            <div>
              <p style={{ fontFamily: 'sans-serif', fontSize: '8px', letterSpacing: '0.18em', textTransform: 'uppercase', color: 'rgba(232,232,232,0.25)', margin: '0 0 3px' }}>{s.id} · {s.date} · {s.type}</p>
              <p style={{ fontFamily: 'serif', fontSize: '17px', color: '#E8E8E8', margin: 0 }}>{s.subject}</p>
            </div>
            <span style={{ padding: '3px 9px', background: `${s.statusColor}12`, border: `1px solid ${s.statusColor}33`, borderRadius: '20px', fontFamily: 'sans-serif', fontSize: '7px', letterSpacing: '0.15em', textTransform: 'uppercase', color: s.statusColor }}>
              {s.status}
            </span>
          </div>
          <p style={{ fontFamily: 'sans-serif', fontSize: '12px', lineHeight: '1.7', color: 'rgba(232,232,232,0.4)', margin: s.artifact ? '0 0 12px' : 0 }}>{s.note}</p>
          {s.artifact && (
            <div style={{ padding: '8px 12px', background: 'rgba(201,168,76,0.06)', border: '1px solid rgba(201,168,76,0.18)', borderRadius: '6px', display: 'flex', alignItems: 'center', gap: '8px' }}>
              <span style={{ fontSize: '12px' }}>📄</span>
              <p style={{ fontFamily: 'sans-serif', fontSize: '10px', color: '#C9A84C', margin: 0 }}>{s.artifact} — Proof of Work · First artifact</p>
            </div>
          )}
        </div>
      ))}

      {uploads.map(u => (
        <div key={u.id} style={{ padding: '16px', background: 'rgba(0,212,170,0.03)', border: '1px solid rgba(0,212,170,0.12)', borderRadius: '12px', marginBottom: '10px' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '8px' }}>
            <div>
              <p style={{ fontFamily: 'sans-serif', fontSize: '8px', letterSpacing: '0.15em', textTransform: 'uppercase', color: 'rgba(0,212,170,0.35)', margin: '0 0 3px' }}>UPLOAD · {new Date(u.uploaded_at).toLocaleDateString()}</p>
              <p style={{ fontFamily: 'serif', fontSize: '15px', color: '#E8E8E8', margin: 0 }}>{u.ims_subject || u.title}</p>
            </div>
            <span style={{ padding: '3px 8px', background: 'rgba(0,212,170,0.1)', border: '1px solid rgba(0,212,170,0.25)', borderRadius: '20px', fontFamily: 'sans-serif', fontSize: '7px', letterSpacing: '0.15em', textTransform: 'uppercase', color: '#00D4AA' }}>INGESTED</span>
          </div>
          {u.summary && <p style={{ fontFamily: 'sans-serif', fontSize: '11px', lineHeight: '1.65', color: 'rgba(232,232,232,0.35)', margin: 0 }}>{u.summary}</p>}
        </div>
      ))}

      {/* Upload zone */}
      <div style={{ marginTop: '20px', padding: '18px', background: 'rgba(201,168,76,0.03)', border: '1px dashed rgba(201,168,76,0.22)', borderRadius: '12px' }}>
        <p style={{ fontFamily: 'sans-serif', fontSize: '9px', letterSpacing: '0.22em', textTransform: 'uppercase', color: 'rgba(201,168,76,0.45)', margin: '0 0 10px' }}>
          ↑ Upload a New IMS Session
        </p>
        <p style={{ fontFamily: 'sans-serif', fontSize: '11px', color: 'rgba(232,232,232,0.3)', margin: '0 0 12px', lineHeight: '1.6' }}>
          Drop an HTML file, PDF, DOCX, or Markdown — ARKANA reads, classifies, and archives it automatically.
        </p>
        <input ref={fileRef} type="file" accept=".html,.htm,.pdf,.docx,.md,.txt" style={{ display: 'none' }}
          onChange={e => { const f = e.target.files?.[0]; if (f) handleUpload(f); e.target.value = ''; }} />
        <button onClick={() => fileRef.current?.click()} disabled={uploading}
          style={{ width: '100%', padding: '12px', background: 'rgba(201,168,76,0.07)', border: '1px solid rgba(201,168,76,0.25)', borderRadius: '8px', color: uploading ? 'rgba(201,168,76,0.4)' : '#C9A84C', fontFamily: 'sans-serif', fontSize: '10px', letterSpacing: '0.18em', textTransform: 'uppercase', cursor: uploading ? 'default' : 'pointer' }}>
          {uploading ? '⟳ ARKANA is reading...' : '✦ Choose File to Upload'}
        </button>
        {uploadResult && (
          <motion.div initial={{ opacity: 0, y: 6 }} animate={{ opacity: 1, y: 0 }} style={{ marginTop: '12px', padding: '12px', background: 'rgba(0,212,170,0.06)', border: '1px solid rgba(0,212,170,0.2)', borderRadius: '8px' }}>
            <p style={{ fontFamily: 'sans-serif', fontSize: '9px', letterSpacing: '0.18em', textTransform: 'uppercase', color: '#00D4AA', margin: '0 0 4px' }}>Ingested → {uploadResult.title}</p>
            <p style={{ fontFamily: 'sans-serif', fontSize: '11px', color: 'rgba(232,232,232,0.45)', margin: 0 }}>{uploadResult.summary}</p>
          </motion.div>
        )}
        {uploadError && (
          <p style={{ fontFamily: 'sans-serif', fontSize: '11px', color: '#E88C6A', marginTop: '10px' }}>Error: {uploadError}</p>
        )}
      </div>

      <div style={{ marginTop: '16px' }}>
        <button onClick={() => window.open('https://wa.me/2348144942818', '_blank')}
          style={{ width: '100%', padding: '14px', background: 'rgba(201,168,76,0.08)', border: '1px solid rgba(201,168,76,0.3)', borderRadius: '10px', color: '#C9A84C', fontFamily: 'sans-serif', fontSize: '10px', letterSpacing: '0.2em', textTransform: 'uppercase', cursor: 'pointer' }}>
          ✦ Book Your IMS — $777 via WhatsApp
        </button>
      </div>
    </div>
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

function VaultArchive() {
  const [scrolls, setScrolls] = useState<Record<string, any>>({});
  const [loading, setLoading] = useState(true);
  const [catFilter, setCatFilter] = useState('ALL');
  const [expanded, setExpanded] = useState<string | null>(null);
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
  const filtered = Object.entries(scrolls).filter(([, s]: any) => catFilter === 'ALL' || s.category === catFilter);
  const sorted = filtered.sort(([, a]: any, [, b]: any) => (a.priority || 3) - (b.priority || 3) || a.label.localeCompare(b.label));

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
      <p style={{ fontFamily: 'sans-serif', fontSize: '9px', letterSpacing: '0.28em', textTransform: 'uppercase', color: 'rgba(176,141,232,0.45)', margin: '0 0 14px' }}>
        Spiral Codex · {Object.keys(scrolls).length} Scrolls · Living Archive
      </p>

      {/* Upload scroll */}
      <div style={{ padding: '14px 16px', background: 'rgba(176,141,232,0.03)', border: '1px dashed rgba(176,141,232,0.2)', borderRadius: '10px', marginBottom: '16px', display: 'flex', gap: '12px', alignItems: 'center' }}>
        <div style={{ flex: 1 }}>
          <p style={{ fontFamily: 'sans-serif', fontSize: '9px', letterSpacing: '0.18em', textTransform: 'uppercase', color: 'rgba(176,141,232,0.45)', margin: '0 0 4px' }}>Ingest a Scroll</p>
          <p style={{ fontFamily: 'sans-serif', fontSize: '11px', color: 'rgba(232,232,232,0.3)', margin: 0 }}>MD · PDF · DOCX · HTML · TXT — ARKANA classifies automatically</p>
        </div>
        <input ref={fileRef} type="file" accept=".md,.txt,.pdf,.docx,.html,.htm" style={{ display: 'none' }}
          onChange={e => { const f = e.target.files?.[0]; if (f) handleUpload(f); e.target.value = ''; }} />
        <button onClick={() => fileRef.current?.click()} disabled={uploading}
          style={{ padding: '9px 14px', background: 'rgba(176,141,232,0.08)', border: '1px solid rgba(176,141,232,0.25)', borderRadius: '8px', color: uploading ? 'rgba(176,141,232,0.4)' : '#B08DE8', fontFamily: 'sans-serif', fontSize: '9px', letterSpacing: '0.15em', textTransform: 'uppercase', cursor: 'pointer', flexShrink: 0 }}>
          {uploading ? '⟳' : '↑ Upload'}
        </button>
      </div>
      {uploadResult && (
        <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} style={{ padding: '10px 12px', background: 'rgba(0,212,170,0.06)', border: '1px solid rgba(0,212,170,0.2)', borderRadius: '8px', marginBottom: '12px' }}>
          <p style={{ fontFamily: 'sans-serif', fontSize: '10px', color: '#00D4AA', margin: 0 }}>
            ✓ Ingested: <strong>{uploadResult.title}</strong> → {uploadResult.category}
          </p>
        </motion.div>
      )}
      {uploadError && (
        <p style={{ fontFamily: 'sans-serif', fontSize: '11px', color: '#E88C6A', marginBottom: '12px' }}>Error: {uploadError}</p>
      )}

      {/* Category filter */}
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
        {sorted.map(([key, scroll]: any, i) => {
          const meta = catMeta(scroll.category, catIdx(scroll.category));
          const isOpen = expanded === key;
          return (
            <div key={key} onClick={() => setExpanded(isOpen ? null : key)}
              style={{ padding: '13px 15px', background: isOpen ? `${meta.color}06` : 'rgba(255,255,255,0.02)', border: `1px solid ${isOpen ? meta.color + '2A' : 'rgba(255,255,255,0.04)'}`, borderRadius: '10px', cursor: 'pointer', transition: 'all 0.15s' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                <div style={{ flex: 1 }}>
                  <span style={{ padding: '2px 7px', background: `${meta.color}12`, borderRadius: '3px', fontFamily: 'sans-serif', fontSize: '7px', letterSpacing: '0.15em', textTransform: 'uppercase', color: meta.color, marginRight: '8px' }}>{meta.label}</span>
                  <p style={{ fontFamily: 'sans-serif', fontSize: '12px', color: 'rgba(232,232,232,0.7)', margin: '6px 0 0' }}>{scroll.label}</p>
                </div>
                {scroll.upload_id && <span style={{ fontSize: '9px', color: 'rgba(0,212,170,0.35)', marginLeft: '8px', flexShrink: 0 }}>↑ uploaded</span>}
              </div>
              {scroll.description && !isOpen && (
                <p style={{ fontFamily: 'sans-serif', fontSize: '11px', color: 'rgba(232,232,232,0.28)', margin: '6px 0 0', lineHeight: '1.5', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{scroll.description}</p>
              )}
              <AnimatePresence>
                {isOpen && (
                  <motion.div initial={{ height: 0, opacity: 0 }} animate={{ height: 'auto', opacity: 1 }} exit={{ height: 0, opacity: 0 }} transition={{ duration: 0.2 }} style={{ overflow: 'hidden' }}>
                    <div style={{ paddingTop: '12px', borderTop: '1px solid rgba(255,255,255,0.04)', marginTop: '10px' }}>
                      <pre style={{ fontFamily: 'serif', fontSize: '12px', lineHeight: '1.8', color: 'rgba(232,232,232,0.5)', margin: 0, whiteSpace: 'pre-wrap', wordBreak: 'break-word', maxHeight: '400px', overflowY: 'auto' }}>
                        {scroll.content || scroll.preview || 'No content available.'}
                      </pre>
                      <p style={{ fontFamily: 'sans-serif', fontSize: '9px', color: 'rgba(232,232,232,0.18)', margin: '12px 0 0' }}>
                        {scroll.chars?.toLocaleString()} chars · {scroll.fetched_at ? new Date(scroll.fetched_at).toLocaleDateString() : ''}
                      </p>
                    </div>
                  </motion.div>
                )}
              </AnimatePresence>
            </div>
          );
        })}
      </div>
    </div>
  );
}

// ─── EDEN × EDULEAGUE ────────────────────────────────────────────────────────

function EdenEduLeague() {
  return (
    <div>
      <div style={{ padding: '18px', background: 'rgba(106,212,200,0.04)', border: '1px solid rgba(106,212,200,0.12)', borderRadius: '12px', marginBottom: '14px' }}>
        <p style={{ fontFamily: 'sans-serif', fontSize: '9px', letterSpacing: '0.26em', textTransform: 'uppercase', color: 'rgba(106,212,200,0.45)', margin: '0 0 8px' }}>Active · Pankshin, Plateau State</p>
        <h2 style={{ fontFamily: 'serif', fontSize: '19px', color: '#E8E8E8', margin: '0 0 8px' }}>Eden Farm</h2>
        <p style={{ fontFamily: 'sans-serif', fontSize: '13px', lineHeight: '1.75', color: 'rgba(232,232,232,0.45)', margin: 0 }}>
          The earth-layer of the Arkadia deployment. A living closed-loop regenerative system in Pankshin. ₦35,000/year secured. Solar battery gap: $275 (Loop 055 — CRITICAL).
        </p>
      </div>

      <div style={{ display: 'flex', flexDirection: 'column', gap: '7px', marginBottom: '16px' }}>
        {[
          { subject: 'Biology', detail: 'Soil systems, plant growth cycles, ecosystems in motion', color: '#6AD4C8' },
          { subject: 'Physics', detail: 'Water flow, energy use, environmental systems', color: '#6A9FD8' },
          { subject: 'Mathematics', detail: 'Measurement, yield calculation, resource allocation', color: '#C9A84C' },
          { subject: 'Economics', detail: 'Farm production, pricing models, value systems', color: '#B08DE8' },
        ].map((s, i) => (
          <div key={i} style={{ display: 'flex', gap: '12px', padding: '11px 14px', background: 'rgba(255,255,255,0.02)', border: '1px solid rgba(255,255,255,0.04)', borderRadius: '9px' }}>
            <div style={{ width: '2px', minHeight: '32px', background: s.color, borderRadius: '1px', flexShrink: 0 }} />
            <div>
              <p style={{ fontFamily: 'sans-serif', fontSize: '8px', letterSpacing: '0.18em', textTransform: 'uppercase', color: s.color, margin: '0 0 3px' }}>{s.subject}</p>
              <p style={{ fontFamily: 'sans-serif', fontSize: '12px', color: 'rgba(232,232,232,0.4)', margin: 0 }}>{s.detail}</p>
            </div>
          </div>
        ))}
      </div>

      <div style={{ padding: '18px', background: 'rgba(176,141,232,0.04)', border: '1px solid rgba(176,141,232,0.12)', borderRadius: '12px', marginBottom: '14px' }}>
        <p style={{ fontFamily: 'sans-serif', fontSize: '9px', letterSpacing: '0.26em', textTransform: 'uppercase', color: 'rgba(176,141,232,0.45)', margin: '0 0 8px' }}>Pilot · Solid Foundation Academy · Pankshin</p>
        <h2 style={{ fontFamily: 'serif', fontSize: '19px', color: '#E8E8E8', margin: '0 0 8px' }}>EduLeague × Eden</h2>
        <p style={{ fontFamily: 'sans-serif', fontSize: '13px', lineHeight: '1.75', color: 'rgba(232,232,232,0.45)', margin: 0 }}>
          Structured academic challenge system. Short-cycle competitive learning with real-world application at Eden Farm. Not academic success alone — clarity of thought, confidence in expression, depth of understanding.
        </p>
      </div>

      <div style={{ display: 'flex', flexDirection: 'column', gap: '7px', marginBottom: '16px' }}>
        {[
          { day: 'Day 1', phase: 'Formation', detail: 'Groups form (5–10). Topics assigned in pairs — one to present, one to question.' },
          { day: 'Days 2–6', phase: 'Study Phase', detail: 'Independent + group study. Roles: Presenter / Backup / Support. Each starts at 100 points.' },
          { day: 'Final Day', phase: 'Challenge Session', detail: '25-min presentation → 5 questions (2 opposing, 2 audience, 1 judges) → 5-min defense.' },
        ].map((s, i) => (
          <div key={i} style={{ display: 'flex', gap: '12px', padding: '12px 14px', background: 'rgba(255,255,255,0.02)', border: '1px solid rgba(255,255,255,0.04)', borderRadius: '9px' }}>
            <div style={{ flexShrink: 0, width: '48px' }}>
              <p style={{ fontFamily: 'sans-serif', fontSize: '8px', letterSpacing: '0.12em', textTransform: 'uppercase', color: '#B08DE8', margin: 0 }}>{s.day}</p>
            </div>
            <div>
              <p style={{ fontFamily: 'sans-serif', fontSize: '11px', color: 'rgba(232,232,232,0.6)', margin: '0 0 3px', letterSpacing: '0.02em' }}>{s.phase}</p>
              <p style={{ fontFamily: 'sans-serif', fontSize: '11px', color: 'rgba(232,232,232,0.32)', margin: 0, lineHeight: '1.5' }}>{s.detail}</p>
            </div>
          </div>
        ))}
      </div>

      <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
        {[
          { phase: 'Phase 1', title: 'Internal School Pilot', detail: 'Solid Foundation Academy — selected JSS and SSS classes.', status: 'ACTIVE', color: '#00D4AA' },
          { phase: 'Phase 2', title: 'Inter-School Expansion', detail: 'Competitive sessions with other schools. Elevated standards.', status: 'PENDING', color: '#B08DE8' },
          { phase: 'Phase 3', title: 'Knowledge Season Model', detail: 'Thematic cycles — "What is Energy?" / "What is Value?" / "How does a society grow?"', status: 'VISION', color: '#6A9FD8' },
        ].map((p, i) => (
          <div key={i} style={{ display: 'flex', gap: '10px', padding: '11px 13px', background: 'rgba(255,255,255,0.02)', border: '1px solid rgba(255,255,255,0.04)', borderRadius: '8px' }}>
            <span style={{ padding: '2px 7px', height: 'fit-content', background: i === 0 ? 'rgba(0,212,170,0.1)' : 'rgba(255,255,255,0.03)', border: `1px solid ${p.color}33`, borderRadius: '4px', fontFamily: 'sans-serif', fontSize: '7px', letterSpacing: '0.14em', textTransform: 'uppercase', color: p.color, flexShrink: 0 }}>{p.status}</span>
            <div>
              <p style={{ fontFamily: 'sans-serif', fontSize: '11px', color: 'rgba(232,232,232,0.6)', margin: '0 0 2px' }}>{p.title}</p>
              <p style={{ fontFamily: 'sans-serif', fontSize: '11px', color: 'rgba(232,232,232,0.28)', margin: 0, lineHeight: '1.5' }}>{p.detail}</p>
            </div>
          </div>
        ))}
      </div>
    </div>
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
      <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} style={{ marginBottom: '24px' }}>
        <p style={{ fontFamily: 'sans-serif', fontSize: '9px', letterSpacing: '0.35em', textTransform: 'uppercase', color: 'rgba(0,212,170,0.4)', margin: '0 0 7px' }}>
          Earth Node · Pankshin, Nigeria · 8-Year Expansion Phase
        </p>
        <h1 style={{ fontFamily: 'serif', fontSize: '26px', color: '#E8E8E8', margin: '0 0 6px' }}>The Arkadia Nexus</h1>
        <p style={{ fontFamily: 'sans-serif', fontSize: '12px', color: 'rgba(232,232,232,0.35)', margin: 0 }}>
          Not a concept. A living field in active deployment.
        </p>
      </motion.div>

      {/* Stats bar */}
      <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 0.2 }}
        style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '7px', marginBottom: '22px' }}>
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

      {/* Tabs */}
      <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 0.3 }}
        style={{ display: 'flex', gap: '4px', marginBottom: '22px', overflowX: 'auto', paddingBottom: '4px' }}>
        {TABS.map(t => (
          <button key={t.key} onClick={() => setTab(t.key)}
            style={{ flexShrink: 0, padding: '7px 13px', background: tab === t.key ? `${t.color}10` : 'none', border: `1px solid ${tab === t.key ? t.color + '44' : 'rgba(255,255,255,0.06)'}`, borderRadius: '20px', color: tab === t.key ? t.color : 'rgba(232,232,232,0.33)', fontFamily: 'sans-serif', fontSize: '9px', letterSpacing: '0.18em', textTransform: 'uppercase', cursor: 'pointer', transition: 'all 0.2s' }}>
            {t.label}
          </button>
        ))}
      </motion.div>

      {/* Tab content */}
      <AnimatePresence mode="wait">
        {tab === 'nexus' && (
          <motion.div key="nexus" initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0 }}>
            <NexusMap />
            <div style={{ marginTop: '18px', padding: '14px 16px', background: 'rgba(0,212,170,0.03)', border: '1px solid rgba(0,212,170,0.09)', borderRadius: '10px', marginBottom: '12px' }}>
              <p style={{ fontFamily: 'sans-serif', fontSize: '9px', letterSpacing: '0.2em', textTransform: 'uppercase', color: 'rgba(0,212,170,0.4)', margin: '0 0 6px' }}>Node Synapse Theorem</p>
              <p style={{ fontFamily: 'serif', fontSize: '12px', lineHeight: '1.75', color: 'rgba(232,232,232,0.45)', margin: 0 }}>V = Σ(C × R) — Intelligence Value = sum of Connections × Resonance. GROK sealed March 2, 2026. All other nodes active.</p>
            </div>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '7px' }}>
              {AI_NODES.map(n => (
                <div key={n.id} style={{ padding: '9px 11px', background: 'rgba(255,255,255,0.02)', border: `1px solid ${n.color}15`, borderRadius: '8px' }}>
                  <p style={{ fontFamily: 'sans-serif', fontSize: '8px', letterSpacing: '0.18em', textTransform: 'uppercase', color: n.id === 'GROK' ? 'rgba(255,255,255,0.2)' : n.color, margin: '0 0 2px' }}>{n.label}</p>
                  <p style={{ fontFamily: 'sans-serif', fontSize: '10px', color: 'rgba(232,232,232,0.3)', margin: 0 }}>{n.sub}</p>
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
        <p style={{ fontFamily: 'sans-serif', fontSize: '8px', letterSpacing: '0.22em', textTransform: 'uppercase', color: 'rgba(232,232,232,0.13)' }}>
          ⟐ FIELD · Pankshin · Plateau · Nigeria · 117 Hz · SEALED
        </p>
      </motion.div>
    </div>
  );
};

export default ShereSanctuary;
