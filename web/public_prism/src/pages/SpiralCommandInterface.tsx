/**
 * Spiral Command Interface (SCI) - MVP2-08 foundation
 *
 * Operator discovery shell. Routes to existing surfaces.
 * Does NOT own authorization, mutation, PassSpec, PatchApproval, K15, or K3.
 * SCI_DISCOVERY_WITHOUT_AUTHORITY
 *
 * WEAVER-SCI-BOUNDARY-01: SCI owns global operator command navigation only.
 * SolSpire owns project/workspace context. Weaver lives under project scope.
 * SCI must not implement PassSpec, PatchApproval, K15, or K3.
 */
import React, { useState } from 'react';
import {
  SCI_CATEGORIES,
  SCI_COMMANDS,
  WEAVER_LIFECYCLE,
  WEAVER_STATE_LABELS,
  commandsForDomain,
  type SciDomain,
  type SciCommand,
} from '../lib/sciCommandRegistry';

type Navigate = (view: string) => void;

const C = {
  gold: '#C9A84C',
  teal: '#00D4AA',
  blue: '#6A9FD8',
  purple: '#B08DE8',
  red: '#C84848',
  text: 'rgba(232,232,232,0.88)',
  muted: 'rgba(232,232,232,0.5)',
  dim: 'rgba(232,232,232,0.28)',
  card: 'rgba(14,17,32,0.72)',
  border: 'rgba(0,212,170,0.12)',
};

function Badge({ label, color }: { label: string; color: string }) {
  return (
    <span
      style={{
        fontFamily: 'ui-monospace, monospace',
        fontSize: 9,
        letterSpacing: '0.12em',
        textTransform: 'uppercase',
        color,
        border: `1px solid ${color}55`,
        background: `${color}12`,
        padding: '2px 8px',
        borderRadius: 4,
      }}
    >
      {label}
    </span>
  );
}

function availabilityColor(a: string): string {
  if (a === 'AVAILABLE') return C.teal;
  if (a === 'LIMITED') return C.gold;
  if (a === 'DISABLED' || a === 'PROPOSAL_ONLY') return C.red;
  return C.dim;
}

function CommandCard({ cmd, onNavigate }: { cmd: SciCommand; onNavigate: Navigate }) {
  return (
    <div
      data-testid={`sci-command-${cmd.id}`}
      style={{
        padding: '14px 16px',
        background: C.card,
        border: `1px solid ${C.border}`,
        borderRadius: 10,
        marginBottom: 10,
      }}
    >
      <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 8, flexWrap: 'wrap' }}>
        <p style={{ margin: 0, fontFamily: 'sans-serif', fontSize: 13, color: C.text, fontWeight: 600 }}>
          {cmd.label}
        </p>
        <Badge label={cmd.availability} color={availabilityColor(cmd.availability)} />
        <Badge label={cmd.authority} color={C.blue} />
        {cmd.mutation && <Badge label="MUTATION" color={C.gold} />}
      </div>
      <p style={{ margin: '0 0 8px', fontSize: 12, color: C.muted, lineHeight: 1.5 }}>{cmd.description}</p>
      {cmd.notes && (
        <p style={{ margin: '0 0 10px', fontSize: 11, color: C.dim, lineHeight: 1.45 }}>{cmd.notes}</p>
      )}
      {cmd.routeView && (
        <button
          type="button"
          data-testid={`sci-open-${cmd.id}`}
          onClick={() => onNavigate(cmd.routeView!)}
          style={{
            padding: '8px 14px',
            background: 'rgba(0,212,170,0.08)',
            border: '1px solid rgba(0,212,170,0.35)',
            borderRadius: 8,
            color: C.teal,
            fontFamily: 'sans-serif',
            fontSize: 10,
            letterSpacing: '0.14em',
            textTransform: 'uppercase',
            cursor: 'pointer',
          }}
        >
          Open existing surface
        </button>
      )}
      {!cmd.routeView && cmd.availability !== 'AVAILABLE' && (
        <p
          data-testid={`sci-na-${cmd.id}`}
          style={{ margin: 0, fontSize: 10, letterSpacing: '0.12em', color: C.dim, textTransform: 'uppercase' }}
        >
          {cmd.availability} - metadata only - no parallel implementation
        </p>
      )}
    </div>
  );
}

