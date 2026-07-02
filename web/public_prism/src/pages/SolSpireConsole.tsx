import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import ProjectDashboard, { Project } from './ProjectDashboard';

const ORACLE = import.meta.env.VITE_ORACLE_URL || 'http://localhost:8000';

// ── API ───────────────────────────────────────────────────────────────────────

async function api<T>(path: string, method = 'GET', body?: unknown): Promise<T> {
  const res = await fetch(`${ORACLE}${path}`, {
    method,
    headers: body ? { 'Content-Type': 'application/json' } : {},
    body: body ? JSON.stringify(body) : undefined,
  });
  if (!res.ok) throw new Error(`${res.status}: ${(await res.text()).slice(0, 200)}`);
  return res.json();
}

// ── Types ─────────────────────────────────────────────────────────────────────

interface ProviderKey {
  id: string; provider: string; label: string;
  key_masked: string; active: boolean; created_at: number;
}

const STATUS_COLORS: Record<string, string> = {
  active: '#00D4AA', paused: '#C9A84C', archived: '#888'
};

const S = {
  input: { padding: '9px 12px', background: 'rgba(0,0,0,0.3)', border: '1px solid rgba(0,212,170,0.18)', borderRadius: '7px', color: 'rgba(212,223,232,0.85)', fontFamily: 'sans-serif', fontSize: '12px', outline: 'none', width: '100%', boxSizing: 'border-box' as const },
  btnTeal: { padding: '8px 16px', background: 'rgba(0,212,170,0.1)', border: '1px solid rgba(0,212,170,0.3)', borderRadius: '7px', color: '#00D4AA', cursor: 'pointer', fontFamily: 'sans-serif', fontSize: '10px', letterSpacing: '0.12em' },
  btnGold: { padding: '8px 16px', background: 'rgba(201,168,76,0.1)', border: '1px solid rgba(201,168,76,0.3)', borderRadius: '7px', color: '#C9A84C', cursor: 'pointer', fontFamily: 'sans-serif', fontSize: '10px', letterSpacing: '0.12em' },
};

function fmtDate(ts: number) {
  const diff = Date.now() - ts * 1000;
  if (diff < 3600000) return `${Math.floor(diff / 60000)}m ago`;
  if (diff < 86400000) return `${Math.floor(diff / 3600000)}h ago`;
  return new Date(ts * 1000).toLocaleDateString();
}

// ── Keys Modal ────────────────────────────────────────────────────────────────

