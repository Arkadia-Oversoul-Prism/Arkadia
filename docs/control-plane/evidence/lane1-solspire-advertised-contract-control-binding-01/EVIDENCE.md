# Lane 1 — bind the SolSpire advertised-contract control to its detector

**Base `main`:** `034d8879d68ecf8ed4c291eb0ab07432657a06a1` (2026-11-22)
**Lane:** 1 (shell / navigation / integration seam) — `SHARED-CONTRACTS.md` §1
**Defect class:** vacuous negative control — a `test_negative_control_*` node that restates its
detector inline and never calls it, so the invariant it claims to protect has no live owner.

## 1. Defect, measured

`tests/test_prism_solspire_control_plane.py::test_page_mounts_the_control_plane_and_advertises_only_served_paths`
enforced "every advertised `contract` is a served `/solspire` path" **inline**:

```python
for value in advertised:
    assert not value.startswith("/api/solspire/"), ...
    assert value.startswith("/solspire/"), ...
```

`test_negative_control_detects_the_wrong_advertised_prefix` claimed to prove that assertion could
fail, but it never called it. It re-implemented the predicate against a synthetic string:

```python
synthetic = '<NotYetWired contract="/api/solspire/pulses" />'
assert any(w in synthetic for w in WRONG_ADVERTISED)
assert "/api/solspire/pulses" not in PAGE
```

Pre-repair proof (real file at `034d8879`, live loop body replaced by `pass`):

```
$ python -m pytest tests/test_prism_solspire_control_plane.py -q -rEf
12 passed
```

The advertised-contract invariant was removed and **every node stayed green**, including the
control that exists to prove it can fail. `--collect-only` at `034d8879` is **12**.

## 2. Repair

The invariant moves onto a module-level detector that both the live assertion and its control call:

```python
_CONTRACT_ROUTE = re.compile(r'contract=(?:"([^"]+)"|\{\s*"([^"]+)"\s*\})')

def _advertised_contracts(text) -> list[str]:
    """Every route literal the page advertises through a `contract` prop."""

def _advertised_contract_defects(text) -> list[str]:
    """Why an advertised contract is not a served `/solspire` route."""
```

`_advertised_contract_defects` returns **reasons**, not a boolean, so "no defects" is
distinguishable from "nothing was read", and a control can assert the specific defect.

The detector also reads a route literal in an expression prop (`contract={"/api/solspire/voice"}`),
which the old `contract="([^"]+)"` regex silently skipped. It deliberately does **not** read
`contract={UNKNOWN_CONTRACT}`: `SolSpirePage.tsx:44` defines that constant as `"UNKNOWN"`, a
classification of an unknown lens, not an advertised route. Comments are stripped through the
file's existing `_code_only`, so a commented-out contract is not a defect either.

Node count unchanged: **12** before and after.

## 3. Post-repair proof (the discriminating controls)

Each mutation applied to the shipped file, module re-run, file restored byte-identically
(`p.read_text() == original` verified) between runs:

| Mutation | Result |
|---|---|
| `_advertised_contract_defects` body -> `return []` | **1 failed, 11 passed** — `test_negative_control_detects_the_wrong_advertised_prefix` |
| `_advertised_contract_defects` body -> `return ["forced"]` | **2 failed, 10 passed** — the live node and the control |
| expression branch dropped from `_CONTRACT_ROUTE` | **1 failed, 11 passed** — the control |

Both polarities are covered: a dead detector reddens the control (silent-pass direction), and an
over-eager detector reddens the live node as well (false-alarm direction). Dropping the expression
branch reddens only the control, which is correct — the live page carries no expression-form route
literal today, so the control is the only node that can observe that branch.

## 4. Verification

| Command | Result |
|---|---|
| `pytest tests/test_prism_solspire_control_plane.py -q -rEf` | **12 passed** (`--collect-only` 12) |
| `pytest tests/test_lane_instruction_doc_currency.py tests/test_lane_currency_ci_wiring.py tests/test_lane_aggregate_pr_classification.py -q` | **93 passed** |
| `python scripts/lane_state.py --check` | exit **0** |
| `python scripts/lane_state.py --check --verify-live` | exit **0** |
| `pytest tests/architecture -q` | **11 passed** |
| `pytest $(python scripts/console_contract_domain.py) -q -rEf` | **10 failed, 1271 passed, 4 skipped** |

### Baseline comparison (node identity, not counts)

The same domain was run in a detached worktree at `origin/main` (`034d8879`) in this environment:

| Tree | Result |
|---|---|
| `main` `034d8879` | 10 failed, 1271 passed, 4 skipped |
| branch head | 10 failed, 1271 passed, 4 skipped |

The sorted `FAILED`/`ERROR` node lists are **identical** (`diff` empty, 10 nodes each). All ten are
`tests/test_mission_lifecycle_adapter_contract.py`, which requires
`web/arkadia_console/node_modules/typescript/lib/typescript.js`; `node_modules` is not installed in
this sandbox. This is the documented environment-limited baseline, identical on both trees, and it
is **not** attributable to this change.

Two environment gaps were closed to reach that baseline rather than recorded as failures:
`python-multipart` (module collection), `PyJWT` (28 nodes importing `api.executive_routes` through
the app). Before installing them the domain read 38 failed on **both** trees, with identical node
sets.

## 5. Lane bookkeeping

`tests/test_prism_solspire_control_plane.py` is a shared endpoint-registry contract test (§1
"shared shell/endpoint contract tests"), and `scripts/lane_state_refresh.py::LANE_OWNERSHIP`
assigned it to no lane, so this PR derived as **unassigned**. One path is added to lane 1's entry,
which is the ownership the lane already holds over `lib/endpoints.ts` / `lib/types.ts` and over the
contract tests that pin them. `test_every_declared_lane_test_path_is_assigned_to_its_lane` derives
the coverage from the map, so the added path is judged by the same rule as the existing ones.

`AGENT-01-SHELL.md` is **not** edited and `lane-state.json` is **not** re-derived. The committed
snapshot records every lane idle, which is the post-merge state; re-deriving it now would write a
snapshot that reddens `lane-doc-currency` on `main` the moment this PR merges, and would require
editing a guarded lane doc in the same change. Currency refresh stays a separate action against the
post-merge state.

## 6. Boundaries

Test-side plus one lane-ownership entry plus this record. No application source, no authority
surface, no identity or governance file, no deployment configuration. `api/main.py` untouched.

Merge execution, production deployment and acceptance remain human-only under GOV-03. This PR is a
draft: it is evidence for human review, not a merge request.
