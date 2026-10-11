import { useState, useRef } from 'react';
import { search, type SearchResult } from '../../lib/knowledgeApi';

const MODES = [
  { id: 'semantic',  label: 'Semantic',  color: '#00D4AA' },
  { id: 'fulltext',  label: 'Full Text', color: '#C9A84C' },
  { id: 'tag',       label: 'Tags',      color: '#B08DE8' },
  { id: 'timeline',  label: 'Timeline',  color: '#6A9FD8' },
  { id: 'project',   label: 'Projects',  color: '#E88C6A' },
  { id: 'people',    label: 'People',    color: '#4CAF50' },
  { id: 'reference', label: 'References', color: '#F4D03F' },
];

const TYPE_COLORS: Record<string, string> = {
  note: '#C9A84C', conversation: '#00D4AA', research: '#B08DE8',
  book: '#6A9FD8', person: '#E88C6A', idea: '#F4D03F', decision: '#C84848', daily: '#4CAF50',
};

export default function SemanticSearchView() {
  const [query, setQuery] = useState('');
  const [activeModes, setActiveModes] = useState<string[]>(['semantic', 'fulltext', 'tag']);
  const [results, setResults] = useState<SearchResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const inputRef = useRef<HTMLInputElement>(null);

  const toggleMode = (mode: string) => {
    setActiveModes(prev =>
      prev.includes(mode) ? prev.filter(m => m !== mode) : [...prev, mode]
    );
  };

  const handleSearch = async (e?: React.FormEvent) => {
    e?.preventDefault();
    if (!query.trim()) return;
    setLoading(true);
    setError('');
    try {
      const res = await search(query, activeModes, 20);
      setResults(res);
    } catch (err) {
      setError('Search failed — is Oracle Temple running?');
    } finally {
      setLoading(false);
    }
  };

  const totalResults = results
    ? Object.values(results).reduce((sum, arr) => sum + (Array.isArray(arr) ? arr.length : 0), 0)
    : 0;

  return (
    <div style={{ height: '100%', display: 'flex', flexDirection: 'column', gap: 16 }}>
      {/* Search form */}
      <form onSubmit={handleSearch} style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
        <div style={{ display: 'flex', gap: 8 }}>
          <input
            ref={inputRef}
            value={query}
            onChange={e => setQuery(e.target.value)}
            placeholder="Search the Knowledge Vault…"
            style={{
              flex: 1, background: 'rgba(255,255,255,0.06)', border: '1px solid rgba(255,255,255,0.15)',
              borderRadius: 8, padding: '10px 14px', color: '#e0e0e0', fontFamily: 'Inter', fontSize: 14,
              outline: 'none',
            }}
          />
          <button type="submit" disabled={loading || !query.trim()}
            style={{
              padding: '10px 20px', borderRadius: 8, background: '#00D4AA', color: '#0C0D18',
              border: 'none', fontFamily: 'Inter', fontWeight: 600, fontSize: 13, cursor: 'pointer',
              opacity: loading || !query.trim() ? 0.5 : 1, transition: 'opacity 0.15s',
            }}>
            {loading ? '…' : 'Search'}
          </button>
        </div>

        {/* Mode toggles */}
        <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap' }}>
          {MODES.map(mode => (
            <button
              key={mode.id}
              type="button"
              onClick={() => toggleMode(mode.id)}
              style={{
                padding: '3px 10px', borderRadius: 4, fontSize: 11, fontFamily: 'Inter', cursor: 'pointer',
                background: activeModes.includes(mode.id) ? mode.color : 'rgba(255,255,255,0.04)',
                color: activeModes.includes(mode.id) ? '#0C0D18' : '#888',
                border: `1px solid ${activeModes.includes(mode.id) ? 'transparent' : 'rgba(255,255,255,0.1)'}`,
                transition: 'all 0.15s',
              }}>
              {mode.label}
            </button>
          ))}
        </div>
      </form>

      {error && (
        <div style={{ color: '#C84848', fontFamily: 'Inter', fontSize: 13, padding: '8px 12px', background: 'rgba(200,72,72,0.1)', borderRadius: 6, border: '1px solid rgba(200,72,72,0.2)' }}>
          {error}
        </div>
      )}

      {/* Results */}
      {results && (
        <div style={{ flex: 1, overflowY: 'auto', display: 'flex', flexDirection: 'column', gap: 16 }}>
          <div style={{ color: '#666', fontFamily: 'Inter', fontSize: 11 }}>
            {totalResults} results across {Object.keys(results).length} modes
          </div>

          {MODES.map(mode => {
            const modeResults = results[mode.id as keyof SearchResult] as unknown[];
            if (!modeResults || modeResults.length === 0) return null;
            return (
              <ResultSection key={mode.id} title={mode.label} color={mode.color} items={modeResults} />
            );
          })}
        </div>
      )}

      {!results && !loading && (
        <div style={{ flex: 1, display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', gap: 8, color: '#555' }}>
          <div style={{ fontSize: 36, color: '#333' }}>⟐</div>
          <div style={{ fontFamily: 'Cinzel, serif', fontSize: 14, color: '#666' }}>Query the Knowledge Vault</div>
          <div style={{ fontFamily: 'Inter', fontSize: 11, color: '#444', textAlign: 'center', maxWidth: 320 }}>
            Semantic search uses AI embeddings to find conceptually related knowledge.<br />
            Full-text matches exact words. Tags find by label. Timeline searches events.
          </div>
        </div>
      )}
    </div>
  );
}

function ResultSection({ title, color, items }: { title: string; color: string; items: unknown[] }) {
  const [expanded, setExpanded] = useState(true);
  return (
    <div>
      <button
        onClick={() => setExpanded(!expanded)}
        style={{ display: 'flex', alignItems: 'center', gap: 8, background: 'none', border: 'none', cursor: 'pointer', marginBottom: 8, padding: 0 }}>
        <div style={{ width: 8, height: 8, borderRadius: '50%', background: color }} />
        <span style={{ color, fontFamily: 'Inter', fontSize: 11, textTransform: 'uppercase', letterSpacing: '0.08em' }}>{title}</span>
        <span style={{ color: '#555', fontFamily: 'Inter', fontSize: 11 }}>({items.length})</span>
        <span style={{ color: '#555', fontSize: 10, marginLeft: 4 }}>{expanded ? '▲' : '▼'}</span>
      </button>
      {expanded && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
          {items.slice(0, 10).map((item, i) => (
            <ResultCard key={i} item={item as Record<string, unknown>} color={color} />
          ))}
          {items.length > 10 && (
            <div style={{ color: '#555', fontFamily: 'Inter', fontSize: 11, padding: '4px 0' }}>
              +{items.length - 10} more results
            </div>
          )}
        </div>
      )}
    </div>
  );
}

function ResultCard({ item, color }: { item: Record<string, unknown>; color: string }) {
  const title = String(item.title || item.name || item.event_type || 'Untitled');
  const type = String(item.note_type || item.type || '');
  const score = typeof item.score === 'number' ? item.score : null;
  const content = String(item.content || item.description || item.target_ref || '').slice(0, 120);
  const date = String(item.created_at || '').slice(0, 10);
  const typeColor = (TYPE_COLORS[type] || color);

  return (
    <div style={{
      background: 'rgba(255,255,255,0.03)', borderRadius: 6, padding: '10px 12px',
      border: '1px solid rgba(255,255,255,0.07)', display: 'flex', flexDirection: 'column', gap: 4,
    }}>
      <div style={{ display: 'flex', alignItems: 'baseline', gap: 8 }}>
        {type && (
          <span style={{ color: typeColor, fontSize: 9, fontFamily: 'Inter', textTransform: 'uppercase', letterSpacing: '0.1em', flexShrink: 0 }}>
            {type}
          </span>
        )}
        <span style={{ color: '#d0d0d0', fontSize: 13, fontFamily: 'Inter', fontWeight: 500, flex: 1 }}>
          {title}
        </span>
        {score !== null && (
          <span style={{ color: color, fontSize: 10, fontFamily: 'monospace', flexShrink: 0 }}>
            {(score * 100).toFixed(0)}%
          </span>
        )}
      </div>
      {content && (
        <div style={{ color: '#666', fontSize: 11, fontFamily: 'Inter', lineHeight: 1.4 }}>
          {content}{content.length >= 120 ? '…' : ''}
        </div>
      )}
      {date && (
        <div style={{ color: '#444', fontSize: 10, fontFamily: 'Inter' }}>{date}</div>
      )}
    </div>
  );
}
