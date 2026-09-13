import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useAuth } from '../contexts/AuthContext';

type View = string;
type Props = { currentView: View; onNavigate: (view: View) => void; children: React.ReactNode };

const PRIMARY = [
  { key: 'novanet', label: 'NovaNet', sub: 'Outer network', sigil: '◉', tone: '#6A9FD8' },
  { key: 'solspire', label: 'SolSpire', sub: 'Workspace', sigil: '◈', tone: '#C9A84C' },
  { key: 'commune', label: 'Oracle', sub: 'Think', sigil: '✧', tone: '#00D4AA' },
  { key: 'reasomate', label: 'ReasoMate', sub: 'Reasoning', sigil: '⌘', tone: '#B08DE8' },
  { key: 'encyclopedia', label: 'Encyclopedia', sub: 'Knowledge', sigil: '◇', tone: '#6A9FD8' },
  { key: 'offerings', label: 'Offerings', sub: 'Exchange', sigil: '✦', tone: '#C9A84C' },
] as const;

const SECONDARY = [
  { key: 'personal-echofeild', label: 'Echo Field', tone: '#B08DE8' },
  { key: 'spiral-codex', label: 'Spiral Codex', tone: '#C9A84C' },
  { key: 'grove', label: 'Spiral Grove', tone: '#00D4AA' },
  { key: 'larder', label: 'Living Larder', tone: '#4CAF50' },
  { key: 'offerings', label: 'Offerings', tone: '#C9A84C' },
] as const;

function activeSurfaceFor(v: View) {
  if (v === 'novanet') return 'novanet';
  if (v === 'solspire' || v === 'loops' || v === 'codex' || v === 'personal-echofeild' || v === 'echofeild-matrix' || v === 'spiral-codex') return 'solspire';
  if (v === 'commune' || v === 'reasomate') return v === 'reasomate' ? 'reasomate' : 'commune';
  if (v === 'encyclopedia' || v === 'knowledge-os') return 'encyclopedia';
  if (v === 'offerings') return 'offerings';
  return null;
}

function SurfaceButton({ active, label, sub, sigil, tone, onClick }: { active: boolean; label: string; sub: string; sigil: string; tone: string; onClick: () => void }) {
  return <button type="button" onClick={onClick} aria-current={active ? 'page' : undefined} style={{ flexShrink: 0, display: 'flex', alignItems: 'center', gap: 8, minWidth: 0, padding: '9px 14px', boxSizing: 'border-box', background: active ? `${tone}14` : 'rgba(255,255,255,.035)', border: active ? `1px solid ${tone}60` : '1px solid rgba(255,255,255,.10)', borderRadius: 11, cursor: 'pointer', transition: 'all .18s', boxShadow: active ? `0 6px 20px ${tone}16, inset 0 1px 0 rgba(255,255,255,.12)` : 'inset 0 1px 0 rgba(255,255,255,.06)' }}><span style={{ fontSize: 13, color: active ? tone : 'rgba(245,247,250,.78)' }}>{sigil}</span><div style={{ textAlign: 'left', minWidth: 0 }}><p style={{ fontFamily: 'Inter,system-ui,sans-serif', fontSize: 9, letterSpacing: '.14em', textTransform: 'uppercase', color: active ? tone : 'rgba(245,247,250,.82)', margin: 0, fontWeight: active ? 700 : 600, whiteSpace: 'nowrap' }}>{label}</p><p style={{ fontFamily: 'Inter,system-ui,sans-serif', fontSize: 8, color: active ? `${tone}b5` : 'rgba(245,247,250,.48)', margin: 0, whiteSpace: 'nowrap' }}>{sub}</p></div></button>;
}

