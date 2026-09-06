import React, { useCallback, useEffect, useState } from 'react';
import { apiFetch } from '../../lib/apiClient';
import type { Project } from '../../pages/ProjectDashboard';

const CARD: React.CSSProperties = { background: 'rgba(16,18,31,.78)', border: '1px solid rgba(255,255,255,.07)', borderRadius: 16, padding: 18, boxShadow: '0 14px 40px rgba(0,0,0,.18)' };
const MONO: React.CSSProperties = { fontFamily: 'ui-monospace,SFMono-Regular,monospace', fontSize: 8, letterSpacing: '.18em', textTransform: 'uppercase', color: 'rgba(201,168,76,.58)' };

export default function ProjectsWorkspace({ onOpenProject }: { onOpenProject: (project: Project) => void }) {
  const [projects, setProjects] = useState<Project[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [creating, setCreating] = useState(false);
  const [name, setName] = useState('');
  const [createError, setCreateError] = useState<string | null>(null);

  const load = useCallback(async () => {
    setLoading(true); setError(null);
    try {
      const response = await apiFetch('/solspire/projects', { headers: {} });
      const data = await response.json();
      if (!response.ok) throw new Error(data?.detail || `${response.status} ${response.statusText}`);
      setProjects(data.projects || []);
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Unable to load projects');
    } finally { setLoading(false); }
  }, []);

  useEffect(() => { void load(); }, [load]);

  async function createProject(event: React.FormEvent) {
    event.preventDefault();
    const trimmed = name.trim();
    if (!trimmed) { setCreateError('Give the project a name first.'); return; }
    setCreating(true); setCreateError(null);
    try {
      const response = await apiFetch('/solspire/projects', {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name: trimmed, metadata: {} }),
      });
      const data = await response.json();
      if (!response.ok) throw new Error(data?.detail || `${response.status} ${response.statusText}`);
      const project = data.project as Project;
      setProjects(current => [project, ...current]);
      setName('');
      setCreating(false);
      onOpenProject(project);
    } catch (e) {
      setCreateError(e instanceof Error ? e.message : 'Project creation failed');
      setCreating(false);
    }
  }

  return <div style={{ display: 'grid', gap: 14 }}>
    <section style={{ ...CARD, background: 'radial-gradient(circle at 88% 0%,rgba(201,168,76,.13),transparent 42%),rgba(16,18,31,.82)' }}>
      <div style={MONO}>SolSpire / Projects</div>
      <div style={{ display: 'flex', gap: 18, alignItems: 'flex-end', justifyContent: 'space-between', flexWrap: 'wrap', marginTop: 6 }}>
        <div><h2 style={{ margin: 0, font: '400 29px Georgia,serif', color: '#E9E7DF' }}>Projects</h2><p style={{ margin: '8px 0 0', maxWidth: 690, font: '12px/1.65 Inter,system-ui,sans-serif', color: 'rgba(233,231,223,.46)' }}>Projects are the organizing context for files, knowledge, conversations, tasks, memory and governed Weaver work.</p></div>
        <span style={{ ...MONO, color: 'rgba(0,212,170,.55)' }}>{loading ? 'READING' : `${projects.length} PROJECT${projects.length === 1 ? '' : 'S'}`}</span>
      </div>
    </section>

    <form onSubmit={createProject} style={{ ...CARD, display: 'flex', gap: 10, alignItems: 'center', flexWrap: 'wrap' }}>
      <input aria-label="New project name" value={name} onChange={e => setName(e.target.value)} placeholder="Name a new project…" style={{ flex: '1 1 260px', minWidth: 0, padding: '11px 13px', background: 'rgba(0,0,0,.28)', border: '1px solid rgba(201,168,76,.2)', borderRadius: 9, color: '#E9E7DF', outline: 'none' }} />
      <button type="submit" disabled={creating} style={{ padding: '10px 16px', borderRadius: 9, border: '1px solid rgba(201,168,76,.34)', background: 'rgba(201,168,76,.09)', color: '#C9A84C', font: '9px ui-monospace,monospace', letterSpacing: '.16em', textTransform: 'uppercase', cursor: creating ? 'wait' : 'pointer' }}>{creating ? 'Creating…' : 'Create project'}</button>
      {createError && <div role="alert" style={{ flexBasis: '100%', font: '11px Inter,system-ui,sans-serif', color: '#E85246' }}>{createError}</div>}
    </form>

    {error && <div role="alert" style={{ ...CARD, borderColor: 'rgba(232,82,70,.25)', color: '#E85246' }}>{error}</div>}
    {loading && <div style={{ ...CARD, color: 'rgba(233,231,223,.32)' }}>Reading your project field…</div>}
    {!loading && !error && projects.length === 0 && <div style={{ ...CARD, textAlign: 'center', padding: '42px 20px' }}><div style={{ fontSize: 28, color: 'rgba(201,168,76,.22)' }}>◈</div><h3 style={{ margin: '9px 0 5px', font: '400 18px Georgia,serif', color: 'rgba(233,231,223,.62)' }}>No projects yet</h3><p style={{ margin: 0, font: '11px/1.6 Inter,system-ui,sans-serif', color: 'rgba(233,231,223,.32)' }}>Create a project above and the rest of the workspace can gather around it.</p></div>}
    {!loading && projects.map(project => <article key={project.id} style={{ ...CARD, padding: 0, overflow: 'hidden' }}>
      <button type="button" onClick={() => onOpenProject(project)} style={{ width: '100%', display: 'flex', alignItems: 'center', gap: 14, padding: 18, border: 0, background: 'transparent', color: 'inherit', cursor: 'pointer', textAlign: 'left' }}>
        <span style={{ width: 44, height: 44, flexShrink: 0, display: 'grid', placeItems: 'center', borderRadius: 13, background: 'rgba(201,168,76,.08)', border: '1px solid rgba(201,168,76,.18)', color: '#C9A84C', fontSize: 19 }}>◈</span>
        <span style={{ flex: 1, minWidth: 0 }}><strong style={{ display: 'block', font: '500 15px Georgia,serif', color: '#E9E7DF' }}>{project.name}</strong><span style={{ display: 'block', marginTop: 5, ...MONO, color: 'rgba(233,231,223,.28)' }}>{project.status} · updated {new Date((project.updated_at || 0) * 1000).toLocaleDateString()}</span></span>
        <span aria-hidden="true" style={{ color: '#C9A84C', fontSize: 18 }}>→</span>
      </button>
      <div style={{ display: 'flex', flexWrap: 'wrap', gap: 7, padding: '0 18px 16px 76px' }}>{['Files','Knowledge','Conversations','Tasks','Memory','Weaver'].map(label => <span key={label} style={{ padding: '5px 8px', borderRadius: 7, border: '1px solid rgba(255,255,255,.06)', background: 'rgba(255,255,255,.02)', ...MONO, color: 'rgba(233,231,223,.28)' }}>{label}</span>)}</div>
    </article>)}
  </div>;
}
