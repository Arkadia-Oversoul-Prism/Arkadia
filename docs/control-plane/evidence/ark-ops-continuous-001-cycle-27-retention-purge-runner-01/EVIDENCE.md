# ARK-OPS-CONTINUOUS-001 — cycle 27: the retention window gets a runner

**Contract:** `ARK-OPS-CONTINUOUS-001` rev `2026-11-22`
**Portfolio directive:** `PORTFOLIO-WEAVER-2026-11-26-01`
**Base:** `main` @ `8f746f9eab6df51733f6d43c8bab26af63eb6471`
**Branch:** `gate-hygiene/portfolio-state-ledger-01`, entered at
`63eb9520df8bdb2042cb413ef519e0daf43394a4`
**Pulse:** 2026-11-27T06:06Z
**Authority:** `MERGE_AUTHORITY := NONE`, `DEPLOY_AUTHORITY := NONE`. No merge, no push to
`main`, no deployment, no acceptance, no draft conversion. No new pull request was opened
for the ledger; the existing PR #744 was extended.

This is a **reconciliation/implementation** record, so it takes the bare
`…-cycle-NN` path. The work itself landed in the selected repository
(`family-safety-network`), not here.

Files this record touches in Arkadia:

```
docs/control-plane/openhands/hourly-weaver/portfolio-state.json   (re-derived)
docs/control-plane/openhands/hourly-weaver/portfolio-cursor.json  (authored)
docs/control-plane/evidence/ark-ops-continuous-001-cycle-27-retention-purge-runner-01/EVIDENCE.md  (new)
tests/test_portfolio_state_ledger.py                              (§7, test-side repair)
```

---

## 1. Reconstruction and selection

Live from GitHub at 2026-11-27T06:06Z, not from memory:

| repository | default branch | head | open PRs | `pushed_at` |
|---|---|---|---|---|
| `sonata` | `feature/sonata-tts-app` | `7c4e6a64e39e` | 1 | 2026-11-27T04:17:56Z |
| `family-safety-network` | `main` | `18c729735fd4` | 5 | **2026-11-27T03:14:30Z** |
| `Arkadia` | `main` | `8f746f9eab6d` | 63 | 2026-11-27T05:28:00Z |

`family-safety-network` carries the oldest verified progress, so §4.1 selects it. This
differs from cycle 26, which selected Arkadia at `pushed_at` 02:13:18Z; Arkadia's 05:28:00Z
push moved it off the front. The selection was recomputed from the API, not carried
forward.

## 2. What was missing, and how that was decided

