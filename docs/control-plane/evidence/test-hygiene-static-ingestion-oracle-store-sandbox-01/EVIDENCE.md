# Test-hygiene — the K5 round-trip test must own its oracle store — Evidence

**Gate / workstream:** test-hygiene (order-dependent suite node).
**Authorization:** human sovereign retains review, merge and acceptance. No merge,
deployment or production claim is made here.
**BASE_MAIN:** `bb19aabda34d59594615b0279a45e9cbd3d8204d` — "test(lane1): bind the lens-strip
owner detector to a control (#678)".
**Branch:** `test-hygiene/static-ingestion-oracle-store-sandbox-01`
**Changed paths:** `tests/test_static_ingestion_idempotency.py`,
`docs/control-plane/evidence/test-hygiene-static-ingestion-oracle-store-sandbox-01/EVIDENCE.md`.
No product code, workflow, governance record or deployment configuration is touched.

## 1. The defect (reproduced, not inferred)

`tests/test_static_ingestion_idempotency.py::test_open_loop_content_is_checksum_stable_through_a_vault_round_trip`
is order-dependent. It **passes in isolation and fails in the full suite**, so it reddens
every full-suite baseline for a reason unrelated to the invariant it guards.

Failure in a full run at `bb19aabd`:

```
>       loops = static_ingestion._oracle_open_loop_rows()
>       assert loops, "oracle store has no open-loop records to verify"
E       AssertionError: oracle store has no open-loop records to verify
E       assert []
```

Deterministic two-module reproduction (no other tests involved):

| Session | Result |
|---|---|
| `pytest tests/test_static_ingestion_idempotency.py` | `2 passed` |
| `pytest tests/test_ao006_canvas_contract.py tests/test_static_ingestion_idempotency.py` | **`1 failed, 17 passed`** |

## 2. Mechanism (proven, not assumed)

`knowledge/static_ingestion.py` snapshots the oracle path from the environment at
**import** time:

```python
_ORACLE_STORE_PATH = Path(os.environ.get("SOLSPIRE_DATA_DIR", str(_REPO_ROOT / "data"))) / "oracle_store.json"
```

`tests/test_ao006_canvas_contract.py` mutates the process-global environment at **module
import** and never restores it:

```python
os.environ.setdefault("SOLSPIRE_DATA_DIR", _STATE)   # _STATE is a per-process tempdir
```

The comment above that block explains why the redirect must precede the store imports; the
consequence for *later* modules is that it is never undone. Measured directly by importing
`test_ao006_canvas_contract` first and then resolving the constant:

```
after ao006: SOLSPIRE_DATA_DIR = /tmp/ao006_canvas__pzo72wj
oracle path = /tmp/ao006_canvas__pzo72wj/oracle_store.json
exists = False
rows = 0
```

So the K5 test reads a file that does not exist, `_oracle_open_loop_rows()` returns `[]`,
and the node fails. The repository's real store (`data/oracle_store.json`, tracked, two
open-loop rows) is never consulted. The K5 module's own docstring claims it is isolated to a
private tempdir; the fixture isolated the knowledge DB and the vault but **not** the oracle
store, so the claim was incomplete.

## 3. Repair

The fixture now owns the oracle path instead of inheriting ambient state: it writes a
deterministic two-row store inside the same sandbox and monkeypatches
`static_ingestion._ORACLE_STORE_PATH` to it. The rows deliberately carry trailing newlines
and padding so `_normalize_body` is exercised rather than bypassed.

This is the file's established pattern — the fixture already monkeypatches `_DB_PATH`,
`VAULT_ROOT` and the package re-exports — extended to the one path it had missed. It is
input data, not a substitute for the code under test: `create_note`, `_normalize_body`,
`_strip_frontmatter` and the checksum comparison all still run for real.

A second test, `test_the_oracle_store_is_sandboxed`, asserts the property rather than
assuming it: the resolved path must sit inside the fixture's sandbox, exist, and yield rows.

## 4. Negative control (the guard is not vacuous)

Removing only the `monkeypatch.setattr(static_ingestion, "_ORACLE_STORE_PATH", oracle_store)`
line from the live file, then re-running the reproduction:

