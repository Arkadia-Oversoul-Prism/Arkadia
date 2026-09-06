/**
 * SolSpire Console
 *
 * Canonical authenticated workspace for the private Arkadia system.
 *
 * Projects are workspace objects/folders, not a navigation container.
 * The existing ProjectDashboard remains available only as a folder/thread
 * surface when a user opens a project object from Files.
 *
 * Public Spiral Codex / Encyclopedia Galactica remains outside this private shell.
 */
import React, { useLayoutEffect, useState } from 'react';
import { useAuth } from '../contexts/AuthContext';
import ProjectDashboard, { setSolspireAuthToken, Project } from './ProjectDashboard';
import Overview from './dashboard/Overview';
import OpenLoops from './dashboard/OpenLoops';
import Goals from './dashboard/Goals';
import Releases from './dashboard/Releases';
import Jobs from './dashboard/Jobs';
import Traces from './dashboard/Traces';
import Tools from './dashboard/Tools';
import System from './dashboard/System';
import KnowledgeOSPage from './knowledge/KnowledgeOSPage';
import UniversalEchofeildMatrix from './UniversalEchofeildMatrix';
import SettingsPage from './SettingsPage';
import { CommercialPanel, Observatory, WeaverSummary, WorkspaceCollection, WorkspaceFiles } from './SolSpireWorkspacePanels';
import type { WorkspaceCollectionKind } from './SolSpireWorkspacePanels';

export type SolSpireSection = 'overview' | 'commercial' | 'knowledge' | 'files' | 'conversations' | 'tasks' | 'memory' | 'weaver' | 'observatory' | 'settings';
type LegacySection = SolSpireSection | 'field' | 'codex' | 'loops' | 'projects' | 'encyclopedia' | 'goals' | 'releases' | 'jobs' | 'traces' | 'tools' | 'system';
type AppView = 'home'|'gate'|'commune'|'reset'|'about'|'login'|'codex'|'dashboard'|'nexus'|'encyclopedia'|'spiral-codex'|'loops'|'grove'|'larder'|'novanet'|'ims'|'distribute'|'offerings'|'aic'|'pulse'|'settings'|'solspire'|'knowledge-os'|'reasomate'|'personal-echofeild'|'echofeild-matrix';

const NAV: { id: SolSpireSection; label: string; sigil: string; color: string; sub: string }[] = [
  { id: 'overview', label: 'Overview', sigil: '◎', color: '#6A9FD8', sub: 'Workspace orientation and operating state' },
  { id: 'commercial', label: 'Commercial', sigil: '◈', color: '#C9A84C', sub: 'Market signals, opportunities, next decisions' },
  { id: 'knowledge', label: 'Knowledge', sigil: '◉', color: '#00D4AA', sub: 'Knowledge OS, graph, corpus and routing' },
  { id: 'files', label: 'Files', sigil: '◫', color: '#C9A84C', sub: 'Folders, projects, documents and media' },
  { id: 'conversations', label: 'Conversations', sigil: '◌', color: '#6A9FD8', sub: 'All private project conversations' },
  { id: 'tasks', label: 'Tasks', sigil: '☐', color: '#00D4AA', sub: 'Workspace-wide task state' },
  { id: 'memory', label: 'Memory', sigil: '∞', color: '#B08DE8', sub: 'Project memory as one private view' },
  { id: 'weaver', label: 'Weaver', sigil: '⚒', color: '#B08DE8', sub: 'Governed engineering workflow' },
  { id: 'observatory', label: 'Observatory', sigil: '⟐', color: '#6A9FD8', sub: 'Events, traces and system activity' },
  { id: 'settings', label: 'Settings', sigil: '◆', color: '#888', sub: 'Private workspace configuration' },
];

const LEGACY_MAP: Record<string, SolSpireSection> = { field: 'overview', codex: 'overview', loops: 'overview', projects: 'files', encyclopedia: 'knowledge', goals: 'overview', releases: 'overview', jobs: 'observatory', traces: 'observatory', tools: 'observatory', system: 'observatory' };

