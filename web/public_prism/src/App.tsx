import React, { useEffect, useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { AuthProvider, useAuth } from './contexts/AuthContext';
import ArkadiaNavigation from './components/ArkadiaNavigation';
import NodeEntry from './pages/NodeEntry';
import FutureSkillsChallenge from './pages/FutureSkillsChallenge';
import ArkanaCommune from './components/ArkanaCommune';
import CoherenceReset from './pages/CoherenceReset';
import AboutArkadia from './pages/AboutArkadia';
import NexusSpiralCodex from './pages/NexusSpiralCodex';
import SpiralCodexFeed from './pages/SpiralCodexFeed';
import SpiralGrovePage from './pages/SpiralGrovePage';
import LivingLarderPage from './pages/LivingLarderPage';
import IMSArchivePage from './pages/IMSArchivePage';
import NovaNetPage from './pages/NovaNetPage';
import SonataBar from './components/SonataBar';
import DistributePage from './pages/DistributePage';
import OfferingsPage from './pages/OfferingsPage';
import ArkadianPulse from './pages/ArkadianPulse';
import SettingsPage from './pages/SettingsPage';
import AccountPage from './pages/AccountPage';
import SolSpireConsole from './pages/SolSpireConsole';
import ReasoMatePage from './pages/ReasoMatePage';
import SpiralCommandInterface from './pages/SpiralCommandInterface';
import UniversalEchofeildMatrix from './pages/UniversalEchofeildMatrix';

type SolSpireLens = 'overview'|'projects'|'commercial'|'knowledge'|'files'|'conversations'|'tasks'|'memory'|'weaver'|'observatory'|'engineering-lab'|'settings';
type View =
  | 'home' | 'gate' | 'commune' | 'reset' | 'about' | 'login' | 'codex' | 'dashboard'
  | 'nexus' | 'encyclopedia' | 'spiral-codex' | 'loops' | 'grove' | 'larder' | 'novanet'
  | 'ims' | 'distribute' | 'offerings' | 'aic' | 'pulse' | 'settings' | 'account' | 'sci' | 'solspire'
  | 'knowledge-os' | 'reasomate' | 'personal-echofeild' | 'echofeild-matrix' | 'challenge';

type RouteState = { view: View; section?: SolSpireLens; path: string };
const SOLSPIRE_LENSES = new Set<SolSpireLens>(['overview','projects','commercial','knowledge','files','conversations','tasks','memory','weaver','observatory','engineering-lab','settings']);

function routeForView(view: View, section?: SolSpireLens): string {
  if (view === 'solspire') return section && section !== 'overview' ? `/solspire/${section}` : '/solspire';
  const routes: Partial<Record<View, string>> = {
    home: '/', gate: '/living-gate', commune: '/oracle', about: '/about', login: '/login',
    novanet: '/nexus', ims: '/nexus/ims', grove: '/nexus/grove', larder: '/nexus/larder', distribute: '/nexus/distribution', encyclopedia: '/encyclopedia', 'spiral-codex': '/spiral-codex',
    offerings: '/offerings', challenge: '/future-skills', reset: '/reset', pulse: '/pulse',
  };
  return routes[view] || '/';
}

function resolvePath(pathname: string): RouteState {
  const path = pathname.replace(/\/+$/, '') || '/';
  const solspire = path.match(/^\/solspire(?:\/([^/]+))?$/);
  if (solspire) {
    const candidate = solspire[1] as SolSpireLens | undefined;
    return { view: 'solspire', section: candidate && SOLSPIRE_LENSES.has(candidate) ? candidate : 'overview', path: routeForView('solspire', candidate && SOLSPIRE_LENSES.has(candidate) ? candidate : 'overview') };
  }
  const compatibility: Record<string, { view: View; section?: SolSpireLens }> = {
    '/codex': {view:'solspire',section:'knowledge'}, '/knowledge-os': {view:'solspire',section:'knowledge'},
    '/loops': {view:'solspire',section:'tasks'}, '/dashboard': {view:'solspire',section:'overview'},
    '/personal-echofeild': {view:'solspire',section:'observatory'}, '/echofeild-matrix': {view:'solspire',section:'observatory'},
    '/settings': {view:'solspire',section:'settings'}, '/account': {view:'solspire',section:'settings'},
    '/sci': {view:'solspire',section:'weaver'}, '/reasomate': {view:'commune'},
    
  };
  if (compatibility[path]) {
    const target = compatibility[path];
    return {...target, path: routeForView(target.view, target.section)};
  }
  const direct: Record<string, View> = {
    '/': 'home', '/home': 'home', '/living-gate': 'gate', '/gate': 'gate', '/oracle': 'commune', '/commune': 'commune',
    '/about': 'about', '/login': 'login', '/nexus': 'novanet', '/nexus/ims': 'ims', '/nexus/grove': 'grove', '/nexus/larder': 'larder',
    '/nexus/distribution': 'distribute', '/encyclopedia': 'encyclopedia', '/spiral-codex': 'spiral-codex', '/offerings': 'offerings', '/future-skills': 'challenge', '/challenge': 'challenge',
    '/reset': 'reset', '/pulse': 'pulse',
  };
  const view = direct[path] || 'home';
  return {view, path: routeForView(view)};
}

function FieldPulse() {
  const [tick, setTick] = useState(0);
  useEffect(() => { const t = setInterval(() => setTick(n => n + 1), 3000); return () => clearInterval(t); }, []);
  return <div style={{ display: 'inline-flex', alignItems: 'center', gap: '8px', padding: '7px 14px', background: 'rgba(0,212,170,0.04)', border: '1px solid rgba(0,212,170,0.12)', borderRadius: '20px', position: 'relative' }}><div style={{ position: 'relative', width: '7px', height: '7px' }}><motion.div key={tick} initial={{ scale: 0.6, opacity: 0.8 }} animate={{ scale: 2.2, opacity: 0 }} transition={{ duration: 1.4, ease: 'easeOut' }} style={{ position: 'absolute', inset: 0, borderRadius: '50%', backgroundColor: '#00D4AA' }} /><div style={{ position: 'absolute', inset: 0, borderRadius: '50%', backgroundColor: '#00D4AA' }} /></div><p style={{ fontFamily: 'sans-serif', fontSize: '9px', letterSpacing: '0.22em', textTransform: 'uppercase', color: 'rgba(0,212,170,0.55)', margin: 0 }}>Field Active · 117 Hz · Jos Node 1759</p></div>;
}
function PortalDoor({ label, sub, color, sigil, onClick, delay }: { label: string; sub: string; color: string; sigil: string; onClick: () => void; delay: number }) {
  const [hovered, setHovered] = useState(false);
  return <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ delay, duration: 0.55 }} onClick={onClick} onMouseEnter={() => setHovered(true)} onMouseLeave={() => setHovered(false)} style={{ padding: '14px 16px', background: hovered ? 'rgba(14,17,32,0.92)' : 'rgba(14,17,32,0.72)', border: `1px solid ${hovered ? color + '55' : 'rgba(0,212,170,0.16)'}`, borderRadius: '10px', cursor: 'pointer', transition: 'all 0.22s', display: 'flex', alignItems: 'center', gap: '13px' }}><span style={{ fontSize: '16px', flexShrink: 0, width: '24px', textAlign: 'center' }}>{sigil}</span><div style={{ flex: 1 }}><p style={{ fontFamily: 'sans-serif', fontSize: '10px', letterSpacing: '0.22em', textTransform: 'uppercase', color: hovered ? color : 'rgba(232,232,232,0.72)', margin: '0 0 3px', fontWeight: 500 }}>{label}</p><p style={{ fontFamily: 'sans-serif', fontSize: '11px', color: 'rgba(232,232,232,0.38)', margin: 0, lineHeight: 1.4 }}>{sub}</p></div><span style={{ color: hovered ? color : 'rgba(255,255,255,0.22)', fontSize: '11px' }}>&gt;</span></motion.div>;
}
function Home({ onNavigate }: { onNavigate: (v: View) => void }) {
  const { isAuthenticated } = useAuth();
  return <div className="min-h-screen w-full relative"><div className="aurora-bg" /><div className="page-column relative z-10 pt-10 pb-16 flex flex-col"><div style={{ marginBottom: '26px', display: 'flex', justifyContent: 'center' }}><FieldPulse /></div><h1 style={{ fontFamily: 'serif', fontSize: '52px', letterSpacing: '0.18em', textAlign: 'center', color: '#C9A84C', marginBottom: '10px', lineHeight: 1 }}>ARKADIA</h1><p style={{ fontFamily: 'serif', fontSize: '17px', lineHeight: '1.5', color: 'rgba(232,232,232,0.78)', margin: '0 0 22px', textAlign: 'center', maxWidth: '28em', alignSelf: 'center' }}>{isAuthenticated ? 'Your private workspace is open — conversations, notes, and projects stay with you.' : 'A place to think, remember, and build — with AI that keeps your thread.'}</p><div style={{ marginBottom: '10px' }}><button onClick={() => onNavigate(isAuthenticated ? 'solspire' : 'gate')} data-testid="button-home-oracle" style={{ width: '100%', padding: '17px', background: 'linear-gradient(135deg, rgba(0,212,170,0.16), rgba(0,212,170,0.06))', border: '1px solid rgba(0,212,170,0.5)', borderRadius: '11px', color: '#00D4AA', fontFamily: 'sans-serif', fontSize: '11px', letterSpacing: '0.22em', textTransform: 'uppercase', cursor: 'pointer' }}>{isAuthenticated ? 'Open SolSpire' : 'Enter Arkadia'}</button></div><div style={{ marginBottom: '18px' }}><button onClick={() => onNavigate(isAuthenticated ? 'solspire' : 'gate')} data-testid="button-home-private" style={{ width: '100%', padding: '13px', background: 'rgba(14,17,32,0.55)', border: '1px solid rgba(201,168,76,0.28)', borderRadius: '11px', color: 'rgba(201,168,76,0.85)', fontFamily: 'sans-serif', fontSize: '10px', letterSpacing: '0.2em', textTransform: 'uppercase', cursor: 'pointer' }}>{isAuthenticated ? 'Open your private field' : 'Sign in / Create Node'}</button></div><div style={{ display: 'flex', flexDirection: 'column', gap: '6px', marginBottom: '30px' }}><PortalDoor label="SolSpire" sub="Private workspace · projects · knowledge · memory · Weaver" color="#C9A84C" sigil="◈" onClick={() => onNavigate(isAuthenticated ? 'solspire' : 'gate')} delay={1.12} /><PortalDoor label="Nexus Hub" sub="NovaNet · Grove · Larder · IMS · Distribution" color="#6A9FD8" sigil="◉" onClick={() => onNavigate(isAuthenticated ? 'novanet' : 'gate')} delay={1.13} /><PortalDoor label="Oracle" sub="ARKANA · Pattern intelligence · Live commune" color="#00D4AA" sigil="✧" onClick={() => onNavigate(isAuthenticated ? 'commune' : 'gate')} delay={1.14} /><PortalDoor label="Offerings" sub="IMS Sessions · Products · AIC Diagnostic" color="#00D4AA" sigil="✦" onClick={() => onNavigate('offerings')} delay={1.15} /><PortalDoor label="Future Skills Lab" sub="Free 60-minute practical capability challenge" color="#00D4AA" sigil="→" onClick={() => onNavigate('challenge')} delay={1.16} /><PortalDoor label="About" sub="Lineage · architecture · principles" color="#6A9FD8" sigil="A" onClick={() => onNavigate('about')} delay={1.17} /></div>{!isAuthenticated && <div style={{ marginBottom: '16px', textAlign: 'center' }}><button onClick={() => onNavigate('gate')} style={{ background: 'none', border: 'none', color: 'rgba(0,212,170,0.35)', fontFamily: 'sans-serif', fontSize: '10px', letterSpacing: '0.18em', textTransform: 'uppercase', cursor: 'pointer' }} data-testid="button-home-login">Sign in / create your node</button></div>}</div></div>;
}

