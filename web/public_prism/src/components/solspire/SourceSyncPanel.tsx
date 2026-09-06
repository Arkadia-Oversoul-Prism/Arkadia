import React, { useEffect, useState } from 'react';
import { API_BASE } from '../../lib/apiConfig';
import { useAuth } from '../../contexts/AuthContext';

type Source = {
  name: string;
  configured: boolean;
  authenticated?: boolean;
  live?: boolean;
  repo?: string;
  branch?: string;
};

const META: Record<string, { label: string; icon: string; color: string; description: string; setup: string[] }> = {
  github: {
    label: 'GitHub', icon: '⟐', color: '#00D4AA',
    description: 'Repository-backed corpus source already connected to Arkadia.',
    setup: ['Repository and branch are controlled by the existing backend configuration.'],
  },
  gdrive: {
    label: 'Google Drive', icon: '◈', color: '#6A9FD8',
    description: 'Bring documents from a Drive folder into the existing corpus and Knowledge OS.',
    setup: ['Create or choose a Drive folder.', 'For private Drive, use a Google service account and share the folder with it.', 'Configure the folder ID and credential on the Oracle/Render backend.'],
  },
  joplin: {
    label: 'Joplin', icon: '◉', color: '#4CB3D4',
    description: 'Sync notes from Joplin Desktop or a Joplin Server through its existing Data API source.',
    setup: ['Enable Joplin Web Clipper service.', 'Copy the Joplin API token.', 'Configure the token and, for Joplin Server, the server URL on the Oracle/Render backend.'],
  },
  obsidian: {
    label: 'Obsidian', icon: '◆', color: '#B08DE8',
    description: 'Existing corpus adapter for an Obsidian vault.',
    setup: ['Configure the vault path on the Oracle/Render backend.'],
  },
};

export default function SourceSyncPanel() {
  const { user } = useAuth();
  const [sources, setSources] = useState<Source[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [message, setMessage] = useState('');
  const [error, setError] = useState('');
  const [expanded, setExpanded] = useState<string | null>(null);

  async function load() {
    try {
      const res = await fetch(`${API_BASE}/api/sources`);
      if (!res.ok) throw new Error(`Source status unavailable (${res.status})`);
      const data = await res.json();
      setSources(Array.isArray(data.sources) ? data.sources : []);
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Could not read source status.');
    } finally { setLoading(false); }
  }

  useEffect(() => { load(); }, []);

  async function refresh() {
    setRefreshing(true); setError(''); setMessage('');
    try {
      const headers: HeadersInit = user?.idToken ? { Authorization: `Bearer ${user.idToken}` } : {};
      const res = await fetch(`${API_BASE}/api/corpus/refresh`, { method: 'POST', headers });
      const data = await res.json().catch(() => ({}));
      if (!res.ok) throw new Error(data.detail || `Refresh failed (${res.status})`);
      setMessage(`Corpus refreshed · ${data.live ?? 0} live documents`);
      await load();
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Corpus refresh failed.');
    } finally { setRefreshing(false); }
  }

  const configured = sources.filter(s => s.configured).length;

  return (
    <section className="solspire-sync-panel">
      <div className="solspire-sync-intro">
        <div>
          <div className="solspire-kicker">External sources · corpus bridge</div>
          <h3>Bring the rest of your knowledge into SolSpire.</h3>
          <p>
            These are not new storage systems. They are existing corpus adapters that feed the same
            Knowledge OS and searchable field. Configure a source once, then refresh the corpus to ingest it.
          </p>
        </div>
        <div className="solspire-sync-summary">
          <strong>{configured}/{sources.length || 4}</strong>
          <span>sources configured</span>
        </div>
      </div>

      {loading ? <div className="solspire-sync-state">Reading source configuration…</div> : (
        <div className="solspire-source-list">
          {sources.map(source => {
            const m = META[source.name] || { label: source.name, icon: '○', color: '#C9A84C', description: 'Corpus source.', setup: [] };
            const open = expanded === source.name;
            return (
              <article className={`solspire-source-card ${source.configured ? 'configured' : ''}`} key={source.name}>
                <button className="solspire-source-head" type="button" onClick={() => setExpanded(open ? null : source.name)}>
                  <span className="solspire-source-icon" style={{ color: m.color }}>{m.icon}</span>
                  <span className="solspire-source-copy">
                    <strong>{m.label}</strong>
                    <small>{m.description}</small>
                  </span>
                  <span className={`solspire-source-status ${source.configured ? 'on' : ''}`}>
                    <i /> {source.configured ? 'CONNECTED' : 'NOT CONNECTED'}
                  </span>
                  <span className="solspire-source-chevron">{open ? '−' : '+'}</span>
                </button>
                {open && <div className="solspire-source-detail">
                  {source.name === 'github' && <div className="solspire-source-fact">{source.repo || 'Repository'} · {source.branch || 'main'}{source.authenticated ? ' · authenticated' : ''}</div>}
                  <div className="solspire-kicker">Setup path</div>
                  <ol>{m.setup.map((step, i) => <li key={i}>{step}</li>)}</ol>
                  {!source.configured && source.name !== 'github' && (
                    <div className="solspire-source-note">
                      <strong>Important:</strong> SolSpire will not collect credentials into browser storage. These adapters currently read their configuration from the Oracle backend environment, so secrets stay server-side.
                    </div>
                  )}
                  {source.configured && <div className="solspire-source-ready">✓ Source configuration detected. It will participate in the existing corpus refresh.</div>}
                </div>}
              </article>
            );
          })}
        </div>
      )}

      <div className="solspire-sync-actions">
        <button type="button" onClick={refresh} disabled={refreshing || loading}>{refreshing ? 'Refreshing corpus…' : '↻ Refresh corpus now'}</button>
        <span>{message || error || 'Refresh is idempotent and uses the existing corpus + Knowledge OS pipeline.'}</span>
      </div>
    </section>
  );
}
