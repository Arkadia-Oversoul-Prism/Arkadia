# M04 — Projects — Evidence

**Authorization:** Architect  
**Base:** `17dc63d` (main; includes merged M03)  
**Branch:** `weaver/arkadia-truthfulness/m04-projects`

## Objective
One coherent project context aligned with SolSpire workspace architecture; no parallel project model.

## Implementation
- `ProjectsWorkspace`: explicit one-model banner + test ids; still uses `/solspire/projects`
- `SolSpireExperience`: project context marker; interior remains `ProjectDashboard`
- `ProjectWorkspaceSurface`: demoted to thin delegate of `ProjectDashboard` (no parallel interior)

## Tests
`tests/test_m04_projects.py` — focused coherence checks

## Out of scope
M05 files expansion, M03 changes, K15/K3, new database, new project store