function AppInner() {
  const initial = resolvePath(window.location.pathname);
  const [view, setView] = useState<View>(initial.view);
  const [solspireSection, setSolspireSection] = useState<SolSpireLens>(initial.section || 'overview');
  const [soulPhrase, setSoulPhrase] = useState<string | undefined>(undefined);
  const [aicSeed, setAicSeed] = useState<any>(null);
  const wrap = { minHeight: 'calc(100vh - 57px)', padding: '28px 16px 60px' };

  useEffect(() => {
    if (window.location.pathname !== initial.path) window.history.replaceState({}, '', initial.path);
    const onPopState = () => {
      const next = resolvePath(window.location.pathname);
      setView(next.view);
      setSolspireSection(next.section || 'overview');
      setSoulPhrase(undefined);
    };
    window.addEventListener('popstate', onPopState);
    return () => window.removeEventListener('popstate', onPopState);
  }, [initial.path]);

  const handleNavigate = (requested: View) => {
    if (requested !== 'commune') setSoulPhrase(undefined);
    let next: RouteState = { view: requested, path: routeForView(requested) };
    if (requested === 'nexus') next = {view:'novanet',path:'/nexus'};
    if (requested === 'knowledge-os' || requested === 'codex') next = {view:'solspire',section:'knowledge',path:'/solspire/knowledge'};
    if (requested === 'loops') next = {view:'solspire',section:'tasks',path:'/solspire/tasks'};
    if (requested === 'dashboard') next = {view:'solspire',section:'overview',path:'/solspire'};
    if (requested === 'personal-echofeild' || requested === 'echofeild-matrix') next = {view:'solspire',section:'observatory',path:'/solspire/observatory'};
    if (requested === 'settings' || requested === 'account') next = {view:'solspire',section:'settings',path:'/solspire/settings'};
    if (requested === 'sci') next = {view:'solspire',section:'weaver',path:'/solspire/weaver'};
    if (requested === 'reasomate') next = {view:'commune',path:'/oracle'};
    setView(next.view);
    setSolSpireSection(next.section || 'overview');
    if (window.location.pathname !== next.path) window.history.pushState({}, '', next.path);
  };

  return <ArkadiaNavigation currentView={view} onNavigate={handleNavigate}><SonataBar /><AnimatePresence mode="wait">
    {view === 'home' && <motion.div key="home" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} transition={{ duration: 0.45 }}><Home onNavigate={handleNavigate} /></motion.div>}
    {view === 'gate' && <motion.div key="gate" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} transition={{ duration: 0.45 }}><NodeEntry onEnterNovaNet={() => handleNavigate('novanet')} onGoToOfferings={() => handleNavigate('offerings')} onBack={() => handleNavigate('home')} onAICComplete={setAicSeed} /></motion.div>}
    {view === 'challenge' && <motion.div key="challenge" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} transition={{ duration: 0.45 }}><FutureSkillsChallenge onNavigate={handleNavigate} /></motion.div>}
    {view === 'commune' && <motion.div key="commune" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} transition={{ duration: 0.38 }}><ArkanaCommune initialMessage={soulPhrase} /></motion.div>}
    {view === 'reset' && <motion.div key="reset" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} transition={{ duration: 0.45 }} style={wrap}><CoherenceReset /></motion.div>}
    {view === 'encyclopedia' && <motion.div key="encyclopedia" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} transition={{ duration: 0.45 }}><NexusSpiralCodex initialMode="scrolls" /></motion.div>}
    {view === 'spiral-codex' && <motion.div key="spiral-codex" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} transition={{ duration: 0.45 }}><SpiralCodexFeed onBack={() => handleNavigate('solspire')} /></motion.div>}
    {view === 'grove' && <motion.div key="grove" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} transition={{ duration: 0.45 }} style={wrap}><SpiralGrovePage /></motion.div>}
    {view === 'larder' && <motion.div key="larder" initial={{ opacity: 1 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} transition={{ duration: 0.45 }} style={wrap}><LivingLarderPage /></motion.div>}
    {view === 'ims' && <motion.div key="ims" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} transition={{ duration: 0.45 }} style={wrap}><IMSArchivePage /></motion.div>}
    {view === 'novanet' && <motion.div key="novanet" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} transition={{ duration: 0.45 }} style={wrap}><NovaNetPage /></motion.div>}
    {view === 'distribute' && <motion.div key="distribute" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} transition={{ duration: 0.45 }} style={wrap}><DistributePage /></motion.div>}
    {view === 'offerings' && <motion.div key="offerings" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} transition={{ duration: 0.45 }}><OfferingsPage onGoToAIC={() => handleNavigate('gate')} onGoToChallenge={() => handleNavigate('challenge')} aicSeed={aicSeed} /></motion.div>}
    {view === 'aic' && <motion.div key="aic" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} transition={{ duration: 0.45 }}><NodeEntry onEnterNovaNet={() => handleNavigate('novanet')} onGoToOfferings={() => handleNavigate('offerings')} onBack={() => handleNavigate('offerings')} onAICComplete={setAicSeed} /></motion.div>}
    {view === 'about' && <motion.div key="about" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} transition={{ duration: 0.45 }} style={wrap}><AboutArkadia /></motion.div>}
    {view === 'login' && <motion.div key="login" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} transition={{ duration: 0.45 }}><NodeEntry onEnterNovaNet={() => handleNavigate('novanet')} onGoToOfferings={() => handleNavigate('offerings')} onBack={() => handleNavigate('home')} onAICComplete={setAicSeed} /></motion.div>}
    {view === 'codex' && <motion.div key="codex" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} transition={{ duration: 0.35 }}><SolSpireConsole onNavigate={handleNavigate} initialSection="knowledge" /></motion.div>}
    {view === 'pulse' && <motion.div key="pulse" initial={{ opacity: 1 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} transition={{ duration: 0.45 }} style={wrap}><ArkadianPulse /></motion.div>}
    {view === 'settings' && <motion.div key="settings" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} transition={{ duration: 0.35 }} style={wrap}><SolSpireConsole onNavigate={handleNavigate} initialSection="settings" /></motion.div>}
    {view === 'account' && <motion.div key="account" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} transition={{ duration: 0.35 }}><SolSpireConsole onNavigate={handleNavigate} initialSection="settings" /></motion.div>}
    {view === 'sci' && <motion.div key="sci" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} transition={{ duration: 0.35 }}><SolSpireConsole onNavigate={handleNavigate} initialSection="weaver" /></motion.div>}
    {view === 'solspire' && <motion.div key={`solspire-${solspireSection}`} initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} transition={{ duration: 0.35 }}><SolSpireConsole onNavigate={handleNavigate} initialSection={solspireSection} /></motion.div>}
    {view === 'knowledge-os' && <motion.div key="knowledge-os" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} transition={{ duration: 0.35 }}><SolSpireConsole onNavigate={handleNavigate} initialSection="knowledge" /></motion.div>}
    {view === 'reasomate' && <motion.div key="reasomate" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} transition={{ duration: 0.35 }}><ReasoMatePage /></motion.div>}
    {view === 'personal-echofeild' && <motion.div key="personal-echofeild" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} transition={{ duration: 0.35 }}><UniversalEchofeildMatrix onNavigate={handleNavigate} /></motion.div>}
    {view === 'echofeild-matrix' && <motion.div key="echofeild-matrix" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} transition={{ duration: 0.35 }}><UniversalEchofeildMatrix onNavigate={handleNavigate} /></motion.div>}
  </AnimatePresence></ArkadiaNavigation>;
}
function App() { return <AuthProvider><AppInner /></AuthProvider>; }
export default App;