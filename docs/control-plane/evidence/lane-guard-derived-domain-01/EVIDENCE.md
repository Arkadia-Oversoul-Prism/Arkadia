# Lane-guard derived domain — the gate now executes the corpus it verifies

**Pass:** `gate-hygiene/lane-guard-derived-domain-01`
**Base:** `main` `36f53be22d753ffe269f05cbf3fb39212f744207`
**Stacked on:** PR #567 (`gate-hygiene/lane-guard-authority-boundary-01`, head `bebb6ed4`),
PR #568 (`gate-hygiene/lane-guard-fixed-scope-01`, head `76f6d87a`)
**Status:** IMPLEMENTED (tests + live negative controls pass; sovereign merge authority)
**Authorization:** none required — repository-local, non-consequential, no authority surface touched.

---

## 1. Defect — the acceptance test for the scope repair was executed by nothing

PR #567 introduced `tests/test_lane_guard_scope_boundary.py`, the acceptance test that
proves the enforced lane set is a constant rather than a function of live PR activity.
PR #568 repaired the scope derivation itself.

Neither PR wired the new guard into `.github/workflows/lane-doc-currency.yml`. Measured
at `76f6d87a`:

| | count |
|---|---|
| guards in the derived domain | **4** |
| guards the gate **executed** | **3** |
| guards the gate's `paths` filters **named** | **3** |

The omission is precisely `tests/test_lane_guard_scope_boundary.py`. The guard that
proves the scope repair held was, itself, run by no workflow — the "a guard no workflow
executes is decoration" class this repository has already closed for
`test_baseline_fingerprint.py`, `scripts/baseline_preflight.py` and
`test_boot_syntax_boundary.py`.

## 2. Why the per-PR view could not see it

A fixed list in the workflow is invisible to the PR that adds a guard: #567 added the
guard and every check it ran was green, because the guard passes when executed by hand.
The gap is only observable from the **composition** — a domain derived from the corpus
against a gate carrying a remembered subset. This is the same hazard PR #435 removed for
the console contract, where `main` went red at `17988afd` after three guards merged into
a domain the gate had enumerated before they existed.

## 3. Repair — one derivation, two consumers

New single source of truth: `scripts/lane_guard_domain.py`.

* `derive_domain()` scans the tracked test corpus (`git ls-files -- tests/`) for modules
  naming the lane substrate (`lane_state`, `lane_scope_probe`, `lane-state.json`) and
  returns them sorted.
* It is read-only, runs no tests, mutates nothing, never prints a token. It exits **2**
  on a git/IO fault or an empty domain, so an empty derivation can never read as a
  satisfied contract.

The workflow executes the derived inventory:

```yaml
run: python -m pytest -q $(python scripts/lane_guard_domain.py)
```

The wiring judge (`tests/test_lane_currency_ci_wiring.py`) imports `derive_domain` from
the same file, so the **executed** inventory and the **verified** inventory cannot
disagree. A guard added to the corpus is executed without editing the workflow.

`tests/test_lane_instruction_doc_currency.py` had pinned the literal
`pytest -q tests/test_lane_instruction_doc_currency.py`; that pin is re-pointed at the
derived form, because a fixed list stops covering the corpus the moment a guard is added.

## 4. Measured result

Corpus, run exactly as the gate runs it:

```
$ python -m pytest -q $(python scripts/lane_guard_domain.py)
81 passed in 0.73s          # was 73 passed at 76f6d87a
```

`--collect-only` attributes the delta by node identity. At `76f6d87a` the domain
collects 73 nodes (wiring 17 + doc-currency 37 + fixed-scope 14 + scope-boundary 5);
after the change it collects 81. All **+8** are in
`tests/test_lane_currency_ci_wiring.py` (17 → 25): 4 nodes from parametrizing
`test_workflow_executes_every_guard_in_the_derived_domain` over the derived domain, plus
the new drift-regression and detector controls. The doc-currency file stays at 37 — its
pin was re-pointed, not added to. Attribution by node count, not by the pass total.

```
$ python scripts/lane_state.py --check
enforced lanes: ['1', '2', '3', '4']; doc_guard (descriptive): ['1', '2'] current, ['3', '4'] deferred
lane instruction docs consistent with snapshot (4 enforced lanes)
```

The scope repair from #567/#568 is intact — the enforced set is the `CANONICAL_LANES`
literal — and is now genuinely executed by the gate.

## 5. Live negative controls (on the real workflow file)

Each mutates `.github/workflows/lane-doc-currency.yml`, asserts the guard reddens, and
restores byte-identically (verified by sha256 `abc4d282ad4cf00f9eb908dde50ee8f04431a6cc46eac580fa15c12cf2ee3166`
before and after).

| control | mutation | result |
|---|---|---|
| NC1 | derived run → fixed list | **4 failed**, 21 passed |
| NC2 | derived run → `echo python -m pytest …` | **4 failed**, 21 passed |
| NC3 | scope-boundary guard removed from filter *and* step (the measured defect) | **2 failed**, 23 passed |

**NC2 initially passed — a real hole in this guard, found by its own control.** The first
`_pytest_command_index` accepted the word `pytest` whenever `-m` immediately preceded it,
so `echo python -m pytest -q $(python scripts/lane_guard_domain.py)` read as an execution.
Repaired to require the interpreter as the **first** token; a regression control
(`test_detector_rejects_echo_prefixed_interpreter_invocation`) now pins that form. A guard
whose detector cannot fail is not a guard, and this control is why the hole is not shipped.

## 6. Regression boundary

* `api/main.py` untouched (budget unaffected).
* No authority surface, no mutation path, no identity boundary changed.
* CP10 boundary judge admits all four changed paths
  (`scripts/lane_guard_domain.py`, the workflow, and the two test files).
* The four derived guards pass; `tests/architecture` unaffected by this change.

## 7. Remaining uncertainty

* The **domain needle set** is a heuristic. A future lane guard that names the substrate
  differently (e.g. only `parallel-ui`) would be missed. `test_domain_is_derived_and_not_empty`
  pins one known member so a needle break is loud rather than silent, but the needle set is
  the residual risk and is recorded as such rather than claimed as complete.
* PRs #567 and #568 remain **open drafts**; this pass stacks on #568. Merge order is the
  sovereign's. This branch does not merge, deploy, or claim production acceptance.
