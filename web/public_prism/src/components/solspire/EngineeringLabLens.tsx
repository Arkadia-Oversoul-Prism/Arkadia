import React, { useEffect, useMemo, useState } from 'react';
import { ApiError, apiRequest } from '../../lib/apiClient';

type LabOverview = {
  schema_version?: string;
  collector_version?: string;
  analysis_version?: string;
  observed_at?: string;
  repository_head?: string | null;
  system?: string;
  repository?: { branch?: string | null; head?: string | null; clean?: boolean | null; remote?: string | null; status?: string; reason?: string };
  architecture?: { components?: number; modules?: number; services?: number; routes?: number; execution_paths?: number; status?: string };
  trajectory?: { commits_analysed?: number; major_transitions?: number; high_churn_components?: number; classifications?: Record<string, number> };
  canon?: { loaded?: boolean; sources?: unknown[]; drift?: unknown[]; version?: string | null };
  patterns?: Array<{ pattern_id?: string; type?: string; severity?: string; confidence?: number; evidence?: string[]; affected_entities?: string[] }>;
  graph?: { entities?: number; relationships?: number; status?: string };
  governance?: { maximum_authority?: number; autonomous_mutation?: boolean; production_mutation?: boolean; approval_required?: boolean };
  errors?: Array<{ component?: string; status?: string; reason?: string }>;
  status?: string;
};

type ObservationState = 'loading' | 'ready' | 'unavailable';

const tone: Record<string, string> = {
  healthy: '#00D4AA', observed: '#00D4AA', warning: '#C9A84C', drift: '#B08DE8', unknown: '#9A9AA2', unavailable: '#D66A6A', inferred: '#6A9FD8', derived: '#6A9FD8',
};

function label(value: unknown): string {
  return String(value ?? 'UNKNOWN').replace(/_/g, ' ').toUpperCase();
}

function EvidenceBadge({ value }: { value: string }) {
  const key = value.toLowerCase();
  const color = tone[key] || tone.unknown;
  return <span style={{ display: 'inline-flex', alignItems: 'center', gap: 6, padding: '4px 8px', border: `1px solid ${color}44`, borderRadius: 999, color, fontSize: 9, letterSpacing: '0.16em', textTransform: 'uppercase' }}>{label(value)}</span>;
}

function Metric({ name, value }: { name: string; value: number | string }) {
  return <div style={{ padding: '14px 16px', border: '1px solid rgba(255,255,255,0.08)', borderRadius: 10, background: 'rgba(255,255,255,0.025)' }}><div className="solspire-kicker">{name}</div><strong style={{ display: 'block', marginTop: 5, fontSize: 23, fontWeight: 500, color: '#E8E8E8' }}>{value}</strong></div>;
}

function Section({ eyebrow, title, children }: { eyebrow: string; title: string; children: React.ReactNode }) {
  return <section style={{ marginBottom: 28 }}><div style={{ marginBottom: 12 }}><div className="solspire-kicker">{eyebrow}</div><h2 style={{ margin: '4px 0 0', fontFamily: 'serif', fontSize: 24, fontWeight: 500, color: '#E8E8E8' }}>{title}</h2></div>{children}</section>;
}