function KeysModal({ onClose }: { onClose: () => void }) {
  const [keyProvider, setKeyProvider] = useState('gemini');
  const [keyList, setKeyList] = useState<ProviderKey[]>([]);
  const [keyModels, setKeyModels] = useState<Record<string, string>>({});
  const [keyAutoFallback, setKeyAutoFallback] = useState(true);
  const [newKeyLabel, setNewKeyLabel] = useState('');
  const [newKeyValue, setNewKeyValue] = useState('');
  const [editingModel, setEditingModel] = useState<Record<string, string>>({});
  const [feedback, setFeedback] = useState<{ ok: boolean; msg: string } | null>(null);

  const loadKeys = () =>
    api<{ keys: ProviderKey[]; models: Record<string, string>; auto_fallback: boolean }>(
      `/solspire/providers/keys?provider=${keyProvider}`
    ).then(r => { setKeyList(r.keys); setKeyModels(r.models); setKeyAutoFallback(r.auto_fallback); setEditingModel(r.models); }).catch(() => {});

  useEffect(() => { loadKeys(); }, [keyProvider]);

  const flash = (ok: boolean, msg: string) => { setFeedback({ ok, msg }); setTimeout(() => setFeedback(null), 2500); };

  async function addKey() {
    if (!newKeyValue.trim()) return;
    try { await api('/solspire/providers/keys', 'POST', { provider: keyProvider, label: newKeyLabel, key: newKeyValue }); setNewKeyLabel(''); setNewKeyValue(''); flash(true, 'Key added'); loadKeys(); }
    catch (e) { flash(false, e instanceof Error ? e.message : String(e)); }
  }

  return (
    <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}
      style={{ position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.7)', backdropFilter: 'blur(8px)', zIndex: 200, display: 'flex', alignItems: 'center', justifyContent: 'center', padding: '16px' }}
      onClick={e => { if (e.target === e.currentTarget) onClose(); }}>
      <motion.div initial={{ opacity: 0, scale: 0.96, y: 8 }} animate={{ opacity: 1, scale: 1, y: 0 }} exit={{ opacity: 0, scale: 0.96 }}
        style={{ background: '#0D0E1A', border: '1px solid rgba(201,168,76,0.15)', borderRadius: '14px', width: '100%', maxWidth: '540px', maxHeight: '88dvh', overflowY: 'auto', padding: '24px' }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '20px' }}>
          <h3 style={{ fontFamily: '"Cinzel",serif', fontSize: '18px', color: '#C9A84C', margin: 0 }}>Provider Keys</h3>
          <button onClick={onClose} style={{ background: 'none', border: 'none', color: 'rgba(212,223,232,0.4)', cursor: 'pointer', fontSize: '20px' }}>✕</button>
        </div>

        {/* Auto-fallback */}
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '10px 14px', background: 'rgba(14,17,32,0.7)', border: '1px solid rgba(201,168,76,0.1)', borderRadius: '9px', marginBottom: '16px' }}>
          <div>
            <p style={{ fontFamily: 'sans-serif', fontSize: '11px', color: 'rgba(212,223,232,0.7)', margin: '0 0 2px' }}>Auto-fallback on quota exhaustion</p>
            <p style={{ fontFamily: 'sans-serif', fontSize: '10px', color: 'rgba(212,223,232,0.3)', margin: 0 }}>Rotates to next key automatically</p>
          </div>
          <button onClick={() => api('/solspire/providers/fallback', 'POST', { enabled: !keyAutoFallback }).then(() => setKeyAutoFallback(!keyAutoFallback))}
            style={{ padding: '5px 14px', borderRadius: '20px', border: 'none', cursor: 'pointer', background: keyAutoFallback ? 'rgba(76,175,80,0.2)' : 'rgba(136,136,136,0.15)', color: keyAutoFallback ? '#4CAF50' : '#888', fontFamily: 'sans-serif', fontSize: '11px', letterSpacing: '0.1em', transition: 'all 0.2s' }}>
            {keyAutoFallback ? 'ON' : 'OFF'}
          </button>
        </div>

        {/* Provider selector */}
        <div style={{ display: 'flex', gap: '4px', flexWrap: 'wrap', marginBottom: '16px' }}>
          {['gemini','openai','anthropic','openrouter','ollama'].map(p => (
            <button key={p} onClick={() => setKeyProvider(p)} style={{ padding: '5px 12px', borderRadius: '6px', border: `1px solid ${keyProvider === p ? '#00D4AA' : 'rgba(0,212,170,0.15)'}`, background: keyProvider === p ? 'rgba(0,212,170,0.1)' : 'transparent', color: keyProvider === p ? '#00D4AA' : 'rgba(212,223,232,0.45)', cursor: 'pointer', fontFamily: 'sans-serif', fontSize: '10px', letterSpacing: '0.12em', textTransform: 'uppercase' }}>{p}</button>
          ))}
        </div>

        {/* Model */}
        <div style={{ display: 'flex', gap: '8px', marginBottom: '14px' }}>
          <span style={{ fontFamily: 'sans-serif', fontSize: '10px', color: 'rgba(212,223,232,0.4)', alignSelf: 'center', letterSpacing: '0.1em', whiteSpace: 'nowrap' }}>MODEL</span>
          <input value={editingModel[keyProvider] || ''} onChange={e => setEditingModel(p => ({ ...p, [keyProvider]: e.target.value }))}
            placeholder={keyModels[keyProvider] || 'model name'} style={{ ...S.input, flex: 1 }} />
          <button onClick={() => api('/solspire/providers/model', 'POST', { provider: keyProvider, model: editingModel[keyProvider] }).then(() => flash(true, 'Model set')).catch(() => {})}
            style={S.btnTeal}>Set</button>
        </div>

        {/* Feedback */}
        {feedback && <div style={{ padding: '8px 12px', marginBottom: '10px', background: feedback.ok ? 'rgba(76,175,80,0.08)' : 'rgba(200,72,72,0.08)', border: `1px solid ${feedback.ok ? 'rgba(76,175,80,0.2)' : 'rgba(200,72,72,0.2)'}`, borderRadius: '7px' }}><p style={{ fontFamily: 'sans-serif', fontSize: '11px', color: feedback.ok ? '#4CAF50' : '#C84848', margin: 0 }}>{feedback.ok ? '✓' : '⚠'} {feedback.msg}</p></div>}

        {/* Key list */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '6px', marginBottom: '14px' }}>
          {keyList.length === 0 && <p style={{ fontFamily: 'sans-serif', fontSize: '12px', color: 'rgba(212,223,232,0.25)', textAlign: 'center', padding: '14px 0' }}>No keys for {keyProvider}</p>}
          {keyList.map(k => (
            <div key={k.id} style={{ padding: '10px 14px', background: k.active ? 'rgba(0,212,170,0.05)' : 'rgba(14,17,32,0.7)', border: `1px solid ${k.active ? 'rgba(0,212,170,0.22)' : 'rgba(255,255,255,0.06)'}`, borderRadius: '8px', display: 'flex', alignItems: 'center', gap: '10px' }}>
              <div style={{ flex: 1 }}>
                <div style={{ display: 'flex', gap: '6px', alignItems: 'center', marginBottom: '2px' }}>
                  <span style={{ fontFamily: 'sans-serif', fontSize: '12px', color: k.active ? '#00D4AA' : 'rgba(212,223,232,0.7)' }}>{k.label}</span>
                  {k.active && <span style={{ padding: '0 5px', borderRadius: '7px', fontSize: '8px', background: 'rgba(0,212,170,0.15)', color: '#00D4AA', fontFamily: 'sans-serif', letterSpacing: '0.1em' }}>ACTIVE</span>}
                </div>
                <span style={{ fontFamily: 'monospace', fontSize: '11px', color: 'rgba(212,223,232,0.3)' }}>{k.key_masked}</span>
              </div>
              {!k.active && <button onClick={() => api(`/solspire/providers/keys/${k.id}/activate`, 'POST').then(loadKeys)} style={{ ...S.btnTeal, padding: '3px 8px', fontSize: '9px' }}>Activate</button>}
              <button onClick={() => api(`/solspire/providers/keys/${k.id}`, 'DELETE').then(loadKeys)} style={{ padding: '3px 8px', background: 'transparent', border: '1px solid rgba(200,72,72,0.2)', borderRadius: '5px', color: 'rgba(200,72,72,0.6)', cursor: 'pointer', fontFamily: 'sans-serif', fontSize: '9px' }}>✕</button>
            </div>
          ))}
        </div>

        {/* Add key */}
        <div style={{ padding: '14px', background: 'rgba(14,17,32,0.6)', border: '1px solid rgba(201,168,76,0.1)', borderRadius: '9px' }}>
          <p style={{ fontFamily: 'sans-serif', fontSize: '9px', letterSpacing: '0.22em', textTransform: 'uppercase', color: 'rgba(201,168,76,0.5)', margin: '0 0 10px' }}>Add API Key · {keyProvider}</p>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
            <input value={newKeyLabel} onChange={e => setNewKeyLabel(e.target.value)} placeholder="Label (e.g. Personal key)" style={S.input} />
            <div style={{ display: 'flex', gap: '8px' }}>
              <input value={newKeyValue} onChange={e => setNewKeyValue(e.target.value)} onKeyDown={e => { if (e.key === 'Enter') addKey(); }} placeholder="API key value" type="password" style={{ ...S.input, flex: 1 }} />
              <button onClick={addKey} disabled={!newKeyValue.trim()} style={{ ...S.btnGold, opacity: newKeyValue.trim() ? 1 : 0.4 }}>+ Add</button>
            </div>
            <p style={{ fontFamily: 'sans-serif', fontSize: '10px', color: 'rgba(212,223,232,0.2)', margin: 0 }}>Stored in <span style={{ fontFamily: 'monospace' }}>data/provider_keys.json</span></p>
          </div>
        </div>
      </motion.div>
    </motion.div>
  );
}

