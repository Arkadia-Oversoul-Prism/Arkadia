/**
 * SolSpire Personal Console — Unified Intelligence & Operational Hub
 *
 * One scrollable unified page. No fragmented tabs.
 * Single sidebar menu routes across all sections:
 *   Personal: Personal Codex · Open Loops
 *   Intelligence: Knowledge OS · Projects
 *   Operational Console: Overview · Goals · Releases · Jobs · Traces · Tools · System
 *
 * Every section header carries a source/route indicator so the origin
 * of each data feed is explicit.
 */
import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { ORACLE } from '../lib/apiConfig';
import { useAuth } from '../contexts/AuthContext';

// ── Dashboard sub-components (direct import, no wrapper nav) ──────────────────
import Overview   from './dashboard/Overview';
import Jobs       from './dashboard/Jobs';
import Goals      from './dashboard/Goals';
import Traces     from './dashboard/Traces';
import Tools      from './dashboard/Tools';
import System     from './dashboard/System';
import OpenLoops  from './dashboard/OpenLoops';
import Releases   from './dashboard/Releases';

// ── Other page components ─────────────────────────────────────────────────────
import KnowledgeOSPage  from './knowledge/KnowledgeOSPage';
import PersonalCodex    from './PersonalCodex';
import ProjectDashboard, { Project } from './ProjectDashboard';

// ── Types ─────────────────────────────────────────────────────────────────────

type SolSection =
  | 'codex' | 'loops' | 'knowledge' | 'projects'
  | 'overview' | 'goals' | 'releases' | 'jobs' | 'traces' | 'tools' | 'system';

interface NavItem {
  id: SolSection;
  label: string;
  sigil: string;
  color: string;
  source: string;    // explicit data-source label
  sub: string;
}

interface NavGroup {
  label: string;
  items: NavItem[];
}

const NAV_GROUPS: NavGroup[] = [
  {
    label: 'Personal',
    items: [
      { id: 'codex',     label: 'Personal Codex',  sigil: '✦', color: '#C9A84C', source: 'vault/identity',  sub: 'Soul map · 90-day architecture · access lattice' },
      { id: 'loops',     label: 'Open Loops',       sigil: '∞', color: '#C84848', source: 'ops/loops',       sub: 'Active tasks · unresolved threads' },
    ],
  },
  {
    label: 'Intelligence',
    items: [
      { id: 'knowledge', label: 'Knowledge OS',     sigil: '◈', color: '#00D4AA', source: 'vault/ + public', sub: 'Graph · timeline · scrolls · full-system feed' },
      { id: 'projects',  label: 'Projects',         sigil: '⚙', color: '#C9A84C', source: 'solspire/projects', sub: 'Operational Console · catalogue & index' },
    ],
  },
  {
    label: 'Operational Console',
    items: [
      { id: 'overview',  label: 'Overview',         sigil: '◎', color: '#6A9FD8', source: 'ops/overview',    sub: 'System metrics · node status' },
      { id: 'goals',     label: 'Goals',            sigil: '◉', color: '#B08DE8', source: 'ops/goals',       sub: 'Strategic objectives · milestones' },
      { id: 'releases',  label: 'Releases',         sigil: '◐', color: '#00D4AA', source: 'ops/releases',    sub: 'Deployment versions · changelogs' },
      { id: 'jobs',      label: 'Jobs',             sigil: '⚒', color: '#C9A84C', source: 'ops/jobs',        sub: 'Operational jobs · execution status' },
      { id: 'traces',    label: 'Traces',           sigil: '⟐', color: '#6A9FD8', source: 'ops/traces',      sub: 'Debug logs · execution traces' },
      { id: 'tools',     label: 'Tools',            sigil: '❖', color: '#B08DE8', source: 'ops/tools',       sub: 'Internal utilities · system functions' },
      { id: 'system',    label: 'System',           sigil: '◆', color: '#00D4AA', source: 'ops/system',      sub: 'Worker threads · hardware metrics' },
    ],
  },
];

