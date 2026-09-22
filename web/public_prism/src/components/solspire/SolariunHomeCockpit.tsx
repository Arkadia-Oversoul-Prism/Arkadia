import React, { useEffect, useMemo, useState } from 'react';
import {
  emitSolariunWorkEvent,
  getSolariunPulse,
  getSolariunProposals,
  getSolariunSynthesis,
  getSolariunWorkEvents,
  getSolariunWorkload,
  recordSolariunProposalDecision,
  SolariunPulse,
  SolariunProposal,
  SolariunSynthesis,
  SolariunWorkEvent,
  SolariunWorkload,
} from '../../lib/solariunApi';
import { useAuth } from '../../contexts/AuthContext';
import { getPersonalField, PersonalField } from '../../lib/knowledgeApi';

const GOLD = '#C9A84C';
const TEAL = '#00D4AA';
const BLUE = '#6A9FD8';
const VIOLET = '#B08DE8';
const MUTED = 'rgba(232,232,232,.54)';
const BORDER = 'rgba(255,255,255,.075)';

function first<T>(...values: Array<T | undefined | null | ''>): T | undefined {
  return values.find(value => value !== undefined && value !== null && value !== '') as T | undefined;
}

function text(value: unknown, fallback = 'No signal recorded.') {
  return typeof value === 'string' ? value : value == null ? fallback : String(value);
}

function dateLabel(value: string | number | undefined) {
  if (value == null) return '';
  const numeric = typeof value === 'number' ? (value < 10_000_000_000 ? value * 1000 : value) : Date.parse(value);
  if (!Number.isFinite(numeric)) return '';
  return new Date(numeric).toLocaleString(undefined, { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' });
}

type SurfaceState = 'LOADING' | 'LIVE' | 'EMPTY' | 'UNAVAILABLE' | 'FAILED';

type SurfaceStatus = {
  state: SurfaceState;
  detail?: string;
};

function errorStatus(error: unknown, notFoundMeansEmpty = false): SurfaceStatus {
  const detail = error instanceof Error ? error.message : String(error);
  const match = detail.match(/\\b(4\\d\\d|5\\d\\d)\\b/);
  const code = match ? Number(match[1]) : null;
  if (code === 404 && notFoundMeansEmpty) return { state: 'EMPTY', detail };
  if (code === 409) return { state: 'UNAVAILABLE', detail };
  return { state: 'FAILED', detail };
}

function stateLabel(status: SurfaceStatus) {
  return status.state;
}

function FieldSection({ label, accent = GOLD, children }: { label: string; accent?: string; children: React.ReactNode }) {
  return (
    <section className="solariun-field-section" style={{ borderTop: `1px solid ${BORDER}`, paddingTop: 14 }}>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 12, marginBottom: 10 }}>
        <span style={{ color: `${accent}aa`, font: '600 8px/1.2 Inter,system-ui,sans-serif', letterSpacing: '.2em', textTransform: 'uppercase' }}>{label}</span>
        <span aria-hidden="true" style={{ width: 5, height: 5, borderRadius: '50%', background: accent, opacity: .7 }} />
      </div>
      {children}
    </section>
  );
}

function StateObject({ label, title, body, accent = GOLD, meta }: { label: string; title: string; body?: string; accent?: string; meta?: string }) {
  return (
    <article className="solspire-object" data-solariun-grammar="object" style={{ padding: 16 }}>
      <div className="solspire-kicker" style={{ color: `${accent}aa` }}>{label}</div>
      <h3 className="solspire-title" style={{ margin: '7px 0 0' }}>{title}</h3>
      {body ? <p className="solspire-object-summary" style={{ margin: '7px 0 0' }}>{body}</p> : null}
      {meta ? <div className="solspire-object-meta" style={{ marginTop: 11 }}>{meta}</div> : null}
    </article>
  );
}

