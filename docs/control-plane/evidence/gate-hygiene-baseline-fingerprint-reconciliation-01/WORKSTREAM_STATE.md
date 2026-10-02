# WORKSTREAM STATE — gate-hygiene / baseline fingerprint reconciliation 01

**State:** IMPLEMENTED — sovereign review required
**Base main:** `2b167e4f41ca87699db33a28c76f03550db66847`
**Branch:** `gate-hygiene/baseline-fingerprint-reconciliation-01`
**Supersedes (value only):** `gate-hygiene/baseline-fingerprint-reproducibility-01` (#203)

## Canonical baseline fingerprint (reproducible)

| Derivation | Value |
|---|---|
| outcomes `"<OUTCOME> <nodeid>"` lines | `4d84e7eb2524d4a5a952405f6df8017398ce21cca44aec6d04fbb523d577c6a7` |
| node set `"<nodeid>"` | `da2ec2620d09988e75702b6444ee8ee6ba5ded8bc067aac6c4e149245c27de71` |

Recorded node set: `tests/fixtures/baseline_node_set.txt` (21 nodes: 20 failed, 1 error).

Reproduce with:

```
python scripts/baseline_fingerprint.py tests/fixtures/baseline_node_set.txt
```

## Superseded (not reproducible — do not republish)

| Value | Source | Status |
|---|---|---|
| `a59453b8a1e5a02899f469cf6ea7db9b5eaae658050261e1405c394cb0f3cf6f` | #203 docs, `.bootstrap/01_STATE.md`, `MISSION.md`, `NEXT_AGENT.md`, ledger | SUPERSEDED — unreproducible |
| `9a35c8122188e272ec5769d7a8f5cdba6160b4f2f1fba8a840019a487c1bcc22` | #203 `WORKSTREAM_STATE.md`, `.bootstrap/01_STATE.md` | SUPERSEDED — unreproducible |

## Guard

`tests/test_baseline_fingerprint.py`:
- `test_live_node_set_reproduces_the_canonical_fingerprint`
- `test_superseded_fingerprints_are_not_reproducible` (negative control)
- `test_published_docs_carry_the_canonical_fingerprint[.bootstrap/01_STATE.md | MISSION.md | NEXT_AGENT.md | docs/phase1/CONTINUATION_LEDGER.md]`

## Next bounded task

None selected in this pass. The unreproducible-value class is now guarded; the origin of the
superseded value remains UNKNOWN and is recorded, not reconstructed.
