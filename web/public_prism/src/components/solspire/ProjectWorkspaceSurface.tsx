/**
 * M04: single project interior surface.
 * Historical parallel workspace demoted to ProjectDashboard (canonical).
 */
import React from 'react';
import ProjectDashboard from '../../pages/ProjectDashboard';
import type { Project, ProjTab } from '../../pages/ProjectDashboard';

export default function ProjectWorkspaceSurface({
  project,
  onBack,
  initialTab = 'overview',
  onProjectUpdated,
}: {
  project: Project;
  onBack: () => void;
  initialTab?: ProjTab;
  onProjectUpdated?: (p: Project) => void;
}) {
  return (
    <div data-testid="solariun-project-context">
      <ProjectDashboard
        project={project}
        onBack={onBack}
        initialTab={initialTab}
        onProjectUpdated={onProjectUpdated}
      />
    </div>
  );
}