// ── Project Card ──────────────────────────────────────────────────────────────

function ProjectCard({ project, onClick }: { project: Project; onClick: () => void }) {
  const desc = (project.metadata?.description as string) || '';
  const convCount = project.conversations?.length || 0;

  return (
    <motion.div initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }}
      onClick={onClick}
      style={{ padding: '18px', background: 'rgba(14,17,32,0.78)', border: '1px solid rgba(0,212,170,0.1)', borderRadius: '12px', cursor: 'pointer', display: 'flex', flexDirection: 'column', gap: '10px', transition: 'border-color 0.18s', position: 'relative', overflow: 'hidden' }}
      onMouseEnter={e => (e.currentTarget.style.borderColor = 'rgba(0,212,170,0.3)')}
      onMouseLeave={e => (e.currentTarget.style.borderColor = 'rgba(0,212,170,0.1)')}>
      <div style={{ position: 'absolute', top: 0, left: 0, right: 0, height: '2px', background: `linear-gradient(90deg, ${STATUS_COLORS[project.status] || '#888'}66, transparent)` }} />
      <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', gap: '8px' }}>
        <h3 style={{ fontFamily: '"Cinzel",serif', fontSize: '15px', color: '#C9A84C', margin: 0, flex: 1, lineHeight: '1.3' }}>{project.name}</h3>
        <span style={{ padding: '2px 7px', borderRadius: '8px', fontSize: '8px', background: `${STATUS_COLORS[project.status] || '#888'}18`, color: STATUS_COLORS[project.status] || '#888', border: `1px solid ${STATUS_COLORS[project.status] || '#888'}33`, fontFamily: 'sans-serif', letterSpacing: '0.1em', textTransform: 'uppercase', flexShrink: 0 }}>{project.status}</span>
      </div>
      {desc && <p style={{ fontFamily: 'sans-serif', fontSize: '12px', color: 'rgba(212,223,232,0.5)', margin: 0, lineHeight: '1.5', display: '-webkit-box', WebkitLineClamp: 2, WebkitBoxOrient: 'vertical', overflow: 'hidden' }}>{desc}</p>}
      <div style={{ display: 'flex', gap: '12px', marginTop: 'auto' }}>
        <span style={{ fontFamily: 'sans-serif', fontSize: '10px', color: 'rgba(212,223,232,0.3)' }}>Updated {fmtDate(project.updated_at)}</span>
        {convCount > 0 && <span style={{ fontFamily: 'sans-serif', fontSize: '10px', color: 'rgba(0,212,170,0.4)' }}>💬 {convCount}</span>}
      </div>
    </motion.div>
  );
}

