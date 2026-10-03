# WORKSTREAM STATE — test-hygiene/authority-boundary-async-01

**As of:** 2026-10-03 hourly pass
**BASE_MAIN:** `162f574b05dd839540d803aadda7608342618a84`
**Branch / PR:** `test-hygiene/authority-boundary-async-01` → **PR #222**
**Status:** `READY FOR SOVEREIGN MERGE` (no merge performed)

## Current state
- Bounded task pinned by PR #219 Pass 6 §8, narrowed to the **mechanism** defect only.
- `tests/test_authority_api_enterprise_boundary.py` async node adapted to the #180
  authority model; `pytest-asyncio` declared in `requirements.txt`.
- Delta by node identity: **1 fixed / 0 new / 20 unchanged**.
- Protected: `api/main.py` untouched (2582 lines), architecture 11/11, CP10 judge PASS.
- CI on head `9962b42c`: validate ✓, secret scan ✓, Vercel preview ✓.

## Evidence
`docs/control-plane/evidence/test-hygiene-authority-boundary-async-01/EVIDENCE.md`

## Next bounded task (for the next heartbeat)
1. **`test_solariun_thread_navigation_01.py::test_shell_wires_home_to_lens_selection`** —
   `STALE_ASSERTION`. Repair is a **product call**: decide whether
   `SolariunInteractionCanvas.onNavigate` should be bounded to `SolSpireLens`. Requires a
   sovereign ruling before it can be executed; do not self-authorize.
2. Remaining 19 baseline failures — unclassified beyond the two #219 §8 named. A
   classification pass is a separate bounded workstream.

## Blockers / holds
- PR #220 (`SH-05` retirement) — draft/HOLD; sovereign disposition required.
- Gate 2 production parity — `BLOCKED` on provider auth (unchanged).

## Forbidden this workstream
- No merge, no push to `main`, no force-push.
- Do not fold the solariun design decision or #220 into this branch.
