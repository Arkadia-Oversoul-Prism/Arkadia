# Lane 4 — scheduler report negative-control integrity

**Pass:** 2026-11-08 (hourly bounded execution, reconciliation edition)
**Lane:** 4 — Arkana + Weaver + Engineering Lab
**Branch:** `feat/prism-l4-scheduler-report-control-integrity-01`
**Base `main`:** `1550a5a1535fa205cc076b68854bc8e8238caf20`
**Scope:** one Lane-4-owned test file. No console source, backend contract, registry, authority
surface, or other lane's file is touched.

## 1. Defect — one orphaned detector

`tests/test_scheduler_trajectory_conformance.py` declares a module-level detector
`_report_names_blockers(script)` — "the report step reads the session result and prints its
blockers", the property the GATE-07 session-report repair (`ef5df651`) exists to hold. Its control
`test_negative_control_pre_fix_report_is_silent` calls it in **both** polarities (the pre-fix
echo-only report → `False`, the live step → `True`).

**No live assertion in the file calls it.** The live node that states the same property,
`test_session_report_surfaces_router_blockers`, reaches the workflow text only through the
*neighbouring* helper `_report_program(step["run"])`, which returns the embedded heredoc program:

```python
program = _report_program(step.get("run") or "")
assert program, "the session report no longer embeds a blockers program"
```

`_report_program` returns the program text; it does not assert that the program *names the
blockers*. So the detector's whole purpose — "the report step reads
`engineering-session-result.json` and prints its `blockers`" — was guarded **only** by a node
labelled as a control. The control protects the detector; nothing protects the control. Editing the
detector to `return False` (or `return None`) reddens the control and **no live node**, so the
shared detector can be disarmed with no live red test.

Measured at `main` `1550a5a1` with AST-scoped mutation (neuter the detector body, then run the live
nodes and the control separately):

| mutation | live nodes red | control nodes red | verdict |
|---|---|---|---|
| `return False` | 0 | 1 | the detector is bound to nothing but its own control |
| `return True` | 0 | 1 | same |
| `return None` | 0 | 1 | same |

This is the same defect class Lane 1 repaired in #631 (`b2d33c80`) / #634 (`f495e1b6`) / #636
(`35e03fcb`) / #637 (`03220c95`), Lane 2 in #635 (`20150343`) / #640 (`d1d7c601`), Lane 3 in #638
(`14aa82e0`) and Lane 4 in #639 (`e14fd5d7`) / #641 (`e07ee81e`) / #642 (`1550a5a1`); those passes
repaired the guards they owned and did not reach this one. It was found by a transitive
call-reachability sweep of every `tests/**/test_*.py` carrying `test_negative_control_*` nodes:
a module-level helper reachable from the control nodes but from **no** live node.

## 2. Repair

The detector is bound to an **existing** live assertion. No node is added or removed.

```diff
     program = _report_program(step.get("run") or "")
     assert program, "the session report no longer embeds a blockers program"
+    # The same property through `_report_names_blockers` — the detector the file's
+    # own control is written against. Without this call the detector is reached only
+    # by its control, so weakening it reddens nothing but a node labelled a control.
+    assert _report_names_blockers(step.get("run") or ""), (
+        "the live report step no longer reads the session result and prints its "
+        "blockers; the pre-fix echo-only report this guard exists to catch would "
+        "pass unremarked"
+    )
```

This is the property the node's own name and docstring already state ("the report must print the
router's blockers, not just the status"). Node count is unchanged at **23**.

## 3. Proof — live mutation on the real file

Post-repair, neutering the detector body reddens the live node **and** the control:

```
--- return False: live[1 failed, 22 deselected] ctrl[1 failed, 22 deselected]
--- return True:  live[1 passed, 22 deselected] ctrl[1 failed, 22 deselected]
--- return None:  live[1 failed, 22 deselected] ctrl[1 failed, 22 deselected]
restored byte-identical: True
--- unmutated ---
   test_session_report_surfaces_router_blockers   1 passed
   test_negative_control_pre_fix_report_is_silent 1 passed
```

`return True` reddens the control because the control asserts the pre-fix report is *not* reported;
`return False` / `return None` redden the live node. The union of the three covers every degenerate
body, so no single-value mutation leaves both nodes green.

## 4. Verification

```
python -m pytest tests/test_scheduler_trajectory_conformance.py -q -rEf
  -> 23 passed
python -m pytest tests/test_scheduler_trajectory_conformance.py --collect-only -q
  -> 23 tests collected   (base main 1550a5a1, collected in place: 23)
python -m pytest tests/architecture -q
  -> see section 5
```

The guard is CI-live: `.github/workflows/arkadia-engineering-scheduler.yml` both selects the file
in its `paths` filter (line 28) and executes it (line 71), so this repair is judged by the gate it
strengthens.

## 5. Baseline comparison and scope

- Node count: **23** before and after — this binds a control, it adds none.
- Changed files: `tests/test_scheduler_trajectory_conformance.py` (+8 lines),
  `docs/control-plane/parallel-ui/AGENT-04-ARKANA-WEAVER-LAB.md`, and
  `docs/control-plane/parallel-ui/lane-state.json` (derived by `scripts/lane_state_refresh.py`).
- No console source, backend contract, registry, endpoint, or authority surface is touched.
- Merge, production deployment and acceptance remain human-only.