function OverviewPanel() {
  return (
    <div data-testid="sci-panel-overview">
      <h2 style={{ fontFamily: 'serif', fontSize: 22, color: C.gold, margin: '0 0 8px' }}>Spiral Command Interface</h2>
      <p style={{ fontSize: 12, color: C.muted, margin: '0 0 18px', lineHeight: 1.6 }}>
        Developer/operator discovery shell. Navigation is not authorization. Capability metadata is not authority.
        Backend governance remains authoritative.
      </p>
      <pre
        data-testid="sci-system-map"
        style={{
          fontFamily: 'ui-monospace, monospace',
          fontSize: 11,
          color: 'rgba(212,223,232,0.55)',
          background: 'rgba(0,0,0,0.25)',
          border: `1px solid ${C.border}`,
          borderRadius: 10,
          padding: 16,
          overflow: 'auto',
          lineHeight: 1.55,
          margin: 0,
        }}
      >{`SCI (global operator shell)
        |
   +----+----+----+
   |    |    |    |
PROJECTS KNOWLEDGE SYSTEM
   |
SOLSPIRE (project workspace)
   |
   +-- Knowledge (project)
   +-- Weaver (project-scoped)
   +-- Tasks / objectives
          |
      GOVERNANCE
          |
       K15 -> K3
          |
      VERIFICATION

SCI routes to existing surfaces only.
SolSpire owns project context. Weaver is project-scoped.
No SCI -> K3. No autonomous mutation.
SCI_DISCOVERY_WITHOUT_AUTHORITY`}</pre>
      <p style={{ marginTop: 16, fontSize: 11, color: C.dim }}>
        Invariant: <code style={{ color: C.teal }}>SCI_DISCOVERY_WITHOUT_AUTHORITY</code>
      </p>
    </div>
  );
}

function WeaverPanel({ onNavigate }: { onNavigate: Navigate }) {
  const cmds = commandsForDomain('weaver');
  return (
    <div data-testid="sci-panel-weaver">
      <h2 style={{ fontFamily: 'serif', fontSize: 20, color: C.teal, margin: '0 0 6px' }}>Weaver</h2>
      <p style={{ fontSize: 12, color: C.muted, margin: '0 0 14px', lineHeight: 1.55 }}>
        Lifecycle is displayed for operator orientation. Execution requires PassSpec + PatchApproval + K15.
        SCI does not call K3 or run_transaction. Weaver workbench lives under SolSpire project context.
      </p>
      <div style={{ marginBottom: 16 }}>
        <p style={{ fontSize: 9, letterSpacing: '0.2em', textTransform: 'uppercase', color: C.dim, margin: '0 0 8px' }}>
          Lifecycle chain
        </p>
        <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6 }} data-testid="sci-weaver-lifecycle">
          {WEAVER_LIFECYCLE.map((stage) => (
            <Badge key={stage} label={stage} color={C.blue} />
          ))}
        </div>
      </div>
      <div style={{ marginBottom: 16 }}>
        <p style={{ fontSize: 9, letterSpacing: '0.2em', textTransform: 'uppercase', color: C.dim, margin: '0 0 8px' }}>
          Allowed state vocabulary
        </p>
        <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6 }} data-testid="sci-weaver-states">
          {WEAVER_STATE_LABELS.map((s) => (
            <Badge key={s} label={s} color={s === 'LOCKED' || s === 'NOT_AVAILABLE' ? C.red : C.gold} />
          ))}
        </div>
      </div>
      {cmds.map((c) => (
        <CommandCard key={c.id} cmd={c} onNavigate={onNavigate} />
      ))}
      <p style={{ fontSize: 11, color: C.dim, marginTop: 8 }}>
        Open SolSpire, select a project, then Weaver tab for the existing WeaverPanel binding.
      </p>
    </div>
  );
}

