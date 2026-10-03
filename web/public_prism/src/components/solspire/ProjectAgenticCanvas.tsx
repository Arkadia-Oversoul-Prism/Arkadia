import React, { useState } from 'react';
import { apiFetch } from '../lib/apiClient';
import type { Project } from './ProjectDashboard';

interface LabSession {
  session_id: string;
  state: string;
  objective?: string;
  project_ref?: string | null;
  authorization_ref?: string | null;
}

const CARD: React.CSSProperties = {
  padding: 16,
  background: 'rgba(14,17,32,0.78)',
  border: '1px solid rgba(0,212,170,0.12)',
  borderRadius: 12,
};
const INPUT: React.CSSProperties = {
  width: '100%',
  boxSizing: 'border-box',
  padding: '10px 12px',
  borderRadius: 8,
  border: '1px solid rgba(0,212,170,0.18)',
  background: 'rgba(0,0,0,0.25)',
  color: '#E9E7DF',
  font: '12px sans-serif',
};

async function request<T>(path: string, body?: unknown): Promise<T> {
  const response = await apiFetch(path, {
    method: body === undefined ? 'GET' : 'POST',
    headers: body === undefined ? {} : { 'Content-Type': 'application/json' },
    body: body === undefined ? undefined : JSON.stringify(body),
  });
  const data = await response.json().catch(() => ({}));
  if (!response.ok) throw new Error(data?.detail || data?.message || `${response.status} ${response.statusText}`);
  return data as T;
}

