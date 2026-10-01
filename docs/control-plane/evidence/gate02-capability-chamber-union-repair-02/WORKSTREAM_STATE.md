# WORKSTREAM STATE - gate02 / capability-chamber union repair 02

**Status:** IMPLEMENTED - awaiting human merge
**BASE_MAIN:** `47e4128b1d1416a9417d9bb33db18a3d269f0200`
**REBASED_ONTO:** `3e1cd007c93fcfe5a73fb3dc81fd65644b06306f`
**Branch:** `gate02/capability-chamber-union-repair-02`
**Authority:** human merge only. No merge / no push to `main` / no force-push performed.

## Measured facts

```
# measured at first pass (base 47e4128)
old main 0fe6d0d  full suite : 20 failed / 1121 passed / 15 skipped / 1 error
new main 47e4128  full suite : 20 failed / 1121 passed / 15 skipped / 1 error
union    @47e4128 full suite : 17 failed / 1124 passed / 15 skipped / 1 error
failing-node set: 0fe6d0d vs 47e4128 : IDENTICAL  (comm both directions empty)
failing-node set: 47e4128 vs union   : 3 FIXED / 0 NEW

# RE-MEASURED after rebase onto the current tip (main moved 47e4128..3e1cd00)
main 3e1cd00     full suite : 22 failed / 1125 passed / 15 skipped / 1 error
union rebased    full suite : 19 failed / 1128 passed / 15 skipped / 1 error
failing-node set: 3e1cd00 vs union   : 3 FIXED / 0 NEW

sha256(nodes 3e1cd00) : 32a2b51bffa8210079f31d3d25e72741fbd605f1c15677a518b9923334d695aa
sha256(nodes union)   : 0a64965140978cc2e588fd0a446a18a661168cc6f3538a1dabb356e3c3162f29

# main moved 47e4128..3e1cd00 with NO overlap on the two repaired files,
# but it introduced 2 NEW failures of its own (see EVIDENCE.md 10b):
#   tests/test_relational_lineage.py::test_graph_node_exposes_canonical_capture_provenance
#   tests/test_relational_lineage.py::test_traversal_preserves_provenance_projection
#   TypeError: register_source() takes 0 positional arguments but 3 were given
#   knowledge/capture.py:78 is keyword-only; test_relational_lineage.py:38,82 call positionally.
#   Owned by the #173 workstream. NOT repaired here (scope).

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
