# M05 — Files — Acceptance-Readiness Verification

**Move:** M05 — files  
**HEAD inspected:** `566df75c90c688c967bd92692e16f83bba86de03`  
**Verdict:** `READY_FOR_REVIEW`

> Does **not** accept M05. No ACCEPT.json in this pass.

## Merge evidence
- PR #45 / implementation `5305585` / merge `cd3dbf9`

## Spec alignment
| Criterion | Result |
|-----------|--------|
| Project corpus only (no parallel FS) | PASS — `project_files` + `/solspire/projects/{id}/files` |
| Rename / copy / share-ref | PASS — dashboard + `copy_file` + copy route |
| Cross-project Move deferred | PASS — explicit |
| Focused tests | PASS — `tests/test_m05_files.py` |

## Boundaries
No ACCEPT · no deploy · no M06+ acceptance in this file alone.
