import React, { useState, useEffect, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';

const ORACLE_URL = import.meta.env.VITE_ORACLE_URL || 'http://localhost:8000';

type IntentType = 'Question' | 'Coding' | 'Research' | 'Automation' | 'Workflow' | 'Project' | 'Memory';
type ExecStatus = 'pending' | 'running' | 'paused' | 'completed' | 'failed' | 'cancelled';

interface Project {
  id: string;
  name: string;
  status: string;
  created_at: number;
  updated_at: number;
  metadata: Record<string, unknown>;
  conversations: Array<{ role: string; content: string; ts: number }>;
}

interface Execution {
  id: string;
  plan_id: string;
  status: ExecStatus;
  started_at: number;
  completed_at: number | null;
  results: Array<Record<string, unknown>>;
  error: string | null;
  retries: number;
}

interface RunResult {
  ok: boolean;
  intent: IntentType;
  plan: { id: string; request: string; intent: string; steps: Array<{ tool: string; description: string }> };
  execution: Execution;
  elapsed_ms: number;
}

interface KernelStatus {
  version: Record<string, string>;
  providers: { active: string; available: string[]; token_usage: Record<string, number> };
  projects: { active_count: number };
  executions: { total: number; active: number; by_status: Record<string, number> };
  milestone: number;
}

interface GhRepo {
  name: string;
  full_name: string;
  url: string;
  description: string | null;
  language: string | null;
  stars: number;
  updated_at: string;
}

interface GhEntry {
  path: string;
  type: 'blob' | 'tree';
  size: number | null;
}

const INTENT_COLORS: Record<IntentType, string> = {
  Question:   '#00D4AA',
  Coding:     '#6A9FD8',
  Research:   '#B08DE8',
  Automation: '#E88C6A',
  Workflow:   '#C9A84C',
  Project:    '#4CAF50',
  Memory:     '#C84848',
};

const INTENT_SIGILS: Record<IntentType, string> = {
  Question: '?', Coding: '</>', Research: '⌖', Automation: '⚙',
  Workflow: '⟐', Project: '◈', Memory: '∞',
};

async function api<T>(path: string, method = 'GET', body?: unknown): Promise<T> {
  const res = await fetch(`${ORACLE_URL}${path}`, {
    method,
    headers: body ? { 'Content-Type': 'application/json' } : {},
    body: body ? JSON.stringify(body) : undefined,
  });
  if (!res.ok) {
    const err = await res.text();
    throw new Error(`API ${res.status}: ${err.slice(0, 200)}`);
  }
  return res.json();
}

function StatusBadge({ status }: { status: ExecStatus }) {
  const colors: Record<ExecStatus, string> = {
    pending: '#C9A84C', running: '#00D4AA', paused: '#6A9FD8',
    completed: '#4CAF50', failed: '#C84848', cancelled: '#888',
  };
  return (
    <span style={{
      padding: '2px 8px', borderRadius: '10px', fontSize: '10px',
      letterSpacing: '0.15em', textTransform: 'uppercase', fontFamily: 'sans-serif',
      background: `${colors[status]}22`, color: colors[status],
      border: `1px solid ${colors[status]}44`,
    }}>
      {status}
    </span>
  );
}

function MetricCard({ label, value, sub }: { label: string; value: string | number; sub?: string }) {
  return (
    <div style={{
      padding: '14px 16px', background: 'rgba(14,17,32,0.7)',
      border: '1px solid rgba(0,212,170,0.14)', borderRadius: '10px',
      backdropFilter: 'blur(12px)',
    }}>
      <p style={{ fontFamily: 'sans-serif', fontSize: '9px', letterSpacing: '0.25em', textTransform: 'uppercase', color: 'rgba(0,212,170,0.55)', margin: '0 0 4px' }}>{label}</p>
      <p style={{ fontFamily: '"Cinzel", serif', fontSize: '22px', color: '#00D4AA', margin: '0 0 2px', letterSpacing: '0.05em' }}>{value}</p>
      {sub && <p style={{ fontFamily: 'sans-serif', fontSize: '10px', color: 'rgba(212,223,232,0.35)', margin: 0 }}>{sub}</p>}
    </div>
  );
}

export default function SolSpireConsole() {
  const [tab, setTab] = useState<'run' | 'projects' | 'executions' | 'tools' | 'github'>('run');
  const [request, setRequest] = useState('');
  const [provider, setProvider] = useState('gemini');
  const [loading, setLoading] = useState(false);
  const [runResult, setRunResult] = useState<RunResult | null>(null);
  const [runError, setRunError] = useState<string | null>(null);
  const [status, setStatus] = useState<KernelStatus | null>(null);
  const [projects, setProjects] = useState<Project[]>([]);
  const [executions, setExecutions] = useState<Execution[]>([]);
  const [newProjectName, setNewProjectName] = useState('');
  const [toolPath, setToolPath] = useState('');
  const [toolContent, setToolContent] = useState('');
  const [toolResult, setToolResult] = useState<Record<string, unknown> | null>(null);
  const [toolLoading, setToolLoading] = useState(false);
  const [toolOp, setToolOp] = useState<'read' | 'write' | 'list'>('list');
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  // GitHub state
  const [ghOwner, setGhOwner] = useState('Arkadia-Oversoul-Prism');
  const [ghRepo, setGhRepo] = useState('');
  const [ghBranch, setGhBranch] = useState('main');
  const [ghFilePath, setGhFilePath] = useState('');
  const [ghRepos, setGhRepos] = useState<GhRepo[]>([]);
  const [ghTree, setGhTree] = useState<GhEntry[]>([]);
  const [ghFileContent, setGhFileContent] = useState<string | null>(null);
  const [ghLoading, setGhLoading] = useState(false);
  const [ghError, setGhError] = useState<string | null>(null);
  const [ghMode, setGhMode] = useState<'repos' | 'tree' | 'file'>('repos');

  useEffect(() => { loadStatus(); }, []);
  useEffect(() => {
    if (tab === 'projects') loadProjects();
    if (tab === 'executions') loadExecutions();
    if (tab === 'github') loadGhRepos();
  }, [tab]);

  async function loadStatus() {
    try { setStatus(await api<KernelStatus>('/solspire/status')); } catch {}
  }

  async function loadProjects() {
    try { const r = await api<{ projects: Project[] }>('/solspire/projects'); setProjects(r.projects); } catch {}
  }

  async function loadExecutions() {
    try { const r = await api<{ executions: Execution[] }>('/solspire/executions'); setExecutions(r.executions); } catch {}
  }

  async function handleRun() {
    if (!request.trim()) return;
    setLoading(true); setRunResult(null); setRunError(null);
    try {
      const result = await api<RunResult>('/solspire/run', 'POST', { request, provider });
      setRunResult(result);
      loadStatus();
    } catch (e) {
      setRunError(e instanceof Error ? e.message : String(e));
    } finally {
      setLoading(false);
    }
  }

  async function handleCreateProject() {
    if (!newProjectName.trim()) return;
    try {
      await api('/solspire/projects', 'POST', { name: newProjectName });
      setNewProjectName('');
      loadProjects();
    } catch (e) {
      alert(e instanceof Error ? e.message : String(e));
    }
  }

  async function handleArchive(id: string) {
    try { await api(`/solspire/projects/${id}/archive`, 'POST'); loadProjects(); } catch {}
  }

  async function handleExecAction(id: string, action: 'pause' | 'resume' | 'cancel') {
    try { await api(`/solspire/executions/${id}/${action}`, 'POST'); loadExecutions(); } catch {}
  }

  async function loadGhRepos() {
    if (!ghOwner.trim()) return;
    setGhLoading(true); setGhError(null);
    try {
      const r = await api<{ ok: boolean; repos: GhRepo[]; error?: string }>('/solspire/tools/github/repos', 'POST', { owner: ghOwner });
      if (!r.ok) { setGhError(r.error || 'Failed'); return; }
      setGhRepos(r.repos); setGhMode('repos');
    } catch (e) { setGhError(e instanceof Error ? e.message : String(e)); }
    finally { setGhLoading(false); }
  }

  async function loadGhTree(repo: string) {
    setGhRepo(repo); setGhLoading(true); setGhError(null); setGhTree([]); setGhFileContent(null);
    try {
      const r = await api<{ ok: boolean; files: GhEntry[]; error?: string }>('/solspire/tools/github/tree', 'POST', { owner: ghOwner, repo, branch: ghBranch });
      if (!r.ok) { setGhError(r.error || 'Failed'); return; }
      setGhTree(r.files); setGhMode('tree');
    } catch (e) { setGhError(e instanceof Error ? e.message : String(e)); }
    finally { setGhLoading(false); }
  }

  async function loadGhFile(path: string) {
    setGhFilePath(path); setGhLoading(true); setGhError(null); setGhFileContent(null);
    try {
      const r = await api<{ ok: boolean; content: string; error?: string }>('/solspire/tools/github/read', 'POST', { owner: ghOwner, repo: ghRepo, path, branch: ghBranch });
      if (!r.ok) { setGhError(r.error || 'Failed'); return; }
      setGhFileContent(r.content); setGhMode('file');
    } catch (e) { setGhError(e instanceof Error ? e.message : String(e)); }
    finally { setGhLoading(false); }
  }

  async function handleFsTool() {
    setToolLoading(true); setToolResult(null);
    try {
      let result: Record<string, unknown>;
      if (toolOp === 'read') result = await api('/solspire/tools/fs/read', 'POST', { path: toolPath });
      else if (toolOp === 'write') result = await api('/solspire/tools/fs/write', 'POST', { path: toolPath, content: toolContent });
      else result = await api('/solspire/tools/fs/list', 'POST', { path: toolPath || '.' });
      setToolResult(result);
    } catch (e) {
      setToolResult({ ok: false, error: e instanceof Error ? e.message : String(e) });
    } finally {
      setToolLoading(false);
    }
  }

  const tabs = [
    { id: 'run' as const, label: 'Run', sigil: '⟐' },
    { id: 'projects' as const, label: 'Projects', sigil: '◈' },
    { id: 'executions' as const, label: 'Executions', sigil: '⚙' },
    { id: 'tools' as const, label: 'Files', sigil: '⌖' },
    { id: 'github' as const, label: 'GitHub', sigil: '⟁' },
  ];

  return (
    <div className="min-h-screen w-full relative" style={{ background: '#0A0B14' }}>
      <div className="aurora-bg" />
      <div style={{ maxWidth: '900px', margin: '0 auto', padding: '24px 16px', position: 'relative', zIndex: 10 }}>

        {/* Header */}
        <motion.div initial={{ opacity: 0, y: -10 }} animate={{ opacity: 1, y: 0 }} style={{ marginBottom: '24px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '6px' }}>
            <div style={{ width: '8px', height: '8px', background: '#C9A84C', borderRadius: '50%', boxShadow: '0 0 12px #C9A84C88' }} />
            <p style={{ fontFamily: 'sans-serif', fontSize: '9px', letterSpacing: '0.35em', textTransform: 'uppercase', color: 'rgba(201,168,76,0.6)', margin: 0 }}>
              SolSpire Console v1.0 · Kernel v0.1 · Milestone 1
            </p>
          </div>
          <h1 style={{ fontFamily: '"Cinzel", serif', fontSize: '32px', color: '#C9A84C', margin: '0 0 4px', letterSpacing: '0.18em', textShadow: '0 0 40px rgba(201,168,76,0.35)' }}>
            SOLSPIRE
          </h1>
          <p style={{ fontFamily: 'sans-serif', fontSize: '12px', color: 'rgba(212,223,232,0.4)', margin: 0, letterSpacing: '0.05em' }}>
            Sovereign intelligence orchestration — Intent · Plan · Execute · Observe
          </p>
        </motion.div>

        {/* Metrics */}
        {status && (
          <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 0.1 }}
            style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '8px', marginBottom: '20px' }}>
            <MetricCard label="Provider" value={status.providers.active} sub="active" />
            <MetricCard label="Projects" value={status.projects.active_count} sub="active" />
            <MetricCard label="Executions" value={status.executions.total} sub={`${status.executions.active} running`} />
            <MetricCard label="Tokens" value={Object.values(status.providers.token_usage).reduce((a,b)=>a+b,0)} sub="used" />
          </motion.div>
        )}

        {/* Tabs */}
        <div style={{ display: 'flex', gap: '4px', marginBottom: '16px', borderBottom: '1px solid rgba(0,212,170,0.12)', paddingBottom: '12px' }}>
          {tabs.map(t => (
            <button key={t.id} onClick={() => setTab(t.id)} style={{
              padding: '7px 16px', borderRadius: '8px', border: 'none', cursor: 'pointer', fontFamily: 'sans-serif',
              fontSize: '10px', letterSpacing: '0.18em', textTransform: 'uppercase', transition: 'all 0.2s',
              background: tab === t.id ? 'rgba(0,212,170,0.12)' : 'transparent',
              color: tab === t.id ? '#00D4AA' : 'rgba(212,223,232,0.4)',
              borderBottom: tab === t.id ? '1px solid #00D4AA' : '1px solid transparent',
            }}>
              {t.sigil} {t.label}
            </button>
          ))}
        </div>

        <AnimatePresence mode="wait">

          {/* ── RUN TAB ── */}
          {tab === 'run' && (
            <motion.div key="run" initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -8 }}>

              {/* Provider select */}
              <div style={{ display: 'flex', gap: '8px', marginBottom: '14px', flexWrap: 'wrap' }}>
                {['gemini', 'openai', 'anthropic', 'openrouter', 'ollama'].map(p => (
                  <button key={p} onClick={() => setProvider(p)} style={{
                    padding: '5px 12px', borderRadius: '20px', border: `1px solid ${provider === p ? '#00D4AA' : 'rgba(0,212,170,0.2)'}`,
                    background: provider === p ? 'rgba(0,212,170,0.10)' : 'transparent',
                    color: provider === p ? '#00D4AA' : 'rgba(212,223,232,0.4)', cursor: 'pointer',
                    fontFamily: 'sans-serif', fontSize: '10px', letterSpacing: '0.12em', transition: 'all 0.18s',
                  }}>{p}</button>
                ))}
                {provider !== 'gemini' && (
                  <span style={{ fontSize: '10px', color: 'rgba(201,168,76,0.55)', alignSelf: 'center', fontFamily: 'sans-serif' }}>
                    ⚠ Milestone 2 provider — stub response
                  </span>
                )}
              </div>

              {/* Request input */}
              <div style={{ position: 'relative', marginBottom: '12px' }}>
                <textarea
                  ref={textareaRef}
                  value={request}
                  onChange={e => setRequest(e.target.value)}
                  onKeyDown={e => { if (e.key === 'Enter' && (e.metaKey || e.ctrlKey)) handleRun(); }}
                  placeholder={`Type a request...\n\nExamples:\n• Create a new project called "Codex Editorial"\n• Research the history of sacred geometry\n• Write a Python function to sort a list\n• What is the SolSpire kernel?`}
                  rows={5}
                  style={{
                    width: '100%', boxSizing: 'border-box', background: 'rgba(14,17,32,0.85)',
                    border: '1px solid rgba(0,212,170,0.2)', borderRadius: '10px', color: 'rgba(212,223,232,0.85)',
                    fontFamily: 'sans-serif', fontSize: '13px', padding: '14px', resize: 'vertical',
                    outline: 'none', lineHeight: '1.6', letterSpacing: '0.02em',
                  }}
                />
              </div>

              <div style={{ display: 'flex', gap: '10px', marginBottom: '20px' }}>
                <button onClick={handleRun} disabled={loading || !request.trim()} style={{
                  flex: 1, padding: '13px', background: loading ? 'rgba(0,212,170,0.05)' : 'linear-gradient(135deg, rgba(0,212,170,0.15), rgba(0,212,170,0.07))',
                  border: '1px solid rgba(0,212,170,0.35)', borderRadius: '10px', color: loading ? 'rgba(0,212,170,0.4)' : '#00D4AA',
                  cursor: loading ? 'not-allowed' : 'pointer', fontFamily: 'sans-serif', fontSize: '11px',
                  letterSpacing: '0.22em', textTransform: 'uppercase', transition: 'all 0.2s',
                }}>
                  {loading ? '⟐ Processing...' : '⟐ Execute  (⌘↵)'}
                </button>
                {runResult && (
                  <button onClick={() => { setRunResult(null); setRunError(null); setRequest(''); }} style={{
                    padding: '13px 18px', background: 'transparent', border: '1px solid rgba(255,255,255,0.1)',
                    borderRadius: '10px', color: 'rgba(212,223,232,0.4)', cursor: 'pointer', fontFamily: 'sans-serif', fontSize: '11px',
                  }}>Clear</button>
                )}
              </div>

              {/* Error */}
              {runError && (
                <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} style={{
                  padding: '14px', background: 'rgba(200,72,72,0.08)', border: '1px solid rgba(200,72,72,0.25)',
                  borderRadius: '10px', marginBottom: '16px',
                }}>
                  <p style={{ fontFamily: 'sans-serif', fontSize: '12px', color: '#C84848', margin: 0 }}>⚠ {runError}</p>
                </motion.div>
              )}

              {/* Result */}
              {runResult && (
                <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>

                  {/* Intent + Plan header */}
                  <div style={{ padding: '14px 16px', background: 'rgba(14,17,32,0.8)', border: '1px solid rgba(0,212,170,0.15)', borderRadius: '10px', display: 'flex', gap: '16px', flexWrap: 'wrap', alignItems: 'center' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                      <span style={{ fontSize: '18px', color: INTENT_COLORS[runResult.intent] }}>{INTENT_SIGILS[runResult.intent]}</span>
                      <div>
                        <p style={{ fontFamily: 'sans-serif', fontSize: '9px', letterSpacing: '0.25em', textTransform: 'uppercase', color: 'rgba(212,223,232,0.4)', margin: '0 0 2px' }}>Intent Classified</p>
                        <p style={{ fontFamily: '"Cinzel", serif', fontSize: '14px', color: INTENT_COLORS[runResult.intent], margin: 0 }}>{runResult.intent}</p>
                      </div>
                    </div>
                    <div>
                      <p style={{ fontFamily: 'sans-serif', fontSize: '9px', letterSpacing: '0.25em', textTransform: 'uppercase', color: 'rgba(212,223,232,0.4)', margin: '0 0 2px' }}>Plan Steps</p>
                      <p style={{ fontFamily: 'sans-serif', fontSize: '13px', color: 'rgba(212,223,232,0.7)', margin: 0 }}>{runResult.plan.steps.length}</p>
                    </div>
                    <div>
                      <p style={{ fontFamily: 'sans-serif', fontSize: '9px', letterSpacing: '0.25em', textTransform: 'uppercase', color: 'rgba(212,223,232,0.4)', margin: '0 0 2px' }}>Elapsed</p>
                      <p style={{ fontFamily: 'sans-serif', fontSize: '13px', color: 'rgba(212,223,232,0.7)', margin: 0 }}>{runResult.elapsed_ms}ms</p>
                    </div>
                    <StatusBadge status={runResult.execution.status} />
                  </div>

                  {/* Plan steps */}
                  <div style={{ padding: '14px 16px', background: 'rgba(14,17,32,0.7)', border: '1px solid rgba(201,168,76,0.12)', borderRadius: '10px' }}>
                    <p style={{ fontFamily: 'sans-serif', fontSize: '9px', letterSpacing: '0.25em', textTransform: 'uppercase', color: 'rgba(201,168,76,0.55)', margin: '0 0 10px' }}>Execution Plan</p>
                    {runResult.plan.steps.map((step, i) => (
                      <div key={i} style={{ display: 'flex', gap: '10px', alignItems: 'flex-start', marginBottom: i < runResult.plan.steps.length - 1 ? '8px' : 0 }}>
                        <span style={{ fontFamily: '"Cinzel", serif', fontSize: '10px', color: 'rgba(201,168,76,0.5)', minWidth: '20px', paddingTop: '1px' }}>{i + 1}.</span>
                        <div style={{ flex: 1 }}>
                          <span style={{ fontFamily: 'monospace', fontSize: '11px', color: '#6A9FD8', padding: '1px 6px', background: 'rgba(106,159,216,0.1)', borderRadius: '4px', marginRight: '8px' }}>{step.tool}</span>
                          <span style={{ fontFamily: 'sans-serif', fontSize: '12px', color: 'rgba(212,223,232,0.6)' }}>{step.description}</span>
                        </div>
                      </div>
                    ))}
                  </div>

                  {/* Results */}
                  {runResult.execution.results.length > 0 && (
                    <div style={{ padding: '14px 16px', background: 'rgba(14,17,32,0.7)', border: '1px solid rgba(0,212,170,0.12)', borderRadius: '10px' }}>
                      <p style={{ fontFamily: 'sans-serif', fontSize: '9px', letterSpacing: '0.25em', textTransform: 'uppercase', color: 'rgba(0,212,170,0.55)', margin: '0 0 10px' }}>Step Results</p>
                      {runResult.execution.results.map((res, i) => {
                        const text = typeof res.result === 'string' ? res.result : JSON.stringify(res, null, 2);
                        return (
                          <div key={i} style={{ marginBottom: i < runResult.execution.results.length - 1 ? '12px' : 0 }}>
                            <p style={{ fontFamily: 'sans-serif', fontSize: '9px', color: 'rgba(212,223,232,0.4)', margin: '0 0 4px' }}>
                              Step {(res.step as number) + 1} · {String(res.tool)}
                            </p>
                            <pre style={{ fontFamily: 'monospace', fontSize: '12px', color: 'rgba(212,223,232,0.75)', background: 'rgba(0,0,0,0.3)', padding: '10px', borderRadius: '6px', margin: 0, whiteSpace: 'pre-wrap', wordBreak: 'break-word', maxHeight: '300px', overflowY: 'auto' }}>
                              {text.slice(0, 3000)}{text.length > 3000 ? '\n[...truncated]' : ''}
                            </pre>
                          </div>
                        );
                      })}
                    </div>
                  )}

                  {runResult.execution.error && (
                    <div style={{ padding: '12px 14px', background: 'rgba(200,72,72,0.08)', border: '1px solid rgba(200,72,72,0.2)', borderRadius: '8px' }}>
                      <p style={{ fontFamily: 'sans-serif', fontSize: '12px', color: '#C84848', margin: 0 }}>
                        Execution error: {runResult.execution.error}
                      </p>
                    </div>
                  )}
                </motion.div>
              )}
            </motion.div>
          )}

          {/* ── PROJECTS TAB ── */}
          {tab === 'projects' && (
            <motion.div key="projects" initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0 }}>
              <div style={{ display: 'flex', gap: '8px', marginBottom: '16px' }}>
                <input
                  value={newProjectName}
                  onChange={e => setNewProjectName(e.target.value)}
                  onKeyDown={e => { if (e.key === 'Enter') handleCreateProject(); }}
                  placeholder="New project name..."
                  style={{
                    flex: 1, padding: '10px 14px', background: 'rgba(14,17,32,0.8)', border: '1px solid rgba(0,212,170,0.2)',
                    borderRadius: '8px', color: 'rgba(212,223,232,0.85)', fontFamily: 'sans-serif', fontSize: '13px', outline: 'none',
                  }}
                />
                <button onClick={handleCreateProject} disabled={!newProjectName.trim()} style={{
                  padding: '10px 18px', background: 'rgba(0,212,170,0.1)', border: '1px solid rgba(0,212,170,0.3)',
                  borderRadius: '8px', color: '#00D4AA', cursor: 'pointer', fontFamily: 'sans-serif', fontSize: '11px', letterSpacing: '0.15em',
                }}>
                  + Create
                </button>
                <button onClick={loadProjects} style={{
                  padding: '10px 14px', background: 'transparent', border: '1px solid rgba(255,255,255,0.1)',
                  borderRadius: '8px', color: 'rgba(212,223,232,0.4)', cursor: 'pointer', fontSize: '13px',
                }}>↺</button>
              </div>

              {projects.length === 0 ? (
                <div style={{ textAlign: 'center', padding: '40px', color: 'rgba(212,223,232,0.3)', fontFamily: 'sans-serif', fontSize: '13px' }}>
                  No projects yet. Create one above.
                </div>
              ) : (
                <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                  {projects.map(p => (
                    <motion.div key={p.id} initial={{ opacity: 0 }} animate={{ opacity: 1 }}
                      style={{ padding: '14px 16px', background: 'rgba(14,17,32,0.75)', border: '1px solid rgba(0,212,170,0.12)', borderRadius: '10px', display: 'flex', alignItems: 'center', gap: '14px' }}>
                      <span style={{ fontSize: '16px' }}>◈</span>
                      <div style={{ flex: 1 }}>
                        <p style={{ fontFamily: '"Cinzel", serif', fontSize: '14px', color: '#C9A84C', margin: '0 0 3px' }}>{p.name}</p>
                        <p style={{ fontFamily: 'sans-serif', fontSize: '10px', color: 'rgba(212,223,232,0.35)', margin: 0 }}>
                          {p.id.slice(0, 8)}... · {new Date(p.created_at * 1000).toLocaleDateString()} · {p.conversations.length} msgs
                        </p>
                      </div>
                      <span style={{ padding: '2px 8px', borderRadius: '10px', fontSize: '9px', letterSpacing: '0.15em', background: p.status === 'active' ? 'rgba(76,175,80,0.15)' : 'rgba(136,136,136,0.12)', color: p.status === 'active' ? '#4CAF50' : '#888', border: `1px solid ${p.status === 'active' ? 'rgba(76,175,80,0.3)' : 'rgba(136,136,136,0.2)'}`, textTransform: 'uppercase', fontFamily: 'sans-serif' }}>
                        {p.status}
                      </span>
                      {p.status === 'active' && (
                        <button onClick={() => handleArchive(p.id)} style={{ padding: '5px 10px', background: 'transparent', border: '1px solid rgba(200,72,72,0.25)', borderRadius: '6px', color: 'rgba(200,72,72,0.6)', cursor: 'pointer', fontFamily: 'sans-serif', fontSize: '10px' }}>
                          Archive
                        </button>
                      )}
                    </motion.div>
                  ))}
                </div>
              )}
            </motion.div>
          )}

          {/* ── EXECUTIONS TAB ── */}
          {tab === 'executions' && (
            <motion.div key="executions" initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0 }}>
              <div style={{ display: 'flex', justifyContent: 'flex-end', marginBottom: '12px' }}>
                <button onClick={loadExecutions} style={{ padding: '7px 14px', background: 'transparent', border: '1px solid rgba(255,255,255,0.1)', borderRadius: '8px', color: 'rgba(212,223,232,0.4)', cursor: 'pointer', fontSize: '13px', fontFamily: 'sans-serif' }}>
                  ↺ Refresh
                </button>
              </div>
              {executions.length === 0 ? (
                <div style={{ textAlign: 'center', padding: '40px', color: 'rgba(212,223,232,0.3)', fontFamily: 'sans-serif', fontSize: '13px' }}>
                  No executions yet. Run a request first.
                </div>
              ) : (
                <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                  {[...executions].reverse().map(ex => (
                    <motion.div key={ex.id} initial={{ opacity: 0 }} animate={{ opacity: 1 }}
                      style={{ padding: '14px 16px', background: 'rgba(14,17,32,0.75)', border: '1px solid rgba(0,212,170,0.10)', borderRadius: '10px' }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '8px' }}>
                        <StatusBadge status={ex.status} />
                        <p style={{ fontFamily: 'monospace', fontSize: '11px', color: 'rgba(212,223,232,0.4)', margin: 0, flex: 1 }}>{ex.id.slice(0, 16)}...</p>
                        <p style={{ fontFamily: 'sans-serif', fontSize: '10px', color: 'rgba(212,223,232,0.35)', margin: 0 }}>
                          {ex.completed_at ? `${Math.round((ex.completed_at - ex.started_at) * 1000)}ms` : 'running'}
                          {ex.retries > 0 ? ` · ${ex.retries} retries` : ''}
                        </p>
                      </div>
                      <p style={{ fontFamily: 'sans-serif', fontSize: '11px', color: 'rgba(212,223,232,0.4)', margin: '0 0 8px' }}>
                        {ex.results.length} step(s) completed
                      </p>
                      {(ex.status === 'running' || ex.status === 'paused') && (
                        <div style={{ display: 'flex', gap: '6px' }}>
                          {ex.status === 'running' && (
                            <button onClick={() => handleExecAction(ex.id, 'pause')} style={{ padding: '4px 10px', background: 'transparent', border: '1px solid rgba(106,159,216,0.3)', borderRadius: '5px', color: '#6A9FD8', cursor: 'pointer', fontSize: '10px', fontFamily: 'sans-serif' }}>Pause</button>
                          )}
                          {ex.status === 'paused' && (
                            <button onClick={() => handleExecAction(ex.id, 'resume')} style={{ padding: '4px 10px', background: 'transparent', border: '1px solid rgba(0,212,170,0.3)', borderRadius: '5px', color: '#00D4AA', cursor: 'pointer', fontSize: '10px', fontFamily: 'sans-serif' }}>Resume</button>
                          )}
                          <button onClick={() => handleExecAction(ex.id, 'cancel')} style={{ padding: '4px 10px', background: 'transparent', border: '1px solid rgba(200,72,72,0.25)', borderRadius: '5px', color: '#C84848', cursor: 'pointer', fontSize: '10px', fontFamily: 'sans-serif' }}>Cancel</button>
                        </div>
                      )}
                    </motion.div>
                  ))}
                </div>
              )}
            </motion.div>
          )}

          {/* ── TOOLS TAB ── */}
          {tab === 'tools' && (
            <motion.div key="tools" initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0 }}>
              <div style={{ display: 'flex', gap: '6px', marginBottom: '14px' }}>
                {(['list', 'read', 'write'] as const).map(op => (
                  <button key={op} onClick={() => setToolOp(op)} style={{
                    padding: '6px 14px', borderRadius: '6px', border: `1px solid ${toolOp === op ? '#00D4AA' : 'rgba(0,212,170,0.15)'}`,
                    background: toolOp === op ? 'rgba(0,212,170,0.1)' : 'transparent', color: toolOp === op ? '#00D4AA' : 'rgba(212,223,232,0.4)',
                    cursor: 'pointer', fontFamily: 'sans-serif', fontSize: '10px', letterSpacing: '0.15em', textTransform: 'uppercase',
                  }}>{op}</button>
                ))}
              </div>
              <div style={{ display: 'flex', gap: '8px', marginBottom: '10px' }}>
                <input value={toolPath} onChange={e => setToolPath(e.target.value)} placeholder={toolOp === 'list' ? 'Directory path (e.g. .)' : 'File path (e.g. data/test.txt)'}
                  style={{ flex: 1, padding: '10px 14px', background: 'rgba(14,17,32,0.8)', border: '1px solid rgba(0,212,170,0.2)', borderRadius: '8px', color: 'rgba(212,223,232,0.85)', fontFamily: 'monospace', fontSize: '12px', outline: 'none' }} />
                <button onClick={handleFsTool} disabled={toolLoading} style={{ padding: '10px 18px', background: 'rgba(0,212,170,0.1)', border: '1px solid rgba(0,212,170,0.3)', borderRadius: '8px', color: '#00D4AA', cursor: 'pointer', fontFamily: 'sans-serif', fontSize: '11px', letterSpacing: '0.15em' }}>
                  {toolLoading ? '...' : 'Run'}
                </button>
              </div>
              {toolOp === 'write' && (
                <textarea value={toolContent} onChange={e => setToolContent(e.target.value)} placeholder="File content to write..."
                  rows={5} style={{ width: '100%', boxSizing: 'border-box', padding: '10px 14px', background: 'rgba(14,17,32,0.8)', border: '1px solid rgba(0,212,170,0.15)', borderRadius: '8px', color: 'rgba(212,223,232,0.85)', fontFamily: 'monospace', fontSize: '12px', resize: 'vertical', outline: 'none', marginBottom: '10px' }} />
              )}
              {toolResult && (
                <div style={{ padding: '14px', background: 'rgba(14,17,32,0.8)', border: `1px solid ${toolResult.ok ? 'rgba(0,212,170,0.15)' : 'rgba(200,72,72,0.2)'}`, borderRadius: '10px' }}>
                  {toolResult.entries ? (
                    <div>
                      <p style={{ fontFamily: 'sans-serif', fontSize: '9px', letterSpacing: '0.25em', textTransform: 'uppercase', color: 'rgba(0,212,170,0.55)', margin: '0 0 10px' }}>
                        {toolResult.path as string} — {(toolResult.count as number)} entries
                      </p>
                      {(toolResult.entries as Array<{ name: string; type: string; size: number | null }>).map((entry, i) => (
                        <div key={i} style={{ display: 'flex', gap: '10px', padding: '4px 0', borderBottom: '1px solid rgba(255,255,255,0.04)' }}>
                          <span style={{ color: entry.type === 'dir' ? '#C9A84C' : 'rgba(212,223,232,0.5)', fontSize: '12px' }}>{entry.type === 'dir' ? '📁' : '📄'}</span>
                          <span style={{ fontFamily: 'monospace', fontSize: '12px', color: entry.type === 'dir' ? '#C9A84C' : 'rgba(212,223,232,0.75)', flex: 1 }}>{entry.name}</span>
                          {entry.size != null && <span style={{ fontFamily: 'monospace', fontSize: '10px', color: 'rgba(212,223,232,0.3)' }}>{entry.size}b</span>}
                        </div>
                      ))}
                    </div>
                  ) : (
                    <pre style={{ fontFamily: 'monospace', fontSize: '12px', color: 'rgba(212,223,232,0.75)', margin: 0, whiteSpace: 'pre-wrap', wordBreak: 'break-word', maxHeight: '400px', overflowY: 'auto' }}>
                      {JSON.stringify(toolResult, null, 2).slice(0, 4000)}
                    </pre>
                  )}
                </div>
              )}
            </motion.div>
          )}

          {/* ── GITHUB TAB ── */}
          {tab === 'github' && (
            <motion.div key="github" initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0 }}>

              {/* Owner + branch bar */}
              <div style={{ display: 'flex', gap: '8px', marginBottom: '14px', flexWrap: 'wrap' }}>
                <input value={ghOwner} onChange={e => setGhOwner(e.target.value)}
                  placeholder="GitHub owner / org"
                  style={{ flex: '2 1 160px', padding: '9px 12px', background: 'rgba(14,17,32,0.85)', border: '1px solid rgba(106,159,216,0.25)', borderRadius: '8px', color: 'rgba(212,223,232,0.85)', fontFamily: 'monospace', fontSize: '12px', outline: 'none' }} />
                <input value={ghBranch} onChange={e => setGhBranch(e.target.value)}
                  placeholder="branch"
                  style={{ flex: '1 1 80px', padding: '9px 12px', background: 'rgba(14,17,32,0.85)', border: '1px solid rgba(106,159,216,0.18)', borderRadius: '8px', color: 'rgba(212,223,232,0.85)', fontFamily: 'monospace', fontSize: '12px', outline: 'none' }} />
                <button onClick={loadGhRepos} disabled={ghLoading || !ghOwner.trim()}
                  style={{ padding: '9px 18px', background: 'rgba(106,159,216,0.12)', border: '1px solid rgba(106,159,216,0.35)', borderRadius: '8px', color: '#6A9FD8', cursor: 'pointer', fontFamily: 'sans-serif', fontSize: '11px', letterSpacing: '0.15em', whiteSpace: 'nowrap' }}>
                  {ghLoading ? '...' : '⟁ Browse'}
                </button>
              </div>

              {/* Breadcrumb */}
              {ghMode !== 'repos' && (
                <div style={{ display: 'flex', gap: '6px', alignItems: 'center', marginBottom: '12px', flexWrap: 'wrap' }}>
                  <button onClick={() => { setGhMode('repos'); setGhRepo(''); setGhTree([]); setGhFileContent(null); }}
                    style={{ background: 'none', border: 'none', color: '#6A9FD8', cursor: 'pointer', fontFamily: 'monospace', fontSize: '12px', padding: 0 }}>
                    {ghOwner}
                  </button>
                  {ghRepo && <>
                    <span style={{ color: 'rgba(212,223,232,0.25)' }}>/</span>
                    <button onClick={() => { setGhMode('tree'); setGhFileContent(null); setGhFilePath(''); }}
                      style={{ background: 'none', border: 'none', color: '#6A9FD8', cursor: 'pointer', fontFamily: 'monospace', fontSize: '12px', padding: 0 }}>
                      {ghRepo}
                    </button>
                  </>}
                  {ghFilePath && <>
                    <span style={{ color: 'rgba(212,223,232,0.25)' }}>/</span>
                    <span style={{ fontFamily: 'monospace', fontSize: '12px', color: 'rgba(212,223,232,0.55)' }}>{ghFilePath.split('/').pop()}</span>
                  </>}
                  <span style={{ marginLeft: '4px', padding: '1px 7px', borderRadius: '8px', fontSize: '9px', background: 'rgba(106,159,216,0.1)', color: '#6A9FD8', fontFamily: 'sans-serif', letterSpacing: '0.12em' }}>
                    {ghBranch}
                  </span>
                </div>
              )}

              {/* Error */}
              {ghError && (
                <div style={{ padding: '12px 14px', background: 'rgba(200,72,72,0.08)', border: '1px solid rgba(200,72,72,0.22)', borderRadius: '8px', marginBottom: '12px' }}>
                  <p style={{ fontFamily: 'sans-serif', fontSize: '12px', color: '#C84848', margin: 0 }}>⚠ {ghError}</p>
                </div>
              )}

              {/* Repos list */}
              {ghMode === 'repos' && !ghLoading && ghRepos.length > 0 && (
                <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
                  <p style={{ fontFamily: 'sans-serif', fontSize: '9px', letterSpacing: '0.25em', textTransform: 'uppercase', color: 'rgba(106,159,216,0.55)', margin: '0 0 8px' }}>
                    {ghRepos.length} repositories · {ghOwner}
                  </p>
                  {ghRepos.map(r => (
                    <motion.div key={r.name} initial={{ opacity: 0 }} animate={{ opacity: 1 }}
                      onClick={() => loadGhTree(r.name)}
                      style={{ padding: '12px 16px', background: 'rgba(14,17,32,0.75)', border: '1px solid rgba(106,159,216,0.12)', borderRadius: '9px', cursor: 'pointer', display: 'flex', gap: '12px', alignItems: 'center', transition: 'border-color 0.18s' }}
                      onMouseEnter={e => (e.currentTarget.style.borderColor = 'rgba(106,159,216,0.35)')}
                      onMouseLeave={e => (e.currentTarget.style.borderColor = 'rgba(106,159,216,0.12)')}>
                      <span style={{ fontSize: '15px' }}>⟁</span>
                      <div style={{ flex: 1, minWidth: 0 }}>
                        <p style={{ fontFamily: 'monospace', fontSize: '13px', color: '#6A9FD8', margin: '0 0 3px', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{r.name}</p>
                        {r.description && <p style={{ fontFamily: 'sans-serif', fontSize: '11px', color: 'rgba(212,223,232,0.4)', margin: 0, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{r.description}</p>}
                      </div>
                      <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'flex-end', gap: '3px', flexShrink: 0 }}>
                        {r.language && <span style={{ fontSize: '9px', color: 'rgba(212,223,232,0.35)', fontFamily: 'sans-serif' }}>{r.language}</span>}
                        <span style={{ fontSize: '9px', color: 'rgba(201,168,76,0.55)', fontFamily: 'sans-serif' }}>★ {r.stars}</span>
                      </div>
                      <span style={{ color: 'rgba(106,159,216,0.4)', fontSize: '12px' }}>→</span>
                    </motion.div>
                  ))}
                </div>
              )}

              {/* File tree */}
              {ghMode === 'tree' && !ghLoading && ghTree.length > 0 && (
                <div>
                  <p style={{ fontFamily: 'sans-serif', fontSize: '9px', letterSpacing: '0.25em', textTransform: 'uppercase', color: 'rgba(106,159,216,0.55)', margin: '0 0 10px' }}>
                    {ghTree.length} entries · click a file to view
                  </p>
                  <div style={{ maxHeight: '480px', overflowY: 'auto', display: 'flex', flexDirection: 'column', gap: '2px' }}>
                    {ghTree.map(entry => (
                      <div key={entry.path}
                        onClick={() => entry.type === 'blob' ? loadGhFile(entry.path) : undefined}
                        style={{ display: 'flex', gap: '10px', alignItems: 'center', padding: '5px 10px', borderRadius: '6px', cursor: entry.type === 'blob' ? 'pointer' : 'default', transition: 'background 0.15s' }}
                        onMouseEnter={e => { if (entry.type === 'blob') e.currentTarget.style.background = 'rgba(106,159,216,0.07)'; }}
                        onMouseLeave={e => { e.currentTarget.style.background = 'transparent'; }}>
                        <span style={{ fontSize: '11px', color: entry.type === 'tree' ? '#C9A84C' : 'rgba(212,223,232,0.4)', flexShrink: 0, width: '14px' }}>
                          {entry.type === 'tree' ? '▸' : '·'}
                        </span>
                        <span style={{ fontFamily: 'monospace', fontSize: '12px', color: entry.type === 'tree' ? 'rgba(201,168,76,0.75)' : 'rgba(212,223,232,0.65)', flex: 1, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                          {entry.path}
                        </span>
                        {entry.size != null && (
                          <span style={{ fontFamily: 'monospace', fontSize: '10px', color: 'rgba(212,223,232,0.25)', flexShrink: 0 }}>
                            {entry.size > 1024 ? `${(entry.size / 1024).toFixed(1)}k` : `${entry.size}b`}
                          </span>
                        )}
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* File viewer */}
              {ghMode === 'file' && !ghLoading && ghFileContent !== null && (
                <div>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '10px' }}>
                    <p style={{ fontFamily: 'sans-serif', fontSize: '9px', letterSpacing: '0.25em', textTransform: 'uppercase', color: 'rgba(106,159,216,0.55)', margin: 0 }}>
                      {ghFilePath} · {ghFileContent.length.toLocaleString()} chars
                    </p>
                    <button onClick={() => navigator.clipboard.writeText(ghFileContent)}
                      style={{ padding: '4px 10px', background: 'transparent', border: '1px solid rgba(106,159,216,0.2)', borderRadius: '5px', color: 'rgba(106,159,216,0.6)', cursor: 'pointer', fontFamily: 'sans-serif', fontSize: '10px' }}>
                      Copy
                    </button>
                  </div>
                  <pre style={{ fontFamily: 'monospace', fontSize: '12px', color: 'rgba(212,223,232,0.78)', background: 'rgba(0,0,0,0.35)', padding: '14px', borderRadius: '8px', margin: 0, whiteSpace: 'pre-wrap', wordBreak: 'break-word', maxHeight: '520px', overflowY: 'auto', lineHeight: '1.6', border: '1px solid rgba(106,159,216,0.1)' }}>
                    {ghFileContent}
                  </pre>
                </div>
              )}

              {/* Loading spinner */}
              {ghLoading && (
                <div style={{ textAlign: 'center', padding: '40px', color: 'rgba(106,159,216,0.5)', fontFamily: 'sans-serif', fontSize: '12px' }}>
                  <motion.span animate={{ opacity: [0.4, 1, 0.4] }} transition={{ duration: 1.2, repeat: Infinity }}>
                    ⟁ Connecting to GitHub...
                  </motion.span>
                </div>
              )}

              {/* Empty state */}
              {!ghLoading && ghMode === 'repos' && ghRepos.length === 0 && !ghError && (
                <div style={{ textAlign: 'center', padding: '40px', color: 'rgba(212,223,232,0.25)', fontFamily: 'sans-serif', fontSize: '13px' }}>
                  Enter an owner / org name and click Browse.
                </div>
              )}

            </motion.div>
          )}

        </AnimatePresence>

        {/* Footer */}
        <div style={{ marginTop: '32px', paddingTop: '16px', borderTop: '1px solid rgba(0,212,170,0.08)', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <p style={{ fontFamily: 'sans-serif', fontSize: '9px', letterSpacing: '0.2em', textTransform: 'uppercase', color: 'rgba(212,223,232,0.2)', margin: 0 }}>
            SolSpire Kernel v0.1 · Provider: {status?.providers.active || '—'} · {status?.executions.total || 0} total runs
          </p>
          <p style={{ fontFamily: 'sans-serif', fontSize: '9px', color: 'rgba(212,223,232,0.2)', margin: 0 }}>Milestone 1 · Phase 1</p>
        </div>
      </div>
    </div>
  );
}
