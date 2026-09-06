import React from 'react';
import { useAuth } from '../contexts/AuthContext';

type View = string;

type Props = {
  currentView: View;
  onNavigate: (view: View) => void;
  children: React.ReactNode;
};

// The authenticated interior deliberately inherits NovaNet's original tab-strip
// visual language. These are the canonical system surfaces; the connected
// NovaNet lenses remain available as secondary navigation below the strip.
const SURFACES = [
  { key: 'novanet', label: 'NovaNet', sub: 'Nexus Hub', sigil: '◉', tone: '#6A9FD8' },
  { key: 'sci', label: 'SCI', sub: 'Command', sigil: '#', tone: '#B08DE8' },
  { key: 'solspire', label: 'SolSpire', sub: 'Workspace', sigil: '◉', tone: '#C9A84C' },
  { key: 'commune', label: 'Oracle', sub: 'ARKANA · Think', sigil: '✧', tone: '#00D4AA' },
  { key: 'knowledge-os', label: 'Knowledge', sub: 'Knowledge OS', sigil: '◈', tone: '#6A9FD8' },
] as const;

const LENSES = [
  { key: 'reasomate', label: 'ReasoMate', sigil: '✧', tone: '#6A9FD8' },
  { key: 'personal-echofeild', label: 'Echo Field', sigil: '⬡', tone: '#B08DE8' },
  { key: 'encyclopedia', label: 'Encyclopedia', sigil: '◈', tone: '#C9A84C' },
  { key: 'spiral-codex', label: 'Spiral Codex', sigil: '∞', tone: '#C9A84C' },
  { key: 'grove', label: 'Spiral Grove', sigil: '🌿', tone: '#00D4AA' },
  { key: 'larder', label: 'Living Larder', sigil: '🌾', tone: '#4CAF50' },
  { key: 'offerings', label: 'Offerings', sigil: '✦', tone: '#00D4AA' },
  { key: 'weaver', label: 'Weaver', sigil: '◇', tone: '#B08DE8' },
] as const;

function activeSurfaceFor(currentView: View) {
  if (currentView === 'novanet') return 'novanet';
  if (currentView === 'sci') return 'sci';
  if (currentView === 'solspire' || currentView === 'loops' || currentView === 'codex' || currentView === 'personal-echofeild' || currentView === 'echofeild-matrix' || currentView === 'spiral-codex') return 'solspire';
  if (currentView === 'knowledge-os' || currentView === 'encyclopedia') return 'knowledge-os';
  if (currentView === 'commune' || currentView === 'reasomate') return 'commune';
  return null;
}

function SurfaceButton({
  active,
  label,
  sub,
  sigil,
  tone,
  onClick,
}: {
  active: boolean;
  label: string;
  sub: string;
  sigil: string;
  tone: string;
  onClick: () => void;
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      aria-current={active ? 'page' : undefined}
      style={{
        flexShrink: 0,
        display: 'flex',
        alignItems: 'center',
        gap: 8,
        padding: '10px 16px',
        background: active ? `${tone}10` : 'transparent',
        border: active ? `1px solid ${tone}45` : '1px solid rgba(255,255,255,0.06)',
        borderRadius: 10,
        cursor: 'pointer',
        transition: 'all 0.18s',
      }}
    >
      <span style={{ fontSize: 14 }}>{sigil}</span>
      <div style={{ textAlign: 'left' }}>
        <p style={{ fontFamily: 'sans-serif', fontSize: 10, letterSpacing: '0.2em', textTransform: 'uppercase', color: active ? tone : 'rgba(232,232,232,0.50)', margin: 0, fontWeight: active ? 600 : 400 }}>
          {label}
        </p>
        <p style={{ fontFamily: 'sans-serif', fontSize: 9, color: active ? `${tone}70` : 'rgba(232,232,232,0.28)', margin: 0, whiteSpace: 'nowrap' }}>
          {sub}
        </p>
      </div>
    </button>
  );
}

