import React, { useEffect, useMemo, useState } from 'react';
import './interaction-canvas.css';
import {
  getSolariunPulse,
  getSolariunProposals,
  getSolariunSynthesis,
  getSolariunWorkEvents,
  getSolariunWorkload,
  getSolariunWorkspace,
  recordSolariunProposalDecision,
  type SolariunProposal,
  type SolariunWorkEvent,
} from '../../lib/solariunApi';
import {
  SolariunObjectSheet,
  type SolariunActionKind,
  type SolariunObject,
  type SolariunRelation,
  visualForObject,
} from './SolariunGrammar';

type Props = { onNavigate?: (target: string) => void };

type Snapshot = {
  workspace: any;
  pulse: any;
  workload: any;
  synthesis: any;
  proposals: SolariunProposal[];
  events: SolariunWorkEvent[];
  state: 'loading' | 'live' | 'partial' | 'unavailable';
};

const EMPTY: Snapshot = {
  workspace: null,
  pulse: null,
  workload: null,
  synthesis: null,
  proposals: [],
  events: [],
  state: 'loading',
};

function value(...items: unknown[]) {
  return items.find(item => item !== undefined && item !== null && String(item).trim() !== '') as string | number | undefined;
}

function text(item: unknown, fallback = 'UNKNOWN') {
  return item == null || String(item).trim() === '' ? fallback : String(item);
}

