import React, { ReactNode, useEffect, useState } from 'react';
import { search as searchKnowledge } from '../lib/knowledgeApi';
import './experience-consolidation.css';

type Surface = 'NovaNet' | 'Solariun' | 'SolSpire' | 'Spiral Command';
type Navigate = (view: string) => void;

const SURFACES: Array<{ id: Surface; view: string; kind: string }> = [
  { id: 'NovaNet', view: 'novanet', kind: 'PUBLIC FIELD' },
  { id: 'Solariun', view: 'solspire', kind: 'PRIVATE WORKSPACE' },
  { id: 'SolSpire', view: 'solspire', kind: 'PROJECT / CONTEXT SUBSTRATE' },
  { id: 'Spiral Command', view: 'sci', kind: 'DISCOVERY / GOVERNANCE VISIBILITY' },
];

const SURFACE_NOTES: Record<Surface, string> = {
  NovaNet: 'Public social field. Private project context is not implied.',
  Solariun: 'Authenticated workspace composed from existing project, knowledge, memory, task, conversation and event substrates.',
  SolSpire: 'Project/context substrate. Project remains the parent object; children remain project-scoped.',
  'Spiral Command': 'Operator discovery shell. Navigation and metadata do not authorize mutation or execution.',
};

function SurfacePill({ active, surface, onClick }: { active: boolean; surface: typeof SURFACES[number]; onClick: () => void }) {
  return (
    <button type="button" className={`experience-surface-pill${active ? ' active' : ''}`} onClick={onClick}>
      <span>{surface.id}</span>
      <small>{surface.kind}</small>
    </button>
  );
}

function SearchPanel({ onClose }: { onClose: () => void }) {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState<any[]>([]);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!query.trim()) {
      setResults([]);
      setError(null);
      return;
    }
    const timer = window.setTimeout(async () => {
      setBusy(true);
      setError(null);
      try {
        const response = await searchKnowledge(query.trim(), ['semantic', 'fulltext', 'project', 'timeline'], 12);
        const groups = ['semantic', 'fulltext', 'project', 'timeline'];
        const seen = new Set<string>();
        const flat = groups.flatMap(group => (response as any)[group] || []);
        setResults(flat.filter((item: any) => {
          const key = String(item.note_uuid || item.id || item.title || JSON.stringify(item));
          if (seen.has(key)) return false;
          seen.add(key);
          return true;
        }));
      } catch (err: any) {
        setError(err?.message || 'Search unavailable');
      } finally {
        setBusy(false);
      }
    }, 260);
    return () => window.clearTimeout(timer);
  }, [query]);

  return (
    <div className="experience-overlay" role="dialog" aria-modal="true" aria-label="Search Arkadia">
      <div className="experience-search-card">
        <div className="experience-overlay-head">
          <div>
            <span className="experience-kicker">EXISTING SUBSTRATE</span>
            <h2>Search Arkadia</h2>
          </div>
          <button type="button" onClick={onClose} aria-label="Close search">×</button>
        </div>
        <p className="experience-honesty">Knowledge OS search only. Project-specific corpus is searched from inside its existing SolSpire context. No universal object index is created here.</p>
        <input autoFocus value={query} onChange={event => setQuery(event.target.value)} placeholder="Search existing knowledge…" />
        {busy && <div className="experience-search-state">Searching existing Knowledge OS…</div>}
        {error && <div className="experience-search-error">{error}</div>}
        {!busy && query.trim() && !results.length && !error && <div className="experience-search-state">No matching results in the active search substrate.</div>}
        <div className="experience-results">
          {results.map((item: any, index: number) => (
            <article key={`${item.note_uuid || item.id || index}`}>
              <span className="experience-result-type">{item.note_type || item.type || 'KNOWLEDGE'}</span>
              <strong>{item.title || item.name || 'Untitled object'}</strong>
              <p>{String(item.content || item.summary || '').slice(0, 180)}</p>
            </article>
          ))}
        </div>
      </div>
    </div>
  );
}

export default function ExperienceConsolidationFrame({ surface, onNavigate, children }: { surface: Surface; onNavigate: Navigate; children: ReactNode }) {
  const [inspectorOpen, setInspectorOpen] = useState(false);
  const [searchOpen, setSearchOpen] = useState(false);
  const current = SURFACES.find(item => item.id === surface)!;

  return (
    <div className="experience-frame" data-testid={`experience-frame-${surface.toLowerCase().replace(/\s+/g, '-')}`}>
      <header className="experience-rail">
        <div className="experience-identity">
          <span className="experience-mark">◈</span>
          <div>
            <strong>ARKADIA PRISM</strong>
            <small>EXPERIENCE FIELD</small>
          </div>
        </div>
        <nav className="experience-surface-nav" aria-label="Arkadia experience surfaces">
          {SURFACES.map(item => (
            <SurfacePill key={item.id} surface={item} active={item.id === surface} onClick={() => onNavigate(item.view)} />
          ))}
        </nav>
        <div className="experience-actions">
          <button type="button" onClick={() => setSearchOpen(true)}>⌕ <span>Search</span></button>
          <button type="button" onClick={() => onNavigate('commune')}>⌁ <span>Arkana</span></button>
          <button type="button" onClick={() => onNavigate('solspire')} title="Open Solariun">◈ <span>Workspace</span></button>
          <button type="button" onClick={() => onNavigate('sci')} title="Open Spiral Command">⌘ <span>Command</span></button>
          <button type="button" className={inspectorOpen ? 'active' : ''} onClick={() => setInspectorOpen(value => !value)} aria-expanded={inspectorOpen}>▣ <span>Inspect</span></button>
        </div>
      </header>

      <div className="experience-context" data-testid="experience-context-bar">
        <div>
          <span className="experience-mono">ARKADIA / {surface.toUpperCase()}</span>
          <span className="experience-separator">/</span>
          <strong>{current.kind}</strong>
        </div>
        <div className="experience-context-badges" aria-label="Experience governance status">
          <span>DISCOVERY ≠ AUTHORIZATION</span>
          <span>ACTIVITY ≠ PROVENANCE</span>
          <span>MERGE / DEPLOY: HUMAN</span>
        </div>
      </div>

      {inspectorOpen && (
        <aside className="experience-inspector" data-testid="experience-inspector" aria-label="Experience inspector">
          <span className="experience-kicker">CONTEXT INSPECTOR</span>
          <h2>{surface}</h2>
          <p>{SURFACE_NOTES[surface]}</p>
          <dl>
            <div><dt>SUBSTRATE</dt><dd>Existing repository components + existing APIs</dd></div>
            <div><dt>AUTHORITY</dt><dd>Human / existing backend governance</dd></div>
            <div><dt>ACTIVITY</dt><dd>Inspectable activity only; not causal provenance</dd></div>
            <div><dt>WEAVER</dt><dd>Visible through existing SolSpire project scope</dd></div>
            <div><dt>ARKANA</dt><dd>Existing intelligence surface; context claims remain bounded</dd></div>
          </dl>
        </aside>
      )}

      <main className="experience-content">{children}</main>

      {searchOpen && <SearchPanel onClose={() => setSearchOpen(false)} />}
    </div>
  );
}
