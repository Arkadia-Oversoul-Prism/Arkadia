# Lane 4 — AO-006 canvas isolation negative-control integrity

**Pass:** 2026-11-08 (hourly bounded execution, reconciliation edition)
**Lane:** 4 — Arkana + Weaver + Engineering Lab
**Branch:** `lane4/ao006-canvas-control-integrity-01`
**Base `main`:** `d82c266cc4f193afcdb4e7f152136980572ba9fa` (PR #644 merge)
**Scope:** one test file. No console source, backend contract, registry, authority surface, or
other lane's file is touched.

## 1. Defect — the control restates the detector instead of calling it

`tests/test_ao006_canvas_contract.py` (added by #644) asserts that the canvas isolation is
structural: "no canvas route accepts a subject, owner or uid parameter", so cross-subject reads are
impossible by construction rather than by a check that could be forgotten.

The live assertion and its negative control each built the **same** detector inline, independently:

```python
# live node — test_no_canvas_route_accepts_a_subject_parameter
forbidden = {"subject", "subject_ref", "uid", "user_id", "owner", "owner_uid"}
offenders = []
for route in router.routes:
    for param in getattr(route, "dependant", None).query_params if route.dependant else []:
        if param.name in forbidden:
            offenders.append(f"{route.path} accepts {param.name!r}")
assert offenders == [], ...

# control — test_negative_control_a_subject_parameter_would_be_detected
forbidden = {"subject", "subject_ref", "uid", "user_id", "owner", "owner_uid"}
found = [param.name for route in probe.routes
         for param in route.dependant.query_params if param.name in forbidden]
assert found == ["subject"], ...
```

Two copies of one predicate, and the control exercises only its **own** copy. The control can
therefore never fail for an edit to the detector the live assertion actually uses.

Measured at `main` `d82c266c` with AST-scoped mutation (neuter the live node's own
`offenders.append` expression, then run the live node and its control separately):

| mutation | live node | control node | verdict |
|---|---|---|---|
| live detector neutered | pass | pass | the control is bound to nothing the live node uses |

Both nodes stayed green, so the live isolation detector could be disarmed with no red test.

This is the same defect class Lane 1 repaired in #631 / #634 / #636 / #637, Lane 2 in #635 / #640,
Lane 3 in #638 and Lane 4 in #639 / #641 / #642 / #643. It is the newest instance: it arrived on
`main` with the newest file (#644), which those passes did not reach. Found by a transitive
call-reachability sweep of every `tests/**/test_*.py` carrying `test_negative_control_*` nodes — a
control that calls no module-level helper reachable from any live node in its own file.

## 2. Repair

The predicate is extracted once to a module-level detector. The live assertion **and** its control
both call it, and the control asserts **both** polarities, so a detector that flags nothing and a
detector that flags everything each redden it.

```diff
+_CALLER_SUPPLIED_SCOPE_PARAMETERS = frozenset(
+    {"subject", "subject_ref", "uid", "user_id", "owner", "owner_uid"}
+)
+
+def _caller_supplied_scope_offenders(routes) -> list[str]:
+    return [
+        f"{route.path} accepts {param.name!r}"
+        for route in routes
+        for param in (getattr(route, "dependant", None).query_params if route.dependant else [])
+        if param.name in _CALLER_SUPPLIED_SCOPE_PARAMETERS
+    ]
+
 def test_no_canvas_route_accepts_a_subject_parameter():
-    forbidden = {...}
-    offenders = []
-    for route in router.routes: ...
-    assert offenders == [], ...
+    offenders = _caller_supplied_scope_offenders(router.routes)
+    assert offenders == [], ...

 def test_negative_control_a_subject_parameter_would_be_detected():
-    ... inline restatement ...
+    assert _caller_supplied_scope_offenders(probe.routes) == ["/probe accepts 'subject'"], ...
+    clean = [r for r in probe.routes if r.path == "/clean"]
+    assert _caller_supplied_scope_offenders(clean) == [], ...
```

The control now also carries a route that takes **no** scope parameter and asserts it is not
reported, so a detector that matches everything cannot pass either.

Node count is unchanged at **16** — this binds a control, it adds none.

## 3. Proof — discriminating A/B on the real file

Each mutation is applied by AST span to the shared detector body on the real file; the file is
restored byte-identically after every probe (asserted in the harness).

| mutation (on the repaired file) | live node | control node |
|---|---|---|
| none (baseline) | pass | pass |
| detector body → `return []` (neutered) | pass | **FAIL** |
| detector body → `if True` (always flags) | **FAIL** | pass |

The binding is exact: weakening the detector now reddens the **control** (it could not before), and
a detector that flags every route reddens the **live** node.

Pre-repair, the same first mutation left both nodes green (section 1), which is the vacuity.

## 4. Verification

- `python -m pytest tests/test_ao006_canvas_contract.py -q -rEf` → **16 passed**
- `python -m pytest tests/test_ao006_canvas_contract.py --collect-only -q` → **16 tests collected**
  (node count unchanged, so the file's delta is zero)
- `python -m pytest tests/architecture -q` → **11 passed**
- `python scripts/lane_state.py --check` → exit **0**
- No console-source, backend, registry or authority file is touched; `api/main.py` is untouched.

## 5. Recorded, not repaired — this guard is executed by no effective gate

Measured on this revision: `tests/test_ao006_canvas_contract.py` names neither
`web/arkadia_console` nor `api/frontend_routes`, so `scripts/console_contract_domain.py` (the
derived inventory the `Prism Console Contract` gate executes) does not include it —
`python scripts/console_contract_domain.py | grep -c test_ao006` → **0**.

Its only trigger is the `sg-02-fe-2-v.yml` `paths` filter (via `web/arkadia_console/**`, which
#644 touched), and that workflow's broad-suite step (`CP10-B broader backend regression`,
`python -m pytest tests/ -q`) aborts at the first collection error and executes **zero** tests —
the defect already recorded in
`docs/control-plane/evidence/gate10-ci-coverage-reconnaissance-01/RECONNAISSANCE.md`.

So this repair protects the control for every whole-suite invocation (a human run, or a future
gate) but no CI gate currently exercises it. **Discovery does not authorize execution**: wiring this
guard into a gate is either a console-domain widening (shared with the wiring judge, and a
sovereign decision) or a repair of the CP10-B broad-suite step. Both are separate bounded
workstreams and are recorded here rather than performed.

## 6. Boundary

Merge, production deployment and acceptance remain human-only. No production claim is made. This
evidence is bound to branch `lane4/ao006-canvas-control-integrity-01` from `main` `d82c266c`.