export default function PrismInteriorShell({ currentView, onNavigate, children }: Props) {
  const { user, profile, codex, isAuthenticated } = useAuth();
  if (!isAuthenticated) return <>{children}</>;

  const displayName = profile?.display_name || user?.displayName || user?.email?.split('@')[0] || 'Node';
  const role = profile?.role || 'Authenticated node';
  const nodeKey = profile?.node_key || codex?.node_key || 'private field';
  const access = profile?.access_level ?? codex?.access_level ?? 0;
  const activeSurface = activeSurfaceFor(currentView);

  return (
    <div data-testid="prism-interior-shell" style={{ minHeight: '100vh', background: '#0C0D18' }}>
      <div
        style={{
          position: 'sticky',
          top: 0,
          zIndex: 30,
          padding: '12px 14px 0',
          borderBottom: '1px solid rgba(201,168,76,0.08)',
          background: 'rgba(8,9,17,0.94)',
          backdropFilter: 'blur(22px)',
          WebkitBackdropFilter: 'blur(22px)',
        }}
      >
        <div style={{ maxWidth: 1180, margin: '0 auto' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 10 }}>
            <div style={{ width: 30, height: 30, borderRadius: 9, display: 'grid', placeItems: 'center', border: '1px solid rgba(201,168,76,.28)', background: 'rgba(201,168,76,.06)', color: '#C9A84C', fontFamily: 'serif', fontSize: 13 }}>*</div>
            <div style={{ minWidth: 0, flex: 1 }}>
              <div style={{ display: 'flex', alignItems: 'baseline', gap: 8, minWidth: 0 }}>
                <span style={{ fontFamily: 'sans-serif', fontSize: 10, letterSpacing: '.16em', textTransform: 'uppercase', color: 'rgba(232,232,232,.82)' }}>{displayName}</span>
                <span style={{ fontFamily: 'sans-serif', fontSize: 8, letterSpacing: '.12em', textTransform: 'uppercase', color: 'rgba(232,232,232,.25)' }}>{role}</span>
              </div>
              <div style={{ fontFamily: 'ui-monospace, monospace', fontSize: 8, color: 'rgba(232,232,232,.25)', marginTop: 2, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                {nodeKey} · access {access}
              </div>
            </div>
            <div style={{ fontFamily: 'ui-monospace, monospace', fontSize: 7, letterSpacing: '.14em', textTransform: 'uppercase', color: 'rgba(0,212,170,.55)', whiteSpace: 'nowrap' }}>
              PRISM / ONE FIELD
            </div>
          </div>

          <div
            className="scrollbar-thin"
            style={{
              display: 'flex',
              gap: 4,
              overflowX: 'auto',
              padding: '4px 0 16px',
            }}
          >
            {SURFACES.map(surface => (
              <SurfaceButton
                key={surface.key}
                active={activeSurface === surface.key}
                label={surface.label}
                sub={surface.sub}
                sigil={surface.sigil}
                tone={surface.tone}
                onClick={() => onNavigate(surface.key)}
              />
            ))}
          </div>

          <div
            className="scrollbar-thin"
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: 6,
              overflowX: 'auto',
              padding: '0 0 10px',
            }}
          >
            <span style={{ flexShrink: 0, fontFamily: 'sans-serif', fontSize: 7, letterSpacing: '.22em', textTransform: 'uppercase', color: 'rgba(201,168,76,.38)', padding: '0 5px' }}>
              Lenses
            </span>
            {LENSES.map(lens => {
              const active = currentView === lens.key || (lens.key === 'weaver' && currentView === 'sci');
              return (
                <button
                  key={lens.key}
                  type="button"
                  onClick={() => onNavigate(lens.key === 'weaver' ? 'sci' : lens.key)}
                  style={{
                    flexShrink: 0,
                    display: 'inline-flex',
                    alignItems: 'center',
                    gap: 5,
                    padding: '5px 9px',
                    borderRadius: 7,
                    border: active ? `1px solid ${lens.tone}35` : '1px solid rgba(255,255,255,0.045)',
                    background: active ? `${lens.tone}09` : 'rgba(255,255,255,0.012)',
                    color: active ? lens.tone : 'rgba(232,232,232,0.38)',
                    cursor: 'pointer',
                    fontFamily: 'sans-serif',
                    fontSize: 8,
                    letterSpacing: '.12em',
                    textTransform: 'uppercase',
                    whiteSpace: 'nowrap',
                  }}
                >
                  <span style={{ fontSize: 10 }}>{lens.sigil}</span>
                  {lens.label}
                </button>
              );
            })}
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: 8, paddingBottom: 8 }}>
            <span style={{ width: 5, height: 5, flexShrink: 0, borderRadius: '50%', background: '#00D4AA', boxShadow: '0 0 10px rgba(0,212,170,.5)' }} />
            <span style={{ fontFamily: 'sans-serif', fontSize: 7.5, letterSpacing: '.15em', textTransform: 'uppercase', color: 'rgba(232,232,232,.22)' }}>
              Same identity · same context · same backend · surface changes, system does not
            </span>
          </div>
        </div>
      </div>
      <div>{children}</div>
    </div>
  );
}
