# EVIDENCE — bind the document-title writer sweep to its detector (lane 1)

**Pass:** `lane1/title-writer-detector-binding-01`
**Base main:** `f9bd8da913fa194d7cff2e53b9c417ddb2a9f43a` (verified live `origin/main`)
**Disposition:** bounded lane-1 test-side binding repair. No source, route, registry, backend,
authority, or governance surface touched.

---

## 1. Defect — the live assertion's detector is not bound to anything a control can call

`tests/test_console_document_title_contract.py::test_the_shell_is_the_only_module_that_writes_the_document_title`
asserts `_title_writers() == ["web/arkadia_console/src/components/Shell.tsx"]`. `_title_writers`
reads the **live tree itself** (`SRC.rglob("*.ts*")`), so it shares no symbol with any control, and
the file holds no control for it at all. Its two controls (`_title_effect`) guard a *different*
detector.

**Measured vacuity at base `f9bd8da9`.** Neutering `_title_writers` to return the expected literal
left the whole file green:

```
$ python -m pytest tests/test_console_document_title_contract.py -q
6 passed
```

The detector could be replaced by its own expected answer with nothing reddening. The guard is the
single-owner rule for `document.title` (WCAG 2.4.2 announcement metadata), so a second module
writing the title would go unreported.

## 2. Repair — move the predicate behind a source-taking helper, and bind a control to it

```python
TITLE_WRITE_MARKER = "document.title"
SHELL_RELATIVE_PATH = "web/arkadia_console/src/components/Shell.tsx"

def _title_writers_in(sources: dict[str, str]) -> list[str]:
    return sorted(p for p, text in sources.items() if TITLE_WRITE_MARKER in text)

def _live_tsx_sources() -> dict[str, str]: ...
def _title_writers() -> list[str]:
    return _title_writers_in(_live_tsx_sources())
```

The live assertion and the new control both call `_title_writers_in`, so an edit to the predicate
is reachable by the control. The literal is hoisted so the assertion and the control cannot drift.

Node count **6 → 7** (+1, exactly the new control). `--collect-only` measured, not inferred from
the delta.

## 3. Proof — a discriminating A/B on the shared helper

Text-scoped mutation of the shared helper body, both polarities, on the real file:

| Mutation of `_title_writers_in` | Result |
|---|---|
| `return []` (always-clean) | **2 failed, 5 passed** — live assertion + bound control |
| `return ["always-dirty"]` (always-dirty) | **2 failed, 5 passed** — live assertion + bound control |
| restored byte-identically (`md5 30e9414a…`) | **7 passed** |

The control fails in *both* polarities, so it is not satisfied by a detector that reports
unconditionally, and the live assertion is no longer satisfied by a detector that reports nothing.

## 4. Checks

| Check | Result |
|---|---|
| `tests/test_console_document_title_contract.py` | 7 passed (was 6) |
| lane-1 console domain (shell / endpoint registry / legacy route / document title / error boundary) | 111 passed |
| `tests/test_prism_console_ci_wiring.py` + `tests/architecture` | 45 passed (architecture 11/11) |
| CP10 boundary judge on the touched path | exit 0 |

The file is executed by the derived console-contract domain
(`scripts/console_contract_domain.py` lists it), so **no new wiring is needed**.

## 5. Attribution — node identity, not counts

Baseline measured on `main` `f9bd8da9` in this environment:
`20 failed, 4034 passed, 18 skipped, 1 error`; sorted FAILED/ERROR node set = **21** nodes,
`sha256 5cb9dc5d9fbf6a8ac2bf176ea712034c1525be920080afa60ac35d91a7e3168c`.

`tests/test_lane_instruction_doc_currency.py::test_live_snapshot_is_fresh_against_current_main`
is in that baseline set — the `lane-doc-currency` red on `main` that PR #663 repairs. It is
pre-existing debt, not branch-caused.

## 6. Boundaries

- Lane-1 owned path only (`tests/…console…` contract test; lane 1 owns the shared shell tests).
- No `web/arkadia_console/src/**` change; no route, surface registry, endpoint, or type change.
- No authority, identity, K15/K3, approval-enforcement, or deployment surface touched.
- Merge, production deployment, and acceptance remain human-only (GOV-03).
