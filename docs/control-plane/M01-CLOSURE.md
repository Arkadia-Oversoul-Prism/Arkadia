# M01 Closure Record — Persistence Architecture

**Status:** ACCEPTED / COMPLETE
**Date:** 2026-09-15
**Trajectory:** ARKADIA-TRUTHFULNESS-01
**Scope:** M01 — persistence-architecture
**K15/K3:** UNCHANGED

---

## 1. Purpose

This artifact records the closure of M01 after the required human review and merge
occurred. It is a closure record, not a new authorization mechanism. Its existence does
not grant authority, create credentials, alter runtime, or authorize M02.

The governing sequence was observed, not assumed:

```text
IMPLEMENTATION → VERIFICATION → READY_FOR_REVIEW → HUMAN APPROVAL → MERGE → CLOSURE
```

---

## 2. Closure Facts

| Field | Value |
|---|---|
| Move | M01 — persistence-architecture |
| PR | #39 |
| Implementation SHA | `332b9d82cf15102d3c29183e2a86aeda9bc21bcc` |
| Merge SHA | `167a1a1c56d23e7d3947203fa640fc506d6d471a` |
| Base before merge | `0a4d79ee25a6723b0b4975d9c891db723e1be2bb` |
| Base branch | `main` |
| Merge method | merge commit (repository default policy) |
| Merged at | 2026-09-15T15:51:46Z |
| Human review | **APPROVED** |

Approval was given by the Architect as: *"M01 implementation is structurally sound and
satisfies the defined acceptance boundary. APPROVED FOR MERGE."*

**Approval covered the reviewed head.** The head SHA was verified as
`332b9d82cf15102d3c29183e2a86aeda9bc21bcc` immediately before merge and was unchanged
from the reviewed artifact — a single commit, `mergeable_state: clean`.

---

## 3. Pre-Merge Gate Record

The first merge attempt was **correctly blocked**: PR #39 was still a GitHub *draft*,
contained zero recorded reviews, and its author was the same identity as the API caller
(GitHub forbids self-approval). The repository therefore derived `M01` as the next legal
move rather than advancing to M02 — the governed outcome.

The merge proceeded only after the Architect's approval was supplied out-of-band and the
draft → ready-for-review transition was performed. Merge is recorded as a human-authorized
repository mutation.

---

## 4. Post-Merge Verification

| Check | Result |
|---|---|
| Canonical branch HEAD | `167a1a1c56d23e7d3947203fa640fc506d6d471a` |
| M01 files present on `main` | `solspire/project_persistence.py`, `tests/test_m01_persistence.py`, `docs/control-plane/evidence/m01-persistence/EVIDENCE.md` — all present |
| Boot code compiles | `api/main.py`, `api/firebase_store.py`, `solspire/project_persistence.py` — clean |
| Focused suite (isolated) | `tests/test_m01_persistence.py` — **13 passed** |
| Full suite (post-merge) | `44 failed, 683 passed, 10 skipped` |
| Full suite (pre-merge baseline `0a4d79e`) | `43 failed, 671 passed, 10 skipped` |
| Unexpected files / parallel systems | none observed |

### 4.1 One regression, recorded truthfully

`tests/test_m01_persistence.py::test_db_path_honours_data_dir_env` **fails under full-suite
collection order** while passing in isolation. It is the single difference between the
pre-merge and post-merge failure sets.

Cause: `SOLSPIRE_PROJECTS_DB` takes precedence over `SOLSPIRE_DATA_DIR` in all eight
SolSpire modules (`os.environ.get("SOLSPIRE_PROJECTS_DB") or join(DATA_DIR, ...)`). Sibling
modules (`test_solspire_ownership.py`, `test_echofeild_aggregator.py`, `test_weaver_w4/w5`)
set `SOLSPIRE_PROJECTS_DB` at import time and mutate `_DB_PATH` in place. When any of those
are collected first, the reloaded module keeps the sibling's path, and the assertion
comparing against this module's own `_tmpdir` fails.

Assessment: **test-isolation defect, not a production path defect.** The variable is absent
from all deploy configurations; deployments set only `SOLSPIRE_DATA_DIR`
(`.env.example:37`, `docs/deployment/RAILWAY.md`), so the precedence branch is never taken
in a deployed environment. It does not violate M01's stated acceptance boundary. It is a
real cross-module leak and is recorded rather than concealed.

The 43 remaining failures are pre-existing and unrelated (weaver SCI/W5 boundary tests,
`api/nodes.py` layer inversions, `test_autonomy.py` and `test_render_codex.py` collection
errors), all reproduced on the pre-merge baseline.

---

## 5. Closure Basis

M01 transitions `READY_FOR_REVIEW` → `ACCEPTED / COMPLETE` because all of the following hold:

- implementation was verified (13 focused tests, zero production regressions);
- human approval was recorded;
- PR #39 was merged;
- post-merge repository state is coherent;
- M01 acceptance evidence exists in the existing evidence mechanism.

The closure marker is `docs/control-plane/evidence/m01-persistence/ACCEPT.json` — the
existing `ACCEPT.json` mechanism that `weaver/engineering_router.py::_load_completion_index()`
already reads. No new evidence architecture was created.

---

## 6. Constitutional Non-Claims

This record does not claim:

- that M02 is authorized, implemented, or started;
- that M01's known limitations were resolved (they were accepted);
- that live production redeploy survival has been observed — it was simulated, and live
  verification still requires deployment authorization, which has not been granted;
- that Firestore was exercised against a live backend;
- that any parallel database, filesystem, identity, memory, Knowledge OS, or conversational
  runtime was introduced;
- that K15 or K3 changed.

```text
MERGE        ≠ DEPLOYMENT
COMPLETION   ≠ AUTHORIZATION OF THE NEXT MOVE
CLOSURE      ≠ PERMISSION TO CONTINUE
```

**Next legal move:** derived from repository state by the router — expected `M02`,
subject to its own authorization and review gate.