# WORKSTREAM STATE — gate-hygiene / baseline fingerprint reconciliation 01

**State:** IMPLEMENTED — sovereign review required
**Base main:** `2b167e4f41ca87699db33a28c76f03550db66847`
**Branch:** `gate-hygiene/baseline-fingerprint-reconciliation-01`
**Supersedes (value only):** `gate-hygiene/baseline-fingerprint-reproducibility-01` (#203)

## Canonical baseline fingerprint (reproducible)

| Derivation | Value |
|---|---|
| outcomes `"<OUTCOME> <nodeid>"` lines | `a578a766c09c949c620c9d324248659812d215d3d1e875a0c25b42adb8912aa1` |
| node set `"<nodeid>"` | `8036fc0692eb0358f037adb2cf9e2b234db1f41a4586ca0162f4e52350cfa713` |

Recorded node set: `tests/fixtures/baseline_node_set.txt` (20 nodes: 19 failed, 1 error).
Depth-stable: excludes the PR-head-pinned
`test_gate2_parent_agents_md_repair_is_byte_identical_to_the_pipeline`, which skips in a
clone that does not carry `7d79f38…` and so made the fingerprint a function of clone depth.

Reproduce with:

```
python scripts/baseline_fingerprint.py tests/fixtures/baseline_node_set.txt
```

## Superseded (not reproducible — do not republish)

| Value | Source | Status |
|---|---|---|
| `a59453b8a1e5a02899f469cf6ea7db9b5eaae658050261e1405c394cb0f3cf6f` | #203 docs, `.bootstrap/01_STATE.md`, `MISSION.md`, `NEXT_AGENT.md`, ledger | SUPERSEDED — unreproducible by any convention |
| `9a35c8122188e272ec5769d7a8f5cdba6160b4f2f1fba8a840019a487c1bcc22` | #203 `WORKSTREAM_STATE.md`, `.bootstrap/01_STATE.md` | SUPERSEDED — unreproducible by any convention |
| `4d84e7eb2524d4a5a952405f6df8017398ce21cca44aec6d04fbb523d577c6a7` | first reconciliation pass | SUPERSEDED — reproducible only when the clone carries `7d79f38…` (clone-depth dependent) |
| `da2ec2620d09988e75702b6444ee8ee6ba5ded8bc067aac6c4e149245c27de71` | first reconciliation pass | SUPERSEDED — reproducible only when the clone carries `7d79f38…` (clone-depth dependent) |

## Guard

`tests/test_baseline_fingerprint.py`:
- `test_live_node_set_reproduces_the_canonical_fingerprint`
- `test_recorded_set_excludes_the_clone_depth_dependent_node`
- `test_superseded_fingerprints_are_not_reproducible` (negative control)
- `test_published_docs_carry_the_canonical_fingerprint[.bootstrap/01_STATE.md | MISSION.md | NEXT_AGENT.md | docs/phase1/CONTINUATION_LEDGER.md]`

## Next bounded task

None selected in this pass. The unreproducible-value class and the clone-depth class are both
guarded; the origin of `a59453b8…` remains UNKNOWN and is recorded, not reconstructed. The
excluded node's own assertion defect (it pins a revision a plain clone does not carry) is a
separate proposed workstream, not executed here.
