import React from 'react';
import { motion } from 'framer-motion';
import { useAuth } from '../contexts/AuthContext';

type View = string;

type Props = {
  currentView: View;
  onNavigate: (view: View) => void;
  children: React.ReactNode;
};

const SURFACES = [
  { key: 'sci', label: 'Command', sub: 'SCI', tone: '#B08DE8' },
  { key: 'solspire', label: 'Workspace', sub: 'SolSpire', tone: '#C9A84C' },
  { key: 'commune', label: 'Oracle', sub: 'Think', tone: '#00D4AA' },
  { key: 'knowledge-os', label: 'Knowledge', sub: 'Knowledge OS', tone: '#6A9FD8' },
];

function SurfaceButton({
  active,
  label,
  sub,
  tone,
  onClick,
}: {
  active: boolean;
  label: string;
  sub: string;
  tone: string;
  onClick: () => void;
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      aria-current={active ? 'page' : undefined}
      style={{
        flex: '1 1 0',
        minWidth: 0,
        padding: '10px 9px',
        borderRadius: 10,
        border: `1px solid ${active ? `${tone}45` : 'rgba(255,255,255,.06)'}`,
        background: active ? `${tone}0d` : 'rgba(255,255,255,.018)',
        color: active ? tone : 'rgba(232,232,232,.58)',
        cursor: 'pointer',
        textAlign: 'left',
      }}
    >
      <span style={{ display: 'block', fontFamily: 'sans-serif', fontSize: 8, letterSpacing: '.16em', textTransform: 'uppercase', marginBottom: 3 }}>
        {label}
      </span>
      <span style={{ display: 'block', fontFamily: 'sans-serif', fontSize: 10, color: active ? `${tone}a8` : 'rgba(232,232,232,.30)', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
        {sub}
      </span>
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
  const activeSurface = currentView === 'sci'
    ? 'sci'
    : currentView === 'solspire' || currentView === 'loops' || currentView === 'codex' || currentView === 'personal-echofeild' || currentView === 'echofeild-matrix' || currentView === 'spiral-codex'
      ? 'solspire'
      : currentView === 'knowledge-os' || currentView === 'encyclopedia'
        ? 'knowledge-os'
        : currentView === 'commune' || currentView === 'reasomate'
          ? 'commune'
          : null;

  return (
    <div data-testid="prism-interior-shell" style={{ minHeight: 'calc(100vh - 52px)' }}>
      <div
        style={{
          position: 'sticky',
          top: 52,
          zIndex: 30,
          padding: '8px 14px 9px',
          borderBottom: '1px solid rgba(201,168,76,.10)',
          background: 'rgba(8,9,17,.90)',
          backdropFilter: 'blur(22px)',
          WebkitBackdropFilter: 'blur(22px)',
        }}
      >
        <div style={{ maxWidth: 1180, margin: '0 auto' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 8 }}>
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
          <div style={{ display: 'flex', gap: 6 }}>
            {SURFACES.map(surface => (
              <SurfaceButton
                key={surface.key}
                active={activeSurface === surface.key}
                label={surface.label}
                sub={surface.sub}
                tone={surface.tone}
                onClick={() => onNavigate(surface.key)}
              />
            ))}
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginTop: 7 }}>
            <motion.span
              animate={{ opacity: [0.35, 0.8, 0.35] }}
              transition={{ duration: 2.8, repeat: Infinity }}
              style={{ width: 5, height: 5, borderRadius: '50%', background: '#00D4AA', boxShadow: '0 0 10px rgba(0,212,170,.5)' }}
            />
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
