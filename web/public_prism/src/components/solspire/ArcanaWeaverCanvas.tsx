import React from 'react';
import ArkanaCommune from '../ArkanaCommune';
import SolariunInteractionCanvas from './SolariunInteractionCanvas';
import ProjectAgenticCanvas from './ProjectAgenticCanvas';
import type { Project } from '../../pages/ProjectDashboard';
import './arcana-weaver.css';

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
    <div data-testid="arcana-weaver-canvas" className="arcana-weaver-canvas">
      <section className="arcana-weaver-pane arcana-weaver-pane--field" aria-label="Solariun field">
        <div className="arcana-weaver-head">
          <div style={{ fontSize: 9, letterSpacing: '.18em', color: '#00D4AA' }}>FIELD</div>
          <div style={{ marginTop: 4, fontSize: 12, color: 'rgba(233,231,223,.72)' }}>Solariun Home Canvas</div>
          <div style={{ marginTop: 3, fontSize: 10, color: 'rgba(212,223,232,.38)' }}>Live personal-field projection inside the project workspace.</div>
        </div>
        <div className="arcana-weaver-body">
          <SolariunInteractionCanvas onNavigate={(target) => {
            if (target === 'commune') window.dispatchEvent(new CustomEvent('arkadia:open-arkana'));
          }} />
        </div>
      </section>

      <section className="arcana-weaver-pane arcana-weaver-pane--arkana" aria-label="Arkana conversation">
        <div className="arcana-weaver-head">
          <div style={{ fontSize: 9, letterSpacing: '.18em', color: '#B08DE8' }}>ARCANA WEAVER</div>
          <div style={{ marginTop: 4, fontSize: 15, color: '#E9E7DF' }}>{project.name}</div>
          <div style={{ marginTop: 3, fontSize: 10, color: 'rgba(212,223,232,.42)' }}>Arkana runtime · project-bound thread · inspect → propose → govern → execute</div>
        </div>
        <div className="arcana-weaver-arkana-body">
          <ArkanaCommune
            projectContextId={project.id}
            projectName={project.name}
            initialMessage={'You are operating inside the Arcana Weaver for ' + project.name + '. Treat the project as the active context. You may inspect, reason, retrieve and propose through the existing Arkadia runtime, but never imply that a proposal is authorization or that execution occurred unless the governed backend records it.'}
          />
        </div>
      </section>

      <section className="arcana-weaver-pane arcana-weaver-pane--weaver" aria-label="Weaver capabilities">
        <div className="arcana-weaver-head">
          <div style={{ fontSize: 9, letterSpacing: '.18em', color: '#C9A84C' }}>WEAVER</div>
          <div style={{ marginTop: 4, fontSize: 12, color: 'rgba(233,231,223,.72)' }}>Governed workbench</div>
          <div style={{ marginTop: 3, fontSize: 10, color: 'rgba(212,223,232,.38)' }}>Existing project execution controls remain backend-authoritative.</div>
        </div>
        <div className="arcana-weaver-body">
          <ProjectAgenticCanvas project={project} />
        </div>
      </section>
    </div>
  );
}
