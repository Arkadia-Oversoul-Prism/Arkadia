import React, { useState, useEffect, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';

const ORACLE = (import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000').replace(/\/$/, '');

// ── Types ─────────────────────────────────────────────────────────────────────

export interface Project {
  id: string; name: string; status: string;
  created_at: number; updated_at: number;
  metadata: Record<string, unknown>;
  conversations: unknown[];
}

interface Conversation { id: string; title: string; status: string; messages: Msg[]; created_at: number; updated_at: number; }
interface Msg { role: string; content: string; ts: number; }
interface PFile { id: string; name: string; size?: number; mime_type: string; created_at: number; updated_at: number; content?: string; }
interface Repo { id: string; owner: string; repo: string; branch: string; label: string; created_at: number; }
interface Task { id: string; title: string; description: string; status: string; assigned_to: string; priority: string; created_at: number; updated_at: number; }
interface MemEntry { id: string; title: string; content: string; tags: string[]; created_at: number; updated_at: number; }
interface PEvent { id: string; event_type: string; summary: string; created_at: number; }
interface RunResult { ok: boolean; intent: string; plan: { steps: { tool: string; description: string }[] }; execution: { status: string; results: Record<string,unknown>[] }; elapsed_ms: number; }
type ProjTab = 'overview'|'weaver'|'knowledge'|'conversations'|'files'|'repos'|'tasks'|'workflows'|'memory'|'events'|'settings';

// ── API ───────────────────────────────────────────────────────────────────────

// Pass 01R: /solspire now requires the Firebase ID token on every request.
let authToken: string | null = null;
export function setSolspireAuthToken(token: string | null) { authToken = token; }

function authHeaders(extra: Record<string, string> = {}): Record<string, string> {
  const h = { ...extra };
  if (authToken) h.Authorization = `Bearer ${authToken}`;
  return h;
}

async function api<T>(path: string, method = 'GET', body?: unknown): Promise<T> {
  const res = await fetch(`${ORACLE}${path}`, {
    method,
    headers: authHeaders(body ? { 'Content-Type': 'application/json' } : {}),
    body: body ? JSON.stringify(body) : undefined,
  });
  if (!res.ok) throw new Error(`${res.status}: ${(await res.text()).slice(0, 200)}`);
  return res.json();
}

// ── Helpers ───────────────────────────────────────────────────────────────────

const S = {
  card: { padding: '14px 16px', background: 'rgba(14,17,32,0.78)', border: '1px solid rgba(0,212,170,0.1)', borderRadius: '10px' } as React.CSSProperties,
  input: { padding: '9px 12px', background: 'rgba(0,0,0,0.3)', border: '1px solid rgba(0,212,170,0.18)', borderRadius: '7px', color: 'rgba(212,223,232,0.85)', fontFamily: 'sans-serif', fontSize: '12px', outline: 'none', width: '100%', boxSizing: 'border-box' as const },
  textarea: { padding: '10px 12px', background: 'rgba(0,0,0,0.3)', border: '1px solid rgba(0,212,170,0.15)', borderRadius: '7px', color: 'rgba(212,223,232,0.85)', fontFamily: 'monospace', fontSize: '12px', outline: 'none', width: '100%', boxSizing: 'border-box' as const, resize: 'vertical' as const },
  btnTeal: { padding: '8px 16px', background: 'rgba(0,212,170,0.1)', border: '1px solid rgba(0,212,170,0.3)', borderRadius: '7px', color: '#00D4AA', cursor: 'pointer', fontFamily: 'sans-serif', fontSize: '10px', letterSpacing: '0.12em', whiteSpace: 'nowrap' as const },
  btnGold: { padding: '8px 16px', background: 'rgba(201,168,76,0.1)', border: '1px solid rgba(201,168,76,0.3)', borderRadius: '7px', color: '#C9A84C', cursor: 'pointer', fontFamily: 'sans-serif', fontSize: '10px', letterSpacing: '0.12em', whiteSpace: 'nowrap' as const },
  btnDanger: { padding: '6px 12px', background: 'transparent', border: '1px solid rgba(200,72,72,0.25)', borderRadius: '6px', color: 'rgba(200,72,72,0.7)', cursor: 'pointer', fontFamily: 'sans-serif', fontSize: '10px' },
  label: { fontFamily: 'sans-serif', fontSize: '9px', letterSpacing: '0.25em', textTransform: 'uppercase' as const, color: 'rgba(0,212,170,0.5)', margin: '0 0 8px', display: 'block' },
  empty: { textAlign: 'center' as const, padding: '40px', color: 'rgba(212,223,232,0.25)', fontFamily: 'sans-serif', fontSize: '13px' },
};

function fmtDate(ts: number) {
  const d = new Date(ts * 1000);
  const now = Date.now();
  const diff = now - d.getTime();
  if (diff < 60000) return 'just now';
  if (diff < 3600000) return `${Math.floor(diff / 60000)}m ago`;
  if (diff < 86400000) return `${Math.floor(diff / 3600000)}h ago`;
  return d.toLocaleDateString();
}

const PRIORITY_COLORS: Record<string, string> = { high: '#C84848', normal: '#C9A84C', low: '#6A9FD8' };
const STATUS_COLORS: Record<string, string> = { open: '#00D4AA', done: '#4CAF50', completed: '#4CAF50', active: '#00D4AA', archived: '#888', paused: '#C9A84C' };
const EVENT_ICONS: Record<string, string> = { conversation_created: '💬', file_created: '📄', repo_linked: '⟁', task_created: '☐', memory_added: '∞', workflow_run: '⟐' };

// ── Tab Sections ──────────────────────────────────────────────────────────────


/** W5 — Project Weaver workbench (read-only). Project access ≠ execution auth. */
function WeaverPanel({ project }: { project: Project }) {
  const [objective, setObjective] = React.useState('');
  const [paths, setPaths] = React.useState('weaver/execution.py');
  const [result, setResult] = React.useState<any>(null);
  const [caps, setCaps] = React.useState<any>(null);
  const [busy, setBusy] = React.useState(false);
  const [err, setErr] = React.useState('');
  const base = `${ORACLE}/solspire/projects/${project.id}/weaver`;
  const token = () => localStorage.getItem('arkadia_token') || '';

  React.useEffect(() => {
    fetch(`${base}/capabilities`, { headers: { Authorization: `Bearer ${token()}` } })
      .then(r => r.json()).then(setCaps).catch(() => {});
  }, [project.id]);

  async function analyze() {
    setBusy(true); setErr('');
    try {
      const r = await fetch(`${base}/analyze`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token()}` },
        body: JSON.stringify({
          objective,
          affected_paths: paths.split(/[\n,]/).map((s: string) => s.trim()).filter(Boolean),
        }),
      });
      const data = await r.json();
      if (!r.ok) throw new Error(typeof data.detail === 'string' ? data.detail : r.statusText);
      setResult(data);
    } catch (e: any) {
      setErr(String(e.message || e));
    } finally {
      setBusy(false);
    }
  }

  const auth = result?.authorization || { Execution: 'LOCKED', PassSpec: 'NONE', PatchApproval: 'NONE' };
  const scope = result?.scope || {};
  const an = result?.analysis || {};
  return (
    <div style={{ fontFamily: 'sans-serif', color: '#D4DFE8' }}>
      <div style={{ marginBottom: 12, padding: 12, border: '1px solid rgba(0,212,170,0.2)', borderRadius: 8 }}>
        <div style={{ fontSize: 11, letterSpacing: '0.12em', color: '#00D4AA', marginBottom: 6 }}>PROJECT ENGINEERING WORKBENCH · READ-ONLY</div>
        <div style={{ fontSize: 12, opacity: 0.75 }}>
          PROJECT ACCESS ≠ PASSSPEC ≠ PATCH APPROVAL ≠ EXECUTION · Mutation: K3 ONLY via K15
        </div>
        <div style={{ marginTop: 8, fontSize: 12 }}>
          Execution: <strong style={{ color: '#C9A84C' }}>{auth.Execution || 'LOCKED'}</strong>
          {' · '}PassSpec: {auth.PassSpec || 'NONE'}
          {' · '}Approval: {auth.PatchApproval || 'NONE'}
        </div>
        {result?.project_context?.knowledge && (
          <div style={{ marginTop: 6, fontSize: 11, opacity: 0.7 }}>
            Context sources: {JSON.stringify(result.project_context.knowledge)}
          </div>
        )}
      </div>
      <div style={{ fontSize: 11, color: 'rgba(212,223,232,0.5)', marginBottom: 4 }}>OBJECTIVE</div>
      <textarea value={objective} onChange={e => setObjective(e.target.value)} placeholder="Engineering objective for this project"
        style={{ width: '100%', minHeight: 56, background: '#0a0b14', border: '1px solid rgba(0,212,170,0.25)', color: '#D4DFE8', padding: 8, borderRadius: 6 }} />
      <div style={{ fontSize: 11, color: 'rgba(212,223,232,0.5)', margin: '10px 0 4px' }}>SCOPE — affected paths (optional)</div>
      <textarea value={paths} onChange={e => setPaths(e.target.value)} placeholder="weaver/execution.py"
        style={{ width: '100%', minHeight: 48, background: '#0a0b14', border: '1px solid rgba(0,212,170,0.25)', color: '#D4DFE8', padding: 8, borderRadius: 6, fontFamily: 'monospace', fontSize: 12 }} />
      <div style={{ display: 'flex', gap: 8, marginTop: 10 }}>
        <button onClick={analyze} disabled={busy || !objective.trim()}
          style={{ padding: '8px 14px', background: 'rgba(0,212,170,0.15)', border: '1px solid #00D4AA', color: '#00D4AA', borderRadius: 6, cursor: 'pointer' }}>
          {busy ? 'Analyzing…' : 'ANALYZE (READ-ONLY)'}
        </button>
        <button disabled title="Requires PassSpec + PatchApproval via K15→K3"
          style={{ padding: '8px 14px', opacity: 0.4, border: '1px solid #666', color: '#888', borderRadius: 6 }}>
          BUILD / EXECUTE (LOCKED)
        </button>
      </div>
      {err && <div style={{ color: '#c44', marginTop: 8 }}>{err}</div>}
      {result && (
        <div style={{ marginTop: 14, display: 'grid', gap: 10 }}>
          <div style={{ padding: 10, border: '1px solid rgba(0,212,170,0.12)', borderRadius: 6 }}>
            <div style={{ fontSize: 11, color: '#00D4AA' }}>SCOPE · {scope.status || 'UNSCOPED'}</div>
            <div style={{ fontSize: 11, fontFamily: 'monospace' }}>{JSON.stringify(scope.affected_paths || [])}</div>
            <div style={{ fontSize: 11, opacity: 0.6 }}>{scope.note}</div>
          </div>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: 8 }}>
            <div><div style={{ fontSize: 10, color: '#8ab' }}>FACTS</div>
              {(an.facts || []).slice(0, 4).map((f: any, i: number) => <div key={i} style={{ fontSize: 11 }}>{f.statement || f}</div>)}
            </div>
            <div><div style={{ fontSize: 10, color: '#ca8' }}>INFERENCES</div>
              {(an.inferences || []).slice(0, 4).map((f: any, i: number) => <div key={i} style={{ fontSize: 11 }}>{f.statement || f}</div>)}
            </div>
            <div><div style={{ fontSize: 10, color: '#a88' }}>UNKNOWN</div>
              {(an.unknowns || []).slice(0, 4).map((f: any, i: number) => <div key={i} style={{ fontSize: 11 }}>{f.statement || f}</div>)}
            </div>
          </div>
          <div style={{ padding: 10, border: '1px solid rgba(0,212,170,0.12)', borderRadius: 6, fontSize: 11 }}>
            <div>PLAN · {result.plan?.plan_id} · {result.plan?.scope_status}</div>
            <div>paths: {JSON.stringify(result.plan?.affected_paths || [])}</div>
            <div>CHANGESET files: {(result.changeset?.files || []).map((f: any) => f.path).join(', ') || '—'}</div>
            <div>PATCH · {result.patch?.status} · quality {result.patch?.implementation_quality || '—'} · EXECUTED: {String(result.patch?.EXECUTED ?? false)}</div>
          </div>
        </div>
      )}
      {caps && (
        <div style={{ marginTop: 16, fontSize: 11, opacity: 0.75 }}>
          Available: {(caps.read_only_capabilities || []).join(', ')}
          {caps.mutation_capabilities?.length ? ` · Gated mutation: ${caps.mutation_capabilities.join(', ')}` : ''}
        </div>
      )}
    </div>
  );
}

function KnowledgePanel({ project }: { project: Project }) {
  const [data, setData] = React.useState<any>(null);
  const [graph, setGraph] = React.useState<any>(null);
  const [emb, setEmb] = React.useState<any>(null);
  const [q, setQ] = React.useState('');
  const [hits, setHits] = React.useState<any[]>([]);
  const base = `${ORACLE}/solspire/projects/${project.id}/knowledge`;
  const token = () => localStorage.getItem('arkadia_token') || '';
  React.useEffect(() => {
    const h = { Authorization: `Bearer ${token()}` };
    fetch(base, { headers: h }).then(r => r.json()).then(setData).catch(() => {});
    fetch(`${base}/graph`, { headers: h }).then(r => r.json()).then(setGraph).catch(() => {});
    fetch(`${base}/embeddings`, { headers: h }).then(r => r.json()).then(setEmb).catch(() => {});
  }, [project.id]);
  async function search() {
    const r = await fetch(`${base}/search`, {
      method: 'POST', headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token()}` },
      body: JSON.stringify({ q }),
    });
    const d = await r.json();
    setHits(d.hits || []);
  }
  return (
    <div style={{ fontFamily: 'sans-serif', color: '#D4DFE8', fontSize: 12 }}>
      <div style={{ marginBottom: 10, color: '#00D4AA', letterSpacing: '0.1em' }}>PROJECT KNOWLEDGE OS</div>
      {data && (
        <div style={{ marginBottom: 12 }}>
          Sources: {JSON.stringify(data.sources)}
          <div style={{ opacity: 0.6, marginTop: 4 }}>{data.embeddings?.note}</div>
        </div>
      )}
      <div style={{ marginBottom: 8 }}>Embeddings: <strong>{emb?.embeddings?.status || data?.embeddings?.status || '—'}</strong></div>
      {graph && (
        <div style={{ marginBottom: 12 }}>
          Graph (DERIVED): {graph.counts?.nodes} nodes / {graph.counts?.edges} edges
          <pre style={{ fontSize: 10, maxHeight: 160, overflow: 'auto', background: '#0a0b14', padding: 8 }}>{JSON.stringify((graph.edges || []).slice(0, 12), null, 2)}</pre>
        </div>
      )}
      <div style={{ display: 'flex', gap: 8 }}>
        <input value={q} onChange={e => setQ(e.target.value)} placeholder="Keyword search" style={{ flex: 1, background: '#0a0b14', border: '1px solid rgba(0,212,170,0.25)', color: '#D4DFE8', padding: 8, borderRadius: 6 }} />
        <button onClick={search} style={{ border: '1px solid #00D4AA', color: '#00D4AA', background: 'transparent', padding: '0 12px', borderRadius: 6 }}>Search</button>
      </div>
      <pre style={{ fontSize: 11, marginTop: 8 }}>{JSON.stringify(hits, null, 2)}</pre>
    </div>
  );
}

