# WORKSTREAM STATE — gate-hygiene landing-headline re-pin 01

Pass: `gate-hygiene/landing-headline-repin-01`
Reconstructed: 2026-10-07T17:06–17:58 UTC · BASE_MAIN `74e8ea53a30213db8783e6733679d2f11903de0b`

## Current state

| item | evidence |
| --- | --- |
| canonical clone | `main`, ancestry intact, `origin/main` = `af3a3541d9fedf8c2d38bb7a0aac56856a879523` |
| active gate | GATE-07 — durable Weaver loop (hourly bounded execution) |
| this pass | test-debt fingerprint reconciliation (one drifted node) |
| PR | this pass, base `main`, test + evidence only |
| frontier | GATE-07 batch **merged and closed**; only the two AEAS PRs remain open, both conflicting |

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

## Open PR inventory (live, at reconstruction)

| PR | branch | role |
| --- | --- | --- |
| #337 | `aeas-01-native-operator-surface` | AEAS operator surface — `CONFLICTING/DIRTY`, separate workstream |
| #338 | `aeas-browser-runner-01` | AEAS browser runner — `CONFLICTING/DIRTY`, separate workstream |

Both AEAS PRs are out of scope for this pass: they conflict with `main`, they are
large, and their own bodies scope them to an external provider boundary (Render
browser verification while Vercel quota is unavailable). Not touched.

## Next bounded task

Attribute the remaining 10 baseline debt nodes against the recorded fixture
(STALE_ASSERTION / REAL_DEFECT / ENVIRONMENT), one node per bounded pass. Not begun.
