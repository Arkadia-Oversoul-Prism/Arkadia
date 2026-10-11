import React, { useEffect, useMemo, useRef, useState } from 'react';
import * as d3 from 'd3';
import { apiFetch } from '../../lib/apiClient';

interface NodeData { id: string; type: string; label: string; classification?: string; }
interface EdgeData { from: string; to: string; type: string; classification?: string; provenance?: string; evidence_id?: string; }
interface GraphData { project_id: string; kind: string; nodes: NodeData[]; edges: EdgeData[]; counts?: { nodes: number; edges: number }; limitations?: string[]; }

const TYPE_COLORS: Record<string, string> = {
  Project: '#C9A84C', File: '#6A9FD8', Repository: '#B08DE8', Task: '#C84848',
  Memory: '#00D4AA', Conversation: '#6A9FD8', Event: '#888',
};

export default function ProjectKnowledgeGraph({ projectId }: { projectId: string }) {
  const svgRef = useRef<SVGSVGElement>(null);
  const canvasRef = useRef<HTMLDivElement>(null);
  const [data, setData] = useState<GraphData | null>(null);
  const [selected, setSelected] = useState<NodeData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let live = true;
    setLoading(true); setError(null); setSelected(null);
    apiFetch(`/solspire/projects/${projectId}/knowledge/graph`, { headers: {} })
      .then(async r => { const d = await r.json(); if (!r.ok) throw new Error(d.detail || `${r.status}`); return d as GraphData; })
      .then(d => { if (live) setData(d); })
      .catch(e => { if (live) setError(e.message || 'Unable to load project graph'); })
      .finally(() => { if (live) setLoading(false); });
    return () => { live = false; };
  }, [projectId]);

  const selectedEdges = useMemo(() => {
    if (!selected || !data) return [];
    return data.edges.filter(e => e.from === selected.id || e.to === selected.id).map(e => ({ ...e, direction: e.from === selected.id ? 'out' : 'in' }));
  }, [data, selected]);

  useEffect(() => {
    if (!data || !svgRef.current || !canvasRef.current) return;
    const svg = d3.select(svgRef.current);
    svg.selectAll('*').remove();
    const { width, height } = canvasRef.current.getBoundingClientRect();
    const nodes = data.nodes.map(n => ({ ...n }));
    const byId = new Map(nodes.map(n => [n.id, n]));
    const edges = data.edges.filter(e => byId.has(e.from) && byId.has(e.to)).map(e => ({ ...e, source: e.from, target: e.to }));
    const g = svg.append('g');
    svg.call(d3.zoom<SVGSVGElement, unknown>().scaleExtent([0.35, 4]).on('zoom', e => g.attr('transform', e.transform)));
    const simulation = d3.forceSimulation(nodes as any)
      .force('link', d3.forceLink(edges as any).id((d: any) => d.id).distance(75).strength(.45))
      .force('charge', d3.forceManyBody().strength(-180))
      .force('center', d3.forceCenter(width / 2, height / 2))
      .force('collision', d3.forceCollide(28));
    const link = g.append('g').selectAll('line').data(edges).join('line')
      .attr('stroke', 'rgba(201,168,76,.28)').attr('stroke-width', 1);
    const node = g.append('g').selectAll<SVGGElement, any>('g').data(nodes).join('g')
      .attr('cursor', 'pointer')
      .on('click', (_, d) => setSelected(d))
      .call(d3.drag<SVGGElement, any>()
        .on('start', (e, d) => { if (!e.active) simulation.alphaTarget(.25).restart(); d.fx = d.x; d.fy = d.y; })
        .on('drag', (e, d) => { d.fx = e.x; d.fy = e.y; })
        .on('end', (e, d) => { if (!e.active) simulation.alphaTarget(0); d.fx = null; d.fy = null; }));
    node.append('circle').attr('r', 10).attr('fill', d => TYPE_COLORS[d.type] || '#888').attr('stroke', '#0A0B14').attr('stroke-width', 2);
    node.append('text').text(d => d.label.length > 18 ? `${d.label.slice(0, 18)}…` : d.label)
      .attr('x', 14).attr('y', 4).attr('fill', '#D4DFE8').attr('font-size', 10).attr('font-family', 'Inter, sans-serif');
    simulation.on('tick', () => {
      link.attr('x1', (d: any) => d.source.x).attr('y1', (d: any) => d.source.y).attr('x2', (d: any) => d.target.x).attr('y2', (d: any) => d.target.y);
      node.attr('transform', (d: any) => `translate(${d.x},${d.y})`);
    });
    return () => simulation.stop();
  }, [data]);

  return <div style={{ display: 'grid', gridTemplateColumns: 'minmax(0,1fr) 260px', gap: 12 }}>
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 7 }}>
        <span style={{ fontSize: 10, letterSpacing: '.14em', textTransform: 'uppercase', color: 'rgba(0,212,170,.55)', fontFamily: 'ui-monospace,monospace' }}>Derived project graph</span>
        {data?.counts && <span style={{ fontSize: 9, color: 'rgba(212,223,232,.3)', fontFamily: 'ui-monospace,monospace' }}>{data.counts.nodes} nodes · {data.counts.edges} edges</span>}
      </div>
      <div ref={canvasRef} style={{ height: 430, minHeight: 320, background: 'rgba(5,7,15,.72)', border: '1px solid rgba(0,212,170,.12)', borderRadius: 9, overflow: 'hidden', position: 'relative', touchAction: 'none' }}>
        {loading && <div style={{ position: 'absolute', inset: 0, display: 'grid', placeItems: 'center', color: 'rgba(212,223,232,.35)', fontSize: 12 }}>Loading project knowledge…</div>}
        {!loading && error && <div style={{ position: 'absolute', inset: 0, display: 'grid', placeItems: 'center', color: '#C84848', fontSize: 12, padding: 20, textAlign: 'center' }}>Project knowledge could not be loaded: {error}</div>}
        {!loading && !error && data?.nodes.length === 0 && <div style={{ position: 'absolute', inset: 0, display: 'grid', placeItems: 'center', color: 'rgba(212,223,232,.3)', fontSize: 12 }}>No source-backed project knowledge yet. Ingest a file or create project activity first.</div>}
        <svg ref={svgRef} style={{ width: '100%', height: '100%' }} />
      </div>
      {data?.limitations?.length ? <div style={{ marginTop: 7, fontSize: 9, lineHeight: 1.5, color: 'rgba(212,223,232,.25)' }}>Bounded projection · {data.limitations[0]}</div> : null}
    </div>
    <aside style={{ background: 'rgba(14,17,32,.72)', border: '1px solid rgba(255,255,255,.07)', borderRadius: 9, padding: 12, minHeight: 260 }}>
      <div style={{ fontSize: 9, letterSpacing: '.15em', textTransform: 'uppercase', color: 'rgba(201,168,76,.55)', fontFamily: 'ui-monospace,monospace', marginBottom: 8 }}>Node inspector</div>
      {!selected ? <div style={{ color: 'rgba(212,223,232,.28)', fontSize: 11, lineHeight: 1.6 }}>Select a node to inspect its source-backed identity and relationships.</div> : <>
        <div style={{ display: 'flex', alignItems: 'center', gap: 7 }}><span style={{ width: 9, height: 9, borderRadius: '50%', background: TYPE_COLORS[selected.type] || '#888' }} /><strong style={{ color: '#E9E7DF', fontSize: 13 }}>{selected.label}</strong></div>
        <div style={{ marginTop: 5, color: 'rgba(212,223,232,.35)', fontSize: 9, fontFamily: 'ui-monospace,monospace' }}>{selected.type} · {selected.classification || 'SOURCE-BACKED'}</div>
        <div style={{ marginTop: 10, paddingTop: 8, borderTop: '1px solid rgba(255,255,255,.06)', color: 'rgba(212,223,232,.3)', fontSize: 8, fontFamily: 'ui-monospace,monospace', wordBreak: 'break-all' }}>{selected.id}</div>
        <div style={{ marginTop: 12, fontSize: 9, color: 'rgba(0,212,170,.5)', letterSpacing: '.12em', textTransform: 'uppercase' }}>Relationships · {selectedEdges.length}</div>
        <div style={{ marginTop: 5, maxHeight: 240, overflowY: 'auto' }}>{selectedEdges.map((e, i) => { const other = e.direction === 'out' ? e.to : e.from; const n = data?.nodes.find(x => x.id === other); return <button key={`${e.evidence_id || i}`} type="button" onClick={() => n && setSelected(n)} style={{ display: 'block', width: '100%', textAlign: 'left', padding: '7px 0', border: 0, borderBottom: '1px solid rgba(255,255,255,.04)', background: 'transparent', color: 'rgba(212,223,232,.48)', cursor: n ? 'pointer' : 'default', fontSize: 10 }}><span style={{ color: '#C9A84C' }}>{e.direction === 'out' ? '→' : '←'} {e.type}</span><br/><span>{n?.label || other}</span></button>; })}</div>
      </>}
    </aside>
  </div>;
}
