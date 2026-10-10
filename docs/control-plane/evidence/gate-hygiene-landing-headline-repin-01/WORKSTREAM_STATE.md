# WORKSTREAM STATE — gate-hygiene landing-headline re-pin 01

Pass: `gate-hygiene/landing-headline-repin-01`
Reconstructed: 2026-10-07T17:06–17:58 UTC · BASE_MAIN `74e8ea53a30213db8783e6733679d2f11903de0b`
Re-verified: continuation pass, 2026-10-07 later UTC · branch base = live `main`
`af3a3541d9fedf8c2d38bb7a0aac56856a879523` (the `74e8ea53` above is the automation's
17:05 fresh clone, taken before the 17:34–17:52 merges — a stale clone SHA, not the base).

## Current state

| item | evidence |
| --- | --- |
| canonical clone | `main`, ancestry intact, `origin/main` = `af3a3541d9fedf8c2d38bb7a0aac56856a879523` |
| active gate | GATE-07 — durable Weaver loop (hourly bounded execution) |
| this pass | test-debt fingerprint reconciliation (one drifted node) |
| PR | #347, base `main`, head `5f22022`, test + evidence only, `MERGEABLE/UNSTABLE` |
| frontier | GATE-07 batch **merged and closed**; #337/#338 open = `BLOCKED` (AEAS authority), see below |

## What merged before this pass (sovereign action)

`#334 → #346`, ending at `af3a354` (`75d18b2` then `af3a354`). #346's diff is
evidence-only (`docs/control-plane/evidence/gate-hygiene-post-merge-verification-06/`),
so it cannot alter frontend source. The `git` ancestry is linear and verified:
`75d18b2` is an ancestor of `af3a354`; `af3a354`'s parents are `75d18b2`, `67aec9d`.

## The drift

`tests/fixtures/baseline_node_set.txt` records **10** failing/error nodes. `main` @
`af3a354` measured **11**. The extra node —
`tests/test_ais_capability_profile_onboarding.py::test_home_is_offer_led_and_keeps_arkadia_entry_points`
— is a stale source-level literal: `2b87e8e` (#276 canonical Oversoul identity,
2026-10-04) replaced the headline the SH-02e test had been pinned to (`479e8de`,
2026-09-29) and no re-pin followed.

Correction to the previous pass's ledger: its node-set sha256 `92d344d0fbeb…` is the
**11-node** value (drifted), not a reconciled baseline. The canonical recorded value
is `124bfdfd…` (ids) / `9a54f5b4…` (outcomes), 10 nodes.

## Measurement

| tree | full suite | nodes | ids sha256 |
| --- | --- | --- | --- |
| `af3a354` pre-fix | 10F / 1760P / 21S / 1E | 11 | `92d344d0fbeb…` |
| repaired | 9F / 1761P / 21S / 1E | **10** | **`124bfdfd078f…`** |

Repaired set == `tests/fixtures/baseline_node_set.txt` exactly. Delta `-1` node, `+0`
introduced. Architecture 11/11; fingerprint guard 24/24; CP10 PASS; `api/main.py`
2434/2600 (untouched).

## Open PR inventory (live, re-measured this pass)

| PR | branch | mergeable | role |
| --- | --- | --- | --- |
| #337 | `aeas-01-native-operator-surface` | `MERGEABLE/UNSTABLE` | AEAS operator surface |
| #338 | `aeas-browser-runner-01` | `CONFLICTING/DIRTY` | AEAS browser runner |

Correction to the previous pass's ledger: it recorded **both** AEAS PRs as
`CONFLICTING`. Re-measured live, `#337` is `MERGEABLE/UNSTABLE` (the `UNSTABLE` is the
Vercel build-rate-limit status, §5 of `EVIDENCE.md`); only `#338` conflicts with `main`.

## AEAS PRs are an authority boundary, not an engineering task

Reconstruction resolved the question the previous pass left open — whether `#337`/`#338`
should be composed into a superset. They must not be, and the reason is governance, not
conflict mechanics:

- `docs/control-plane/AEAS-v0.1.1.md` is `Status: FROZEN`, **`Implementation: NOT
  AUTHORIZED`**, `Authority Ceiling: LEVEL 2 (specification only)`, `Human Authorization:
  REQUIRED FOR ALL EXECUTION`; its freeze declaration states "No implementation is
  authorized by this freeze." This is the state on current `main` (`af3a354`).
- The authorization-provenance chain is normative (spec §1):
  `ARCHITECT → AUTHORIZATION RECORD → ENGINEERING LAB → WORKER → EVIDENCE`, and "A task
  without such a record is not authorized and must not be dispatched."
- Both open PRs are *AEAS implementations*. `#337` adds an "AEAS-01 native operator
  surface" (`api/lab_routes.py`, `App.tsx`, `ArkadiaNavigation.tsx`,
  `EngineeringLabPage.tsx`); `#338` adds an "AEAS browser runner"
  (`tools/aeas-browser-runner/**`, `api/lab_routes.py`, and the same three frontend
  files). Neither body cites an architect-originated authorization record. The only AEAS
  acceptance artifact on `main` is
  `docs/control-plane/evidence/m07-aeas-freeze/ACCEPT.json`, which records
  `aeas_implementation_activated: false` and `implementation_not_authorized: true`.
- Composition is also **mechanically** blocked: measured on `main` `af3a354`, applying
  `#337` then `#338` yields 29 conflict regions (`lab_routes.py` 5,
  `EngineeringLabPage.tsx` 17, `App.tsx` 4, `ArkadiaNavigation.tsx` 3). The merge-base of
  the two heads is `17e626c` (Merge PR #333) and `#337` is not an ancestor of `#338` —
  divergent siblings, not a superset pair.

**Classification: `#337` / `#338` = `BLOCKED` (authority).** Advancing them requires an
architect-originated authorization record naming the bounded AEAS task, not a larger
engineering pass. No composition, rebase, or conflict resolution was performed.

## Next bounded task

Attribute the remaining 10 baseline debt nodes against the recorded fixture
(STALE_ASSERTION / REAL_DEFECT / ENVIRONMENT), one node per bounded pass. Not begun.
