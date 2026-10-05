# WORKSTREAM STATE — gate-hygiene

Pass: `gate-hygiene/scheduler-trajectory-conformance-01`
Reconstructed: 2026-10-05 · BASE_MAIN `451e41a30fcbff4a65326e897a84818cc623b769`

## Current state

| item | evidence |
|---|---|
| canonical clone | `main`, ancestry intact, `origin/main` = `451e41a` (#317) |
| active workstream | gate-hygiene — hourly bounded-execution loop integrity |
| this pass | scheduler↔trajectory structural conformance fix + guard |
| PR | #319 (base `main`, head `b0a431f8…`), OPEN, MERGEABLE |
| frontier | G12-A `merged_acceptance_pending` → worker returns `NO_LEGAL_MOVE` (truthful) |

## Defect and fix (measured)

| | pre-fix | post-fix |
|---|---|---|
| trajectory structure | `moves` nested under `trajectory:` | `moves` top-level |
| router result | `ValueError: invalid trajectory structure` | routing decision |
| worker status / exit | `FAILED` / 1 | `NO_LEGAL_MOVE` / 0 |
| guard tests | 4 failed / 6 passed | **10 passed** |

## Test / baseline fingerprint at this pass

- `tests/test_scheduler_trajectory_conformance.py` — **10 passed** (negative control 4F pre-fix)
- `tests/architecture` — **11 passed** (main's own baseline)
- `python -m py_compile api/main.py` — OK; `api/main.py` untouched
- CP10 boundary judge on changed paths — **PASS** (exit 0)
- full suite — main `451e41a`: 1005P/69F/48E/20S, 117 nodes, fp `f33d69df…`/`6dde9f16…`
- branch: node-set delta `only in main: []`, `only in branch: []` → zero regression

## Environment note

`fastapi` / `pydantic` are **not installed** in this sandbox, so a local full-suite
run cannot exercise the API surface. Recorded, not worked around. CI (with the
installed environment) is the authority for those nodes.

## CI state on #319 (measured)

| check | result | attribution |
|---|---|---|
| Vercel – arkadia-prism | fail | provider **build rate limit** ("retry in 24 hours") — environmental; also fails on `main` |
| Vercel – console | fail | same provider rate limit |
| Full-history secret scan | pending | range scan |
| CP10 / sg-02-fe-2-v | not triggered | path filter did not match this diff |

## Next bounded task

Sovereign review of #319 (human-only merge). On merge, the next heartbeat
reconstructs `main` and the console frontier stays at G12-A acceptance — that
remains sovereign authority, not an engineering move.

## Proposed, not executed

- **Status-vocabulary divergence** — schema enumerates
  `{pending, revision_required, completed, accepted, blocked, failed, aborted}`;
  the console trajectory uses `merged_acceptance_pending` / `in_progress`, and
  `weaver/engineering_router.py::ACTIVE_STATUSES` accepts `in_progress`. Pre-existing;
  not the cause of the hourly failure; separate bounded workstream.
- **`attention-events.jsonl`** is generated at the repo root by
  `weaver/attention_bus.py` on every worker run and is **untracked/ungitignored**.
  Left uncommitted here; whether it should be gitignored is a separate proposal.
