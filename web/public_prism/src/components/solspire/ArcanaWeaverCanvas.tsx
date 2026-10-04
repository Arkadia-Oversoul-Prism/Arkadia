import React from 'react';
import ArkanaCommune from '../ArkanaCommune';
import SolariunInteractionCanvas from './SolariunInteractionCanvas';
import ProjectAgenticCanvas from './ProjectAgenticCanvas';
import type { Project } from '../../pages/ProjectDashboard';

type Props = { project: Project };

/**
 * Arcana Weaver
 *
 * One project-scoped interaction surface:
 * - Solariun Home Canvas field projection
 * - Arkana's canonical LLM conversation/runtime
 * - Weaver governed workbench + Engineering Lab agent substrate
 *
 * These are projections of existing systems, not a new execution authority.
 */
export default function ArcanaWeaverCanvas({ project }: Props) {
  return (
    <div
      data-testid="arcana-weaver-canvas"
      style={{
        display: 'grid',
        gridTemplateColumns: 'minmax(230px,.78fr) minmax(360px,1.35fr) minmax(300px,.95fr)',
        gap: 12,
        minHeight: 'calc(100dvh - 118px)',
        color: '#D4DFE8',
        fontFamily: 'sans-serif',
      }}
    >
      <section style={{ minWidth: 0, overflow: 'auto', border: '1px solid rgba(0,212,170,.12)', borderRadius: 12, background: 'rgba(8,10,18,.78)' }} aria-label="Solariun field">
        <div style={{ padding: '12px 14px', borderBottom: '1px solid rgba(0,212,170,.08)' }}>
          <div style={{ fontSize: 9, letterSpacing: '.18em', color: '#00D4AA' }}>FIELD</div>
          <div style={{ marginTop: 4, fontSize: 12, color: 'rgba(233,231,223,.72)' }}>Solariun Home Canvas</div>
          <div style={{ marginTop: 3, fontSize: 10, color: 'rgba(212,223,232,.38)' }}>Live personal-field projection inside the project workspace.</div>
        </div>
        <div style={{ padding: 10 }}>
          <SolariunInteractionCanvas
            onNavigate={(target) => {
              if (target === 'commune') window.dispatchEvent(new CustomEvent('arkadia:open-arkana'));
            }}
          />
        </div>
      </section>

      <section style={{ minWidth: 0, display: 'flex', flexDirection: 'column', border: '1px solid rgba(176,141,232,.16)', borderRadius: 12, background: 'radial-gradient(circle at 50% 0%,rgba(176,141,232,.10),transparent 42%),rgba(8,10,18,.88)', overflow: 'hidden' }} aria-label="Arkana conversation">
        <div style={{ padding: '12px 14px', borderBottom: '1px solid rgba(176,141,232,.12)', flexShrink: 0 }}>
          <div style={{ fontSize: 9, letterSpacing: '.18em', color: '#B08DE8' }}>ARCANA WEAVER</div>
          <div style={{ marginTop: 4, fontSize: 15, color: '#E9E7DF' }}>{project.name}</div>
          <div style={{ marginTop: 3, fontSize: 10, color: 'rgba(212,223,232,.42)' }}>Arkana runtime · project-bound thread · inspect → propose → govern → execute</div>
        </div>
        <div style={{ flex: 1, minHeight: 560, overflow: 'hidden' }}>
          <ArkanaCommune
            projectContextId={project.id}
            projectName={project.name}
            initialMessage={'You are operating inside the Arcana Weaver for ' + project.name + '. Treat the project as the active context. You may inspect, reason, retrieve and propose through the existing Arkadia runtime, but never imply that a proposal is authorization or that execution occurred unless the governed backend records it.'}
          />
        </div>
      </section>

      <section style={{ minWidth: 0, overflow: 'auto', border: '1px solid rgba(201,168,76,.14)', borderRadius: 12, background: 'rgba(8,10,18,.78)' }} aria-label="Weaver capabilities">
        <div style={{ padding: '12px 14px', borderBottom: '1px solid rgba(201,168,76,.08)' }}>
          <div style={{ fontSize: 9, letterSpacing: '.18em', color: '#C9A84C' }}>WEAVER</div>
          <div style={{ marginTop: 4, fontSize: 12, color: 'rgba(233,231,223,.72)' }}>Governed workbench</div>
          <div style={{ marginTop: 3, fontSize: 10, color: 'rgba(212,223,232,.38)' }}>Existing project execution controls remain backend-authoritative.</div>
        </div>
        <div style={{ padding: 10 }}>
          <ProjectAgenticCanvas project={project} />
        </div>
      </section>
    </div>
  );
}
