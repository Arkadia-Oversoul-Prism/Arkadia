# ARK-OPS-CONTINUOUS-001 — cycle 29: FSN's device location read is now audited

**Contract:** `ARK-OPS-CONTINUOUS-001` rev `2026-11-22`
**Portfolio directive:** `PORTFOLIO-WEAVER-2026-11-26-01`
**Base:** `main` @ `8f746f9eab6df51733f6d43c8bab26af63eb6471` (Arkadia)
**Branch:** `gate-hygiene/portfolio-state-ledger-01`
**Pulse:** 2026-11-28T00:07Z
**Authority:** `MERGE_AUTHORITY := NONE`, `DEPLOY_AUTHORITY := NONE`. No merge, no push to any
canonical branch, no deployment, no acceptance, no draft conversion. The ledger's own PR #744
was extended rather than duplicated.

This is a **reconciliation/implementation** record, so it takes the bare `…-cycle-NN` path.
The work itself landed in the selected repository (`family-safety-network`), not here.

Files this record touches in Arkadia:

```
docs/control-plane/openhands/hourly-weaver/portfolio-state.json                                      (re-derived)
docs/control-plane/openhands/hourly-weaver/portfolio-cursor.json                                     (authored judgement)
docs/control-plane/evidence/ark-ops-continuous-001-cycle-29-fsn-location-read-audit-01/EVIDENCE.md   (new)
```

---

## 1. Reconstruction and selection

Live from GitHub at 2026-11-28T00:07Z, not from memory:

| Repository | Default branch | Head | Open PRs | `last_progress_at` |
|---|---|---|---|---|
| `sonata` | `feature/sonata-tts-app` | `7c4e6a64e39e` | 2 | 2026-11-27T16:19:14Z |
| `family-safety-network` | `main` | `18c729735fd4` | 8 | 2026-11-27T14:15:04Z |
| `Arkadia` | `main` | `8f746f9eab6d` | 64 | 2026-11-27T17:12:43Z |

FSN was oldest, so the fairness rule selected it; the tie-break order was never reached.
The selection was re-derived twice: once by hand from the GitHub API and once by
`scripts/portfolio_state_refresh.py --write` at 00:19Z. Both agreed.

## 2. Selected task — and a recorded divergence from the cursor

The cursor's FSN `next_legal_task` named **F4's threat-model re-review** (the stale `F3`
TLS row and `F4` retention row). This pulse selected a different slice, and the reason is
recorded rather than glossed:

- the directive says to *prefer the earliest incomplete phase in the canonical trajectory*;
  **F2** (privacy and data lifecycle → *audit requirements*) precedes **F4**;
- the slice found is a **code** defect on a security boundary, not a documentation refresh;
- no open FSN draft owned it, so the cursor's own rule — "do not open a ninth FSN PR for a
  slice an existing draft owns" — was respected, not bent.

The F4 re-review is **not** retired by this pulse. It remains the next unowned F-series
slice and is still recorded as such in the cursor.

## 3. The defect

`documentation/security/THREAT-MODEL.md` **T14** states the invariant: *"Every sensitive
action writes an `audit_events` row, including denied reads."* `documentation/api/API-CONTRACT-v1.md`
**§3.13** gives `GET /v1/devices/{device_id}/last-location` *"Same authorization as 3.12"*.

The device read wrote **no** audit row at all — allowed, denied and unavailable were all
invisible — while the member read in §3.12 recorded both outcomes. One of the two
location-read paths had no accountability record, so the same last-known location was
auditable through one route and untraceable through the other.

Measured, not inferred: the new test file carries a **positive control** on the §3.12 path.
Pre-repair that control passed and all three §3.13 assertions failed with `len(audit rows)
== 0` — the assertion shape is not vacuous.

## 4. Change and evidence

| Item | Value |
|---|---|
| FSN issue | #20 |
| FSN branch | `fsn/location-read-audit-completeness-01` |
| FSN PR | #21 (draft) |
| Head SHA | `796d4a6a0bf260e62055586c5f7cea0cf112d548` |
| Files | `backend/app/routes.py`, `backend/tests/test_location_read_audit.py`, `documentation/api/API-CONTRACT-v1.md`, `documentation/security/THREAT-MODEL.md` |
| Negative control | `3 failed, 1 passed` on the pre-repair tree |
| Local full suite | `65 passed` (61 pre-existing + 4 new) on PostgreSQL 15 + PostGIS 3.3 |
| Live contract | `tools/api_integration_test.py` → 14/14 calls matched |
| `alembic check` | `No new upgrade operations detected.` |
| CI | run `46087140191` at `796d4a6` — all three jobs `success`; the backend step log reads `65 passed`, all four new nodes `PASSED`, `No new upgrade operations detected.`, `ALL 14 CONTRACT CALLS MATCHED` |

## 5. Composition, measured

Two open FSN drafts touch `backend/app/routes.py`. Composed in a detached worktree:

| Composition | Conflicted files | Backend suite |
|---|---|---|
| #21 + #15 | 1 — `documentation/api/API-CONTRACT-v1.md` §3.13 only (both append a sentence to the same paragraph) | 72 passed |
| #21 + #15 + #16 | 0 | 85 passed |

`backend/app/routes.py` auto-merged in both cases: the audit block was deliberately anchored
*below* `viewer = require_membership(...)` so #15's one-line change to that statement is a
different hunk. The single reconciliation is keeping both sentences in §3.13.

## 6. Adjacent defects recorded, not repaired

1. `THREAT-MODEL.md` §5.5 still says *"no retention or deletion policy is implemented"*
   while `backend/app/retention.py` implements purge, member erasure and account erasure.
   PR #17 already touches the retention documentation; fixing it here would duplicate that
   work and widen this PR's scope.
2. `THREAT-MODEL.md` `F3` (TLS) and `F4` (retention) rows — the cursor's named F4 re-review.
   Still outstanding.
3. FSN issue/PR phase labels remain misaligned with the directive's phase definitions
   (recorded in the previous cycle; unchanged).

## 7. Boundary

No merge, no deployment, no release, no acceptance. FSN's merge policy requires explicit
repository governance authorisation and human approval; neither is claimed here. PR #21 is a
draft and becomes reviewable only by its owner.
