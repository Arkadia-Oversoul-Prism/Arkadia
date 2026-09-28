import React, { useEffect, useState } from 'react';
import { apiFetch } from '../lib/apiClient';

type Labeled = { value: unknown; state: string };

type ControlRoomPayload = {
  zones: {
    command: Record<string, unknown>;
    commercial: Record<string, Labeled>;
    money: Record<string, Labeled>;
    desks: {
      staffed: string[];
      members: { handle: string; human_name: string; desk: string }[];
      reserve: { label: string; role: string };
    };
    tasks: { by_desk: Record<string, Record<string, number>> };
    next_gate: { unknowns: number; awaiting_authority: number; message: string };
  };
};

const card: React.CSSProperties = {
  background: 'rgba(255,255,255,0.03)',
  border: '1px solid rgba(255,255,255,0.08)',
  borderRadius: 14,
  padding: 16,
};
const muted = 'rgba(233,231,223,0.55)';

function StatePill({ state }: { state: string }) {
  const color =
    state === 'RECORDED'
      ? '#00D4AA'
      : state === 'ESTIMATED'
        ? '#E8B86D'
        : state === 'COMMITTED'
          ? '#7EB6FF'
          : 'rgba(233,231,223,0.45)';
  return (
    <span
      style={{
        fontSize: 9,
        letterSpacing: 0.6,
        textTransform: 'uppercase',
        color,
        border: `1px solid ${color}`,
        borderRadius: 999,
        padding: '2px 8px',
      }}
    >
      {state}
    </span>
  );
}

function Zone({
  title,
  children,
}: {
  title: string;
  children: React.ReactNode;
}) {
  return (
    <section style={card}>
      <div
        style={{
          fontSize: 10,
          color: muted,
          textTransform: 'uppercase',
          letterSpacing: 1,
          marginBottom: 10,
        }}
      >
        {title}
      </div>
      {children}
    </section>
  );
}

export function EdenControlRoom({
  enterpriseId,
  onBack,
}: {
  enterpriseId: string;
  onBack?: () => void;
}) {
  const [data, setData] = useState<ControlRoomPayload | null>(null);
  const [error, setError] = useState('');
  const [busy, setBusy] = useState(true);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      setBusy(true);
      setError('');
      try {
        const r = await apiFetch(
          `/solspire/enterprise/workspaces/${enterpriseId}/control-room`
        );
        const d = await r.json();
        if (!r.ok) throw new Error(d?.detail || 'Unable to load control room');
        if (!cancelled) setData(d);
      } catch (e) {
        if (!cancelled)
          setError(e instanceof Error ? e.message : 'Unable to load control room');
      } finally {
        if (!cancelled) setBusy(false);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [enterpriseId]);

  if (busy) {
    return (
      <main style={{ maxWidth: 1180, margin: '0 auto', padding: 20, color: muted }}>
        Loading control room…
      </main>
    );
  }
  if (error || !data) {
    return (
      <main style={{ maxWidth: 1180, margin: '0 auto', padding: 20 }}>
        <p style={{ color: '#f88' }}>{error || 'No data'}</p>
        {onBack && (
          <button type="button" onClick={onBack}>
            ← Back
          </button>
        )}
      </main>
    );
  }

  const z = data.zones;

  return (
    <main
      style={{
        maxWidth: 1180,
        margin: '0 auto',
        display: 'grid',
        gap: 12,
        paddingBottom: 40,
      }}
    >
      <section style={{ ...card, padding: 20 }}>
        <div style={{ fontSize: 10, color: muted, letterSpacing: 1 }}>SOLSPIRE · CONTROL ROOM</div>
        <h1 style={{ fontSize: 'clamp(28px,6vw,40px)', fontWeight: 400, margin: '8px 0' }}>
          {String(z.command.enterprise_id || enterpriseId)}
        </h1>
        <p style={{ color: muted, lineHeight: 1.6 }}>
          Projection of governed records. Values without evidence stay UNKNOWN.
        </p>
      </section>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit,minmax(260px,1fr))', gap: 10 }}>
        <Zone title="Command">
          <div style={{ fontSize: 12, lineHeight: 1.7 }}>
            <div>Cycle: {String(z.command.cycle || '—')}</div>
            <div>Bindings: {String(z.command.bindings_count ?? 0)}</div>
            <div>Unknowns: {z.next_gate.unknowns}</div>
            <div>Awaiting authority: {z.next_gate.awaiting_authority}</div>
          </div>
        </Zone>

        <Zone title="Commercial">
          {Object.entries(z.commercial).map(([k, v]) => (
            <div
              key={k}
              style={{
                display: 'flex',
                justifyContent: 'space-between',
                gap: 8,
                fontSize: 12,
                marginBottom: 6,
              }}
            >
              <span style={{ color: muted }}>{k}</span>
              <span style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
                <span>{String(v.value)}</span>
                <StatePill state={v.state} />
              </span>
            </div>
          ))}
        </Zone>

        <Zone title="Money">
          {Object.entries(z.money).map(([k, v]) => (
            <div
              key={k}
              style={{
                display: 'flex',
                justifyContent: 'space-between',
                gap: 8,
                fontSize: 12,
                marginBottom: 6,
              }}
            >
              <span style={{ color: muted }}>{k}</span>
              <span style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
                <span>{String(v.value)}</span>
                <StatePill state={v.state} />
              </span>
            </div>
          ))}
        </Zone>

        <Zone title="Desks">
          <div style={{ fontSize: 12, marginBottom: 8 }}>
            {z.desks.staffed.join(' · ')}
          </div>
          <div style={{ fontSize: 11, color: muted }}>
            {z.desks.reserve.label}: {z.desks.reserve.role}
          </div>
          <ul style={{ margin: '10px 0 0', paddingLeft: 18, fontSize: 12 }}>
            {z.desks.members.map((m, i) => (
              <li key={`${m.desk}-${i}`}>
                {m.human_name} — {m.desk}
              </li>
            ))}
          </ul>
        </Zone>

        <Zone title="Tasks">
          {Object.keys(z.tasks.by_desk).length === 0 && (
            <div style={{ fontSize: 12, color: muted }}>No tasks seeded yet.</div>
          )}
          {Object.entries(z.tasks.by_desk).map(([desk, counts]) => (
            <div key={desk} style={{ fontSize: 12, marginBottom: 6 }}>
              <b>{desk}</b>:{' '}
              {Object.entries(counts)
                .map(([st, n]) => `${st} ${n}`)
                .join(' · ')}
            </div>
          ))}
        </Zone>

        <Zone title="Next gate">
          <p style={{ fontSize: 12, lineHeight: 1.6, color: muted }}>{z.next_gate.message}</p>
          <div style={{ fontSize: 12, marginTop: 8 }}>
            Unknowns {z.next_gate.unknowns} · Awaiting authority{' '}
            {z.next_gate.awaiting_authority}
          </div>
        </Zone>
      </div>

      {onBack && (
        <button type="button" onClick={onBack} style={{ justifySelf: 'start' }}>
          ← Return to onboarding
        </button>
      )}
    </main>
  );
}

export default EdenControlRoom;
