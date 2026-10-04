# EVIDENCE — gate02/production-deploy-fetch-suffixed-labels

Bounded workstream: repair the **Gate-2 production-observation harness** so it can
see the newest Production deployment, and pin the repair with tests plus a
negative control. This is a source + test change, not an evidence-only pass.

Observation timestamp: `2026-10-04T12:0xZ` (automation run).

## 1. Reconstruction (live evidence)

| item | value |
|---|---|
| canonical repo | `https://github.com/Arkadia-Oversoul-Prism/Arkadia` |
| BASE_MAIN (origin/main) | `1b7c089f237a1a8ea11791ab060525b0e36e2029` |
| open PRs (all) | **1** — `#262` (`gate-hygiene/baseline-reconciliation-recovery-frontend-build-01`) |
| PR #262 base / head | base `1b7c089f` / head `3eefcb03f2d1e5cd9baac8fb52020c273d9f097f`, mergeable |
| PR #262 diff | **+373 / -0, 2 files** — both `docs/control-plane/evidence/.../` (evidence-only) |
| PR #262 checks on head | `Vercel Preview Comments` success, `Full-history secret scan` success |

### 1.1 Queue-count caveat (uncorrected by this pass)

Repo memory (`AGENTS.md`) records a **7-open-PR** inventory from a same-day pass. All
four API spellings tried here (`GET /pulls?state=open`, with/without
`per_page`, `X-GitHub-Api-Version`, `Accept: application/vnd.github+json`) returned
exactly one open PR. The discrepancy is **UNKNOWN** — it is not reconciled or
overwritten by this pass. Per contract rule 1 the live query is authoritative for this
pass; the memory figure is left for the next pass to reconcile.

## 2. Defect (reproduced)

`scripts/gate2_production_observation.py` reported `main -> deployment identity`
as `UNKNOWN` on current `main` while a newer Production deployment existed.

Root cause measured directly against the API:

```
GET /deployments?environment=Production&per_page=100
  -> newest record: 57e67c534ff6...  2026-10-02T06:06:28Z  environment="Production"
GET /deployments?per_page=200   (unfiltered, filter client-side)
  -> newest Production record: fa1b40787544...  2026-10-04T08:42:37Z
                               environment="Production - arkadia-prism"
```

Both the client-side equality test (`d.get("environment") != "Production"`) and the
server-side `?environment=Production` query predicate match only the **bare** label.
Once Vercel began suffixing the project name, the harness admitted **zero** production
deployments and reported the link as `UNKNOWN` — indistinguishable from "no deploy
exists". The previous pass (PR #262 section 9.3) recorded this as a *caution for the
next pass*; this pass implements that recorded recommendation.

## 3. Change

- `scripts/gate2_production_observation.py`
  - `PRODUCTION_ENVIRONMENT_RE = re.compile(r"^Production\b")` — anchored prefix match,
    so `Production - arkadia-prism` is admitted and `Preview - arkadia-prism` is not.
  - `production_deployments()` matches on that prefix and skips non-string env values.
  - fetch changed to `GET /deployments?per_page={max(limit*5, 50)}` (unfiltered);
    filtering is client-side via the tested predicate.
- `tests/test_gate2_production_observation.py` — +3 tests:
  `test_project_suffixed_production_labels_are_admitted`,
  `test_suffixed_preview_label_is_not_admitted` (negative control for the regex),
  `test_deployments_are_fetched_unfiltered` (pins the unfiltered fetch).

## 4. Verification

| gate | command | measured |
|---|---|---|
| target tests | `pytest tests/test_gate2_production_observation.py -q` | **19 passed** |
| negative control | 3 new tests vs pre-change script | **3 failed, 16 passed** (control bites) |
| architecture | `pytest tests/architecture -q` | **11 passed** (11/11) |
| full suite | `pytest tests/ -q --continue-on-collection-errors -rf` | **9F / 1417P / 20S / 1E** |
| failure node-set sha256 | `grep -E '^(FAILED\|ERROR)' \| sort \| sha256sum` | `00b3984e7ad487f1c36e1449429834cdf398f5dde8d4591f4079942c180af48b` |
| `api/main.py` | `wc -l` + `py_compile` | 2582 / 2600, compiles OK |
| CP10 boundary | `git diff --name-only \| python scripts/cp10_mutation_boundary_policy.py --judge` | PASS (RC 0) |

### 4.1 Regression boundary

The failure node-set sha256 `00b3984e...` is **byte-identical** to the baseline PR #262
records. The `+3 passed` is exactly the 3 added tests. **Zero node-set delta.**

### 4.2 Live harness output after the repair

```
newest Production deploy: fa1b40787544  id=6838852040  2026-10-04T08:42:37Z
  deploy SHA == main    : False  (deploy predates main -> STALE)
  current main resolved                      VERIFIED
  main -> deployment identity                STALE   (was UNKNOWN)
  deployment build output observed           BLOCKED
  alias reachable                            VERIFIED
  build <-> source lineage                   VERIFIED
```

`fa1b40787544` is an **ancestor** of `main` and is a descendant of `dc3f605b` (the last
commit touching a frontend build input), so the deployed frontend artifact is
source-identical to `main` — `STALE`-by-ref, not divergent. Gate 2 observation remains
`BLOCKED` on Vercel Deployment Protection (unchanged).

## 5. Classification

**VERIFIED** — implementation exists, target tests pass, negative control bites,
protected architecture passes, node-set fingerprint unchanged, provenance inspectable.

Authorization required: sovereign review → merge. No merge, no push to `main`.
This pass does **not** close Gate 2; production acceptance remains a sovereign act.

_Repair and evidence written by an AI agent (OpenHands) on behalf of the sovereign._
