import { apiFetch } from '../lib/apiClient';
import React, { useEffect, useMemo, useState } from 'react';
import { motion } from 'framer-motion';
import { useAuth } from '../contexts/AuthContext';

interface IdentitySpine {
  version: number;
  identity: {
    uid: string;
    canonical_name: string;
    preferred_name: string;
    username?: string | null;
    role: string;
    role_sigil: string;
    ims_id?: string | null;
  };
  capability: {
    baseline: {
      identity: string;
      capabilities: string[];
      builds: string;
      evidence: string;
      projects: string;
      offer: string;
      credentials: string;
      growth: string[];
    };
    evidence_count: number;
    development_events: Array<Record<string, unknown>>;
    last_assessed_at?: string | null;
  };
  relationship: {
    preferred_ai_role?: string | null;
    communication_preference?: string | null;
    collaboration_preference?: string | null;
  };
  relational_index: {
    version: number;
    status: string;
    score?: number | null;
    confidence: number;
    dimensions: Record<string, number | null>;
    observations: string[];
    last_evaluated_at?: string | null;
  };
  symbolic: {
    seed_phrase?: string | null;
    seed_symbols: string[];
    sigil_seed: string;
    resonance_signature?: string | null;
  };
  provenance: {
    ais_version?: number | null;
    seed_created_at?: string | null;
    last_reconciled_at?: string | null;
    schema_version: number;
  };
}

const C = {
  gold: '#C9A84C',
  teal: '#00D4AA',
  blue: '#6A9FD8',
  violet: '#B08DE8',
  text: 'rgba(232,232,232,.82)',
  muted: 'rgba(232,232,232,.44)',
  dim: 'rgba(232,232,232,.24)',
};

function Section({ title, sigil, children, accent = C.gold }: { title: string; sigil: string; children: React.ReactNode; accent?: string }) {
  return (
    <section style={{ marginBottom: 14, border: `1px solid ${accent}22`, borderRadius: 14, background: 'rgba(14,17,32,.62)', overflow: 'hidden' }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: 9, padding: '11px 15px', borderBottom: `1px solid ${accent}15`, background: `${accent}08` }}>
        <span style={{ color: accent, fontSize: 13 }}>{sigil}</span>
        <span style={{ fontFamily: 'ui-monospace, monospace', fontSize: 8.5, letterSpacing: '.24em', textTransform: 'uppercase', color: `${accent}aa` }}>{title}</span>
      </div>
      <div style={{ padding: 16 }}>{children}</div>
    </section>
  );
}

function Chip({ children, accent = C.teal }: { children: React.ReactNode; accent?: string }) {
  return <span style={{ display: 'inline-flex', padding: '6px 9px', borderRadius: 16, background: `${accent}0d`, border: `1px solid ${accent}28`, color: `${accent}cc`, fontFamily: 'ui-monospace, monospace', fontSize: 9 }}>{children}</span>;
}

function makeSigil(seed: string) {
  const chars = ['◈', '✦', '⬡', '◇', '✧', '◉', '⌬', '⟐'];
  let n = 0;
  for (let i = 0; i < seed.length; i += 1) n = (n * 31 + seed.charCodeAt(i)) >>> 0;
  return chars[n % chars.length];
}

