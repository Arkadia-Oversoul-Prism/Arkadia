# Lane 4 — N-ATLAS self-host route control integrity

**Pass:** 2026-11-08 (hourly bounded execution, reconciliation edition)
**Lane:** 4 — Arkana + Weaver + Engineering Lab
**Branch:** `lane4/natlas-route-control-integrity-01`
**Base `main`:** `a2a0a0858c147fb1948a85a4173ca9b8abb676df` (PR #646 merge)
**Scope:** one test file. No console source, backend contract, registry, authority surface, or
other lane's file is touched.

## 0. Reconciliation state at the start of this pass

Measured live at `2026-11-08T17:0xZ`: `gh api repos/Arkadia-Oversoul-Prism/Arkadia/pulls?state=open`
-> **0** open PRs repo-wide (confirmed by both `gh pr list --state open` and the REST endpoint).
The derived snapshot (`docs/control-plane/parallel-ui/lane-state.json`, `observed_at`
`2026-11-08T15:20:23Z`) reports all four lanes `doc_guard: idle`, `open_prs: []`, and
`unassigned_open_prs: []`. `scripts/lane_state.py --check` and `--check --verify-live` both exit
**0**. Reconciliation is exhausted, so this pass opens the next bounded lane PR under
`11 — LANE NEW-PR AUTHORIZATION` (N1 satisfied).

The contract's credential rule applied as written: `gh auth status` began "not logged into any
GitHub hosts", and the documented recovery
`export GH_TOKEN="${GITHUB_PERSONAL_ACCESS_TOKEN}"` restored the session (`gh api user` ->
`Arkadia-Oversoul-Prism`). The ambient `GITHUB_TOKEN` is the stale path, not a blocker.

## 1. Defect — a control that restates its input instead of calling the detector

`tests/test_natlas_selfhost_contract.py` holds **two** negative controls for the same detector.
`_missing_contract_routes(src)` returns the required OpenAI routes absent from a gateway source:

```python
HISTORICAL_ROUTES = (
    "@app.post('/v1/chat/completions')",
    "@app.get('/v1/models')",
    "@app.get('/health')",
)

def _missing_contract_routes(src: str) -> set[str]:
    return {route for route in HISTORICAL_ROUTES if route not in src}
```

The live assertion calls it and asserts the result is empty:

```python
# test_historical_gateway_declares_the_openai_compatible_contract
missing = _missing_contract_routes(_source(APP))
assert not missing, f"historical gateway is missing required routes: {sorted(missing)}"
```

The **first** control (`test_negative_control_detector_reports_a_missing_route`, line 63) is
correctly bound — it calls `_missing_contract_routes(stripped)` and asserts the returned set. The
**second** control (`test_negative_control_detector_flags_a_missing_route`, line 188) is not:

```python
# pre-repair
def test_negative_control_detector_flags_a_missing_route():
    """The route detector must actually detect absence, not just presence."""
    src = "@app.get('/health')\ndef health(): ..."
    assert "@app.post('/v1/chat/completions')" not in src
```

It asserts only that its own hand-written string lacks the literal. It never calls
`_missing_contract_routes`, so it cannot fail for any edit to that detector — and the live
assertion `assert not missing` is *satisfied* by a detector neutered to `return set()`. The
detector could therefore be disarmed with no red test anywhere in the file, which is the same
defect class #631/#634/#636/#637 (Lane 1), #635/#640 (Lane 2), #638 (Lane 3) and
#639/#641/#642/#643/#645/#646 (Lane 4) repaired.

This control is one of the four the previous Lane 4 pass recorded in §9 of
`lane4-run-trace-vocabulary-control-integrity-01/EVIDENCE.md` as *candidates* — "a
non-intersecting call set is a *candidate* signal, not proof of vacuity". This pass supplies the
measurement and the classification.

## 2. Measurement — the control is vacuous (AST-scoped A/B)

Neutering the shared detector's own body (`return set()`, patched by its `ast` span) and running
the three nodes separately:

| tree | live node | bound control (l. 63) | flagged control (l. 188) |
|---|---|---|---|
| pre-repair | pass | pass | **pass** (vacuity: nothing reddens) |
| pre-repair, detector neutered | pass | **FAIL** | **pass** (still nothing reddens) |

The pre-repair control stayed green under a detector that reports nothing, so it proved nothing
about the code it names. The file was restored byte-identically after the mutation (asserted in
the harness).

## 3. Repair

The control now calls the same detector the live assertion uses, and asserts **both** polarities
so a detector that reports unconditionally cannot pass either:

```python
def test_negative_control_detector_flags_a_missing_route():
    stripped = "@app.get('/health')\ndef health(): ..."
    missing = _missing_contract_routes(stripped)
    assert missing, "a source without the required routes must be reported"
    assert "@app.post('/v1/chat/completions')" in missing
    # ...and a source carrying every route must not be reported.
    assert _missing_contract_routes(_source(APP)) == set()
```

Node count is unchanged at **18** (`--collect-only` -> 18, before and after) — this binds a
control, it adds none.

## 4. Verification

| check | command | result |
|---|---|---|
| targeted | `python -m pytest tests/test_natlas_selfhost_contract.py -q -rEf` | **18 passed** |
| post-repair A/B (detector neutered) | live / flagged control / bound control | pass / **FAIL** / **FAIL** |
| wiring guard | `python -m pytest tests/test_natlas_selfhost_ci_wiring.py -q` | **12 passed** |
| architecture | `python -m pytest tests/architecture -q` | **11 passed** |
| lane guards | `python -m pytest tests/test_lane_instruction_doc_currency.py tests/test_lane_currency_ci_wiring.py -q` | **67 passed** |
| lane currency | `python scripts/lane_state.py --check` / `--check --verify-live` | exit **0** both |
| CP10 boundary | `printf 'tests/test_natlas_selfhost_contract.py\n' \| python scripts/cp10_mutation_boundary_policy.py --judge` | **PASS** |
| full suite (once) | `python -m pytest tests/ -q -rEf --continue-on-collection-errors` | `21 failed, 3995 passed, 18 skipped, 1 error` |

The full-suite counts are **identical** to the baseline the previous Lane 4 pass recorded at
`f608ecd2` (`21 failed, 3995 passed, 18 skipped, 1 error`), and the target file contributes
**zero** nodes to the failing/error set (22 nodes: 21 `FAILED` + 1 `ERROR`; node-set sha256
`af4ad19a53dbe0edc5dfe577bce8ebdfc147fdfd888cb394dfb027b56232b741`). Per the contract, the change
is attributed by the failing/error node **set** and by `--collect-only` node count, not by a
second full run. The 9 `test_mission_lifecycle_adapter_contract.py` failures are the documented
missing-`node_modules` TypeScript-toolchain baseline.

The file is executed by the whole-suite surfaces (`economic-seam-engine.yml` selects `tests/**`;
`provider-routing.yml` runs the full suite and is dispatchable), so no new wiring is required.

## 5. Governance

No authority, identity, K15/K3 governance, approval enforcement, constitutional architecture,
deployment configuration, or console source is altered. The change is confined to one test file
inside Lane 4's Engineering-Lab-owned surface (`lab/engineering_lab/natlas.py` is the contract
under test). Merge, production deployment and acceptance remain human-only.

## 6. Next action

Lane 4's next bounded PR opens only after this one merges. Remaining recorded candidates from the
prior pass that this pass did **not** repair (one bounded slice per lane PR) still require their
own measurement before classification:

- `tests/test_attention_truthfulness.py::test_negative_control_status_only_rule_would_miss_the_defect`
- `tests/test_prism_solspire_control_plane.py::test_negative_control_detects_the_wrong_advertised_prefix`
- `tests/test_console_facts_value_overflow_contract.py` controls (measured **bound** this pass —
  each calls `_unwrappable_value_column_defects`, so they are not vacuous)