function dateLabel(value: unknown) {
  if (value == null) return '';
  const n = typeof value === 'number' ? (value < 10_000_000_000 ? value * 1000 : value) : Date.parse(String(value));
  return Number.isFinite(n) ? new Date(n).toLocaleString(undefined, { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' }) : '';
}

function proposalStatus(proposal: SolariunProposal) {
  return text(value(proposal.proposal_status, proposal.status), 'UNKNOWN').toUpperCase();
}

function proposalActionKinds(proposal: SolariunProposal): SolariunActionKind[] {
  const status = proposalStatus(proposal);
  if (['DRAFT', 'PRESENTED', 'UNDER_REVIEW', 'REVISION_REQUESTED', 'REVISED', 'DECISION_PENDING'].includes(status)) {
    return ['INSPECT', 'ASK', 'APPROVE', 'DECLINE'];
  }
  return ['INSPECT'];
}

export default function SolariunInteractionCanvas({ onNavigate }: Props) {
  const [snapshot, setSnapshot] = useState<Snapshot>(EMPTY);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [decisionBusy, setDecisionBusy] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);

  const read = async () => {
    setSnapshot(current => ({ ...current, state: 'loading' }));
    const results = await Promise.allSettled([
      getSolariunWorkspace(),
      getSolariunPulse(),
      getSolariunWorkload(),
      getSolariunSynthesis(),
      getSolariunProposals(20),
      getSolariunWorkEvents(10),
    ]);
    const [workspace, pulse, workload, synthesis, proposals, events] = results;
    const fulfilled = results.filter(result => result.status === 'fulfilled').length;
    setSnapshot({
      workspace: workspace.status === 'fulfilled' ? workspace.value.workspace ?? null : null,
      pulse: pulse.status === 'fulfilled' ? pulse.value.pulse ?? null : null,
      workload: workload.status === 'fulfilled' ? workload.value.workload ?? null : null,
      synthesis: synthesis.status === 'fulfilled' ? synthesis.value.synthesis ?? null : null,
      proposals: proposals.status === 'fulfilled' ? proposals.value.proposals ?? [] : [],
      events: events.status === 'fulfilled' ? (events.value.work_events ?? events.value.events ?? []) : [],
      state: fulfilled === 0 ? 'unavailable' : fulfilled < results.length ? 'partial' : 'live',
    });
  };

  useEffect(() => {
    let alive = true;
    void Promise.allSettled([
      getSolariunWorkspace(),
      getSolariunPulse(),
      getSolariunWorkload(),
      getSolariunSynthesis(),
      getSolariunProposals(20),
      getSolariunWorkEvents(10),
    ]).then(results => {
      if (!alive) return;
      const [workspace, pulse, workload, synthesis, proposals, events] = results;
      const fulfilled = results.filter(result => result.status === 'fulfilled').length;
      setSnapshot({
        workspace: workspace.status === 'fulfilled' ? workspace.value.workspace ?? null : null,
        pulse: pulse.status === 'fulfilled' ? pulse.value.pulse ?? null : null,
        workload: workload.status === 'fulfilled' ? workload.value.workload ?? null : null,
        synthesis: synthesis.status === 'fulfilled' ? synthesis.value.synthesis ?? null : null,
        proposals: proposals.status === 'fulfilled' ? proposals.value.proposals ?? [] : [],
        events: events.status === 'fulfilled' ? (events.value.work_events ?? events.value.events ?? []) : [],
        state: fulfilled === 0 ? 'unavailable' : fulfilled < results.length ? 'partial' : 'live',
      });
    });
    return () => { alive = false; };
  }, []);

  const objects = useMemo<SolariunObject[]>(() => {
    const rows: SolariunObject[] = [];
    const worldId = text(value(snapshot.workspace?.id, snapshot.workspace?.canonical_subject_ref), 'personal-field');

    if (snapshot.workspace) {
      rows.push({
        id: worldId,
        type: 'WORLD',
        title: text(value(snapshot.workspace.display_name, snapshot.workspace.workspace_type), 'Personal Field'),
        summary: 'The current authenticated operational world. The field is a projection of canonical state.',
        status: text(snapshot.workspace.lifecycle, 'ACTIVE').toUpperCase(),
        source: 'SolSpire workspace',
        visual: 'NODE',
        actionKinds: ['OPEN', 'ASK'],
      });
    }

    const attention = value(snapshot.pulse?.open_loops, snapshot.pulse?.open_loop_summary, snapshot.pulse?.loops);
    if (attention) {
      rows.push({
        id: 'signal:attention',
        type: 'SIGNAL',
        title: 'Attention',
        summary: text(attention),
        status: 'OPEN',
        source: 'Daily Pulse',
        visual: 'PANEL',
        actionKinds: ['INSPECT', 'ASK'],
      });
    }

    if (snapshot.workload) {
      rows.push({
        id: 'workload:current',
        type: 'WORK',
        title: text(value(snapshot.workload.title, snapshot.workload.display_name), 'Current Work'),
        summary: text(snapshot.workload.objective, 'No workload objective recorded.'),
        status: text(value(snapshot.workload.status, snapshot.workload.phase), 'UNKNOWN').toUpperCase(),
        source: 'Workload',
        visual: 'CARD',
        actionKinds: ['INSPECT', 'ASK'],
      });
    }

    if (snapshot.synthesis) {
      rows.push({
        id: 'synthesis:current',
        type: 'KNOWLEDGE',
        title: 'Current synthesis',
        summary: text(value(snapshot.synthesis.summary, snapshot.synthesis.synthesis_summary), 'No current synthesis recorded.'),
        status: 'CURRENT',
        source: 'Synthesis',
        updatedAt: value(snapshot.synthesis.updated_at, snapshot.synthesis.created_at),
        visual: 'SHEET',
        actionKinds: ['INSPECT', 'ASK'],
      });
    }

    snapshot.proposals.slice(0, 6).forEach((proposal, index) => {
      const id = text(proposal.proposal_id, `proposal:${index}`);
      rows.push({
        id,
        type: 'PROPOSAL',
        title: text(value(proposal.objective, proposal.requested_decision), 'Untitled proposal'),
        summary: 'Candidate action. Decision remains human-authoritative and does not itself authorize execution.',
        status: proposalStatus(proposal),
        source: 'Proposal substrate',
        visual: 'CONTROL',
        actionKinds: proposalActionKinds(proposal),
      });
    });

    snapshot.events.slice(0, 5).forEach((event, index) => {
      rows.push({
        id: text(value(event.work_event_id, event.id), `event:${index}`),
        type: 'EVENT',
        title: text(value(event.state_after_ref, event.work_ref, event.scope_ref), 'Recorded activity'),
        summary: text(value(event.event_type, event.type), 'WORK_EVENT'),
        status: 'RECORDED',
        source: 'WorkEvent',
        updatedAt: value(event.occurred_at, event.created_at),
        visual: 'TIMELINE',
        actionKinds: ['INSPECT'],
      });
    });
    return rows;
  }, [snapshot]);

  const relations = useMemo<SolariunRelation[]>(() => {
    const out: SolariunRelation[] = [];
    const world = objects.find(o => o.type === 'WORLD');
    if (!world) return out;
    objects.filter(o => o.id !== world.id).forEach(object => {
      out.push({ type: object.type === 'EVENT' ? 'REFERENCES' : 'BELONGS TO', sourceId: object.id, targetId: world.id });
    });
    const attention = objects.find(o => o.id === 'signal:attention');
    const work = objects.find(o => o.id === 'workload:current');
    if (attention && work) out.push({ type: 'FOLLOW-UP FOR', sourceId: attention.id, targetId: work.id });
    return out;
  }, [objects]);

  const selected = objects.find(object => object.id === selectedId) ?? null;
  const selectedRelations = selected ? relations.filter(r => r.sourceId === selected.id || r.targetId === selected.id) : [];
  const openProposals = snapshot.proposals.filter(p => proposalActionKinds(p).includes('APPROVE'));

  async function act(object: SolariunObject, kind: SolariunActionKind) {
    setNotice(null);
    if (kind === 'ASK') {
      onNavigate?.('commune');
      return;
    }
    if (kind === 'OPEN' || kind === 'INSPECT') {
      setSelectedId(object.id);
      return;
    }
    if (object.type !== 'PROPOSAL') return;
    const proposal = snapshot.proposals.find(item => text(item.proposal_id) === object.id);
    if (!proposal?.proposal_id) return;
    if (kind === 'APPROVE' || kind === 'DECLINE' || kind === 'WITHDRAW') {
      const decision = kind === 'APPROVE' ? 'ACCEPTED' : kind === 'DECLINE' ? 'DECLINED' : 'WITHDRAWN';
      setDecisionBusy(`${proposal.proposal_id}:${decision}`);
      try {
        const result = await recordSolariunProposalDecision(String(proposal.proposal_id), decision);
        const updated = result.proposal ?? { ...proposal, proposal_status: decision };
        setSnapshot(current => ({
          ...current,
          proposals: current.proposals.map(item => item.proposal_id === proposal.proposal_id ? { ...item, ...updated } : item),
        }));
        setNotice(`${decision} recorded. This does not authorize execution.`);
      } catch (error) {
        setNotice(error instanceof Error ? error.message : 'Decision could not be recorded.');
      } finally {
        setDecisionBusy(null);
      }
    }
  }

  const statusLabel = snapshot.state === 'live' ? 'LIVE' : snapshot.state === 'partial' ? 'PARTIAL' : snapshot.state === 'loading' ? 'READING' : 'UNAVAILABLE';

  return (
    <div className="living-canvas" data-testid="solariun-living-canvas" data-solariun-grammar="living-canvas">
      <header className="living-canvas-header">
        <div>
          <div className="canvas-eyebrow">SOLARIUN / FIELD</div>
          <h1>Your field.</h1>
          <p>One living projection of the things that exist, the things that changed, and the things that require you.</p>
        </div>
        <div className="living-canvas-status">
          <span className={`canvas-live-dot ${snapshot.state}`}><i />{statusLabel}</span>
          <button type="button" onClick={() => void read()} aria-label="Refresh Solariun field">↻</button>
        </div>
      </header>

      <div className="living-canvas-modes" role="tablist" aria-label="Solariun field depth">
        <span className="active">FIELD <small>What matters?</small></span>
        <span>FOCUS <small>Select an object</small></span>
        <span>DEEP <small>Inspect provenance</small></span>
      </div>

      <section className="living-field" aria-label="Living semantic field">
        <div className="field-orbit field-orbit-a" />
        <div className="field-orbit field-orbit-b" />
        {objects.map((object, index) => {
          const selectedState = selectedId === object.id;
          const offset = index - Math.floor(objects.length / 2);
          const visual = object.visual ?? visualForObject(object.type, object.status);
          const className = `field-object field-object-${visual.toLowerCase()} ${selectedState ? 'is-selected' : ''}`;
          return (
            <button
              type="button"
              key={object.id}
              className={className}
              style={{ '--field-offset': offset, '--field-index': index } as React.CSSProperties}
              onClick={() => setSelectedId(object.id)}
              aria-pressed={selectedState}
              data-solariun-object-type={object.type}
              data-solariun-visual={visual}
            >
              <span className="field-object-type">{object.type}</span>
              <strong>{object.title}</strong>
              <small>{object.status || 'UNKNOWN'}</small>
              {object.type === 'PROPOSAL' && <span className="field-object-action-mark">●</span>}
            </button>
          );
        })}
        {!objects.length && snapshot.state !== 'loading' ? (
          <div className="living-field-empty">
            <span>FIELD / EMPTY</span>
            <strong>No canonical objects are currently available.</strong>
            <p>Nothing has been substituted for unavailable state.</p>
          </div>
        ) : null}
      </section>

      <section className="living-canvas-strip">
        <div>
          <span className="canvas-label">CURRENT SIGNAL</span>
          <strong>{text(value(snapshot.pulse?.current_signal, snapshot.pulse?.signal, snapshot.pulse?.signal_summary), 'No current signal recorded.')}</strong>
        </div>
        <div className="living-canvas-metrics">
          <span><b>{objects.filter(o => o.type === 'WORK').length}</b> work</span>
          <span><b>{openProposals.length}</b> decisions</span>
          <span><b>{snapshot.events.length}</b> recent events</span>
        </div>
      </section>

      {notice ? <div className="living-canvas-notice" role="status">{notice}</div> : null}

      {selected ? (
        <SolariunObjectSheet
          object={selected}
          relationships={selectedRelations}
          activity={snapshot.events.slice(0, 6).map(event => ({
            type: text(value(event.event_type, event.type), 'EVENT'),
            title: text(value(event.state_after_ref, event.work_ref, event.scope_ref), 'Recorded activity'),
            time: dateLabel(value(event.occurred_at, event.created_at)),
            id: text(value(event.work_event_id, event.id), ''),
          }))}
          sourceNote={selected.source}
          actions={
            <div className="living-sheet-actions">
              {(selected.actionKinds ?? []).map(kind => {
                const proposalId = selected.type === 'PROPOSAL' ? selected.id : null;
                const busy = proposalId && decisionBusy?.startsWith(proposalId);
                return (
                  <button
                    key={kind}
                    type="button"
                    disabled={Boolean(busy)}
                    onClick={() => void act(selected, kind)}
                    data-action={kind}
                  >
                    {busy ? 'Recording…' : kind}
                  </button>
                );
              })}
            </div>
          }
          onClose={() => setSelectedId(null)}
        />
      ) : null}

      <footer className="living-canvas-footer">
        <span>CAN ≠ MAY ≠ DID</span>
        <span>Display does not authorize execution.</span>
        <button type="button" onClick={() => onNavigate?.('commune')}>Ask Arkana about this field ↗</button>
      </footer>
    </div>
  );
}
