/**
 * Personal Echofeild
 *
 * Auth-gated living feed of the authenticated node's own work: active SolSpire
 * projects, the Personal Codex identity, and Knowledge OS graph/timeline nodes
 * that belong to this human. Rendered as a dynamic, substack-style feed
 * aggregated and organised through the knowledge graph.
 *
 * This is the private half of the Universal Echofeild Crystal Matrix. Public
 * Scrolls live in the Spiral Codex Live Feed; the Personal Echofeild is the
 * personal user-data feed — never public.
 *
 * Spine relationship: data flows NovaNet/Oracle -> Knowledge OS -> (graph +
 * timeline) -> Personal Echofeild. The UI is a window onto the spine, not a
 * second memory store.
 */
import React, { useEffect, useMemo, useState } from 'react';
import { motion } from 'framer-motion';
import { useAuth } from '../contexts/AuthContext';
import { ORACLE } from '../lib/apiConfig';
import { getGraph, getRecentTimeline, GraphNode, GraphEdge, TimelineEvent } from '../lib/knowledgeApi';
import ScrollListenButton from '../components/ScrollListenButton';
import PersonalCodex from './PersonalCodex';

type View = 'home' | 'gate' | 'commune' | 'reset' | 'about' | 'login' | 'codex' | 'dashboard'
  | 'nexus' | 'encyclopedia' | 'spiral-codex' | 'loops' | 'grove' | 'larder' | 'novanet'
  | 'ims' | 'distribute' | 'offerings' | 'aic' | 'pulse' | 'settings' | 'solspire'
  | 'knowledge-os' | 'reasomate' | 'personal-echofeild' | 'echofeild-matrix';

interface SolProject {
  id: string; name: string; status: string;
  created_at: number; updated_at: number;
  metadata: Record<string, unknown>; conversations: unknown[];
}

const API_BASE = (import.meta.env.VITE_API_BASE_URL ?? '').replace(/\/$/, '');

