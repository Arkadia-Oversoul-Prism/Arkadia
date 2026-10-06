# WORKSTREAM STATE — gate07 chain integration

Pass: `gate07/chain-integration-evidence-01`
Reconstructed: 2026-10-06 · BASE_MAIN `451e41a30fcbff4a65326e897a84818cc623b769`

## Current state

| item | evidence |
|---|---|
| canonical clone | `main`, ancestry intact, `origin/main` = `451e41a` (#317) |
| active gate | GATE-07 — durable Weaver loop (hourly bounded execution) |
| this pass | composed-chain integration measurement for PRs #319/#320/#321/#322/#323 |
| PR | this pass, base `main`, artifact-only |
| frontier | G12-A / G12-C `merged_acceptance_pending` (sovereign authority) |

## Open PR inventory (live, at reconstruction)

| PR | branch | head | base | role |
|---|---|---|---|---|
| #319 | `gate-hygiene/scheduler-trajectory-conformance-01` | `3d1829d` | `main` | trajectory conformance (crash fix) + CI-live guard |
| #320 | `gate-hygiene/scheduler-runtime-outbox-ignored` | `d5adcba` | `main` | ignore worker attention outbox |
| #321 | `gate-hygiene/scheduler-trajectory-schema-01` | `e611edd` | **#319** (stacked) | status enum + schema guard |
| #322 | `gate07/router-status-truthfulness` | `9d0f1ce` | `main` | report unrecognized move status |
| #323 | `gate07/attention-truthfulness` | `cd749ea` | `main` | push unresolved stop to sovereign |

Unrelated / older: #318 (`fix/prism-arkana-surface-consolidation`), #306
(`feat/oversoul-prism-9cell-conformance`).

## Merge order (proposed; agent does not merge)

`#319` → `#320` → `#321` → `#322` → `#323`. #321 must follow #319 (stacked base).
#320/#321 are hygiene; #319/#322/#323 are the runtime loop chain.

## Composition probe (measured)

| tree | status | attention |
|---|---|---|
| `main` | `FAILED` / `invalid trajectory structure` | `WEAVER_BLOCKED` HIGH |
| #319 only | `NO_LEGAL_MOVE` / generic blocker | `WEAVER_STATE_CHANGED` INFO (silent) |
| composed | `NO_LEGAL_MOVE` / typed G12-A,G12-C blocker | `WEAVER_BLOCKED` HIGH |

## Test / baseline fingerprint

- composed guard suite: conformance + schema + router-truthfulness + attention-truthfulness
  → pass; `test_repo_hygiene_gitignore.py` env-blocked (`fastapi` absent) on `main` too.
- `tests/architecture` — not run this pass (no runtime change); unaffected.
- No runtime code changed in this pass; no `api/main.py` touch.

## Environment note

`fastapi` / `pydantic` are not installed in this sandbox, so the API-surface tests cannot
run locally. CI (with the installed environment) is the authority for those nodes.
Recorded, not worked around.

## Next bounded task

Chain is READY FOR SOVEREIGN MERGE in the order above (each PR independently green on its
triggered checks; provider-routing failures are pre-existing CE-01 debt). The only permitted
next action is human review + merge — no agent merges. On merge, the next heartbeat
reconstructs `main` and the hourly loop should emit a HIGH `WEAVER_BLOCKED` naming the
G12-A/G12-C frontier, which is the correct human-authority stop.
