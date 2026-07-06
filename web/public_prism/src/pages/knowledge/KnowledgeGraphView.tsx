import { useEffect, useRef, useState, useCallback } from 'react';
import * as d3 from 'd3';
import { useQuery } from '@tanstack/react-query';
import { getGraph, type GraphNode, type GraphEdge } from '../../lib/knowledgeApi';

const TYPE_COLORS: Record<string, string> = {
  note:         '#C9A84C',
  conversation: '#00D4AA',
  research:     '#B08DE8',
  book:         '#6A9FD8',
  person:       '#E88C6A',
  idea:         '#F4D03F',
  decision:     '#C84848',
  daily:        '#4CAF50',
};

const REL_COLORS: Record<string, string> = {
  references:   '#00D4AA',
  extends:      '#C9A84C',
  contradicts:  '#C84848',
  summarizes:   '#B08DE8',
  implements:   '#6A9FD8',
  belongs_to:   '#888',
  generated_by: '#E88C6A',
  reviewed_by:  '#4CAF50',
  derived_from: '#F4D03F',
};

interface SimNode extends GraphNode {
  x?: number; y?: number; vx?: number; vy?: number; fx?: number | null; fy?: number | null;
}
interface SimEdge {
  source: SimNode | number; target: SimNode | number;
  relationship: string; weight: number;
}

