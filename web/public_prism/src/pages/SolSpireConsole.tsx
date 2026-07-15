import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import ProjectDashboard, { Project } from './ProjectDashboard';
import KnowledgeOSPage from './knowledge/KnowledgeOSPage';
import Dashboard from './dashboard/Dashboard';
import NexusSpiralCodex from './NexusSpiralCodex';
import { ORACLE } from '../lib/apiConfig';

// ── API ───────────────────────────────────────────────────────────────────────

async function api<T>(path: string, method = 'GET', body?: unknown): Promise<T> {
  const url = `${ORACLE}${path}`;
  const res = await fetch(url, {
    method,
    headers: body ? { 'Content-Type': 'application/json' } : {},
    body: body ? JSON.stringify(body) : undefined,
  });
  if (!res.ok) throw new Error(`${res.status}: ${(await res.text()).slice(0, 200)}`);
  return res.json();
}

// ── Types ─────────────────────────────────────────────────────────────────────

const STATUS_COLORS: Record<string, string> = {
  active: '#00D4AA', paused: '#C9A84C', archived: '#888'
};

function fmtDate(ts: number) {
  const diff = Date.now() - ts * 1000;
  if (diff < 3600000) return `${Math.floor(diff / 60000)}m ago`;
  if (diff < 86400000) return `${Math.floor(diff / 3600000)}h ago`;
  return new Date(ts * 1000).toLocaleDateString();
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

// ── Tab Types ──────────────────────────────────────────────────────────────────

type SolSpireTab = 'projects' | 'knowledge' | 'operations' | 'codex';

const TABS: { id: SolSpireTab; label: string; sigil: string; color: string }[] = [
  { id: 'projects',   label: 'Projects',    sigil: '⚙',  color: '#C9A84C' },
  { id: 'knowledge',  label: 'Knowledge',   sigil: '◈',  color: '#00D4AA' },
  { id: 'operations', label: 'Operations',   sigil: '◎',  color: '#E88C6A' },
  { id: 'codex',      label: 'Codex',       sigil: '⟐',  color: '#B08DE8' },
];

// ── Main Console Shell ────────────────────────────────────────────────────────

export default function SolSpireConsole() {
  	  const [projects, setProjects] = useState<Project[]>([]);
  const [openProject, setOpenProject] = useState<Project | null>(null);
  const [creating, setCreating] = useState(false);
  const [newName, setNewName] = useState('');
  const [newDesc, setNewDesc] = useState('');
  const [filter, setFilter] = useState<'all' | 'active' | 'archived'>('active');
  const [searchQ, setSearchQ] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [tab, setTab] = useState<SolSpireTab>('projects');

  const load = () => {
    setLoading(true);
    setError(null);
    api<{ projects: Project[] }>('/solspire/projects')
      .then(r => { setProjects(r.projects); setLoading(false); })
      .catch(err => {
        console.error('Failed to load projects:', err);
        setError(err.message || 'Failed to connect to backend');
        setLoading(false);
      });
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
    <ProjectDashboard
      project={openProject}
      onBack={() => { setOpenProject(null); load(); }}
      onProjectUpdated={p => setOpenProject(p)}
    />
  );

  // Render different tab content
  if (tab === 'knowledge') {
    return (
      <div className="min-h-screen w-full" style={{ background: '#0A0B14' }}>
        <KnowledgeOSPage />
      </div>
    );
  }

  if (tab === 'operations') {
    return (
      <div className="min-h-screen w-full" style={{ background: '#0A0B14' }}>
        <div style={{ maxWidth: '1200px', margin: '0 auto', padding: '24px 16px' }}>
          <Dashboard />
        </div>
      </div>
    );
  }

  if (tab === 'codex') {
    return (
      <div className="min-h-screen w-full" style={{ background: '#0A0B14' }}>
        <NexusSpiralCodex />
      </div>
    );
  }

  // Projects tab (default)
  return (
    <div className="min-h-screen w-full" style={{ background: '#0A0B14' }}>
      <div className="aurora-bg" />
      <div style={{ maxWidth: '920px', margin: '0 auto', padding: '28px 16px', position: 'relative', zIndex: 10 }}>

        {/* Header */}
        <motion.div initial={{ opacity: 0, y: -10 }} animate={{ opacity: 1, y: 0 }} style={{ marginBottom: '16px', display: 'flex', alignItems: 'flex-end', justifyContent: 'space-between', gap: '16px', flexWrap: 'wrap' }}>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '6px' }}>
              <div style={{ width: '7px', height: '7px', background: '#C9A84C', borderRadius: '50%', boxShadow: '0 0 10px #C9A84C88' }} />
              <p style={{ fontFamily: 'sans-serif', fontSize: '9px', letterSpacing: '0.35em', textTransform: 'uppercase', color: 'rgba(201,168,76,0.55)', margin: 0 }}>
                SolSpire Console · Project-First Intelligence
              </p>
            </div>
            <h1 style={{ fontFamily: '"Cinzel",serif', fontSize: '34px', color: '#C9A84C', margin: '0 0 4px', letterSpacing: '0.18em', textShadow: '0 0 40px rgba(201,168,76,0.3)' }}>SOLSPIRE</h1>
            <p style={{ fontFamily: 'sans-serif', fontSize: '10px', color: 'rgba(212,223,232,0.35)', margin: '4px 0 0' }}>API Keys managed in Settings</p>
          </div>
        </motion.div>

        {/* Tab navigation */}
        <div style={{ display: 'flex', gap: '4px', marginBottom: '20px', borderBottom: '1px solid rgba(201,168,76,0.08)', paddingBottom: '12px' }}>
          {TABS.map(t => (
            <button
              key={t.id}
              onClick={() => setTab(t.id)}
              style={{
                padding: '8px 16px',
                background: tab === t.id ? `${t.color}10` : 'transparent',
                border: tab === t.id ? `1px solid ${t.color}45` : '1px solid rgba(255,255,255,0.06)',
                borderRadius: '10px',
                cursor: 'pointer',
                transition: 'all 0.18s',
                display: 'flex',
                alignItems: 'center',
                gap: '8px',
              }}
            >
              <span style={{ fontSize: '14px' }}>{t.sigil}</span>
              <span style={{ fontFamily: 'sans-serif', fontSize: '10px', letterSpacing: '0.15em', textTransform: 'uppercase', color: tab === t.id ? t.color : 'rgba(212,223,232,0.5)' }}>
                {t.label}
              </span>
            </button>
          ))}
        </div>

        {/* Sub-header for projects tab */}
        <p style={{ fontFamily: 'sans-serif', fontSize: '12px', color: 'rgba(212,223,232,0.4)', margin: '0 0 20px' }}>Select a project — or create a new one</p>

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
                    style={{ padding: '8px 16px', background: 'rgba(201,168,76,0.1)', border: '1px solid rgba(201,168,76,0.3)', borderRadius: '7px', color: '#C9A84C', cursor: 'pointer', fontFamily: 'sans-serif', fontSize: '10px', letterSpacing: '0.12em', opacity: newName.trim() ? 1 : 0.45 }}>Create & Open →</button>
                  <button onClick={() => { setCreating(false); setNewName(''); setNewDesc(''); }}
                    style={{ padding: '8px 14px', background: 'transparent', border: '1px solid rgba(255,255,255,0.1)', borderRadius: '7px', color: 'rgba(212,223,232,0.4)', cursor: 'pointer', fontFamily: 'sans-serif', fontSize: '10px' }}>Cancel</button>
                </div>
              </div>
            </motion.div>
          )}
        </AnimatePresence>

        {/* Error display */}
        {error && (
          <div style={{ padding: '16px', background: 'rgba(200,72,72,0.08)', border: '1px solid rgba(200,72,72,0.25)', borderRadius: '8px', marginBottom: '20px' }}>
            <p style={{ fontFamily: 'sans-serif', fontSize: '12px', color: 'rgba(200,72,72,0.9)', margin: '0 0 8px' }}>
              ⚠ Connection Error
            </p>
            <p style={{ fontFamily: 'sans-serif', fontSize: '11px', color: 'rgba(212,223,232,0.5)', margin: '0' }}>
              {error}
            </p>
            <p style={{ fontFamily: 'sans-serif', fontSize: '10px', color: 'rgba(212,223,232,0.3)', margin: '8px 0 0' }}>
              Backend: {ORACLE}
            </p>
          </div>
        )}

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
    </div>
  );
}
