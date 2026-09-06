import React, { useEffect, useMemo, useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useAuth } from '../contexts/AuthContext';
import { API_BASE } from '../lib/apiConfig';
import LoginPage from './LoginPage';
import { AIS_CAPABILITIES, GROVE_DOMAINS } from '../data/spiralGroveCatalog';
import type { AisCapabilityPortfolio } from './LivingGate';

interface NodeEntryProps {
  onEnterNovaNet: () => void;
  onBack?: () => void;
  onAICComplete?: (portfolio: AisCapabilityPortfolio) => void;
}

type Stage = 'auth' | 'diagnostic' | 'formed';
type StepKey = keyof Pick<AisCapabilityPortfolio, 'identity' | 'capabilities' | 'builds' | 'evidence' | 'projects' | 'offer' | 'credentials' | 'growth'>;

type Step = { key: StepKey; label: string; question: string; helper: string; reflect: string };

const STEPS: Step[] = [
  { key: 'identity', label: 'ARRIVAL', question: 'What brings you to Arkadia?', helper: 'Tell us what you are building, exploring, solving, or trying to understand right now. A sentence is enough.', reflect: 'Good. That gives us a place to begin.' },
  { key: 'capabilities', label: 'MIND + CRAFT', question: 'What are you naturally good at?', helper: 'Pick up to four things people rely on you for. We will keep learning the shape of your capability in Spiral Grove.', reflect: 'Interesting. We can use those as your first capability signals.' },
  { key: 'builds', label: 'MAKING', question: 'What have you made real?', helper: 'Name one thing you built, made, shipped, repaired, researched, organised, or brought to life.', reflect: 'That is useful evidence. Arkadia will remember the work, not just the claim.' },
  { key: 'evidence', label: 'EVIDENCE', question: 'How could someone see it?', helper: 'A link, artifact, result, screenshot, testimony, or working demonstration is enough. If there is no link, just describe it.', reflect: 'Perfect. Proof can take many forms.' },
  { key: 'projects', label: 'APPLICATION', question: 'Where has your capability met the real world?', helper: 'Tell us about a person, problem, team, business, community, or project where you have applied it.', reflect: 'Now we have context, not just credentials.' },
  { key: 'offer', label: 'VALUE', question: 'What value can you bring?', helper: 'Complete this naturally: “I help ___ achieve ___ using ___.” Or say it your own way.', reflect: 'That helps us understand the value you want to create.' },
  { key: 'credentials', label: 'PROOF', question: 'What have you demonstrated?', helper: 'Certificates are welcome, but practical proof counts too. Tell us what you have actually demonstrated.', reflect: 'Good. Demonstrated capability will matter more than labels.' },
  { key: 'growth', label: 'BECOMING', question: 'What are you becoming?', helper: 'Choose up to two directions you want to grow into next. Spiral Grove will use them as your first learning horizon.', reflect: 'That gives your node a direction, not just a history.' },
];

const QUICK_CAPABILITIES = AIS_CAPABILITIES.map(c => c.name).slice(0, 18);
const GROWTH_OPTIONS = GROVE_DOMAINS.map(d => ({ id: d.id, label: d.label }));
const AIS_PROFILE_URL = `${API_BASE.replace(/\/$/, '')}/api/me/ais-profile`;

const EMPTY: Omit<AisCapabilityPortfolio, 'version' | 'completedAt'> = {
  identity: '', capabilities: [], builds: '', evidence: '', projects: '', offer: '', credentials: '', growth: [],
};

