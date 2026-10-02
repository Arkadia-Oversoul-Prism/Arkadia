/**
 * EL-10 — Engineering Lab operational surface.
 *
 * The C09 operational surface: what is running, who is running, where, what it
 * is doing, what changed, what was observed, what tested, what artifacts and
 * evidence exist, what PR exists, and what requires a human decision.
 *
 * Extends the existing read-only observation lens; it does not replace it and
 * does not introduce a second shell. All data comes from the authenticated
 * /api/lab/engineering/* endpoints. The surface renders real state: an
 * unavailable integration is shown as unavailable, never fabricated.
 */
import { useCallback, useEffect, useState } from 'react';
import { apiRequest, ApiError } from '../../lib/apiClient';
import EngineeringLabWorkspace from './EngineeringLabWorkspace';

type EngineOverview = {
  sessions: Array<{
    session_id: string; state: string; objective: string; agent_id: string;
    workspace_ref: string; repository_ref?: string | null;
  }>;
  agents: Array<{ agent_id: string; role: string; capabilities: string[] }>;
  automations: Array<{ automation_id: string; name: string; state: string }>;
  loop: string[];
  counts: { sessions: number; active: number; awaiting_human: number };
  authority: {
    lab_authority_ceiling: number; autonomous_merge: boolean;
    autonomous_deploy: boolean; human_authorization_required: boolean;
  };
  gateway: { catalog: Array<{ provider: string; model: string; status: string; config_class: string }> };
  integrations: Record<string, { provider: string; state: string; detail?: string }>;
  android: { capabilities: Array<{ capability: string; state: string }>; authority: { merge_exposed: boolean; deploy_exposed: boolean } };
  voice: { recognizer_state: string; assistant_is_hidden_authority: boolean };
  automation_grammar: { may_authorize_consequential_action: boolean; final_transition: string };
};

type SurfaceState = 'LOADING' | 'LIVE' | 'UNAVAILABLE';

const STATE_TONE: Record<string, string> = {
  PROPOSED: '#6b7280', AUTHORIZED: '#3b82f6', QUEUED: '#3b82f6',
  RUNNING: '#f59e0b', CHECKPOINTED: '#f59e0b', VERIFYING: '#a855f7',
  READY_FOR_REVIEW: '#00D4AA', REVISION_REQUIRED: '#f97316',
  BLOCKED: '#ef4444', FAILED: '#ef4444', COMPLETED: '#22c55e',
};

function Badge({ text, tone }: { text: string; tone: string }) {
  return (
    <span
      style={{
        display: 'inline-block', padding: '1px 8px', borderRadius: 999,
        border: `1px solid ${tone}`, color: tone, fontSize: 11, letterSpacing: 0.4,
      }}
    >
      {text}
    </span>
  );
}

function Card({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <section style={{ border: '1px solid #1f2937', borderRadius: 10, padding: 14, marginBottom: 12 }}>
      <h3 style={{ margin: '0 0 10px', fontSize: 13, letterSpacing: 0.6, textTransform: 'uppercase', color: '#00D4AA' }}>
        {title}
      </h3>
      {children}
    </section>
  );
}

