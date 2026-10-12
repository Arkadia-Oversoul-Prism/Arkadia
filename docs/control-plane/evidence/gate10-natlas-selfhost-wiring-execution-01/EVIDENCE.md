# GATE-10 · N-ATLAS self-host wiring guard is executed, not only selected

Pass N. Measured at `main` `ee684fff` (merge #487), 2026-10-12.

## Defect

`tests/test_natlas_selfhost_ci_wiring.py` is the guard introduced in `c88b2eb2`
("AEAS-04: close the CI coverage gap for the n-atlas-server deployment unit"). It
asserts three facts about `.github/workflows/n-atlas-developer-lab.yml`:

1. some workflow runs `tests/test_natlas_selfhost_contract.py`;
2. that workflow's `pull_request` `paths` filter selects the contract file **and every
   tracked file under** `deploy/n-atlas-server`;
3. some job **builds and runs** the image (`docker run`, not only `docker build`).

The same commit added the guard to the workflow's `paths` filter:

```yaml
      - "tests/test_natlas_selfhost_ci_wiring.py"
```

— but added no step that runs it. A change to the guard **triggered** the gate; the gate
never **executed** the guard. The execute-to-selects invariant (proved in
`tests/test_gate_filter_selection.py`, whose own docstring names the class) was breached:
selecting a file is not executing it.

Measured over the live tracked corpus at `ee684fff`, scanning every `*_ci_wiring.py`:

| guard | selected by | executed by |
|---|---|---|
| `test_baseline_fingerprint_ci_wiring.py` | baseline-fingerprint | baseline-fingerprint |
| `test_baseline_preflight_ci_wiring.py` | baseline-preflight | baseline-preflight |
| `test_boot_syntax_ci_wiring.py` | boot-syntax | boot-syntax |
| `test_ci_gate_trigger_coverage_ci_wiring.py` | ci-gate-trigger-coverage | ci-gate-trigger-coverage |
| `test_ci_verdict_step_integrity_ci_wiring.py` | ci-verdict-step-integrity | ci-verdict-step-integrity |
| `test_economic_seam_ci_wiring.py` | economic-seam-engine | economic-seam-engine |
| `test_gitleaks_config_guard_ci_wiring.py` | gitleaks-config-guard | gitleaks-config-guard |
| **`test_natlas_selfhost_ci_wiring.py`** | **n-atlas-developer-lab** (+3 generic) | **none** |
| `test_prism_console_ci_wiring.py` | prism-console-contract | prism-console-contract |
| `test_solspire_route_composition_ci_wiring.py` | solspire-route-composition | solspire-route-composition |
| `test_static_ingestion_corpus_ci_wiring.py` | static-ingestion-corpus | static-ingestion-corpus |

Every other wiring guard both selects and executes itself. This is the sole breach, so the
defect is unowned: no open PR branch modifies `n-atlas-developer-lab.yml` or the guard
(`git ls-remote --heads origin` shows no natlas/wiring branch touching it).

## Repair (bounded, 2 files)

`.github/workflows/n-atlas-developer-lab.yml`:
- the backend job now runs the wiring guard:
  `- name: N-ATLAS self-host wiring boundary`
  `  run: python -m pytest tests/test_natlas_selfhost_ci_wiring.py -q`
- the dependency install names `pyyaml` explicitly. `requirements.txt` does **not** declare
  it, but the wiring guard parses `.github/workflows/*.yml` with it; without it the step
  would error at import and read as a filter defect rather than a guard failure.

`tests/test_natlas_selfhost_ci_wiring.py`:
- `_wiring_steps()` / `_executes_wiring_guard()` — execute-side detectors;
- `test_contract_workflow_executes_its_own_wiring_guard` (parametrized over every workflow
  that runs the contract) — a gate that *selects* the guard must *execute* it, and its
  wiring step must be able to fail the job;
- `test_executes_wiring_guard_detector_distinguishes_the_forms` — negative control: a
  `run:` block that does not `pytest`-run the guard is not an execution.

## Proof

| command | result |
|---|---|
| `pytest tests/test_natlas_selfhost_ci_wiring.py -q` (post-repair) | **12 passed** |
| same, with the execute step removed from the real workflow, paths untouched | **1 failed, 11 passed** (the new node) |
| restore byte-identically (`diff -q`) | clean; **12 passed** |
| `pytest tests/test_natlas_selfhost_contract.py -q` | 18 passed |
| `pytest tests/test_workflow_injection_boundary.py -q` | 46 passed |
| full suite, failing/error **node set** vs `main` | **identical** (202 nodes, `diff` empty) |
| CP10 boundary judge on all three changed paths | PASS |

Negative control is on the **real** workflow file, not a synthetic fixture: the detector is
proven to read the file it guards. No untrusted `github.event`/`inputs` interpolation is
added (`test_workflow_injection_boundary.py` is parametrized over every workflow).

## Uncertainty / not claimed

- `tests/test_natlas_developer_lab.py` cannot be collected in this sandbox
  (`ModuleNotFoundError: No module named 'pydantic'`); a local dependency gap, not related
  to this change and not attributable to it.
- The `selfhost-image` job requires Docker on the runner; this repair does not change that
  job, and its runtime behaviour is not re-observed here.
- No production configuration changed. Production acceptance remains **NOT CLAIMED**.
- Scope: the repair makes the gate execute the guard. Retiring the hand-maintained
  three-place pattern (paths x2 + step) in favour of a derived-domain runner is a separate,
  sovereign-reviewed workstream — discovery does not authorize execution.