```
FAILED tests/test_static_ingestion_idempotency.py::test_the_oracle_store_is_sandboxed
FAILED tests/test_static_ingestion_idempotency.py::test_open_loop_content_is_checksum_stable_through_a_vault_round_trip
2 failed, 17 passed
```

Restored byte-identically (`diff -q` clean) → `19 passed`. Both the new guard and the
round-trip node redden without the repair, so the guard measures the defect it names.

## 5. Full-suite measurement (attribute by node identity, never by count)

Same interpreter, same installed dependency set, same clone, both trees measured in this
pass. Convention: `python -m pytest tests/ -q -rEf --continue-on-collection-errors`
(the `-rEf` form is required — `-rf` alone suppresses `ERROR` summary lines and yields a
subset).

| Tree | Outcome | Failing/error nodes | Node-set sha256 |
|---|---|---|---|
| `main` `bb19aabd` | `19 failed, 4250 passed, 22 skipped, 1 error` | **20** | `d6101722f624c0eedb48a957375f0b8abbef398f20e93e55e889dd8d9e0893ce` |
| branch | `18 failed, 4252 passed, 22 skipped, 1 error` | **19** | `be2d0b55481d23f1d44a8e61b36896965046d05b6673a8869b247378aa44faa1` |

`comm -3` on the sorted node lists yields exactly one line, the repaired node, on the
`main` side only:

```
tests/test_static_ingestion_idempotency.py::test_open_loop_content_is_checksum_stable_through_a_vault_round_trip
```

So the delta is `-1` repaired / `+0` introduced. The `+2 passed` is the repaired node plus
the new isolation guard. Architecture suite: **11 passed**.

## 6. Boundaries and residual facts

- **Not repaired here, and deliberately so:**
  - `tests/test_ao006_canvas_contract.py` still mutates `SOLSPIRE_DATA_DIR` process-wide at
    import. That is the contaminator, and any *other* module that snapshots a path from
    `SOLSPIRE_DATA_DIR` at import is still exposed to it. Retiring that shape needs a
    conftest-level rebind for every such constant, which is a wider change than this
    node's defect; it is recorded as the next bounded slice rather than folded in.
  - `data/oracle_store.json` being tracked and non-empty is no longer a precondition of this
    test, which is the point of the repair: the invariant is checksum stability, not the
    contents of a repository data file.
- **Owned elsewhere, not touched:** the remaining `main` debt nodes are carried by open PRs
  (`tests/test_m01_persistence.py` and `tests/test_m05_files.py` by #690; the two
  `test_solspire_r1_governance_convergence.py` nodes by #693; the
  `test_solspire_r3_execution_runtime.py` node by #691), are sovereign-gated
  (`tests/test_autonomy.py` CE-01; the `test_ais_w2_living_gate_grove_handoff.py` F-01
  proxy-invalidation), are environment-dependent in this sandbox
  (`tests/test_mission_lifecycle_adapter_contract.py` needs `web/arkadia_console/node_modules`
  for its TypeScript compiler), or are recorded debt
  (`tests/test_identity_spine_w1.py`, `tests/test_m02_reasomate_truth.py`).
- **Observed, owned by #688, not staged:** a full-suite run materialises
  `data/engineering_lab/agent_events.jsonl`. That residue is the Engineering Lab event-log
  leak #688 sandboxes and gitignores. It is left untracked here.
- **Production observation (read-only, this pass).** `GET https://arkadia-qzu4.onrender.com/api/version`
  → `source_revision = bb19aabda34d59594615b0279a45e9cbd3d8204d`, `revision_source =
  RENDER_GIT_COMMIT`, `revision_conflict = false`, i.e. source↔runtime consistency at the
  measured `main`. This is a revision-identity observation only; it is **not** application
  acceptance, and no deployment was performed.
- **Composition measurement (informational).** Pairwise `git merge-tree` over all 20 open PR
  heads judges 190 pairs: 189 `CLEAN`, one `CONFLICT` (`#681 × #687` on
  `tests/test_gate2_production_observation.py`, in both orders, append-only at EOF; the
  hand-resolved composition runs `64 passed` on the two Gate-2 test files). Recorded for the
  human merge order; nothing here depends on it.

## 7. Merge

Not performed. GOV-03: all merge execution is human-only. This change is a draft candidate
for human review.
