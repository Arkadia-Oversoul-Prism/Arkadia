import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { AreaChart, Area, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid } from 'recharts';
import { getRecentTimeline, getTimeline, type TimelineEvent } from '../../lib/knowledgeApi';

const EVENT_COLORS: Record<string, string> = {
  conversation:       '#00D4AA',
  prompt:             '#B08DE8',
  response:           '#6A9FD8',
  knowledge_created:  '#C9A84C',
  knowledge_modified: '#E88C6A',
  review:             '#F4D03F',
  decision:           '#C84848',
  sync:               '#4CAF50',
  error:              '#C84848',
  pipeline_run:       '#00D4AA',
  embed_complete:     '#B08DE8',
  graph_link:         '#6A9FD8',
  search_query:       '#888',
  provider_call:      '#C9A84C',
};

const EVENT_TYPES = [
  'all', 'conversation', 'knowledge_created', 'knowledge_modified',
  'decision', 'embed_complete', 'graph_link', 'provider_call',
];

function formatTime(iso: string) {
  const d = new Date(iso);
  return d.toLocaleString(undefined, { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' });
}

function buildChartData(events: TimelineEvent[]) {
  // Group events by hour-bucket for the area chart
  const buckets: Record<string, Record<string, number>> = {};
  events.forEach(e => {
    const d = new Date(e.created_at);
    const key = `${d.getMonth() + 1}/${d.getDate()} ${d.getHours()}:00`;
    if (!buckets[key]) buckets[key] = {};
    buckets[key][e.event_type] = (buckets[key][e.event_type] || 0) + 1;
    buckets[key].total = (buckets[key].total || 0) + 1;
  });
  // Sort by epoch (reliable chronological order), then take last 24 buckets
  return Object.entries(buckets)
    .map(([time, counts]) => ({ time, epoch: new Date(time.replace(/^(\d+)\/(\d+) (\d+):00$/, '2026-$1-$2T$3:00:00')).getTime(), ...counts }))
    .sort((a, b) => a.epoch - b.epoch)
    .slice(-24)
    .map(({ epoch: _epoch, ...rest }) => rest);
}

export default function TimelineView() {
  const [filter, setFilter] = useState('all');
  const [limit, setLimit] = useState(100);

  const { data: events = [], isLoading, error } = useQuery({
    queryKey: ['timeline', filter, limit],
    queryFn: () => filter === 'all'
      ? getRecentTimeline(limit)
      : getTimeline({ event_type: filter, limit }),
    refetchInterval: 15000,
  });

  const chartData = buildChartData(events);

  return (
    <div style={{ height: '100%', display: 'flex', flexDirection: 'column', gap: 16 }}>
      {/* Area chart */}
      <div style={{ background: 'rgba(255,255,255,0.03)', borderRadius: 8, border: '1px solid rgba(255,255,255,0.08)', padding: 16, height: 160 }}>
        <div style={{ color: '#666', fontSize: 10, fontFamily: 'Inter', marginBottom: 8, textTransform: 'uppercase', letterSpacing: '0.1em' }}>
          Event Frequency (last 24 hours)
        </div>
        <ResponsiveContainer width="100%" height={110}>
          <AreaChart data={chartData} margin={{ top: 0, right: 0, left: -30, bottom: 0 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
            <XAxis dataKey="time" tick={{ fill: '#666', fontSize: 9 }} />
            <YAxis tick={{ fill: '#666', fontSize: 9 }} allowDecimals={false} />
            <Tooltip
              contentStyle={{ background: '#1a1b2e', border: '1px solid rgba(255,255,255,0.1)', borderRadius: 6, color: '#e0e0e0', fontSize: 11 }}
              labelStyle={{ color: '#C9A84C' }}
            />
            <Area type="monotone" dataKey="total" stroke="#00D4AA" fill="rgba(0,212,170,0.15)" strokeWidth={2} />
          </AreaChart>
        </ResponsiveContainer>
      </div>

      {/* Filters + count */}
      <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap', alignItems: 'center' }}>
        {EVENT_TYPES.map(t => (
          <button key={t} onClick={() => setFilter(t)}
            style={{
              padding: '3px 10px', borderRadius: 4, fontSize: 11, fontFamily: 'Inter', cursor: 'pointer',
              background: filter === t ? (EVENT_COLORS[t] || '#00D4AA') : 'rgba(255,255,255,0.06)',
              color: filter === t ? '#0C0D18' : '#aaa',
              border: `1px solid ${filter === t ? 'transparent' : 'rgba(255,255,255,0.1)'}`,
            }}>
            {t}
          </button>
        ))}
        <select value={limit} onChange={e => setLimit(Number(e.target.value))}
          style={{ marginLeft: 'auto', background: 'rgba(255,255,255,0.06)', border: '1px solid rgba(255,255,255,0.1)', borderRadius: 4, color: '#aaa', fontSize: 11, padding: '3px 6px', fontFamily: 'Inter' }}>
          {[50, 100, 200, 500].map(l => <option key={l} value={l}>{l} events</option>)}
        </select>
        <span style={{ color: '#666', fontSize: 11, fontFamily: 'Inter' }}>{events.length} events</span>
      </div>

      {/* Event stream */}
      <div style={{ flex: 1, overflowY: 'auto', display: 'flex', flexDirection: 'column', gap: 6 }}>
        {isLoading && (
          <div style={{ color: '#666', fontFamily: 'Inter', fontSize: 13, padding: 20, textAlign: 'center' }}>Loading timeline…</div>
        )}
        {error && (
          <div style={{ color: '#C84848', fontFamily: 'Inter', fontSize: 13, padding: 20, textAlign: 'center' }}>Failed to load timeline — is Oracle Temple running?</div>
        )}
        {!isLoading && events.length === 0 && (
          <div style={{ color: '#666', fontFamily: 'Inter', fontSize: 13, padding: 20, textAlign: 'center' }}>
            <div style={{ fontSize: 28, marginBottom: 8 }}>◎</div>
            No events yet. Every action will appear here.
          </div>
        )}
        {events.map(event => (
          <EventRow key={event.id} event={event} />
        ))}
      </div>
    </div>
  );
}

function EventRow({ event }: { event: TimelineEvent }) {
  const [expanded, setExpanded] = useState(false);
  const color = EVENT_COLORS[event.event_type] || '#888';
  const payloadStr = typeof event.payload === 'object'
    ? JSON.stringify(event.payload, null, 2)
    : String(event.payload);
  const preview = typeof event.payload === 'object'
    ? (event.payload.title || event.payload.note_id || event.payload.type || event.event_type)
    : String(event.payload).slice(0, 60);

  return (
    <div
      onClick={() => setExpanded(!expanded)}
      style={{
        background: 'rgba(255,255,255,0.03)', borderRadius: 6, padding: '8px 12px',
        border: `1px solid rgba(255,255,255,${expanded ? '0.12' : '0.06'})`,
        cursor: 'pointer', transition: 'border-color 0.15s',
      }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
        <div style={{ width: 8, height: 8, borderRadius: '50%', background: color, flexShrink: 0 }} />
        <span style={{ color, fontSize: 10, fontFamily: 'Inter', textTransform: 'uppercase', letterSpacing: '0.08em', width: 140, flexShrink: 0 }}>
          {event.event_type}
        </span>
        <span style={{ color: '#ccc', fontSize: 12, fontFamily: 'Inter', flex: 1, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
          {String(preview)}
        </span>
        {event.provider && (
          <span style={{ color: '#666', fontSize: 10, fontFamily: 'Inter', flexShrink: 0 }}>{event.provider}</span>
        )}
        <span style={{ color: '#555', fontSize: 10, fontFamily: 'Inter', flexShrink: 0 }}>
          {formatTime(event.created_at)}
        </span>
      </div>
      {expanded && (
        <pre style={{ marginTop: 8, color: '#888', fontSize: 10, fontFamily: 'monospace', overflow: 'auto', maxHeight: 120, background: 'rgba(0,0,0,0.3)', borderRadius: 4, padding: 8 }}>
          {payloadStr}
        </pre>
      )}
    </div>
  );
}
