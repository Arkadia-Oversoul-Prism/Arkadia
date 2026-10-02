# GATE-HYGIENE · baseline fingerprint reconciliation 01

**Status:** IMPLEMENTED — sovereign review required
**Date:** 2026-10-02
**Base main:** `2b167e4f41ca87699db33a28c76f03550db66847`
**Branch:** `gate-hygiene/baseline-fingerprint-reconciliation-01`
**Gate:** GATE-01 / GATE-04 (canonical evidence + provenance) · `gate-hygiene`
**Prior workstream:** `gate-hygiene/baseline-fingerprint-reproducibility-01` (PR #203)

## 1. Objective

Repair the repository's published baseline test-debt fingerprint so it is reproducible
from the derivation printed beside it, and install a guard that prevents the
non-reproducible value from being republished.

## 2. Evidence-backed defect

PR #203 (`gate-hygiene/baseline-fingerprint-reproducibility-01`, merged `964c103`) set out
to make the baseline fingerprint reproducible and merged `scripts/baseline_fingerprint.py`.
The pair it published is **not reproducible by that script, or by any other derivation**:

| Where | Value published |
|---|---|
| `.bootstrap/01_STATE.md` | outcomes `a59453b8…`, node set `9a35c812…` |
| `MISSION.md` | `a59453b8…` |
| `NEXT_AGENT.md` | `a59453b8…` |
| `docs/phase1/CONTINUATION_LEDGER.md` | `a59453b8…` |
| PR #203 `WORKSTREAM_STATE.md` | `a59453b8…` (outcomes), `9a35c812…` (node set) |

Measured against the live tool and the recorded node set:

```
$ python scripts/baseline_fingerprint.py tests/fixtures/baseline_node_set.txt
  failing/error nodes : 20 (19 failed, 1 error)
  outcomes fingerprint: a578a766c09c949c620c9d324248659812d215d3d1e875a0c25b42adb8912aa1
  ids fingerprint     : 8036fc0692eb0358f037adb2cf9e2b234db1f41a4586ca0162f4e52350cfa713
```

The tool is **unchanged since #203** — `git diff 6dbdde5:scripts/baseline_fingerprint.py
HEAD:scripts/baseline_fingerprint.py` is empty, and `git log -- scripts/baseline_fingerprint.py`
shows only `6dbdde5`. Running **#203's own tool on #203's own base revision** (`702b63ae`)
prints `4d84e7eb…` / `da2ec262…`, not the values #203 documented. The published pair is
therefore unreproducible by the artifact merged to make it reproducible.

A sweep of candidate derivations (reason-included, unsorted, without trailing newline,
node-id-only variants) produced **no** hit on either published value.

### 2.1 The first reconciliation's value was reproducible — but only by clone depth

The first reconciliation pass published `4d84e7eb…` / `da2ec262…` for a recorded set of
**21** nodes. That pair is genuinely derivable — but only in a clone that carries the
PR-head revision `7d79f38…` pinned by `tests/test_agents_md_encoding_adjudication.py`
(`GATE2_PARENT_REV`). The recorded set held
`tests/test_agents_md_encoding_adjudication.py::test_gate2_parent_agents_md_repair_is_byte_identical_to_the_pipeline`,
which **skips** when that revision is absent, so:

| Clone | Node outcome | Recorded set |
|---|---|---|
| carries `7d79f38…` (interactive checkout, PR ref fetched) | FAILED | 21 nodes → `4d84e7eb…` / `da2ec262…` |
| does not carry it (CI checkout, `actions/checkout` without PR refs) | SKIPPED | 20 nodes → `a578a766…` / `8036fc06…` |

The value therefore encoded **clone depth**, not the repository's test debt — the same
defect class this workstream exists to remove, one layer down. CI is the authority for a
gate-hygiene fingerprint, so the recorded set must be depth-stable. The node is now
**excluded** from `tests/fixtures/baseline_node_set.txt` (20 nodes: 19 failed, 1 error),
and `test_recorded_set_excludes_the_clone_depth_dependent_node` fails if it re-enters.
The node itself is not deleted or weakened — it still runs, and its outcome is simply not
part of the recorded debt set.

## 3. Bounded change

| File | Change |
|---|---|
| `tests/fixtures/baseline_node_set.txt` | new — the recorded **20**-node baseline set (clone-depth-stable) |
| `tests/test_baseline_fingerprint.py` | +5 tests (1 fixture-driven, 1 clone-depth guard, 1 negative control, 2 doc-agreement cases) |
| `.bootstrap/01_STATE.md` | republish canonical pair + correction note |
| `MISSION.md` | republish canonical value |
| `NEXT_AGENT.md` | republish canonical value |
| `docs/phase1/CONTINUATION_LEDGER.md` | republish canonical value + correction note |
| this evidence dir | record the clone-depth root cause |

No production code, no boot code, no workflow, no architecture surface, no authority path.

### Why the existing tests did not catch it

`tests/test_baseline_fingerprint.py` pinned the derivation with a **synthetic known-answer
fixture** only. It never fed the repository's *published* value back through the derivation,
so an internally inconsistent published value could not fail. The new tests close that gap:

- `test_live_node_set_reproduces_the_canonical_fingerprint` — the recorded node set must
  hash to the canonical pair.
- `test_recorded_set_excludes_the_clone_depth_dependent_node` — the recorded set must not
  contain a node whose outcome depends on whether the clone carries `7d79f38…`.
- `test_superseded_fingerprints_are_not_reproducible` — **negative control**: the superseded
  values must *not* reproduce, so doc agreement cannot be satisfied by accident.
- `test_published_docs_carry_the_canonical_fingerprint[doc]` — every document that publishes
  a fingerprint must carry the canonical value and must not carry a superseded one.

## 4. Verification

| Check | Result |
|---|---|
| `tests/test_baseline_fingerprint.py` before doc fix | **4 failed, 12 passed** — detects the defect (failing-first) |
| `tests/test_baseline_fingerprint.py` after doc fix | **17 passed** |
| `python scripts/baseline_fingerprint.py tests/fixtures/baseline_node_set.txt` | `a578a766…` / `8036fc06…` (20 nodes) |
| CP10 mutation-boundary judge on changed paths | PASS (exit 0) |
| `pytest tests/architecture -q` | 11 passed |
| `python -m py_compile api/main.py` | PASS (boot code untouched) |

Fingerprint delta: **none**, once the depth-dependent node is excluded. The 20 stable
failing/error nodes are identical with the pinned PR-head revision present and absent; the
only node that moved between the two clones is the depth-dependent node now excluded from
the recorded set.

## 5. Remaining uncertainty

- The origin of `a59453b8…` / `9a35c812…` is **UNKNOWN** — no tested convention reproduces
  them. This is recorded as unexplained rather than reconstructed.
- The depth-dependent node is excluded, not repaired. Its own assertion defect (it demands a
  byte-identical repair against a revision absent from a plain clone) is a **separate**
  bounded workstream; this pass neither fixes it nor hides it.
- Passed-count variation between runs of the same tree is the documented order-dependence of
  `tests/test_engineering_lab_agent_loop.py::test_agent_loop_does_not_mutate_repository`
  (see `AGENTS.md`), not a node-set change.

## 6. Authorization required

Sovereign review and merge. No further action taken in this pass.
