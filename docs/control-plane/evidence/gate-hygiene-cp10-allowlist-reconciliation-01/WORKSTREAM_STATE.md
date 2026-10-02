# Workstream state — gate-hygiene/cp10-allowlist-reconciliation-01

Gate: GATE-10 (governed execution) / CP10 mutation boundary
Branch: `gate-hygiene/cp10-allowlist-reconciliation-01`
Base main: `ae847ddfd4bd01bd61e3c26545f90f3fe217f5a5`
Status: IMPLEMENTED — sovereign merge required

## Current state

CP10's `LEGIT` allowlist omitted the tracked `reconciliation/` surface, leaving
three CP10 fitness tests red on `main` (`3F/46P`) and one of 1579 tracked paths
rejected by the boundary module. The surface was merged by PR #180 (`ae847dd`).

## Evidence

- `docs/control-plane/evidence/gate-hygiene-cp10-allowlist-reconciliation-01/EVIDENCE.md`

## Baseline fingerprint (measured at pass start)

- `pytest tests/architecture -q` -> 11 passed (the contract's `9/10` is stale)
- `pytest tests/test_m02a_ci_gate_integrity.py -q` -> 3 failed / 46 passed
- `api/main.py` line budget unchanged (not touched)

## Blocker / separate workstream (NOT in this PR)

- `Provider Routing Verification` is red on PR #181 because
  `tests/test_autonomy.py` errors at collection: `weaver/autonomy.py` resolves
  `governance/autonomy.json` through `os.getcwd()` (cwd-dependent path
  resolution), so the suite only collects when run from the repo root. The
  documented fix (`REPO_ROOT`-anchored resolution) is a **separate bounded
  workstream** and is not started here.

## Bootstrap reconciliation (NOT in this PR)

`.bootstrap/01_STATE.md` and `NEXT_AGENT.md` still assert
"K4 — Response Provenance (READY TO BEGIN) / NEXT". Live `main` contradicts this.
Reconciling those docs is a separate bounded workstream; this PR does not widen
into it.

## Next bounded task (authorized envelope)

Either (a) sovereign merges this PR, or (b) authorize the cwd-independent
`weaver/autonomy.py` path-resolution repair as its own bounded branch/PR.

## Forbidden actions

Merge, push to `main`, force-push, self-authorization, scope expansion into
adjacent gates.