const ALL_ITEMS: NavItem[] = NAV_GROUPS.flatMap(g => g.items);

// ── API ───────────────────────────────────────────────────────────────────────

async function apiFetch<T>(path: string, method = 'GET', body?: unknown): Promise<T> {
  const res = await fetch(`${ORACLE}${path}`, {
    method,
    headers: body ? { 'Content-Type': 'application/json' } : {},
    body: body ? JSON.stringify(body) : undefined,
  });
  if (!res.ok) throw new Error(`${res.status}: ${(await res.text()).slice(0, 200)}`);
  return res.json();
}

function fmtDate(ts: number) {
  const diff = Date.now() - ts * 1000;
  if (diff < 3600000) return `${Math.floor(diff / 60000)}m ago`;
  if (diff < 86400000) return `${Math.floor(diff / 3600000)}h ago`;
  return new Date(ts * 1000).toLocaleDateString();
}

const STATUS_COLORS: Record<string, string> = {
  active: '#00D4AA', paused: '#C9A84C', archived: '#888'
};

// ── Section header with source route badge ─────────────────────────────────────

function SectionHeader({ item }: { item: NavItem }) {
  return (
    <div style={{ marginBottom: 20 }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 6 }}>
        <span style={{ color: item.color, fontSize: 16 }}>{item.sigil}</span>
        <h2 style={{ fontFamily: '"Cinzel", serif', fontSize: 22, color: item.color, margin: 0, letterSpacing: '0.12em' }}>
          {item.label.toUpperCase()}
        </h2>
        <span style={{
          padding: '2px 8px',
          background: `${item.color}10`,
          border: `1px solid ${item.color}28`,
          borderRadius: 12,
          fontFamily: 'monospace',
          fontSize: 9,
          color: `${item.color}99`,
          letterSpacing: '0.08em',
        }}>
          ⟐ {item.source}
        </span>
      </div>
      <p style={{ fontFamily: 'sans-serif', fontSize: 11, color: 'rgba(212,223,232,0.4)', margin: 0, letterSpacing: '0.04em' }}>
        {item.sub}
      </p>
      <div style={{ height: 1, background: `linear-gradient(90deg, ${item.color}30, transparent)`, marginTop: 12 }} />
    </div>
  );
}

// ── Project Card ───────────────────────────────────────────────────────────────

function ProjectCard({ project, onClick }: { project: Project; onClick: () => void }) {
  const desc = (project.metadata?.description as string) || '';
  const convCount = project.conversations?.length || 0;
  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }}
      onClick={onClick}
      style={{ padding: 18, background: 'rgba(14,17,32,0.78)', border: '1px solid rgba(0,212,170,0.1)', borderRadius: 12, cursor: 'pointer', display: 'flex', flexDirection: 'column', gap: 10, transition: 'border-color 0.18s', position: 'relative', overflow: 'hidden' }}
      onMouseEnter={e => (e.currentTarget.style.borderColor = 'rgba(0,212,170,0.3)')}
      onMouseLeave={e => (e.currentTarget.style.borderColor = 'rgba(0,212,170,0.1)')}
    >
      <div style={{ position: 'absolute', top: 0, left: 0, right: 0, height: 2, background: `linear-gradient(90deg, ${STATUS_COLORS[project.status] || '#888'}66, transparent)` }} />
      <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', gap: 8 }}>
        <h3 style={{ fontFamily: '"Cinzel",serif', fontSize: 15, color: '#C9A84C', margin: 0, flex: 1, lineHeight: 1.3 }}>{project.name}</h3>
        <span style={{ padding: '2px 7px', borderRadius: 8, fontSize: 8, background: `${STATUS_COLORS[project.status] || '#888'}18`, color: STATUS_COLORS[project.status] || '#888', border: `1px solid ${STATUS_COLORS[project.status] || '#888'}33`, fontFamily: 'sans-serif', letterSpacing: '0.1em', textTransform: 'uppercase', flexShrink: 0 }}>
          {project.status}
        </span>
      </div>
      {desc && <p style={{ fontFamily: 'sans-serif', fontSize: 12, color: 'rgba(212,223,232,0.5)', margin: 0, lineHeight: 1.5, display: '-webkit-box', WebkitLineClamp: 2, WebkitBoxOrient: 'vertical', overflow: 'hidden' }}>{desc}</p>}
      <div style={{ display: 'flex', gap: 12, marginTop: 'auto' }}>
        <span style={{ fontFamily: 'sans-serif', fontSize: 10, color: 'rgba(212,223,232,0.3)' }}>Updated {fmtDate(project.updated_at)}</span>
        {convCount > 0 && <span style={{ fontFamily: 'sans-serif', fontSize: 10, color: 'rgba(0,212,170,0.4)' }}>💬 {convCount}</span>}
      </div>
    </motion.div>
  );
}

