# gate10/economic-seam-gate-domain-completion-01 — execute the whole economic-seam guard domain

**Status:** IMPLEMENTED — repair proven locally, PR open, human merge required.
**Branch:** `gate10/economic-seam-gate-domain-completion-01`
**Base:** `main` @ `850216fc99b0eab66a66f8a8290c0db33823b681`
**Related (not competing):** PR #447 (`gate10/prism-console-contract-domain-derivation-01`) is a
*different* file and a *different* question — see §7.

## 1. Defect (measured, not inferred)

The provider-neutral economic seam engine (`economic_seams/`) and the sovereign scan surface
that fronts it (`api/economic_seam_routes.py`) are judged by a set of contract guards. The only
workflow that runs any of them, `.github/workflows/economic-seam-engine.yml`, carried a **fixed
inventory** in both its `paths` filters and its executing step.

Derived from guard content at `main` @ `850216fc`, the domain is **seven** modules — every
tracked test that names `economic_seams` or `economic_seam_routes` (including the joined
spellings several guards build with `Path` segments):

```
tests/test_deal_sheet.py
tests/test_economic_seam_authority_boundary.py
tests/test_economic_seam_correlation.py
tests/test_economic_seam_engine.py
tests/test_m02a_ci_gate_integrity.py
tests/test_market_data.py
tests/test_nocopo_adapter.py
```

The gate executed **five**. Two arrived after the inventory was written:

| guard | what it holds | in gate before this change |
|---|---|---|
| `tests/test_economic_seam_authority_boundary.py` | the sovereign-boundary pin for the seam | **no** |
| `tests/test_m02a_ci_gate_integrity.py` | the CP10 coupling to this seam | **no** |

Measured on `main` @ `850216fc`, gate step:

```
pytest -q tests/test_economic_seam_engine.py tests/test_economic_seam_correlation.py \
  tests/test_nocopo_adapter.py tests/test_market_data.py tests/test_deal_sheet.py
```

