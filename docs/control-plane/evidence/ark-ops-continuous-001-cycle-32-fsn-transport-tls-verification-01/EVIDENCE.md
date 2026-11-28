# ARK-OPS-CONTINUOUS-001 — cycle 32: FSN's transport guard is verified, and the row that denies it is not

**Contract:** `ARK-OPS-CONTINUOUS-001` rev `2026-11-22`
**Portfolio directive:** `PORTFOLIO-WEAVER-2026-11-26-01`
**Base:** `main` @ `8f746f9eab6df51733f6d43c8bab26af63eb6471` (Arkadia)
**Branch:** `gate-hygiene/portfolio-state-ledger-01`
**Pulse:** 2026-11-28T02:06Z
**Authority:** `MERGE_AUTHORITY := NONE`, `DEPLOY_AUTHORITY := NONE`. No merge, no push to any
canonical branch, no deployment, no acceptance, no draft conversion. The ledger's own PR #744
was extended rather than duplicated.

This is a **reconciliation/implementation** record, so it takes the bare `…-cycle-NN` path.
The work itself landed in the selected repository (`family-safety-network`), not here.

Files this record touches in Arkadia:

```
docs/control-plane/openhands/hourly-weaver/portfolio-state.json                                       (re-derived)
docs/control-plane/openhands/hourly-weaver/portfolio-cursor.json                                      (authored judgement)
docs/control-plane/evidence/ark-ops-continuous-001-cycle-32-fsn-transport-tls-verification-01/EVIDENCE.md (new)
```

The cycle index (`…/ark-ops-continuous-001/LEDGER.md`) is **not** updated here: it lives on
`main` (merged by #705 at `8f746f9e`) and this branch is based on `cb284195`, five commits behind.
Adding the cycle-32 row belongs to whoever next reconciles the index, and inventing a second copy
on this branch would recreate the split-ledger problem the index was written to fix.

---

## 1. Reconstruction and selection

Live from GitHub at 2026-11-28T02:07Z, not from memory:

| Repository | Default branch | Head | Open PRs | `last_progress_at` |
|---|---|---|---|---|
| `sonata` | `feature/sonata-tts-app` | `7c4e6a64e39e` | 3 | 2026-11-28T01:22:22Z |
| `family-safety-network` | `main` | `18c729735fd4` | 9 | 2026-11-28T00:17:44Z |
| `Arkadia` | `main` | `8f746f9eab6d` | 64 | 2026-11-28T01:24:08Z |

FSN was oldest, so the fairness rule selected it; the tie-break order was never reached.
Selection was derived by hand from the GitHub API and then re-derived by
`scripts/portfolio_state_refresh.py`; both agreed.

All three repositories were reachable with the session token
(`GET /repos/Arkadia-Oversoul-Prism/{Arkadia,sonata,family-safety-network}` → 200, `sonata`
default branch `feature/sonata-tts-app`, FSN `private: true`). Nothing was omitted.

## 2. Selected task — F4's first named item, and the cursor's named row

The cursor's FSN `next_legal_task` named the **F4 threat-model re-review** and required an F4
phase issue before implementation (directive §7). No F4 issue existed, so **#22** was created
first, then the slice was implemented as **draft PR #23** (`fsn/f4-transport-tls-boundary-01`,
head `0dc96d7`).

The slice is the part of F4 that is a **code** defect rather than a documentation refresh:
*verify TLS* — the directive's first F4 item.

## 3. The defect

`documentation/security/THREAT-MODEL.md` **F3** (line 92) reads *"No TLS enforcement in
application code; relies entirely on deployment."* The control exists:

| Control | Location |
|---|---|
| request-time refusal of plaintext in production | `backend/app/main.py` `enforce_https` (`@app.middleware("http")`) |
| `require_https` flag | `backend/app/config.py:75` (`FSN_REQUIRE_HTTPS`) |
| startup refusal when production omits it | `backend/app/config.py:150` `validate_settings` |
| test for the startup half | `backend/tests/test_config_security.py:80` |
| **test for the request-time half** | **absent** |

Measured on `main` `18c7297`:

```
$ grep -rn "https_required\|enforce_https\|is_production" backend/tests/
(no matches)
```

The middleware could be deleted and every assertion in the suite would still pass, while a
production deployment served plaintext. The security record simultaneously told a reader the
control did not exist. Both halves are the same defect: a boundary that is neither verified
nor correctly described.

## 4. Change and evidence

One new file, `backend/tests/test_transport_tls_boundary.py`, 110 lines, 7 nodes. No production
code changed.

