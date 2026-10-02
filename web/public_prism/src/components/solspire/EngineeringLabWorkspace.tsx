import { useState } from 'react';
import { ApiError, apiRequest } from '../../lib/apiClient';

type Props = { onChanged: () => void };
type Agent = { agent_id: string; role: string; capabilities: string[] };
type Session = { session_id: string; state: string; objective: string; agent_id: string };
type RunTurn = { turn_index: number; text: string; tool_name?: string | null; decision: string; observation?: Record<string, unknown> | null };
type RunResult = {
  run_id?: string; state?: string; result_state?: string; summary?: string;
  loop_state?: string; turns?: RunTurn[]; evidence_refs?: string[];
};

const C = {
  gold: '#c9a84c', teal: '#00d4aa', ink: '#101317', panel: '#15191f',
  border: 'rgba(255,255,255,.09)', muted: '#9aa4b2', text: '#edf0f3',
  red: '#ef7777', blue: '#7eafe8',
};
const panel: React.CSSProperties = {
  border: `1px solid rgba(201,168,76,.22)`, borderRadius: 18, padding: 20,
  background: 'radial-gradient(ellipse at 100% 0%, rgba(201,168,76,.07), transparent 38%), linear-gradient(145deg,#171b21,#101317)',
  color: C.text, marginBottom: 16, boxShadow: '0 16px 45px rgba(0,0,0,.14)',
};
const field: React.CSSProperties = {
  width: '100%', minWidth: 0, boxSizing: 'border-box', background: '#0d1014',
  color: C.text, border: `1px solid ${C.border}`, borderRadius: 11,
  padding: '12px 13px', font: 'inherit', outlineColor: C.teal,
};
const button: React.CSSProperties = {
  border: `1px solid rgba(0,212,170,.42)`, background: 'rgba(0,212,170,.09)',
  color: C.teal, borderRadius: 11, padding: '11px 15px', fontWeight: 650,
  cursor: 'pointer', font: 'inherit', fontSize: 13,
};
const secondary: React.CSSProperties = {
  ...button, color: '#d1d5db', borderColor: C.border, background: 'rgba(255,255,255,.025)',
};
const label: React.CSSProperties = { display: 'grid', gap: 7, color: '#b7c0cb', fontSize: 12, minWidth: 0 };
const card: React.CSSProperties = {
  border: `1px solid ${C.border}`, borderRadius: 13, background: 'rgba(255,255,255,.025)', padding: 14, minWidth: 0,
};