function Header({ item, onMenu }: { item: typeof NAV[number]; onMenu: () => void }) { return <div style={{ padding: '13px 16px', borderBottom: '1px solid rgba(201,168,76,0.09)', background: 'rgba(9,10,22,0.96)', display: 'flex', alignItems: 'center', gap: 10, position: 'sticky', top: 52, zIndex: 20 }}><span style={{ color: item.color, fontSize: 15 }}>{item.sigil}</span><div style={{ flex: 1 }}><div style={{ fontFamily: 'Cinzel,serif', fontSize: 13, letterSpacing: '0.1em', color: item.color }}>{item.label}</div><div style={{ fontFamily: 'sans-serif', fontSize: 9, color: 'rgba(212,223,232,0.28)', marginTop: 2 }}>{item.sub}</div></div><button onClick={onMenu} style={{ border: 0, background: 'transparent', color: 'rgba(232,232,232,0.5)', fontSize: 18, cursor: 'pointer' }}>☰</button></div>; }
function Sidebar({ section, onSection }: { section: SolSpireSection; onSection: (s: SolSpireSection) => void }) { return <aside style={{ width: 224, flexShrink: 0, borderRight: '1px solid rgba(201,168,76,0.08)', background: 'rgba(9,10,22,0.82)', padding: '22px 11px', position: 'sticky', top: 52, height: 'calc(100vh - 52px)', overflowY: 'auto' }}><div style={{ padding: '0 9px 17px', borderBottom: '1px solid rgba(201,168,76,0.08)', marginBottom: 10 }}><div style={{ display: 'flex', alignItems: 'center', gap: 7 }}><span style={{ width: 6, height: 6, borderRadius: '50%', background: '#C9A84C', boxShadow: '0 0 8px #C9A84C88' }} /><span style={{ fontFamily: 'Cinzel,serif', fontSize: 11, letterSpacing: '0.3em', color: '#C9A84C' }}>SOLSPIRE</span></div><div style={{ fontFamily: 'sans-serif', fontSize: 8.5, color: 'rgba(212,223,232,0.27)', marginTop: 5 }}>Private workspace · one surface</div></div>{NAV.map(item => <button key={item.id} type="button" onClick={() => onSection(item.id)} style={{ width: '100%', border: `1px solid ${section === item.id ? item.color + '30' : 'transparent'}`, background: section === item.id ? `${item.color}0b` : 'transparent', borderRadius: 8, padding: '9px 8px', marginBottom: 3, display: 'flex', alignItems: 'center', gap: 9, cursor: 'pointer', textAlign: 'left' }}><span style={{ color: section === item.id ? item.color : 'rgba(232,232,232,0.38)', width: 17, textAlign: 'center' }}>{item.sigil}</span><span style={{ fontFamily: 'sans-serif', fontSize: 10.5, color: section === item.id ? item.color : 'rgba(232,232,232,0.62)' }}>{item.label}</span></button>)}<div style={{ marginTop: 14, padding: '10px 8px', borderTop: '1px solid rgba(0,212,170,0.07)', fontFamily: 'sans-serif', fontSize: 8, letterSpacing: '0.15em', textTransform: 'uppercase', color: 'rgba(0,212,170,0.3)' }}>◈ Authenticated · private</div></aside>; }
function OverviewSurface() { const [ops, setOps] = useState(false); return <div style={{ display: 'flex', flexDirection: 'column', gap: 14 }}><Overview /><div style={{ padding: 14, background: 'rgba(176,141,232,0.04)', border: '1px solid rgba(176,141,232,0.1)', borderRadius: 12 }}><button type="button" onClick={() => setOps(v => !v)} style={{ width: '100%', background: 'transparent', border: 0, color: '#B08DE8', cursor: 'pointer', display: 'flex', justifyContent: 'space-between', padding: 0, fontFamily: 'sans-serif', fontSize: 9, letterSpacing: '0.2em', textTransform: 'uppercase' }}><span>Operational substrate</span><span>{ops ? '⌃' : '⌄'}</span></button>{ops && <div style={{ marginTop: 14, display: 'flex', flexDirection: 'column', gap: 14 }}><OpenLoops /><Goals /><Releases /><Jobs onOpenTrace={() => {}} /><Traces /><Tools /><System /></div>}</div><div style={{ padding: 14, background: 'rgba(176,141,232,0.04)', border: '1px solid rgba(176,141,232,0.1)', borderRadius: 12 }}><div style={{ fontFamily: 'sans-serif', fontSize: 8, letterSpacing: '0.22em', textTransform: 'uppercase', color: 'rgba(176,141,232,0.5)', marginBottom: 9 }}>Field substrate</div><UniversalEchofeildMatrix onNavigate={() => {}} /></div></div>; }

