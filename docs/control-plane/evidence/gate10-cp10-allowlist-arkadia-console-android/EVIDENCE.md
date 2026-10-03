# GATE-10 · CP10 allowlist — admit `arkadia-console-android/`

**Status:** IMPLEMENTED — sovereign review required
**Date:** 2026-10-03
**Base main:** `d798811e6197db8cdb46fe5302f274765cd6f883` (merge PR #236, feature/mie-mvp-01)
**Branch:** `gate10/cp10-allowlist-arkadia-console-android`
**Gate:** GATE-10 (governed execution) · mutation boundary `SG-02-FE.2-V`

## 1. Objective

Restore the CP10 mutation boundary to a truthful inventory of the repository's
tracked surfaces by admitting the one surface `main` tracks and the allowlist
omits — `arkadia-console-android/` — so that the gate stops rejecting legitimate
work and its three fitness tests stop failing on `main`.

## 2. Evidence-backed defect

The CP10 policy (`scripts/cp10_mutation_boundary_policy.py`) holds `LEGIT`, the
only copy of the admit-list. Its invariant is stated in `AGENTS.md`:

> **The invariant, not the list:** every path in `git ls-files` must be admitted
> by the policy module.

Measured against the live tree at `d798811`:

```
$ python - <<'PY'
import importlib.util, subprocess
spec = importlib.util.spec_from_file_location("pol", "scripts/cp10_mutation_boundary_policy.py")
pol = importlib.util.module_from_spec(spec); spec.loader.exec_module(pol)
paths = subprocess.run(["git","ls-files"], capture_output=True, text=True).stdout.splitlines()
rej = [p for p in paths if not pol.evaluate_changed_paths([p])[0]]
print(len(paths), len(rej), sorted({p.split('/',1)[0] for p in rej}))
PY
1726 18 ['arkadia-console-android']
```

**1726 tracked paths, 18 rejected, exactly one rejected top-level prefix:**
`arkadia-console-android/`. Every rejected path is a legitimate native-product
surface (Kotlin sources, Gradle build files, resources) merged to `main` by the
Arkadia Console Android work.

Consequence on `main` (three fitness nodes red):

- `tests/test_m02a_ci_gate_integrity.py::test_allowlist_admits_every_tracked_top_level_prefix`
- `tests/test_m02a_ci_gate_integrity.py::test_allowlist_covers_every_tracked_surface`
- `tests/test_m02a_ci_gate_integrity.py::test_delegated_verdict_admits_every_tracked_surface`

This is the recurring defect class `AGENTS.md` records (omissions previously:
root narrative docs, `conftest.py`, `knowledge/`, `spiral_grove/`, `opportunity_radar/`,
`reconciliation/`, `economic_seams/`, `musical-intention-engine/`). Per that
guidance: *"a path that is plainly legitimate work means the allowlist is wrong,
not the commit."* The repair is an allowlist omission fix, not a gate weakening —
the `forbid` stage (constitutional V3/V2) and the unknown-root rejection are
untouched.

## 3. Change

`scripts/cp10_mutation_boundary_policy.py` — one alternation added to `LEGIT`
(`|arkadia-console-android/`), plus the omission comment. The stale path-count
prose in the module header ("83 entries, 1645 paths at 886759f") was replaced
with the current measured count; no other rule changed.

## 4. Verification

### 4.1 Fitness tests — the invariant

```
$ PYTHONPATH=$PWD/archive/legacy_python python -m pytest tests/test_m02a_ci_gate_integrity.py -q
55 passed in 0.26s
```

### 4.2 Live `--judge` (the code the workflow executes) with negative controls

| input path | verdict | rc |
|---|---|---|
| `arkadia-console-android/app/src/main/kotlin/com/arkadia/console/MainActivity.kt` | PASS | 0 |
| `totally-unknown-root/x.txt` | reject (unknown root) | 1 |
| `web/public_prism/src/components/SolSpireExperienceV3.tsx` | reject (V3 dual shell) | 1 |
| `vault/Ideas/note.md` | reject (vault outside scaffold) | 1 |

The allowlist widened by exactly one legitimate surface; all three teeth of the
boundary still bite.

### 4.3 Full-suite node delta (not counts)

Command: `PYTHONPATH=$PWD/archive/legacy_python python -m pytest tests/ -q --continue-on-collection-errors`

| | before | after |
|---|---|---|
| result | 30 failed, 1354 passed, 20 skipped, 1 error | 27 failed, 1357 passed, 20 skipped, 1 error |
| failing/error node set | 31 nodes | 28 nodes |

Node-set delta is **exactly** the three `test_m02a_ci_gate_integrity.py` nodes
removed; **zero new failing nodes** (`comm -23 after baseline` shows no node that
was absent before). The remaining 28 nodes are pre-existing `main` debt
(frontend projection + boundary-literal assertions), unchanged by this pass and
out of scope.

## 5. Baseline classification of remaining debt (recorded, not fixed)

The 28 remaining nodes are unchanged by this pass. Classification of the subset
inspected this run:

| node(s) | class |
|---|---|
| `tests/test_agents_md_encoding_adjudication.py` (3) | boundary literal / oracle-revision access; `AGENTS.md` insertion-only constraint |
| `tests/test_evidence_verification_boundary.py`, `test_verification_review_boundary.py`, `test_workevent_evidence_boundary.py` | boundary-literal assertions; **not** a new HTTP mutation path (the two store calls in `solspire/console_authority_router.py` are pre-existing) |
| `tests/test_steward_filter.py` (3) | content-filter behaviour mismatch |
| `tests/test_solspire_project_*`, `test_solspire_p1_experience_01`, `test_solspire_r*` | frontend projection + governance literal pins |
| `tests/test_autonomy.py` (collection ERROR) | `weaver.autonomy` module-vs-package collision — reserved to the sovereign |

Each of these is a candidate **separate** bounded workstream. None is a
dependency of this gate repair.

## 6. Authority boundary

- Mutation: one policy alternation + evidence. No merge, no push to `main`.
- Human authority is required to merge.
- No scope expansion: the 28 pre-existing nodes are recorded, not repaired here.
- Rollback: revert the single `LEGIT` alternation and delete this evidence
  directory; no other file is touched.