function NovaNetRail({ currentView, onNavigate }: { currentView: View; onNavigate: (view: View) => void }) {
  const [lensesOpen, setLensesOpen] = useState(false);
  const activeSurface = activeSurfaceFor(currentView);
  return <nav aria-label="NovaNet primary navigation" data-testid="novanet-primary-rail" style={{ position: 'relative', zIndex: 40, width: '100%', maxWidth: '100vw', boxSizing: 'border-box', overflowX: 'hidden', padding: '9px 14px 10px', borderBottom: '1px solid rgba(201,168,76,.16)', background: 'linear-gradient(180deg, rgba(18,22,35,.94), rgba(8,11,19,.90))', backdropFilter: 'blur(24px)', WebkitBackdropFilter: 'blur(24px)', boxShadow: '0 8px 28px rgba(0,0,0,.22), inset 0 1px 0 rgba(255,255,255,.07)' }}><div style={{ maxWidth: 1180, width: '100%', minWidth: 0, margin: '0 auto' }}><div style={{ display: 'flex', gap: 5, minWidth: 0, overflowX: 'auto', overflowY: 'hidden', paddingBottom: 2, scrollbarWidth: 'none', WebkitOverflowScrolling: 'touch' }}>{PRIMARY.map(s => <SurfaceButton key={s.key} active={activeSurface === s.key} label={s.label} sub={s.sub} sigil={s.sigil} tone={s.tone} onClick={() => { setLensesOpen(false); onNavigate(s.key); }} />)}<button type="button" aria-expanded={lensesOpen} onClick={() => setLensesOpen(v => !v)} style={{ flexShrink: 0, padding: '9px 14px', boxSizing: 'border-box', borderRadius: 11, border: lensesOpen ? '1px solid rgba(106,159,216,.55)' : '1px solid rgba(255,255,255,.10)', background: lensesOpen ? 'rgba(106,159,216,.13)' : 'rgba(255,255,255,.035)', color: lensesOpen ? '#8EC5FF' : 'rgba(245,247,250,.76)', font: '700 9px Inter,system-ui,sans-serif', letterSpacing: '.14em', textTransform: 'uppercase', cursor: 'pointer', boxShadow: 'inset 0 1px 0 rgba(255,255,255,.07)' }}>More</button></div><AnimatePresence>{lensesOpen && <motion.div initial={{ opacity: 0, height: 0 }} animate={{ opacity: 1, height: 'auto' }} exit={{ opacity: 0, height: 0 }} transition={{ duration: .18 }} style={{ overflow: 'hidden' }}><div style={{ display: 'flex', flexWrap: 'wrap', gap: 5, marginTop: 8, paddingTop: 8, borderTop: '1px solid rgba(255,255,255,.09)' }}>{SECONDARY.map(item => <button key={item.key} type="button" onClick={() => { setLensesOpen(false); onNavigate(item.key); }} style={{ padding: '7px 11px', borderRadius: 8, border: '1px solid rgba(255,255,255,.10)', background: 'rgba(255,255,255,.045)', color: 'rgba(245,247,250,.74)', font: '700 8px Inter,system-ui,sans-serif', letterSpacing: '.12em', textTransform: 'uppercase', cursor: 'pointer', boxShadow: 'inset 0 1px 0 rgba(255,255,255,.06)' }}>{item.label}</button>)}</div></motion.div>}</AnimatePresence></div></nav>;
}