export default function KnowledgeGraphView() {
  const svgRef = useRef<SVGSVGElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  const [selected, setSelected] = useState<GraphNode | null>(null);
  const [hoveredRel, setHoveredRel] = useState<string>('');
  const [filterType, setFilterType] = useState<string>('all');

  const { data, isLoading, error } = useQuery({
    queryKey: ['knowledge-graph'],
    queryFn: getGraph,
    refetchInterval: 30000,
  });

  const buildGraph = useCallback(() => {
    if (!svgRef.current || !containerRef.current || !data) return;
    const svg = d3.select(svgRef.current);
    svg.selectAll('*').remove();

    const { width, height } = containerRef.current.getBoundingClientRect();
    svg.attr('width', width).attr('height', height);

    const nodes: SimNode[] = (filterType === 'all'
      ? data.nodes
      : data.nodes.filter(n => n.note_type === filterType)
    ).map(n => ({ ...n }));

    const nodeIds = new Set(nodes.map(n => n.id));
    const edges: SimEdge[] = data.edges
      .filter(e => nodeIds.has(e.source_note_id) && nodeIds.has(e.target_note_id))
      .map(e => ({ ...e, source: e.source_note_id, target: e.target_note_id }));

    // Zoom layer
    const g = svg.append('g');
    svg.call(
      d3.zoom<SVGSVGElement, unknown>()
        .scaleExtent([0.1, 4])
        .on('zoom', (event) => g.attr('transform', event.transform))
    );

    // Arrow markers
    const defs = svg.append('defs');
    Object.entries(REL_COLORS).forEach(([rel, color]) => {
      defs.append('marker')
        .attr('id', `arrow-${rel}`)
        .attr('viewBox', '0 -5 10 10')
        .attr('refX', 18).attr('refY', 0)
        .attr('markerWidth', 6).attr('markerHeight', 6)
        .attr('orient', 'auto')
        .append('path').attr('d', 'M0,-5L10,0L0,5').attr('fill', color);
    });

    // Force simulation
    const simulation = d3.forceSimulation<SimNode>(nodes)
      .force('link', d3.forceLink<SimNode, SimEdge>(edges)
        .id(d => d.id).distance(80).strength(0.3))
      .force('charge', d3.forceManyBody().strength(-120))
      .force('center', d3.forceCenter(width / 2, height / 2))
      .force('collision', d3.forceCollide(24));

    // Edges
    const link = g.append('g').selectAll('line')
      .data(edges).join('line')
      .attr('stroke', d => REL_COLORS[d.relationship] || '#555')
      .attr('stroke-width', d => Math.max(0.5, d.weight))
      .attr('stroke-opacity', 0.6)
      .attr('marker-end', d => `url(#arrow-${d.relationship})`);

    // Nodes
    const node = g.append('g').selectAll<SVGGElement, SimNode>('g')
      .data(nodes).join('g')
      .attr('cursor', 'pointer')
      .call(
        d3.drag<SVGGElement, SimNode>()
          .on('start', (event, d) => { if (!event.active) simulation.alphaTarget(0.3).restart(); d.fx = d.x; d.fy = d.y; })
          .on('drag', (event, d) => { d.fx = event.x; d.fy = event.y; })
          .on('end', (event, d) => { if (!event.active) simulation.alphaTarget(0); d.fx = null; d.fy = null; })
      )
      .on('click', (_, d) => setSelected(d));

    node.append('circle')
      .attr('r', 10)
      .attr('fill', d => TYPE_COLORS[d.note_type] || '#888')
      .attr('stroke', '#1a1b2e')
      .attr('stroke-width', 2);

    node.append('text')
      .text(d => d.title.slice(0, 18) + (d.title.length > 18 ? '…' : ''))
      .attr('x', 14).attr('y', 4)
      .attr('fill', '#e0e0e0')
      .attr('font-size', '10px')
      .attr('font-family', 'Inter, sans-serif');

    simulation.on('tick', () => {
      link
        .attr('x1', d => (d.source as SimNode).x!)
        .attr('y1', d => (d.source as SimNode).y!)
        .attr('x2', d => (d.target as SimNode).x!)
        .attr('y2', d => (d.target as SimNode).y!);
      node.attr('transform', d => `translate(${d.x},${d.y})`);
    });

    return () => simulation.stop();
  }, [data, filterType]);

  useEffect(() => {
    const cleanup = buildGraph();
    return cleanup;
  }, [buildGraph]);

  useEffect(() => {
    const obs = new ResizeObserver(() => buildGraph());
    if (containerRef.current) obs.observe(containerRef.current);
    return () => obs.disconnect();
  }, [buildGraph]);

  const noteTypes = data ? [...new Set(data.nodes.map(n => n.note_type))] : [];

  return (
    <div style={{ height: '100%', display: 'flex', flexDirection: 'column', gap: 12 }}>
      {/* Controls */}
      <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap', alignItems: 'center' }}>
        <span style={{ color: '#888', fontSize: 12, fontFamily: 'Inter' }}>Filter:</span>
        {['all', ...noteTypes].map(t => (
          <button key={t} onClick={() => setFilterType(t)}
            style={{
              padding: '3px 10px', borderRadius: 4, fontSize: 11, fontFamily: 'Inter', cursor: 'pointer',
              background: filterType === t ? (TYPE_COLORS[t] || '#00D4AA') : 'rgba(255,255,255,0.06)',
              color: filterType === t ? '#0C0D18' : '#aaa',
              border: `1px solid ${filterType === t ? 'transparent' : 'rgba(255,255,255,0.1)'}`,
            }}>
            {t}
          </button>
        ))}
        {data && (
          <span style={{ marginLeft: 'auto', color: '#666', fontSize: 11, fontFamily: 'Inter' }}>
            {data.nodes.length} nodes · {data.edges.length} edges
          </span>
        )}
      </div>

      {/* Graph + Legend row */}
      <div style={{ display: 'flex', gap: 12, flex: 1, minHeight: 0 }}>
        {/* SVG Canvas */}
        <div ref={containerRef} style={{ flex: 1, background: 'rgba(255,255,255,0.03)', borderRadius: 8, border: '1px solid rgba(255,255,255,0.08)', position: 'relative', overflow: 'hidden' }}>
          {isLoading && (
            <div style={{ position: 'absolute', inset: 0, display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#666', fontFamily: 'Inter', fontSize: 13 }}>
              Loading knowledge graph…
            </div>
          )}
          {error && (
            <div style={{ position: 'absolute', inset: 0, display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#C84848', fontFamily: 'Inter', fontSize: 13 }}>
              Failed to load graph — is Oracle Temple running?
            </div>
          )}
          {!isLoading && !error && data?.nodes.length === 0 && (
            <div style={{ position: 'absolute', inset: 0, display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', gap: 8, color: '#666', fontFamily: 'Inter', fontSize: 13 }}>
              <span style={{ fontSize: 28 }}>◈</span>
              <span>No knowledge yet. Ingest a note to see the graph.</span>
            </div>
          )}
          <svg ref={svgRef} style={{ width: '100%', height: '100%' }} />
        </div>

        {/* Side panel */}
        <div style={{ width: 220, display: 'flex', flexDirection: 'column', gap: 10 }}>
          {/* Selected note */}
          {selected && (
            <div style={{ background: 'rgba(255,255,255,0.05)', borderRadius: 8, border: '1px solid rgba(255,255,255,0.1)', padding: 12 }}>
              <div style={{ color: TYPE_COLORS[selected.note_type] || '#C9A84C', fontSize: 10, fontFamily: 'Inter', marginBottom: 4, textTransform: 'uppercase', letterSpacing: '0.1em' }}>
                {selected.note_type}
              </div>
              <div style={{ color: '#e0e0e0', fontSize: 13, fontFamily: 'Cinzel, serif', fontWeight: 600, marginBottom: 6 }}>
                {selected.title}
              </div>
              <div style={{ color: '#666', fontSize: 10, fontFamily: 'Inter' }}>
                {new Date(selected.created_at).toLocaleDateString()}
              </div>
              <button onClick={() => setSelected(null)}
                style={{ marginTop: 8, width: '100%', padding: '4px', background: 'rgba(255,255,255,0.06)', border: '1px solid rgba(255,255,255,0.1)', borderRadius: 4, color: '#888', fontSize: 11, cursor: 'pointer', fontFamily: 'Inter' }}>
                Clear
              </button>
            </div>
          )}

          {/* Relationship legend */}
          <div style={{ background: 'rgba(255,255,255,0.03)', borderRadius: 8, border: '1px solid rgba(255,255,255,0.08)', padding: 12 }}>
            <div style={{ color: '#666', fontSize: 10, fontFamily: 'Inter', marginBottom: 8, textTransform: 'uppercase', letterSpacing: '0.1em' }}>Relationships</div>
            {Object.entries(REL_COLORS).map(([rel, color]) => (
              <div key={rel} style={{ display: 'flex', alignItems: 'center', gap: 6, marginBottom: 5 }}>
                <div style={{ width: 20, height: 2, background: color, borderRadius: 1 }} />
                <span style={{ color: '#999', fontSize: 10, fontFamily: 'Inter' }}>{rel}</span>
              </div>
            ))}
          </div>

          {/* Node type legend */}
          <div style={{ background: 'rgba(255,255,255,0.03)', borderRadius: 8, border: '1px solid rgba(255,255,255,0.08)', padding: 12 }}>
            <div style={{ color: '#666', fontSize: 10, fontFamily: 'Inter', marginBottom: 8, textTransform: 'uppercase', letterSpacing: '0.1em' }}>Node Types</div>
            {Object.entries(TYPE_COLORS).map(([type, color]) => (
              <div key={type} style={{ display: 'flex', alignItems: 'center', gap: 6, marginBottom: 5 }}>
                <div style={{ width: 10, height: 10, borderRadius: '50%', background: color }} />
                <span style={{ color: '#999', fontSize: 10, fontFamily: 'Inter' }}>{type}</span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
