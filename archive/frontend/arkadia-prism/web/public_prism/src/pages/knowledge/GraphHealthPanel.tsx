/**
 * GraphHealthPanel — Knowledge Graph section for SolSpire / KnowledgeOSPage.
 *
 * Consumes:
 *   GET /api/knowledge/status        → nodes, edges, ontology, density, health, ingestion
 *   GET /api/knowledge/relationships → distribution, top nodes, components
 *   GET /api/knowledge/graph/health  → detailed health checks
 *
 * Do NOT redesign the page layout.  This panel drops into the existing tab system.
 */

import { useQuery } from '@tanstack/react-query';
import {
  getStatus,
  getGraphRelationships,
  getGraphHealth,
  type KnowledgeStatus,
  type GraphRelationships,
  type GraphHealth,
} from '../../lib/knowledgeApi';

const C = {
  teal:   '#00D4AA',
  gold:   '#C9A84C',
  purple: '#B08DE8',
  blue:   '#6A9FD8',
  red:    '#C84848',
  muted:  'rgba(232,232,232,0.40)',
  dim:    'rgba(232,232,232,0.18)',
  border: 'rgba(255,255,255,0.07)',
  card:   'rgba(14,17,32,0.72)',
};

// ── Tiny primitives ───────────────────────────────────────────────────────────

function Row({ label, value, color }: { label: string; value: string | number; color?: string }) {
  return (
    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'baseline',
                  padding: '6px 0', borderBottom: `1px solid ${C.border}` }}>
      <span style={{ fontFamily: 'Inter, sans-serif', fontSize: 11, color: C.muted }}>{label}</span>
      <span style={{ fontFamily: 'ui-monospace, monospace', fontSize: 12,
                     color: color || '#e0e0e0', fontWeight: 600 }}>{value}</span>
    </div>
  );
}

function StatusBadge({ value }: { value?: string }) {
  const color = value === 'ok' ? C.teal : value === 'warn' ? C.gold : C.red;
  return (
    <span style={{ padding: '2px 8px', borderRadius: 4, background: `${color}22`,
                   border: `1px solid ${color}55`, color, fontFamily: 'Inter', fontSize: 10,
                   fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.08em' }}>
      {value ?? '—'}
    </span>
  );
}

function Card({ title, sigil, children }: { title: string; sigil: string; children: React.ReactNode }) {
  return (
    <div style={{ background: C.card, border: `1px solid ${C.border}`, borderRadius: 12,
                  padding: '18px 20px', display: 'flex', flexDirection: 'column', gap: 4 }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 10 }}>
        <span style={{ color: C.teal, fontSize: 14 }}>{sigil}</span>
        <span style={{ fontFamily: 'Cinzel, serif', fontSize: 11, color: '#e0e0e0',
                       letterSpacing: '0.12em', textTransform: 'uppercase' }}>{title}</span>
      </div>
      {children}
    </div>
  );
}

function MiniBar({ value, total, color = C.teal }: { value: number; total: number; color?: string }) {
  const pct = total > 0 ? Math.round((value / total) * 100) : 0;
  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
      <div style={{ flex: 1, height: 4, background: 'rgba(255,255,255,0.07)', borderRadius: 2 }}>
        <div style={{ width: `${pct}%`, height: '100%', background: color,
                      borderRadius: 2, transition: 'width 0.4s' }} />
      </div>
      <span style={{ fontFamily: 'ui-monospace', fontSize: 10, color: C.muted, minWidth: 28, textAlign: 'right' }}>
        {pct}%
      </span>
    </div>
  );
}

// ── Main panel ────────────────────────────────────────────────────────────────

