import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import KnowledgeGraphView from './KnowledgeGraphView';
import TimelineView from './TimelineView';
import SemanticSearchView from './SemanticSearchView';
import ProjectsView from './ProjectsView';

type Tab = 'graph' | 'timeline' | 'search' | 'projects';

const TABS: { id: Tab; label: string; sigil: string; color: string }[] = [
  { id: 'graph',    label: 'Knowledge Graph', sigil: '◈', color: '#00D4AA' },
  { id: 'timeline', label: 'Timeline',         sigil: '◎', color: '#C9A84C' },
  { id: 'search',   label: 'Search',           sigil: '⟐', color: '#B08DE8' },
  { id: 'projects', label: 'Observatory',      sigil: '✧', color: '#6A9FD8' },
];

export default function KnowledgeOSPage() {
  const [tab, setTab] = useState<Tab>('graph');

  return (
    <div style={{
      minHeight: '100vh',
      background: 'radial-gradient(ellipse at 20% 20%, rgba(0,212,170,0.04) 0%, transparent 50%), #0C0D18',
      display: 'flex',
      flexDirection: 'column',
      padding: '24px 28px 28px',
    }}>
      {/* Header */}
      <div style={{ marginBottom: 24 }}>
        <div style={{ display: 'flex', alignItems: 'baseline', gap: 12 }}>
          <span style={{ color: '#00D4AA', fontFamily: 'Cinzel, serif', fontSize: 11, letterSpacing: '0.2em', textTransform: 'uppercase' }}>
            Arkadia
          </span>
          <span style={{ color: '#333', fontSize: 11 }}>·</span>
          <span style={{ color: '#666', fontFamily: 'Cinzel, serif', fontSize: 11, letterSpacing: '0.15em' }}>
            Knowledge OS
          </span>
        </div>
        <h1 style={{ color: '#e0e0e0', fontFamily: 'Cinzel, serif', fontSize: 22, fontWeight: 700, margin: '4px 0 0', letterSpacing: '0.05em' }}>
          Prism
        </h1>
        <p style={{ color: '#555', fontFamily: 'Inter', fontSize: 12, margin: '4px 0 0' }}>
          Knowledge Graph · Timeline · Semantic Search · Projects
        </p>
      </div>

      {/* Tab bar */}
      <div style={{ display: 'flex', gap: 4, marginBottom: 20, borderBottom: '1px solid rgba(255,255,255,0.07)', paddingBottom: 0 }}>
        {TABS.map(t => (
          <button
            key={t.id}
            onClick={() => setTab(t.id)}
            style={{
              padding: '8px 16px',
              background: 'none',
              border: 'none',
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              gap: 7,
              fontFamily: 'Inter',
              fontSize: 12,
              color: tab === t.id ? t.color : '#555',
              borderBottom: `2px solid ${tab === t.id ? t.color : 'transparent'}`,
              transition: 'all 0.15s',
              marginBottom: -1,
            }}>
            <span style={{ fontSize: 14 }}>{t.sigil}</span>
            {t.label}
          </button>
        ))}
      </div>

      {/* Tab content */}
      <div style={{ flex: 1, minHeight: 0, height: 'calc(100vh - 180px)' }}>
        <AnimatePresence mode="wait">
          <motion.div
            key={tab}
            initial={{ opacity: 0, y: 6 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -6 }}
            transition={{ duration: 0.18 }}
            style={{ height: '100%' }}
          >
            {tab === 'graph'    && <KnowledgeGraphView />}
            {tab === 'timeline' && <TimelineView />}
            {tab === 'search'   && <SemanticSearchView />}
            {tab === 'projects' && <ProjectsView />}
          </motion.div>
        </AnimatePresence>
      </div>
    </div>
  );
}
