# api/main.py Line-Budget Restoration — EVIDENCE

Bounded workstream: `architecture/main-line-budget-restoration-01`
Base: `main` @ `4550531e1912e46d231a45f27ca801810def699d`
(`Research: define WorkEvent review, completion, and production acceptance (#290)`)
Branch head: see PR.
Classification: **VERIFIED** (repository evidence; no runtime/production claim).

## 1. Defect (measured, not inferred)

`api/main.py` exceeds its hard 2600-line architecture budget on pristine `main`.
`tests/architecture/test_layer_boundaries.py::test_api_main_line_count_within_budget`
therefore **fails on `main`**.

```
$ wc -l api/main.py
2805 api/main.py

$ python -m pytest tests/architecture/test_layer_boundaries.py -q
FAILED tests/architecture/test_layer_boundaries.py::test_api_main_line_count_within_budget
1 failed, 10 passed
```

The budget breach was introduced by the Arkana Signal Gate 01 ingestion boundary
(`71cbcb8`, 2719 lines) and widened by the multimodal signal response seam
(`1be5ce1`, 2805 lines).

## 2. Bounded change

A **pure move**: the two Arkana Signal route handlers were extracted verbatim from
`api/main.py` into a dedicated APIRouter module, `api/arkana_signal_routes.py`
(ARK-01 Gate 01 audio boundary), and mounted through the established
module-level `include_router` convention.

* `api/main.py`: `-221` / `+10` → **2594** lines (within the 2600 budget).
* `api/arkana_signal_routes.py`: new router module holding the moved handlers.
* No route path, request shape, response shape, or behaviour was changed.

## 3. Proof of purity

* **OpenAPI parity** — 300 paths, byte-identical before and after extraction;
  `POST /api/arkana/signal/ingest` and `POST /api/arkana/signal/respond` both present.
* **Byte-identical handlers** — `arkana_signal_ingest` and `arkana_signal_respond` are
  byte-for-byte equal to their originals in `main`.
* **Functional ASGI parity** — ingest empty → 400, ingest valid → 503 (no Gemini key
  configured, environmental), respond → 400, ingest malformed JSON → 400; the
  pre-extraction control returns the identical 400/503/400/400.
* **Compile** — `python -m py_compile api/main.py` passes (P1-A boot-code rule).

## 4. Architecture gate

```
$ python -m pytest tests/architecture/test_layer_boundaries.py -q
11 passed
```

Budget node flips from FAIL to PASS; the other 10 architecture fitness tests are
unchanged.

## 5. Full-suite regression measurement

Both trees measured in the same environment, `-rEf --continue-on-collection-errors`,
`PYTHONPATH=<tree>/archive/legacy_python`:

| tree | `api/main.py` | failed | passed | skipped | collection errors |
|---|---|---|---|---|---|
| `main` `4550531` | 2805 | 14 | 1418 | 20 | 1 |
| extraction | 2594 | 13 | 1419 | 20 | 1 |

Failure node sets compared by **identity**, not count:

```
main  nodes 15  4223d47da98edac434290bf2c6cf4448b0dbadb06257c9e04e837064b6965645
extr  nodes 14  bd958f91c278b22db6306c8f218b37bc52f53475ae10adfdd3bbf8d1a2570725
FIXED : ['FAILED tests/architecture/test_layer_boundaries.py::test_api_main_line_count_within_budget']
NEW   : []
```

Exactly one node repaired, zero nodes introduced. The remaining 13 failures and the
`tests/test_autonomy.py` collection error are **pre-existing `main` debt**, unrelated to
this change and explicitly out of scope (baseline debt is not fixed inside an unrelated
bounded task).

## 6. Mutation-boundary gate

```
$ printf 'api/arkana_signal_routes.py\napi/main.py\ndocs/.../EVIDENCE.md\n' \
    | python scripts/cp10_mutation_boundary_policy.py --judge
Mutation boundary PASS (M02A legitimate-surface + constitutional denylist)
```

