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
  const runtime = (project.metadata?.project_runtime && typeof project.metadata.project_runtime === 'object')
    ? project.metadata.project_runtime as Record<string, any>
    : null;
  const runtimeBindings = runtime?.runtime || {};
  const runtimeStatus = (value: any) => typeof value === 'string' ? value.replace(/_/g, ' ') : 'UNKNOWN';

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

      {runtime && (
        <section data-testid="solariun-project-runtime" style={{ padding: 14, borderRadius: 12, border: '1px solid rgba(201,168,76,0.16)', background: 'rgba(14,17,32,0.66)', display: 'grid', gap: 12 }}>
          <div>
            <div style={{ fontSize: 9, letterSpacing: '0.2em', textTransform: 'uppercase', color: 'rgba(201,168,76,0.65)' }}>Project runtime contract</div>
            <div style={{ marginTop: 5, fontFamily: 'Georgia,serif', fontSize: 17, color: '#E9E7DF' }}>{runtime.template_id || 'Enterprise project'}</div>
            <div style={{ marginTop: 4, fontSize: 10, lineHeight: 1.6, color: 'rgba(212,223,232,0.46)' }}>Configured on the canonical project record. Requested capabilities are targets, not proof that every integration is live.</div>
          </div>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(135px, 1fr))', gap: 8 }}>
            {[
              ['Weaver', runtimeBindings.operational_engine?.state],
              ['Arkana', runtimeBindings.conversation_interface?.state],
              ['Sandbox', runtimeBindings.sandbox?.state],
              ['Domain module', runtime.domain?.state],
            ].map(([label, state]) => (
              <div key={String(label)} style={{ padding: 10, borderRadius: 8, border: '1px solid rgba(255,255,255,0.06)', background: 'rgba(255,255,255,0.02)' }}>
                <div style={{ fontSize: 9, letterSpacing: '0.14em', textTransform: 'uppercase', color: 'rgba(212,223,232,0.38)' }}>{label}</div>
                <div style={{ marginTop: 5, fontSize: 10, color: state === 'not_configured' || String(state).includes('requires_live') ? '#C9A84C' : '#00D4AA' }}>{runtimeStatus(state)}</div>
              </div>
            ))}
          </div>
          <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
            <button type="button" onClick={() => onTabChange('weaver')} style={{ padding: '7px 10px', borderRadius: 8, border: '1px solid rgba(176,141,232,0.25)', background: 'rgba(176,141,232,0.06)', color: '#B08DE8', cursor: 'pointer', fontSize: 10 }}>Open Weaver workbench →</button>
            {Array.isArray(runtime.requested_capabilities) && <span style={{ alignSelf: 'center', fontSize: 9, color: 'rgba(212,223,232,0.35)' }}>Requested modules · {runtime.requested_capabilities.length}</span>}
          </div>
        </section>
      )}

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