export default function MasterProfile() {
  const { isAuthenticated, user } = useAuth();
  const [spine, setSpine] = useState<IdentitySpine | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!isAuthenticated || !user?.idToken) {
      setSpine(null);
      setLoading(false);
      return;
    }
    let cancelled = false;
    (async () => {
      setLoading(true);
      try {
        const res = await apiFetch('/api/me/identity-spine', {
          headers: {},
        });
        if (!res.ok) throw new Error('Unable to resolve your identity spine.');
        const data = await res.json() as { identity_spine?: IdentitySpine };
        if (!cancelled) setSpine(data.identity_spine ?? null);
      } catch (e) {
        if (!cancelled) setError(e instanceof Error ? e.message : 'Unable to resolve your identity spine.');
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();
    return () => { cancelled = true; };
  }, [isAuthenticated, user?.idToken]);

  const sigil = useMemo(() => makeSigil(spine?.identity.uid || user?.uid || 'arkadia'), [spine?.identity.uid, user?.uid]);

  if (!isAuthenticated) {
    return <div style={{ padding: 50, textAlign: 'center', color: C.muted, fontFamily: 'sans-serif', fontSize: 12 }}>Sign in to open your Master Profile.</div>;
  }
  if (loading) {
    return <div style={{ padding: 70, textAlign: 'center', color: C.teal, fontFamily: 'ui-monospace, monospace', fontSize: 9, letterSpacing: '.28em', textTransform: 'uppercase' }}>Resolving your node…</div>;
  }
  if (error || !spine) {
    return <div style={{ padding: 50, textAlign: 'center', color: C.muted, fontFamily: 'sans-serif', fontSize: 12 }}>{error || 'Your identity spine is not available yet.'}</div>;
  }

  const baseline = spine.capability.baseline;
  const ri = spine.relational_index;
  const displayName = spine.identity.preferred_name || spine.identity.canonical_name || 'Node';
  const username = spine.identity.username ? `@${spine.identity.username}` : 'username forming';
  const dimensions = Object.entries(ri.dimensions).filter(([, value]) => typeof value === 'number');

  return (
    <div style={{ maxWidth: 760, margin: '0 auto', padding: '20px 20px 90px' }} data-testid="master-profile">
      <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} style={{ marginBottom: 16, padding: '22px 20px', border: `1px solid ${C.gold}28`, borderRadius: 16, background: `radial-gradient(circle at 50% 15%, ${C.gold}0d, transparent 65%), rgba(10,12,22,.8)`, textAlign: 'center' }}>
        <div style={{ width: 72, height: 72, margin: '0 auto 12px', display: 'grid', placeItems: 'center', borderRadius: '50%', border: `1px solid ${C.gold}55`, boxShadow: `0 0 42px ${C.gold}12`, color: C.gold, fontSize: 32 }}>{spine.symbolic.sigil_seed || sigil}</div>
        <p style={{ margin: '0 0 5px', fontFamily: 'ui-monospace, monospace', fontSize: 8.5, letterSpacing: '.32em', textTransform: 'uppercase', color: `${C.teal}9c` }}>Node Identity · Seeded by A.I.S</p>
        <h1 style={{ margin: '0 0 4px', fontFamily: 'serif', fontSize: 30, fontWeight: 400, color: C.gold }}>{displayName}</h1>
        <p style={{ margin: 0, fontFamily: 'ui-monospace, monospace', fontSize: 9, letterSpacing: '.16em', color: C.muted }}>{username} · {spine.identity.role}</p>
        <p style={{ maxWidth: 520, margin: '15px auto 0', fontFamily: 'serif', fontSize: 13, lineHeight: 1.7, color: C.text }}>
          This is your living identity spine. It begins with A.I.S, learns through experience, and changes as your capabilities, context and relationship with Arkadia change.
        </p>
        <div style={{ display: 'flex', justifyContent: 'center', gap: 7, flexWrap: 'wrap', marginTop: 14 }}>
          <Chip accent={C.gold}>SEED {spine.provenance.ais_version ? `v${spine.provenance.ais_version}` : 'PENDING'}</Chip>
          <Chip accent={C.teal}>{spine.capability.evidence_count} DEVELOPMENT EVENTS</Chip>
          <Chip accent={C.blue}>{spine.identity.ims_id || 'NO IMS ID YET'}</Chip>
        </div>
      </motion.div>

      <Section title="Identity" sigil="◈" accent={C.gold}>
        <div style={{ display: 'grid', gap: 12 }}>
          <div><div style={{ fontSize: 8, letterSpacing: '.2em', textTransform: 'uppercase', color: C.dim, marginBottom: 5 }}>A.I.S identity statement</div><div style={{ color: C.text, fontFamily: 'serif', lineHeight: 1.7 }}>{baseline.identity || 'Your first identity statement will appear here.'}</div></div>
          <div><div style={{ fontSize: 8, letterSpacing: '.2em', textTransform: 'uppercase', color: C.dim, marginBottom: 7 }}>Growth direction</div><div style={{ display: 'flex', gap: 6, flexWrap: 'wrap' }}>{baseline.growth.length ? baseline.growth.map(x => <Chip key={x} accent={C.violet}>{x}</Chip>) : <span style={{ color: C.muted, fontSize: 11 }}>The Grove will learn your next direction.</span>}</div></div>
        </div>
      </Section>

      <Section title="Capability Baseline · Spiral Grove" sigil="⌬" accent={C.teal}>
        <p style={{ margin: '0 0 12px', fontFamily: 'sans-serif', fontSize: 11, lineHeight: 1.6, color: C.muted }}>This is the starting point, not a verdict. Spiral Grove can add evidence and development events without erasing the original seed.</p>
        <div style={{ display: 'flex', gap: 7, flexWrap: 'wrap' }}>{baseline.capabilities.length ? baseline.capabilities.map(x => <Chip key={x}>{x}</Chip>) : <span style={{ color: C.muted, fontSize: 11 }}>No capability signals recorded yet.</span>}</div>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 8, marginTop: 14 }}>
          <div style={{ padding: 11, borderRadius: 10, background: `${C.teal}07`, border: `1px solid ${C.teal}16` }}><b style={{ color: C.teal, fontSize: 18 }}>{baseline.capabilities.length}</b><div style={{ color: C.dim, fontSize: 8, marginTop: 3 }}>BASELINE SIGNALS</div></div>
          <div style={{ padding: 11, borderRadius: 10, background: `${C.blue}07`, border: `1px solid ${C.blue}16` }}><b style={{ color: C.blue, fontSize: 18 }}>{spine.capability.evidence_count}</b><div style={{ color: C.dim, fontSize: 8, marginTop: 3 }}>EVIDENCE EVENTS</div></div>
          <div style={{ padding: 11, borderRadius: 10, background: `${C.violet}07`, border: `1px solid ${C.violet}16` }}><b style={{ color: C.violet, fontSize: 18 }}>{spine.capability.development_events.length}</b><div style={{ color: C.dim, fontSize: 8, marginTop: 3 }}>GROWTH EVENTS</div></div>
        </div>
      </Section>

      <Section title="Relational Index" sigil="∞" accent={C.violet}>
        <div style={{ display: 'flex', alignItems: 'baseline', justifyContent: 'space-between', gap: 16, marginBottom: 10 }}>
          <div><div style={{ fontFamily: 'serif', fontSize: 22, color: C.violet }}>{ri.score == null ? 'Learning' : ri.score}</div><div style={{ fontSize: 8, letterSpacing: '.18em', textTransform: 'uppercase', color: C.dim }}>alignment state</div></div>
          <Chip accent={ri.status === 'seeded' ? C.teal : C.blue}>{ri.status.replace('_', ' ')}</Chip>
        </div>
        <p style={{ margin: '0 0 12px', fontFamily: 'sans-serif', fontSize: 11, lineHeight: 1.65, color: C.muted }}>
          The index is intentionally not a fake precision score. It becomes meaningful as Arkadia accumulates interaction evidence and can evaluate coherence, continuity, personalization, agency, trust and responsiveness over time.
        </p>
        {dimensions.length > 0 && <div style={{ display: 'grid', gap: 7 }}>{dimensions.map(([key, value]) => <div key={key} style={{ display: 'flex', justifyContent: 'space-between', fontSize: 9, color: C.muted }}><span>{key.replaceAll('_', ' ')}</span><span style={{ color: C.violet }}>{value}</span></div>)}</div>}
      </Section>

      <Section title="Relational Preferences" sigil="✧" accent={C.blue}>
        <div style={{ display: 'grid', gap: 9, fontSize: 11, color: C.text }}>
          <div><span style={{ color: C.dim }}>Arkadia's role · </span>{spine.relationship.preferred_ai_role || 'Not yet established'}</div>
          <div><span style={{ color: C.dim }}>Communication · </span>{spine.relationship.communication_preference || 'Learning from interaction'}</div>
          <div><span style={{ color: C.dim }}>Collaboration · </span>{spine.relationship.collaboration_preference || 'Learning from interaction'}</div>
        </div>
      </Section>

      <Section title="Continuity" sigil="⬡" accent={C.gold}>
        <div style={{ display: 'flex', gap: 7, flexWrap: 'wrap', marginBottom: 10 }}>
          {['NovaNet', 'ReasoMate', 'Personal Codex', 'Personal EchoField', 'Spiral Grove', 'IMS', 'Encyclopedia Galactica'].map(x => <Chip key={x} accent={C.gold}>{x}</Chip>)}
        </div>
        <p style={{ margin: 0, fontFamily: 'sans-serif', fontSize: 10.5, lineHeight: 1.6, color: C.muted }}>These are continuity surfaces of this node, not separate identities. The seed remains provenance; current understanding can evolve without rewriting the history that produced it.</p>
      </Section>
    </div>
  );
}
