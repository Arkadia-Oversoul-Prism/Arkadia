# WORKSTREAM_STATE — gate-hygiene independent queue verification 07

## Current state
- **main**: `2b87e8efdbcbd777def07bb71c720e5b234ae6ac` (#276 merged)
- **recorded baseline**: `89f9e78` — 9F/1426P/17S/1E (10 nodes)
- **main measured**: 10F/1425P/17S/1E (11 nodes) — `+1/-0` vs baseline, attributable to #276
- **branch**: `gate-hygiene/independent-queue-verification-07`
- **mode**: read-only verification; the only artifact is this evidence record

## Queue disposition
| PR | Head | State |
|---|---|---|
| #267 | `51b0a3f4` | docs-only, no code surface |
| #268 | `ab427481` | docs-only, no code surface |
| #270 | `1a264efe` | **CONTRADICTED** — silently drops SolSpire Console router at boot |
| #271 | `6598c26d` | docs-only, no code surface |
| #273 | `93ea19549aab` | **CONTRADICTED** — frontend build fails |
| #274 | `0239ff11` | no regression; safe for review |

## Load-bearing evidence
- #270: `require_project_owner` imported from `api.auth` (undefined there); defined in
  `solspire/console_router.py:68`. Composed app mounts **15 routers on main, 14 on #270**.
  `api/main.py:332-337` bare `except Exception` converts the failure into a log warning.
- #273: `pnpm build` → unresolved `../components/solspire/ArkanaWeaverCanvas`.
- CI coverage: 42 test files named across `.github/workflows/*.yml` vs 179 on disk; no
  workflow runs the full suite; every defect node is UNCOVERED.

## Fingerprints
- outcomes: `9a54f5b478d1135f27ab9e54d95706f03eae1ceb5d4c1f3ae075bffc4208ab38`
- ids: `124bfdfd078fe878fe7c9de358ba271e977c4f7b73909b9d7d016b9ae9c1e87f`

## Next authorized action
Sovereign review of this record. Follow-on repairs (D-07-1…D-07-5) are **proposed only**,
each a separate bounded workstream, none begun.

## Forbidden without new authorization
Merge; direct push to `main`; boot-path (`api/main.py`) edits; test/policy edits inside this
evidence workstream; scope expansion.