function Overview({ project, onTabChange }: { project: Project; onTabChange: (t: ProjTab) => void }) {
  const [events, setEvents] = useState<PEvent[]>([]);
  const [counts, setCounts] = useState({ tasks: 0, files: 0, repos: 0, memory: 0 });

  useEffect(() => {
    api<{ events: PEvent[] }>(`/solspire/projects/${project.id}/events`).then(r => setEvents(r.events.slice(0, 8))).catch(() => {});
    Promise.all([
      api<{ tasks: Task[] }>(`/solspire/projects/${project.id}/tasks`),
      api<{ files: PFile[] }>(`/solspire/projects/${project.id}/files`),
      api<{ repositories: Repo[] }>(`/solspire/projects/${project.id}/repositories`),
      api<{ memory: MemEntry[] }>(`/solspire/projects/${project.id}/memory`),
    ]).then(([t, f, r, m]) => setCounts({ tasks: t.tasks.length, files: f.files.length, repos: r.repositories.length, memory: m.memory.length })).catch(() => {});
  }, [project.id]);

  const desc = (project.metadata?.description as string) || '';

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
      {desc && <div style={{ ...S.card, borderColor: 'rgba(201,168,76,0.12)' }}><p style={{ fontFamily: 'sans-serif', fontSize: '13px', color: 'rgba(212,223,232,0.6)', margin: 0, lineHeight: '1.6' }}>{desc}</p></div>}

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4,1fr)', gap: '8px' }}>
        {[
          { label: 'Tasks', value: counts.tasks, tab: 'tasks' as ProjTab, color: '#00D4AA' },
          { label: 'Files', value: counts.files, tab: 'files' as ProjTab, color: '#C9A84C' },
          { label: 'Repos', value: counts.repos, tab: 'repos' as ProjTab, color: '#6A9FD8' },
          { label: 'Memory', value: counts.memory, tab: 'memory' as ProjTab, color: '#B08DE8' },
        ].map(c => (
          <button key={c.label} onClick={() => onTabChange(c.tab)} style={{ padding: '14px', background: 'rgba(14,17,32,0.75)', border: `1px solid ${c.color}22`, borderRadius: '10px', cursor: 'pointer', textAlign: 'left' }}>
            <p style={{ fontFamily: 'sans-serif', fontSize: '9px', letterSpacing: '0.2em', textTransform: 'uppercase', color: `${c.color}88`, margin: '0 0 4px' }}>{c.label}</p>
            <p style={{ fontFamily: '"Cinzel",serif', fontSize: '24px', color: c.color, margin: 0 }}>{c.value}</p>
          </button>
        ))}
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3,1fr)', gap: '8px' }}>
        {[
          { label: '⟐ New Workflow', tab: 'workflows' as ProjTab },
          { label: '☐ New Task', tab: 'tasks' as ProjTab },
          { label: '📄 New File', tab: 'files' as ProjTab },
        ].map(a => (
          <button key={a.label} onClick={() => onTabChange(a.tab)} style={{ ...S.btnTeal, justifyContent: 'center', display: 'flex' }}>{a.label}</button>
        ))}
      </div>

      <div style={S.card}>
        <span style={S.label}>Recent Activity</span>
        {events.length === 0 ? <p style={{ ...S.empty, padding: '20px 0' }}>No events yet</p> : (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
            {events.map(e => (
              <div key={e.id} style={{ display: 'flex', gap: '10px', alignItems: 'flex-start' }}>
                <span style={{ fontSize: '14px', flexShrink: 0, paddingTop: '1px' }}>{EVENT_ICONS[e.event_type] || '·'}</span>
                <div style={{ flex: 1 }}>
                  <p style={{ fontFamily: 'sans-serif', fontSize: '12px', color: 'rgba(212,223,232,0.7)', margin: '0 0 2px' }}>{e.summary}</p>
                  <p style={{ fontFamily: 'sans-serif', fontSize: '10px', color: 'rgba(212,223,232,0.3)', margin: 0 }}>{fmtDate(e.created_at)}</p>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

function Conversations({ project }: { project: Project }) {
  const [convs, setConvs] = useState<Conversation[]>([]);
  const [open, setOpen] = useState<Conversation | null>(null);
  const [newTitle, setNewTitle] = useState('');
  const [msgInput, setMsgInput] = useState('');
  const [loading, setLoading] = useState(false);
  const bottomRef = useRef<HTMLDivElement>(null);

  const load = () => api<{ conversations: Conversation[] }>(`/solspire/projects/${project.id}/conversations`).then(r => setConvs(r.conversations)).catch(() => {});
  useEffect(() => { load(); }, [project.id]);
  useEffect(() => { bottomRef.current?.scrollIntoView({ behavior: 'smooth' }); }, [open?.messages]);

  async function createConv() {
    if (!newTitle.trim()) return;
    await api(`/solspire/projects/${project.id}/conversations`, 'POST', { title: newTitle });
    setNewTitle(''); load();
  }

  async function sendMsg() {
    if (!open || !msgInput.trim()) return;
    setLoading(true);
    await api(`/solspire/projects/${project.id}/conversations/${open.id}/messages`, 'POST', { role: 'user', content: msgInput });
    setMsgInput('');
    const updated = await api<Conversation>(`/solspire/projects/${project.id}/conversations`).then(() =>
      api<{ conversations: Conversation[] }>(`/solspire/projects/${project.id}/conversations`).then(r => r.conversations.find(c => c.id === open.id))
    );
    if (updated) setOpen(updated);
    setLoading(false);
  }

  if (open) return (
    <div style={{ display: 'flex', flexDirection: 'column', height: 'calc(100dvh - 220px)', minHeight: '400px' }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '12px' }}>
        <button onClick={() => setOpen(null)} style={{ ...S.btnTeal, padding: '5px 10px' }}>← Back</button>
        <h3 style={{ fontFamily: '"Cinzel",serif', fontSize: '16px', color: '#C9A84C', margin: 0, flex: 1 }}>{open.title}</h3>
      </div>
      <div style={{ flex: 1, overflowY: 'auto', display: 'flex', flexDirection: 'column', gap: '10px', marginBottom: '12px', paddingRight: '4px' }}>
        {open.messages.length === 0 && <p style={S.empty}>No messages yet</p>}
        {open.messages.map((m, i) => (
          <div key={i} style={{ display: 'flex', justifyContent: m.role === 'user' ? 'flex-end' : 'flex-start' }}>
            <div style={{ maxWidth: '80%', padding: '10px 14px', background: m.role === 'user' ? 'rgba(0,212,170,0.1)' : 'rgba(14,17,32,0.85)', border: `1px solid ${m.role === 'user' ? 'rgba(0,212,170,0.2)' : 'rgba(255,255,255,0.07)'}`, borderRadius: '10px' }}>
              <p style={{ fontFamily: 'sans-serif', fontSize: '12px', color: 'rgba(212,223,232,0.82)', margin: '0 0 4px', lineHeight: '1.6', whiteSpace: 'pre-wrap' }}>{m.content}</p>
              <p style={{ fontFamily: 'sans-serif', fontSize: '9px', color: 'rgba(212,223,232,0.3)', margin: 0 }}>{m.role} · {fmtDate(m.ts)}</p>
            </div>
          </div>
        ))}
        <div ref={bottomRef} />
      </div>
      <div style={{ display: 'flex', gap: '8px' }}>
        <input value={msgInput} onChange={e => setMsgInput(e.target.value)} onKeyDown={e => { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); sendMsg(); } }}
          placeholder="Type a message… (Enter to send)" style={{ ...S.input, flex: 1 }} />
        <button onClick={sendMsg} disabled={loading} style={S.btnTeal}>{loading ? '…' : 'Send'}</button>
      </div>
    </div>
  );

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
      <div style={{ display: 'flex', gap: '8px' }}>
        <input value={newTitle} onChange={e => setNewTitle(e.target.value)} onKeyDown={e => { if (e.key === 'Enter') createConv(); }}
          placeholder="New conversation title…" style={{ ...S.input, flex: 1 }} />
        <button onClick={createConv} disabled={!newTitle.trim()} style={S.btnTeal}>+ New</button>
      </div>
      {convs.length === 0 ? <div style={S.empty}>No conversations yet</div> : convs.map(c => (
        <motion.div key={c.id} initial={{ opacity: 0 }} animate={{ opacity: 1 }}
          onClick={() => setOpen(c)}
          style={{ ...S.card, cursor: 'pointer', display: 'flex', alignItems: 'center', gap: '12px', transition: 'border-color 0.18s' }}
          onMouseEnter={e => (e.currentTarget.style.borderColor = 'rgba(0,212,170,0.28)')}
          onMouseLeave={e => (e.currentTarget.style.borderColor = 'rgba(0,212,170,0.1)')}>
          <span style={{ fontSize: '18px' }}>💬</span>
          <div style={{ flex: 1 }}>
            <p style={{ fontFamily: 'sans-serif', fontSize: '13px', color: 'rgba(212,223,232,0.85)', margin: '0 0 3px' }}>{c.title}</p>
            <p style={{ fontFamily: 'sans-serif', fontSize: '10px', color: 'rgba(212,223,232,0.35)', margin: 0 }}>{c.messages.length} messages · {fmtDate(c.updated_at)}</p>
          </div>
          <span style={{ color: 'rgba(0,212,170,0.4)', fontSize: '14px' }}>→</span>
        </motion.div>
      ))}
    </div>
  );
}

function Files({ project }: { project: Project }) {
  const [files, setFiles] = useState<PFile[]>([]);
  const [open, setOpen] = useState<PFile | null>(null);
  const [editContent, setEditContent] = useState('');
  const [creating, setCreating] = useState(false);
  const [newName, setNewName] = useState('');
  const [newContent, setNewContent] = useState('');
  const [saving, setSaving] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [uploadMsg, setUploadMsg] = useState<{ ok: boolean; text: string } | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const load = () => api<{ files: PFile[] }>(`/solspire/projects/${project.id}/files`).then(r => setFiles(r.files)).catch(() => {});
  useEffect(() => { load(); }, [project.id]);

  async function openFile(f: PFile) {
    const full = await api<PFile>(`/solspire/projects/${project.id}/files/${f.id}`);
    setOpen(full); setEditContent(full.content || '');
  }

  async function saveFile() {
    if (!open) return;
    setSaving(true);
    await api(`/solspire/projects/${project.id}/files/${open.id}`, 'PUT', { content: editContent });
    setSaving(false); setOpen(null); load();
  }

  async function createFile() {
    if (!newName.trim()) return;
    await api(`/solspire/projects/${project.id}/files`, 'POST', { name: newName, content: newContent });
    setCreating(false); setNewName(''); setNewContent(''); load();
  }

  async function deleteFile(id: string) {
    await api(`/solspire/projects/${project.id}/files/${id}`, 'DELETE');
    load();
  }

  async function uploadAttachment(file: File) {
    setUploading(true); setUploadMsg(null);
    try {
      const fd = new FormData();
      fd.append('file', file);
      const res = await fetch(`${ORACLE}/solspire/projects/${project.id}/files/upload`, { method: 'POST', headers: authHeaders(), body: fd });
      const data = await res.json().catch(() => ({}));
      if (!res.ok) throw new Error(data.detail || `${res.status}`);
      setUploadMsg({ ok: true, text: data.message || `'${file.name}' attached.` });
      load();
      setTimeout(() => setUploadMsg(null), 3000);
    } catch (e) {
      setUploadMsg({ ok: false, text: (e as Error).message || 'Upload failed.' });
    } finally {
      setUploading(false);
      if (fileInputRef.current) fileInputRef.current.value = '';
    }
  }

  if (open) return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
      <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
        <button onClick={() => setOpen(null)} style={{ ...S.btnTeal, padding: '5px 10px' }}>← Back</button>
        <span style={{ fontFamily: 'monospace', fontSize: '13px', color: '#C9A84C', flex: 1 }}>{open.name}</span>
        <button onClick={saveFile} disabled={saving} style={S.btnGold}>{saving ? 'Saving…' : 'Save'}</button>
      </div>
      <textarea value={editContent} onChange={e => setEditContent(e.target.value)} rows={24} style={S.textarea} />
    </div>
  );

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
      {/* Upload + create controls */}
      <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap', alignItems: 'center' }}>
        <input ref={fileInputRef} type="file" style={{ display: 'none' }}
          accept=".pdf,.docx,.txt,.md,.html,.htm,.json"
          onChange={e => { if (e.target.files?.[0]) uploadAttachment(e.target.files[0]); }} />
        <button onClick={() => fileInputRef.current?.click()} disabled={uploading}
          style={{ ...S.btnTeal, opacity: uploading ? 0.6 : 1 }}>
          {uploading ? 'Uploading…' : '⬆ Attach file'}
        </button>
        {!creating && (
          <button onClick={() => setCreating(true)} style={S.btnGold}>+ New file</button>
        )}
        <span style={{ fontFamily: 'sans-serif', fontSize: 9, color: 'rgba(212,223,232,0.3)' }}>PDF · DOCX · TXT · MD → extracted & stored in project</span>
      </div>
      {uploadMsg && (
        <div style={{ padding: '8px 12px', background: uploadMsg.ok ? 'rgba(0,212,170,0.08)' : 'rgba(200,72,72,0.08)', border: `1px solid ${uploadMsg.ok ? 'rgba(0,212,170,0.25)' : 'rgba(200,72,72,0.25)'}`, borderRadius: 7, fontFamily: 'sans-serif', fontSize: 11, color: uploadMsg.ok ? '#00D4AA' : 'rgba(200,72,72,0.9)' }}>
          {uploadMsg.ok ? '✓ ' : '⚠ '}{uploadMsg.text}
        </div>
      )}
      {creating ? (
        <div style={{ ...S.card, display: 'flex', flexDirection: 'column', gap: '8px' }}>
          <span style={S.label}>New File</span>
          <input value={newName} onChange={e => setNewName(e.target.value)} placeholder="filename.md" style={S.input} />
          <textarea value={newContent} onChange={e => setNewContent(e.target.value)} rows={8} placeholder="File content…" style={S.textarea} />
          <div style={{ display: 'flex', gap: '8px' }}>
            <button onClick={createFile} disabled={!newName.trim()} style={S.btnGold}>Create</button>
            <button onClick={() => setCreating(false)} style={S.btnDanger}>Cancel</button>
          </div>
        </div>
      ) : null}
      {files.length === 0 && !creating ? <div style={S.empty}>No files yet — attach a document or create a new file above.</div> : files.map(f => (
        <motion.div key={f.id} initial={{ opacity: 0 }} animate={{ opacity: 1 }}
          style={{ ...S.card, display: 'flex', alignItems: 'center', gap: '12px' }}>
          <span style={{ fontSize: '16px' }}>📄</span>
          <div style={{ flex: 1, cursor: 'pointer' }} onClick={() => openFile(f)}>
            <p style={{ fontFamily: 'monospace', fontSize: '13px', color: '#C9A84C', margin: '0 0 3px' }}>{f.name}</p>
            <p style={{ fontFamily: 'sans-serif', fontSize: '10px', color: 'rgba(212,223,232,0.35)', margin: 0 }}>{f.mime_type} · {fmtDate(f.updated_at)}</p>
          </div>
          <button onClick={() => openFile(f)} style={{ ...S.btnTeal, padding: '5px 10px' }}>Edit</button>
          <button onClick={() => deleteFile(f.id)} style={S.btnDanger}>✕</button>
        </motion.div>
      ))}
    </div>
  );
}

