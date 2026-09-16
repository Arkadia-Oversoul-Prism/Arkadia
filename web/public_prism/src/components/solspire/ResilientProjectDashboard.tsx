import React, { Component, lazy, Suspense } from 'react';
import type { Project, ProjTab } from '../../pages/ProjectDashboard';

const ProjectDashboard = lazy(() => import('../../pages/ProjectDashboard'));

interface Props {
  project: Project;
  initialTab: ProjTab;
  onBack: () => void;
  onProjectUpdated: (project: Project) => void;
}

interface State {
  failed: boolean;
}

class ProjectDashboardBoundary extends Component<Props, State> {
  state: State = { failed: false };

  static getDerivedStateFromError(): State {
    return { failed: true };
  }

  componentDidCatch(error: Error) {
    if (typeof window !== 'undefined') {
      console.error('[Solariun] project dashboard isolated failure', error);
    }
  }

  render() {
    if (this.state.failed) {
      return (
        <section
          data-testid="solariun-project-fallback"
          aria-live="polite"
          style={{
            minHeight: 320,
            display: 'grid',
            placeItems: 'center',
            padding: 32,
            border: '1px solid rgba(201,168,76,0.16)',
            borderRadius: 14,
            background: 'rgba(8,10,18,0.52)',
          }}
        >
          <div style={{ maxWidth: 520, textAlign: 'center' }}>
            <div style={{ fontSize: 11, letterSpacing: '0.22em', textTransform: 'uppercase', color: 'rgba(201,168,76,0.72)', marginBottom: 10 }}>
              Project surface isolated
            </div>
            <h2 style={{ margin: '0 0 8px', color: 'rgba(232,232,232,0.88)', fontSize: 18, fontWeight: 500 }}>
              {this.props.project.name}
            </h2>
            <p style={{ margin: '0 auto 18px', maxWidth: 430, color: 'rgba(232,232,232,0.42)', fontSize: 12, lineHeight: 1.7 }}>
              A secondary project surface failed to render. The project context remains available, and the failure has been isolated from the Solariun field.
            </p>
            <button
              type="button"
              onClick={() => this.setState({ failed: false })}
              style={{
                padding: '9px 14px',
                borderRadius: 8,
                border: '1px solid rgba(0,212,170,0.28)',
                background: 'rgba(0,212,170,0.06)',
                color: '#00D4AA',
                cursor: 'pointer',
                fontSize: 10,
                letterSpacing: '0.14em',
                textTransform: 'uppercase',
              }}
            >
              Retry project surface
            </button>
          </div>
        </section>
      );
    }

    return (
      <Suspense
        fallback={
          <section data-testid="solariun-project-loading" style={{ minHeight: 320, display: 'grid', placeItems: 'center', color: 'rgba(232,232,232,0.38)', fontSize: 11, letterSpacing: '0.16em', textTransform: 'uppercase' }}>
            Opening project surface…
          </section>
        }
      >
        <ProjectDashboard
          project={this.props.project}
          initialTab={this.props.initialTab}
          onBack={this.props.onBack}
          onProjectUpdated={this.props.onProjectUpdated}
        />
      </Suspense>
    );
  }
}

export default ProjectDashboardBoundary;