Not from a hunch. `backend/app/retention.py` states that `purge_expired` "is idempotent
and safe to run on a schedule", and `POST /v1/maintenance/purge` repeats it ("Idempotent;
safe to schedule"). `grep -rn "scheduler\|BackgroundTasks\|lifespan\|cron\|APScheduler"
backend .github docker-compose.yml` returned **no match**: nothing called the purge on a
schedule, so the 90-day observation window and the 730-day emergency-event window held
only when a human remembered to POST.

The repository had already recorded it. `documentation/REMEDIATION-REPORT-PR8.md` §9,
"Remaining before any production release":

> a scheduled purge runner (the endpoint is ready; no scheduler is deployed)

No open PR owned it: the five open FSN drafts touch `routes.py`, `authz.py`,
`ratelimit.py`, `security.py`, `models.py`, `alembic/`, `.env.example` and the
remediation report — none touch `retention.py` or add a caller.

## 3. The change

`family-safety-network` PR #17 (draft), branch `fsn/f4-scheduled-purge-runner`,
head `b11052c02da8683f8137e4970cdce4adcde5412c`:

```
.github/workflows/ci.yml                        +7
backend/app/maintenance.py                      +116 (new)
backend/tests/test_maintenance_purge_runner.py  +220 (new)
documentation/privacy/RETENTION-PURGE-RUNNER.md +101 (new)
```

`python -m app.maintenance purge` is a **one-shot** command, not an in-process thread. A
thread inside the API process runs once per worker, so N uvicorn workers would purge N
times per interval and a scaled deployment would silently multiply the work — the same
class as F8 (process-local rate limiter). Scheduling belongs to cron / systemd /
CronJob, which own process lifetime; all three shapes are documented and none applied.

A run writes one audit row with `target_id=scheduler` and `actor_user_id=NULL`, which
keeps a scheduled purge distinguishable from an operator's authenticated call
(`target_id=purge`, user id present). Failures report the exception **type** only, because
driver errors embed the connection string and a cron log is shipped to a log aggregator;
`--traceback` is the explicit opt-in.

## 4. Verification

Real PostgreSQL 15 + PostGIS 3.3.3 (`postgis/postgis:15-3.3`), `alembic upgrade head`:

```
main 18c72973    python -m pytest tests/ -q    61 passed
branch b11052c    python -m pytest tests/ -q    69 passed
```

`+8` is exactly the new file's 8 nodes (`pytest tests/test_maintenance_purge_runner.py`
-> `8 passed`), measured per file rather than inferred from the delta.

Negative controls, each applied to the real module and then restored:

| mutation | result |
|---|---|
| echo `str(exc)` instead of the type | **2 failed** (no-echo test + opt-in polarity test) |
| attribute the audit row to `"system"` | **1 failed** (unattributed-run test) |

Runtime evidence, GitHub Actions run `45950456249` (`push`, head `b11052c`),
`conclusion: success`:

- `9. Run the retention purge runner once` -> **success** — the command a deployment
  would schedule executed against the CI PostGIS service;
- `8. Run test suite`, `10. Verify app starts`, `11. alembic check`,
  `12. Verify OpenAPI contract`, `13. API integration test` -> success;
- `Android build` -> success (`./gradlew assembleDebug` with the committed wrapper).

**Limitation, recorded rather than papered over:** the per-step raw log could not be
retrieved with this token (the job-log endpoint returned no content), so the JSON the CI
step emitted is **not quoted** here. The quoted JSON comes from the local run against the
same image tag. The step *conclusion* is the runtime evidence; the payload is not.

## 5. Post-pulse derivation

The push advanced FSN's own clock, which is the expected effect of a real push (cycle 26
established `pushed_at` as the fairness input precisely so a comment cannot do this):

```
family-safety-network: progress=2026-11-27T06:13:11Z pulls=6
Arkadia:               progress=2026-11-27T05:28:00Z
sonata:                progress=2026-11-27T04:17:56Z
next: sonata -- oldest verified last_progress_at
```

So the next pulse selects `sonata`. `portfolio-state.json` was re-derived by
`scripts/portfolio_state_refresh.py --write`, not hand-edited.

## 6. Not done

- **Physical-device acceptance (F7) is untouched.** No device; CI is not device evidence.
- **No scheduler is deployed.** Deployment is a human-authorised action.
- **F8 (process-local rate limiter) is untouched.** The one-shot design avoids adding a
  second process-local mechanism; it does not repair the existing one.
- **`documentation/REMEDIATION-REPORT-PR8.md` was not edited** in the FSN PR: #10 and #12
  both modify that file and a third edit would conflict for no benefit.
- **The cycle index** (`docs/control-plane/evidence/ark-ops-continuous-001/LEDGER.md`)
  is not present on this branch — it was merged to `main` in #705 after this branch's
  base `cb284195` — so it was not updated here. Adding it on this branch would conflict
  on merge.

## 7. A state-pinned control that a correct refresh reddened

Refreshing `portfolio-state.json` from live state moved the recomputed selection from
`Arkadia` to `sonata` (FSN's push advanced its clock, and Arkadia's 05:28 push had
already overtaken it). That reddened one existing node:

```
FAILED tests/test_portfolio_state_ledger.py::test_a_recorded_selection_that_disagrees_with_arithmetic_is_reported
1 failed, 21 passed
```

The control hard-coded `SONATA` as the "typed" winner:

```python
broken["selection"] = {"repository": SONATA, "reason": "typed"}
```

It passed only while the live arithmetic selected something **other than** Sonata. Once
the arithmetic legitimately selected Sonata, the forced value *agreed* with the
recomputation and the expected finding could not be produced. The guard had not been
testing disagreement; it had been testing a remembered winner — the same class as the
`declared_idle` first-vs-last defect and the stale fixture-vs-live fingerprint gap already
recorded in `AGENTS.md`.

Repair (test-side, 6 lines): derive the disagreeing value from the recomputation itself.

```python
recomputed = portfolio_state.select_next(broken, cursor)["repository"]
disagreeing = next(n for n in portfolio_state.CANONICAL_REPOS if n != recomputed)
broken["selection"] = {"repository": disagreeing, "reason": "typed"}
```

Proven in both polarities against the live ledger:

```
recomputed: Arkadia-Oversoul-Prism/sonata | forced: Arkadia-Oversoul-Prism/family-safety-network
findings: ["recorded selection 'Arkadia-Oversoul-Prism/family-safety-network' is not the
            recomputed selection 'Arkadia-Oversoul-Prism/sonata'"]
agreeing case silent: True
```

`python -m pytest tests/test_portfolio_state_ledger.py -q` -> **22 passed**, and
`scripts/portfolio_state.py --check` -> `PASS (3 repositories, next:
Arkadia-Oversoul-Prism/sonata)`, exit 0.

The alternative — leaving the state unrefreshed so the old winner stayed true — would have
kept a control green by keeping the ledger wrong. The ledger's whole purpose is that its
selection is derived, so the refresh is correct and the control was the defect.