export default function SolSpireConsole({ onNavigate, initialSection = 'overview' }: { onNavigate?: (v: AppView) => void; initialSection?: LegacySection } = {}) {
  const { isAuthenticated, user } = useAuth();
  const initial = (LEGACY_MAP[initialSection] || initialSection) as SolSpireSection;
  const [section, setSection] = useState<SolSpireSection>(initial);
  const [mobileNav, setMobileNav] = useState(false);
  const [openProject, setOpenProject] = useState<Project | null>(null);
  useLayoutEffect(() => { setSolspireAuthToken(user?.idToken ?? null); }, [user?.idToken]);

  if (!isAuthenticated) return <div style={{ minHeight: 'calc(100vh - 52px)', background: '#0A0B14', display: 'grid', placeItems: 'center', padding: 24 }}><div style={{ maxWidth: 520, textAlign: 'center', padding: 28, border: '1px solid rgba(201,168,76,0.15)', borderRadius: 14, background: 'rgba(14,17,32,0.8)' }}><div style={{ fontFamily: 'Cinzel,serif', color: '#C9A84C', letterSpacing: '0.18em', fontSize: 16 }}>SOLSPIRE</div><p style={{ fontFamily: 'sans-serif', color: 'rgba(212,223,232,0.42)', lineHeight: 1.6, fontSize: 12 }}>This is the private workspace. Sign in to enter the authenticated field.</p><button onClick={() => onNavigate?.('gate')} style={{ padding: '9px 16px', borderRadius: 7, border: '1px solid rgba(0,212,170,0.3)', background: 'rgba(0,212,170,0.08)', color: '#00D4AA', cursor: 'pointer' }}>Enter workspace</button></div></div>;
  if (openProject) return <div style={{ minHeight: 'calc(100vh - 52px)', background: '#0A0B14' }}><div style={{ padding: '11px 16px', borderBottom: '1px solid rgba(201,168,76,0.1)', background: 'rgba(9,10,22,0.95)', display: 'flex', alignItems: 'center', gap: 10, position: 'sticky', top: 52, zIndex: 30 }}><button type="button" onClick={() => setOpenProject(null)} style={{ border: '1px solid rgba(201,168,76,0.2)', background: 'rgba(201,168,76,0.06)', color: '#C9A84C', borderRadius: 7, padding: '7px 10px', cursor: 'pointer', fontSize: 9 }}>← Files</button><span style={{ fontFamily: 'Cinzel,serif', color: '#C9A84C', fontSize: 13 }}>📁 {openProject.name}</span><span style={{ fontFamily: 'sans-serif', fontSize: 8, color: 'rgba(212,223,232,0.25)', marginLeft: 'auto' }}>WORKSPACE THREAD</span></div><ProjectDashboard project={openProject} onBack={() => setOpenProject(null)} onProjectUpdated={setOpenProject} /></div>;
  const item = NAV.find(n => n.id === section) || NAV[0];
  const collection: WorkspaceCollectionKind | null = section === 'conversations' ? 'conversations' : section === 'tasks' ? 'tasks' : section === 'memory' ? 'memory' : null;
  const content = section === 'overview' ? <OverviewSurface /> : section === 'commercial' ? <CommercialPanel /> : section === 'knowledge' ? <KnowledgeOSPage /> : section === 'files' ? <WorkspaceFiles onOpenProject={setOpenProject} /> : collection ? <WorkspaceCollection kind={collection} /> : section === 'weaver' ? <WeaverSummary onOpenProject={setOpenProject} /> : section === 'observatory' ? <Observatory /> : <SettingsPage />;
  return <div data-testid="solspire-console" style={{ minHeight: 'calc(100vh - 52px)', background: '#0A0B14', position: 'relative' }}><div className="aurora-bg" /><div className="solspire-mobile"><Header item={item} onMenu={() => setMobileNav(v => !v)} />{mobileNav && <div style={{ padding: 10, background: 'rgba(9,10,22,0.98)', borderBottom: '1px solid rgba(201,168,76,0.1)', position: 'sticky', top: 101, zIndex: 19 }}>{NAV.map(n => <button key={n.id} type="button" onClick={() => { setSection(n.id); setMobileNav(false); }} style={{ width: '100%', padding: 9, marginBottom: 3, borderRadius: 7, border: `1px solid ${section === n.id ? n.color + '30' : 'rgba(255,255,255,0.05)'}`, background: section === n.id ? `${n.color}0b` : 'transparent', color: section === n.id ? n.color : 'rgba(232,232,232,0.55)', textAlign: 'left', cursor: 'pointer' }}>{n.sigil} {n.label}</button>)}</div>}<main style={{ padding: '14px 16px 60px', position: 'relative', zIndex: 5 }}><SectionHeader item={item} />{content}</main></div><div className="solspire-desktop"><div style={{ display: 'flex', position: 'relative', zIndex: 5 }}><Sidebar section={section} onSection={setSection} /><main style={{ flex: 1, minWidth: 0, padding: '24px 28px 60px' }}><SectionHeader item={item} />{content}</main></div></div><style>{`@media (min-width:1024px){.solspire-mobile{display:none}.solspire-desktop{display:block}}@media (max-width:1023px){.solspire-mobile{display:block}.solspire-desktop{display:none}}`}</style></div>;
}
function SectionHeader({ item }: { item: typeof NAV[number] }) { return <div style={{ marginBottom: 18 }}><div style={{ display: 'flex', alignItems: 'center', gap: 9 }}><span style={{ color: item.color, fontSize: 16 }}>{item.sigil}</span><h2 style={{ fontFamily: 'Cinzel,serif', fontSize: 21, color: item.color, margin: 0, letterSpacing: '0.11em' }}>{item.label.toUpperCase()}</h2></div><div style={{ marginTop: 5, fontFamily: 'sans-serif', fontSize: 10, color: 'rgba(212,223,232,0.3)' }}>{item.sub}</div><div style={{ height: 1, marginTop: 11, background: `linear-gradient(90deg,${item.color}28,transparent)` }} /></div>; }
