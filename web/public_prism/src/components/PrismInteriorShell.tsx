import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useAuth } from '../contexts/AuthContext';

type View = string;

type Props = {
  currentView: View;
  onNavigate: (view: View) => void;
  children: React.ReactNode;
};

/** Canonical primary destinations — authenticated NovaNet / Nexus orientation rail. */
const PRIMARY = [
  { key: 'novanet', label: 'Nova', sub: 'NovaNet', tone: '#6A9FD8' },
  { key: 'sci', label: 'Command', sub: 'SCI', tone: '#B08DE8' },
  { key: 'solspire', label: 'Workspace', sub: 'SolSpire', tone: '#C9A84C' },
  { key: 'commune', label: 'Oracle', sub: 'Think', tone: '#00D4AA' },
  { key: 'knowledge-os', label: 'Knowledge', sub: 'Knowledge OS', tone: '#6A9FD8' },
] as const;

/**
 * Secondary Nexus lenses — existing App views only.
 * Not a second product shelf; contextual rooms of the same interior.
 */
const SECONDARY = [
  { key: 'reasomate', label: 'ReasoMate', tone: '#00D4AA' },
  { key: 'personal-echofeild', label: 'Echo Field', tone: '#B08DE8' },
  { key: 'encyclopedia', label: 'Encyclopedia', tone: '#C9A84C' },
  { key: 'spiral-codex', label: 'Spiral Codex', tone: '#C9A84C' },
  { key: 'grove', label: 'Spiral Grove', tone: '#00D4AA' },
  { key: 'larder', label: 'Living Larder', tone: '#4CAF50' },
  { key: 'offerings', label: 'Offerings', tone: '#C9A84C' },
  { key: 'sci', label: 'Weaver', tone: '#B08DE8' },
] as const;

function resolvePrimary(view: View): string | null {
  if (view === 'novanet' || view === 'nexus') return 'novanet';
  if (view === 'sci') return 'sci';
  if (
    view === 'solspire' ||
    view === 'loops' ||
    view === 'codex' ||
    view === 'personal-echofeild' ||
    view === 'echofeild-matrix' ||
    view === 'spiral-codex'
  ) {
    return 'solspire';
  }
  if (view === 'knowledge-os' || view === 'encyclopedia') return 'knowledge-os';
  if (view === 'commune' || view === 'reasomate') return 'commune';
  return null;
}

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
        flex: '0 0 auto',
        minWidth: 88,
        padding: '9px 11px',
        borderRadius: 10,
        border: `1px solid ${active ? `${tone}45` : 'rgba(255,255,255,.06)'}`,
        background: active ? `${tone}0d` : 'rgba(255,255,255,.018)',
        color: active ? tone : 'rgba(232,232,232,.58)',
        cursor: 'pointer',
        textAlign: 'left',
      }}
    >
      <span
        style={{
          display: 'block',
          fontFamily: 'sans-serif',
          fontSize: 8,
          letterSpacing: '.16em',
          textTransform: 'uppercase',
          marginBottom: 3,
        }}
      >
        {label}
      </span>
      <span
        style={{
          display: 'block',
          fontFamily: 'sans-serif',
          fontSize: 10,
          color: active ? `${tone}a8` : 'rgba(232,232,232,.30)',
          whiteSpace: 'nowrap',
          overflow: 'hidden',
          textOverflow: 'ellipsis',
        }}
      >
        {sub}
      </span>
    </button>
  );
}

/**
 * Authenticated NovaNet / Nexus interior shell.
 * Presentation orientation only — identity from AuthContext; no mutation authority.
 */
