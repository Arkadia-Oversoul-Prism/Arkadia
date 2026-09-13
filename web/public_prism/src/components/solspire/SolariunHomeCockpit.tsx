import React, { useEffect, useState } from 'react';
import { apiRequest } from '../../lib/apiClient';

const GOLD = '#C9A84C';
const TEAL = '#00D4AA';
const BLUE = '#6A9FD8';
const MUTED = 'rgba(232,232,232,0.58)';
const PANEL = 'rgba(255,255,255,0.035)';
const BORDER = 'rgba(255,255,255,0.09)';

type RecordValue = Record<string, any>;

function first<T = any>(...values: T[]): T | undefined { return values.find(v => v !== undefined && v !== null && v !== ''); }
function text(value: any, fallback = 'No signal recorded.') { return typeof value === 'string' ? value : value == null ? fallback : String(value); }
function dateLabel(value: any) {
  if (value == null) return '';
  const n = typeof value === 'number' ? (value < 10000000000 ? value * 1000 : value) : Date.parse(String(value));
  if (!Number.isFinite(n)) return '';
  return new Date(n).toLocaleString(undefined, { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' });
}

function Card({ label, children, accent = GOLD, className = '' }: { label: string; children: React.ReactNode; accent?: string; className?: string }) {
  return <section className={className} style={{ background: PANEL, border: `1px solid ${BORDER}`, borderRadius: 18, padding: 18, minWidth: 0 }}>
    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: 12, marginBottom: 12 }}>
      <span style={{ fontSize: 9, letterSpacing: '0.22em', textTransform: 'uppercase', color: `${accent}cc` }}>{label}</span>
      <span style={{ width: 6, height: 6, borderRadius: '50%', background: accent, opacity: 0.8 }} />
    </div>
    {children}
  </section>;
}

function Loading({ label }: { label: string }) { return <div style={{ color: MUTED, fontSize: 12 }}>{label}…</div>; }
function ErrorState({ message }: { message: string }) { return <div style={{ color: '#ef9a9a', fontSize: 12 }}>{message}</div>; }

function normalizeArray(data: any, keys: string[]) {
  for (const key of keys) if (Array.isArray(data?.[key])) return data[key];
  return [];
}

