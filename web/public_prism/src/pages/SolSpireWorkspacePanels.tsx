import React, { useEffect, useMemo, useState } from 'react';
import { motion } from 'framer-motion';
import { ORACLE } from '../lib/apiConfig';
import type { Project } from './ProjectDashboard';

export type WorkspaceCollectionKind = 'conversations' | 'tasks' | 'memory' | 'events';

async function workspaceFetch<T>(path: string): Promise<T> {
  const token = localStorage.getItem('arkadia_token') || '';
  const res = await fetch(`${ORACLE}${path}`, { headers: token ? { Authorization: `Bearer ${token}` } : {} });
  if (!res.ok) throw new Error(`${res.status}: ${(await res.text()).slice(0, 180)}`);
  return res.json();
}

const card: React.CSSProperties = {
  padding: 16,
  background: 'rgba(14,17,32,0.72)',
  border: '1px solid rgba(0,212,170,0.1)',
  borderRadius: 12,
};

const label: React.CSSProperties = {
  fontFamily: 'sans-serif',
  fontSize: 8,
  letterSpacing: '0.24em',
  textTransform: 'uppercase',
  color: 'rgba(0,212,170,0.48)',
  margin: '0 0 8px',
};

function useProjects() {
  const [projects, setProjects] = useState<Project[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  useEffect(() => {
    workspaceFetch<{ projects: Project[] }>('/solspire/projects')
      .then(r => setProjects(r.projects || []))
      .catch(e => setError(e.message || 'Unable to load workspace'))
      .finally(() => setLoading(false));
  }, []);
  return { projects, error, loading };
}

export function WorkspaceFiles({ onOpenProject }: { onOpenProject: (project: Project) => void }) {
  const { projects, error, loading } = useProjects();
  const [expanded, setExpanded] = useState<string | null>(null);
  const [files, setFiles] = useState<Record<string, any[]>>({});

  async function loadFiles(projectId: string) {
    setExpanded(expanded === projectId ? null : projectId);
    if (files[projectId]) return;
    try {
      const r = await workspaceFetch<{ files: any[] }>(`/solspire/projects/${projectId}/files`);
      setFiles(prev => ({ ...prev, [projectId]: r.files || [] }));
    } catch {
      setFiles(prev => ({ ...prev, [projectId]: [] }));
    }
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
      <div style={{ ...card, background: 'linear-gradient(135deg,rgba(201,168,76,0.08),rgba(14,17,32,0.72))' }}>
        <p style={{ ...label, color: 'rgba(201,168,76,0.52)' }}>Files / Spiral Codex</p>
        <h3 style={{ fontFamily: 'Cinzel,serif', fontSize: 21, color: '#C9A84C', margin: '0 0 6px' }}>Workspace folders</h3>
        <p style={{ margin: 0, fontFamily: 'sans-serif', fontSize: 12, lineHeight: 1.6, color: 'rgba(212,223,232,0.46)' }}>
          Projects are folder objects here. Documents and media remain inside the existing project file store. Opening a folder enters its workspace thread, not another console.
        </p>
      </div>

      {loading && <div style={{ ...card, color: 'rgba(212,223,232,0.3)' }}>Reading workspace folders…</div>}
      {error && <div style={{ ...card, borderColor: 'rgba(200,72,72,0.2)', color: 'rgba(200,72,72,0.7)' }}>{error}</div>}
      {!loading && !projects.length && <div style={{ ...card, color: 'rgba(212,223,232,0.28)' }}>No workspace folders yet.</div>}

      {projects.map(project => {
        const isOpen = expanded === project.id;
        const projectFiles = files[project.id] || [];
        return (
          <motion.div key={project.id} layout style={{ ...card, padding: 0, overflow: 'hidden' }}>
            <button type="button" onClick={() => loadFiles(project.id)} style={{ width: '100%', border: 0, background: 'transparent', color: 'inherit', padding: 16, cursor: 'pointer', textAlign: 'left' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
                <span style={{ fontSize: 22, color: '#C9A84C' }}>📁</span>
                <div style={{ flex: 1 }}>
                  <div style={{ fontFamily: 'Cinzel,serif', fontSize: 15, color: '#C9A84C' }}>{project.name}</div>
                  <div style={{ marginTop: 4, fontFamily: 'sans-serif', fontSize: 10, color: 'rgba(212,223,232,0.3)' }}>{project.status} · {projectFiles.length || '…'} objects</div>
                </div>
                <span style={{ color: 'rgba(212,223,232,0.28)' }}>{isOpen ? '⌄' : '›'}</span>
              </div>
            </button>
            {isOpen && (
              <div style={{ padding: '0 16px 16px', borderTop: '1px solid rgba(201,168,76,0.07)' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '12px 0 8px' }}>
                  <span style={{ ...label, margin: 0 }}>Folder contents</span>
                  <button type="button" onClick={() => onOpenProject(project)} style={{ border: '1px solid rgba(201,168,76,0.25)', background: 'rgba(201,168,76,0.08)', color: '#C9A84C', borderRadius: 7, padding: '6px 10px', cursor: 'pointer', fontSize: 9, letterSpacing: '0.12em', textTransform: 'uppercase' }}>Open thread →</button>
                </div>
                {!projectFiles.length ? <div style={{ padding: '12px 0', color: 'rgba(212,223,232,0.24)', fontSize: 11 }}>No files in this folder.</div> : projectFiles.map(file => (
                  <div key={file.id} style={{ padding: '9px 0', borderTop: '1px solid rgba(255,255,255,0.035)', display: 'flex', gap: 10, alignItems: 'center' }}>
                    <span>📄</span><span style={{ flex: 1, fontFamily: 'sans-serif', fontSize: 11, color: 'rgba(212,223,232,0.6)' }}>{file.name}</span><span style={{ fontFamily: 'monospace', fontSize: 9, color: 'rgba(212,223,232,0.22)' }}>{file.mime_type || 'file'}</span>
                  </div>
                ))}
              </div>
            )}
          </motion.div>
        );
      })}
    </div>
  );
}

const ENDPOINTS: Record<WorkspaceCollectionKind, string> = {
  conversations: 'conversations',
  tasks: 'tasks',
  memory: 'memory',
  events: 'events',
};

const TITLES: Record<WorkspaceCollectionKind, { title: string; icon: string; description: string }> = {
  conversations: { title: 'Conversations', icon: '💬', description: 'Every project conversation, surfaced as one workspace stream.' },
  tasks: { title: 'Tasks', icon: '☐', description: 'Tasks across the workspace, without requiring a project detour.' },
  memory: { title: 'Memory', icon: '∞', description: 'Project-scoped memory entries composed into one private view.' },
  events: { title: 'Observatory', icon: '⟐', description: 'The existing event ledger rendered as a live workspace feed.' },
};

export function WorkspaceCollection({ kind }: { kind: WorkspaceCollectionKind }) {
  const { projects, loading: projectLoading } = useProjects();
  const [items, setItems] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  const meta = TITLES[kind];

  useEffect(() => {
    if (!projects.length) return;
    let cancelled = false;
    setLoading(true);
    Promise.all(projects.map(async p => {
      try {
        const r = await workspaceFetch<Record<string, any[]>>(`/solspire/projects/${p.id}/${ENDPOINTS[kind]}`);
        const rows = r[ENDPOINTS[kind]] || [];
        return rows.map(row => ({ ...row, project_name: p.name, project_id: p.id }));
      } catch { return []; }
    })).then(groups => { if (!cancelled) setItems(groups.flat().sort((a, b) => (b.updated_at || b.created_at || 0) - (a.updated_at || a.created_at || 0))); })
      .finally(() => { if (!cancelled) setLoading(false); });
    return () => { cancelled = true; };
  }, [kind, projects]);

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
      <div style={card}><p style={{ ...label }}>{meta.title}</p><h3 style={{ fontFamily: 'Cinzel,serif', fontSize: 21, color: '#00D4AA', margin: '0 0 6px' }}>{meta.icon} {meta.title}</h3><p style={{ margin: 0, fontFamily: 'sans-serif', fontSize: 12, color: 'rgba(212,223,232,0.42)', lineHeight: 1.5 }}>{meta.description}</p></div>
      {(projectLoading || loading) && <div style={{ ...card, color: 'rgba(212,223,232,0.3)' }}>Composing workspace feed…</div>}
      {!loading && !items.length && !projectLoading && <div style={{ ...card, color: 'rgba(212,223,232,0.28)' }}>Nothing recorded here yet.</div>}
      {items.map((item, i) => (
        <motion.div key={item.id || `${item.project_id}-${i}`} initial={{ opacity: 0, y: 5 }} animate={{ opacity: 1, y: 0 }} style={card}>
          <div style={{ display: 'flex', gap: 10, alignItems: 'flex-start' }}>
            <span style={{ fontSize: 15 }}>{meta.icon}</span>
            <div style={{ flex: 1 }}>
              <div style={{ fontFamily: 'sans-serif', fontSize: 12, color: 'rgba(232,232,232,0.72)' }}>{item.title || item.summary || item.event_type || 'Untitled'}</div>
              <div style={{ marginTop: 4, fontFamily: 'monospace', fontSize: 8.5, color: 'rgba(0,212,170,0.35)', letterSpacing: '0.08em' }}>{item.project_name}</div>
              {(item.description || item.content) && <div style={{ marginTop: 7, fontFamily: 'sans-serif', fontSize: 11, lineHeight: 1.5, color: 'rgba(212,223,232,0.38)' }}>{String(item.description || item.content).slice(0, 240)}</div>}
            </div>
            {item.status && <span style={{ fontFamily: 'sans-serif', fontSize: 8, textTransform: 'uppercase', color: 'rgba(0,212,170,0.45)' }}>{item.status}</span>}
          </div>
        </motion.div>
      ))}
    </div>
  );
}

export function CommercialPanel() {
  const { projects, loading, error } = useProjects();
  const [tasks, setTasks] = useState<any[]>([]);
  const [events, setEvents] = useState<any[]>([]);

  useEffect(() => {
    if (!projects.length) return;
    Promise.all(projects.map(async p => {
      const [taskResult, eventResult] = await Promise.all([
        workspaceFetch<{ tasks: any[] }>(`/solspire/projects/${p.id}/tasks`).catch(() => ({ tasks: [] })),
        workspaceFetch<{ events: any[] }>(`/solspire/projects/${p.id}/events`).catch(() => ({ events: [] })),
      ]);
      return {
        project: p,
        tasks: (taskResult.tasks || []).map(t => ({ ...t, project_name: p.name })),
        events: (eventResult.events || []).map(e => ({ ...e, project_name: p.name })),
      };
    })).then(groups => {
      setTasks(groups.flatMap(g => g.tasks));
      setEvents(groups.flatMap(g => g.events));
    });
  }, [projects]);

  const opportunities = useMemo(() => projects.filter(p => p.status === 'active').map(project => {
    const projectTasks = tasks.filter(t => t.project_id === project.id);
    const recentEvents = events.filter(e => e.project_id === project.id).length;
    const openTasks = projectTasks.filter(t => !['done', 'completed'].includes(t.status)).length;
    const score = Math.min(100, 30 + openTasks * 8 + recentEvents * 3 + (project.metadata?.commercial ? 20 : 0));
    return { project, openTasks, recentEvents, score };
  }).sort((a, b) => b.score - a.score), [projects, tasks, events]);

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
      <div style={{ ...card, background: 'linear-gradient(135deg,rgba(201,168,76,0.1),rgba(0,212,170,0.035))' }}>
        <p style={{ ...label, color: 'rgba(201,168,76,0.55)' }}>SolSpire / Commercial Intelligence</p>
        <h3 style={{ fontFamily: 'Cinzel,serif', fontSize: 23, color: '#C9A84C', margin: '0 0 7px' }}>Commercial</h3>
        <p style={{ margin: 0, maxWidth: 720, fontFamily: 'sans-serif', fontSize: 12, lineHeight: 1.65, color: 'rgba(212,223,232,0.46)' }}>
          The commercial layer now lives beside Knowledge, Files, Conversations and Tasks. This first surface reads the existing workspace state and ranks active work for commercial attention. It does not create a second CRM, call the execution pipeline, or invent authority.
        </p>
      </div>

      {loading && <div style={{ ...card, color: 'rgba(212,223,232,0.3)' }}>Reading commercial signals from the workspace…</div>}
      {error && <div style={{ ...card, color: 'rgba(200,72,72,0.7)' }}>{error}</div>}
      {!loading && <>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit,minmax(150px,1fr))', gap: 10 }}>
          {[
            ['Active work', projects.filter(p => p.status === 'active').length],
            ['Open tasks', tasks.filter(t => !['done','completed'].includes(t.status)).length],
            ['Workspace signals', events.length],
            ['Commercial candidates', opportunities.length],
          ].map(([name, value]) => <div key={String(name)} style={card}><div style={{ fontFamily: 'monospace', fontSize: 22, color: '#00D4AA' }}>{value}</div><div style={{ marginTop: 4, fontFamily: 'sans-serif', fontSize: 8, textTransform: 'uppercase', letterSpacing: '0.14em', color: 'rgba(212,223,232,0.3)' }}>{name}</div></div>)}
        </div>

        <div style={card}>
          <p style={label}>Opportunity radar · derived, not authoritative</p>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
            {opportunities.map(({ project, openTasks, recentEvents, score }) => (
              <div key={project.id} style={{ padding: '12px 0', borderTop: '1px solid rgba(255,255,255,0.05)' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', gap: 12 }}>
                  <span style={{ fontFamily: 'Cinzel,serif', fontSize: 13, color: '#C9A84C' }}>{project.name}</span>
                  <span style={{ fontFamily: 'monospace', fontSize: 9, color: 'rgba(0,212,170,0.55)' }}>signal {score}/100</span>
                </div>
                <div style={{ marginTop: 5, fontFamily: 'sans-serif', fontSize: 10, color: 'rgba(212,223,232,0.32)' }}>{openTasks} open tasks · {recentEvents} recorded signals · next decision should be operator-owned</div>
              </div>
            ))}
            {!opportunities.length && <div style={{ color: 'rgba(212,223,232,0.25)', fontSize: 11 }}>No active commercial candidates in the current workspace state.</div>}
          </div>
        </div>
      </>}
    </div>
  );
}

export function WeaverSummary({ onOpenProject }: { onOpenProject: (project: Project) => void }) {
  const { projects, loading } = useProjects();
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
      <div style={card}><p style={label}>Weaver / governed engineering</p><h3 style={{ fontFamily: 'Cinzel,serif', fontSize: 21, color: '#B08DE8', margin: '0 0 6px' }}>Weaver</h3><p style={{ margin: 0, fontFamily: 'sans-serif', fontSize: 12, lineHeight: 1.55, color: 'rgba(212,223,232,0.42)' }}>Weaver remains the project-scoped engineering workflow and mutation boundary. SolSpire exposes its operating state here, while K15 → K3 remains the only governed mutation path.</p></div>
      {loading && <div style={{ ...card, color: 'rgba(212,223,232,0.3)' }}>Reading Weaver project state…</div>}
      {projects.filter(p => p.status === 'active').map(project => <div key={project.id} style={{ ...card, display: 'flex', alignItems: 'center', gap: 12 }}><span style={{ fontSize: 19 }}>⚒</span><div style={{ flex: 1 }}><div style={{ fontFamily: 'Cinzel,serif', fontSize: 13, color: '#B08DE8' }}>{project.name}</div><div style={{ fontSize: 9, color: 'rgba(212,223,232,0.28)', marginTop: 3 }}>Project-bound Weaver context</div></div><button type="button" onClick={() => onOpenProject(project)} style={{ border: '1px solid rgba(176,141,232,0.25)', background: 'rgba(176,141,232,0.07)', color: '#B08DE8', borderRadius: 7, padding: '7px 10px', cursor: 'pointer', fontSize: 9 }}>Open thread →</button></div>)}
    </div>
  );
}

export function Observatory() {
  return <WorkspaceCollection kind="events" />;
}
