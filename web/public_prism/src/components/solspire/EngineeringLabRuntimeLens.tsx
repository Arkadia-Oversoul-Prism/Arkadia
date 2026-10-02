/**
 * Engineering Lab operational surface inside the existing SolSpire workspace.
 * This is a comprehension and control surface, not a second execution authority.
 * Runtime facts come from the authenticated Engineering Lab API.
 */
import { useCallback, useEffect, useState } from 'react';
import { apiRequest, ApiError } from '../../lib/apiClient';
import EngineeringLabWorkspace from './EngineeringLabWorkspace';

type EngineOverview = {
  sessions: Array<{ session_id: string; state: string; objective: string; agent_id: string; workspace_ref: string; repository_ref?: string | null }>;
  agents: Array<{ agent_id: string; role: string; capabilities: string[] }>;
  automations: Array<{ automation_id: string; name: string; state: string }>;
  loop: string[];
  counts: { sessions: number; active: number; awaiting_human: number };
  authority: { lab_authority_ceiling: number; autonomous_merge: boolean; autonomous_deploy: boolean; human_authorization_required: boolean };
  gateway: { catalog: Array<{ provider: string; model: string; status: string; config_class: string }> };
  integrations: Record<string, { provider: string; state: string; detail?: string }>;
  android: { capabilities: Array<{ capability: string; state: string }>; authority: { merge_exposed: boolean; deploy_exposed: boolean } };
  voice: { recognizer_state: string; assistant_is_hidden_authority: boolean };
  automation_grammar: { may_authorize_consequential_action: boolean; final_transition: string };
};

type SurfaceState = 'LOADING' | 'LIVE' | 'UNAVAILABLE';
const T = { gold: '#c9a84c', teal: '#00d4aa', text: '#edf0f3', muted: '#9aa4b2', border: 'rgba(255,255,255,.09)', red: '#ef7777' };
const surface: React.CSSProperties = { color: T.text, minWidth: 0 };
const panel: React.CSSProperties = { border: `1px solid ${T.border}`, borderRadius: 15, padding: 16, background: 'rgba(19,23,28,.82)', minWidth: 0 };
const pill = (tone: string): React.CSSProperties => ({ display: 'inline-flex', alignItems: 'center', border: `1px solid ${tone}55`, background: `${tone}12`, color: tone, borderRadius: 999, padding: '4px 8px', fontSize: 10, fontWeight: 700, letterSpacing: '.06em' });
const buttonStyle: React.CSSProperties = { background: 'rgba(255,255,255,.03)', border: `1px solid ${T.border}`, borderRadius: 9, color: T.text, padding: '8px 11px', font: 'inherit', fontSize: 12, cursor: 'pointer' };
const STATE_TONE: Record<string, string> = { PROPOSED: '#9aa4b2', AUTHORIZED: '#7eafe8', QUEUED: '#7eafe8', RUNNING: T.gold, CHECKPOINTED: T.gold, VERIFYING: '#b08de8', READY_FOR_REVIEW: T.teal, REVISION_REQUIRED: '#f0a06b', BLOCKED: T.red, FAILED: T.red, COMPLETED: T.teal };

function StatusPill({ value }: { value: string }) {
  const tone = STATE_TONE[value] || (value === 'AVAILABLE' ? T.teal : '#9aa4b2');
  return <span style={pill(tone)}>{value.replaceAll('_', ' ')}</span>;
}
function Metric({ value, label, note }: { value: string | number; label: string; note?: string }) {
  return <div style={panel}><div style={{ color: T.muted, fontSize: 10, letterSpacing: '.1em', textTransform: 'uppercase' }}>{label}</div><div style={{ fontSize: 27, lineHeight: 1.2, marginTop: 8, fontWeight: 650, letterSpacing: '-.04em' }}>{value}</div>{note && <div style={{ color: T.muted, fontSize: 11, marginTop: 5 }}>{note}</div>}</div>;
}
function Section({ title, note, children }: { title: string; note?: string; children: React.ReactNode }) {
  return <section style={{ ...panel, marginTop: 12 }}><div style={{ marginBottom: 12 }}><h3 style={{ fontSize: 13, margin: 0, fontWeight: 650 }}>{title}</h3>{note && <p style={{ color: T.muted, fontSize: 11, margin: '5px 0 0', lineHeight: 1.55 }}>{note}</p>}</div>{children}</section>;
}
function humanize(value: string) { return value.replaceAll('_', ' ').toLowerCase().replace(/^./, c => c.toUpperCase()); }

