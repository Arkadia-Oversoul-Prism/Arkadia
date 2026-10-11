import React, { ReactNode } from 'react';
import './experience-consolidation.css';
import './experience-repair.css';

type Surface = 'NovaNet' | 'Solariun' | 'SolSpire' | 'Spiral Command';

type Props = {
  surface: Surface;
  onNavigate: (view: string) => void;
  children: ReactNode;
};

/**
 * Experience boundary only.
 *
 * The canonical SolSpireExperience owns navigation, search, Arkana, project
 * context and workspace composition. This wrapper deliberately does not add
 * another navigation/header/inspector/search system.
 */
export default function ExperienceConsolidationFrame({ surface, children }: Props) {
  return (
    <div
      className="experience-repair-scope"
      data-testid={`experience-frame-${surface.toLowerCase().replace(/\s+/g, '-')}`}
      data-experience-surface={surface}
    >
      {children}
    </div>
  );
}
