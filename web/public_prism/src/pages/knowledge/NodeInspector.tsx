/**
 * NodeInspector — Graph Explorer node detail panel.
 *
 * Shows:
 *   • Full node metadata (type, UUID, created, embedding status)
 *   • Outbound edges (what this node references)
 *   • Inbound edges (what references this node)
 *   • Neighbor drill-down link
 *
 * Used as the side-panel in KnowledgeGraphView when a node is selected.
 * Do NOT redesign the overall KnowledgeGraphView layout — this replaces
 * only the small selected-node card that existed before.
 */

import { useQuery } from '@tanstack/react-query';
import { getNode, type NodeDetail, type EdgeDetail } from '../../lib/knowledgeApi';

const C = {
  teal:   '#00D4AA',
  gold:   '#C9A84C',
  purple: '#B08DE8',
  red:    '#C84848',
  muted:  'rgba(232,232,232,0.45)',
  dim:    'rgba(232,232,232,0.18)',
  border: 'rgba(255,255,255,0.08)',
  card:   'rgba(14,17,32,0.80)',
};

const TYPE_COLORS: Record<string, string> = {
  document: '#6A9FD8', conversation: '#00D4AA', scroll: '#C9A84C',
  chapter: '#B08DE8', person: '#E88C6A', concept: '#F4D03F',
  note: '#C9A84C', project: '#4CAF50', task: '#C84848',
};

function typeColor(t: string) { return TYPE_COLORS[t] || '#888'; }

function Chip({ label, color = C.teal }: { label: string; color?: string }) {
  return (
    <span style={{
      padding: '2px 7px', borderRadius: 4, fontSize: 9, fontFamily: 'ui-monospace, monospace',
      background: `${color}18`, border: `1px solid ${color}40`, color, letterSpacing: '0.06em',
    }}>{label}</span>
  );
}

