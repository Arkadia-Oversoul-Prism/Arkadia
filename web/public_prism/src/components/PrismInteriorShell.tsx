import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useAuth } from '../contexts/AuthContext';

type View = string;
type Props = { currentView: View; onNavigate: (view: View) => void; children: React.ReactNode };

const PRIMARY = [
  { key: 'novanet', label: 'Nova', sub: 'NovaNet', sigil: '◉', tone: '#6A9FD8' },
  { key: 'sci', label: 'Command', sub: 'SCI', sigil: '⌘', tone: '#B08DE8' },
  { key: 'solspire', label: 'Workspace', sub: 'SolSpire', sigil: '◈', tone: '#C9A84C' },
  { key: 'commune', label: 'Oracle', sub: 'Think', sigil: '✧', tone: '#00D4AA' },
  { key: 'knowledge-os', label: 'Knowledge', sub: 'Knowledge OS', sigil: '◇', tone: '#6A9FD8' },
] as const;

const SECONDARY = [
  { key: 'reasomate', label: 'ReasoMate', tone: '#00D4AA' },
  { key: 'personal-echofeild', label: 'Echo Field', tone: '#B08DE8' },
  { key: 'encyclopedia', label: 'Encyclopedia', tone: '#C9A84C' },
  { key: 'spiral-codex', label: 'Spiral Codex', tone: '#C9A84C' },
  { key: 'grove', label: 'Spiral Grove', tone: '#00D4AA' },
  { key: 'larder', label: 'Living Larder', tone: '#4CAF50' },
  { key: 'offerings', label: 'Offerings', tone: '#00D4AA' },
] as const;

function activeSurfaceFor(v: View) {
  if (v === 'novanet') return 'novanet';
  if (v === 'sci') return 'sci';
  if (v === 'solspire' || v === 'loops' || v === 'codex' || v === 'personal-echofeild' || v === 'echofeild-matrix' || v === 'spiral-codex') return 'solspire';
  if (v === 'commune' || v === 'reasomate') return 'commune';
  if (v === 'knowledge-os' || v === 'encyclopedia') return 'knowledge-os';
  return null;
}

function SurfaceButton({ active, label, sub, sigil, tone, onClick }: { active: boolean; label: string; sub: string; sigil: string; tone: string; onClick: () => void }) {
  return <button type="button" onClick={onClick} aria-current={active ? 'page' : undefined} style={{ flexShrink: 0, display: 'flex', alignItems: 'center', gap: 8, minWidth: 0, padding: '9px 14px', boxSizing: 'border-box', background: active ? `${tone}10` : 'rgba(255,255,255,.012)', border: active ? `1px solid ${tone}45` : '1px solid rgba(255,255,255,.055)', borderRadius: 11, cursor: 'pointer', transition: 'all .18s' }}><span style={{ fontSize: 13 }}>{sigil}</span><div style={{ textAlign: 'left', minWidth: 0 }}><p style={{ fontFamily: 'Inter,system-ui,sans-serif', fontSize: 9, letterSpacing: '.14em', textTransform: 'uppercase', color: active ? tone : 'rgba(232,232,232,.5)', margin: 0, fontWeight: active ? 600 : 400, whiteSpace: 'nowrap' }}>{label}</p><p style={{ fontFamily: 'Inter,system-ui,sans-serif', fontSize: 8, color: active ? `${tone}70` : 'rgba(232,232,232,.24)', margin: 0, whiteSpace: 'nowrap' }}>{sub}</p></div></button>;
}

function NovaNetRail({ currentView, onNavigate }: { currentView: View; onNavigate: (view: View) => void }) {
  const [lensesOpen, setLensesOpen] = useState(false);
  const activeSurface = activeSurfaceFor(currentView);
  return <nav aria-label="NovaNet primary navigation" data-testid="novanet-primary-rail" style={{ position: 'sticky', top: 0, zIndex: 40, width: '100%', maxWidth: '100vw', boxSizing: 'border-box', overflowX: 'hidden', padding: '8px 14px 9px', borderBottom: '1px solid rgba(201,168,76,.10)', background: 'rgba(8,9,17,.90)', backdropFilter: 'blur(22px)', WebkitBackdropFilter: 'blur(22px)' }}><div style={{ maxWidth: 1180, width: '100%', minWidth: 0, margin: '0 auto' }}><div style={{ display: 'flex', gap: 4, minWidth: 0, overflowX: 'auto', overflowY: 'hidden', paddingBottom: 2, scrollbarWidth: 'none', WebkitOverflowScrolling: 'touch' }}>{PRIMARY.map(s => <SurfaceButton key={s.key} active={activeSurface === s.key} label={s.label} sub={s.sub} sigil={s.sigil} tone={s.tone} onClick={() => { setLensesOpen(false); onNavigate(s.key); }} />)}<button type="button" aria-expanded={lensesOpen} onClick={() => setLensesOpen(v => !v)} style={{ flexShrink: 0, padding: '9px 14px', boxSizing: 'border-box', borderRadius: 11, border: lensesOpen ? '1px solid rgba(106,159,216,.40)' : '1px solid rgba(255,255,255,.055)', background: lensesOpen ? 'rgba(106,159,216,.08)' : 'rgba(255,255,255,.012)', color: lensesOpen ? '#6A9FD8' : 'rgba(232,232,232,.55)', font: '9px Inter,system-ui,sans-serif', letterSpacing: '.14em', textTransform: 'uppercase', cursor: 'pointer' }}>More</button></div><AnimatePresence>{lensesOpen && <motion.div initial={{ opacity: 0, height: 0 }} animate={{ opacity: 1, height: 'auto' }} exit={{ opacity: 0, height: 0 }} transition={{ duration: .18 }} style={{ overflow: 'hidden' }}><div style={{ display: 'flex', flexWrap: 'wrap', gap: 5, marginTop: 8, paddingTop: 8, borderTop: '1px solid rgba(255,255,255,.05)' }}>{SECONDARY.map(item => <button key={item.key} type="button" onClick={() => { setLensesOpen(false); onNavigate(item.key); }} style={{ padding: '6px 10px', borderRadius: 8, border: '1px solid rgba(255,255,255,.06)', background: 'rgba(255,255,255,.02)', color: 'rgba(232,232,232,.55)', font: '8px Inter,system-ui,sans-serif', letterSpacing: '.12em', textTransform: 'uppercase', cursor: 'pointer' }}>{item.label}</button>)}</div></motion.div>}</AnimatePresence></div></nav>;
}