export default function EngineeringLabLens() {
  const [state, setState] = useState<ObservationState>('loading');
  const [data, setData] = useState<LabOverview | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let active = true;
    setState('loading');
    setError(null);
    apiRequest<LabOverview>('/api/lab/overview')
      .then((payload) => { if (active) { setData(payload); setState('ready'); } })
      .catch((reason) => { if (active) { setData(null); setError(reason instanceof ApiError ? `${reason.kind}: ${reason.message}` : String(reason)); setState('unavailable'); } });
    return () => { active = false; };
  }, []);

  const patterns = useMemo(() => data?.patterns || [], [data]);
  const sources = data?.canon?.sources || [];
  const errors = data?.errors || [];

  if (state === 'loading') return <div className="solspire-object" style={{ padding: 24 }}><EvidenceBadge value="observed" /><h2 style={{ margin: '14px 0 8px', fontFamily: 'serif', fontSize: 28 }}>The Lab is observing Arkadia.</h2><p style={{ color: 'rgba(232,232,232,0.58)', maxWidth: 560, lineHeight: 1.7 }}>No temporary metrics are rendered while the observation is in flight.</p></div>;

  if (state === 'unavailable') return <div className="solspire-object" style={{ padding: 24, borderColor: 'rgba(214,106,106,0.28)' }}><EvidenceBadge value="unavailable" /><h2 style={{ margin: '14px 0 8px', fontFamily: 'serif', fontSize: 28 }}>Observation unavailable.</h2><p style={{ color: 'rgba(232,232,232,0.58)', lineHeight: 1.7 }}>The Engineering Lab could not obtain its current observation. No healthy or empty substitute has been inferred.</p><div style={{ marginTop: 14, color: '#D66A6A', fontFamily: 'monospace', fontSize: 11, wordBreak: 'break-word' }}>{error || 'Unknown observation failure'}</div></div>;

  const repo = data?.repository;
  const architecture = data?.architecture;
  const trajectory = data?.trajectory;
  const canon = data?.canon;
  const governance = data?.governance;

  return <div data-testid="engineering-lab-lens">
    <div style={{ display: 'grid', gridTemplateColumns: 'minmax(0, 1.6fr) minmax(220px, 0.8fr)', gap: 12, marginBottom: 28 }}>
      <div className="solspire-object" style={{ padding: 20 }}><div style={{ display: 'flex', justifyContent: 'space-between', gap: 16, alignItems: 'flex-start' }}><div><div className="solspire-kicker">System state</div><h2 style={{ margin: '5px 0 8px', fontFamily: 'serif', fontSize: 30, fontWeight: 500 }}>{data?.system || 'UNKNOWN SYSTEM'}</h2><p style={{ margin: 0, color: 'rgba(232,232,232,0.52)', lineHeight: 1.6 }}>Deterministic observation of the existing Arkadia substrate.</p></div><EvidenceBadge value={data?.status === 'observed' ? 'observed' : 'warning'} /></div><div style={{ marginTop: 20, display: 'grid', gap: 8, fontFamily: 'monospace', fontSize: 10, color: 'rgba(232,232,232,0.6)' }}><div>REPOSITORY · {repo?.remote || 'UNKNOWN'}</div><div>BRANCH · {repo?.branch || 'UNKNOWN'}</div><div>HEAD · {repo?.head || 'UNKNOWN'}</div><div>WORKTREE · {repo?.clean === true ? 'CLEAN' : repo?.clean === false ? 'CHANGES PRESENT' : 'UNKNOWN'}</div><div>OBSERVED · {data?.observed_at || 'UNKNOWN'}</div></div></div>
      <div className="solspire-object" style={{ padding: 20 }}><div className="solspire-kicker">Lab version</div><div style={{ marginTop: 12, display: 'grid', gap: 10, fontFamily: 'monospace', fontSize: 10, color: 'rgba(232,232,232,0.66)' }}><div>SCHEMA · {data?.schema_version || 'UNKNOWN'}</div><div>COLLECTOR · {data?.collector_version || 'UNKNOWN'}</div><div>ANALYSIS · {data?.analysis_version || 'UNKNOWN'}</div></div></div>
    </div>

    <Section eyebrow="Architecture" title="What exists now"><div style={{ display: 'grid', gridTemplateColumns: 'repeat(5, minmax(0, 1fr))', gap: 8 }}>{[['Components', architecture?.components], ['Modules', architecture?.modules], ['Services', architecture?.services], ['Routes', architecture?.routes], ['Execution paths', architecture?.execution_paths]].map(([name, value]) => <Metric key={String(name)} name={String(name)} value={typeof value === 'number' ? value : 'UNKNOWN'} />)}</div></Section>

    <Section eyebrow="Trajectory" title="How the system arrived here"><div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, minmax(0, 1fr))', gap: 8, marginBottom: 10 }}><Metric name="Commits analysed" value={trajectory?.commits_analysed ?? 'UNKNOWN'} /><Metric name="Major transitions" value={trajectory?.major_transitions ?? 'UNKNOWN'} /><Metric name="High churn" value={trajectory?.high_churn_components ?? 'UNKNOWN'} /></div>{trajectory?.classifications && <div className="solspire-object" style={{ padding: 14 }}><div className="solspire-kicker">Commit classifications</div><div style={{ marginTop: 10, display: 'flex', flexWrap: 'wrap', gap: 8 }}>{Object.entries(trajectory.classifications).map(([key, value]) => <span key={key} style={{ fontFamily: 'monospace', fontSize: 10, color: 'rgba(232,232,232,0.64)' }}>{label(key)} · {value}</span>)}</div></div>}</Section>

    <Section eyebrow="Patterns" title="Structural signals">{patterns.length === 0 ? <div className="solspire-object" style={{ padding: 18 }}><EvidenceBadge value="observed" /><p style={{ margin: '12px 0 0', color: 'rgba(232,232,232,0.58)' }}>No structural patterns detected in the current observation.</p></div> : <div style={{ display: 'grid', gap: 8 }}>{patterns.map((pattern, index) => <article key={pattern.pattern_id || index} className="solspire-object" style={{ padding: 16 }}><div style={{ display: 'flex', justifyContent: 'space-between', gap: 10, alignItems: 'center' }}><div><div className="solspire-kicker">{pattern.type || 'PATTERN'}</div><h3 style={{ margin: '5px 0 0', fontSize: 15, fontWeight: 500 }}>{pattern.pattern_id || 'UNKNOWN PATTERN'}</h3></div><EvidenceBadge value={pattern.severity || 'unknown'} /></div><div style={{ marginTop: 10, fontSize: 10, color: 'rgba(232,232,232,0.55)' }}>CONFIDENCE · {typeof pattern.confidence === 'number' ? `${Math.round(pattern.confidence * 100)}%` : 'UNKNOWN'}</div>{pattern.evidence?.length ? <ul style={{ margin: '10px 0 0', paddingLeft: 18, color: 'rgba(232,232,232,0.62)', fontSize: 11, lineHeight: 1.6 }}>{pattern.evidence.slice(0, 8).map(item => <li key={item}>{item}</li>)}</ul> : <div style={{ marginTop: 10, color: 'rgba(232,232,232,0.4)', fontSize: 11 }}>Evidence unavailable.</div>}</article>)}</div>}</Section>

    <div style={{ display: 'grid', gridTemplateColumns: 'minmax(0, 1fr) minmax(0, 1fr)', gap: 18 }}>
      <Section eyebrow="Canon" title="What Arkadia treats as reference"><div className="solspire-object" style={{ padding: 16 }}><div style={{ display: 'flex', justifyContent: 'space-between', gap: 10 }}><EvidenceBadge value={canon?.loaded ? 'healthy' : 'unknown'} /><span className="solspire-mono">{canon?.version || 'VERSION UNKNOWN'}</span></div><div style={{ marginTop: 12, fontSize: 11, color: 'rgba(232,232,232,0.6)' }}>Loaded sources · {canon?.loaded === true ? sources.length : 'UNKNOWN'}</div>{sources.length > 0 && <ul style={{ margin: '10px 0 0', paddingLeft: 18, fontSize: 11, lineHeight: 1.6, color: 'rgba(232,232,232,0.62)' }}>{sources.slice(0, 12).map((source, i) => <li key={i}>{typeof source === 'string' ? source : JSON.stringify(source)}</li>)}</ul>}<div style={{ marginTop: 12 }}><EvidenceBadge value={(canon?.drift?.length || 0) > 0 ? 'drift' : 'observed'} /></div></div></Section>
      <Section eyebrow="Governance" title="Authority remains outside the Lab"><div className="solspire-object" style={{ padding: 16, display: 'grid', gap: 12 }}><div><div className="solspire-kicker">Authority ceiling</div><strong style={{ fontFamily: 'monospace', fontSize: 18 }}>LEVEL {governance?.maximum_authority ?? 'UNKNOWN'}</strong></div><div style={{ display: 'flex', flexWrap: 'wrap', gap: 8 }}><EvidenceBadge value={governance?.autonomous_mutation === false ? 'healthy' : 'warning'} /><span className="solspire-mono">AUTONOMOUS MUTATION · {governance?.autonomous_mutation === false ? 'DISABLED' : 'UNKNOWN'}</span></div><div style={{ display: 'flex', flexWrap: 'wrap', gap: 8 }}><EvidenceBadge value={governance?.production_mutation === false ? 'healthy' : 'warning'} /><span className="solspire-mono">PRODUCTION MUTATION · {governance?.production_mutation === false ? 'DISABLED' : 'UNKNOWN'}</span></div><div className="solspire-mono">APPROVAL REQUIRED · {governance?.approval_required === true ? 'YES' : 'UNKNOWN'}</div></div></Section>
    </div>

    {errors.length > 0 && <section className="solspire-object" style={{ padding: 16, borderColor: 'rgba(201,168,76,0.25)' }}><div className="solspire-kicker">Observation warnings</div>{errors.map((item, i) => <div key={i} style={{ marginTop: 8, fontSize: 11, color: 'rgba(232,232,232,0.6)' }}>{item.component || 'unknown'} · {item.status || 'unknown'} · {item.reason || 'reason unavailable'}</div>)}</section>}
  </div>;
}
