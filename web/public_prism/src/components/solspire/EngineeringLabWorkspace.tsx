import { useState } from 'react';
import { ApiError, apiRequest } from '../../lib/apiClient';

type Props = { onChanged: () => void };
type Agent = { agent_id: string; role: string; capabilities: string[] };
type Session = { session_id: string; state: string; objective: string; agent_id: string };
type RunResult = {
  run_id?: string;
  state?: string;
  result_state?: string;
  summary?: string;
  loop_state?: string;
  turns?: Array<{ turn_index: number; text: string; tool_name?: string | null; decision: string; observation?: Record<string, unknown> | null }>;
  evidence_refs?: string[];
};

const panel: React.CSSProperties = {
  border: '1px solid rgba(201,168,76,.22)', borderRadius: 14, padding: 16,
  background: 'linear-gradient(145deg, rgba(18,22,27,.96), rgba(12,15,19,.98))',
  color: '#e8e8e8', marginBottom: 14,
};
const field: React.CSSProperties = {
  width: '100%', boxSizing: 'border-box', background: '#0b0e12', color: '#f3f4f6',
  border: '1px solid #303741', borderRadius: 9, padding: '11px 12px', font: 'inherit',
};
const action: React.CSSProperties = {
  border: '1px solid rgba(0,212,170,.4)', background: 'rgba(0,212,170,.08)',
  color: '#00d4aa', borderRadius: 9, padding: '10px 13px', fontWeight: 600, cursor: 'pointer',
};

function explain(error: unknown): string {
  if (error instanceof ApiError) return `${error.kind}: ${error.message}`;
  return error instanceof Error ? error.message : String(error);
}