async function get<T>(path: string): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`);
  if (!res.ok) throw new Error(`${res.status}`);
  return res.json();
}

function fmtAgo(ts: number | string): string {
  const ms = typeof ts === 'number' ? (ts < 1e12 ? ts * 1000 : ts) : Date.parse(ts);
  if (!ms || isNaN(ms)) return '';
  const diff = Date.now() - ms;
  if (diff < 60_000) return 'just now';
  if (diff < 3_600_000) return `${Math.floor(diff / 60_000)}m ago`;
  if (diff < 86_400_000) return `${Math.floor(diff / 3_600_000)}h ago`;
  return `${Math.floor(diff / 86_400_000)}d ago`;
}

// Build adjacency for conversation-type graph nodes so the feed can surface
// connections among the human's own captures (the Exp 3 friction point: the
// graph must be represented, not just prose).
function buildAdjacency(nodes: GraphNode[], edges: GraphEdge[]) {
  const adj = new Map<number, Set<number>>();
  const byId = new Map(nodes.map(n => [n.id, n]));
  for (const e of edges) {
    if (!byId.has(e.source_note_id) || !byId.has(e.target_note_id)) continue;
    if (!adj.has(e.source_note_id)) adj.set(e.source_note_id, new Set());
    if (!adj.has(e.target_note_id)) adj.set(e.target_note_id, new Set());
    adj.get(e.source_note_id)!.add(e.target_note_id);
    adj.get(e.target_note_id)!.add(e.source_note_id);
  }
  return adj;
}

export default function PersonalEchofeild({ onNavigate }: { onNavigate: (v: View) => void }) {
  const { isAuthenticated } = useAuth();
  const [projects, setProjects] = useState<SolProject[]>([]);
  const [graphNodes, setGraphNodes] = useState<GraphNode[]>([]);
  const [graphEdges, setGraphEdges] = useState<GraphEdge[]>([]);
  const [timeline, setTimeline] = useState<TimelineEvent[]>([]);
  const [loading, setLoading] = useState(true);
  const [err, setErr] = useState<string | null>(null);

  useEffect(() => {
    if (!isAuthenticated) { setLoading(false); return; }
    let cancelled = false;
    (async () => {
      setLoading(true); setErr(null);
      const results = await Promise.allSettled([
        get<{ projects: SolProject[] }>(`${ORACLE}/solspire/projects?status=active`),
        getGraph(),
        getRecentTimeline(40),
      ]);
      if (cancelled) return;
      if (results[0].status === 'fulfilled') setProjects(results[0].value.projects ?? []);
      if (results[1].status === 'fulfilled') {
        setGraphNodes(results[1].value.nodes ?? []);
        setGraphEdges(results[1].value.edges ?? []);
      }
      if (results[2].status === 'fulfilled') setTimeline(results[2].value ?? []);
      if (results.every(r => r.status === 'rejected')) setErr('Unable to reach the field right now.');
      setLoading(false);
    })();
    return () => { cancelled = true; };
  }, [isAuthenticated]);

  const adjacency = useMemo(() => buildAdjacency(graphNodes, graphEdges), [graphNodes, graphEdges]);
  const convNodes = useMemo(
    () => graphNodes.filter(n => n.note_type === 'conversation')
      .sort((a, b) => Date.parse(b.created_at) - Date.parse(a.created_at)),
    [graphNodes],
  );

  // Auth gate — the Personal Echofeild is genuinely private, not decorative.
  // Delegates to PersonalCodex's own gate for the identity half, so the unified
  // field shows the same sign-in prompt either way.
  if (!isAuthenticated) {
    return (
      <div style={{ maxWidth: 760, margin: '0 auto', padding: '24px 20px 80px' }}>
        <PersonalCodex onNavigate={onNavigate} />
      </div>
    );
  }

  const activeProjects = projects.filter(p => p.status === 'active');
  const totalConnections = Array.from(adjacency.values()).reduce((s, set) => s + set.size, 0) / 2;

  return (
    <div style={{ maxWidth: 760, margin: '0 auto', padding: '24px 20px 80px' }}>
      {/* ── UNIFIED IDENTITY: Personal Codex IS the Personal Echofeild ── */}
      {/* The Personal Codex identity stack renders as the identity layer of the
          unified field. Below it: the living projects + knowledge graph feed. */}
      <PersonalCodex />

      {/* Crystal Matrix metadata aggregation — the field stats the Codex identity
          does not carry: graph connections, timeline events, project pulse. */}
      <div style={{ marginTop: 28, marginBottom: 28, padding: '16px 20px', background: 'rgba(176,141,232,0.04)', border: '1px solid rgba(176,141,232,0.16)', borderRadius: 12, borderBottom: '3px solid rgba(176,141,232,0.5)' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 12 }}>
          <span style={{ color: '#B08DE8', fontSize: 14 }}>⬡</span>
          <span style={{ fontFamily: 'ui-monospace, monospace', fontSize: 9, letterSpacing: '0.24em', textTransform: 'uppercase', color: 'rgba(176,141,232,0.6)' }}>Crystal Matrix · Echofeild Aggregation</span>
        </div>
        <div style={{ display: 'flex', gap: 18, flexWrap: 'wrap' }}>
          <Stat label="active projects" value={activeProjects.length} color="#00D4AA" />
          <Stat label="knowledge nodes" value={graphNodes.length} color="#C9A84C" />
          <Stat label="graph connections" value={totalConnections} color="#B08DE8" />
          <Stat label="timeline events" value={timeline.length} color="#6A9FD8" />
        </div>
      </div>

      {loading && (
        <div style={{ textAlign: 'center', padding: '60px 0', color: 'rgba(232,232,232,0.35)', fontFamily: 'sans-serif', fontSize: 12 }}>
          <motion.span animate={{ opacity: [0.4, 1, 0.4] }} transition={{ duration: 1.2, repeat: Infinity }}>
            Gathering the field…
          </motion.span>
        </div>
      )}

      {err && !loading && (
        <div style={{ padding: '40px 0', textAlign: 'center', color: 'rgba(232,232,232,0.4)', fontFamily: 'sans-serif', fontSize: 13 }}>{err}</div>
      )}

      {!loading && !err && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
          {/* Active projects — the primary feed entries */}
          {activeProjects.length > 0 && (
            <SectionLabel sigil="◉" color="#00D4AA" label="Active projects" sub="from SolSpire" />
          )}
          {activeProjects.map((p, i) => (
            <motion.div key={p.id} initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: Math.min(i * 0.04, 0.3), duration: 0.25 }}
              onClick={() => onNavigate('solspire')}
              style={{ cursor: 'pointer', padding: '18px 20px', background: 'rgba(0,212,170,0.03)', border: '1px solid rgba(0,212,170,0.12)',
                borderRadius: 12, borderLeft: '3px solid rgba(0,212,170,0.4)' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'baseline', gap: 12 }}>
                <h3 style={{ fontFamily: 'serif', fontSize: 17, fontWeight: 400, color: 'rgba(232,232,232,0.9)', margin: 0, letterSpacing: '0.01em' }}>{p.name}</h3>
                <span style={{ fontFamily: 'ui-monospace, monospace', fontSize: 9, color: 'rgba(0,212,170,0.6)', whiteSpace: 'nowrap' }}>{fmtAgo(p.updated_at)}</span>
              </div>
              <div style={{ display: 'flex', gap: 10, marginTop: 8, flexWrap: 'wrap' }}>
                <Chip text={p.status} color="#00D4AA" />
                {p.conversations.length > 0 && <Chip text={`${p.conversations.length} conversations`} color="rgba(232,232,232,0.4)" />}
                {Object.keys(p.metadata).length > 0 && <Chip text={`${Object.keys(p.metadata).length} metadata fields`} color="rgba(232,232,232,0.3)" />}
              </div>
            </motion.div>
          ))}

          {/* Knowledge graph captures — conversation nodes + their connections */}
          {convNodes.length > 0 && (
            <SectionLabel sigil="⬡" color="#B08DE8" label="Captured knowledge" sub="from the knowledge graph" />
          )}
          {convNodes.slice(0, 20).map((n, i) => {
            const connections = adjacency.get(n.id);
            const connCount = connections ? connections.size : 0;
            return (
              <motion.div key={n.id} initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: Math.min(i * 0.03, 0.3), duration: 0.25 }}
                style={{ padding: '14px 18px', background: 'rgba(176,141,232,0.03)', border: '1px solid rgba(176,141,232,0.12)', borderRadius: 10 }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'baseline', gap: 12 }}>
                  <h4 style={{ fontFamily: 'serif', fontSize: 14, fontWeight: 400, color: 'rgba(232,232,232,0.82)', margin: 0 }}>{n.title}</h4>
                  <span style={{ fontFamily: 'ui-monospace, monospace', fontSize: 8.5, color: 'rgba(176,141,232,0.5)', whiteSpace: 'nowrap' }}>{fmtAgo(n.created_at)}</span>
                </div>
                <div style={{ display: 'flex', gap: 8, marginTop: 7, flexWrap: 'wrap' }}>
                  <Chip text={n.note_type} color="rgba(176,141,232,0.6)" />
                  {connCount > 0
                    ? <Chip text={`${connCount} graph ${connCount === 1 ? 'connection' : 'connections'}`} color="#B08DE8" />
                    : <Chip text="isolated node" color="rgba(232,232,232,0.25)" />}
                </div>
                <div style={{ marginTop: 8 }}>
                  <ScrollListenButton text={n.title} label={`PERSONAL CAPTURE · ${n.title.slice(0, 36)}`} accent="#B08DE8" />
                </div>
              </motion.div>
            );
          })}

          {/* Truthful empty state — no fake data */}
          {!loading && activeProjects.length === 0 && convNodes.length === 0 && (
            <div style={{ padding: '60px 20px', textAlign: 'center' }}>
              <div style={{ fontSize: 28, color: 'rgba(232,232,232,0.18)', marginBottom: 14 }}>✦</div>
              <h3 style={{ fontFamily: 'serif', fontSize: 17, fontWeight: 400, color: 'rgba(232,232,232,0.6)', margin: '0 0 8px' }}>Your field is open, but empty</h3>
              <p style={{ fontFamily: 'sans-serif', fontSize: 12, color: 'rgba(232,232,232,0.4)', lineHeight: 1.6, maxWidth: 420, margin: '0 auto' }}>
                Nothing has accumulated yet. Talk to Arkana in the Oracle or ReasoMate, or create a SolSpire project,
                and the knowledge graph will populate this feed with your real, connected work.
              </p>
              <div style={{ display: 'flex', gap: 10, justifyContent: 'center', marginTop: 20 }}>
                <button onClick={() => onNavigate('commune')} style={ctaBtn}>Open the Oracle</button>
                <button onClick={() => onNavigate('solspire')} style={ctaBtn}>Create a project</button>
              </div>
            </div>
          )}
        </div>
      )}

      <p style={{ textAlign: 'center', fontFamily: 'ui-monospace, monospace', fontSize: 8, letterSpacing: '0.24em', textTransform: 'uppercase', color: 'rgba(232,232,232,0.18)', margin: '36px 0 0' }}>
        ✦ personal echofeild · auth-gated · source: solspire/projects · knowledge/graph · knowledge/timeline ✦
      </p>
    </div>
  );
}

const ctaBtn: React.CSSProperties = {
  padding: '9px 18px', background: 'rgba(201,168,76,0.08)', border: '1px solid rgba(201,168,76,0.22)',
  borderRadius: 8, color: 'rgba(201,168,76,0.85)', fontFamily: 'sans-serif', fontSize: 10,
  letterSpacing: '0.1em', textTransform: 'uppercase', cursor: 'pointer',
};

function Stat({ label, value, color }: { label: string; value: number; color: string }) {
  return (
    <div>
      <div style={{ fontFamily: 'serif', fontSize: 20, color, fontWeight: 400 }}>{value}</div>
      <div style={{ fontFamily: 'sans-serif', fontSize: 8.5, letterSpacing: '0.14em', textTransform: 'uppercase', color: 'rgba(232,232,232,0.3)', marginTop: 2 }}>{label}</div>
    </div>
  );
}

function SectionLabel({ sigil, color, label, sub }: { sigil: string; color: string; label: string; sub: string }) {
  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: 10, margin: '16px 0 2px' }}>
      <span style={{ color, fontSize: 13 }}>{sigil}</span>
      <span style={{ fontFamily: 'ui-monospace, monospace', fontSize: 8.5, letterSpacing: '0.24em', textTransform: 'uppercase', color: 'rgba(232,232,232,0.5)' }}>{label}</span>
      <span style={{ fontFamily: 'sans-serif', fontSize: 9, color: 'rgba(232,232,232,0.25)' }}>· {sub}</span>
      <div style={{ flex: 1, height: 1, background: 'linear-gradient(90deg, rgba(255,255,255,0.06), transparent)' }} />
    </div>
  );
}

function Chip({ text, color }: { text: string; color: string }) {
  return (
    <span style={{ fontFamily: 'ui-monospace, monospace', fontSize: 8, letterSpacing: '0.1em', textTransform: 'uppercase',
      color, padding: '2px 8px', background: `${color}10`, border: `1px solid ${color}25`, borderRadius: 4 }}>
      {text}
    </span>
  );
}