export default function NodeEntry({ onEnterNovaNet, onBack, onAICComplete }: NodeEntryProps) {
  const { user, isAuthenticated, profile, loading } = useAuth();
  const [stage, setStage] = useState<Stage>(isAuthenticated ? 'diagnostic' : 'auth');
  const [checkingIdentity, setCheckingIdentity] = useState(false);
  const [index, setIndex] = useState(0);
  const [form, setForm] = useState(EMPTY);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    if (loading) return;
    if (!isAuthenticated || !user?.idToken) {
      setStage('auth');
      return;
    }
    let cancelled = false;
    const resolveNode = async () => {
      setCheckingIdentity(true);
      try {
        const response = await fetch(AIS_PROFILE_URL, { headers: { Authorization: `Bearer ${user.idToken}` } });
        if (!response.ok) { if (!cancelled) setStage('diagnostic'); return; }
        const data = await response.json() as { profile?: { kind?: string; profile?: AisCapabilityPortfolio } | null };
        if (!cancelled) {
          if (data.profile?.kind === 'portfolio' && data.profile.profile) {
            setForm({ ...EMPTY, ...data.profile.profile });
            setStage('formed');
          } else setStage('diagnostic');
        }
      } catch {
        if (!cancelled) setStage('diagnostic');
      } finally {
        if (!cancelled) setCheckingIdentity(false);
      }
    };
    void resolveNode();
    return () => { cancelled = true; };
  }, [loading, isAuthenticated, user?.idToken]);

  const step = STEPS[index];
  const value = form[step.key];
  const progress = Math.round(((index + 1) / STEPS.length) * 100);
  const canContinue = Array.isArray(value) ? value.length > 0 : value.trim().length > 0;
  const displayName = profile?.display_name || user?.displayName || user?.email?.split('@')[0] || 'Node';

  const setText = (key: Exclude<StepKey, 'capabilities' | 'growth'>, next: string) => setForm(prev => ({ ...prev, [key]: next }));
  const toggle = (key: 'capabilities' | 'growth', item: string, max: number) => setForm(prev => {
    const current = prev[key];
    return { ...prev, [key]: current.includes(item) ? current.filter(x => x !== item) : current.length >= max ? current : [...current, item] };
  });

  const finish = async () => {
    if (!user?.idToken) return;
    setSaving(true);
    const portfolio: AisCapabilityPortfolio = { version: 1, ...form, completedAt: new Date().toISOString() };
    try {
      const res = await fetch(AIS_PROFILE_URL, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${user.idToken}` },
        body: JSON.stringify({ kind: 'portfolio', profile: portfolio }),
      });
      if (!res.ok) throw new Error('Could not save your node seed.');
      onAICComplete?.(portfolio);
      setForm({ ...EMPTY, ...portfolio });
      setStage('formed');
    } catch {
      // Keep the completed answers on screen. The user can try the final step again.
    } finally {
      setSaving(false);
    }
  };

  if (stage === 'auth') {
    return <div className="relative w-full min-h-screen" style={{ background: '#0A0A0F' }}><LoginPage onSuccess={() => setStage('diagnostic')} onBack={onBack} /></div>;
  }

  if (checkingIdentity) {
    return <div className="relative w-full min-h-screen flex items-center justify-center" style={{ background: '#0A0A0F' }}><p style={{ fontFamily: 'ui-monospace, monospace', fontSize: 9, letterSpacing: '.28em', textTransform: 'uppercase', color: 'rgba(0,212,170,.65)' }}>Recognising your node…</p></div>;
  }

  if (stage === 'formed') {
    return (
      <div className="relative w-full min-h-screen flex items-center justify-center px-5 py-12" style={{ background: '#0A0A0F' }}>
        <div className="absolute inset-0 pointer-events-none" style={{ background: 'radial-gradient(circle at 50% 42%, rgba(0,212,170,.09), transparent 58%)' }} />
        <motion.div initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }} className="relative z-10 w-full" style={{ maxWidth: 620, textAlign: 'center' }}>
          <div style={{ width: 76, height: 76, margin: '0 auto 18px', display: 'grid', placeItems: 'center', borderRadius: '50%', border: '1px solid rgba(201,168,76,.5)', color: '#C9A84C', fontSize: 34, boxShadow: '0 0 48px rgba(201,168,76,.1)' }}>◈</div>
          <p style={{ fontFamily: 'ui-monospace, monospace', fontSize: 9, letterSpacing: '.34em', textTransform: 'uppercase', color: 'rgba(0,212,170,.7)', margin: '0 0 10px' }}>Identity Resolved · A.I.S Complete</p>
          <h1 style={{ fontFamily: 'serif', fontSize: 42, fontWeight: 400, color: '#C9A84C', margin: '0 0 10px' }}>NODE FORMED</h1>
          <p style={{ fontFamily: 'serif', fontSize: 16, lineHeight: 1.7, color: 'rgba(232,232,232,.68)', maxWidth: 490, margin: '0 auto 8px' }}>Welcome, {displayName}. Your first identity seed is alive.</p>
          <p style={{ fontFamily: 'sans-serif', fontSize: 11, lineHeight: 1.7, color: 'rgba(232,232,232,.4)', maxWidth: 480, margin: '0 auto 26px' }}>This seed is the baseline for your capability map, Personal Codex, EchoField, ReasoMate relationship and future Arkadia continuity. It can evolve as you do.</p>
          <button type="button" onClick={onEnterNovaNet} data-testid="enter-novanet" style={{ width: '100%', maxWidth: 460, padding: '16px 20px', background: 'linear-gradient(135deg, rgba(0,212,170,.16), rgba(106,159,216,.08))', border: '1px solid rgba(0,212,170,.5)', borderRadius: 11, color: '#00D4AA', fontFamily: 'sans-serif', fontSize: 10, letterSpacing: '.24em', textTransform: 'uppercase', cursor: 'pointer' }}>Enter NovaNet →</button>
        </motion.div>
      </div>
    );
  }

  return (
    <div className="relative w-full min-h-screen flex flex-col items-center px-5 py-10" style={{ background: '#0A0A0F' }}>
      <div className="absolute inset-0 pointer-events-none" style={{ background: 'radial-gradient(circle at 50% 12%, rgba(0,212,170,.08), transparent 52%)' }} />
      <div className="relative z-10 w-full" style={{ maxWidth: 650 }}>
        <div style={{ textAlign: 'center', marginBottom: 26 }}>
          <p style={{ fontFamily: 'ui-monospace, monospace', fontSize: 9, letterSpacing: '.34em', textTransform: 'uppercase', color: 'rgba(0,212,170,.68)', margin: '0 0 10px' }}>WELCOME TO ARKADIA</p>
          <h1 style={{ fontFamily: 'serif', fontSize: 36, fontWeight: 400, color: '#C9A84C', margin: '0 0 9px' }}>Let's form your node.</h1>
          <p style={{ fontFamily: 'sans-serif', fontSize: 11.5, lineHeight: 1.7, color: 'rgba(232,232,232,.48)', maxWidth: 500, margin: '0 auto' }}>A few questions. A couple of minutes. No perfect answers. Give us the first thing that feels true.</p>
        </div>

        <div style={{ marginBottom: 22 }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 7, fontFamily: 'ui-monospace, monospace', fontSize: 8, letterSpacing: '.2em', textTransform: 'uppercase', color: 'rgba(232,232,232,.28)' }}><span>{step.label}</span><span>{index + 1} / {STEPS.length}</span></div>
          <div style={{ height: 3, borderRadius: 3, background: 'rgba(255,255,255,.06)', overflow: 'hidden' }}><motion.div animate={{ width: `${progress}%` }} style={{ height: '100%', background: 'linear-gradient(90deg, #00D4AA, #C9A84C)' }} /></div>
        </div>

        <AnimatePresence mode="wait">
          <motion.section key={step.key} initial={{ opacity: 0, x: 14 }} animate={{ opacity: 1, x: 0 }} exit={{ opacity: 0, x: -14 }} transition={{ duration: .2 }} style={{ padding: 20, borderRadius: 15, border: '1px solid rgba(255,255,255,.08)', background: 'rgba(14,17,32,.68)' }}>
            <p style={{ margin: '0 0 8px', fontFamily: 'ui-monospace, monospace', fontSize: 8, letterSpacing: '.26em', textTransform: 'uppercase', color: 'rgba(0,212,170,.58)' }}>I'm listening.</p>
            <h2 style={{ margin: '0 0 10px', fontFamily: 'serif', fontSize: 26, fontWeight: 400, color: '#E8E8E8', lineHeight: 1.3 }}>{step.question}</h2>
            <p style={{ margin: '0 0 18px', fontFamily: 'sans-serif', fontSize: 11.5, lineHeight: 1.7, color: 'rgba(232,232,232,.43)' }}>{step.helper}</p>

            {step.key === 'capabilities' ? (
              <div style={{ display: 'flex', gap: 7, flexWrap: 'wrap' }}>{QUICK_CAPABILITIES.map(item => <button key={item} type="button" onClick={() => toggle('capabilities', item, 4)} style={{ padding: '8px 11px', borderRadius: 18, cursor: 'pointer', background: form.capabilities.includes(item) ? 'rgba(0,212,170,.12)' : 'rgba(255,255,255,.025)', border: `1px solid ${form.capabilities.includes(item) ? 'rgba(0,212,170,.5)' : 'rgba(255,255,255,.08)'}`, color: form.capabilities.includes(item) ? '#00D4AA' : 'rgba(232,232,232,.48)', fontFamily: 'sans-serif', fontSize: 9.5 }}>{item}</button>)}</div>
            ) : step.key === 'growth' ? (
              <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>{GROWTH_OPTIONS.map(item => <button key={item.id} type="button" onClick={() => toggle('growth', item.label, 2)} style={{ flex: '1 1 180px', textAlign: 'left', padding: '11px 12px', borderRadius: 10, cursor: 'pointer', background: form.growth.includes(item.label) ? 'rgba(176,141,232,.11)' : 'rgba(255,255,255,.025)', border: `1px solid ${form.growth.includes(item.label) ? 'rgba(176,141,232,.5)' : 'rgba(255,255,255,.08)'}`, color: form.growth.includes(item.label) ? '#B08DE8' : 'rgba(232,232,232,.48)', fontFamily: 'sans-serif', fontSize: 10 }}>{item.label}</button>)}</div>
            ) : (
              <textarea autoFocus value={String(value)} onChange={e => setText(step.key as Exclude<StepKey, 'capabilities' | 'growth'>, e.target.value)} onKeyDown={e => { if (e.key === 'Enter' && (e.ctrlKey || e.metaKey)) { e.preventDefault(); if (canContinue) void (index === STEPS.length - 1 ? finish() : setIndex(i => i + 1)); } }} placeholder="Just say it naturally…" style={{ width: '100%', minHeight: 125, boxSizing: 'border-box', padding: '14px 15px', resize: 'vertical', borderRadius: 11, outline: 'none', background: 'rgba(255,255,255,.025)', border: '1px solid rgba(255,255,255,.09)', color: '#E8E8E8', fontFamily: 'sans-serif', fontSize: 13, lineHeight: 1.65 }} />
            )}

            <div style={{ marginTop: 18, display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 10 }}>
              <button type="button" onClick={() => index === 0 ? onBack?.() : setIndex(i => i - 1)} style={{ padding: '11px 13px', border: 'none', background: 'transparent', color: 'rgba(232,232,232,.3)', fontFamily: 'sans-serif', fontSize: 10, cursor: 'pointer' }}>{index === 0 ? '← Back' : '← Previous'}</button>
              <p style={{ margin: 0, flex: 1, textAlign: 'center', fontFamily: 'serif', fontSize: 11, color: 'rgba(232,232,232,.28)' }}>{step.reflect}</p>
              <button type="button" disabled={!canContinue || saving} onClick={() => void (index === STEPS.length - 1 ? finish() : setIndex(i => i + 1))} style={{ padding: '12px 18px', borderRadius: 10, border: `1px solid ${canContinue ? 'rgba(0,212,170,.5)' : 'rgba(255,255,255,.08)'}`, background: canContinue ? 'rgba(0,212,170,.1)' : 'rgba(255,255,255,.02)', color: canContinue ? '#00D4AA' : 'rgba(232,232,232,.25)', fontFamily: 'sans-serif', fontSize: 10, letterSpacing: '.15em', textTransform: 'uppercase', cursor: canContinue && !saving ? 'pointer' : 'not-allowed' }}>{saving ? 'Forming…' : index === STEPS.length - 1 ? 'Form my node →' : 'Continue →'}</button>
            </div>
          </motion.section>
        </AnimatePresence>

        <p style={{ margin: '16px 0 0', textAlign: 'center', fontFamily: 'ui-monospace, monospace', fontSize: 8.5, letterSpacing: '.14em', color: 'rgba(232,232,232,.22)' }}>Your answers become the seed. Your future experience becomes the evidence.</p>
      </div>
    </div>
  );
}
