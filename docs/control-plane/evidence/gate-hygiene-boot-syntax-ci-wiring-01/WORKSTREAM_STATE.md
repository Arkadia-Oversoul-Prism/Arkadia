# WORKSTREAM STATE — gate-hygiene

Pass: `gate-hygiene/boot-syntax-ci-wiring-01`
Reconstructed: 2026-10-10 · BASE_MAIN `f9ced6b6b974a6e19a8a19b4d1360b59b037a2c8`

## Current state (derived from live evidence)

| item | value |
|---|---|
| canonical clone | `main`, non-shallow, ancestry intact |
| BASE_MAIN | `f9ced6b6…` |
| open PRs | 40 (incl. sizeable evidence/composition cluster) |
| active claim | no workflow runs `tests/test_boot_syntax_boundary.py` (P1-A boot guard) |
| this pass | wire that guard into CI + a wiring-invariant test |

## Dependencies / boundaries

- The boot guard's domain is the whole tracked Python corpus (556 files at base).
- `api/main.py` is under its 2600-line budget (2450) and is not touched.
- No authority, identity, or mutation path is touched. CI-only wiring.

## Test / baseline fingerprint

- `tests/architecture` — 11 passed.
- full suite — 16 nodes (15F/1E); `bfcfe592…` / `ed5e4714…` (canonical, reproduced with
  declared deps `pdfminer.six` + `pytest-asyncio` installed).
- `python -m py_compile api/main.py` — OK.

## Next bounded task

Sovereign review of this PR. Follow-on, non-consequential candidates are recorded in the
repository's open evidence cluster; none is begun here.
