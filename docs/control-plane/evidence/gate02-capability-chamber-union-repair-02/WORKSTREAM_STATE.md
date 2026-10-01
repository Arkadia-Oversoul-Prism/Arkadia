# WORKSTREAM STATE - gate02 / capability-chamber union repair 02

**Status:** IMPLEMENTED - awaiting human merge
**BASE_MAIN:** `47e4128b1d1416a9417d9bb33db18a3d269f0200`
**Branch:** `gate02/capability-chamber-union-repair-02`
**Authority:** human merge only. No merge / no push to `main` / no force-push performed.

## Measured facts

```
old main 0fe6d0d  full suite : 20 failed / 1121 passed / 15 skipped / 1 error
new main 47e4128  full suite : 20 failed / 1121 passed / 15 skipped / 1 error
union    this br  full suite : 17 failed / 1124 passed / 15 skipped / 1 error

failing-node set: 0fe6d0d vs 47e4128 : IDENTICAL  (comm both directions empty)
failing-node set: 47e4128 vs union   : 3 FIXED / 0 NEW

sha256(new-main nodes) : 5d8a25ea26638eceba3d5ac7ccfb7d4a194e643bd6b03c21f4815b7a93b1bd14
sha256(union nodes)    : 2867517d338844492e4895eb9be1aa89b95c9e7f2836b2769c1eb9275c762d96

architecture : 11 passed
py_compile api/main.py : OK
api/main.py : 2531 / 2600 lines
```

The 3 fixed nodes:
- `tests/test_spiral_grove_activity_runtime.py::test_runtime_is_mounted_by_the_capability_chamber`
- `tests/test_spiral_grove_activity_runtime.py::test_chamber_preserves_sg03_downstream_boundary`
- `tests/test_spiral_grove_activity_runtime.py::test_spiral_grove_uses_the_nexus_canonical_header`

## Disposition of PR #166

MERGED as `47e4128`, but the squash landed the branch's oldest head (`0ebb9c4` /
chamber `5c78fcbcd`), not the measured final state (`6786763` / chamber `20f58649`).
Net effect on the test suite: zero - failing-node set unchanged. The Pass 02 evidence
merged with it asserts numbers that were never true of `main`; a correction banner has been
added to both files on this branch.

## Next bounded task (not started)

`test_runtime_dispatches_all_eight_kinds_to_deterministic_renderers` is a pre-existing
`main` test-side defect: the test asserts the literal `activity-surface-<kind>` while
`ActivityRuntime.tsx` renders a template expression. Unchanged by this branch; requires its
own bounded workstream. Do not fold it into this repair.

## Frontend build

Not run. `npm ping` succeeds but package tarball fetch fails in this environment.
Unproven, not claimed.
