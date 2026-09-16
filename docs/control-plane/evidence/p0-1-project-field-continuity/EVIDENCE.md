# P0.1 — Project Field Continuity — Evidence

**Authorization:** Architect — Proposal P0.1 exact scope  
**Base:** `dcda7efa7f5209c9afc9739ebdf029792c9acc95`  
**Parent proposal:** `docs/architecture/SOLSPIRE_GAP_PROPOSALS_v1.md` §P0.1

## Scope implemented
- When a project is open, selecting mapped lenses (overview, files, tasks, conversations, memory, knowledge, weaver, observatory) **keeps** the project and sets the corresponding `ProjectDashboard` tab.
- Non-mapped lenses (e.g. projects, commercial, engineering-lab, settings) still **clear** project context.
- Explicit “← Projects” still exits to list; onBack also returns section to `projects`.
- No new storage, APIs, or authorization changes.

## Forbidden (not done)
- New project model / DB
- Universal object store
- PassSpec/K15 changes
- M10 / AEAS activation
- Deploy

## Tests
`tests/test_p0_1_project_field_continuity.py`
