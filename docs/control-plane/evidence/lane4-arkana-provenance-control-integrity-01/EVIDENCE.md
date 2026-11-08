# Lane 4 — Arkana provenance negative-control integrity

**Pass:** 2026-11-08 (hourly bounded execution, reconciliation edition)
**Lane:** 4 — Arkana + Weaver + Engineering Lab
**Branch:** `feat/lane4-arkana-provenance-control-integrity-01`
**Base `main`:** `d1d7c601c8038047ba37e1024d3675a1cb396fe9`
**Scope:** one Lane-4-owned test file. No console source, backend contract, registry, authority
surface, or other lane's file is touched.

## 1. Defect — one orphaned detector, two vacuous controls

`tests/test_prism_rec_arkana_provenance.py` declares a module-level detector
`renders_provenance_from_a_constant(text)` — "a page that renders a provenance object the reply
did not supply". Two `test_negative_control_*` nodes call it and assert its both-polarity
behaviour:

- `test_negative_control_detector_flags_a_hardcoded_provenance`
- `test_negative_control_page_shape_is_flagged_as_constant_fed`

**No live assertion in the file calls it.** Every other assertion in the file is a plain substring
check (`'import { ArkanaProvenancePanel }' in page`, `"result.provenance" in page`, ...), so the
detector's whole purpose — "the provenance the panel renders is normalised from the response, not
invented" — was guarded **only** by nodes labelled as controls. Editing the detector to `return
False` reddened the two controls and nothing else; a page that fed the panel from a literal would
still pass every live node.

Measured at `main` `d1d7c601` with AST-scoped mutation (neuter the detector body, then run the
live nodes and the controls separately):

| mutation | live nodes red | control nodes red | verdict |
|---|---|---|---|
| `return False` | 0 | 2 | the detector is bound to nothing but its own controls |
| `return True` | 0 | 1 | same |
| `return None` | 0 | 2 | same |

A detector that no live assertion calls cannot fail for any edit to the property it claims to
protect. This is the same defect class Lane 1 repaired in #631 (`b2d33c80`) / #634 (`f495e1b6`),
Lane 2 in #635 (`20150343`), Lane 3 in #638 (`14aa82e0`) and Lane 4 in #639 (`e14fd5d7`); those
passes repaired the guards they owned and did not reach this one.

## 2. Repair

The detector is **bound to an existing live assertion** — no new node is added, and no node is
removed:

```python
def test_arkana_page_renders_the_provenance_panel():
    page = _read(PAGE)
    assert 'import { ArkanaProvenancePanel }' in page
    assert "<ArkanaProvenancePanel provenance={turn.provenance} />" in page
    assert not renders_provenance_from_a_constant(page)
```

This is the property the file's own docstring already states: "the provenance is normalised, not
invented ... the surface renders the normalized channels from `askArkana` ... not from a constant".
The live assertion now measures it.

The second control gains the opposite polarity, matching the convention the sibling passes set:

```python
def test_negative_control_page_shape_is_flagged_as_constant_fed():
    assert renders_provenance_from_a_constant(
        "<ArkanaProvenancePanel provenance={{ rag_refs: reply.rag_refs }} />"
    ) is True
    assert renders_provenance_from_a_constant(_read(PAGE)) is False
```

The detector's semantics are unchanged; the file's node count is unchanged at **15** — this binds
a control, it adds none.

## 3. Proof of the repair (live mutation, both polarities)

Post-repair, neutering the detector body reddens the live node **and** both controls:

```
renders_provenance_from_a_constant -> return True    live=FAIL control=FAIL
renders_provenance_from_a_constant -> return False   live=FAIL control=FAIL
```

Pre-repair the same mutation left every live node green. The discriminating property is
`live=FAIL`: the detector is now bound to a live assertion. The file was restored byte-identically
after every control run (asserted in the harness).

A two-polarity sweep over the whole file confirms the repaired detector is **BOUND** and that no
other detector in it is orphaned:

```
BOUND  _read                              T(live,ctl)=(12, 1)  F(live,ctl)=(12, 1)
BOUND  mutating_calls                     T(live,ctl)=(1, 1)   F(live,ctl)=(1, 1)
BOUND  renders_provenance_from_a_constant T(live,ctl)=(1, 2)   F(live,ctl)=(0, 2)
BOUND  _panel_renders_field               T(live,ctl)=(0, 0)   F(live,ctl)=(1, 0)
```

## 4. Verification

| command | result |
|---|---|
| `pytest tests/test_prism_rec_arkana_provenance.py -q` | **15 passed** |
| `pytest tests/architecture -q` | **11 passed** |
| `pytest --collect-only` (this file) | **15** collected (unchanged) |
| `pytest tests/ -q -rEf --continue-on-collection-errors` | **20 failed, 3978 passed, 18 skipped, 1 error** — the recorded `main` baseline node set (21 nodes, sha256 `7be4ad19...`); this file is absent from the failing set |

## 5. Boundaries

- Files touched: one Lane-4-owned test file, this evidence doc, `AGENT-04-ARKANA-WEAVER-LAB.md`
  (Lane 4's own instruction), and `lane-state.json` (refreshed in the same change — see §6).
- No console source, backend contract, registry entry, authority surface, or other lane's file.
- The PR stays **draft**. Merge, production deployment, and acceptance remain human-only.

## 6. Lane-doc currency

The slice edits `AGENT-04-ARKANA-WEAVER-LAB.md`, a guarded lane doc.
`scripts/lane_state.py::_freshness_findings` treats a commit after the newest snapshot commit that
touches a guarded lane doc as staleness, so merging as-is would redden `lane-doc-currency` on
`main` the instant the merge lands. The snapshot is re-derived with
`scripts/lane_state_refresh.py --write --base-main <fresh main>` in the same change, matching the
convention #614/#619/#633/#639 set.