export default function EngineeringLabRuntimeLens() {
  const [state, setState] = useState<SurfaceState>('LOADING');
  const [error, setError] = useState<string>('');
  const [data, setData] = useState<EngineOverview | null>(null);

  const load = useCallback(async () => {
    setState('LOADING');
    try {
      const overview = await apiRequest<EngineOverview>('/api/lab/engineering/overview');
      setData(overview);
      setState('LIVE');
    } catch (err) {
      const kind = err instanceof ApiError ? err.kind : 'UNKNOWN';
      setError(`${kind}: ${err instanceof Error ? err.message : 'unknown failure'}`);
      setState('UNAVAILABLE');
    }
  }, []);

  useEffect(() => { void load(); }, [load]);

  if (state === 'LOADING') {
    return <div data-testid="engineering-lab-runtime-lens">The Engineering Lab is reconstructing runtime state…</div>;
  }
  if (state === 'UNAVAILABLE') {
    return (
      <div data-testid="engineering-lab-runtime-lens">
        <div style={{ border: '1px solid #ef4444', borderRadius: 10, padding: 14 }}>
          <strong>Runtime state unavailable.</strong>
          <p style={{ fontSize: 12, opacity: 0.85 }}>{error}</p>
          <button onClick={() => void load()}>Retry</button>
        </div>
      </div>
    );
  }
  if (!data) return null;

  return (
    <div data-testid="engineering-lab-runtime-lens" data-solariun-grammar="operational-surface">
      <EngineeringLabWorkspace onChanged={() => { void load(); }} />
      <Card title="C09 Canonical Loop">
        <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6 }}>
          {data.loop.map((stage) => (
            <span key={stage} style={{ fontSize: 11, padding: '2px 8px', border: '1px solid #374151', borderRadius: 6 }}>
              {stage}
            </span>
          ))}
        </div>
      </Card>

      <Card title="Authority">
        <div style={{ fontSize: 12, lineHeight: 1.8 }}>
          <div>Lab authority ceiling: <strong>Level {data.authority.lab_authority_ceiling}</strong></div>
          <div>Autonomous merge: <strong>{data.authority.autonomous_merge ? 'ENABLED' : 'DISABLED'}</strong></div>
          <div>Autonomous deploy: <strong>{data.authority.autonomous_deploy ? 'ENABLED' : 'DISABLED'}</strong></div>
          <div>Human authorization required: <strong>{String(data.authority.human_authorization_required)}</strong></div>
        </div>
      </Card>

      <Card title="Active Sessions">
        <div style={{ fontSize: 12, opacity: 0.8, marginBottom: 8 }}>
          {data.counts.active} active · {data.counts.awaiting_human} awaiting human decision
        </div>
        {data.sessions.length === 0 ? (
          <div style={{ fontSize: 12, opacity: 0.7 }}>No sessions yet. Open one from the Lab API or Android control plane.</div>
        ) : (
          <ul style={{ listStyle: 'none', padding: 0, margin: 0 }}>
            {data.sessions.map((s) => (
              <li key={s.session_id} style={{ display: 'flex', justifyContent: 'space-between', padding: '6px 0', borderBottom: '1px solid #111827' }}>
                <span>
                  <code style={{ fontSize: 11 }}>{s.session_id}</code>
                  <div style={{ fontSize: 12, opacity: 0.85 }}>{s.objective || '(no objective)'}</div>
                </span>
                <Badge text={s.state} tone={STATE_TONE[s.state] ?? '#6b7280'} />
              </li>
            ))}
          </ul>
        )}
      </Card>

      <Card title="Agents">
        {data.agents.length === 0 ? (
          <div style={{ fontSize: 12, opacity: 0.7 }}>No agents deployed.</div>
        ) : (
          <ul style={{ listStyle: 'none', padding: 0, margin: 0, fontSize: 12 }}>
            {data.agents.map((a) => (
              <li key={a.agent_id} style={{ padding: '4px 0' }}>
                <strong>{a.role}</strong> · <code style={{ fontSize: 11 }}>{a.agent_id}</code> · {a.capabilities.join(', ')}
              </li>
            ))}
          </ul>
        )}
      </Card>

      <Card title="Model Gateway">
        <table style={{ width: '100%', fontSize: 12, borderCollapse: 'collapse' }}>
          <tbody>
            {data.gateway.catalog.slice(0, 9).map((p) => (
              <tr key={p.provider}>
                <td style={{ padding: '3px 0' }}>{p.provider}</td>
                <td style={{ opacity: 0.7 }}>{p.config_class}</td>
                <td><Badge text={p.status} tone={p.status === 'AVAILABLE' ? '#22c55e' : '#6b7280'} /></td>
              </tr>
            ))}
          </tbody>
        </table>
      </Card>

      <Card title="External Integrations">
        <ul style={{ listStyle: 'none', padding: 0, margin: 0, fontSize: 12 }}>
          {Object.entries(data.integrations).map(([name, info]) => (
            <li key={name} style={{ padding: '3px 0' }}>
              <strong>{name}</strong>{' '}
              <Badge text={info.state} tone={info.state === 'AVAILABLE' ? '#22c55e' : '#6b7280'} />
            </li>
          ))}
        </ul>
      </Card>

      <Card title="Android Control Plane / Voice">
        <div style={{ fontSize: 12 }}>
          Android merge exposed: <strong>{String(data.android.authority.merge_exposed)}</strong><br />
          Android deploy exposed: <strong>{String(data.android.authority.deploy_exposed)}</strong><br />
          Voice recognizer: <strong>{data.voice.recognizer_state}</strong><br />
          Assistant is hidden authority: <strong>{String(data.voice.assistant_is_hidden_authority)}</strong>
        </div>
      </Card>
    </div>
  );
}