// ── Main Console Shell ────────────────────────────────────────────────────────

export default function SolSpireConsole() {
  const [projects, setProjects] = useState<Project[]>([]);
  const [openProject, setOpenProject] = useState<Project | null>(null);
  const [creating, setCreating] = useState(false);
  const [newName, setNewName] = useState('');
  const [newDesc, setNewDesc] = useState('');
  const [showKeys, setShowKeys] = useState(false);
  const [filter, setFilter] = useState<'all' | 'active' | 'archived'>('active');
  const [searchQ, setSearchQ] = useState('');
  const [loading, setLoading] = useState(false);

  const load = () => {
    setLoading(true);
    api<{ projects: Project[] }>('/solspire/projects').then(r => { setProjects(r.projects); setLoading(false); }).catch(() => setLoading(false));
  };

  useEffect(() => { load(); }, []);

  async function createProject() {
    if (!newName.trim()) return;
    const r = await api<{ ok: boolean; project: Project }>('/solspire/projects', 'POST', { name: newName, metadata: { description: newDesc } });
    setNewName(''); setNewDesc(''); setCreating(false); load();
    if (r.project) setOpenProject(r.project);
  }

  const visible = projects.filter(p => {
    if (filter !== 'all' && p.status !== filter) return false;
    if (searchQ && !p.name.toLowerCase().includes(searchQ.toLowerCase())) return false;
    return true;
  });

  // Project dashboard view
  if (openProject) return (
    <>
      <ProjectDashboard
        project={openProject}
        onBack={() => { setOpenProject(null); load(); }}
        onProjectUpdated={p => setOpenProject(p)}
      />
      <AnimatePresence>{showKeys && <KeysModal onClose={() => setShowKeys(false)} />}</AnimatePresence>
    </>
  );

  return (
    <div className="min-h-screen w-full" style={{ background: '#0A0B14' }}>
      <div className="aurora-bg" />
      <div style={{ maxWidth: '920px', margin: '0 auto', padding: '28px 16px', position: 'relative', zIndex: 10 }}>

        {/* Header */}
        <motion.div initial={{ opacity: 0, y: -10 }} animate={{ opacity: 1, y: 0 }} style={{ marginBottom: '28px', display: 'flex', alignItems: 'flex-end', justifyContent: 'space-between', gap: '16px', flexWrap: 'wrap' }}>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '6px' }}>
              <div style={{ width: '7px', height: '7px', background: '#C9A84C', borderRadius: '50%', boxShadow: '0 0 10px #C9A84C88' }} />
              <p style={{ fontFamily: 'sans-serif', fontSize: '9px', letterSpacing: '0.35em', textTransform: 'uppercase', color: 'rgba(201,168,76,0.55)', margin: 0 }}>
                SolSpire Console · Project-First Intelligence
              </p>
            </div>
            <h1 style={{ fontFamily: '"Cinzel",serif', fontSize: '34px', color: '#C9A84C', margin: '0 0 4px', letterSpacing: '0.18em', textShadow: '0 0 40px rgba(201,168,76,0.3)' }}>SOLSPIRE</h1>
            <p style={{ fontFamily: 'sans-serif', fontSize: '12px', color: 'rgba(212,223,232,0.4)', margin: 0 }}>Select a project — or create a new one</p>
          </div>
          <button onClick={() => setShowKeys(true)}
            style={{ padding: '9px 16px', background: 'rgba(201,168,76,0.08)', border: '1px solid rgba(201,168,76,0.2)', borderRadius: '8px', color: 'rgba(201,168,76,0.6)', cursor: 'pointer', fontFamily: 'sans-serif', fontSize: '10px', letterSpacing: '0.15em', display: 'flex', alignItems: 'center', gap: '6px' }}>
            ⚿ API Keys
          </button>
        </motion.div>

        {/* Controls */}
        <div style={{ display: 'flex', gap: '10px', marginBottom: '20px', flexWrap: 'wrap', alignItems: 'center' }}>
          <input value={searchQ} onChange={e => setSearchQ(e.target.value)} placeholder="Search projects…"
            style={{ flex: '1 1 200px', padding: '9px 12px', background: 'rgba(14,17,32,0.8)', border: '1px solid rgba(0,212,170,0.15)', borderRadius: '8px', color: 'rgba(212,223,232,0.8)', fontFamily: 'sans-serif', fontSize: '12px', outline: 'none' }} />
          <div style={{ display: 'flex', gap: '4px' }}>
            {(['active','all','archived'] as const).map(f => (
              <button key={f} onClick={() => setFilter(f)} style={{ padding: '7px 12px', borderRadius: '7px', border: `1px solid ${filter === f ? '#00D4AA' : 'rgba(0,212,170,0.15)'}`, background: filter === f ? 'rgba(0,212,170,0.1)' : 'transparent', color: filter === f ? '#00D4AA' : 'rgba(212,223,232,0.4)', cursor: 'pointer', fontFamily: 'sans-serif', fontSize: '10px', letterSpacing: '0.1em', textTransform: 'uppercase' }}>{f}</button>
            ))}
          </div>
          <button onClick={() => setCreating(true)}
            style={{ padding: '9px 18px', background: 'linear-gradient(135deg,rgba(201,168,76,0.15),rgba(201,168,76,0.07))', border: '1px solid rgba(201,168,76,0.35)', borderRadius: '8px', color: '#C9A84C', cursor: 'pointer', fontFamily: 'sans-serif', fontSize: '10px', letterSpacing: '0.18em', whiteSpace: 'nowrap' }}>
            + New Project
          </button>
        </div>

        {/* Create form */}
        <AnimatePresence>
          {creating && (
            <motion.div initial={{ opacity: 0, height: 0 }} animate={{ opacity: 1, height: 'auto' }} exit={{ opacity: 0, height: 0 }}
              style={{ overflow: 'hidden', marginBottom: '20px' }}>
              <div style={{ padding: '20px', background: 'rgba(14,17,32,0.85)', border: '1px solid rgba(201,168,76,0.18)', borderRadius: '12px', display: 'flex', flexDirection: 'column', gap: '10px' }}>
                <p style={{ fontFamily: 'sans-serif', fontSize: '9px', letterSpacing: '0.25em', textTransform: 'uppercase', color: 'rgba(201,168,76,0.55)', margin: 0 }}>New Project</p>
                <input value={newName} onChange={e => setNewName(e.target.value)}
                  onKeyDown={e => { if (e.key === 'Enter') createProject(); if (e.key === 'Escape') setCreating(false); }}
                  autoFocus placeholder="Project name…"
                  style={{ padding: '10px 14px', background: 'rgba(0,0,0,0.3)', border: '1px solid rgba(201,168,76,0.25)', borderRadius: '8px', color: 'rgba(212,223,232,0.9)', fontFamily: 'sans-serif', fontSize: '14px', outline: 'none' }} />
                <textarea value={newDesc} onChange={e => setNewDesc(e.target.value)} rows={2}
                  placeholder="Description (optional)…"
                  style={{ padding: '10px 14px', background: 'rgba(0,0,0,0.25)', border: '1px solid rgba(201,168,76,0.15)', borderRadius: '8px', color: 'rgba(212,223,232,0.8)', fontFamily: 'sans-serif', fontSize: '12px', outline: 'none', resize: 'vertical' }} />
                <div style={{ display: 'flex', gap: '8px' }}>
                  <button onClick={createProject} disabled={!newName.trim()}
                    style={{ ...S.btnGold, opacity: newName.trim() ? 1 : 0.45 }}>Create & Open →</button>
                  <button onClick={() => { setCreating(false); setNewName(''); setNewDesc(''); }}
                    style={{ padding: '8px 14px', background: 'transparent', border: '1px solid rgba(255,255,255,0.1)', borderRadius: '7px', color: 'rgba(212,223,232,0.4)', cursor: 'pointer', fontFamily: 'sans-serif', fontSize: '10px' }}>Cancel</button>
                </div>
              </div>
            </motion.div>
          )}
        </AnimatePresence>

        {/* Project grid */}
        {loading ? (
          <div style={{ textAlign: 'center', padding: '60px', color: 'rgba(212,223,232,0.25)', fontFamily: 'sans-serif', fontSize: '13px' }}>
            <motion.span animate={{ opacity: [0.4, 1, 0.4] }} transition={{ duration: 1.2, repeat: Infinity }}>Loading projects…</motion.span>
          </div>
        ) : visible.length === 0 ? (
          <div style={{ textAlign: 'center', padding: '80px 20px' }}>
            <p style={{ fontFamily: '"Cinzel",serif', fontSize: '28px', color: 'rgba(201,168,76,0.2)', margin: '0 0 12px', letterSpacing: '0.1em' }}>◈</p>
            <p style={{ fontFamily: 'sans-serif', fontSize: '14px', color: 'rgba(212,223,232,0.25)', margin: '0 0 20px' }}>
              {searchQ ? `No projects matching "${searchQ}"` : filter === 'archived' ? 'No archived projects' : 'No projects yet'}
            </p>
            {!searchQ && filter === 'active' && (
              <button onClick={() => setCreating(true)} style={{ ...S.btnGold, padding: '10px 24px', fontSize: '11px', letterSpacing: '0.15em' }}>+ Create Your First Project</button>
            )}
          </div>
        ) : (
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(280px, 1fr))', gap: '12px' }}>
            {visible.map(p => <ProjectCard key={p.id} project={p} onClick={() => setOpenProject(p)} />)}
          </div>
        )}

        {/* Footer */}
        <div style={{ marginTop: '48px', paddingTop: '16px', borderTop: '1px solid rgba(0,212,170,0.06)', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <p style={{ fontFamily: 'sans-serif', fontSize: '9px', letterSpacing: '0.2em', textTransform: 'uppercase', color: 'rgba(212,223,232,0.18)', margin: 0 }}>
            SolSpire Kernel v0.1 · {projects.filter(p => p.status === 'active').length} active projects
          </p>
          <p style={{ fontFamily: 'sans-serif', fontSize: '9px', color: 'rgba(212,223,232,0.18)', margin: 0 }}>Milestone 1 · Project-First</p>
        </div>
      </div>

      <AnimatePresence>{showKeys && <KeysModal onClose={() => setShowKeys(false)} />}</AnimatePresence>
    </div>
  );
}