export default function SolariunHomeCockpit() {
  const [pulse, setPulse] = useState<RecordValue | null>(null);
  const [workload, setWorkload] = useState<RecordValue | null>(null);
  const [events, setEvents] = useState<RecordValue[]>([]);
  const [synthesis, setSynthesis] = useState<RecordValue | null>(null);
  const [proposals, setProposals] = useState<RecordValue[]>([]);
  const [state, setState] = useState<'loading' | 'ready' | 'partial'>('loading');
  const [errorCount, setErrorCount] = useState(0);

  useEffect(() => {
    let alive = true;
    Promise.allSettled([
      apiRequest<RecordValue>('/solspire/pulses/today'),
      apiRequest<RecordValue>('/solspire/workloads'),
      apiRequest<RecordValue>('/solspire/workevents?limit=8'),
      apiRequest<RecordValue>('/solspire/syntheses/current'),
      apiRequest<RecordValue>('/solspire/proposals?limit=20'),
    ]).then(results => {
      if (!alive) return;
      const failures = results.filter(r => r.status === 'rejected').length;
      if (results[0].status === 'fulfilled') setPulse(results[0].value?.pulse ?? null);
      if (results[1].status === 'fulfilled') setWorkload(results[1].value?.workload ?? null);
      if (results[2].status === 'fulfilled') setEvents(normalizeArray(results[2].value, ['work_events', 'events']));
      if (results[3].status === 'fulfilled') setSynthesis(results[3].value?.synthesis ?? null);
      if (results[4].status === 'fulfilled') setProposals(normalizeArray(results[4].value, ['proposals']));
      setErrorCount(failures);
      setState(failures ? 'partial' : 'ready');
    });
    return () => { alive = false; };
  }, []);

  const openProposals = proposals.filter(p => ['DRAFT', 'PRESENTED', 'UNDER_REVIEW', 'REVISION_REQUESTED', 'REVISED', 'DECISION_PENDING'].includes(String(p.proposal_status ?? p.status)));
  const pulseData = pulse ?? {};
  const synthesisData = synthesis ?? {};
  const workloadData = workload ?? {};

  return <div style={{ display: 'flex', flexDirection: 'column', gap: 18, width: '100%' }}>
    <div style={{ padding: '4px 2px 6px' }}>
      <div style={{ fontSize: 9, letterSpacing: '0.28em', textTransform: 'uppercase', color: TEAL }}>Solariun / Home</div>
      <h2 style={{ margin: '7px 0 5px', fontFamily: 'serif', fontWeight: 500, fontSize: 'clamp(30px, 5vw, 46px)', lineHeight: 1.05 }}>Personal Intelligence Workspace</h2>
      <p style={{ margin: 0, color: MUTED, fontSize: 13, maxWidth: 680 }}>One field for what changed, what is active, what persists, and what now asks for your attention.</p>
    </div>

    {state === 'loading' && <Card label="Live field" accent={TEAL}><Loading label="Reading the sovereign workspace" /></Card>}
    {state !== 'loading' && errorCount > 0 && <div style={{ fontSize: 11, color: MUTED, padding: '0 2px' }}>Some live surfaces are quiet or unavailable. No placeholder data is being substituted.</div>}

    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(min(100%, 280px), 1fr))', gap: 14 }}>
      <Card label="Today" accent={TEAL}>
        <div style={{ fontFamily: 'serif', fontSize: 22, lineHeight: 1.2 }}>{text(first(pulseData.state_summary, pulseData.summary), 'No daily pulse recorded.')}</div>
        <div style={{ marginTop: 12, display: 'flex', flexWrap: 'wrap', gap: 12, color: MUTED, fontSize: 11 }}>
          <span>{text(first(pulseData.period), 'day')}</span>
          {first(pulseData.created_at, pulseData.updated_at, pulseData.occurred_at) && <span>{dateLabel(first(pulseData.created_at, pulseData.updated_at, pulseData.occurred_at))}</span>}
        </div>
      </Card>

      <Card label="Open loops" accent={BLUE}>
        <div style={{ fontSize: 13, color: MUTED }}>{text(first(pulseData.open_loops, pulseData.open_loop_summary, pulseData.loops), 'No open-loop summary recorded.')}</div>
      </Card>

      <Card label="Current signal" accent={GOLD}>
        <div style={{ fontSize: 13, lineHeight: 1.55 }}>{text(first(pulseData.current_signal, pulseData.signal, pulseData.signal_summary), 'No current signal recorded.')}</div>
      </Card>
    </div>

    <Card label="Active work" accent={GOLD}>
      {workload ? <div style={{ display: 'grid', gap: 10 }}>
        <div style={{ fontFamily: 'serif', fontSize: 24 }}>{text(first(workloadData.title, workloadData.display_name), 'Canonical workload')}</div>
        <div style={{ color: MUTED, fontSize: 12 }}>{text(workloadData.objective)}</div>
        <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8, marginTop: 2 }}>
          {[first(workloadData.status), first(workloadData.phase), first(workloadData.workload_type)].filter(Boolean).map((v, i) => <span key={`${v}-${i}`} style={{ border: `1px solid ${BORDER}`, borderRadius: 999, padding: '5px 9px', fontSize: 9, letterSpacing: '0.12em', color: i === 0 ? GOLD : MUTED }}>{String(v).replaceAll('_', ' ')}</span>)}
        </div>
        <div style={{ color: MUTED, fontSize: 11, paddingTop: 4 }}>Barnabas · Eden Food Systems · R01 — Plateau Market Reconnaissance</div>
      </div> : <div style={{ color: MUTED, fontSize: 12 }}>No canonical workload is currently available.</div>}
    </Card>

    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(min(100%, 320px), 1fr))', gap: 14 }}>
      <Card label="Continuity" accent={BLUE}>
        {events.length ? <div style={{ display: 'grid', gap: 12 }}>{events.slice(0, 6).map((event, i) => <div key={String(first(event.work_event_id, event.id, i))} style={{ display: 'grid', gridTemplateColumns: '7px 1fr auto', gap: 10, alignItems: 'start' }}>
          <span style={{ width: 7, height: 7, marginTop: 5, borderRadius: '50%', background: BLUE }} />
          <div><div style={{ fontSize: 12 }}>{text(first(event.event_type, event.type), 'WorkEvent')}</div><div style={{ color: MUTED, fontSize: 10, marginTop: 3 }}>{text(first(event.state_after_ref, event.work_ref, event.scope_ref), '')}</div></div>
          <span style={{ color: MUTED, fontSize: 9, whiteSpace: 'nowrap' }}>{dateLabel(first(event.occurred_at, event.created_at))}</span>
        </div>)}</div> : <div style={{ color: MUTED, fontSize: 12 }}>No recent WorkEvents recorded.</div>}
      </Card>

      <Card label="This week" accent={TEAL}>
        <div style={{ fontFamily: 'serif', fontSize: 22, lineHeight: 1.25 }}>{text(first(synthesisData.summary, synthesisData.synthesis_summary), 'No current weekly synthesis recorded.')}</div>
        <div style={{ color: MUTED, fontSize: 10, marginTop: 12 }}>{dateLabel(first(synthesisData.created_at, synthesisData.updated_at))}</div>
      </Card>
    </div>

    <Card label="Decisions" accent={GOLD}>
      {openProposals.length ? <div style={{ display: 'grid', gap: 10 }}>{openProposals.slice(0, 5).map((proposal, i) => <div key={String(first(proposal.proposal_id, i))} style={{ display: 'grid', gap: 5, padding: '11px 0', borderBottom: i < Math.min(openProposals.length, 5) - 1 ? `1px solid ${BORDER}` : 'none' }}>
        <div style={{ fontSize: 13 }}>{text(first(proposal.objective, proposal.requested_decision), 'Untitled proposal')}</div>
        <div style={{ display: 'flex', flexWrap: 'wrap', gap: 9, color: MUTED, fontSize: 10 }}><span>{text(first(proposal.proposal_status, proposal.status))}</span><span>{text(proposal.requested_decision, '')}</span></div>
      </div>)}</div> : <div style={{ color: MUTED, fontSize: 12 }}>No proposals are currently awaiting attention.</div>}
    </Card>

    <Card label="Next" accent={BLUE}>
      <div style={{ display: 'grid', gap: 9 }}>
        <div style={{ fontSize: 13 }}>Review the live state above and choose what deserves attention.</div>
        <div style={{ color: MUTED, fontSize: 11 }}>Candidate actions are presented as context only. Nothing here authorizes execution or mutation.</div>
      </div>
    </Card>
  </div>;
}
