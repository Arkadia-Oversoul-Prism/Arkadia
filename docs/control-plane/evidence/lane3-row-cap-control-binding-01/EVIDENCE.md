# Lane 3 — bind the row-cap convention control to its detector

**Lane:** 3 (Solariun + Knowledge OS)
**Base:** `main` `4b91c2f416a104589283c3846a0766e252a08900`
**Branch:** `lane3/row-cap-control-binding-01`
**Scope:** `tests/test_knowledge_graph_provenance_boundary.py` only — lane-3 owned
(`SHARED-CONTRACTS.md` §1: Knowledge OS feature-local tests/evidence). No console source,
backend contract, registry, or other lane's file is touched. Node count unchanged at **29**.

## 1. The defect

`test_panel_discloses_the_row_cap` and `test_negative_control_a_bare_slice_is_not_the_convention`
were a live assertion and a control in name only. The live node asserted four literals
against `KnowledgeGraphPanel.tsx`; the control built its own `pre_repair` string and
asserted facts **about that string**:

```python
pre_repair = ("{graph.nodes.length > 0 && (\n"
              '  <ul data-testid="knowledge-graph-provenance-rows">\n' ...)
assert "boundedRowNotice" not in pre_repair           # a fact about a literal just written
assert 'data-testid="knowledge-graph-rows-bounded"' not in pre_repair
assert "boundedRowNotice" in PANEL_TSX.read_text(...)  # the only real read
```

The final line re-read the panel but tested one of four literals. Nothing connected the
control to the live assertion's detector, so the live assertion could be disarmed with no
failing test.

## 2. Measured before the repair

Neutering **every** assertion in `test_panel_discloses_the_row_cap` and re-running both nodes:

```
ALL-LIVE-NEUTERED: 2 passed, 27 deselected in 0.36s
```

Both green. The control proved nothing about the detector it claimed to prove.

## 3. The repair

The required literals move to `ROW_CAP_REQUIRED_LITERALS` and the predicate to a
module-level `_row_cap_defects(source)`. The live node and the control **both** call it:

```python
def _row_cap_defects(source: str) -> list[str]:
    return [reason for literal, reason in ROW_CAP_REQUIRED_LITERALS if literal not in source]

def test_panel_discloses_the_row_cap():
    assert _row_cap_defects(PANEL_TSX.read_text(encoding="utf-8")) == []

def test_negative_control_a_bare_slice_is_not_the_convention():
    reported = _row_cap_defects(PRE_REPAIR_PANEL_BODY)
    assert reported, "the detector must report a bare slice with no notice"
    assert "the panel must render the bounded-row notice" in reported
    assert _row_cap_defects(PANEL_TSX.read_text(encoding="utf-8")) == [], (
        "the shipped panel must be clean under the same detector the control used")
```

The control now asserts **both polarities**: the pre-repair shape is reported, and the
shipped panel is clean. A detector that flagged everything fails the second half; a
detector that flagged nothing fails the first.

## 4. Measured after the repair (discriminating A/B)

Mutating the **shared helper body** — not a fixture — then restoring byte-identically
(`restored byte-identical: True` asserted in the harness):

| Mutation of `_row_cap_defects` | Result |
|---|---|
| none (live) | `2 passed` |
| `return []` (always-clean) | `1 failed, 1 passed` — **control fails** |
| `return ['x']` (always-dirty) | `2 failed` — both fail |
| literal table emptied | `1 failed, 1 passed` — **control fails** |

`always-clean` is the load-bearing row: it is exactly the mutation that was invisible
before the repair.

## 5. Verification

| Check | Result |
|---|---|
| `pytest tests/test_knowledge_graph_provenance_boundary.py -q -rEf` | **29 passed** |
| `--collect-only` this file, branch vs `main` | **29 vs 29** (strengthening, not addition) |
| `pytest tests/architecture -q` | **11 passed** |
| `python scripts/lane_state.py --check` | exit **0** |
| CP10 boundary judge on the changed path | **PASS**, exit 0 |
| `scripts/console_contract_domain.py` names this file | **1** — gate executes it, no workflow edit |

## 6. Unknowns

- No full-suite pass was run this pulse (contract: at most one, and the change is a
  single test file's internal restructuring). Regression attribution is by node identity
  within the file plus the architecture suite; the full-suite baseline was not re-measured.
- `main` moved during the pulse (`b842892b` → `4b91c2f4`); the branch is created from
  `4b91c2f4` and this record is bound to that base.

Merge, production deployment and acceptance remain human-only under GOV-03.