export default function ProjectAgenticCanvas({ project }: { project: Project }) {
  const [objective, setObjective] = useState('Inspect this project workspace and report its available files, constraints, and next useful actions.');
  const [provider, setProvider] = useState('ollama');
  const [session, setSession] = useState<LabSession | null>(null);
  const [result, setResult] = useState<any>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  const [notice, setNotice] = useState('');

  async function createSession() {
    setBusy(true); setError(''); setNotice(''); setResult(null);
    try {
      const workspace = await request<{ workspace: { id: string } }>('/solspire/workspace');
      const agent = await request<{ agent_id: string }>('/api/lab/engineering/agents', {
        role: 'BUILDER',
        display_name: `${project.name} · Bounded Canvas Worker`,
        capabilities: ['READ', 'RUN'],
        write_allowed: false,
      });
      const created = await request<LabSession>('/api/lab/engineering/sessions', {
        workspace_ref: workspace.workspace.id,
        agent_id: agent.agent_id,
        objective: objective.trim(),
        project_ref: project.id,
      });
      setSession(created);
      setNotice('Session created in PROPOSED state. No tools are authorized yet.');
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Unable to create project session');
    } finally { setBusy(false); }
  }

  async function authorizeSession() {
    if (!session) return;
    setBusy(true); setError(''); setNotice('');
    try {
      const data = await request<{ session: LabSession }>(`/api/lab/engineering/sessions/${session.session_id}/authorize`, {
        operations_allowed: ['read', 'list', 'run'],
        duration_minutes: 60,
      });
      setSession(data.session);
      setNotice('Human authorization recorded for read/list and the closed read-only terminal grammar. Filesystem writes and network access remain disabled.');
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Authorization failed');
    } finally { setBusy(false); }
  }

  async function runAgent() {
    if (!session) return;
    setBusy(true); setError(''); setNotice(''); setResult(null);
    try {
      const data = await request<any>(`/api/lab/engineering/sessions/${session.session_id}/run-agent`, {
        objective: objective.trim(),
        provider: provider.trim() || 'ollama',
        max_turns: 6,
      });
      setResult(data);
      setNotice('Run returned. Inspect the actual observations and evidence below; a run is not human acceptance.');
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Agent run failed');
    } finally { setBusy(false); }
  }

  const state = session?.state || 'NO SESSION';
  const stateColor = state === 'AUTHORIZED' || state === 'QUEUED' ? '#00D4AA' : '#C9A84C';

  return <div data-testid="solariun-project-agentic-canvas" style={{ display: 'grid', gap: 14, color: '#D4DFE8', fontFamily: 'sans-serif' }}>
    <section style={{ ...CARD, background: 'radial-gradient(circle at 90% 0%,rgba(176,141,232,.12),transparent 44%),rgba(14,17,32,.82)' }}>
      <div style={{ fontSize: 9, letterSpacing: '.2em', textTransform: 'uppercase', color: '#B08DE8' }}>SolSpire · Agentic Canvas</div>
      <h3 style={{ margin: '7px 0', font: '400 24px Georgia,serif', color: '#E9E7DF' }}>{project.name}</h3>
      <p style={{ margin: 0, maxWidth: 680, fontSize: 11, lineHeight: 1.7, color: 'rgba(212,223,232,.55)' }}>
        A project-bound session using the existing Engineering Lab runtime. It snapshots canonical project files into a server-managed workspace and runs with a closed, read-only command grammar. This is not a container boundary; no writes, network access, merge or deployment are enabled.
      </p>
    </section>

    <section style={{ ...CARD, display: 'grid', gap: 10 }}>
      <label style={{ display: 'grid', gap: 6, fontSize: 10, color: 'rgba(212,223,232,.5)' }}>
        OBJECTIVE
        <textarea aria-label="Canvas objective" value={objective} onChange={e => setObjective(e.target.value)} rows={3} style={{ ...INPUT, resize: 'vertical' }} />
      </label>
      <label style={{ display: 'grid', gap: 6, fontSize: 10, color: 'rgba(212,223,232,.5)' }}>
        MODEL PROVIDER
        <input aria-label="Canvas model provider" value={provider} onChange={e => setProvider(e.target.value)} placeholder="Configured provider, e.g. ollama" style={INPUT} />
      </label>
      <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8 }}>
        <button type="button" disabled={busy || !objective.trim()} onClick={() => void createSession()} style={{ padding: '9px 12px', borderRadius: 8, border: '1px solid rgba(176,141,232,.35)', background: 'rgba(176,141,232,.08)', color: '#B08DE8', cursor: busy ? 'wait' : 'pointer', fontSize: 10 }}>
          {busy && !session ? 'Creating…' : 'Create project session'}
        </button>
        {session?.state === 'PROPOSED' && <button type="button" disabled={busy} onClick={() => void authorizeSession()} style={{ padding: '9px 12px', borderRadius: 8, border: '1px solid rgba(201,168,76,.35)', background: 'rgba(201,168,76,.08)', color: '#C9A84C', cursor: busy ? 'wait' : 'pointer', fontSize: 10 }}>Authorize read-only run</button>}
        {session && (session.state === 'AUTHORIZED' || session.state === 'QUEUED') && <button type="button" disabled={busy} onClick={() => void runAgent()} style={{ padding: '9px 12px', borderRadius: 8, border: '1px solid rgba(0,212,170,.35)', background: 'rgba(0,212,170,.08)', color: '#00D4AA', cursor: busy ? 'wait' : 'pointer', fontSize: 10 }}>{busy ? 'Running…' : 'Run bounded agent'}</button>}
      </div>
      <div style={{ fontSize: 10, color: 'rgba(212,223,232,.4)' }}>SESSION · <strong style={{ color: stateColor }}>{state}</strong>{session?.session_id ? ` · ${session.session_id}` : ''}</div>
      {notice && <div role="status" style={{ fontSize: 11, lineHeight: 1.6, color: '#00D4AA' }}>{notice}</div>}
      {error && <div role="alert" style={{ fontSize: 11, lineHeight: 1.6, color: '#E66B6B' }}>{error}</div>}
    </section>

    <section style={{ ...CARD, display: 'grid', gap: 8 }}>
      <div style={{ fontSize: 9, letterSpacing: '.18em', textTransform: 'uppercase', color: 'rgba(201,168,76,.6)' }}>Execution boundary</div>
      {['Project ownership checked against the authenticated UID','Workspace root derived by the server from subject + project','Only canonical project files are materialized, with path and size limits','Human authorization required before an agent run','Filesystem writes and network access disabled in v0.1','Run evidence is reviewable; execution does not imply acceptance'].map(item => <div key={item} style={{ display: 'flex', gap: 8, fontSize: 10, lineHeight: 1.5, color: 'rgba(212,223,232,.58)' }}><span style={{ color: '#00D4AA' }}>•</span>{item}</div>)}
    </section>

    {result && <section style={{ ...CARD, display: 'grid', gap: 8 }}>
      <div style={{ fontSize: 9, letterSpacing: '.18em', textTransform: 'uppercase', color: '#00D4AA' }}>Observed run result</div>
      <div style={{ fontSize: 11, color: 'rgba(212,223,232,.7)' }}>State · {String(result.state || result.result_state || 'UNKNOWN')} · Turns · {Array.isArray(result.turns) ? result.turns.length : 0}</div>
      <pre style={{ margin: 0, padding: 12, maxHeight: 420, overflow: 'auto', whiteSpace: 'pre-wrap', overflowWrap: 'anywhere', borderRadius: 8, background: 'rgba(0,0,0,.25)', color: 'rgba(212,223,232,.7)', fontSize: 10, lineHeight: 1.6 }}>{JSON.stringify(result, null, 2)}</pre>
    </section>}
  </div>;
}