export default function GraphHealthPanel() {
  const { data: status, isLoading: statusLoading } =
    useQuery<KnowledgeStatus>({ queryKey: ['knowledge-status'], queryFn: getStatus, refetchInterval: 30000 });

  const { data: rels, isLoading: relsLoading } =
    useQuery<GraphRelationships>({ queryKey: ['knowledge-relationships'], queryFn: getGraphRelationships, refetchInterval: 60000 });

  const { data: health } =
    useQuery<GraphHealth>({ queryKey: ['knowledge-graph-health'], queryFn: getGraphHealth, refetchInterval: 60000 });

  if (statusLoading || relsLoading) {
    return (
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center',
                    height: 200, color: C.muted, fontFamily: 'Inter', fontSize: 12 }}>
        Loading graph state…
      </div>
    );
  }

  const totalNodes = status?.vault?.notes ?? 0;
  const totalEdges = status?.graph?.edges ?? 0;
  const idx        = status?.indexing_status;
  const idxTotal   = idx ? (idx.complete + idx.pending + idx.partial + idx.failed) : 0;

  const topRels = (rels?.relationship_distribution ?? []).slice(0, 8);
  const topNodes = rels?.top_connected_nodes ?? [];
  const maxRelCount = topRels[0]?.count ?? 1;

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 16, overflowY: 'auto',
                  paddingBottom: 24, maxHeight: 'calc(100vh - 220px)' }}>

      {/* ── Summary strip ──────────────────────────────────────────────────── */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(130px, 1fr))', gap: 10 }}>
        {[
          { label: 'Total Nodes',        value: totalNodes.toLocaleString(),           color: C.teal,   sigil: '◈' },
          { label: 'Total Relationships', value: totalEdges.toLocaleString(),           color: C.gold,   sigil: '⟶' },
          { label: 'Rel. Types Used',     value: rels?.summary.relationship_types_used ?? '—', color: C.purple, sigil: '⊕' },
          { label: 'Graph Density',       value: rels ? `${((rels.summary.graph_density ?? 0) * 100).toFixed(4)}%` : '—', color: C.blue, sigil: '⬡' },
          { label: 'Avg Degree',          value: rels?.summary.average_degree ?? '—',  color: C.muted,  sigil: '∿' },
          { label: 'Components',          value: rels?.summary.connected_components ?? '—', color: C.muted, sigil: '⊞' },
        ].map(({ label, value, color, sigil }) => (
          <div key={label} style={{ background: C.card, border: `1px solid ${C.border}`,
                                    borderRadius: 10, padding: '14px 16px' }}>
            <div style={{ fontFamily: 'ui-monospace', fontSize: 10, color: C.dim,
                          marginBottom: 6, display: 'flex', alignItems: 'center', gap: 5 }}>
              <span>{sigil}</span>{label}
            </div>
            <div style={{ fontFamily: 'Cinzel, serif', fontSize: 18,
                          color, fontWeight: 700 }}>{value}</div>
          </div>
        ))}
      </div>

      {/* ── Two-column: ontology + health ──────────────────────────────────── */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16 }}>

        {/* Ontology */}
        <Card title="Ontology" sigil="⊕">
          <Row label="Ontology Version"    value={status?.ontology?.version ?? '—'} color={C.teal} />
          <Row label="Graph Version"        value={status?.graph_version ?? '—'}     color={C.teal} />
          <Row label="Node Types"           value={status?.ontology?.node_types_count ?? '—'} />
          <Row label="Relationship Types"   value={status?.ontology?.relationship_types_count ?? '—'} />
          <Row label="Notes Ingested (7d)"  value={status?.growth?.notes_last_7d ?? 0} color={C.gold} />
          <Row label="Edges Created (7d)"   value={status?.growth?.edges_last_7d ?? 0} color={C.gold} />
          {status?.last_ingestion && (
            <Row label="Last Ingestion"
                 value={new Date(status.last_ingestion).toLocaleString(undefined, { dateStyle: 'short', timeStyle: 'short' })} />
          )}
        </Card>

        {/* Graph health */}
        <Card title="Graph Health" sigil="◎">
          <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 10 }}>
            <span style={{ fontFamily: 'Inter', fontSize: 11, color: C.muted }}>Overall</span>
            <StatusBadge value={health?.overall ?? status?.graph_health} />
          </div>
          {health?.checks && Object.entries(health.checks).map(([key, chk]: [string, Record<string, unknown>]) => (
            <div key={key} style={{ display: 'flex', justifyContent: 'space-between',
                                    alignItems: 'center', padding: '4px 0',
                                    borderBottom: `1px solid ${C.border}` }}>
              <span style={{ fontFamily: 'Inter', fontSize: 10, color: C.muted }}>
                {key.replace(/_/g, ' ')}
              </span>
              <StatusBadge value={chk.status as string} />
            </div>
          ))}
        </Card>
      </div>

      {/* ── Indexing progress ──────────────────────────────────────────────── */}
      {idx && (
        <Card title="Indexing Progress" sigil="⟐">
          <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
            {[
              { label: 'Complete', count: idx.complete, color: C.teal },
              { label: 'Pending',  count: idx.pending,  color: C.gold },
              { label: 'Partial',  count: idx.partial,  color: C.purple },
              { label: 'Failed',   count: idx.failed,   color: C.red },
            ].map(({ label, count, color }) => (
              <div key={label}>
                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 3 }}>
                  <span style={{ fontFamily: 'Inter', fontSize: 10, color: C.muted }}>{label}</span>
                  <span style={{ fontFamily: 'ui-monospace', fontSize: 10, color }}>{count.toLocaleString()}</span>
                </div>
                <MiniBar value={count} total={idxTotal} color={color} />
              </div>
            ))}
          </div>
        </Card>
      )}

      {/* ── Two-column: relationship distribution + top nodes ──────────────── */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16 }}>

        {/* Relationship distribution */}
        <Card title="Relationship Distribution" sigil="⟶">
          {topRels.length === 0
            ? <span style={{ fontFamily: 'Inter', fontSize: 11, color: C.dim }}>No edges yet.</span>
            : topRels.map(r => (
                <div key={r.type} style={{ marginBottom: 8 }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 2 }}>
                    <span style={{ fontFamily: 'Inter', fontSize: 10, color: C.muted }}>{r.display_name}</span>
                    <span style={{ fontFamily: 'ui-monospace', fontSize: 10, color: C.teal }}>{r.count}</span>
                  </div>
                  <MiniBar value={r.count} total={maxRelCount} />
                </div>
              ))
          }
        </Card>

        {/* Top connected nodes */}
        <Card title="Most Connected Concepts" sigil="✦">
          {topNodes.length === 0
            ? <span style={{ fontFamily: 'Inter', fontSize: 11, color: C.dim }}>No nodes yet.</span>
            : topNodes.map((n, i) => (
                <div key={n.id} style={{ display: 'flex', alignItems: 'baseline', gap: 8,
                                         padding: '5px 0', borderBottom: `1px solid ${C.border}` }}>
                  <span style={{ fontFamily: 'ui-monospace', fontSize: 9, color: C.dim, minWidth: 14 }}>
                    {i + 1}
                  </span>
                  <span style={{ fontFamily: 'Inter', fontSize: 11, color: '#d0d0d0', flex: 1,
                                 overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                    {n.title}
                  </span>
                  <span style={{ fontFamily: 'ui-monospace', fontSize: 9, color: C.teal }}>
                    {n.degree}✦
                  </span>
                </div>
              ))
          }
        </Card>
      </div>

      {/* ── Nodes by type (if available) ───────────────────────────────────── */}
      {status?.nodes_by_type && Object.keys(status.nodes_by_type).length > 0 && (
        <Card title="Node Type Distribution" sigil="◈">
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8 }}>
            {Object.entries(status.nodes_by_type)
              .sort((a, b) => b[1] - a[1])
              .map(([type, count]) => (
                <div key={type} style={{ padding: '4px 10px', borderRadius: 6,
                                         background: 'rgba(0,212,170,0.07)',
                                         border: '1px solid rgba(0,212,170,0.14)' }}>
                  <span style={{ fontFamily: 'ui-monospace', fontSize: 9, color: C.teal }}>{type}</span>
                  <span style={{ fontFamily: 'ui-monospace', fontSize: 9, color: C.muted, marginLeft: 6 }}>
                    {count}
                  </span>
                </div>
              ))
            }
          </div>
        </Card>
      )}

    </div>
  );
}
