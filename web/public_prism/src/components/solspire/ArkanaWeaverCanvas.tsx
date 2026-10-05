import React from 'react';
import ArkanaCommune from '../ArkanaCommune';
import SolariunInteractionCanvas from './SolariunInteractionCanvas';
import ProjectAgenticCanvas from './ProjectAgenticCanvas';
import type { Project } from '../../pages/ProjectDashboard';
import './arcana-weaver.css';

type Props = { project: Project };

/**
 * Arkana Weaver: one project-scoped interaction surface combining
 * Solariun field projection, Arkana's canonical LLM runtime, and
 * the existing governed Weaver agent workbench.
 *
 * This composes existing systems. It does not create execution authority.
 */
export default function ArkanaWeaverCanvas({ project }: Props) {
  return (
    <div data-testid="arcana-weaver-canvas" className="arcana-weaver-canvas">
      <section className="arcana-weaver-pane arcana-weaver-pane--field" aria-label="Solariun field">
        <div className="arcana-weaver-head">
          <div className="arcana-weaver-kicker" style={{ color: '#00D4AA' }}>FIELD</div>
          <div className="arcana-weaver-title">Solariun Home Canvas</div>
          <div className="arcana-weaver-subtitle">Live personal-field projection inside the active project.</div>
        </div>
        <div className="arcana-weaver-body">
          <SolariunInteractionCanvas onNavigate={(target) => {
            if (target === 'commune') window.dispatchEvent(new CustomEvent('arkadia:open-arkana'));
          }} />
        </div>
      </section>

      <section className="arcana-weaver-pane arcana-weaver-pane--arkana" aria-label="Arkana conversation">
        <div className="arcana-weaver-head">
          <div className="arcana-weaver-kicker" style={{ color: '#B08DE8' }}>ARCANA WEAVER</div>
          <div className="arcana-weaver-title">{project.name}</div>
          <div className="arcana-weaver-subtitle">Arkana runtime · project-bound thread · inspect → propose → govern → execute</div>
        </div>
        <div className="arcana-weaver-arkana-body">
          <ArkanaCommune
            projectContextId={project.id}
            projectName={project.name}
            initialMessage={'You are operating inside the Arkana Weaver for ' + project.name + '. Treat the project as the active context. You may inspect, reason, retrieve and propose through the existing Arkadia runtime, but never imply that a proposal is authorization or that execution occurred unless the governed backend records it.'}
          />
        </div>
      </section>

      <section className="arcana-weaver-pane arcana-weaver-pane--weaver" aria-label="Weaver capabilities">
        <div className="arcana-weaver-head">
          <div className="arcana-weaver-kicker" style={{ color: '#C9A84C' }}>WEAVER</div>
          <div className="arcana-weaver-title">Governed workbench</div>
          <div className="arcana-weaver-subtitle">Existing project execution controls remain backend-authoritative.</div>
        </div>
        <div className="arcana-weaver-body">
          <ProjectAgenticCanvas project={project} />
        </div>
      </section>
    </div>
  );
}
