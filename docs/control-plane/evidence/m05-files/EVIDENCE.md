# M05 — Files — Evidence

**Authorization:** Architect  
**Base:** `391b805`  
**Branch:** `weaver/arkadia-truthfulness/m05-files`

## Objective
Complete project file surface on existing corpus (no parallel storage).

## Implementation
- `copy_file` in `solspire/project_store.py` + `POST .../files/{id}/copy`
- ProjectDashboard Files: rename (PUT name), copy, share-ref; upload auth via apiFetch
- Cross-project Move explicitly deferred
- Files remain `project_files` / `/solspire/projects/{id}/files`

## Tests
`tests/test_m05_files.py` — 5 passed
