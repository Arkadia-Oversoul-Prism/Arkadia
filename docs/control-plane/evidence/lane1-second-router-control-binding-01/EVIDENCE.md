# EVIDENCE — lane 1: bind the second-router detector to a control

**Pulse:** Weaver hourly bounded execution, 2026-11-20T05:06Z
**Base:** `main` `b842892b9fc64dede5e655db0d293da77248a430` (PR #657)
**Branch:** `lane1/second-router-control-binding-01`
**Lane:** 1 (shell / navigation / design system / integration seam)
**Owned paths touched:** `tests/test_console_shell_nav_contract.py` (lane-1 owned per
`SHARED-CONTRACTS.md` §1), this evidence record.
**Disposition:** IMPLEMENTED. Merge execution is human-only (GOV-03); this PR stays draft.

---

## 1. Defect — a lane-1 detector could be disarmed with every node green

`test_router_module_owns_the_only_pathname_resolution` asserted that no module outside
`router.ts` reads `window.location.pathname`. The detector was an **inline comprehension
inside the test**, so nothing else in the suite exercised it.

Measured at `main` `b842892b` by replacing that comprehension with `users = []`:

```
MUTATION A (neutered router-ownership detector): 53 passed in 1.85s
MUTATION B (neutered shell-mount detector):      1 failed, 52 passed in 1.84s
```

Mutation A left **all 53 nodes green**. A detector neutered to report nothing satisfies
`assert users == []` unconditionally, so the guard protecting the single-router invariant
could be removed with no red test. Mutation B, run as the same-instrument comparison,
correctly reddened — so the harness can detect this class, and the difference is binding,
not luck.

This is the defect class already recorded in `AGENTS.md` for
`tests/test_prism_opportunity_entry_flow.py` (lane 2, PR for
`lane2-opportunity-control-integrity-02`): a live assertion whose detector has no control
that calls it. `tests/test_console_shell_nav_contract.py` carries the sibling case: its
`_navigation_owners` helper was moved to module level **for exactly this reason**, and the
docstring says so — the router detector was never given the same treatment.

## 2. Repair — a module-level helper both the assertion and a control call

`_pathname_parsers(sources)` now holds the detector. The live assertion calls it, and
`test_detector_flags_a_second_pathname_parser` calls it with an injected
`SecondRouter.tsx` that reads the pathname.

**Both polarities are asserted**, so a detector that reports unconditionally cannot pass
either: the injected reader must be reported, and the live tree must not be.

### Discriminating A/B on the real file

Neutering the **shared helper body** (`return []`) is the exact mutation that was invisible
before the repair:

```
NEUTERED HELPER -> 1 failed, 53 passed
   FAILED tests/test_console_shell_nav_contract.py::test_detector_flags_a_second_pathname_parser
```

The control reddens for an edit to the detector it protects. Pre-repair the same mutation
was silent (53 passed). The file was restored byte-identically after the mutation
(`diff -q` clean).

## 3. Measured results

| Check | Result |
|---|---|
| `pytest tests/test_console_shell_nav_contract.py` | **54 passed** (was 53; +1 is the new control) |
| `pytest tests/test_console_endpoint_registry_contract.py` | 20 passed |
| `pytest tests/test_lane_instruction_doc_currency.py` | 55 passed |
| `scripts/lane_state.py --check --verify-live` | exit 0 |
| `pytest tests/architecture` | 11 passed |
| `scripts/console_contract_domain.py` | names this file, so the console gate executes it with **no workflow edit** |

Node count 53 -> 54 is exactly the added control; `--collect-only` on the file confirms 54.

## 4. Wiring

`scripts/console_contract_domain.py` derives the console-contract domain from tracked
content and names `tests/test_console_shell_nav_contract.py` (verified: the derived list
contains it). `.github/workflows/prism-console-contract.yml` executes
`pytest -q $(python scripts/console_contract_domain.py)`, so this guard runs in CI without a
workflow edit — the drift class PR #435 removed. No `paths:` change is required because the
workflow already selects `tests/**`.

## 5. Scope boundaries

- No console source, backend contract, endpoint registry, or other lane's file is touched.
- No protected authority, identity, K15/K3 governance, approval enforcement, or deployment
  configuration is altered.
- Merge, production deployment and acceptance remain human-only under GOV-03.

## 6. Why this PR does not edit the lane doc or the snapshot

This slice touches a **lane-1-owned** path, so a fresh `lane_state_refresh.py` derivation
would place it in lane 1's `open_prs`. Recording that in `lane-state.json` is
self-contradicting — the merge that lands this PR closes it, and `_pr_state_findings` then
reports "recorded as open but is MERGED" on `main` (the defect repaired for #610 by #613
and recurring on `main` at `b842892b`). `doc_guard` is not an escape: measured against the
live decision function, `current`, `deferred` and `idle` all yield the same finding; only
`open_prs: []` returns `[]`.

So neither the snapshot nor the four lane docs is touched here. `scripts/lane_state.py
--check` is **exit 0** on this branch (verified), because the snapshot and docs are exactly
as `main` carries them. The pre-existing `--check --verify-live` failure on `main` (8 DRIFT
findings — four merged PRs still recorded open) is owned by **PR #669**, not by this slice;
repairing it here would duplicate that PR's objective and its snapshot refresh.

Lane pointer re-derivation belongs to the snapshot refresh that follows this merge.

## 7. Reproduce

```bash
git checkout lane1/second-router-control-binding-01
python -m pytest tests/test_console_shell_nav_contract.py -q          # 54 passed

# control bites: neuter the shared helper, expect 1 failed
python - <<'PY'
import pathlib, subprocess
p = pathlib.Path("tests/test_console_shell_nav_contract.py"); o = p.read_text()
m = o.replace('''    return sorted(
        name
        for name, src in sources.items()
        if "window.location.pathname" in src and name != str(ROUTER_PATH.relative_to(ROOT))
    )''', '    return []')
assert m != o
p.write_text(m)
print(subprocess.run(["python","-m","pytest","tests/test_console_shell_nav_contract.py","-q","-rf"],
                     capture_output=True, text=True).stdout.strip().splitlines()[-1])
p.write_text(o)
PY
```