export default function EngineeringLabRuntimeLens() {
  const [state, setState] = useState<SurfaceState>('LOADING');
  const [error, setError] = useState('');
  const [data, setData] = useState<EngineOverview | null>(null);
  const [refreshedAt, setRefreshedAt] = useState<Date | null>(null);

  const load = useCallback(async (showLoading = true) => {
    if (showLoading) setState('LOADING');
    try {
      const overview = await apiRequest<EngineOverview>('/api/lab/engineering/overview');
      setData(overview); setError(''); setState('LIVE'); setRefreshedAt(new Date());
    } catch (err) {
      const kind = err instanceof ApiError ? err.kind : 'UNKNOWN';
      setError(`${kind}: ${err instanceof Error ? err.message : 'unknown failure'}`);
      if (!data || showLoading) setState('UNAVAILABLE');
    }
  }, [data]);

  useEffect(() => { void load(); }, [load]);
  const refreshOverview = useCallback(async () => { await load(false); }, [load]);

  if (state === 'LOADING') return <div data-testid="engineering-lab-runtime-lens" style={{ ...surface, ...panel }}><div style={{ color: T.gold, fontSize: 10, letterSpacing: '.14em' }}>SOLSPIRE / ENGINEERING LAB</div><h2 style={{ margin: '9px 0 4px', fontSize: 20 }}>Opening your workspace…</h2><p style={{ color: T.muted, fontSize: 12 }}>Connecting to the authenticated runtime view.</p></div>;
  if (state === 'UNAVAILABLE') return <div data-testid="engineering-lab-runtime-lens" style={{ ...surface, ...panel, borderColor: 'rgba(239,119,119,.35)' }}><StatusPill value="RUNTIME UNAVAILABLE" /><h2 style={{ margin: '12px 0 6px', fontSize: 20 }}>The Lab could not load its live state.</h2><p style={{ color: T.muted, fontSize: 12, lineHeight: 1.6 }}>{error}</p><button style={buttonStyle} onClick={() => void load()}>Try again</button></div>;
  if (!data) return null;

  const availableProviders = data.gateway.catalog.filter(p => p.status === 'AVAILABLE').length;
  const integrationEntries = Object.entries(data.integrations || {});
  return (
    <div data-testid="engineering-lab-runtime-lens" data-solariun-grammar="operational-surface" style={surface}>
      <div style={{ ...panel, padding: 19, background: 'radial-gradient(ellipse at 100% 0%, rgba(201,168,76,.09), transparent 42%), rgba(19,23,28,.82)' }}>
        <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', flexWrap: 'wrap', gap: 12 }}>
          <div style={{ minWidth: 0 }}>
            <div style={{ color: T.gold, fontSize: 10, letterSpacing: '.16em', fontWeight: 700 }}>SOLSPIRE · ENGINEERING LAB</div>
            <h1 style={{ margin: '8px 0 5px', fontSize: 'clamp(23px,3vw,31px)', lineHeight: 1.15, letterSpacing: '-.04em' }}>Your engineering workspace.</h1>
            <p style={{ margin: 0, color: T.muted, fontSize: 12, lineHeight: 1.65, maxWidth: 650 }}>Inspect work, coordinate agents, and follow the evidence trail from one place. Consequential changes remain behind the existing governed execution path.</p>
          </div>
          <button style={buttonStyle} onClick={() => void load(false)} disabled={state === 'LOADING'}>↻ Refresh</button>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: 8, flexWrap: 'wrap', marginTop: 14 }}>
          <StatusPill value="LIVE OVERVIEW" />
          <span style={{ color: T.muted, fontSize: 10 }}>{refreshedAt ? `Updated ${refreshedAt.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}` : 'Waiting for first refresh'}</span>
          {error && <span role="status" style={{ color: T.gold, fontSize: 11 }}>Refresh issue: {error}</span>}
        </div>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit,minmax(135px,1fr))', gap: 9, marginTop: 12 }}>
        <Metric value={data.counts.sessions} label="Sessions" note="Recorded in the Lab" />
        <Metric value={data.counts.active} label="In progress" note="Active sessions" />
        <Metric value={data.counts.awaiting_human} label="Your review" note="Awaiting a human decision" />
        <Metric value={availableProviders} label="Model routes" note={`of ${data.gateway.catalog.length} marked available`} />
      </div>

      <EngineeringLabWorkspace onChanged={() => { void refreshOverview(); }} />

      <Section title="Work in motion" note="Live sessions from the backend. Start a new inspection above; this list reflects the recorded overview.">
        {data.sessions.length === 0 ? <div style={{ padding: '12px 0', color: T.muted, fontSize: 12 }}>No sessions recorded yet. Create the first inspection in the workspace above.</div> : <div style={{ display: 'grid', gap: 8 }}>
          {data.sessions.map(s => <div key={s.session_id} style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', gap: 12, flexWrap: 'wrap', border: `1px solid ${T.border}`, borderRadius: 11, padding: 12 }}>
            <div style={{ minWidth: 0, flex: '1 1 220px' }}><div style={{ fontSize: 12, fontWeight: 600, lineHeight: 1.5 }}>{s.objective || 'Untitled session'}</div><div style={{ marginTop: 5, color: T.muted, fontSize: 10, overflowWrap: 'anywhere' }}>{s.workspace_ref} · {s.session_id.slice(0, 8)}…</div></div><StatusPill value={s.state} />
          </div>)}
        </div>}
      </Section>

      <details style={{ ...panel, marginTop: 12 }}>
        <summary style={{ cursor: 'pointer', fontSize: 12, fontWeight: 650, listStylePosition: 'inside' }}>System map and connected capabilities <span style={{ color: T.muted, fontWeight: 400 }}>· technical details</span></summary>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit,minmax(min(100%,250px),1fr))', gap: 10, marginTop: 14 }}>
          <div style={panel}><h4 style={{ margin: '0 0 9px', fontSize: 12 }}>Authority boundary</h4><div style={{ display: 'grid', gap: 8, fontSize: 11, color: T.muted }}>
            <div>Lab ceiling <strong style={{ color: T.text }}>Level {data.authority.lab_authority_ceiling}</strong></div>
            <div>Human authorization <strong style={{ color: T.text }}>{data.authority.human_authorization_required ? 'Required' : 'Not required'}</strong></div>
            <div>Agent merge <strong style={{ color: data.authority.autonomous_merge ? T.red : T.teal }}>{data.authority.autonomous_merge ? 'Enabled' : 'Disabled'}</strong></div>
            <div>Agent deploy <strong style={{ color: data.authority.autonomous_deploy ? T.red : T.teal }}>{data.authority.autonomous_deploy ? 'Enabled' : 'Disabled'}</strong></div>
          </div></div>
          <div style={panel}><h4 style={{ margin: '0 0 9px', fontSize: 12 }}>Model gateway</h4>{data.gateway.catalog.length ? <div style={{ display: 'grid', gap: 8 }}>{data.gateway.catalog.slice(0, 12).map(p => <div key={p.provider} style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 8, fontSize: 11 }}><span>{humanize(p.provider)}<div style={{ color: T.muted, fontSize: 10 }}>{p.model || p.config_class}</div></span><StatusPill value={p.status} /></div>)}</div> : <div style={{ color: T.muted, fontSize: 11 }}>No model routes were returned.</div>}</div>
          <div style={panel}><h4 style={{ margin: '0 0 9px', fontSize: 12 }}>Agents</h4>{data.agents.length ? <div style={{ display: 'grid', gap: 8 }}>{data.agents.map(a => <div key={a.agent_id} style={{ fontSize: 11 }}><div style={{ fontWeight: 650 }}>{humanize(a.role)}</div><div style={{ color: T.muted, marginTop: 3 }}>{a.capabilities.join(' · ') || 'No capabilities reported'}</div></div>)}</div> : <div style={{ color: T.muted, fontSize: 11 }}>No agents registered.</div>}</div>
          <div style={panel}><h4 style={{ margin: '0 0 9px', fontSize: 12 }}>Integrations</h4>{integrationEntries.length ? <div style={{ display: 'grid', gap: 8 }}>{integrationEntries.map(([name, info]) => <div key={name} style={{ display: 'flex', justifyContent: 'space-between', gap: 8, alignItems: 'center', fontSize: 11 }}><span>{humanize(name)}</span><StatusPill value={info.state} /></div>)}</div> : <div style={{ color: T.muted, fontSize: 11 }}>No integration states returned.</div>}</div>
          <div style={panel}><h4 style={{ margin: '0 0 9px', fontSize: 12 }}>Automation and mobile</h4><div style={{ display: 'grid', gap: 7, color: T.muted, fontSize: 11 }}>
            <div>Automations recorded: <strong style={{ color: T.text }}>{data.automations.length}</strong></div>
            <div>Android merge control: <strong style={{ color: T.text }}>{data.android.authority.merge_exposed ? 'Exposed' : 'Not exposed'}</strong></div>
            <div>Android deploy control: <strong style={{ color: T.text }}>{data.android.authority.deploy_exposed ? 'Exposed' : 'Not exposed'}</strong></div>
            <div>Voice recognizer: <strong style={{ color: T.text }}>{humanize(data.voice.recognizer_state)}</strong></div>
            <div>Voice as hidden authority: <strong style={{ color: T.text }}>{data.voice.assistant_is_hidden_authority ? 'Yes' : 'No'}</strong></div>
          </div></div>
          <div style={panel}><h4 style={{ margin: '0 0 9px', fontSize: 12 }}>Governed workflow</h4><div style={{ display: 'flex', gap: 6, flexWrap: 'wrap' }}>{data.loop.map((stage, index) => <span key={stage} style={{ border: `1px solid ${T.border}`, borderRadius: 7, padding: '6px 8px', color: T.muted, fontSize: 10 }}>{index + 1}. {humanize(stage)}</span>)}</div><div style={{ marginTop: 10, color: T.muted, fontSize: 11 }}>Consequential action: <strong style={{ color: T.text }}>{data.automation_grammar.final_transition}</strong></div></div>
        </div>
      </details>
    </div>
  );
}