// ── Projects view ──────────────────────────────────────────────────────────────

function ProjectsView({ onOpenProject }: { onOpenProject: (p: Project) => void }) {
  const [projects, setProjects] = useState<Project[]>([]);
  const [creating, setCreating] = useState(false);
  const [newName, setNewName] = useState('');
  const [newDesc, setNewDesc] = useState('');
  const [filter, setFilter] = useState<'all' | 'active' | 'archived'>('active');
  const [searchQ, setSearchQ] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const load = () => {
    setLoading(true);
    setError(null);
    apiFetch<{ projects: Project[] }>('/solspire/projects')
      .then(r => { setProjects(r.projects); setLoading(false); })
      .catch(err => { setError(err.message || 'Failed to connect'); setLoading(false); });
  };

  useEffect(() => { load(); }, []);

  const createProject = async () => {
    if (!newName.trim()) return;
    const r = await apiFetch<{ ok: boolean; project: Project }>('/solspire/projects', 'POST', {
      name: newName, metadata: { description: newDesc },
    });
    setNewName(''); setNewDesc(''); setCreating(false); load();
    if (r.project) onOpenProject(r.project);
  };

  const visible = projects.filter(p => {
    if (filter !== 'all' && p.status !== filter) return false;
    if (searchQ && !p.name.toLowerCase().includes(searchQ.toLowerCase())) return false;
    return true;
  });

  return (
    <div>
      {/* Controls */}
      <div style={{ display: 'flex', gap: 10, marginBottom: 20, flexWrap: 'wrap', alignItems: 'center' }}>
        <input value={searchQ} onChange={e => setSearchQ(e.target.value)} placeholder="Search projects…"
          style={{ flex: '1 1 200px', padding: '9px 12px', background: 'rgba(14,17,32,0.8)', border: '1px solid rgba(0,212,170,0.15)', borderRadius: 8, color: 'rgba(212,223,232,0.8)', fontFamily: 'sans-serif', fontSize: 12, outline: 'none' }} />
        <div style={{ display: 'flex', gap: 4 }}>
          {(['active', 'all', 'archived'] as const).map(f => (
            <button key={f} onClick={() => setFilter(f)}
              style={{ padding: '7px 12px', borderRadius: 7, border: `1px solid ${filter === f ? '#00D4AA' : 'rgba(0,212,170,0.15)'}`, background: filter === f ? 'rgba(0,212,170,0.1)' : 'transparent', color: filter === f ? '#00D4AA' : 'rgba(212,223,232,0.4)', cursor: 'pointer', fontFamily: 'sans-serif', fontSize: 10, letterSpacing: '0.1em', textTransform: 'uppercase' }}>
              {f}
            </button>
          ))}
        </div>
        <button onClick={() => setCreating(true)}
          style={{ padding: '9px 18px', background: 'linear-gradient(135deg,rgba(201,168,76,0.15),rgba(201,168,76,0.07))', border: '1px solid rgba(201,168,76,0.35)', borderRadius: 8, color: '#C9A84C', cursor: 'pointer', fontFamily: 'sans-serif', fontSize: 10, letterSpacing: '0.18em', whiteSpace: 'nowrap' }}>
          + New Project
        </button>
      </div>

      {/* Create form */}
      <AnimatePresence>
        {creating && (
          <motion.div initial={{ opacity: 0, height: 0 }} animate={{ opacity: 1, height: 'auto' }} exit={{ opacity: 0, height: 0 }}
            style={{ overflow: 'hidden', marginBottom: 20 }}>
            <div style={{ padding: 20, background: 'rgba(14,17,32,0.85)', border: '1px solid rgba(201,168,76,0.18)', borderRadius: 12, display: 'flex', flexDirection: 'column', gap: 10 }}>
              <p style={{ fontFamily: 'sans-serif', fontSize: 9, letterSpacing: '0.25em', textTransform: 'uppercase', color: 'rgba(201,168,76,0.55)', margin: 0 }}>New Project</p>
              <input value={newName} onChange={e => setNewName(e.target.value)}
                onKeyDown={e => { if (e.key === 'Enter') createProject(); if (e.key === 'Escape') setCreating(false); }}
                autoFocus placeholder="Project name…"
                style={{ padding: '10px 14px', background: 'rgba(0,0,0,0.3)', border: '1px solid rgba(201,168,76,0.25)', borderRadius: 8, color: 'rgba(212,223,232,0.9)', fontFamily: 'sans-serif', fontSize: 14, outline: 'none' }} />
              <textarea value={newDesc} onChange={e => setNewDesc(e.target.value)} rows={2}
                placeholder="Description (optional)…"
                style={{ padding: '10px 14px', background: 'rgba(0,0,0,0.25)', border: '1px solid rgba(201,168,76,0.15)', borderRadius: 8, color: 'rgba(212,223,232,0.8)', fontFamily: 'sans-serif', fontSize: 12, outline: 'none', resize: 'vertical' }} />
              <div style={{ display: 'flex', gap: 8 }}>
                <button onClick={createProject} disabled={!newName.trim()}
                  style={{ padding: '8px 16px', background: 'rgba(201,168,76,0.1)', border: '1px solid rgba(201,168,76,0.3)', borderRadius: 7, color: '#C9A84C', cursor: 'pointer', fontFamily: 'sans-serif', fontSize: 10, letterSpacing: '0.12em', opacity: newName.trim() ? 1 : 0.45 }}>
                  Create & Open →
                </button>
                <button onClick={() => { setCreating(false); setNewName(''); setNewDesc(''); }}
                  style={{ padding: '8px 14px', background: 'transparent', border: '1px solid rgba(255,255,255,0.1)', borderRadius: 7, color: 'rgba(212,223,232,0.4)', cursor: 'pointer', fontFamily: 'sans-serif', fontSize: 10 }}>
                  Cancel
                </button>
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {error && (
        <div style={{ padding: 16, background: 'rgba(200,72,72,0.08)', border: '1px solid rgba(200,72,72,0.25)', borderRadius: 8, marginBottom: 20 }}>
          <p style={{ fontFamily: 'sans-serif', fontSize: 12, color: 'rgba(200,72,72,0.9)', margin: '0 0 8px' }}>⚠ Connection Error</p>
          <p style={{ fontFamily: 'sans-serif', fontSize: 11, color: 'rgba(212,223,232,0.5)', margin: 0 }}>{error}</p>
          <p style={{ fontFamily: 'sans-serif', fontSize: 10, color: 'rgba(212,223,232,0.3)', margin: '8px 0 0' }}>Backend: {ORACLE}</p>
        </div>
      )}

      {loading ? (
        <div style={{ textAlign: 'center', padding: 60, color: 'rgba(212,223,232,0.25)', fontFamily: 'sans-serif', fontSize: 13 }}>
          <motion.span animate={{ opacity: [0.4, 1, 0.4] }} transition={{ duration: 1.2, repeat: Infinity }}>Loading projects…</motion.span>
        </div>
      ) : visible.length === 0 ? (
        <div style={{ textAlign: 'center', padding: '80px 20px' }}>
          <p style={{ fontFamily: '"Cinzel",serif', fontSize: 28, color: 'rgba(201,168,76,0.2)', margin: '0 0 12px', letterSpacing: '0.1em' }}>◈</p>
          <p style={{ fontFamily: 'sans-serif', fontSize: 14, color: 'rgba(212,223,232,0.25)', margin: '0 0 20px' }}>
            {searchQ ? `No projects matching "${searchQ}"` : filter === 'archived' ? 'No archived projects' : 'No projects yet'}
          </p>
          {!searchQ && filter === 'active' && (
            <button onClick={() => setCreating(true)}
              style={{ padding: '10px 24px', background: 'rgba(201,168,76,0.1)', border: '1px solid rgba(201,168,76,0.3)', borderRadius: 8, color: '#C9A84C', cursor: 'pointer', fontFamily: 'sans-serif', fontSize: 11, letterSpacing: '0.15em' }}>
              + Create Your First Project
            </button>
          )}
        </div>
      ) : (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(280px, 1fr))', gap: 12 }}>
          {visible.map(p => <ProjectCard key={p.id} project={p} onClick={() => onOpenProject(p)} />)}
        </div>
      )}

      <div style={{ marginTop: 40, paddingTop: 16, borderTop: '1px solid rgba(0,212,170,0.06)', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <p style={{ fontFamily: 'sans-serif', fontSize: 9, letterSpacing: '0.2em', textTransform: 'uppercase', color: 'rgba(212,223,232,0.18)', margin: 0 }}>
          SolSpire Kernel · {projects.filter(p => p.status === 'active').length} active projects
        </p>
        <p style={{ fontFamily: 'sans-serif', fontSize: 9, color: 'rgba(212,223,232,0.18)', margin: 0 }}>source: solspire/projects</p>
      </div>
    </div>
  );
}

// ── Sidebar nav item ──────────────────────────────────────────────────────────

function SidebarItem({ item, active, onClick }: { item: NavItem; active: boolean; onClick: () => void }) {
  return (
    <button onClick={onClick} style={{
      display: 'flex', alignItems: 'center', gap: 10,
      width: '100%', padding: '9px 11px',
      background: active ? `${item.color}0e` : 'transparent',
      border: active ? `1px solid ${item.color}28` : '1px solid transparent',
      borderRadius: 9, cursor: 'pointer', textAlign: 'left', transition: 'all 0.15s',
    }}>
      <motion.span
        animate={active ? { opacity: [0.6, 1, 0.6] } : {}}
        transition={{ duration: 3, repeat: Infinity }}
        style={{ fontSize: 12, flexShrink: 0, width: 18, textAlign: 'center', color: active ? item.color : 'rgba(232,232,232,0.42)' }}
      >
        {item.sigil}
      </motion.span>
      <div style={{ flex: 1, overflow: 'hidden' }}>
        <p style={{ fontFamily: 'sans-serif', fontSize: 10.5, color: active ? item.color : 'rgba(232,232,232,0.72)', margin: 0, fontWeight: active ? 600 : 400, whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
          {item.label}
        </p>
      </div>
      {active && <motion.div layoutId="sol-active" style={{ width: 3, height: 3, borderRadius: '50%', background: item.color, flexShrink: 0 }} />}
    </button>
  );
}

// ── Main Console ──────────────────────────────────────────────────────────────

export default function SolSpireConsole() {
  const [section, setSection] = useState<SolSection>('codex');
  const [openProject, setOpenProject] = useState<Project | null>(null);
  const [traceJobId, setTraceJobId] = useState<string | null>(null);
  const [mobileNavOpen, setMobileNavOpen] = useState(false);
  const { isAuthenticated } = useAuth();

  const activeItem = ALL_ITEMS.find(i => i.id === section)!;

  // If a project is open, render it full-screen
  if (openProject) {
    return (
      <ProjectDashboard
        project={openProject}
        onBack={() => setOpenProject(null)}
        onProjectUpdated={p => setOpenProject(p)}
      />
    );
  }

  const handleSection = (s: SolSection) => {
    setSection(s);
    setMobileNavOpen(false);
  };

  const SectionContent = () => (
    <AnimatePresence mode="wait">
      <motion.div
        key={section}
        initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0 }}
        transition={{ duration: 0.2 }}
      >
        <SectionHeader item={activeItem} />

        {section === 'codex'     && <PersonalCodex />}
        {section === 'loops'     && <OpenLoops />}
        {section === 'knowledge' && <KnowledgeOSPage />}
        {section === 'projects'  && (
          <ProjectsView onOpenProject={p => setOpenProject(p)} />
        )}
        {section === 'overview'  && <Overview />}
        {section === 'goals'     && <Goals />}
        {section === 'releases'  && <Releases />}
        {section === 'jobs'      && <Jobs onOpenTrace={(id: string) => { setTraceJobId(id); setSection('traces'); }} />}
        {section === 'traces'    && <Traces openJobId={traceJobId} />}
        {section === 'tools'     && <Tools />}
        {section === 'system'    && <System />}
      </motion.div>
    </AnimatePresence>
  );

  return (
    <div style={{ minHeight: 'calc(100vh - 52px)', background: '#0A0B14', position: 'relative' }}>
      <div className="aurora-bg" />

      {/* ── Mobile: collapsible menu strip ── */}
      <div style={{ display: 'block' }} className="lg:hidden">
        {/* Mobile header */}
        <div style={{ padding: '12px 16px', borderBottom: '1px solid rgba(201,168,76,0.1)', display: 'flex', alignItems: 'center', justifyContent: 'space-between', background: 'rgba(10,11,20,0.95)', position: 'sticky', top: 52, zIndex: 20 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
            <span style={{ color: activeItem.color, fontSize: 14 }}>{activeItem.sigil}</span>
            <p style={{ fontFamily: '"Cinzel", serif', fontSize: 13, color: activeItem.color, margin: 0, letterSpacing: '0.1em' }}>{activeItem.label}</p>
            <span style={{ padding: '1px 6px', background: `${activeItem.color}10`, border: `1px solid ${activeItem.color}22`, borderRadius: 10, fontFamily: 'monospace', fontSize: 8, color: `${activeItem.color}88` }}>
              {activeItem.source}
            </span>
          </div>
          <button onClick={() => setMobileNavOpen(o => !o)} style={{ background: 'none', border: 'none', color: 'rgba(232,232,232,0.5)', cursor: 'pointer', fontSize: 18, padding: '4px 8px' }}>
            {mobileNavOpen ? '✕' : '☰'}
          </button>
        </div>

        {/* Mobile nav drawer */}
        <AnimatePresence>
          {mobileNavOpen && (
            <motion.div
              initial={{ height: 0, opacity: 0 }} animate={{ height: 'auto', opacity: 1 }} exit={{ height: 0, opacity: 0 }}
              style={{ overflow: 'hidden', background: 'rgba(9,10,22,0.98)', borderBottom: '1px solid rgba(201,168,76,0.12)', position: 'sticky', top: 92, zIndex: 19 }}
            >
              <div style={{ padding: '10px 12px' }}>
                {NAV_GROUPS.map(group => (
                  <div key={group.label} style={{ marginBottom: 12 }}>
                    <p style={{ fontFamily: 'sans-serif', fontSize: 7.5, letterSpacing: '0.38em', textTransform: 'uppercase', color: 'rgba(201,168,76,0.45)', margin: '0 6px 6px' }}>{group.label}</p>
                    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 4 }}>
                      {group.items.map(item => (
                        <button key={item.id} onClick={() => handleSection(item.id)} style={{
                          padding: '8px 6px',
                          background: section === item.id ? `${item.color}10` : 'transparent',
                          border: `1px solid ${section === item.id ? item.color + '35' : 'rgba(255,255,255,0.07)'}`,
                          borderRadius: 8, cursor: 'pointer', textAlign: 'center',
                          display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 3,
                        }}>
                          <span style={{ fontSize: 13, color: section === item.id ? item.color : 'rgba(232,232,232,0.45)' }}>{item.sigil}</span>
                          <span style={{ fontFamily: 'sans-serif', fontSize: 8.5, color: section === item.id ? item.color : 'rgba(232,232,232,0.5)', letterSpacing: '0.08em', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis', maxWidth: '100%' }}>{item.label}</span>
                        </button>
                      ))}
                    </div>
                  </div>
                ))}
              </div>
            </motion.div>
          )}
        </AnimatePresence>

        {/* Mobile content */}
        <div style={{ padding: '20px 16px 60px', position: 'relative', zIndex: 10 }}>
          <SectionContent />
        </div>
      </div>

      {/* ── Desktop: sidebar + content ── */}
      <div style={{ display: 'none' }} className="lg:flex">
        <aside style={{
          width: 236, flexShrink: 0,
          borderRight: '1px solid rgba(201,168,76,0.08)',
          background: 'rgba(9,10,22,0.75)',
          backdropFilter: 'blur(20px)',
          WebkitBackdropFilter: 'blur(20px)',
          padding: '24px 12px',
          display: 'flex', flexDirection: 'column', gap: 4,
          position: 'sticky', top: 52, height: 'calc(100vh - 52px)', overflowY: 'auto',
          zIndex: 10,
        }}>
          {/* Console header */}
          <div style={{ padding: '0 8px 16px', borderBottom: '1px solid rgba(201,168,76,0.08)', marginBottom: 8 }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 6, marginBottom: 4 }}>
              <div style={{ width: 6, height: 6, background: '#C9A84C', borderRadius: '50%', boxShadow: '0 0 8px #C9A84C88' }} />
              <p style={{ fontFamily: '"Cinzel", serif', fontSize: 11, letterSpacing: '0.3em', textTransform: 'uppercase', color: '#C9A84C', margin: 0 }}>SOLSPIRE</p>
            </div>
            <p style={{ fontFamily: 'sans-serif', fontSize: 9, color: 'rgba(212,223,232,0.3)', margin: 0, letterSpacing: '0.06em' }}>Personal Console · All sources unified</p>
          </div>

          {/* Nav groups */}
          {NAV_GROUPS.map(group => (
            <div key={group.label} style={{ marginBottom: 14 }}>
              <p style={{ fontFamily: 'sans-serif', fontSize: 7.5, letterSpacing: '0.4em', textTransform: 'uppercase', color: 'rgba(201,168,76,0.45)', margin: '0 6px 5px' }}>
                {group.label}
              </p>
              <div style={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
                {group.items.map(item => (
                  <SidebarItem key={item.id} item={item} active={section === item.id} onClick={() => handleSection(item.id)} />
                ))}
              </div>
            </div>
          ))}

          {/* Auth indicator */}
          {isAuthenticated && (
            <div style={{ marginTop: 'auto', padding: '10px 8px', borderTop: '1px solid rgba(0,212,170,0.08)' }}>
              <p style={{ fontFamily: 'sans-serif', fontSize: 8, letterSpacing: '0.18em', textTransform: 'uppercase', color: 'rgba(0,212,170,0.35)', margin: 0 }}>
                ◈ Node authenticated · full access
              </p>
            </div>
          )}
        </aside>

        {/* Main content */}
        <main style={{ flex: 1, padding: '32px 36px 60px', overflowX: 'hidden', position: 'relative', zIndex: 10 }}>
          <SectionContent />
        </main>
      </div>

      {/* Fallback for when neither responsive class applies — show sidebar layout inline */}
      <style>{`
        @media (min-width: 1024px) {
          .lg\\:hidden { display: none !important; }
          .lg\\:flex { display: flex !important; }
        }
        @media (max-width: 1023px) {
          .lg\\:flex { display: none !important; }
          .lg\\:hidden { display: block !important; }
        }
      `}</style>
    </div>
  );
}