export default function PrismInteriorShell({ currentView, onNavigate, children }: Props) {
  const { user, profile, identitySpine, codex, isAuthenticated } = useAuth();
  if (!isAuthenticated) return <>{children}</>;

  const displayName = identitySpine?.identity.preferred_name || profile?.display_name || user?.displayName || user?.email?.split('@')[0] || 'Authenticated node';
  const role = identitySpine?.identity.role || profile?.role || 'Authenticated node';
  const username = identitySpine?.identity.username ? `@${identitySpine.identity.username}` : '';
  const sigil = identitySpine?.seed?.sigil || identitySpine?.symbolic?.sigil_seed || profile?.role_sigil || '◈';
  const nodeKey = profile?.node_key || codex?.node_key || 'private field';
  const activeSurface = activeSurfaceFor(currentView);
  const solariunSurface = currentView === 'solspire' || currentView === 'loops' || currentView === 'codex' || currentView === 'personal-echofeild' || currentView === 'echofeild-matrix' || currentView === 'spiral-codex';

  if (solariunSurface) {
    return <div data-testid="prism-interior-shell" style={{ minHeight: '100vh', width: '100%', maxWidth: '100vw', overflowX: 'hidden', background: '#0C0D18', color: '#E9E7DF' }}><NovaNetRail currentView={currentView} onNavigate={onNavigate} />{children}</div>;
  }

  return <div data-testid="prism-interior-shell" style={{ minHeight: '100vh', width: '100%', maxWidth: '100vw', overflowX: 'hidden', background: '#0C0D18', color: '#E9E7DF' }}><header style={{ position: 'sticky', top: 0, zIndex: 30, width: '100%', boxSizing: 'border-box', borderBottom: '1px solid rgba(255,255,255,.07)', background: 'rgba(8,9,17,.94)', backdropFilter: 'blur(22px)', WebkitBackdropFilter: 'blur(22px)' }}><div style={{ maxWidth: 1180, width: '100%', margin: '0 auto', padding: '11px 16px 9px', boxSizing: 'border-box' }}><div style={{ display: 'flex', alignItems: 'center', gap: 10, minWidth: 0 }}>{profile?.avatar_url ? <img src={profile.avatar_url} alt="" style={{ width: 30, height: 30, flexShrink: 0, borderRadius: 10, objectFit: 'cover', border: '1px solid rgba(201,168,76,.25)' }} /> : <div style={{ width: 30, height: 30, flexShrink: 0, borderRadius: 10, display: 'grid', placeItems: 'center', background: 'rgba(201,168,76,.07)', border: '1px solid rgba(201,168,76,.24)', color: '#C9A84C', fontFamily: 'Georgia,serif' }}>{sigil}</div>}<div style={{ minWidth: 0, flex: 1 }}><div style={{ display: 'flex', gap: 8, alignItems: 'baseline', minWidth: 0 }}><span style={{ font: '600 10px Inter,system-ui,sans-serif', letterSpacing: '.12em', textTransform: 'uppercase', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{displayName}</span><span style={{ font: '8px Inter,system-ui,sans-serif', color: 'rgba(233,231,223,.28)', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{role}</span>{username && <span style={{ font: '8px ui-monospace,monospace', color: 'rgba(201,168,76,.45)', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{username}</span>}</div><div style={{ font: '7px ui-monospace,monospace', color: 'rgba(233,231,223,.2)', marginTop: 2, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{nodeKey}</div></div><div style={{ flexShrink: 0, font: '7px ui-monospace,monospace', letterSpacing: '.16em', textTransform: 'uppercase', color: 'rgba(0,212,170,.55)' }}>PRISM · AUTHENTICATED</div></div><div style={{ display: 'flex', gap: 4, overflowX: 'auto', overflowY: 'hidden', paddingTop: 10, scrollbarWidth: 'none' }}>{PRIMARY.map(s => <SurfaceButton key={s.key} active={activeSurface === s.key} label={s.label} sub={s.sub} sigil={s.sigil} tone={s.tone} onClick={() => onNavigate(s.key)} />)}<button type="button" onClick={() => onNavigate('account')} style={{ flexShrink: 0, padding: '9px 14px', borderRadius: 11, border: '1px solid rgba(255,255,255,.055)', background: 'rgba(255,255,255,.012)', color: 'rgba(232,232,232,.55)', font: '9px Inter,system-ui,sans-serif', letterSpacing: '.14em', textTransform: 'uppercase', cursor: 'pointer' }}>Account</button></div></div></header><main style={{ width: '100%', minWidth: 0, maxWidth: '100vw' }}>{children}</main></div>;
}
