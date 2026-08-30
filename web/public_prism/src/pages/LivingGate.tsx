import React, { useEffect, useMemo, useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { AIS_CAPABILITIES, GROVE_DOMAINS } from '../data/spiralGroveCatalog';
import { useAuth } from '../contexts/AuthContext';
import LoginPage from './LoginPage';

export interface AisCapabilityPortfolio {
  version: 1;
  identity: string;
  capabilities: string[];
  builds: string;
  evidence: string;
  projects: string;
  offer: string;
  credentials: string;
  growth: string[];
  completedAt: string;
}

interface DiagnosticHandoff {
  version: 1;
  source: 'future-skills-lab';
  identity: string;
  capabilities: string[];
  builds: string;
  evidence: string;
  projects: string;
  offer: string;
  credentials: string;
  growth: string[];
  researchSignal: string;
  createdAt: string;
}

interface StoredAisProjection {
  kind: 'diagnostic_seed' | 'portfolio';
  profile: DiagnosticHandoff | AisCapabilityPortfolio;
}

interface LivingGateProps {
  onAICComplete?: (seed: AisCapabilityPortfolio) => void;
  onEnterSpiralGrove?: () => void;
}

type StepKey = keyof Pick<AisCapabilityPortfolio, 'identity' | 'capabilities' | 'builds' | 'evidence' | 'projects' | 'offer' | 'credentials' | 'growth'>;

const STEPS: Array<{ key: StepKey; label: string; question: string; helper: string }> = [
  { key: 'identity', label: 'Identity', question: 'Who are you becoming useful as?', helper: 'A role, craft, field, or direction. Keep it simple.' },
  { key: 'capabilities', label: 'Capability Map', question: 'What can you already do?', helper: 'Pick up to 4 capabilities. We will map the rest in Spiral Grove.' },
  { key: 'builds', label: 'Builds', question: 'What have you created?', helper: 'Name one thing you built, made, shipped, repaired, researched, or organized.' },
  { key: 'evidence', label: 'Evidence', question: 'Can you demonstrate it?', helper: 'A link, artifact, result, screenshot, testimony, or working demonstration is enough.' },
  { key: 'projects', label: 'Projects', question: 'Where have you applied it?', helper: 'Tell us where your capability has met a real person, problem, team, business, or community.' },
  { key: 'offer', label: 'Offer', question: 'What value can you provide?', helper: 'Finish: “I help ___ achieve ___ using ___.”' },
  { key: 'credentials', label: 'Credentials', question: 'What have you demonstrated?', helper: 'Certificates are welcome, but practical proof counts too.' },
  { key: 'growth', label: 'Growth Map', question: 'What should you learn next?', helper: 'Choose the direction that feels most useful now. Grove will turn it into a path.' },
];

const QUICK_CAPABILITIES = AIS_CAPABILITIES.map(capability => capability.name).slice(0, 18);
const GROWTH_OPTIONS = GROVE_DOMAINS.map(domain => ({ id: domain.id, label: domain.label }));
const HANDOFF_KEY = 'arkadia.ais.diagnostic-handoff.v1';
const PORTFOLIO_KEY = 'arkadia.ais.capability-portfolio.v1';

const EMPTY: Omit<AisCapabilityPortfolio, 'version' | 'completedAt'> = {
  identity: '', capabilities: [], builds: '', evidence: '', projects: '', offer: '', credentials: '', growth: [],
};

function readDiagnosticHandoff(): DiagnosticHandoff | null {
  try {
    const raw = sessionStorage.getItem(HANDOFF_KEY);
    if (!raw) return null;
    const parsed = JSON.parse(raw) as DiagnosticHandoff;
    return parsed?.version === 1 && parsed?.source === 'future-skills-lab' ? parsed : null;
  } catch { return null; }
}

function readStoredPortfolio(): AisCapabilityPortfolio | null {
  try {
    const raw = sessionStorage.getItem(PORTFOLIO_KEY);
    if (!raw) return null;
    const parsed = JSON.parse(raw) as AisCapabilityPortfolio;
    return parsed?.version === 1 ? parsed : null;
  } catch { return null; }
}

function profileFromHandoff(handoff: DiagnosticHandoff | null): typeof EMPTY {
  if (!handoff) return EMPTY;
  const evidence = [handoff.evidence, handoff.researchSignal ? `Research approach: ${handoff.researchSignal}` : ''].filter(Boolean).join('\n\n');
  return {
    identity: handoff.identity,
    capabilities: handoff.capabilities,
    builds: handoff.builds,
    evidence,
    projects: handoff.projects,
    offer: handoff.offer,
    credentials: handoff.credentials,
    growth: handoff.growth,
  };
}

function profileFromStoredProjection(projection: StoredAisProjection | null): typeof EMPTY {
  if (!projection?.profile) return EMPTY;
  const profile = projection.profile as Partial<AisCapabilityPortfolio> & Partial<DiagnosticHandoff>;
  const evidence = [profile.evidence, 'researchSignal' in profile && profile.researchSignal ? `Research approach: ${profile.researchSignal}` : ''].filter(Boolean).join('\n\n');
  return {
    identity: profile.identity ?? '',
    capabilities: profile.capabilities ?? [],
    builds: profile.builds ?? '',
    evidence,
    projects: profile.projects ?? '',
    offer: profile.offer ?? '',
    credentials: profile.credentials ?? '',
    growth: profile.growth ?? [],
  };
}

const fieldStyle: React.CSSProperties = {
  width: '100%', minHeight: 88, boxSizing: 'border-box', padding: '14px 15px',
  background: 'rgba(255,255,255,0.025)', border: '1px solid rgba(255,255,255,0.09)',
  borderRadius: 11, color: '#E8E8E8', fontFamily: 'sans-serif', fontSize: 13,
  lineHeight: 1.6, outline: 'none', resize: 'vertical',
};

function Pill({ label, active, onClick }: { label: string; active: boolean; onClick: () => void }) {
  return <button type="button" onClick={onClick} style={{ padding: '9px 12px', borderRadius: 20, cursor: 'pointer', background: active ? 'rgba(0,212,170,.12)' : 'rgba(255,255,255,.025)', border: `1px solid ${active ? 'rgba(0,212,170,.5)' : 'rgba(255,255,255,.08)'}`, color: active ? '#00D4AA' : 'rgba(232,232,232,.5)', fontFamily: 'sans-serif', fontSize: 10, letterSpacing: '.05em' }}>{label}</button>;
}

function PortfolioSnapshot({ portfolio, onRetake, onGrove, authenticated, onAuthenticate }: { portfolio: AisCapabilityPortfolio; onRetake: () => void; onGrove?: () => void; authenticated: boolean; onAuthenticate: () => void }) {
  const rows: Array<[string, string | string[]]> = [
    ['Identity', portfolio.identity], ['Capability Map', portfolio.capabilities], ['Builds', portfolio.builds],
    ['Evidence', portfolio.evidence], ['Projects', portfolio.projects], ['Offer', portfolio.offer],
    ['Credentials', portfolio.credentials], ['Growth Map', portfolio.growth],
  ];
  return <motion.div initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} style={{ maxWidth: 620, margin: '0 auto' }}>
    <div style={{ textAlign: 'center', marginBottom: 22 }}>
      <p style={{ fontFamily: 'sans-serif', fontSize: 9, letterSpacing: '.3em', textTransform: 'uppercase', color: 'rgba(0,212,170,.5)', margin: '0 0 7px' }}>A.I.S Capability Portfolio</p>
      <h2 style={{ fontFamily: 'serif', fontSize: 28, fontWeight: 400, color: '#C9A84C', margin: '0 0 8px' }}>Your working profile</h2>
      <p style={{ fontFamily: 'sans-serif', fontSize: 11, lineHeight: 1.65, color: 'rgba(232,232,232,.42)', margin: 0 }}>{authenticated ? 'Your profile is bound to your Arkadia identity. This becomes the starting map for what you can do, prove, offer, and grow.' : 'Your map is ready. Create your free Arkadia identity to keep it and continue into your personalized Grove.'}</p>
    </div>
    <div style={{ display: 'grid', gap: 8, marginBottom: 18 }}>
      {rows.map(([label, value]) => <section key={label} style={{ padding: '13px 15px', background: 'rgba(14,17,32,.72)', border: '1px solid rgba(255,255,255,.07)', borderRadius: 10 }}>
        <p style={{ fontFamily: 'sans-serif', fontSize: 8, letterSpacing: '.22em', textTransform: 'uppercase', color: 'rgba(201,168,76,.55)', margin: '0 0 6px' }}>{label}</p>
        <p style={{ fontFamily: 'sans-serif', fontSize: 12, lineHeight: 1.65, color: 'rgba(232,232,232,.7)', margin: 0 }}>{Array.isArray(value) ? (value.length ? value.join(' · ') : 'Not set yet') : (value || 'Not set yet')}</p>
      </section>)}
    </div>
    <div style={{ display: 'flex', gap: 8 }}>
      <button type="button" onClick={onRetake} style={{ padding: '13px 16px', background: 'rgba(255,255,255,.025)', border: '1px solid rgba(255,255,255,.08)', borderRadius: 10, color: 'rgba(232,232,232,.45)', fontFamily: 'sans-serif', fontSize: 10, cursor: 'pointer' }}>↺ Edit map</button>
      {authenticated && onGrove ? <button type="button" data-testid="open-spiral-grove" onClick={onGrove} style={{ flex: 1, padding: 14, background: 'linear-gradient(135deg, rgba(0,212,170,.16), rgba(0,212,170,.06))', border: '1px solid rgba(0,212,170,.55)', borderRadius: 10, color: '#00D4AA', fontFamily: 'sans-serif', fontSize: 10, letterSpacing: '.18em', textTransform: 'uppercase', cursor: 'pointer' }}>Enter Spiral Grove →</button> : <button type="button" data-testid="bind-ais-profile" onClick={onAuthenticate} style={{ flex: 1, padding: 14, background: 'linear-gradient(135deg, rgba(201,168,76,.16), rgba(201,168,76,.06))', border: '1px solid rgba(201,168,76,.5)', borderRadius: 10, color: '#C9A84C', fontFamily: 'sans-serif', fontSize: 10, letterSpacing: '.18em', textTransform: 'uppercase', cursor: 'pointer' }}>Create free Arkadia profile →</button>}
    </div>
  </motion.div>;
}

