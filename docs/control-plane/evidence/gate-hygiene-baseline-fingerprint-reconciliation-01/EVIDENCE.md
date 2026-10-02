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
  failing/error nodes : 21 (20 failed, 1 error)
  outcomes fingerprint: 4d84e7eb2524d4a5a952405f6df8017398ce21cca44aec6d04fbb523d577c6a7
  ids fingerprint     : da2ec2620d09988e75702b6444ee8ee6ba5ded8bc067aac6c4e149245c27de71
```

The tool is **unchanged since #203** — `git diff 6dbdde5:scripts/baseline_fingerprint.py
HEAD:scripts/baseline_fingerprint.py` is empty, and `git log -- scripts/baseline_fingerprint.py`
shows only `6dbdde5`. Running **#203's own tool on #203's own base revision** (`702b63ae`)
also prints `4d84e7eb…` / `da2ec262…`, not the values #203 documented. The published pair is
therefore unreproducible by the artifact merged to make it reproducible.

A sweep of candidate derivations (reason-included, unsorted, without trailing newline,
node-id-only variants) produced **no** hit on either published value.

## 3. Bounded change

| File | Change |
|---|---|
| `tests/fixtures/baseline_node_set.txt` | new — the recorded 21-node baseline set |
| `tests/test_baseline_fingerprint.py` | +4 tests (1 fixture-driven, 1 negative control, 2 doc-agreement cases) |
| `.bootstrap/01_STATE.md` | republish canonical pair + correction note |
| `MISSION.md` | republish canonical value |
| `NEXT_AGENT.md` | republish canonical value |
| `docs/phase1/CONTINUATION_LEDGER.md` | republish canonical value + correction note |

No production code, no boot code, no workflow, no architecture surface, no authority path.

### Why the existing tests did not catch it

`tests/test_baseline_fingerprint.py` pinned the derivation with a **synthetic known-answer
fixture** only. It never fed the repository's *published* value back through the derivation,
so an internally inconsistent published value could not fail. The new tests close that gap:

- `test_live_node_set_reproduces_the_canonical_fingerprint` — the recorded node set must
  hash to the canonical pair.
- `test_superseded_fingerprints_are_not_reproducible` — **negative control**: the superseded
  values must *not* reproduce, so doc agreement cannot be satisfied by accident.
- `test_published_docs_carry_the_canonical_fingerprint[doc]` — every document that publishes
  a fingerprint must carry the canonical value and must not carry the superseded one.

## 4. Verification

| Check | Result |
|---|---|
| `tests/test_baseline_fingerprint.py` before doc fix | **4 failed, 12 passed** — detects the defect (failing-first) |
| `tests/test_baseline_fingerprint.py` after doc fix | **16 passed** |
| `python scripts/baseline_fingerprint.py tests/fixtures/baseline_node_set.txt` | `4d84e7eb…` / `da2ec262…` |
| CP10 mutation-boundary judge on changed paths | PASS (exit 0) |
| `pytest tests/architecture -q` | 11 passed |
| `python -m py_compile api/main.py` | PASS (boot code untouched) |

Fingerprint delta: **none**. The 21 failing/error nodes are byte-identical at `702b63ae`
and `2b167e4` (both fingerprints match), so no failure node was introduced or removed.

## 5. Remaining uncertainty

- The origin of `a59453b8…` / `9a35c812…` is **UNKNOWN** — no tested convention reproduces
  them. This is recorded as unexplained rather than reconstructed.
- Passed-count variation between runs of the same tree is the documented order-dependence of
  `tests/test_engineering_lab_agent_loop.py::test_agent_loop_does_not_mutate_repository`
  (see `AGENTS.md`), not a node-set change.

## 6. Authorization required

Sovereign review and merge. No further action taken in this pass.
