import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { getProjects, getNotes, getProviders, getPersonas, getStatus } from '../../lib/knowledgeApi';

export default function ProjectsView() {
  const [selectedProject, setSelectedProject] = useState<number | null>(null);

  const { data: status } = useQuery({ queryKey: ['knowledge-status'], queryFn: getStatus, refetchInterval: 15000 });
  const { data: projects = [], isLoading: projLoading } = useQuery({ queryKey: ['projects'], queryFn: getProjects });
  const { data: providers = [] } = useQuery({ queryKey: ['providers'], queryFn: getProviders });
  const { data: personas = [] } = useQuery({ queryKey: ['personas'], queryFn: getPersonas });
  const { data: recentNotes = [] } = useQuery({
    queryKey: ['notes', selectedProject],
    queryFn: () => getNotes({ project_id: selectedProject || undefined, limit: 20 }),
  });

  const STATS = [
    { label: 'Notes',       value: status?.vault.notes ?? '—',       color: '#C9A84C' },
    { label: 'Embeddings',  value: status?.vault.embeddings ?? '—',  color: '#00D4AA' },
    { label: 'Graph Edges', value: status?.graph.edges ?? '—',        color: '#B08DE8' },
    { label: 'Events',      value: status?.timeline.events ?? '—',    color: '#6A9FD8' },
  ];

  return (
    <div style={{ height: '100%', overflowY: 'auto', display: 'flex', flexDirection: 'column', gap: 20 }}>
      {/* Vault stats */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 10 }}>
        {STATS.map(s => (
          <div key={s.label} style={{ background: 'rgba(255,255,255,0.04)', borderRadius: 8, border: '1px solid rgba(255,255,255,0.08)', padding: '14px 16px' }}>
            <div style={{ color: s.color, fontSize: 22, fontFamily: 'Cinzel, serif', fontWeight: 700 }}>{s.value}</div>
            <div style={{ color: '#666', fontSize: 10, fontFamily: 'Inter', textTransform: 'uppercase', letterSpacing: '0.1em', marginTop: 2 }}>{s.label}</div>
          </div>
        ))}
      </div>

      {/* Providers */}
      <div>
        <SectionTitle>Provider Status</SectionTitle>
        <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap', marginTop: 8 }}>
          {providers.map(p => (
            <div key={p.name} style={{
              padding: '6px 12px', borderRadius: 6, fontFamily: 'Inter', fontSize: 11,
              background: p.authenticated ? 'rgba(0,212,170,0.12)' : 'rgba(255,255,255,0.04)',
              border: `1px solid ${p.authenticated ? 'rgba(0,212,170,0.3)' : 'rgba(255,255,255,0.08)'}`,
              display: 'flex', alignItems: 'center', gap: 6,
            }}>
              <div style={{ width: 6, height: 6, borderRadius: '50%', background: p.authenticated ? '#00D4AA' : '#555' }} />
              <span style={{ color: p.authenticated ? '#00D4AA' : '#666' }}>{p.display_name}</span>
              <span style={{ color: '#444', fontSize: 9 }}>{p.capabilities.slice(0, 2).join(' · ')}</span>
            </div>
          ))}
          {providers.length === 0 && (
            <div style={{ color: '#555', fontFamily: 'Inter', fontSize: 12 }}>No providers configured — add GEMINI_API_KEY to start.</div>
          )}
        </div>
      </div>

      {/* Personas */}
      <div>
        <SectionTitle>Active Personas</SectionTitle>
        <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap', marginTop: 8 }}>
          {personas.map(p => (
            <div key={p.name} style={{
              padding: '4px 10px', borderRadius: 20, fontFamily: 'Inter', fontSize: 11,
              background: 'rgba(201,168,76,0.1)', border: '1px solid rgba(201,168,76,0.2)', color: '#C9A84C',
            }}>
              {p.name}
            </div>
          ))}
        </div>
      </div>

      {/* Projects */}
      <div style={{ flex: 1 }}>
        <SectionTitle>Projects</SectionTitle>
        {projLoading && <div style={{ color: '#666', fontFamily: 'Inter', fontSize: 12, marginTop: 8 }}>Loading…</div>}
        {projects.length === 0 && !projLoading && (
          <div style={{ color: '#555', fontFamily: 'Inter', fontSize: 12, marginTop: 8 }}>
            No projects yet. Create one via POST /api/knowledge/projects.
          </div>
        )}
        <div style={{ display: 'flex', gap: 10, flexWrap: 'wrap', marginTop: 8 }}>
          {projects.map(p => (
            <div key={p.id}
              onClick={() => setSelectedProject(selectedProject === p.id ? null : p.id)}
              style={{
                padding: '10px 14px', borderRadius: 8, cursor: 'pointer',
                background: selectedProject === p.id ? 'rgba(0,212,170,0.1)' : 'rgba(255,255,255,0.04)',
                border: `1px solid ${selectedProject === p.id ? 'rgba(0,212,170,0.3)' : 'rgba(255,255,255,0.08)'}`,
                minWidth: 140,
              }}>
              <div style={{ color: '#e0e0e0', fontFamily: 'Cinzel, serif', fontSize: 13, fontWeight: 600 }}>{p.name}</div>
              {p.description && (
                <div style={{ color: '#666', fontFamily: 'Inter', fontSize: 11, marginTop: 4 }}>
                  {p.description.slice(0, 60)}{p.description.length > 60 ? '…' : ''}
                </div>
              )}
              <div style={{ color: '#444', fontFamily: 'Inter', fontSize: 10, marginTop: 4 }}>
                {p.updated_at?.slice(0, 10)}
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Project notes */}
      {selectedProject !== null && (
        <div>
          <SectionTitle>Recent Notes</SectionTitle>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 6, marginTop: 8 }}>
            {recentNotes.map(n => (
              <div key={n.id} style={{ padding: '8px 12px', borderRadius: 6, background: 'rgba(255,255,255,0.03)', border: '1px solid rgba(255,255,255,0.07)', display: 'flex', gap: 10, alignItems: 'baseline' }}>
                <span style={{ color: '#666', fontSize: 10, fontFamily: 'Inter', width: 80, flexShrink: 0, textTransform: 'uppercase' }}>{n.note_type}</span>
                <span style={{ color: '#d0d0d0', fontFamily: 'Inter', fontSize: 12, flex: 1 }}>{n.title}</span>
                <span style={{ color: n.embedding_status === 'complete' ? '#00D4AA' : '#666', fontSize: 10, fontFamily: 'Inter' }}>{n.embedding_status}</span>
                <span style={{ color: '#444', fontSize: 10, fontFamily: 'Inter', flexShrink: 0 }}>{n.created_at?.slice(0, 10)}</span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

function SectionTitle({ children }: { children: React.ReactNode }) {
  return (
    <div style={{ color: '#888', fontSize: 10, fontFamily: 'Inter', textTransform: 'uppercase', letterSpacing: '0.12em', borderBottom: '1px solid rgba(255,255,255,0.07)', paddingBottom: 6 }}>
      {children}
    </div>
  );
}
