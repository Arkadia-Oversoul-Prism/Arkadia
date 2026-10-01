# GATE-01 · Relational lineage — canonical provenance shape

Workstream: `gate01/relational-lineage-canonical-provenance`
Base: `main` `3e1cd007c93fcfe5a73fb3dc81fd65644b06306f`
Observed: 2026-10-01T17:0x UTC

## Objective

Make `knowledge/graph.py` project the **canonical** GATE-01 provenance shape, and rebind the
two `tests/test_relational_lineage.py` assertions that were reading a divergent shape.

## Root cause — a self-contradictory pair landed with no gate

`main` carries two provenance producers that disagree:

| Producer | Shape |
|---|---|
| `knowledge/capture.py::_provenance_from_capture_row` (canonical) | `authorship.authored_by`, `source.source_ref`, `capture.*` |
| `knowledge/graph.py::_attach_provenance` (divergent, PR #170) | flat `authored_by`, `capture_uuid`, `raw_checksum`, … |

`tests/test_relational_lineage.py` was authored against the **divergent** shape, so it
passed while the graph and the canonical capture layer contradicted each other.

## Provenance correction — which PR is which

An earlier commit message on this branch cited **PR #173** as the source of the divergent
shape. That is **wrong** and is corrected here.

`git diff refs/pull/170/head 3e1cd00 -- knowledge/graph.py` → **empty**. Main's `graph.py`
is **byte-identical to PR #170's** (`arkadia-relational-lineage-02`). PR #173
(`arkadia-relational-lineage-01`) landed **later** (17:27:58 vs 17:27:02) and contributed
**only** `tests/test_relational_lineage.py` + `docs/architecture/RELATIONAL_LINEAGE_01.md`.

So the divergent implementation is **#170**'s, and the gate-less test is **#173**'s.

## Merge-order inversion — a batch-merge hazard

Five PRs were merged in a ~60-second window, and the ordering inverted the numeric sequence:

| Order | Time | PR | Branch |
|---|---|---|---|
| 1 | 17:26:46 | #169 | `arkadia-canonical-ingress-boundary-01` |
| 2 | 17:27:02 | #170 | `arkadia-relational-lineage-02` |
| 3 | 17:27:21 | #171 | `arkadia-context-provenance-01` |
| 4 | 17:27:40 | #172 | `arkadia-operational-capture-bridge-01` |
| 5 | 17:27:58 | #173 | `arkadia-relational-lineage-01` |

`...-02` landed **before** `...-01`. #170 and #173 are duplicate implementations of the same
workstream — both rewrote `knowledge/graph.py` (`+47/-1`) and `tests/test_relational_lineage.py`.
Both were squash-merged, so no merge commit recorded the conflict.

#173 also **deleted** a passing test (`test_conversation_ingress_adds_existing_replies_to_edge`)
present in #170. Deletions of green coverage should not ride along silently in a squash.

## Repair

`_attach_provenance` now reads through `capture.provenance_for_note`; `traverse()` wraps its
nodes with it. `tests/test_relational_lineage.py` asserts the nested canonical shape
(`provenance["authorship"]["authored_by"]`, `provenance["source"]["source_ref"]`).

## Measured — full suite, by test-node identity

`PYTHONPATH=archive/legacy_python pytest tests/ -q --continue-on-collection-errors -p no:randomly`

| Tree | failed | passed | skipped | errors |
|---|---|---|---|---|
| `main` `3e1cd00` | 22 | 1123 | 17 | 1 |
| this branch | 20 | 1125 | 17 | 1 |
| `main` + this branch + PR #174 | **17** | **1128** | 17 | 1 |

Fingerprint diff, both directions:

- **FIXED** (2): `test_graph_node_exposes_canonical_capture_provenance`,
  `test_traversal_preserves_provenance_projection`
- **NEW**: none

`comm -13` is empty on every pair — **zero new failures**, measured, not claimed.

The composed run fixes 3 further nodes, all attributable to PR #174 and none to this branch:

- `test_spiral_grove_activity_runtime.py::test_runtime_is_mounted_by_the_capability_chamber`
- `test_spiral_grove_activity_runtime.py::test_chamber_preserves_sg03_downstream_boundary`
- `test_spiral_grove_activity_runtime.py::test_spiral_grove_uses_the_nexus_canonical_header`

## Residual failures — pre-existing, deliberately not fixed

17 failures remain on the composed tree. None is attributable to this branch. One is a
test-side defect worth its own bounded workstream:

- `test_runtime_dispatches_all_eight_kinds_to_deterministic_renderers` asserts the literal
  `data-testid="activity-surface-<kind>"` while `ActivityRuntime.tsx` renders the template
  `` data-testid={`activity-surface-${kind}`} ``. The property holds; the assertion cannot
  match its own template.

The rest span `test_steward_filter.py` (3), `test_spiral_grove_registry.py` (2),
`test_solspire_r1_governance_convergence.py` (2), `test_agents_md_encoding_adjudication.py` (2),
and one each in `test_solspire_r2_github_mutation.py`, `test_solspire_r3_execution_runtime.py`,
`test_m02_reasomate_truth.py`, `test_identity_spine_w1.py`, `test_gate_status.py`,
`test_gate_serve_script.py`, `test_ais_w2_living_gate_grove_handoff.py`, plus the
`test_autonomy.py` collection error.

## Structural observation — no workflow runs this test

`grep -rn "knowledge/" .github/workflows/*.yml` → **no match**. No workflow references
`test_relational_lineage`. The workflows that invoke `pytest` are path-filtered to
`solspire/**`, `weaver/**`, `lab/**`, `kernel/jobs.py`, `web/public_prism/**`, and
`spiral_grove/**`; `security-secret-scan.yml` runs on every PR but only scans for secrets.

Consequence: a `knowledge/` change is gated by **nothing** except the secret scan. That is
the enabling condition for the self-contradictory pair above. Recorded as a **proposed**
workstream — not executed here (NO SELF-EXPANSION).

## Not claimed

- Frontend build / production parity — not attempted in this pass.
- Acceptance. Source repair + evidence only.

## Authority boundary

Not merged. No push to `main`, no force-push. Merge is reserved to the human sovereign.
