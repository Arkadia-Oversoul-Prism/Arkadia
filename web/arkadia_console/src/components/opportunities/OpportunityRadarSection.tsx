/**
 * Project Opportunity Radar — the Projects-surface section.
 *
 * The backend contract is project-scoped (`GET /solspire/buyer-recon/projects/{id}`,
 * authenticated, owner-enforced). This component owns the *selection* of the
 * project; the read itself is delegated to the existing prop-driven
 * `ProjectOpportunityRadar`, which owns the loading/auth/unavailable/error/ready
 * states. Nothing here invents a route, a project, a buyer, or a price: an empty
 * board stays visibly empty, and an unselected project is a prompt, not an error.
 *
 * The reader is reconnaissance only. It exposes no execute, spend, or settlement
 * control, and it repeats the backend's own authority block rather than asserting
 * a success state of its own.
 */
import { useEffect, useState } from "react";
import { Panel } from "../ui";
import { ProjectOpportunityRadar } from "./ProjectOpportunityRadar";
import { projectBoardPath } from "./opportunityRadarContract";
import type { SolspireProject } from "../../lib/types";

export function OpportunityRadarSection({ projects }: { projects: SolspireProject[] }) {
  const [selected, setSelected] = useState<string | null>(null);

  // Default to the first project the caller actually returned — never a
  // fabricated id. A board that disappears from the list resets the selection.
  useEffect(() => {
    if (selected && !projects.some((p) => p.id === selected)) setSelected(null);
    else if (!selected && projects.length > 0) setSelected(projects[0].id);
  }, [projects, selected]);

  if (projects.length === 0) {
    return (
      <Panel className="border-dashed border-line">
        <p className="font-mono text-[11px] uppercase tracking-widest text-white/40">Project field · Opportunity Radar</p>
        <p className="mt-2 text-sm text-white/60">
          No projects exist in this workspace yet, so there is no project board to read. This is not an empty
          opportunity board.
        </p>
      </Panel>
    );
  }

  return (
    <div className="flex flex-col gap-3">
      <div className="flex flex-wrap items-center gap-2">
        <label
          htmlFor="opportunity-radar-project"
          className="font-mono text-[11px] uppercase tracking-widest text-white/40"
        >
          Project
        </label>
        <select
          id="opportunity-radar-project"
          data-testid="opportunity-radar-project-select"
          value={selected ?? ""}
          onChange={(event) => setSelected(event.target.value || null)}
          className="rounded border border-line bg-ink/60 px-2 py-1 font-mono text-[11px] text-white/80"
        >
          {projects.map((project) => (
            <option key={project.id} value={project.id}>
              {project.name}
            </option>
          ))}
        </select>
      </div>
      {selected ? (
        <ProjectOpportunityRadar readPath={projectBoardPath(selected)} />
      ) : (
        <Panel className="border-dashed border-line">
          <p className="text-sm text-white/60">Select a project to read its opportunity board.</p>
        </Panel>
      )}
    </div>
  );
}