export default function LivingGate({ onAICComplete, onEnterSpiralGrove }: LivingGateProps) {
  const { user, isAuthenticated } = useAuth();
  const initialHandoff = readDiagnosticHandoff();
  const storedPortfolio = readStoredPortfolio();
  const [index, setIndex] = useState(storedPortfolio ? 0 : 0);
  const [profile, setProfile] = useState(() => storedPortfolio ? { ...storedPortfolio, completedAt: undefined } as typeof EMPTY : profileFromHandoff(initialHandoff));
  const [complete, setComplete] = useState(Boolean(storedPortfolio));
  const [handoffActive, setHandoffActive] = useState(Boolean(initialHandoff));
  const [showAuth, setShowAuth] = useState(false);
  const step = STEPS[index];
  const progress = Math.round(((index + 1) / STEPS.length) * 100);
  const selectedCapabilities = profile.capabilities;
  const selectedGrowth = profile.growth;

  useEffect(() => {
    let cancelled = false;
    const sync = async () => {
      if (!isAuthenticated || !user?.idToken) return;
      try {
        const pending = readStoredPortfolio();
        const handoff = readDiagnosticHandoff();
        if (pending) {
          await fetch('/api/me/ais-profile', { method: 'PATCH', headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${user.idToken}` }, body: JSON.stringify({ kind: 'portfolio', profile: pending }) });
          return;
        }
        if (handoff) {
          await fetch('/api/me/ais-profile', { method: 'PATCH', headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${user.idToken}` }, body: JSON.stringify({ kind: 'diagnostic_seed', profile: handoff }) });
          return;
        }
        const res = await fetch('/api/me/ais-profile', { headers: { Authorization: `Bearer ${user.idToken}` } });
        if (!res.ok || cancelled) return;
        const data = await res.json() as { profile?: StoredAisProjection | null };
        if (data.profile && !cancelled) {
          setProfile(profileFromStoredProjection(data.profile));
          if (data.profile.kind === 'portfolio') setComplete(true);
        }
      } catch {}
    };
    void sync();
    return () => { cancelled = true; };
  }, [isAuthenticated, user?.idToken]);

  const setText = (key: Exclude<StepKey, 'capabilities' | 'growth'>, value: string) => setProfile(prev => ({ ...prev, [key]: value }));
  const toggleCapability = (value: string) => setProfile(prev => ({ ...prev, capabilities: prev.capabilities.includes(value) ? prev.capabilities.filter(item => item !== value) : prev.capabilities.length >= 4 ? prev.capabilities : [...prev.capabilities, value] }));
  const toggleGrowth = (value: string) => setProfile(prev => ({ ...prev, growth: prev.growth.includes(value) ? prev.growth.filter(item => item !== value) : [...prev.growth, value].slice(0, 2) }));

  const canContinue = useMemo(() => {
    const value = profile[step.key];
    return Array.isArray(value) ? value.length > 0 : value.trim().length > 0;
  }, [profile, step.key]);

  const finish = () => {
    const portfolio: AisCapabilityPortfolio = { version: 1, ...profile, completedAt: new Date().toISOString() };
    try { sessionStorage.setItem(PORTFOLIO_KEY, JSON.stringify(portfolio)); sessionStorage.removeItem(HANDOFF_KEY); } catch {}
    onAICComplete?.(portfolio);
    setComplete(true);
    setHandoffActive(false);
    if (isAuthenticated && user?.idToken) {
      void fetch('/api/me/ais-profile', { method: 'PATCH', headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${user.idToken}` }, body: JSON.stringify({ kind: 'portfolio', profile: portfolio }) });
    }
  };

  const next = () => index === STEPS.length - 1 ? finish() : setIndex(value => value + 1);
  const retake = () => {
    try { sessionStorage.removeItem(HANDOFF_KEY); sessionStorage.removeItem(PORTFOLIO_KEY); } catch {}
    setProfile(EMPTY); setIndex(0); setComplete(false); setHandoffActive(false); setShowAuth(false);
  };

  if (showAuth && !isAuthenticated) return <div className="relative w-full min-h-screen" style={{ background: '#0A0A0F' }}><LoginPage onSuccess={() => setShowAuth(false)} onBack={() => setShowAuth(false)} /></div>;

  if (complete) return <div className="relative w-full min-h-screen flex flex-col items-center px-5 py-8" style={{ background: '#0A0A0F' }}><div className="relative z-10 w-full"><PortfolioSnapshot portfolio={{ version: 1, ...profile, completedAt: readStoredPortfolio()?.completedAt ?? new Date().toISOString() }} onRetake={retake} onGrove={onEnterSpiralGrove} authenticated={isAuthenticated} onAuthenticate={() => setShowAuth(true)} /></div></div>;

  return <div className="relative w-full min-h-screen flex flex-col items-center px-5 py-8" style={{ background: '#0A0A0F' }}>
    <motion.div className="absolute inset-0 pointer-events-none" animate={{ opacity: [0.5, 0.8, 0.5] }} transition={{ duration: 7, repeat: Infinity }} style={{ background: 'radial-gradient(circle at 50% 35%, rgba(0,212,170,.07), transparent 62%)' }} />
    <div className="relative z-10 w-full" style={{ maxWidth: 620 }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'end', marginBottom: 18 }}>
        <div><p style={{ fontFamily: 'sans-serif', fontSize: 9, letterSpacing: '.3em', textTransform: 'uppercase', color: 'rgba(0,212,170,.55)', margin: '0 0 5px' }}>Living Gate · A.I.S Diagnostic</p><h1 style={{ fontFamily: 'serif', fontSize: 29, fontWeight: 400, color: '#E8E8E8', margin: 0 }}>Build your capability profile.</h1></div>
        <span style={{ fontFamily: 'monospace', fontSize: 10, color: 'rgba(232,232,232,.28)' }}>{index + 1}/{STEPS.length}</span>
      </div>
      <p style={{ fontFamily: 'sans-serif', fontSize: 12, lineHeight: 1.65, color: 'rgba(232,232,232,.45)', margin: '0 0 13px' }}>{handoffActive ? 'Your Future Skills Lab work is already in the map. Fill the missing signals, then we will turn it into your A.I.S Capability Portfolio.' : 'Eight quick signals. A practical A.I.S Capability Portfolio. No long questionnaire, no certificate theatre.'}</p>
      <div style={{ height: 2, background: 'rgba(255,255,255,.06)', marginBottom: 24 }}><motion.div animate={{ width: `${progress}%` }} style={{ height: '100%', background: 'linear-gradient(90deg,#00D4AA,#C9A84C)' }} /></div>
      <AnimatePresence mode="wait">
        <motion.section key={step.key} initial={{ opacity: 0, x: 14 }} animate={{ opacity: 1, x: 0 }} exit={{ opacity: 0, x: -14 }} transition={{ duration: .24 }} style={{ padding: 18, background: 'rgba(14,17,32,.68)', border: '1px solid rgba(255,255,255,.07)', borderRadius: 13 }}>
          <p style={{ fontFamily: 'sans-serif', fontSize: 9, letterSpacing: '.22em', textTransform: 'uppercase', color: '#C9A84C', margin: '0 0 7px' }}>{step.label}</p>
          <h2 style={{ fontFamily: 'serif', fontSize: 22, fontWeight: 400, color: '#E8E8E8', margin: '0 0 7px' }}>{step.question}</h2>
          <p style={{ fontFamily: 'sans-serif', fontSize: 10, lineHeight: 1.6, color: 'rgba(232,232,232,.34)', margin: '0 0 16px' }}>{step.helper}</p>
          {step.key === 'capabilities' ? <div style={{ display: 'flex', flexWrap: 'wrap', gap: 7 }}>{QUICK_CAPABILITIES.map(value => <Pill key={value} label={value} active={selectedCapabilities.includes(value)} onClick={() => toggleCapability(value)} />)}</div>
            : step.key === 'growth' ? <div style={{ display: 'flex', flexWrap: 'wrap', gap: 7 }}>{GROWTH_OPTIONS.map(option => <Pill key={option.id} label={option.label} active={selectedGrowth.includes(option.id)} onClick={() => toggleGrowth(option.id)} />)}</div>
            : <textarea autoFocus value={profile[step.key] as string} onChange={event => setText(step.key as Exclude<StepKey, 'capabilities' | 'growth'>, event.target.value)} placeholder="Type a short answer…" style={fieldStyle} />}
        </motion.section>
      </AnimatePresence>
      <div style={{ display: 'flex', gap: 8, marginTop: 12 }}>
        {index > 0 && <button type="button" onClick={() => setIndex(value => value - 1)} style={{ padding: '12px 16px', background: 'rgba(255,255,255,.025)', border: '1px solid rgba(255,255,255,.08)', borderRadius: 10, color: 'rgba(232,232,232,.4)', cursor: 'pointer' }}>←</button>}
        <button type="button" disabled={!canContinue} onClick={next} style={{ flex: 1, padding: 13, background: canContinue ? 'rgba(0,212,170,.1)' : 'rgba(255,255,255,.025)', border: `1px solid ${canContinue ? 'rgba(0,212,170,.45)' : 'rgba(255,255,255,.07)'}`, borderRadius: 10, color: canContinue ? '#00D4AA' : 'rgba(232,232,232,.22)', fontFamily: 'sans-serif', fontSize: 10, letterSpacing: '.18em', textTransform: 'uppercase', cursor: canContinue ? 'pointer' : 'not-allowed' }}>{index === STEPS.length - 1 ? 'Create my capability portfolio' : 'Next →'}</button>
      </div>
      <p style={{ textAlign: 'center', fontFamily: 'sans-serif', fontSize: 9, color: 'rgba(232,232,232,.18)', marginTop: 12 }}>{isAuthenticated ? 'Your A.I.S profile is attached to your canonical Arkadia identity.' : 'Your work stays local until you choose to create a free Arkadia identity.'}</p>
    </div>
  </div>;
}