function DomainPanel({ domain, onNavigate }: { domain: SciDomain; onNavigate: Navigate }) {
  if (domain === 'command') return <OverviewPanel />;
  if (domain === 'weaver') return <WeaverPanel onNavigate={onNavigate} />;
  const cmds = commandsForDomain(domain);
  const title = SCI_CATEGORIES.find((c) => c.id === domain)?.label ?? domain;
  return (
    <div data-testid={`sci-panel-${domain}`}>
      <h2 style={{ fontFamily: 'serif', fontSize: 20, color: C.gold, margin: '0 0 12px' }}>{title}</h2>
      {cmds.length === 0 ? (
        <p data-testid={`sci-empty-${domain}`} style={{ color: C.dim, fontSize: 12 }}>
          NOT_AVAILABLE - no registry entries for this domain yet.
        </p>
      ) : (
        cmds.map((c) => <CommandCard key={c.id} cmd={c} onNavigate={onNavigate} />)
      )}
    </div>
  );
}

export default function SpiralCommandInterface({ onNavigate }: { onNavigate: Navigate }) {
  const [active, setActive] = useState<SciDomain>('command');

  return (
    <div
      data-testid="spiral-command-interface"
      style={{
        display: 'flex',
        minHeight: 'calc(100vh - 57px)',
        background: '#0A0B14',
        color: C.text,
      }}
    >
      <nav
        data-testid="sci-command-rail"
        style={{
          width: 200,
          flexShrink: 0,
          borderRight: `1px solid ${C.border}`,
          padding: '20px 12px',
          background: 'rgba(8,9,16,0.95)',
        }}
      >
        <p
          style={{
            fontFamily: 'ui-monospace, monospace',
            fontSize: 9,
            letterSpacing: '0.28em',
            textTransform: 'uppercase',
            color: 'rgba(0,212,170,0.45)',
            margin: '0 0 16px',
            paddingLeft: 8,
          }}
        >
          COMMAND
        </p>
        {SCI_CATEGORIES.map((cat) => {
          const isActive = active === cat.id;
          return (
            <button
              key={cat.id}
              type="button"
              data-testid={`sci-nav-${cat.id}`}
              onClick={() => setActive(cat.id)}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: 10,
                width: '100%',
                textAlign: 'left',
                padding: '10px 10px',
                marginBottom: 4,
                background: isActive ? 'rgba(0,212,170,0.08)' : 'transparent',
                border: isActive ? '1px solid rgba(0,212,170,0.28)' : '1px solid transparent',
                borderRadius: 8,
                color: isActive ? C.teal : C.muted,
                fontFamily: 'sans-serif',
                fontSize: 11,
                letterSpacing: '0.06em',
                cursor: 'pointer',
              }}
            >
              <span style={{ width: 16, textAlign: 'center' }}>{cat.sigil}</span>
              {cat.label}
            </button>
          );
        })}
        <div style={{ marginTop: 24, padding: '0 8px' }}>
          <p style={{ fontSize: 9, color: C.dim, letterSpacing: '0.1em', lineHeight: 1.5, margin: 0 }}>
            SCI navigation is not authorization
          </p>
        </div>
      </nav>

      <main style={{ flex: 1, padding: '28px 28px 48px', overflow: 'auto' }}>
        <DomainPanel domain={active} onNavigate={onNavigate} />
        <div style={{ marginTop: 32, opacity: 0.35 }}>
          <p style={{ fontSize: 9, letterSpacing: '0.16em', textTransform: 'uppercase', margin: 0 }}>
            Registry commands: {SCI_COMMANDS.length} - Descriptive only - No authority granted
          </p>
        </div>
      </main>
    </div>
  );
}