| Check | Result |
|---|---|
| Baseline `main` `18c7297` (`pytest tests/ -q`) | **61 passed** |
| Branch `0dc96d7` (same tree + new file) | **68 passed** |
| Attribution | `--collect-only` on the new file → **7**, exactly the delta |
| Negative control (guard condition → `if False:` in `app/main.py`) | **3 failed, 4 passed** — exactly the three refusal assertions; every positive control stayed green |
| Restore | `git diff` empty (byte-identical) |
| Composition with open FSN drafts | #21 clean, #15 clean, **#16 CONFLICT** in `THREAT-MODEL.md` |

Database: PostgreSQL 15 + PostGIS 3.3 (`postgis/postgis:15-3.3`, the CI image), `alembic upgrade
head` applied to a clean database (12 tables). The new tests need no database — the middleware
runs before routing — so they also pass where PostGIS is absent.

Positive controls are on both sides deliberately: a guard that refused everything, and a guard
that gated every environment, are both indistinguishable from the real one on the refusal
assertions alone.

## 5. What was NOT done, and why — a measured deferral

The F3 row is still stale on the branch. Editing it conflicts with open draft #16, whose
findings-table hunk (`@@ -88,7 +88,7 @@`) rewrites the F2 row and carries F3/F4 as context:

```
$ git merge --no-commit --no-ff origin/fsn/route-rate-limit-coverage-01          # #16
CONFLICT (content): Merge conflict in documentation/security/THREAT-MODEL.md
$ git merge --no-commit --no-ff origin/fsn/location-read-audit-completeness-01   # #21
Automatic merge went well; stopped before committing as requested
$ git merge --no-commit --no-ff origin/fsn/resource-existence-oracle-01          # #15
Automatic merge went well; stopped before committing as requested
```

Carrying the one-line correction would make the tenth FSN draft conflict with a CI-green draft
awaiting human review. The correction becomes conflict-free the moment #16 lands, so it is
recorded on #22 (comment `7232219693`) and deferred, not dropped.

The same conflict applies to **F4** (line 93) and **§5.5** (line 81), which still deny a
retention policy that `backend/app/retention.py` implements (`purge_expired`,
`erase_member_data`, `erase_account_data` behind `POST /v1/maintenance/purge`,
`DELETE /v1/account`, `DELETE /v1/families/{fid}/members/{mid}/data`); §5.5 is context in #21's
hunk.

Also recorded, not repaired: the guard compares `X-Forwarded-Proto` to `"https"` **exactly**, so
`HTTPS` and a chained-proxy list `https, http` are refused (`400`). Widening that is a behaviour
change to a security control — accepting the first element of a client-supplied list is not
obviously safe — so it is stated in the test module and left for a deliberate decision.

## 6. Portfolio state after this cycle

`scripts/portfolio_state_refresh.py --write` re-derived the ledger at 02:14Z. FSN's
`last_progress_at` is now `2026-11-28T02:13:12Z` (this cycle's push), so the fairness rule selects
**Sonata** next. That is the ledger's own push clock advancing itself — the property cycle 26
(`…-cycle-26-portfolio-push-clock-01`) fixed — not a judgement about which repository needs work.

## 7. Deterministic next action

**Current state.** Arkadia `main` `8f746f9eab6d`. FSN `main` `18c729735fd4`, 10 open drafts
(#10, #12, #14–#19, #21, #23) plus issue #22. Sonata `7c4e6a64e39e`, 3 open drafts (#9, #10,
#11). All three reachable.

**Evidence.** PR #23 (FSN) head `0dc96d7`: 68 passed vs 61 on `main`, negative control
`3 failed, 4 passed`, #21/#15 compose cleanly, #16 conflicts on `THREAT-MODEL.md`.

**Blockers.** (a) Human review of ten FSN drafts; (b) the F3/F4/§5.5 row corrections wait on
#16/#21 landing; (c) physical-device acceptance has no hardware; (d) the F4 release checklist is
absent and is a separate slice.

**Authorized action next cycle.** Select by fairness (currently Sonata), and continue an existing
draft rather than opening a parallel one.

**Forbidden.** Merge, push to a canonical branch, deploy, convert a draft to ready, delete a
branch, widen the TLS guard's matching rule.

**Completion condition for this cycle.** Met: one bounded slice implemented in the selected
repository, tests measured against a real PostGIS database, a negative control proving the pin
bites, the deferral recorded with its measurement, and the ledger re-derived.