function Repos({ project }: { project: Project }) {
  const [repos, setRepos] = useState<Repo[]>([]);
  const [linking, setLinking] = useState(false);
  const [owner, setOwner] = useState(''); const [repo, setRepo] = useState(''); const [branch, setBranch] = useState('main'); const [label, setLabel] = useState('');
  const [browsing, setBrowsing] = useState<Repo | null>(null);
  const [tree, setTree] = useState<{ path: string; type: string; size: number | null }[]>([]);
  const [fileContent, setFileContent] = useState<string | null>(null);
  const [filePath, setFilePath] = useState('');
  const [ghLoading, setGhLoading] = useState(false);

  const load = () => api<{ repositories: Repo[] }>(`/solspire/projects/${project.id}/repositories`).then(r => setRepos(r.repositories)).catch(() => {});
  useEffect(() => { load(); }, [project.id]);

  async function linkRepo() {
    await api(`/solspire/projects/${project.id}/repositories`, 'POST', { owner, repo, branch, label });
    setLinking(false); setOwner(''); setRepo(''); setBranch('main'); setLabel(''); load();
  }

  async function browse(r: Repo) {
    setBrowsing(r); setTree([]); setFileContent(null); setFilePath('');
    setGhLoading(true);
    const res = await api<{ ok: boolean; files: typeof tree }>('/solspire/tools/github/tree', 'POST', { owner: r.owner, repo: r.repo, branch: r.branch }).catch(() => ({ ok: false, files: [] }));
    setTree(res.files || []); setGhLoading(false);
  }

  async function readFile(path: string) {
    if (!browsing) return;
    setGhLoading(true); setFilePath(path); setFileContent(null);
    const res = await api<{ ok: boolean; content: string }>('/solspire/tools/github/read', 'POST', { owner: browsing.owner, repo: browsing.repo, path, branch: browsing.branch }).catch(() => ({ ok: false, content: '' }));
    setFileContent(res.content || ''); setGhLoading(false);
  }

  if (browsing) return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
      <div style={{ display: 'flex', gap: '8px', alignItems: 'center', flexWrap: 'wrap' }}>
        <button onClick={() => { setBrowsing(null); setFileContent(null); setFilePath(''); }} style={{ ...S.btnTeal, padding: '5px 10px' }}>← Back</button>
        {filePath && <button onClick={() => { setFileContent(null); setFilePath(''); }} style={{ ...S.btnTeal, padding: '5px 10px' }}>⟁ Tree</button>}
        <span style={{ fontFamily: 'monospace', fontSize: '12px', color: '#6A9FD8' }}>{browsing.owner}/{browsing.repo}@{browsing.branch}</span>
        {filePath && <span style={{ fontFamily: 'monospace', fontSize: '11px', color: 'rgba(212,223,232,0.5)' }}>/{filePath}</span>}
      </div>
      {ghLoading && <p style={{ ...S.empty, padding: '20px 0' }}>Loading…</p>}
      {!ghLoading && !fileContent && tree.map(e => (
        <div key={e.path} onClick={() => e.type === 'blob' && readFile(e.path)}
          style={{ display: 'flex', gap: '10px', padding: '6px 10px', borderRadius: '6px', cursor: e.type === 'blob' ? 'pointer' : 'default',
            background: e.type === 'blob' ? 'transparent' : 'rgba(201,168,76,0.03)' }}
          onMouseEnter={el => { if (e.type === 'blob') el.currentTarget.style.background = 'rgba(106,159,216,0.07)'; }}
          onMouseLeave={el => { el.currentTarget.style.background = e.type === 'blob' ? 'transparent' : 'rgba(201,168,76,0.03)'; }}>
          <span style={{ fontSize: '11px', color: e.type === 'tree' ? '#C9A84C' : 'rgba(212,223,232,0.4)', width: '14px' }}>{e.type === 'tree' ? '▸' : '·'}</span>
          <span style={{ fontFamily: 'monospace', fontSize: '12px', color: e.type === 'tree' ? 'rgba(201,168,76,0.75)' : 'rgba(212,223,232,0.65)', flex: 1 }}>{e.path}</span>
          {e.size != null && <span style={{ fontFamily: 'monospace', fontSize: '10px', color: 'rgba(212,223,232,0.25)' }}>{e.size > 1024 ? `${(e.size/1024).toFixed(1)}k` : `${e.size}b`}</span>}
        </div>
      ))}
      {!ghLoading && fileContent !== null && (
        <pre style={{ fontFamily: 'monospace', fontSize: '12px', color: 'rgba(212,223,232,0.78)', background: 'rgba(0,0,0,0.35)', padding: '14px', borderRadius: '8px', margin: 0, whiteSpace: 'pre-wrap', wordBreak: 'break-word', maxHeight: '500px', overflowY: 'auto', border: '1px solid rgba(106,159,216,0.1)' }}>
          {fileContent}
        </pre>
      )}
    </div>
  );

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
      {linking ? (
        <div style={{ ...S.card, display: 'flex', flexDirection: 'column', gap: '8px' }}>
          <span style={S.label}>Link Repository</span>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '8px' }}>
            <input value={owner} onChange={e => setOwner(e.target.value)} placeholder="owner / org" style={S.input} />
            <input value={repo} onChange={e => setRepo(e.target.value)} placeholder="repository" style={S.input} />
            <input value={branch} onChange={e => setBranch(e.target.value)} placeholder="branch" style={S.input} />
            <input value={label} onChange={e => setLabel(e.target.value)} placeholder="label (optional)" style={S.input} />
          </div>
          <div style={{ display: 'flex', gap: '8px' }}>
            <button onClick={linkRepo} disabled={!owner.trim() || !repo.trim()} style={S.btnTeal}>Link</button>
            <button onClick={() => setLinking(false)} style={S.btnDanger}>Cancel</button>
          </div>
        </div>
      ) : (
        <button onClick={() => setLinking(true)} style={{ ...S.btnTeal, alignSelf: 'flex-start' }}>⟁ Link Repository</button>
      )}
      {repos.length === 0 ? <div style={S.empty}>No repos linked yet</div> : repos.map(r => (
        <motion.div key={r.id} initial={{ opacity: 0 }} animate={{ opacity: 1 }}
          style={{ ...S.card, display: 'flex', alignItems: 'center', gap: '12px' }}>
          <span style={{ fontSize: '16px' }}>⟁</span>
          <div style={{ flex: 1 }}>
            <p style={{ fontFamily: 'monospace', fontSize: '13px', color: '#6A9FD8', margin: '0 0 3px' }}>{r.owner}/{r.repo}</p>
            <p style={{ fontFamily: 'sans-serif', fontSize: '10px', color: 'rgba(212,223,232,0.35)', margin: 0 }}>@{r.branch} · {fmtDate(r.created_at)}</p>
          </div>
          <button onClick={() => browse(r)} style={{ ...S.btnTeal, padding: '5px 10px' }}>Browse</button>
          <button onClick={() => api(`/solspire/projects/${project.id}/repositories/${r.id}`, 'DELETE').then(load)} style={S.btnDanger}>✕</button>
        </motion.div>
      ))}
    </div>
  );
}