export default function SolariunHomeCockpit() {
  const { codex } = useAuth();
  const [pulse, setPulse] = useState<SolariunPulse | null>(null);
  const [workload, setWorkload] = useState<SolariunWorkload | null>(null);
  const [events, setEvents] = useState<SolariunWorkEvent[]>([]);
  const [synthesis, setSynthesis] = useState<SolariunSynthesis | null>(null);
  const [proposals, setProposals] = useState<SolariunProposal[]>([]);
  const [personalField, setPersonalField] = useState<PersonalField | null>(null);
  const [loading, setLoading] = useState(true);
  const [surfaceStatus, setSurfaceStatus] = useState<Record<'pulse' | 'workload' | 'events' | 'synthesis' | 'proposals', SurfaceStatus>>({
    pulse: { state: 'LOADING' },
    workload: { state: 'LOADING' },
    events: { state: 'LOADING' },
    synthesis: { state: 'LOADING' },
    proposals: { state: 'LOADING' },
  });
  const [failureCount, setFailureCount] = useState(0);
  const [decisionBusy, setDecisionBusy] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);

  useEffect(() => {
    let alive = true;
    Promise.allSettled([
      getSolariunPulse(),
      getSolariunWorkload(),
      getSolariunWorkEvents(),
      getSolariunSynthesis(),
      getSolariunProposals(),
      getPersonalField(),
    ]).then(results => {
      if (!alive) return;
      const failures = results.filter(result => result.status === 'rejected').length;
      const nextStatus = {
        pulse: results[0].status === 'fulfilled'
          ? (results[0].value.pulse ? { state: 'LIVE' as const } : { state: 'EMPTY' as const })
          : errorStatus(results[0].reason, true),
        workload: results[1].status === 'fulfilled'
          ? (results[1].value.workload ? { state: 'LIVE' as const } : { state: 'EMPTY' as const })
          : errorStatus(results[1].reason, true),
        events: results[2].status === 'fulfilled'
          ? ((first(results[2].value.work_events, results[2].value.events) ?? []).length ? { state: 'LIVE' as const } : { state: 'EMPTY' as const })
          : errorStatus(results[2].reason),
        synthesis: results[3].status === 'fulfilled'
          ? (results[3].value.synthesis ? { state: 'LIVE' as const } : { state: 'EMPTY' as const })
          : errorStatus(results[3].reason, true),
        proposals: results[4].status === 'fulfilled'
          ? ((results[4].value.proposals ?? []).length ? { state: 'LIVE' as const } : { state: 'EMPTY' as const })
          : errorStatus(results[4].reason),
      };
      if (results[0].status === 'fulfilled') setPulse(results[0].value.pulse ?? null);
      if (results[1].status === 'fulfilled') setWorkload(results[1].value.workload ?? null);
      if (results[2].status === 'fulfilled') setEvents(first(results[2].value.work_events, results[2].value.events) ?? []);
      if (results[3].status === 'fulfilled') setSynthesis(results[3].value.synthesis ?? null);
      if (results[4].status === 'fulfilled') setProposals(results[4].value.proposals ?? []);
      if (results[5].status === 'fulfilled') setPersonalField(results[5].value);
      setSurfaceStatus(nextStatus);
      setFailureCount(failures);
      setLoading(false);
    });
    return () => { alive = false; };
  }, []);

  const openProposals = useMemo(() => proposals.filter(proposal => {
    const status = String(proposal.proposal_status ?? proposal.status ?? '').toUpperCase();
    return ['DRAFT', 'PRESENTED', 'UNDER_REVIEW', 'REVISION_REQUESTED', 'REVISED', 'DECISION_PENDING'].includes(status);
  }), [proposals]);

  async function decide(proposal: SolariunProposal, decision: 'ACCEPTED' | 'DECLINED' | 'WITHDRAWN') {
    const proposalId = String(proposal.proposal_id || '');
    if (!proposalId) return;
    setDecisionBusy(`${proposalId}:${decision}`);
    setNotice(null);
    try {
      const result = await recordSolariunProposalDecision(proposalId, decision);
      const updated = result.proposal ?? { ...proposal, proposal_status: decision };
      setProposals(current => current.map(item => item.proposal_id === proposalId ? { ...item, ...updated } : item));
      try {
        await emitSolariunWorkEvent({
          event_type: 'PROPOSAL_DECISION',
          work_ref: proposalId,
          scope_ref: proposalId,
          decision_ref: updated.decision_ref ? String(updated.decision_ref) : proposalId,
          state_after_ref: decision,
        });
      } catch {
        // Decision remains authoritative; continuity emission is best-effort.
      }
      setNotice(`${decision} recorded. This does not authorize execution.`);
    } catch (error) {
      setNotice(error instanceof Error ? error.message : 'Decision could not be recorded.');
    } finally {
      setDecisionBusy(null);
    }
  }

  const pulseData = pulse ?? {};
  const workloadData = workload ?? {};
  const synthesisData = synthesis ?? {};
  const activeWorkTitle = text(first(workloadData.title, workloadData.display_name), 'No active workload recorded.');
  const activeWorkBody = text(workloadData.objective, 'No workload objective recorded.');
  const attention = first(pulseData.open_loops, pulseData.open_loop_summary, pulseData.loops);

  return (
    <div
      data-solariun-field="overview"
      data-solariun-grammar="field-composition"
      aria-label="Solariun field: what matters now"
      style={{ display: 'grid', gap: 24, width: '100%' }}
    >
      <header style={{ padding: '10px 2px 6px' }}>
        <div style={{ color: `${TEAL}aa`, font: '600 8px/1.2 Inter,system-ui,sans-serif', letterSpacing: '.24em', textTransform: 'uppercase' }}>SOLARIUN / FIELD</div>
        <h2 style={{ margin: '9px 0 7px', font: '500 clamp(34px,5vw,58px)/1.02 Georgia,"Times New Roman",serif', color: '#E9E7DF' }}>What matters now?</h2>
        <p style={{ margin: 0, maxWidth: 720, color: MUTED, font: '13px/1.65 Inter,system-ui,sans-serif' }}>
          The field composes live workspace state. Values below are rendered only when the existing substrate returns them.
        </p>
      </header>

      {loading ? (
        <FieldSection label="Field state" accent={TEAL}><div style={{ color: MUTED, fontSize: 12 }}>Reading existing Solariun state…</div></FieldSection>
      ) : null}

      {!loading ? (
        <div role="status" style={{ color: MUTED, font: '10px/1.5 Inter,system-ui,sans-serif', padding: '9px 0', letterSpacing: '.03em' }}>
          Live-state diagnostics · {Object.values(surfaceStatus).map(status => stateLabel(status)).join(' · ')}
          {failureCount > 0 ? ' · No placeholder state has been substituted.' : ''}
        </div>
      ) : null}

      <FieldSection label="Identity context" accent={VIOLET}>
        {codex ? (
          <StateObject
            label="PERSONAL CODEX"
            title={text(codex.display_name, 'Authenticated node')}
            body={text(codex.soul_function, 'No soul function recorded.')}
            accent={VIOLET}
            meta={text(codex.role, 'ROLE UNAVAILABLE')}
          />
        ) : (
          <div style={{ color: MUTED, fontSize: 12 }}>Personal Codex unavailable for the current authenticated node.</div>
        )}
      </FieldSection>

      <FieldSection label="Personal field" accent={VIOLET}>
        {personalField ? (
          <div style={{ display: 'grid', gap: 10 }}>
            <div style={{ color: '#E9E7DF', font: '500 17px/1.45 Georgia,serif' }}>
              {text(personalField.identity?.display_name, 'Authenticated node')}'s field is connected.
            </div>
            <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
              <span className="solspire-relation">PROJECTS · {personalField.solspire_projects?.length ?? 0}</span>
              <span className="solspire-relation">NOTES · {personalField.notes?.length ?? 0}</span>
              <span className="solspire-relation">GRAPH · {personalField.graph?.nodes?.length ?? 0}</span>
              <span className="solspire-relation">TIMELINE · {personalField.timeline?.length ?? 0}</span>
            </div>
            {personalField.graph?.nodes?.[0] ? (
              <div style={{ color: MUTED, font: '11px/1.5 Inter,system-ui,sans-serif' }}>
                Latest knowledge node: {text(personalField.graph.nodes[0].title, 'Untitled node')}
              </div>
            ) : (
              <div style={{ color: MUTED, font: '11px/1.5 Inter,system-ui,sans-serif' }}>
                No knowledge nodes are currently recorded in the personal field.
              </div>
            )}
          </div>
        ) : (
          <div style={{ color: MUTED, fontSize: 12 }}>Personal field unavailable for the current authenticated node.</div>
        )}
      </FieldSection>

      <FieldSection label="Attention" accent={TEAL}>
        {attention ? (
          <StateObject label="OPEN LOOP" title={text(attention)} accent={TEAL} />
        ) : (
          <div style={{ color: MUTED, fontSize: 12 }}>No open-loop state is currently recorded.</div>
        )}
      </FieldSection>

      <FieldSection label="Active world" accent={GOLD}>
        {workload ? (
          <div style={{ display: 'grid', gap: 12 }}>
            <StateObject
              label={text(first(workloadData.workload_type, workloadData.phase), 'WORKLOAD')}
              title={activeWorkTitle}
              body={activeWorkBody}
              accent={GOLD}
              meta={[first(workloadData.status), first(workloadData.updated_at, workloadData.created_at)].filter(Boolean).map(value => String(value)).join(' · ')}
            />
            <div style={{ color: MUTED, font: '10px/1.5 ui-monospace,SFMono-Regular,monospace' }}>
              Workspace context is supplied by the existing workload substrate. No project identity is inferred here.
            </div>
          </div>
        ) : (
          <div style={{ color: MUTED, fontSize: 12 }}>
            {surfaceStatus.workload.state === 'EMPTY' ? 'No active workload is currently recorded.' :
             surfaceStatus.workload.state === 'UNAVAILABLE' ? 'Canonical workspace is unavailable for the workload surface.' :
             surfaceStatus.workload.state === 'FAILED' ? 'Workload surface failed to respond.' :
             'Workload surface is not currently available.'}
          </div>
        )}
      </FieldSection>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit,minmax(min(100%,300px),1fr))', gap: 20 }}>
        <FieldSection label="Current signal" accent={GOLD}>
          <div style={{ color: '#E9E7DF', font: '500 18px/1.45 Georgia,serif' }}>
            {surfaceStatus.pulse.state === 'LIVE'
              ? text(first(pulseData.current_signal, pulseData.signal, pulseData.signal_summary), 'No current signal recorded.')
              : surfaceStatus.pulse.state === 'EMPTY'
                ? 'No current signal recorded.'
                : surfaceStatus.pulse.state === 'UNAVAILABLE'
                  ? 'Pulse surface unavailable for the current workspace.'
                  : 'Pulse surface failed to respond.'}
          </div>
        </FieldSection>
        <FieldSection label="Continuity" accent={BLUE}>
          {events.length ? (
            <div className="solariun-activity-stream">
              {events.slice(0, 6).map((event, index) => (
                <div key={String(first(event.work_event_id, event.id, index))} className="solspire-activity-item">
                  <span className="solspire-activity-dot" />
                  <div>
                    <div className="solspire-kicker">{text(first(event.event_type, event.type), 'EVENT')}</div>
                    <div className="solspire-activity-title">{text(first(event.state_after_ref, event.work_ref, event.scope_ref), 'Recorded activity')}</div>
                  </div>
                  <div className="solspire-activity-time">{dateLabel(first(event.occurred_at, event.created_at))}</div>
                </div>
              ))}
            </div>
          ) : (
            <div style={{ color: MUTED, fontSize: 12 }}>
              {surfaceStatus.events.state === 'EMPTY' ? 'No recent activity events are currently recorded.' :
               surfaceStatus.events.state === 'UNAVAILABLE' ? 'WorkEvent surface unavailable for the current workspace.' :
               surfaceStatus.events.state === 'FAILED' ? 'WorkEvent surface failed to respond.' :
               'WorkEvent surface is not currently available.'}
            </div>
          )}
        </FieldSection>
      </div>

      <FieldSection label="Synthesis" accent={VIOLET}>
        <div style={{ color: '#E9E7DF', font: '500 20px/1.45 Georgia,serif' }}>
          {surfaceStatus.synthesis.state === 'LIVE'
            ? text(first(synthesisData.summary, synthesisData.synthesis_summary), 'No current synthesis recorded.')
            : surfaceStatus.synthesis.state === 'EMPTY'
              ? 'No current synthesis recorded.'
              : surfaceStatus.synthesis.state === 'UNAVAILABLE'
                ? 'Synthesis surface unavailable for the current workspace.'
                : 'Synthesis surface failed to respond.'}
        </div>
        {first(synthesisData.created_at, synthesisData.updated_at) ? (
          <div style={{ marginTop: 8, color: MUTED, font: '9px ui-monospace,SFMono-Regular,monospace' }}>{dateLabel(first(synthesisData.created_at, synthesisData.updated_at))}</div>
        ) : null}
      </FieldSection>

      <FieldSection label="Decisions" accent={GOLD}>
        {openProposals.length ? (
          <div style={{ display: 'grid', gap: 12 }}>
            {openProposals.slice(0, 5).map(proposal => {
              const proposalId = String(proposal.proposal_id || '');
              const status = text(first(proposal.proposal_status, proposal.status), 'DECISION_PENDING');
              return (
                <article key={proposalId} className="solspire-object" style={{ padding: 15 }}>
                  <div className="solspire-kicker">PROPOSAL · {status}</div>
                  <h3 className="solspire-title">{text(first(proposal.objective, proposal.requested_decision), 'Untitled proposal')}</h3>
                  <div className="solspire-object-actions" style={{ marginTop: 10 }}>
                    {(['ACCEPTED', 'DECLINED', 'WITHDRAWN'] as const).map(decision => (
                      <button
                        key={decision}
                        type="button"
                        disabled={Boolean(decisionBusy)}
                        onClick={() => void decide(proposal, decision)}
                        style={{ border: `1px solid ${BORDER}`, borderRadius: 4, padding: '6px 9px', background: 'rgba(255,255,255,.025)', color: GOLD, font: '8px ui-monospace,SFMono-Regular,monospace', letterSpacing: '.08em', cursor: decisionBusy ? 'wait' : 'pointer' }}
                      >
                        {decisionBusy === `${proposalId}:${decision}` ? 'Recording…' : decision}
                      </button>
                    ))}
                  </div>
                </article>
              );
            })}
          </div>
        ) : (
          <div style={{ color: MUTED, fontSize: 12 }}>
            {surfaceStatus.proposals.state === 'EMPTY' ? 'No proposals are currently awaiting attention.' :
             surfaceStatus.proposals.state === 'UNAVAILABLE' ? 'Proposal surface unavailable for the current workspace.' :
             surfaceStatus.proposals.state === 'FAILED' ? 'Proposal surface failed to respond.' :
             'Proposal surface is not currently available.'}
          </div>
        )}
        {notice ? <div role="status" style={{ marginTop: 10, color: MUTED, fontSize: 11 }}>{notice}</div> : null}
      </FieldSection>
    </div>
  );
}