export default function EngineeringLabWorkspace({ onChanged }: Props) {
  const [objective, setObjective] = useState('Inspect the current workspace and summarize its state.');
  const [workspace, setWorkspace] = useState('arkadia-workspace');
  const [provider, setProvider] = useState('ollama');
  const [session, setSession] = useState<Session | null>(null);
  const [agent, setAgent] = useState<Agent | null>(null);
  const [authorization, setAuthorization] = useState(false);
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState('');
  const [run, setRun] = useState<RunResult | null>(null);
  const [detail, setDetail] = useState<Record<string, unknown> | null>(null);

  async function createSession() {
    setBusy(true); setMessage('Creating a read-only agent session…'); setRun(null); setDetail(null);
    try {
      const createdAgent = await apiRequest<Agent>('/api/lab/engineering/agents', {
        method: 'POST',
        body: JSON.stringify({ role: 'WEAVER', display_name: 'Engineering Lab Weaver', capabilities: ['READ', 'OBSERVE'], write_allowed: false, model_ref: provider }),
      });
      const createdSession = await apiRequest<Session>('/api/lab/engineering/sessions', {
        method: 'POST',
        body: JSON.stringify({ workspace_ref: workspace.trim(), agent_id: createdAgent.agent_id, objective: objective.trim() }),
      });
      setAgent(createdAgent); setSession(createdSession); setAuthorization(false);
      setMessage('Session created. Review the scope, then explicitly authorize the read-only run.');
      onChanged();
    } catch (error) { setMessage(explain(error)); }
    finally { setBusy(false); }
  }

  async function authorize() {
    if (!session) return;
    setBusy(true); setMessage('Recording your explicit read-only authorization…');
    try {
      await apiRequest('/api/lab/engineering/sessions/' + encodeURIComponent(session.session_id) + '/authorize', {
        method: 'POST',
        body: JSON.stringify({ operations_allowed: ['read', 'list', 'git_status'], duration_minutes: 30 }),
      });
      setAuthorization(true);
      setSession({ ...session, state: 'AUTHORIZED' });
      setMessage('Authorized for read, list, and Git status only. No repository mutation is available.');
      onChanged();
    } catch (error) { setMessage(explain(error)); }
    finally { setBusy(false); }
  }

  async function runAgent() {
    if (!session || !authorization) return;
    setBusy(true); setMessage('Running the bounded model → tool → observation loop…'); setRun(null); setDetail(null);
    try {
      const result = await apiRequest<RunResult>('/api/lab/engineering/sessions/' + encodeURIComponent(session.session_id) + '/run-agent', {
        method: 'POST',
        body: JSON.stringify({ objective: objective.trim(), provider, max_turns: 6 }),
      });
      setRun(result);
      const projection = await apiRequest<Record<string, unknown>>('/api/lab/engineering/sessions/' + encodeURIComponent(session.session_id));
      setDetail(projection);
      setMessage(result.loop_state === 'DONE' ? 'Run reached the review boundary. Inspect the recorded turns and evidence below.' : 'Run stopped without claiming completion. Inspect the observed state below.');
      onChanged();
    } catch (error) { setMessage(explain(error)); }
    finally { setBusy(false); }
  }

  return (
    <section data-testid="engineering-lab-workspace" style={panel}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'start', gap: 12, flexWrap: 'wrap' }}>
        <div>
          <div style={{ color: '#c9a84c', fontSize: 10, letterSpacing: '.18em', textTransform: 'uppercase' }}>Engineering Lab · EL-01</div>
          <h2 style={{ margin: '6px 0', fontSize: 23, fontWeight: 550 }}>Work with an agent</h2>
          <p style={{ margin: 0, color: '#9ca3af', fontSize: 13, lineHeight: 1.6 }}>One workspace. Visible steps. You authorize each run.</p>
        </div>
        <span style={{ border: '1px solid #2b6157', color: '#00d4aa', borderRadius: 999, padding: '5px 9px', fontSize: 10 }}>READ-ONLY GATE</span>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit,minmax(190px,1fr))', gap: 12, marginTop: 16 }}>
        <label style={{ display: 'grid', gap: 6, fontSize: 12, color: '#b6bec8' }}>Workspace name
          <input value={workspace} onChange={e => setWorkspace(e.target.value)} style={field} maxLength={100} disabled={busy || !!session} />
        </label>
        <label style={{ display: 'grid', gap: 6, fontSize: 12, color: '#b6bec8' }}>Model provider
          <select value={provider} onChange={e => setProvider(e.target.value)} style={field} disabled={busy || !!session}>
            <option value="ollama">Ollama · local</option>
            <option value="openai_compatible_local">OpenAI-compatible local</option>
            <option value="gemini">Gemini · configured remote</option>
          </select>
        </label>
      </div>
      <label style={{ display: 'grid', gap: 6, fontSize: 12, color: '#b6bec8', marginTop: 12 }}>What should the agent inspect?
        <textarea value={objective} onChange={e => setObjective(e.target.value)} style={{ ...field, minHeight: 88, resize: 'vertical' }} maxLength={2000} disabled={busy || !!session} />
      </label>

      {!session ? (
        <button style={{ ...action, marginTop: 12 }} disabled={busy || !objective.trim() || !workspace.trim()} onClick={() => void createSession()}>{busy ? 'Working…' : 'Create read-only session'}</button>
      ) : (
        <div style={{ display: 'grid', gap: 10, marginTop: 14 }}>
          <div style={{ border: '1px solid #303741', borderRadius: 10, padding: 12, fontSize: 12 }}>
            <div style={{ color: '#9ca3af' }}>Session scope</div>
            <div style={{ marginTop: 5, overflowWrap: 'anywhere' }}><code>{session.session_id}</code> · {session.state}</div>
            <div style={{ marginTop: 5 }}>{session.objective}</div>
            {agent && <div style={{ color: '#9ca3af', marginTop: 5 }}>Agent {agent.agent_id} · {agent.capabilities.join(' / ')}</div>}
          </div>
          {!authorization ? (
            <button style={action} disabled={busy} onClick={() => void authorize()}>I authorize read, list and Git status</button>
          ) : (
            <button style={action} disabled={busy} onClick={() => void runAgent()}>{busy ? 'Running…' : 'Run agent and collect evidence'}</button>
          )}
          <button style={{ ...action, borderColor: '#4b5563', color: '#d1d5db', background: 'transparent', justifySelf: 'start' }} disabled={busy} onClick={() => { setSession(null); setAgent(null); setAuthorization(false); setRun(null); setDetail(null); setMessage('Ready for a new session.'); }}>New session</button>
        </div>
      )}

      {message && <div role="status" style={{ marginTop: 12, color: '#cbd5e1', fontSize: 12, lineHeight: 1.6 }}>{message}</div>}
      {run && <div style={{ marginTop: 14, borderTop: '1px solid #303741', paddingTop: 14 }}>
        <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap', alignItems: 'center' }}>
          <strong>Run result</strong>
          <span style={{ fontSize: 11, border: '1px solid #46515e', borderRadius: 999, padding: '3px 8px' }}>{run.loop_state || run.state || 'UNKNOWN'}</span>
          {run.run_id && <code style={{ fontSize: 10, color: '#9ca3af' }}>{run.run_id}</code>}
        </div>
        {run.summary && <p style={{ fontSize: 12, color: '#cbd5e1' }}>{run.summary}</p>}
        <div style={{ display: 'grid', gap: 8, marginTop: 10 }}>
          {(run.turns || []).map(turn => <article key={turn.turn_index} style={{ border: '1px solid #303741', borderRadius: 9, padding: 10 }}>
            <div style={{ fontSize: 11, color: '#c9a84c' }}>TURN {turn.turn_index} · {turn.tool_name || 'MODEL'} · {turn.decision}</div>
            {turn.text && <p style={{ whiteSpace: 'pre-wrap', fontSize: 12, lineHeight: 1.5 }}>{turn.text}</p>}
            {turn.observation && <pre style={{ whiteSpace: 'pre-wrap', overflowWrap: 'anywhere', fontSize: 11, color: '#9ca3af' }}>{JSON.stringify(turn.observation, null, 2)}</pre>}
          </article>)}
        </div>
        {detail && <details style={{ marginTop: 12 }}><summary style={{ cursor: 'pointer' }}>Inspect session events and evidence</summary><pre style={{ whiteSpace: 'pre-wrap', overflowWrap: 'anywhere', fontSize: 11, maxHeight: 360, overflow: 'auto' }}>{JSON.stringify({ events: detail.events, evidence: detail.evidence, artifacts: detail.artifacts }, null, 2)}</pre></details>}
      </div>}
    </section>
  );
}