function EdgeRow({ edge, direction }: { edge: EdgeDetail; direction: 'out' | 'in' }) {
  const title   = direction === 'out' ? edge.target_title : edge.source_title;
  const type    = direction === 'out' ? edge.target_type  : edge.source_type;
  const relColor = edge.weight >= 0.65 ? C.teal : edge.weight >= 0.4 ? C.gold : C.muted;
  return (
    <div style={{
      display: 'flex', flexDirection: 'column', gap: 2,
      padding: '5px 0', borderBottom: `1px solid ${C.border}`,
    }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
        <span style={{ fontFamily: 'ui-monospace', fontSize: 8, color: relColor, minWidth: 18 }}>
          {direction === 'out' ? '→' : '←'}
        </span>
        <span style={{
          fontFamily: 'ui-monospace', fontSize: 9, color: relColor,
          background: `${relColor}12`, padding: '1px 5px', borderRadius: 3,
          border: `1px solid ${relColor}30`,
        }}>{edge.relationship}</span>
        {type && <Chip label={type} color={typeColor(type)} />}
      </div>
      {title && (
        <span style={{
          fontFamily: 'Inter, sans-serif', fontSize: 10, color: C.muted,
          paddingLeft: 24, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap',
        }} title={title}>{title}</span>
      )}
      <span style={{ paddingLeft: 24, fontFamily: 'ui-monospace', fontSize: 8, color: C.dim }}>
        weight {edge.weight.toFixed(2)}
      </span>
    </div>
  );
}

interface Props {
  noteId: number;
  title: string;
  noteType: string;
  createdAt: string;
  onClear: () => void;
  onDrillDown?: (noteId: number) => void;
}

export default function NodeInspector({ noteId, title, noteType, createdAt, onClear, onDrillDown }: Props) {
  const { data, isLoading } = useQuery<NodeDetail>({
    queryKey: ['node-detail', noteId],
    queryFn: () => getNode(noteId),
    staleTime: 30000,
  });

  const color = typeColor(noteType);

  return (
    <div style={{
      background: C.card, border: `1px solid ${color}40`, borderRadius: 10,
      padding: 12, display: 'flex', flexDirection: 'column', gap: 8,
      maxHeight: '100%', overflow: 'hidden',
    }}>
      {/* Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
        <div style={{ flex: 1, minWidth: 0 }}>
          <Chip label={noteType} color={color} />
          <div style={{
            fontFamily: 'Cinzel, serif', fontSize: 12, color: '#e0e0e0', fontWeight: 600,
            marginTop: 5, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap',
          }} title={title}>{title}</div>
          <div style={{ fontFamily: 'ui-monospace', fontSize: 9, color: C.dim, marginTop: 3 }}>
            {new Date(createdAt).toLocaleDateString()}
          </div>
        </div>
        <button onClick={onClear} style={{
          padding: '3px 8px', background: 'rgba(255,255,255,0.05)', border: `1px solid ${C.border}`,
          borderRadius: 4, color: C.dim, fontSize: 10, cursor: 'pointer', fontFamily: 'Inter', marginLeft: 6,
        }}>✕</button>
      </div>

      {/* Stable ID */}
      {data?.node?.uuid && (
        <div style={{ borderTop: `1px solid ${C.border}`, paddingTop: 6 }}>
          <div style={{ fontFamily: 'ui-monospace', fontSize: 8, color: C.dim, marginBottom: 2 }}>STABLE ID</div>
          <div style={{
            fontFamily: 'ui-monospace', fontSize: 8, color: C.muted,
            overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap',
          }} title={data.node.uuid}>{data.node.uuid}</div>
        </div>
      )}

      {/* Degree summary */}
      {data && (
        <div style={{ display: 'flex', gap: 8 }}>
          <div style={{ flex: 1, padding: '5px 8px', background: 'rgba(0,212,170,0.06)', borderRadius: 6, textAlign: 'center' }}>
            <div style={{ fontFamily: 'Cinzel', fontSize: 14, color: C.teal }}>{data.outbound_edges.length}</div>
            <div style={{ fontFamily: 'Inter', fontSize: 8, color: C.dim }}>out</div>
          </div>
          <div style={{ flex: 1, padding: '5px 8px', background: 'rgba(201,168,76,0.06)', borderRadius: 6, textAlign: 'center' }}>
            <div style={{ fontFamily: 'Cinzel', fontSize: 14, color: C.gold }}>{data.inbound_edges.length}</div>
            <div style={{ fontFamily: 'Inter', fontSize: 8, color: C.dim }}>in</div>
          </div>
          <div style={{ flex: 1, padding: '5px 8px', background: 'rgba(176,141,232,0.06)', borderRadius: 6, textAlign: 'center' }}>
            <div style={{ fontFamily: 'Cinzel', fontSize: 14, color: C.purple }}>{data.degree}</div>
            <div style={{ fontFamily: 'Inter', fontSize: 8, color: C.dim }}>total</div>
          </div>
        </div>
      )}

      {/* Edges — scrollable */}
      {isLoading && (
        <div style={{ fontFamily: 'Inter', fontSize: 10, color: C.dim, textAlign: 'center', padding: 8 }}>
          Loading edges…
        </div>
      )}

      {data && (
        <div style={{ overflowY: 'auto', flex: 1, minHeight: 0 }}>
          {data.outbound_edges.length > 0 && (
            <div>
              <div style={{ fontFamily: 'Inter', fontSize: 9, color: C.dim, letterSpacing: '0.1em',
                            textTransform: 'uppercase', marginBottom: 3 }}>Outbound</div>
              {data.outbound_edges.slice(0, 8).map((e, i) => (
                <EdgeRow key={i} edge={e} direction="out" />
              ))}
            </div>
          )}
          {data.inbound_edges.length > 0 && (
            <div style={{ marginTop: 8 }}>
              <div style={{ fontFamily: 'Inter', fontSize: 9, color: C.dim, letterSpacing: '0.1em',
                            textTransform: 'uppercase', marginBottom: 3 }}>Inbound</div>
              {data.inbound_edges.slice(0, 8).map((e, i) => (
                <EdgeRow key={i} edge={e} direction="in" />
              ))}
            </div>
          )}
          {data.degree === 0 && (
            <div style={{ fontFamily: 'Inter', fontSize: 10, color: C.dim, textAlign: 'center', padding: '12px 0' }}>
              No connections yet
            </div>
          )}
        </div>
      )}

      {/* Drill-down */}
      {onDrillDown && (
        <button onClick={() => onDrillDown(noteId)} style={{
          width: '100%', padding: '5px', background: `${color}14`,
          border: `1px solid ${color}35`, borderRadius: 6,
          color, fontSize: 10, cursor: 'pointer', fontFamily: 'Inter',
          letterSpacing: '0.06em', textTransform: 'uppercase',
        }}>
          ◈ Explore Neighbors
        </button>
      )}
    </div>
  );
}