and the same five in both `paths` filters. The sovereign-boundary pin — the guard that holds the
seam's authority boundary — was executed by **no** workflow: `grep -rn
test_economic_seam_authority_boundary .github/workflows/` returns the gate file, and the gate did
not name it. A guard no workflow executes is decoration.

**No single pull request could have observed this.** The guard arrived after the inventory was
written, and nothing asserted the two agreed. That is the defect class this change closes.

## 2. What changed

Two files, bounded to the seam gate and its judge.

### 2.1 `.github/workflows/economic-seam-engine.yml` — execute the whole domain

* The executing step now names all **seven** derived guards.
* Both `paths` filters select `tests/**` rather than an enumerated guard list, so a guard *added*
  to the corpus triggers the judge that would otherwise never run to report it unexecuted. The
  judge still asserts every derived guard is selected, so narrowing the filter reddens it.
* `workflow_dispatch` added. The gate is path-filtered, so a revision touching none of its paths
  has no execution; this makes the contract executable against an exact revision on demand.
* `permissions: contents: read`, `timeout-minutes: 10`, `PYTHONPATH: .` pinned.

### 2.2 `tests/test_economic_seam_ci_wiring.py` — new wiring judge

Mirrors the accepted convention of `tests/test_prism_console_ci_wiring.py` **exactly**: the judge
derives the domain from guard content at test time and asserts the gate executes the whole derived
set, while the gate carries an enumerated inventory. The two agree because the gate's `paths`
filter selects `tests/**` and the judge is named in it.

Invariants, each parametrized over **every** workflow that references the domain:

1. At least one workflow executes the whole derived domain.
2. Such a gate is selected by the surfaces it judges, by every guard it runs, and by its own file.
3. Such a gate is dispatchable.
4. A complete gate's executing steps can fail the run — no step- or job-level
   `continue-on-error`, no step- or job-level `if: false`.

Rule 4 is scoped to the complete gate(s) deliberately: `sg-02-fe-2-v.yml` runs the whole suite on
a `continue-on-error: true` step as recorded pre-existing debt from another workstream, and
re-litigating that here would be scope expansion.

The judge derives its domain by reading guard content, and the detector is proven against the
forms it is meant to catch (§4).

## 3. Commands run

```
python -m pytest tests/test_economic_seam_ci_wiring.py -q -rEf   # 21 passed
python -m pytest tests/architecture -q -rEf                      # 11 passed
printf 'tests/test_economic_seam_ci_wiring.py\n.github/workflows/economic-seam-engine.yml\n' \
  | python scripts/cp10_mutation_boundary_policy.py --judge      # PASS, exit 0
```

The gate's own executing step, run verbatim:

```
PYTHONPATH=. python -m pytest -q tests/test_deal_sheet.py \
  tests/test_economic_seam_authority_boundary.py tests/test_economic_seam_correlation.py \
  tests/test_economic_seam_engine.py tests/test_m02a_ci_gate_integrity.py \
  tests/test_market_data.py tests/test_nocopo_adapter.py
124 passed, 1 warning in 1.33s
```

Architecture **11/11** (the contract's older "9/10" does not reproduce on this revision).
CP10 admits both changed paths; no allowlist edit was needed.

**One environment caveat, measured.** On the first run of that step the sandbox reported
`1 failed` — `tests/test_market_data.py::test_nepc_unparseable_pdf_fails_closed_at_fetch_boundary`
raising `ModuleNotFoundError: No module named 'pdfminer'`. `pdfminer.six` is a declared
dependency (`requirements.txt` lines 8, 18, 36, 48, 62) and the gate installs `requirements.txt`
before running the step, so this is a **local sandbox gap, not a source defect**. After
`pip install pdfminer.six` the step is **124 passed**. The same node is present in the `main`
baseline node set, so it is baseline debt under this sandbox's dependency set and is neither
introduced nor repaired here.

## 4. Live negative controls (against the real workflow file)

Each control mutates `.github/workflows/economic-seam-engine.yml` itself, runs the judge, then
restores the file byte-identically (sha256 `ef6f325b190e981ff455e8c7edd7cef642547b450420ea8954fbaf66c5ace24a`
before and after).

| control | mutation | result |
|---|---|---|
| drop the boundary pin | delete `tests/test_economic_seam_authority_boundary.py` from the step | **2 failed**, 17 passed, 2 skipped |
| narrow the filter | replace `'tests/**'` with one guard path | **1 failed**, 20 passed |
| remove dispatchability | delete the `workflow_dispatch:` key | **1 failed**, 20 passed |
| exempt the step | `continue-on-error: true` on the executing step | **2 failed**, 17 passed, 2 skipped |

Synthetic controls inside the judge additionally prove the detector flags: a bare `echo` of the
guard list; a comment-only mention; `pytest` appearing as an **argument** to another command
(`echo pytest …`, `printf %s pytest …`, `echo 'python -m pytest …'`); a partial domain; the exact
**shipped pre-fix inventory** (asserting both missing guards are measured as unexecuted); an
incomplete filter; and step- and job-level `continue-on-error` / `if: false`. Two positive
controls prove it stays silent on the wired shape and accepts a directory invocation
(`pytest tests/ -q`), so the detector is not trivially red.

`test_selector_rejects_unrelated_paths` guards the glob translation itself: a selector that
matched everything would make every filter assertion vacuous.

## 5. Baseline comparison

Baseline measured on `main` @ `850216fc` (same environment, `-rEf --continue-on-collection-errors`):

| | main | branch |
|---|---|---|
| failing/error nodes | 71 (60 F, 11 E) | **71 (60 F, 11 E)** |
| outcomes fingerprint | `d731a6c230c00b5aedd023f35e8c719f57b9b0b2a560bf67aee4d319b390c9f6` | **identical** |
| ids fingerprint | `3f769cc1d99b3403d3610e824cd3b80d97b3c14ac663ad7ddf25dcfee06ea177` | **identical** |
| passed | 2509 | **2530** |
| skipped | 34 | 34 |

The load-bearing invariant is the sorted failing/error **node set**, not the counts. A set
comparison by node identity returns `only in baseline: []`, `only in branch: []` — **zero
regression**. The `+21 passed` is attributed by measurement, not inference:
`pytest tests/test_economic_seam_ci_wiring.py --collect-only -q` → **21 tests collected**, exactly
the delta. No pre-existing failure was fixed, and none was introduced.

## 6. Measured result on the branch

```
python -m pytest tests/ -q -rEf --continue-on-collection-errors
60 failed, 2530 passed, 34 skipped, 9 warnings, 11 errors in 189.36s (0:03:09)
```

Baseline on `main` @ `850216fc`, same command and environment:

```
60 failed, 2509 passed, 34 skipped, 9 warnings, 11 errors in 187.93s (0:03:07)
```

Failing/error node set identical on both sides (71 nodes, both fingerprints unchanged). The 60
failures and 11 errors are pre-existing main debt, recorded here and **not** repaired — repairing
them is not this gate's scope.

## 7. Relationship to PR #447 (not a competitor)

PR #447 (`gate10/prism-console-contract-domain-derivation-01`, draft) derives the **console**
gate's inventory from `scripts/console_contract_domain.py`. That is a *different file* and a
*wider execution surface*: a workflow that computes its own inventory from a script executes
whatever that script returns.

This change deliberately does **not** do that for the seam. Main's console gate carries an
enumerated inventory today and its judge asserts the domain is executed; this change mirrors that
accepted shape so the two gates stay comparable, and leaves derivation — if the sovereign wants it
— to #447's workstream rather than pre-empting it here. The judge's docstring records this
explicitly, so a future pass does not read the enumeration as an oversight.

## 8. Runtime evidence (CI) — the gate now executes the whole domain

Run **`38174340491`** on head `b54eaeb49a2041c5c68bc8365d4e903fcf253ed4`
(`event=pull_request`, `completed/success`) is the first execution of the repaired gate. Both
steps succeeded, and the step log proves the guards actually ran rather than merely that the job
exited 0:

```
Verify the economic-seam contract guards
  python -m pytest -q tests/test_deal_sheet.py tests/test_economic_seam_authority_boundary.py \
    tests/test_economic_seam_correlation.py tests/test_economic_seam_engine.py \
    tests/test_m02a_ci_gate_integrity.py tests/test_market_data.py tests/test_nocopo_adapter.py
  124 passed in 1.48s

Economic-seam CI-wiring guard
  python -m pytest tests/test_economic_seam_ci_wiring.py -q
  21 passed in 4.13s
```

`124 passed` in CI (against `124 passed` locally) confirms the two previously-unexecuted guards
are now executed, and that the dependency gap recorded in §3 is a sandbox artifact only — CI
installs `requirements.txt` and the node passes there.

## 9. The `tests/**` filter widening — trade-off, stated

The filter was widened from seven named files to `tests/**`. That is the only way an **added**
seam guard triggers the gate that must judge it: a filter naming today's guards cannot fire when a
guard does not yet exist, which is precisely how the two guards went unexecuted.

The cost is real and is recorded rather than glossed: any `tests/**` change now runs this gate, so
a commit touching an unrelated test also executes the seam guards. Measured at this revision the
step is ~1.5 s (`124 passed in 1.48s`) plus ~4.1 s for the judge, so the added cost is a few
seconds on a job that already installs `requirements.txt`. A narrower filter was considered and
rejected: naming a subset of guards restores the exact drift being repaired.

## 10. Remaining uncertainty / authorization

* **Not claimed:** production parity, deployment identity, or acceptance. The CI run above is
  evidence that the *gate* executes its whole domain at this revision; it is not a deployment
  observation and does not establish that anything is running in production.
* Recurrence risk is structural: a hand-maintained inventory drifts again on the next
  economic-seam guard. The judge now makes that drift *fail CI* instead of passing silently,
  which is the bounded repair. Removing the class entirely requires the derived-inventory
  execution surface — a separate bounded workstream for sovereign review (§7).
* Human merge authority is required. No production action is requested or performed.
