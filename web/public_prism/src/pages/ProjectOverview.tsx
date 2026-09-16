import React, { useEffect, useState } from 'react';
import type { Project, ProjTab } from './ProjectDashboard';
import { apiRequest } from '../lib/apiClient';

interface OverviewProps {
  project: Project;
  onTabChange: (tab: ProjTab) => void;
}

interface CollectionResponse {
  conversations?: unknown[];
  files?: unknown[];
  tasks?: unknown[];
  events?: unknown[];
}

async function loadCount(path: string, key: keyof CollectionResponse): Promise<number> {
  try {
    const data = await apiRequest<CollectionResponse>(path);
    const items = data?.[key];
    return Array.isArray(items) ? items.length : 0;
  } catch {
    return 0;
  }
}

export default function ProjectOverview({ project, onTabChange }: OverviewProps) {
  const [counts, setCounts] = useState({ conversations: 0, files: 0, tasks: 0, events: 0 });

  useEffect(() => {
    let cancelled = false;
    Promise.all([
      loadCount(`/solspire/projects/${project.id}/conversations`, 'conversations'),
      loadCount(`/solspire/projects/${project.id}/files`, 'files'),
      loadCount(`/solspire/projects/${project.id}/tasks`, 'tasks'),
      loadCount(`/solspire/projects/${project.id}/events`, 'events'),
    ]).then(([conversations, files, tasks, events]) => {
      if (!cancelled) setCounts({ conversations, files, tasks, events });
    });
    return () => { cancelled = true; };
  }, [project.id]);

  const cards: Array<{ label: string; value: number; tab: ProjTab; sigil: string }> = [
    { label: 'Conversations', value: counts.conversations, tab: 'conversations', sigil: '◌' },
    { label: 'Files', value: counts.files, tab: 'files', sigil: '□' },
    { label: 'Tasks', value: counts.tasks, tab: 'tasks', sigil: '☐' },
    { label: 'Events', value: counts.events, tab: 'events', sigil: '◇' },
  ];

  const metadataEntries = Object.entries(project.metadata || {}).filter(([, value]) => value !== null && value !== undefined);

  return (
    <section data-testid="solariun-project-overview" style={{ display: 'flex', flexDirection: 'column', gap: 16, color: '#D4DFE8', fontFamily: 'sans-serif' }}>
      <div style={{ padding: '18px 18px 16px', border: '1px solid rgba(0,212,170,0.14)', borderRadius: 12, background: 'rgba(14,17,32,0.72)' }}>
        <div style={{ fontSize: 9, letterSpacing: '0.25em', textTransform: 'uppercase', color: 'rgba(0,212,170,0.55)', marginBottom: 7 }}>Project Overview</div>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 12, flexWrap: 'wrap' }}>
          <h3 style={{ margin: 0, fontFamily: 'Georgia, serif', fontSize: 22, fontWeight: 500, color: '#E9E7DF' }}>{project.name}</h3>
          <span style={{ padding: '4px 9px', borderRadius: 999, border: '1px solid rgba(201,168,76,0.25)', background: 'rgba(201,168,76,0.06)', color: '#C9A84C', fontSize: 9, letterSpacing: '0.14em', textTransform: 'uppercase' }}>{project.status}</span>
        </div>
        <p style={{ margin: '10px 0 0', color: 'rgba(212,223,232,0.48)', fontSize: 11, lineHeight: 1.6 }}>
          Existing project context, live object counts, and direct routes into the project substrate.
        </p>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(145px, 1fr))', gap: 10 }}>
        {cards.map(card => (
          <button key={card.tab} type="button" onClick={() => onTabChange(card.tab)} style={{ textAlign: 'left', padding: 14, borderRadius: 10, border: '1px solid rgba(0,212,170,0.1)', background: 'rgba(14,17,32,0.62)', color: '#D4DFE8', cursor: 'pointer' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <span style={{ fontSize: 16, color: 'rgba(0,212,170,0.65)' }}>{card.sigil}</span>
              <span style={{ fontSize: 22, color: '#E9E7DF' }}>{card.value}</span>
            </div>
            <div style={{ marginTop: 8, fontSize: 9, letterSpacing: '0.16em', textTransform: 'uppercase', color: 'rgba(212,223,232,0.42)' }}>{card.label}</div>
          </button>
        ))}
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: 12 }}>
        <div style={{ padding: 14, borderRadius: 10, border: '1px solid rgba(0,212,170,0.08)', background: 'rgba(14,17,32,0.55)' }}>
          <div style={{ fontSize: 9, letterSpacing: '0.2em', textTransform: 'uppercase', color: 'rgba(0,212,170,0.5)', marginBottom: 8 }}>Identity</div>
          <div style={{ fontSize: 11, color: 'rgba(212,223,232,0.68)' }}>Project ID</div>
          <div style={{ marginTop: 3, fontFamily: 'monospace', fontSize: 10, color: 'rgba(212,223,232,0.4)', overflowWrap: 'anywhere' }}>{project.id}</div>
        </div>
        <div style={{ padding: 14, borderRadius: 10, border: '1px solid rgba(0,212,170,0.08)', background: 'rgba(14,17,32,0.55)' }}>
          <div style={{ fontSize: 9, letterSpacing: '0.2em', textTransform: 'uppercase', color: 'rgba(0,212,170,0.5)', marginBottom: 8 }}>Lifecycle</div>
          <div style={{ fontSize: 11, color: 'rgba(212,223,232,0.68)' }}>Created {new Date(project.created_at * 1000).toLocaleString()}</div>
          <div style={{ marginTop: 4, fontSize: 11, color: 'rgba(212,223,232,0.45)' }}>Updated {new Date(project.updated_at * 1000).toLocaleString()}</div>
        </div>
      </div>

      {metadataEntries.length > 0 && (
        <div style={{ padding: 14, borderRadius: 10, border: '1px solid rgba(201,168,76,0.1)', background: 'rgba(201,168,76,0.025)' }}>
          <div style={{ fontSize: 9, letterSpacing: '0.2em', textTransform: 'uppercase', color: 'rgba(201,168,76,0.55)', marginBottom: 9 }}>Existing Metadata</div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
            {metadataEntries.slice(0, 12).map(([key, value]) => (
              <div key={key} style={{ display: 'flex', justifyContent: 'space-between', gap: 12, fontSize: 10 }}>
                <span style={{ color: 'rgba(212,223,232,0.45)' }}>{key}</span>
                <span style={{ color: 'rgba(212,223,232,0.7)', textAlign: 'right', overflowWrap: 'anywhere' }}>{typeof value === 'string' ? value : JSON.stringify(value)}</span>
              </div>
            ))}
          </div>
        </div>
      )}
    </section>
  );
}
