# Lane 4 — Lab resume negative-control integrity

**Pass:** 2026-11-08 (hourly bounded execution, reconciliation edition)
**Lane:** 4 — Arkana + Weaver + Engineering Lab
**Branch:** `feat/prism-l4-lab-resume-control-integrity-01`
**Base `main`:** `e07ee81ea75668c43885ccac49859c77fd05d417`
**Scope:** one Lane-4-owned test file. No console source, backend contract, registry, authority
surface, or other lane's file is touched.

## 1. Defect — one orphaned detector

`tests/test_lab_mission_workspace_contract.py` declares a module-level detector
`_resume_reconstructs_authorization(source)` — "a resume handler that sets an authorization object
it cannot have read". Its control
`test_negative_control_resume_detector_flags_a_reconstructed_authorization` calls it in **both**
polarities (broken shape → `True`, repaired shape → `False`, live file → `False`).

**No live assertion in the file calls it.** The live node that states the same property,
`test_resume_never_reconstructs_an_authorization`, restates the property **inline** instead:

```python
body = _resume_handler_body(workspace)
assert "setAuthorization" not in body, (...)
```

So the detector's whole purpose — "a resume path that writes an authorization object while no
served route returns one" — was guarded **only** by a node labelled as a control. The control
protects the detector; nothing protects the control. Editing the detector to `return False` (or
`return True`, or `return None`) reddens the control and **no live node**, so the shared detector
can be disarmed with no live red test.

Measured at `main` `e07ee81e` with AST-scoped mutation (neuter the detector body, then run the
whole file):

| mutation | live nodes red | control nodes red | verdict |
|---|---|---|---|
| `return False` | 0 | 1 | the detector is bound to nothing but its own control |
| `return True` | 0 | 1 | same |
| `return None` | 0 | 1 | same |

This is the same defect class Lane 1 repaired in #631 (`b2d33c80`) / #634 (`f495e1b6`) / #636
(`35e03fcb`) / #637 (`03220c95`), Lane 2 in #635 (`20150343`) / #640 (`d1d7c601`), Lane 3 in #638
(`14aa82e0`) and Lane 4 in #639 (`e14fd5d7`) / #641 (`e07ee81e`); those passes repaired the guards
they owned and did not reach this one.

## 2. Repair

The detector is **bound to an existing live assertion** — no new node is added, and no node is
removed:

```python
def test_resume_never_reconstructs_an_authorization():
    ...
    assert "setAuthorization" not in body, (...)
    # The same property through `_resume_reconstructs_authorization` — the
    # detector the file's own control is written against.
    assert not _resume_reconstructs_authorization(workspace), (...)
```

This is the property the node's own docstring already states: "A surface that rebuilt an
`LabAuthorization` from the stored id would be asserting `originated_by: "human"` on evidence it
does not have". The live assertion now measures it through the shared detector.

The detector's semantics are unchanged; the file's node count is unchanged at **29** — this binds
a control, it adds none.

## 3. Proof of the repair (live mutation, both polarities)

Post-repair, neutering the detector body reddens the live node **and** the control in the
over-permissive direction:

```
_resume_reconstructs_authorization -> return True    live=FAIL control=FAIL   (2 failed, 27 passed)
_resume_reconstructs_authorization -> return False   live=pass control=FAIL   (1 failed, 28 passed)
_resume_reconstructs_authorization -> return None    live=pass control=FAIL   (1 failed, 28 passed)
```

Pre-repair the same `return True` mutation left every live node green (0 live red, 1 control red).

The discriminating property is **`live=FAIL` under `return True`**: the detector is now bound to a
live assertion, so a detector that reports *everything* as reconstructed can no longer pass.

The `return False` / `return None` directions redden **only** the control, and that is correct, not
a gap: the live node asserts the *absence* of the defect, so a detector that reports nothing yields
`False`, which satisfies `assert not _resume_reconstructs_authorization(workspace)`. Recording the
per-direction result rather than a blanket "both redden" — the direction that reddens both is
`return True`. (The sibling pass #636 corrected exactly this over-claim in its own evidence.)

The file was restored byte-identically after every control run (asserted in the harness).

## 4. Verification

| command | result |
|---|---|
| `pytest tests/test_lab_mission_workspace_contract.py -q -rEf` | **29 passed** |
| `pytest tests/test_lab_mission_workspace_contract.py --collect-only` | **29** collected (unchanged) |
| `pytest tests/architecture -q` | **11 passed** |
| `pytest -q $(python scripts/console_contract_domain.py)` | **1123 passed, 10 failed** — the 10 are the documented missing-`node_modules` TypeScript toolchain in `test_mission_lifecycle_adapter_contract.py` (the #633/#634/#639/#641 baseline); this file is absent from the failing set |
| `pytest tests/test_lane_instruction_doc_currency.py tests/test_lane_currency_ci_wiring.py tests/test_prism_console_ci_wiring.py -q` | **98 passed** |
| `python scripts/lane_state.py --check` | exit **0** |

The guard is executed by the console-contract gate, whose domain
`scripts/console_contract_domain.py` derives at test time, so **no workflow edit is needed** for
this slice.

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
`scripts/lane_state_refresh.py --write --base-main e07ee81e` in the same change, matching the
convention #614/#619/#633/#639/#641 set.

The lane declares no active PR in its appended block: a lane PR cannot declare itself open at merge
time, because the merge that lands it closes it. The lane's status is left to the derived snapshot,
the convention #638/#639/#641 set.
