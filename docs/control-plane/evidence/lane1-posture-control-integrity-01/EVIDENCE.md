# Lane 1 — bind the posture-currency revision control to its detector

**Branch:** `feat/prism-l1-posture-control-integrity-01`
**Base:** `main` `2015034389d82bcf1f1dbffd190f913bf6861790` (freshly fetched, observed 2026-11-07T18:2xZ)
**Ownership:** Lane 1 (`SHARED-CONTRACTS.md` §1, shared console contract tests). One file touched.
**Scope class:** test-side control integrity. No console source, backend contract, registry, or
other lane's file is touched.

## Objective

`tests/test_console_posture_currency.py` carried one negative control that restated its
detector inline:

```python
def test_negative_control_detector_flags_a_hardcoded_revision():
    defect = '<span className="topbar-meta tiny mono">ae847dd · reconciled</span>'
    assert re.findall(r"\b[0-9a-f]{7,40}\b", defect) == ["ae847dd"]
```

The live assertion reads the pattern inside `_hardcoded_revision_hits()`; the control held a
second, independent copy. Editing the live pattern therefore left the control green — the
detector could be disarmed with no red test. This is the same defect class repaired in
`tests/test_console_surface_error_boundary.py` and `tests/test_console_shell_nav_contract.py`
(#631) and in `tests/test_console_unified_interface_contract.py` (#634).

## Bounded scope

`tests/test_console_posture_currency.py` only. The revision pattern moves to a module-level
`_REVISION_RE` constant exposed through `hardcoded_revision_hits_in(text)`; the live detector
and its control both call that helper, and the control also asserts the repaired input is not
reported.

## Evidence

**Node count unchanged: 20** (`--collect-only` → 20; before the change → 20). This strengthens
a control; it adds none.

**Discriminating A/B on the real file** (the control is driven by the shared pattern, so a
change to the *live* pattern is observable to it):

| Shape | Live node | Control node |
|---|---|---|
| PRE-REPAIR (`main`), over-permissive live regex `\S+` | FAIL | **PASS** (vacuous) |
| POST-REPAIR, over-permissive shared `_REVISION_RE` | FAIL | **FAIL** (bound) |

Neutering the shared pattern (`NEVER_MATCHES`) reddens both the live node and the control on
the repaired file.

**Domain regression:** `pytest $(python scripts/console_contract_domain.py)` failing/error node
set is **identical** to the same command on `main` (38 nodes, `diff` empty). The 4
`test_every_declared_surface_is_served[...]` failures are **pre-existing `main` debt** —
measured on a clean `main` checkout before this change, same 4 nodes, 16 passed.

**Architecture:** `pytest tests/architecture -q` → 11 passed.

**Boundary:** `printf '<path>' | python scripts/cp10_mutation_boundary_policy.py --judge` → PASS.

## Classification

IMPLEMENTED. The control is bound to its detector and the binding is proven by mutation; the
node set is unchanged against `main`. Merge, production deployment, and acceptance remain
human-only.