export default function PrismInteriorShell({ currentView, onNavigate, children }: Props) {
  const { user, profile, codex, isAuthenticated } = useAuth();
  const [lensesOpen, setLensesOpen] = useState(false);

  if (!isAuthenticated) return <>{children}</>;

  const displayName =
    profile?.display_name || user?.displayName || user?.email?.split('@')[0] || 'Node';
  const role = profile?.role || 'Authenticated node';
  const nodeKey = profile?.node_key || codex?.node_key || 'private field';
  const access = profile?.access_level ?? codex?.access_level ?? 0;
  const activePrimary = resolvePrimary(currentView);

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
            <div
              style={{
                width: 30,
                height: 30,
                borderRadius: 9,
                display: 'grid',
                placeItems: 'center',
                border: '1px solid rgba(201,168,76,.28)',
                background: 'rgba(201,168,76,.06)',
                color: '#C9A84C',
                fontFamily: 'serif',
                fontSize: 13,
              }}
            >
              *
            </div>
            <div style={{ minWidth: 0, flex: 1 }}>
              <div style={{ display: 'flex', alignItems: 'baseline', gap: 8, minWidth: 0 }}>
                <span
                  style={{
                    fontFamily: 'sans-serif',
                    fontSize: 10,
                    letterSpacing: '.16em',
                    textTransform: 'uppercase',
                    color: 'rgba(232,232,232,.82)',
                  }}
                >
                  {displayName}
                </span>
                <span
                  style={{
                    fontFamily: 'sans-serif',
                    fontSize: 8,
                    letterSpacing: '.12em',
                    textTransform: 'uppercase',
                    color: 'rgba(232,232,232,.25)',
                  }}
                >
                  {role}
                </span>
              </div>
              <div
                style={{
                  fontFamily: 'ui-monospace, monospace',
                  fontSize: 8,
                  color: 'rgba(232,232,232,.25)',
                  marginTop: 2,
                  overflow: 'hidden',
                  textOverflow: 'ellipsis',
                  whiteSpace: 'nowrap',
                }}
              >
                {nodeKey} · access {access}
              </div>
            </div>
            <div
              style={{
                fontFamily: 'ui-monospace, monospace',
                fontSize: 7,
                letterSpacing: '.14em',
                textTransform: 'uppercase',
                color: 'rgba(0,212,170,.55)',
                whiteSpace: 'nowrap',
              }}
            >
              PRISM / NOVANET
            </div>
          </div>

          {/* Primary horizontal rail — NovaNet visual language */}
          <div
            data-testid="prism-primary-rail"
            style={{
              display: 'flex',
              gap: 6,
              overflowX: 'auto',
              WebkitOverflowScrolling: 'touch',
              paddingBottom: 2,
            }}
          >
            {PRIMARY.map((surface) => (
              <SurfaceButton
                key={surface.key}
                active={activePrimary === surface.key}
                label={surface.label}
                sub={surface.sub}
                tone={surface.tone}
                onClick={() => {
                  setLensesOpen(false);
                  onNavigate(surface.key);
                }}
              />
            ))}
            <button
              type="button"
              data-testid="prism-secondary-toggle"
              aria-expanded={lensesOpen}
              onClick={() => setLensesOpen((v) => !v)}
              style={{
                flex: '0 0 auto',
                minWidth: 72,
                padding: '9px 11px',
                borderRadius: 10,
                border: `1px solid ${lensesOpen ? 'rgba(106,159,216,.40)' : 'rgba(255,255,255,.06)'}`,
                background: lensesOpen ? 'rgba(106,159,216,.08)' : 'rgba(255,255,255,.018)',
                color: lensesOpen ? '#6A9FD8' : 'rgba(232,232,232,.50)',
                cursor: 'pointer',
                textAlign: 'left',
              }}
            >
              <span
                style={{
                  display: 'block',
                  fontFamily: 'sans-serif',
                  fontSize: 8,
                  letterSpacing: '.16em',
                  textTransform: 'uppercase',
                  marginBottom: 3,
                }}
              >
                More
              </span>
              <span
                style={{
                  display: 'block',
                  fontFamily: 'sans-serif',
                  fontSize: 10,
                  color: lensesOpen ? 'rgba(106,159,216,.85)' : 'rgba(232,232,232,.30)',
                }}
              >
                Lenses
              </span>
            </button>
          </div>

          <AnimatePresence>
            {lensesOpen && (
              <motion.div
                data-testid="prism-secondary-lenses"
                initial={{ opacity: 0, height: 0 }}
                animate={{ opacity: 1, height: 'auto' }}
                exit={{ opacity: 0, height: 0 }}
                transition={{ duration: 0.2 }}
                style={{ overflow: 'hidden' }}
              >
                <div
                  style={{
                    display: 'flex',
                    flexWrap: 'wrap',
                    gap: 6,
                    marginTop: 8,
                    paddingTop: 8,
                    borderTop: '1px solid rgba(255,255,255,.05)',
                  }}
                >
                  {SECONDARY.map((item) => {
                    const active = currentView === item.key;
                    return (
                      <button
                        key={`${item.key}-${item.label}`}
                        type="button"
                        onClick={() => {
                          setLensesOpen(false);
                          onNavigate(item.key);
                        }}
                        style={{
                          padding: '6px 10px',
                          borderRadius: 8,
                          border: `1px solid ${active ? `${item.tone}40` : 'rgba(255,255,255,.06)'}`,
                          background: active ? `${item.tone}0c` : 'rgba(255,255,255,.02)',
                          color: active ? item.tone : 'rgba(232,232,232,.55)',
                          fontFamily: 'sans-serif',
                          fontSize: 9,
                          letterSpacing: '.12em',
                          textTransform: 'uppercase',
                          cursor: 'pointer',
                        }}
                      >
                        {item.label}
                      </button>
                    );
                  })}
                </div>
              </motion.div>
            )}
          </AnimatePresence>

          <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginTop: 7 }}>
            <motion.span
              animate={{ opacity: [0.35, 0.8, 0.35] }}
              transition={{ duration: 2.8, repeat: Infinity }}
              style={{
                width: 5,
                height: 5,
                borderRadius: '50%',
                background: '#00D4AA',
                boxShadow: '0 0 10px rgba(0,212,170,.5)',
              }}
            />
            <span
              style={{
                fontFamily: 'sans-serif',
                fontSize: 7.5,
                letterSpacing: '.15em',
                textTransform: 'uppercase',
                color: 'rgba(232,232,232,.22)',
              }}
            >
              Same identity · same context · same backend · surface changes, system does not
            </span>
          </div>
        </div>
      </div>
      <div>{children}</div>
    </div>
  );
}
