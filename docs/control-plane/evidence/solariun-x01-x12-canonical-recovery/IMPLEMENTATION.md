# SOLARIUN-X01 → X12 — CANONICAL RECOVERY IMPLEMENTATION

## Changes

### Shell ownership
`ExperienceConsolidationFrame.tsx` is now a boundary wrapper only. It no longer renders a second header, surface navigation, search panel, context inspector, or Arkana/command navigation. `SolSpireExperience` remains the single canonical Solariun workspace shell.

### Spatial composition
`experience-repair.css` restores:

- quiet Solariun header
- one desktop navigation spine
- one mobile bottom navigation rail
- field-first Obsidian depth
- editorial object typography
- project-world focus composition
- contextual coordinate bars
- readable object/activity/relationship treatment
- reduced-motion behavior
- keyboard-visible focus states inherited and strengthened through the canonical shell

### Home field truthfulness
`SolariunHomeCockpit.tsx` was corrected so the field no longer hardcodes a specific project/workload narrative. It now renders only values returned by the existing pulse, workload, WorkEvent, synthesis and proposal APIs, with explicit empty/unavailable states.

## Existing substrate retained

- `SolSpireExperience`
- `ProjectDashboard`
- `ProjectsWorkspace`
- `solariunApi`
- `knowledgeApi`
- existing Arkana context pack
- existing Weaver project routes
- existing activity/WorkEvent routes

## No new substrate

No database, graph store, universal object persistence, Intent schema, Automation Ontology, provenance engine, or execution authority was introduced.
