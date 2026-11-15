# Lane 3 — bind the positional-read scanner to its detector

**Lane:** 3 (Solariun + Knowledge OS)
**Branch:** `feat/prism-l3-positional-read-detector-binding-01`
**Base:** `main` `19697a6a358ec114265e665fcc22eea8d5018ac2`
**Scope:** `tests/test_knowledge_graph_health_read_boundary.py` only (lane-3 owned test).
No production source, no backend contract, no other lane's file is touched.

## Objective

`test_no_other_module_reads_a_row_positionally` is the *class* guard for the
`knowledge.graph_health._count()` defect repaired in #621: it sweeps every
`knowledge/**/*.py` file for a positional read of a `knowledge.db` dict row.
Its predicate was written **inline inside the test body**, so it shared no symbol
with anything a control could call — there was no control at all. A detector
written inline is exactly the shape the lane scheme has been repairing: the
assertion can be disarmed by editing the very expression it depends on, and no
test fails.

## Measured defect at base `19697a6a`

The guard is vacuous in the disarm direction, and that measurement is the one
that matters:

1. **It is disarmable.** With a positional read planted in
   `knowledge/graph_health.py` (`return int(list(row)[0])`) **and** the inline
   predicate rewritten to `if False:`, the node
   `test_no_other_module_reads_a_row_positionally` still **passed**
   (`1 passed`). The planted defect is exactly the defect #621 repaired, and the
   guard that exists to catch its recurrence did not see it.
2. **It has no control.** `grep -c test_negative_control` for this predicate
   returned 0: nothing fed the detector the shape it must reject, so the only way
   to notice a disarm was to read the source.

## Repair

The predicate moves to a module-level detector `_positional_row_reads(source)`
with its vocabulary hoisted to `POSITIONAL_ROW_READ_SHAPES`, and the live sweep
and a new control both call it. The control asserts **both** polarities — the
pre-repair shape is reported, and the shipped module is *not* — so a detector
that reports unconditionally cannot pass either.

Node count `11 → 12` (`--collect-only` per file: 11 → 12, `+1` = the new control).

## Evidence — live negative controls on the real file

The detector body was mutated **in the real file** (not a synthetic fixture),
each mutation measured, and the file restored byte-identically afterwards
(`md5 6940eb90e622fdc8a79653a880b8bede` before and after).

| Mutation of `_positional_row_reads` | Result | Reading |
|---|---|---|
| `return []` (always-clean) | `1 failed, 11 passed` — the **control** reddens | the control bites when the detector stops reporting |
| `return ["always-dirty"]` (always-dirty) | `2 failed, 10 passed` — the sweep **and** the control redden | the control bites on the opposite polarity too |

The "always-dirty" row is the discriminating one: it is the only mutation that
reddens the *control* through its shipped-module polarity, so the control is not
satisfied by a detector that reports everything.

Restored file: `tests/test_knowledge_graph_health_read_boundary.py` and
`tests/test_knowledge_graph_health_ci_wiring.py` — **24 passed** together
(12 + 12).

## Wiring

The file is executed by the derived `knowledge-connection-lifecycle-guard.yml`
step and is a declared input of `tests/test_knowledge_graph_health_ci_wiring.py`,
which asserts (over the real workflow) that the guard is executed, dispatchable,
selects every input it reads, and cannot be exempted. No new wiring is needed and
none was added.

## Boundaries preserved

- No protected authority, identity, K15/K3 governance, approval-enforcement,
  constitutional architecture, or deployment configuration is altered.
- `knowledge/graph_health.py` is unchanged; the repair is test-side only.
- Lane ownership: `tests/test_knowledge_graph_health_read_boundary.py` is a
  lane-3-owned guard; no other lane's path is touched.

## Verification summary

| Check | Result |
|---|---|
| `tests/test_knowledge_graph_health_read_boundary.py` | 12 passed |
| `tests/test_knowledge_graph_health_ci_wiring.py` | 12 passed |
| `--collect-only` node count | 11 → 12 (+1, the new control) |
| Live negative control, always-clean | control reddens (`1 failed, 11 passed`) |
| Live negative control, always-dirty | sweep + control redden (`2 failed, 10 passed`) |
| File restored byte-identically | md5 `6940eb90…` before and after |
| `tests/architecture` | 11 passed |
| `scripts/lane_state.py --check` | exit 0 |

Merge, production deployment and acceptance remain human-only.