function explain(error: unknown): string {
  if (error instanceof ApiError) return `${error.kind}: ${error.message}`;
  return error instanceof Error ? error.message : String(error);
}
function shortId(value?: string) {
  return value ? (value.length > 20 ? `${value.slice(0, 8)}…${value.slice(-6)}` : value) : 'Not assigned';
}
function Pill({ children, tone = C.teal }: { children: React.ReactNode; tone?: string }) {
  return <span style={{ display: 'inline-flex', alignItems: 'center', gap: 6, border: `1px solid ${tone}55`, background: `${tone}12`, color: tone, padding: '5px 9px', borderRadius: 999, fontSize: 10, letterSpacing: '.06em', fontWeight: 700 }}>{children}</span>;
}
function SectionTitle({ eyebrow, title, note }: { eyebrow?: string; title: string; note?: string }) {
  return <div style={{ marginBottom: 12 }}><div style={{ color: C.gold, fontSize: 10, letterSpacing: '.16em', textTransform: 'uppercase', fontWeight: 700 }}>{eyebrow || 'WORKSPACE'}</div><h3 style={{ fontSize: 15, margin: '5px 0', fontWeight: 650 }}>{title}</h3>{note && <p style={{ margin: 0, color: C.muted, fontSize: 12, lineHeight: 1.6 }}>{note}</p>}</div>;
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
  const [messageKind, setMessageKind] = useState<'info' | 'error'>('info');
  const [run, setRun] = useState<RunResult | null>(null);
  const [detail, setDetail] = useState<Record<string, unknown> | null>(null);
  const [showRaw, setShowRaw] = useState(false);

  async function createSession() {
    setBusy(true); setMessageKind('info'); setMessage('Preparing your workspace…'); setRun(null); setDetail(null);
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
      setMessage('Workspace prepared. Review the scope before authorizing the read-only inspection.');
      onChanged();
    } catch (error) { setMessageKind('error'); setMessage(explain(error)); }
    finally { setBusy(false); }
  }

  async function authorize() {
    if (!session) return;
    setBusy(true); setMessageKind('info'); setMessage('Recording your authorization…');
    try {
      await apiRequest('/api/lab/engineering/sessions/' + encodeURIComponent(session.session_id) + '/authorize', {
        method: 'POST',
        body: JSON.stringify({ operations_allowed: ['read', 'list', 'git_status'], duration_minutes: 30 }),
      });
      setAuthorization(true); setSession({ ...session, state: 'AUTHORIZED' });
      setMessage('Authorization recorded: read files, list paths, and inspect Git status for 30 minutes. Changes are not permitted.');
      onChanged();
    } catch (error) { setMessageKind('error'); setMessage(explain(error)); }
    finally { setBusy(false); }
  }

  async function runAgent() {
    if (!session || !authorization) return;
    setBusy(true); setMessageKind('info'); setMessage('Agent is inspecting the authorized workspace…'); setRun(null); setDetail(null);
    try {
      const result = await apiRequest<RunResult>('/api/lab/engineering/sessions/' + encodeURIComponent(session.session_id) + '/run-agent', {
        method: 'POST', body: JSON.stringify({ objective: objective.trim(), provider, max_turns: 6 }),
      });
      setRun(result);
      const projection = await apiRequest<Record<string, unknown>>('/api/lab/engineering/sessions/' + encodeURIComponent(session.session_id));
      setDetail(projection);
      setMessage(result.loop_state === 'DONE'
        ? 'Inspection stopped at the review boundary. Read the findings and evidence before deciding what happens next.'
        : 'The run stopped without claiming completion. The observations below show what was returned.');
      onChanged();
    } catch (error) { setMessageKind('error'); setMessage(explain(error)); }
    finally { setBusy(false); }
  }

  const steps = [
    { label: 'Set up', done: !!session },
    { label: 'Authorize', done: authorization },
    { label: 'Inspect', done: !!run },
    { label: 'Review evidence', done: !!detail },
  ];
  const status = busy ? 'WORKING' : run ? (run.loop_state || run.state || 'RUN COMPLETE') : authorization ? 'AUTHORIZED' : session ? 'AWAITING AUTHORIZATION' : 'READY';
  const statusTone = busy ? C.gold : messageKind === 'error' ? C.red : authorization ? C.teal : C.blue;

  return (
    <section data-testid="engineering-lab-workspace" style={panel}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', gap: 14, flexWrap: 'wrap' }}>
        <div style={{ minWidth: 0, flex: '1 1 270px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8, flexWrap: 'wrap' }}><Pill tone={C.gold}>ENGINEERING LAB</Pill><span style={{ color: C.muted, fontSize: 11 }}>SolSpire workspace</span></div>
          <h2 style={{ margin: '12px 0 5px', fontSize: 'clamp(22px, 3vw, 29px)', lineHeight: 1.15, letterSpacing: '-.035em', fontWeight: 650 }}>Build with visibility.</h2>
          <p style={{ margin: 0, color: C.muted, fontSize: 13, lineHeight: 1.65, maxWidth: 560 }}>Give an agent a bounded inspection task, watch what it observes, then review the evidence. You remain in control of every consequential step.</p>
        </div>
        <div style={{ ...card, minWidth: 150, padding: 12 }}>
          <div style={{ color: C.muted, fontSize: 10, textTransform: 'uppercase', letterSpacing: '.12em' }}>Session state</div>
          <div style={{ marginTop: 8 }}><Pill tone={statusTone}>{status.replaceAll('_', ' ')}</Pill></div>
          <div style={{ color: C.muted, fontSize: 10, marginTop: 9 }}>Read-only authority ceiling</div>
        </div>
      </div>

      <div aria-label="Inspection progress" style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit,minmax(130px,1fr))', gap: 8, margin: '20px 0' }}>
        {steps.map((step, index) => <div key={step.label} style={{ display: 'flex', alignItems: 'center', gap: 9, padding: '10px 11px', borderRadius: 10, border: `1px solid ${step.done ? 'rgba(0,212,170,.26)' : C.border}`, background: step.done ? 'rgba(0,212,170,.055)' : 'rgba(255,255,255,.015)' }}>
          <span style={{ width: 23, height: 23, display: 'grid', placeItems: 'center', borderRadius: 8, background: step.done ? 'rgba(0,212,170,.14)' : 'rgba(255,255,255,.06)', color: step.done ? C.teal : C.muted, fontSize: 11, fontWeight: 700 }}>{step.done ? '✓' : String(index + 1).padStart(2, '0')}</span>
          <span style={{ fontSize: 11, color: step.done ? C.text : C.muted }}>{step.label}</span>
        </div>)}
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit,minmax(min(100%,260px),1fr))', gap: 12 }}>
        <div style={card}>
          <SectionTitle eyebrow="01 · Task" title="What should be inspected?" note="Start with one clear objective. The agent cannot modify repository state in this slice." />
          <label style={label}>Workspace reference
            <input aria-label="Workspace reference" value={workspace} onChange={e => setWorkspace(e.target.value)} style={field} maxLength={100} disabled={busy || !!session} placeholder="Workspace name or reference" />
          </label>
          <label style={{ ...label, marginTop: 12 }}>Inspection objective
            <textarea aria-label="Inspection objective" value={objective} onChange={e => setObjective(e.target.value)} style={{ ...field, minHeight: 106, resize: 'vertical', lineHeight: 1.55 }} maxLength={2000} disabled={busy || !!session} placeholder="Describe what the agent should inspect…" />
          </label>
          <label style={{ ...label, marginTop: 12 }}>Model route
            <select aria-label="Model route" value={provider} onChange={e => setProvider(e.target.value)} style={field} disabled={busy || !!session}>
              <option value="ollama">Local · Ollama</option>
              <option value="openai_compatible_local">Local · OpenAI-compatible</option>
              <option value="gemini">Remote · Gemini</option>
            </select>
          </label>
          {!session && <button style={{ ...button, marginTop: 14, width: '100%' }} disabled={busy || !objective.trim() || !workspace.trim()} onClick={() => void createSession()}>{busy ? 'Preparing workspace…' : 'Create inspection session  →'}</button>}
          {session && <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap', marginTop: 14 }}><button style={secondary} disabled={busy} onClick={() => { setSession(null); setAgent(null); setAuthorization(false); setRun(null); setDetail(null); setMessage('Ready for a new session.'); setMessageKind('info'); }}>Start a new session</button></div>}
        </div>

        <div style={card}>
          <SectionTitle eyebrow="02 · Authority" title="A visible permission boundary" note="Authorization is explicit, scoped, and time-limited. It does not permit edits, commits, merges, or deployment." />
          <div style={{ display: 'grid', gap: 8 }}>
            {[
              ['Read files', 'Inspect file contents'],
              ['List paths', 'Understand workspace structure'],
              ['Git status', 'Observe tracked changes'],
            ].map(([name, description]) => <div key={name} style={{ display: 'flex', gap: 10, alignItems: 'flex-start', padding: 10, border: `1px solid ${C.border}`, borderRadius: 10 }}>
              <span style={{ color: authorization ? C.teal : C.muted, fontSize: 14 }}>{authorization ? '✓' : '○'}</span><div><div style={{ fontSize: 12, fontWeight: 600 }}>{name}</div><div style={{ color: C.muted, fontSize: 11, marginTop: 3 }}>{description}</div></div>
            </div>)}
          </div>
          {session && <div style={{ marginTop: 12, padding: 11, borderRadius: 10, background: 'rgba(255,255,255,.025)', border: `1px solid ${C.border}` }}>
            <div style={{ fontSize: 10, color: C.muted, textTransform: 'uppercase', letterSpacing: '.1em' }}>Session reference</div>
            <code title={session.session_id} style={{ display: 'block', marginTop: 6, overflowWrap: 'anywhere', fontSize: 11 }}>{shortId(session.session_id)}</code>
            <div style={{ display: 'flex', gap: 6, alignItems: 'center', flexWrap: 'wrap', marginTop: 9 }}><Pill tone={authorization ? C.teal : C.gold}>{session.state.replaceAll('_', ' ')}</Pill>{agent && <span style={{ color: C.muted, fontSize: 10 }}>Weaver · {agent.capabilities.join(' / ')}</span>}</div>
          </div>}
          {!session && <div style={{ marginTop: 12, color: C.muted, fontSize: 11, lineHeight: 1.6 }}>Create a session to inspect the exact scope before permission can be granted.</div>}
          {session && !authorization && <button style={{ ...button, width: '100%', marginTop: 13 }} disabled={busy} onClick={() => void authorize()}>{busy ? 'Recording authorization…' : 'Authorize read-only inspection'}</button>}
          {session && authorization && !run && <button style={{ ...button, width: '100%', marginTop: 13 }} disabled={busy} onClick={() => void runAgent()}>{busy ? 'Inspecting…' : 'Run agent  →'}</button>}
          {authorization && <div style={{ marginTop: 10, color: C.teal, fontSize: 11, lineHeight: 1.5 }}>Human authorization recorded for this session. No mutation capability is exposed here.</div>}
        </div>
      </div>

      {message && <div role="status" aria-live="polite" style={{ display: 'flex', gap: 10, alignItems: 'flex-start', marginTop: 13, padding: '11px 13px', borderRadius: 11, border: `1px solid ${messageKind === 'error' ? 'rgba(239,119,119,.35)' : C.border}`, background: messageKind === 'error' ? 'rgba(239,119,119,.06)' : 'rgba(255,255,255,.025)', color: messageKind === 'error' ? '#ffb4b4' : '#c9d0d9', fontSize: 12, lineHeight: 1.6 }}>
        <span aria-hidden="true" style={{ color: messageKind === 'error' ? C.red : C.teal }}>{messageKind === 'error' ? '!' : '●'}</span><span>{message}</span>
      </div>}

      {run && <div style={{ marginTop: 18 }}>
        <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', gap: 12, flexWrap: 'wrap', marginBottom: 12 }}>
          <div><SectionTitle eyebrow="03 · Observations" title="Run report" note="These are recorded observations, not approval to change the repository." />{run.run_id && <code style={{ color: C.muted, fontSize: 10 }}>Run {shortId(run.run_id)}</code>}</div>
          <Pill tone={run.loop_state === 'DONE' ? C.teal : C.gold}>{(run.loop_state || run.state || 'STATE UNKNOWN').replaceAll('_', ' ')}</Pill>
        </div>
        {run.summary && <div style={{ ...card, marginBottom: 12, fontSize: 13, lineHeight: 1.7 }}>{run.summary}</div>}
        <div style={{ display: 'grid', gap: 9 }}>
          {(run.turns || []).map((turn, index) => <article key={turn.turn_index ?? index} style={{ ...card, padding: 0, overflow: 'hidden' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: 10, flexWrap: 'wrap', padding: '11px 13px', borderBottom: `1px solid ${C.border}`, background: 'rgba(255,255,255,.02)' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}><span style={{ color: C.gold, fontSize: 10, fontWeight: 800 }}>STEP {String(index + 1).padStart(2, '0')}</span><span style={{ fontSize: 12, fontWeight: 600 }}>{turn.tool_name || 'Agent reasoning'}</span></div>
              <Pill tone={turn.decision?.toLowerCase().includes('deny') || turn.decision?.toLowerCase().includes('block') ? C.red : C.blue}>{(turn.decision || 'OBSERVED').replaceAll('_', ' ')}</Pill>
            </div>
            <div style={{ padding: 13 }}>
              {turn.text && <p style={{ whiteSpace: 'pre-wrap', overflowWrap: 'anywhere', fontSize: 12, lineHeight: 1.7, margin: 0 }}>{turn.text}</p>}
              {turn.observation && <details style={{ marginTop: 10 }}><summary style={{ color: C.muted, cursor: 'pointer', fontSize: 11 }}>View tool observation</summary><pre style={{ whiteSpace: 'pre-wrap', overflowWrap: 'anywhere', fontSize: 11, lineHeight: 1.55, color: '#c2cbd5', background: '#0b0e12', padding: 12, borderRadius: 9, maxHeight: 320, overflow: 'auto' }}>{JSON.stringify(turn.observation, null, 2)}</pre></details>}
            </div>
          </article>)}
          {!(run.turns || []).length && <div style={{ ...card, color: C.muted, fontSize: 12 }}>No turn details were returned by the runtime for this run.</div>}
        </div>
        {(run.evidence_refs?.length || detail) && <div style={{ marginTop: 12, ...card }}>
          <SectionTitle eyebrow="04 · Evidence" title="What the run left behind" note="Review evidence before proposing any next action." />
          {run.evidence_refs?.length ? <div style={{ display: 'flex', gap: 7, flexWrap: 'wrap' }}>{run.evidence_refs.map(ref => <Pill key={ref} tone={C.gold}>{shortId(ref)}</Pill>)}</div> : <div style={{ color: C.muted, fontSize: 12 }}>No evidence references were returned in the run response.</div>}
          {detail && <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap', marginTop: 12 }}>
            {(['events', 'evidence', 'artifacts'] as const).map(key => {
              const value = detail[key];
              const count = Array.isArray(value) ? value.length : value && typeof value === 'object' ? Object.keys(value as Record<string, unknown>).length : 0;
              return <div key={key} style={{ flex: '1 1 110px', border: `1px solid ${C.border}`, borderRadius: 10, padding: 10 }}><div style={{ color: C.muted, fontSize: 10, textTransform: 'uppercase' }}>{key}</div><div style={{ fontSize: 20, marginTop: 4, fontWeight: 650 }}>{count}</div><div style={{ color: C.muted, fontSize: 10 }}>recorded items</div></div>;
            })}
          </div>}
          {detail && <button style={{ ...secondary, marginTop: 12 }} onClick={() => setShowRaw(value => !value)} aria-expanded={showRaw}>{showRaw ? 'Hide raw session records' : 'Inspect raw session records'}</button>}
          {detail && showRaw && <pre style={{ whiteSpace: 'pre-wrap', overflowWrap: 'anywhere', fontSize: 11, lineHeight: 1.5, color: '#c2cbd5', background: '#0b0e12', padding: 12, borderRadius: 9, maxHeight: 380, overflow: 'auto' }}>{JSON.stringify({ events: detail.events, evidence: detail.evidence, artifacts: detail.artifacts }, null, 2)}</pre>}
        </div>}
      </div>}
    </section>
  );
}