function IdentityPersistence({ displayName, role, username, sigil, nodeKey }: { displayName: string; role: string; username: string; sigil: string; nodeKey: string }) {
  return <section aria-label="Identity persistence" data-testid="identity-persistence" style={{ width: '100%', maxWidth: '100vw', boxSizing: 'border-box', padding: '10px 16px 9px', borderBottom: '1px solid rgba(255,255,255,.10)', background: 'linear-gradient(180deg, rgba(17,20,32,.98), rgba(9,11,19,.96))', color: '#F4F6F8', boxShadow: 'inset 0 1px 0 rgba(255,255,255,.05)' }}><div style={{ maxWidth: 1180, width: '100%', minWidth: 0, margin: '0 auto', display: 'flex', alignItems: 'center', gap: 10 }}><div style={{ width: 30, height: 30, flex: '0 0 auto', borderRadius: 10, display: 'grid', placeItems: 'center', background: 'linear-gradient(145deg, rgba(201,168,76,.18), rgba(201,168,76,.05))', border: '1px solid rgba(201,168,76,.42)', color: '#E6C96A', fontFamily: 'Georgia,serif', boxShadow: 'inset 0 1px 0 rgba(255,255,255,.10), 0 5px 18px rgba(0,0,0,.25)' }}>{sigil}</div><div style={{ minWidth: 0, flex: 1 }}><div style={{ display: 'flex', gap: 8, alignItems: 'baseline', minWidth: 0, flexWrap: 'nowrap' }}><span style={{ font: '700 10px Inter,system-ui,sans-serif', letterSpacing: '.12em', textTransform: 'uppercase', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{displayName}</span><span style={{ font: '600 8px Inter,system-ui,sans-serif', color: 'rgba(244,246,248,.52)', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{role}</span>{username && <span style={{ font: '700 8px ui-monospace,monospace', color: 'rgba(230,201,106,.72)', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{username}</span>}</div><div style={{ font: '700 7px ui-monospace,monospace', color: 'rgba(244,246,248,.38)', marginTop: 2, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{nodeKey}</div></div><div style={{ flexShrink: 0, font: '700 7px ui-monospace,monospace', letterSpacing: '.16em', textTransform: 'uppercase', color: 'rgba(65,230,190,.82)' }}>PRISM · AUTHENTICATED</div></div></section>;
}

const CLARITY_CSS = `
  .solspire-workspace { color:#F4F6F8 !important; background:radial-gradient(circle at 50% -10%,rgba(106,159,216,.10),transparent 38%),#0B0E17 !important; }
  .solspire-workspace *, .solspire-workspace button, .solspire-workspace input, .solspire-workspace textarea { -webkit-font-smoothing:antialiased; }
  .solspire-workspace p, .solspire-workspace span, .solspire-workspace small, .solspire-workspace label { text-rendering:optimizeLegibility; }
  .solspire-canonical-header { background:linear-gradient(180deg,rgba(24,28,43,.98),rgba(11,14,23,.96)) !important; border-bottom:1px solid rgba(255,255,255,.13) !important; box-shadow:0 10px 30px rgba(0,0,0,.25),inset 0 1px 0 rgba(255,255,255,.08) !important; }
  .solspire-brand-name,.solspire-lens-heading h1,.solspire-project-heading h1,.solspire-overlay-head h2 { color:#F7F8FA !important; text-shadow:0 1px 18px rgba(255,255,255,.06); }
  .solspire-brand-sub,.solspire-kicker,.solspire-mono { color:rgba(220,230,242,.62) !important; }
  .solspire-main,.solspire-project-main { background:transparent !important; }
  .solspire-object,.solspire-attention-note,.solspire-sync-panel,.solspire-source-card,.solspire-search-panel,.solspire-arkana-panel { background:linear-gradient(145deg,rgba(28,33,49,.82),rgba(13,17,27,.78)) !important; border-color:rgba(255,255,255,.13) !important; box-shadow:0 14px 36px rgba(0,0,0,.28),inset 0 1px 0 rgba(255,255,255,.07) !important; backdrop-filter:blur(18px); -webkit-backdrop-filter:blur(18px); }
  .solspire-object:hover,.solspire-source-card:hover { border-color:rgba(106,159,216,.34) !important; transform:translateY(-1px); box-shadow:0 18px 42px rgba(0,0,0,.34),inset 0 1px 0 rgba(255,255,255,.10) !important; }
  .solspire-title,.solspire-object h3,.solspire-search-results h3 { color:#F1F4F7 !important; }
  .solspire-object-summary,.solspire-activity-context,.solspire-source-copy small,.solspire-sync-intro p,.solspire-search-results p { color:rgba(232,238,245,.68) !important; }
  .solspire-object-meta,.solspire-object-meta span { color:rgba(226,235,244,.64) !important; }
  .solspire-header-actions button,.solspire-context-actions button { color:rgba(245,247,250,.78) !important; border-color:rgba(255,255,255,.13) !important; background:rgba(255,255,255,.045) !important; box-shadow:inset 0 1px 0 rgba(255,255,255,.07); }
  .solspire-header-actions button:hover,.solspire-context-actions button:hover { color:#FFFFFF !important; background:rgba(106,159,216,.12) !important; border-color:rgba(106,159,216,.35) !important; }
  .solspire-context-bar { background:rgba(13,17,27,.90) !important; border-bottom:1px solid rgba(255,255,255,.10) !important; box-shadow:0 8px 22px rgba(0,0,0,.18); }
  .solspire-mobile-bottom { display:none !important; }
  .solspire-prism-rail { display:none !important; }
  .solspire-sidebar { position:fixed !important; left:0 !important; right:0 !important; bottom:0 !important; top:auto !important; width:100% !important; height:auto !important; max-width:100vw !important; z-index:70 !important; display:flex !important; flex-direction:row !important; align-items:stretch !important; gap:0 !important; overflow-x:auto !important; overflow-y:hidden !important; padding:6px 0 max(6px,env(safe-area-inset-bottom)) !important; box-sizing:border-box !important; background:linear-gradient(180deg,rgba(24,29,44,.98),rgba(8,11,18,.99)) !important; border-top:1px solid rgba(255,255,255,.14) !important; box-shadow:0 -14px 38px rgba(0,0,0,.34),inset 0 1px 0 rgba(255,255,255,.07) !important; scrollbar-width:none !important; backdrop-filter:blur(22px) !important; -webkit-backdrop-filter:blur(22px) !important; }
  .solspire-sidebar::-webkit-scrollbar { display:none !important; }
  .solspire-sidebar-intro { display:none !important; }
  .solspire-sidebar .solspire-nav-button { flex:0 0 82px !important; width:82px !important; min-width:82px !important; min-height:60px !important; margin:0 !important; padding:7px 5px !important; border:0 !important; border-right:1px solid rgba(255,255,255,.045) !important; border-radius:0 !important; background:transparent !important; color:rgba(239,244,249,.68) !important; display:flex !important; flex-direction:column !important; align-items:center !important; justify-content:center !important; gap:4px !important; }
  .solspire-sidebar .solspire-nav-button > span { font-size:16px !important; line-height:1 !important; }
  .solspire-sidebar .solspire-nav-button > div { min-width:0 !important; text-align:center !important; }
  .solspire-sidebar .solspire-nav-button strong { display:block !important; color:inherit !important; font:700 8px Inter,system-ui,sans-serif !important; letter-spacing:.07em !important; text-transform:uppercase !important; white-space:nowrap !important; }
  .solspire-sidebar .solspire-nav-button small { display:none !important; }
  .solspire-sidebar .solspire-nav-button.active { color:#5FF0C9 !important; background:linear-gradient(180deg,rgba(0,212,170,.16),rgba(0,212,170,.055)) !important; box-shadow:inset 0 2px 0 rgba(95,240,201,.55),0 0 22px rgba(0,212,170,.08) !important; }
  .solspire-body,.solspire-main { min-width:0 !important; width:100% !important; }
  .solspire-main { padding-bottom:calc(78px + env(safe-area-inset-bottom)) !important; }
  .solspire-project-main { padding-bottom:calc(78px + env(safe-area-inset-bottom)) !important; }
  .solspire-canonical-header { top:0 !important; }
  @media(max-width:700px){ .solspire-sidebar .solspire-nav-button { flex-basis:76px !important; width:76px !important; min-width:76px !important; } }
`;

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
  if (solariunSurface) return <div data-testid="prism-interior-shell" style={{ minHeight: '100vh', width: '100%', maxWidth: '100vw', overflowX: 'hidden', background: '#0B0E17', color: '#F4F6F8' }}><style dangerouslySetInnerHTML={{__html:CLARITY_CSS}}/><IdentityPersistence displayName={displayName} role={role} username={username} sigil={sigil} nodeKey={nodeKey} /><NovaNetRail currentView={currentView} onNavigate={onNavigate} />{children}</div>;
  return <div data-testid="prism-interior-shell" style={{ minHeight: '100vh', width: '100%', maxWidth: '100vw', overflowX: 'hidden', background: '#0B0E17', color: '#F4F6F8' }}><header style={{ position: 'sticky', top: 0, zIndex: 30, width: '100%', boxSizing: 'border-box', borderBottom: '1px solid rgba(255,255,255,.10)', background: 'rgba(12,16,26,.96)', backdropFilter: 'blur(22px)', WebkitBackdropFilter: 'blur(22px)' }}><div style={{ maxWidth: 1180, width: '100%', margin: '0 auto', padding: '11px 16px 9px', boxSizing: 'border-box' }}><div style={{ display: 'flex', alignItems: 'center', gap: 10, minWidth: 0 }}>{profile?.avatar_url ? <img src={profile.avatar_url} alt="" style={{ width: 30, height: 30, flexShrink: 0, borderRadius: 10, objectFit: 'cover', border: '1px solid rgba(201,168,76,.30)' }} /> : <div style={{ width: 30, height: 30, flexShrink: 0, borderRadius: 10, display: 'grid', placeItems: 'center', background: 'rgba(201,168,76,.10)', border: '1px solid rgba(201,168,76,.30)', color: '#E6C96A', fontFamily: 'Georgia,serif' }}>{sigil}</div>}<div style={{ minWidth: 0, flex: 1 }}><div style={{ display: 'flex', gap: 8, alignItems: 'baseline', minWidth: 0 }}><span style={{ font: '700 10px Inter,system-ui,sans-serif', letterSpacing: '.12em', textTransform: 'uppercase', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{displayName}</span><span style={{ font: '600 8px Inter,system-ui,sans-serif', color: 'rgba(244,246,248,.52)', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{role}</span>{username && <span style={{ font: '700 8px ui-monospace,monospace', color: 'rgba(230,201,106,.72)', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{username}</span>}</div><div style={{ font: '700 7px ui-monospace,monospace', color: 'rgba(244,246,248,.38)', marginTop: 2, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{nodeKey}</div></div><div style={{ flexShrink: 0, font: '700 7px ui-monospace,monospace', letterSpacing: '.16em', textTransform: 'uppercase', color: 'rgba(65,230,190,.82)' }}>PRISM · AUTHENTICATED</div></div><div style={{ display: 'flex', gap: 4, overflowX: 'auto', overflowY: 'hidden', paddingTop: 10, scrollbarWidth: 'none' }}>{PRIMARY.map(s => <SurfaceButton key={s.key} active={activeSurface === s.key} label={s.label} sub={s.sub} sigil={s.sigil} tone={s.tone} onClick={() => onNavigate(s.key)} />)}</div></div></header><main style={{ width: '100%', minWidth: 0, maxWidth: '100vw' }}>{children}</main></div>;
}