function Tasks({ project }: { project: Project }) {
  const [tasks, setTasks] = useState<Task[]>([]);
  const [creating, setCreating] = useState(false);
  const [title, setTitle] = useState(''); const [desc, setDesc] = useState(''); const [priority, setPriority] = useState('normal');

  const load = () => api<{ tasks: Task[] }>(`/solspire/projects/${project.id}/tasks`).then(r => setTasks(r.tasks)).catch(() => {});
  useEffect(() => { load(); }, [project.id]);

  async function create() {
    if (!title.trim()) return;
    await api(`/solspire/projects/${project.id}/tasks`, 'POST', { title, description: desc, priority });
    setTitle(''); setDesc(''); setPriority('normal'); setCreating(false); load();
  }

  async function complete(id: string) { await api(`/solspire/projects/${project.id}/tasks/${id}`, 'PUT', { status: 'done' }); load(); }
  async function del(id: string) { await api(`/solspire/projects/${project.id}/tasks/${id}`, 'DELETE'); load(); }

  const open = tasks.filter(t => t.status === 'open');
  const done = tasks.filter(t => t.status === 'done');

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
      {creating ? (
        <div style={{ ...S.card, display: 'flex', flexDirection: 'column', gap: '8px' }}>
          <span style={S.label}>New Task</span>
          <input value={title} onChange={e => setTitle(e.target.value)} placeholder="Task title" style={S.input} />
          <textarea value={desc} onChange={e => setDesc(e.target.value)} rows={3} placeholder="Description (optional)" style={S.textarea} />
          <div style={{ display: 'flex', gap: '6px' }}>
            {['low','normal','high'].map(p => (
              <button key={p} onClick={() => setPriority(p)} style={{ padding: '5px 12px', borderRadius: '15px', border: `1px solid ${PRIORITY_COLORS[p]}44`, background: priority === p ? `${PRIORITY_COLORS[p]}18` : 'transparent', color: priority === p ? PRIORITY_COLORS[p] : 'rgba(212,223,232,0.4)', cursor: 'pointer', fontFamily: 'sans-serif', fontSize: '10px' }}>{p}</button>
            ))}
          </div>
          <div style={{ display: 'flex', gap: '8px' }}>
            <button onClick={create} disabled={!title.trim()} style={S.btnTeal}>Create</button>
            <button onClick={() => setCreating(false)} style={S.btnDanger}>Cancel</button>
          </div>
        </div>
      ) : (
        <button onClick={() => setCreating(true)} style={{ ...S.btnTeal, alignSelf: 'flex-start' }}>+ New Task</button>
      )}
      {tasks.length === 0 && !creating && <div style={S.empty}>No tasks yet</div>}
      {open.length > 0 && (
        <div>
          <span style={S.label}>Open ({open.length})</span>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
            {open.map(t => (
              <motion.div key={t.id} initial={{ opacity: 0 }} animate={{ opacity: 1 }}
                style={{ ...S.card, display: 'flex', gap: '12px', alignItems: 'flex-start', borderColor: `${PRIORITY_COLORS[t.priority]}22` }}>
                <div style={{ flex: 1 }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '4px' }}>
                    <span style={{ padding: '1px 6px', borderRadius: '8px', fontSize: '9px', background: `${PRIORITY_COLORS[t.priority]}18`, color: PRIORITY_COLORS[t.priority], fontFamily: 'sans-serif' }}>{t.priority}</span>
                    <p style={{ fontFamily: 'sans-serif', fontSize: '13px', color: 'rgba(212,223,232,0.82)', margin: 0 }}>{t.title}</p>
                  </div>
                  {t.description && <p style={{ fontFamily: 'sans-serif', fontSize: '11px', color: 'rgba(212,223,232,0.4)', margin: 0 }}>{t.description}</p>}
                </div>
                <div style={{ display: 'flex', gap: '6px', flexShrink: 0 }}>
                  <button onClick={() => complete(t.id)} style={{ ...S.btnTeal, padding: '4px 10px' }}>✓</button>
                  <button onClick={() => del(t.id)} style={S.btnDanger}>✕</button>
                </div>
              </motion.div>
            ))}
          </div>
        </div>
      )}
      {done.length > 0 && (
        <div>
          <span style={{ ...S.label, color: 'rgba(76,175,80,0.45)' }}>Completed ({done.length})</span>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '6px', opacity: 0.6 }}>
            {done.map(t => (
              <div key={t.id} style={{ ...S.card, display: 'flex', gap: '12px', alignItems: 'center', borderColor: 'rgba(76,175,80,0.1)' }}>
                <span style={{ color: '#4CAF50' }}>✓</span>
                <p style={{ fontFamily: 'sans-serif', fontSize: '12px', color: 'rgba(212,223,232,0.5)', margin: 0, flex: 1, textDecoration: 'line-through' }}>{t.title}</p>
                <button onClick={() => del(t.id)} style={S.btnDanger}>✕</button>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

function Workflows({ project }: { project: Project }) {
  const [request, setRequest] = useState('');
  const [prov, setProv] = useState('gemini');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<RunResult | null>(null);
  const [error, setError] = useState<string | null>(null);

  async function run() {
    if (!request.trim()) return;
    setLoading(true); setResult(null); setError(null);
    try {
      const r = await api<RunResult>(`/solspire/projects/${project.id}/run`, 'POST', { request, provider: prov });
      setResult(r);
    } catch (e) { setError(e instanceof Error ? e.message : String(e)); }
    setLoading(false);
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
      <div style={{ display: 'flex', gap: '6px', flexWrap: 'wrap' }}>
        {['gemini','openai','anthropic','openrouter','ollama'].map(p => (
          <button key={p} onClick={() => setProv(p)} style={{ padding: '5px 12px', borderRadius: '20px', border: `1px solid ${prov === p ? '#00D4AA' : 'rgba(0,212,170,0.2)'}`, background: prov === p ? 'rgba(0,212,170,0.1)' : 'transparent', color: prov === p ? '#00D4AA' : 'rgba(212,223,232,0.4)', cursor: 'pointer', fontFamily: 'sans-serif', fontSize: '10px' }}>{p}</button>
        ))}
      </div>
      <textarea value={request} onChange={e => setRequest(e.target.value)}
        onKeyDown={e => { if (e.key === 'Enter' && (e.metaKey || e.ctrlKey)) run(); }}
        placeholder={`Issue a command in the context of "${project.name}"…\n\n⌘↵ to execute`}
        rows={5} style={S.textarea} />
      <div style={{ display: 'flex', gap: '8px' }}>
        <button onClick={run} disabled={loading || !request.trim()}
          style={{ ...S.btnTeal, flex: 1, justifyContent: 'center', display: 'flex', padding: '12px', fontSize: '11px', letterSpacing: '0.2em' }}>
          {loading ? '⟐ Running…' : '⟐ Execute  (⌘↵)'}
        </button>
        {result && <button onClick={() => { setResult(null); setError(null); setRequest(''); }} style={{ ...S.btnDanger, alignSelf: 'stretch' }}>Clear</button>}
      </div>
      {error && <div style={{ padding: '12px', background: 'rgba(200,72,72,0.08)', border: '1px solid rgba(200,72,72,0.2)', borderRadius: '8px' }}><p style={{ fontFamily: 'sans-serif', fontSize: '12px', color: '#C84848', margin: 0 }}>⚠ {error}</p></div>}
      {result && (
        <motion.div initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
          <div style={{ ...S.card, display: 'flex', gap: '16px', flexWrap: 'wrap', alignItems: 'center' }}>
            <div><span style={S.label}>Intent</span><p style={{ fontFamily: '"Cinzel",serif', fontSize: '14px', color: '#00D4AA', margin: 0 }}>{result.intent}</p></div>
            <div><span style={S.label}>Steps</span><p style={{ fontFamily: 'sans-serif', fontSize: '13px', color: 'rgba(212,223,232,0.7)', margin: 0 }}>{result.plan.steps.length}</p></div>
            <div><span style={S.label}>Elapsed</span><p style={{ fontFamily: 'sans-serif', fontSize: '13px', color: 'rgba(212,223,232,0.7)', margin: 0 }}>{result.elapsed_ms}ms</p></div>
            <span style={{ padding: '2px 8px', borderRadius: '10px', fontSize: '10px', background: result.ok ? 'rgba(76,175,80,0.12)' : 'rgba(200,72,72,0.12)', color: result.ok ? '#4CAF50' : '#C84848', border: `1px solid ${result.ok ? 'rgba(76,175,80,0.3)' : 'rgba(200,72,72,0.3)'}`, fontFamily: 'sans-serif', letterSpacing: '0.12em' }}>{result.execution.status}</span>
          </div>
          {result.plan.steps.length > 0 && (
            <div style={S.card}>
              <span style={S.label}>Plan</span>
              {result.plan.steps.map((s, i) => (
                <div key={i} style={{ display: 'flex', gap: '8px', marginBottom: i < result.plan.steps.length - 1 ? '6px' : 0 }}>
                  <span style={{ fontFamily: '"Cinzel",serif', fontSize: '10px', color: 'rgba(201,168,76,0.5)', minWidth: '18px' }}>{i+1}.</span>
                  <span style={{ fontFamily: 'monospace', fontSize: '11px', color: '#6A9FD8', padding: '1px 5px', background: 'rgba(106,159,216,0.1)', borderRadius: '4px', marginRight: '6px' }}>{s.tool}</span>
                  <span style={{ fontFamily: 'sans-serif', fontSize: '12px', color: 'rgba(212,223,232,0.6)' }}>{s.description}</span>
                </div>
              ))}
            </div>
          )}
          {result.execution.results.length > 0 && (
            <div style={S.card}>
              <span style={S.label}>Output</span>
              {result.execution.results.map((r, i) => {
                const text = typeof r.result === 'string' ? r.result : JSON.stringify(r, null, 2);
                return (
                  <div key={i} style={{ marginBottom: i < result.execution.results.length - 1 ? '10px' : 0 }}>
                    <p style={{ fontFamily: 'sans-serif', fontSize: '9px', color: 'rgba(212,223,232,0.35)', margin: '0 0 4px' }}>Step {(r.step as number) + 1} · {String(r.tool)}</p>
                    <pre style={{ fontFamily: 'monospace', fontSize: '12px', color: 'rgba(212,223,232,0.75)', background: 'rgba(0,0,0,0.3)', padding: '10px', borderRadius: '6px', margin: 0, whiteSpace: 'pre-wrap', wordBreak: 'break-word', maxHeight: '280px', overflowY: 'auto' }}>
                      {text.slice(0, 2500)}{text.length > 2500 ? '\n[…truncated]' : ''}
                    </pre>
                  </div>
                );
              })}
            </div>
          )}
        </motion.div>
      )}
    </div>
  );
}

function Memory({ project }: { project: Project }) {
  const [entries, setEntries] = useState<MemEntry[]>([]);
  const [q, setQ] = useState('');
  const [creating, setCreating] = useState(false);
  const [editing, setEditing] = useState<MemEntry | null>(null);
  const [title, setTitle] = useState(''); const [content, setContent] = useState(''); const [tags, setTags] = useState('');

  const load = (query = '') => api<{ memory: MemEntry[] }>(`/solspire/projects/${project.id}/memory?q=${encodeURIComponent(query)}`).then(r => setEntries(r.memory)).catch(() => {});
  useEffect(() => { load(); }, [project.id]);
  useEffect(() => { const t = setTimeout(() => load(q), 300); return () => clearTimeout(t); }, [q]);

  async function save() {
    const tagList = tags.split(',').map(t => t.trim()).filter(Boolean);
    if (editing) {
      await api(`/solspire/projects/${project.id}/memory/${editing.id}`, 'PUT', { title, content, tags: tagList });
      setEditing(null);
    } else {
      await api(`/solspire/projects/${project.id}/memory`, 'POST', { title, content, tags: tagList });
      setCreating(false);
    }
    setTitle(''); setContent(''); setTags(''); load();
  }

  function startEdit(e: MemEntry) { setEditing(e); setTitle(e.title); setContent(e.content); setTags(e.tags.join(', ')); setCreating(false); }

  async function del(id: string) { await api(`/solspire/projects/${project.id}/memory/${id}`, 'DELETE'); load(); }

  const isEditorOpen = creating || !!editing;

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
      <div style={{ display: 'flex', gap: '8px' }}>
        <input value={q} onChange={e => setQ(e.target.value)} placeholder="Search memory…" style={{ ...S.input, flex: 1 }} />
        {!isEditorOpen && <button onClick={() => { setCreating(true); setEditing(null); setTitle(''); setContent(''); setTags(''); }} style={S.btnGold}>+ Add</button>}
      </div>
      {isEditorOpen && (
        <div style={{ ...S.card, display: 'flex', flexDirection: 'column', gap: '8px' }}>
          <span style={S.label}>{editing ? 'Edit Memory' : 'New Memory'}</span>
          <input value={title} onChange={e => setTitle(e.target.value)} placeholder="Title" style={S.input} />
          <textarea value={content} onChange={e => setContent(e.target.value)} rows={5} placeholder="Content / knowledge…" style={S.textarea} />
          <input value={tags} onChange={e => setTags(e.target.value)} placeholder="Tags (comma-separated)" style={S.input} />
          <div style={{ display: 'flex', gap: '8px' }}>
            <button onClick={save} disabled={!title.trim()} style={S.btnGold}>Save</button>
            <button onClick={() => { setCreating(false); setEditing(null); }} style={S.btnDanger}>Cancel</button>
          </div>
        </div>
      )}
      {entries.length === 0 && !isEditorOpen ? <div style={S.empty}>No memory entries yet</div> : entries.map(e => (
        <motion.div key={e.id} initial={{ opacity: 0 }} animate={{ opacity: 1 }} style={{ ...S.card, display: 'flex', gap: '12px' }}>
          <span style={{ fontSize: '16px', flexShrink: 0 }}>∞</span>
          <div style={{ flex: 1, minWidth: 0 }}>
            <p style={{ fontFamily: 'sans-serif', fontSize: '13px', color: 'rgba(212,223,232,0.85)', margin: '0 0 4px' }}>{e.title}</p>
            <p style={{ fontFamily: 'sans-serif', fontSize: '11px', color: 'rgba(212,223,232,0.45)', margin: '0 0 6px', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{e.content}</p>
            {e.tags.length > 0 && <div style={{ display: 'flex', gap: '4px', flexWrap: 'wrap' }}>
              {e.tags.map(t => <span key={t} style={{ padding: '1px 6px', borderRadius: '8px', fontSize: '9px', background: 'rgba(176,141,232,0.12)', color: '#B08DE8', fontFamily: 'sans-serif' }}>{t}</span>)}
            </div>}
          </div>
          <div style={{ display: 'flex', gap: '6px', flexShrink: 0, alignSelf: 'flex-start' }}>
            <button onClick={() => startEdit(e)} style={{ ...S.btnGold, padding: '4px 8px' }}>✎</button>
            <button onClick={() => del(e.id)} style={S.btnDanger}>✕</button>
          </div>
        </motion.div>
      ))}
    </div>
  );
}

function Events({ project }: { project: Project }) {
  const [events, setEvents] = useState<PEvent[]>([]);
  const [filter, setFilter] = useState('');

  const load = () => api<{ events: PEvent[] }>(`/solspire/projects/${project.id}/events${filter ? `?event_type=${filter}` : ''}`).then(r => setEvents(r.events)).catch(() => {});
  useEffect(() => { load(); }, [project.id, filter]);

  const types = Array.from(new Set(events.map(e => e.event_type)));

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
      <div style={{ display: 'flex', gap: '6px', flexWrap: 'wrap' }}>
        <button onClick={() => setFilter('')} style={{ padding: '4px 10px', borderRadius: '15px', border: `1px solid ${!filter ? '#00D4AA' : 'rgba(0,212,170,0.2)'}`, background: !filter ? 'rgba(0,212,170,0.1)' : 'transparent', color: !filter ? '#00D4AA' : 'rgba(212,223,232,0.4)', cursor: 'pointer', fontFamily: 'sans-serif', fontSize: '10px' }}>All</button>
        {types.map(t => (
          <button key={t} onClick={() => setFilter(t)} style={{ padding: '4px 10px', borderRadius: '15px', border: `1px solid ${filter === t ? '#C9A84C' : 'rgba(201,168,76,0.15)'}`, background: filter === t ? 'rgba(201,168,76,0.1)' : 'transparent', color: filter === t ? '#C9A84C' : 'rgba(212,223,232,0.4)', cursor: 'pointer', fontFamily: 'sans-serif', fontSize: '10px' }}>{t.replace(/_/g, ' ')}</button>
        ))}
      </div>
      {events.length === 0 ? <div style={S.empty}>No events yet</div> : (
        <div style={{ position: 'relative', paddingLeft: '20px' }}>
          <div style={{ position: 'absolute', left: '7px', top: 0, bottom: 0, width: '1px', background: 'rgba(0,212,170,0.1)' }} />
          <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
            {events.map(e => (
              <div key={e.id} style={{ position: 'relative' }}>
                <div style={{ position: 'absolute', left: '-16px', top: '6px', width: '8px', height: '8px', borderRadius: '50%', background: '#0A0B14', border: '1px solid rgba(0,212,170,0.4)' }} />
                <div style={S.card}>
                  <div style={{ display: 'flex', gap: '8px', alignItems: 'flex-start' }}>
                    <span style={{ fontSize: '14px' }}>{EVENT_ICONS[e.event_type] || '·'}</span>
                    <div style={{ flex: 1 }}>
                      <p style={{ fontFamily: 'sans-serif', fontSize: '12px', color: 'rgba(212,223,232,0.75)', margin: '0 0 3px' }}>{e.summary}</p>
                      <p style={{ fontFamily: 'sans-serif', fontSize: '9px', letterSpacing: '0.15em', color: 'rgba(212,223,232,0.3)', margin: 0, textTransform: 'uppercase' }}>{e.event_type.replace(/_/g,' ')} · {fmtDate(e.created_at)}</p>
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

function Settings({ project, onProjectUpdated, onArchive }: { project: Project; onProjectUpdated: (p: Project) => void; onArchive: () => void }) {
  const [name, setName] = useState(project.name);
  const [desc, setDesc] = useState((project.metadata?.description as string) || '');
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);

  async function save() {
    setSaving(true);
    await api(`/solspire/projects/${project.id}`, 'PUT', { name, description: desc });
    setSaving(false); setSaved(true); setTimeout(() => setSaved(false), 2000);
    onProjectUpdated({ ...project, name, metadata: { ...project.metadata, description: desc } });
  }

  async function archive() {
    if (!confirm('Archive this project? You can unarchive it later.')) return;
    await api(`/solspire/projects/${project.id}/archive`, 'POST');
    onArchive();
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '16px', maxWidth: '560px' }}>
      <div style={S.card}>
        <span style={S.label}>Project Name</span>
        <input value={name} onChange={e => setName(e.target.value)} style={S.input} />
      </div>
      <div style={S.card}>
        <span style={S.label}>Description</span>
        <textarea value={desc} onChange={e => setDesc(e.target.value)} rows={4} placeholder="What is this project about?" style={S.textarea} />
      </div>
      <div style={S.card}>
        <span style={S.label}>Status</span>
        <div style={{ display: 'flex', gap: '6px' }}>
          {['active','paused'].map(s => (
            <button key={s} onClick={() => api(`/solspire/projects/${project.id}`, 'PUT', { status: s })}
              style={{ padding: '6px 14px', borderRadius: '15px', border: `1px solid ${project.status === s ? STATUS_COLORS[s] : 'rgba(255,255,255,0.1)'}`, background: project.status === s ? `${STATUS_COLORS[s]}18` : 'transparent', color: project.status === s ? STATUS_COLORS[s] : 'rgba(212,223,232,0.4)', cursor: 'pointer', fontFamily: 'sans-serif', fontSize: '10px' }}>{s}</button>
          ))}
        </div>
      </div>
      <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
        <button onClick={save} disabled={saving} style={S.btnTeal}>{saving ? 'Saving…' : saved ? '✓ Saved' : 'Save Changes'}</button>
      </div>
      <div style={{ ...S.card, borderColor: 'rgba(200,72,72,0.15)', marginTop: '16px' }}>
        <span style={{ ...S.label, color: 'rgba(200,72,72,0.5)' }}>Danger Zone</span>
        <p style={{ fontFamily: 'sans-serif', fontSize: '12px', color: 'rgba(212,223,232,0.4)', margin: '0 0 12px' }}>Archiving hides the project from the active list. All data is preserved.</p>
        <button onClick={archive} style={S.btnDanger}>Archive Project</button>
      </div>
    </div>
  );
}

// ── Main Dashboard ────────────────────────────────────────────────────────────

const TABS: { id: ProjTab; label: string; sigil: string }[] = [
  { id: 'overview',       label: 'Overview',       sigil: '◈' },
  { id: 'weaver',         label: 'Weaver',         sigil: '⟐' },
  { id: 'knowledge',      label: 'Knowledge',      sigil: '◈' },
  { id: 'conversations',  label: 'Conversations',  sigil: '💬' },
  { id: 'files',          label: 'Files',          sigil: '📄' },
  { id: 'repos',          label: 'Repos',          sigil: '⟁' },
  { id: 'tasks',          label: 'Tasks',          sigil: '☐' },
  { id: 'workflows',      label: 'Workflows',      sigil: '⟐' },
  { id: 'memory',         label: 'Memory',         sigil: '∞' },
  { id: 'events',         label: 'Events',         sigil: '◎' },
  { id: 'settings',       label: 'Settings',       sigil: '⚙' },
];

interface Props {
  project: Project;
  onBack: () => void;
  onProjectUpdated: (p: Project) => void;
}

export default function ProjectDashboard({ project, onBack, onProjectUpdated }: Props) {
  const [tab, setTab] = useState<ProjTab>('overview');
  const [currentProject, setCurrentProject] = useState(project);
  const tabBarRef = useRef<HTMLDivElement>(null);

  useEffect(() => { setCurrentProject(project); }, [project]);

  // Scroll active tab into view on mobile
  useEffect(() => {
    if (!tabBarRef.current) return;
    const active = tabBarRef.current.querySelector('[data-active="true"]') as HTMLElement | null;
    active?.scrollIntoView({ behavior: 'smooth', inline: 'nearest', block: 'nearest' });
  }, [tab]);

  const handleProjectUpdated = (p: Project) => { setCurrentProject(p); onProjectUpdated(p); };

  return (
    <div style={{ minHeight: '100dvh', background: '#0A0B14', display: 'flex', flexDirection: 'column' }}>

      {/* Header */}
      <div style={{ padding: '12px 16px', borderBottom: '1px solid rgba(0,212,170,0.08)', display: 'flex', alignItems: 'center', gap: '12px', background: 'rgba(10,11,20,0.95)', backdropFilter: 'blur(12px)', position: 'sticky', top: 0, zIndex: 20, flexShrink: 0 }}>
        <button onClick={onBack} style={{ background: 'none', border: 'none', color: 'rgba(0,212,170,0.6)', cursor: 'pointer', fontSize: '18px', padding: '2px 8px 2px 0', lineHeight: 1 }}>←</button>
        <div style={{ flex: 1, minWidth: 0 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <h2 style={{ fontFamily: '"Cinzel",serif', fontSize: '16px', color: '#C9A84C', margin: 0, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{currentProject.name}</h2>
            <span style={{ padding: '1px 7px', borderRadius: '8px', fontSize: '9px', background: `${STATUS_COLORS[currentProject.status] || '#888'}18`, color: STATUS_COLORS[currentProject.status] || '#888', border: `1px solid ${STATUS_COLORS[currentProject.status] || '#888'}33`, fontFamily: 'sans-serif', letterSpacing: '0.12em', flexShrink: 0, textTransform: 'uppercase' }}>{currentProject.status}</span>
          </div>
          <p style={{ fontFamily: 'sans-serif', fontSize: '9px', letterSpacing: '0.2em', textTransform: 'uppercase', color: 'rgba(201,168,76,0.4)', margin: 0 }}>SolSpire Console · Project View</p>
        </div>
        <button onClick={() => setTab('settings')} style={{ background: 'none', border: 'none', color: 'rgba(212,223,232,0.3)', cursor: 'pointer', fontSize: '16px', padding: '4px' }}>⚙</button>
      </div>

      {/* Tab Bar */}
      <div ref={tabBarRef} style={{ display: 'flex', overflowX: 'auto', borderBottom: '1px solid rgba(0,212,170,0.08)', background: 'rgba(10,11,20,0.9)', padding: '0 8px', scrollbarWidth: 'none', flexShrink: 0, WebkitOverflowScrolling: 'touch' as unknown as string }}>
        {TABS.map(t => (
          <button key={t.id} data-active={tab === t.id} onClick={() => setTab(t.id)} style={{ padding: '10px 14px', background: 'none', border: 'none', borderBottom: `2px solid ${tab === t.id ? '#00D4AA' : 'transparent'}`, color: tab === t.id ? '#00D4AA' : 'rgba(212,223,232,0.4)', cursor: 'pointer', fontFamily: 'sans-serif', fontSize: '10px', letterSpacing: '0.12em', textTransform: 'uppercase', whiteSpace: 'nowrap', transition: 'all 0.15s', flexShrink: 0 }}>
            <span style={{ marginRight: '4px' }}>{t.sigil}</span>{t.label}
          </button>
        ))}
      </div>

      {/* Content */}
      <div style={{ flex: 1, overflowY: 'auto', padding: '20px 16px', maxWidth: '880px', width: '100%', margin: '0 auto', boxSizing: 'border-box' }}>
        <AnimatePresence mode="wait">
          {tab === 'knowledge'     && <motion.div key="kn" initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0 }}><KnowledgePanel project={currentProject} /></motion.div>}
          {tab === 'weaver'        && <motion.div key="wv" initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0 }}><WeaverPanel project={currentProject} /></motion.div>}
          {tab === 'overview'      && <motion.div key="ov" initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0 }}><Overview project={currentProject} onTabChange={setTab} /></motion.div>}
          {tab === 'conversations' && <motion.div key="cv" initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0 }}><Conversations project={currentProject} /></motion.div>}
          {tab === 'files'         && <motion.div key="fi" initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0 }}><Files project={currentProject} /></motion.div>}
          {tab === 'repos'         && <motion.div key="re" initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0 }}><Repos project={currentProject} /></motion.div>}
          {tab === 'tasks'         && <motion.div key="ta" initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0 }}><Tasks project={currentProject} /></motion.div>}
          {tab === 'workflows'     && <motion.div key="wf" initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0 }}><Workflows project={currentProject} /></motion.div>}
          {tab === 'memory'        && <motion.div key="me" initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0 }}><Memory project={currentProject} /></motion.div>}
          {tab === 'events'        && <motion.div key="ev" initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0 }}><Events project={currentProject} /></motion.div>}
          {tab === 'settings'      && <motion.div key="se" initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0 }}><Settings project={currentProject} onProjectUpdated={handleProjectUpdated} onArchive={onBack} /></motion.div>}
        </AnimatePresence>
      </div>
    </div>
  );
}
