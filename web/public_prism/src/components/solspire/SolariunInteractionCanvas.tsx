import React, { useEffect, useState } from 'react';
import { getSolariunPulse, getSolariunWorkload } from '../../lib/solariunApi';

type Props = { onNavigate?: (target: string) => void };

type Snapshot = {
  pulse?: any;
  workload?: any;
  state: 'loading' | 'live' | 'unavailable';
};

const actions = [
  { id: 'commune', label: 'Ask Arkana', note: 'Start or continue a conversation', icon: '✦' },
  { id: 'projects', label: 'Projects', note: 'Open the work you are building', icon: '◈' },
  { id: 'knowledge', label: 'Knowledge', note: 'Find what you have kept', icon: '⌘' },
  { id: 'files', label: 'Files', note: 'Browse project material', icon: '□' },
  { id: 'tasks', label: 'Tasks', note: 'See what needs attention', icon: '✓' },
  { id: 'engineering-lab', label: 'Engineering Lab', note: 'See how Arkadia is doing', icon: '⌬' },
];

function value(...items: unknown[]) {
  return items.find(item => item !== undefined && item !== null && String(item).trim() !== '') as string | number | undefined;
}

export default function SolariunInteractionCanvas({ onNavigate }: Props) {
  const [snapshot, setSnapshot] = useState<Snapshot>({ state: 'loading' });

  useEffect(() => {
    let alive = true;
    Promise.allSettled([getSolariunPulse(), getSolariunWorkload()]).then(results => {
      if (!alive) return;
      const pulse = results[0].status === 'fulfilled' ? results[0].value.pulse : null;
      const workload = results[1].status === 'fulfilled' ? results[1].value.workload : null;
      setSnapshot({
        pulse,
        workload,
        state: results.some(result => result.status === 'fulfilled') ? 'live' : 'unavailable',
      });
    });
    return () => { alive = false; };
  }, []);

  const workloadTitle = String(value(snapshot.workload?.title, snapshot.workload?.display_name) || 'No active project');
  const attention = value(snapshot.pulse?.open_loops, snapshot.pulse?.open_loop_summary, snapshot.pulse?.loops);

  return (
    <div className="interaction-canvas" data-testid="solariun-interaction-canvas">
      <section className="canvas-welcome">
        <div>
          <span className="canvas-eyebrow">SOLARIUN</span>
          <h1>What are you doing?</h1>
          <p>Your workspace, without the maze. Pick a direction and keep moving.</p>
        </div>
        <span className={`canvas-live-dot ${snapshot.state}`}>
          <i /> {snapshot.state === 'loading' ? 'Reading' : snapshot.state === 'live' ? 'Live' : 'Unavailable'}
        </span>
      </section>

      <section className="canvas-focus" aria-label="Current focus">
        <div>
          <span className="canvas-label">CURRENT FOCUS</span>
          <strong>{workloadTitle}</strong>
          <p>{attention ? String(attention) : 'Nothing is asking for attention right now.'}</p>
        </div>
        <button type="button" onClick={() => onNavigate?.('commune')}>Talk to Arkana <span>→</span></button>
      </section>

      <section className="canvas-grid" aria-label="Solariun actions">
        {actions.map(action => (
          <button key={action.id} type="button" className={`canvas-action canvas-action-${action.id}`} onClick={() => onNavigate?.(action.id)}>
            <span className="canvas-action-icon">{action.icon}</span>
            <span className="canvas-action-copy">
              <strong>{action.label}</strong>
              <small>{action.note}</small>
            </span>
            <span className="canvas-arrow">↗</span>
          </button>
        ))}
      </section>

      <section className="canvas-footer">
        <span>Solariun is your personal workspace.</span>
        <button type="button" onClick={() => onNavigate?.('solspire')}>Open SolSpire <span>→</span></button>
      </section>
    </div>
  );
}