## 7. Composition with the open PR queue (measured)

The open PR queue touches `api/main.py`, so the budget interacts with it. Measured on
this branch's tree:

| composed tree | `api/main.py` | budget gate |
|---|---|---|
| this extraction | 2594 | PASS |
| this extraction + `arch/arkana-signal-gate-02-runtime` (`2d0970a`) | 2683 | **FAIL** |

The #293 branch alone is **2894** lines (measured at live tip `2d0970a`; the earlier
`2719` figure quoted in the commit message is `main` @ `71cbcb8`, the Gate 01 commit, not
#293). The #293 diff applies cleanly onto this extraction, so the extraction does not
create a textual conflict — but it does **not** by itself restore the composed tree to
budget. A further ~83-line reduction, or a relaxation of the #293 change, is required.
This is recorded as a **dependent workstream**, not absorbed into this change (scope
discipline).

## 8. Separately reported defect (not repaired here)

`arch/arkana-signal-gate-02-runtime` @ `2d0970a` contains a **SyntaxError** in
`api/main.py`. A diff hunk pasted literal `\n` escapes instead of newlines, collapsing
four statements onto one physical line:

```
$ git show 2d0970a:api/main.py > /tmp/pr293_main_real.py
$ python -m py_compile /tmp/pr293_main_real.py
  File "/tmp/pr293_main_real.py", line 1584
    if signal:\n            reply = await _gemini_signal_chat(...)\n        else:\n ...
SyntaxError: unexpected character after line continuation character
```

This is the **P1-A boot-break class** (`api/main.py` failing to import at service
start). It is reported as its own workstream; repairing another branch's defect is not
part of this bounded task.

## 9. Remaining uncertainty

* No runtime or production observation is claimed. This is a repository-source result.
* The extraction reduces `api/main.py` but the 2600 budget remains a hard ceiling that
  the Arkana Signal workstream keeps pressing against; Phase 2 decomposition is the
  durable remedy, and it is a separate, larger workstream.

## 10. Full-suite fingerprint, environment-independent (measured 2026-10-05)

Measured with `PYTHONPATH=archive/legacy_python python -m pytest tests/ -q -rEf
--continue-on-collection-errors` on two trees in the same environment:

| tree | result | outcomes fingerprint | ids fingerprint |
|---|---|---|---|
| `main` @ `4550531` | 14F / 1418P / 20S / 1E (15 nodes) | `4b8a609c1f766afd9d60a349b8a835ea35d4c4df30a06a2d6ce9b173f79072d8` | `c6fc30ebe95babf78953219d42e4cda3b3740046d12913ba0cb0cf6a85fa9787` |
| this branch @ `ae0864b` | 13F / 1419P / 20S / 1E (14 nodes) | `14eed8eb11249a3f08cb24fabd9bb44f0a28b8cd83394bc09bf34abaa0135103` | `3d09dc8f855ceb7d852ea26eca8368e217120f4d17ea5e285d2907a334ccf9de` |

Node-set delta (`comm` over the sorted `FAILED`/`ERROR` node lists):

* **new** (branch-only): *(none)*
* **fixed** (main-only): `tests/architecture/test_layer_boundaries.py::test_api_main_line_count_within_budget`

Exactly one node repaired, zero introduced. This is the load-bearing claim — absolute
counts are environment-dependent (`AGENTS.md` → *Test-suite fingerprint is UNSTABLE on
main*); the failing/error **node set** is not.

The 13 remaining branch failures are pre-existing debt, byte-identical in node identity
to `main`: `test_agents_md_encoding_adjudication.py`, `test_engineering_lab_agent_loop.py`,
`test_m02a_ci_gate_integrity.py` (×3), `test_repository_snapshot.py`,
`test_solspire_r2_github_mutation.py`, `test_spiral_grove_activity_runtime.py`,
`test_spiral_grove_capability_chamber.py` (×2), `test_spiral_grove_draft_persistence.py`,
`test_steward_filter.py` (×2), plus the `test_autonomy` collection error.

