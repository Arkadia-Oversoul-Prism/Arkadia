# Gate-2 open-PR composition — measured, not assumed

**Workstream:** `gate-hygiene/gate2-open-pr-composition-01`
**Base revision:** `main` @ `bb19aabda34d59594615b0279a45e9cbd3d8204d` (2026-11-22T17:23:48Z)
**Candidates:** PR #681 (head `04f2969b5269d5606f4a42abc7852c5b84d4b5ef`), PR #687 (head `be751f9db372b635033a35cbee7c9e691e64c5f8`)
**Authority:** NONE. No merge, no push to `main`, no deployment, no acceptance. This record is measurement plus a proposed next action.

---

## 1. Why this record exists

Two open candidates modify the same two files of the production-observation harness:

| PR | Title | Files touching the harness |
|----|-------|----------------------------|
| #681 | `fix(gate2): bind the marker oracle to the app the served artifact belongs to` | `scripts/gate2_production_observation.py`, `tests/test_gate2_production_observation.py`, `.github/workflows/gate2-production-observation.yml`, `tests/test_gate2_production_observation_ci_wiring.py` |
| #687 | `fix(gate2): stop calling a warming deployment an unreachable alias` | `scripts/gate2_production_observation.py`, `tests/test_gate2_production_observation.py` |

The repository's own rule (`AGENTS.md`, "Contradicting PRs: resolve by measurement, not argument") is that a claimed conflict must be **measured**, and that git conflict-free is not proof of semantic compatibility. Neither PR records whether the other can be merged alongside it. This pass measures both directions.

---

## 2. The conflict is real, and it is additive-at-end-of-file only

```
$ git worktree add --detach /tmp/wt681 04f2969b
$ git merge --no-edit be751f9d
Auto-merging scripts/gate2_production_observation.py
Auto-merging tests/test_gate2_production_observation.py
CONFLICT (content): Merge conflict in tests/test_gate2_production_observation.py
```

* `scripts/gate2_production_observation.py` auto-merges (no conflict).
* `tests/test_gate2_production_observation.py` carries **one** conflicted region, `<<<<<<< HEAD` at line 499 through `>>>>>>> be751f9d` at line 706.
* Both sides of that region are a **new test section appended at end of file** — #681 appends "Served-artifact app identity", #687 appends its cold-start section. There is no shared line under contention; git reports a conflict because both branches insert at the same offset.

### The resolution is mechanical: keep both sections

```python
# both sides are whole appended sections -> concatenate them
text[:start] + head_side + theirs_side + text[end:]
```

Applied in `/tmp/wt681`; zero conflict markers remain; `python -m py_compile
scripts/gate2_production_observation.py` exits 0.

---

## 3. The composition is semantically disjoint — proven by node identity, not by count

Per-file collection on each tree:

| Tree | `test_gate2_production_observation.py` | `..._ci_wiring.py` |
|------|----------------------------------------|--------------------|
| `main` `bb19aabd` | 41 | 0 (file does not exist) |
| #681 head | 48 (+7) | 8 |
| #687 head | 49 (+8) | — |
| **composed** | **56 = 41 + 7 + 8** | 8 |

The composed count is exactly the sum of the two deltas over the base. Neither PR's appended section shadows a node of the other (a name collision would make the composed count *smaller* than the sum), and neither removes a base node.

```
$ PYTHONPATH=$PWD python -m pytest tests/test_gate2_production_observation.py \
      tests/test_gate2_production_observation_ci_wiring.py -q
64 passed in 1.13s
```

Individually, for completeness: #681 alone **56 passed**; #687 alone **49 passed**.

---

## 4. The composed harness produces a stronger boundary classification than `main`

Same machine, same minute, same canonical origin. The difference is the PR content, not the environment.

### `main` @ `bb19aabd`

```
MARKER-SET LINEAGE (literal : deployed / expected)
  artifact app: UNDETERMINED   scoring against: no declared marker list
  no artifact fetched -> no marker set read (NOT OBSERVED)
  !! STALE marker list -- literals gone from source: [... 7 Prism-era literals ...]

BOUNDARY CLASSIFICATION
  main -> deployment identity                UNKNOWN
  deployment build output observed           UNKNOWN
  marker-set oracle                          NOT OBSERVED (served app undetermined; markers describe 'arkadia-prism')
```

The alias *was* fetched (HTTP 200, `assets/index-CYGHeCpJ.js`) yet nothing scored it: the marker list still describes the archived Prism app, and the served artifact is the console.

### Composed (#681 + #687)

```
  bundle  : assets/index-CYGHeCpJ.js (426232 bytes)

MARKER-SET LINEAGE (literal : deployed / expected)
  artifact app: arkadia-console   scoring against: arkadia-console
  Protected surface                              1  (expect>0)
  Sign in to continue                            1  (expect>0)
  Go to sign in                                  1  (expect>0)
  Reading canonical contract                     1  (expect>0)
  Human authority remains the decision boundary  3  (expect>0)
  Arkadia is temporarily unreachable             2  (expect>0)
  Enter the enterprise layer.                    0  (expect 0)

BOUNDARY CLASSIFICATION
  main -> deployment identity                UNKNOWN
  marker-set oracle                          VERIFIED (marker set observed in served artifact)
  SG-04                                      NOT EVALUABLE: score against the 'arkadia-console' app, which has no SG-04 surface
  production acceptance                      NOT CLAIMED (human authority)
```

The control literal (`Enter the enterprise layer.`) reads **0** and is scored under its declared `expect == 0` polarity, so the oracle is not merely "everything present".

**What this does not prove.** It is an observation of the served artifact, not deployment-identity evidence, not browser-rendered UI correctness, and not production acceptance. `main -> deployment identity` stays `UNKNOWN` on the composed tree too (see §6).

---

## 5. Merge sequencing — advisory only

Both orders are mechanically viable; the conflict is symmetric. Recommended for human consideration:

1. **#681 first** (larger surface: it also adds the CI-wiring workflow and the wiring judge), then
2. **rebase #687 onto the new `main`**, resolving the single appended-section region by keeping both sections, and re-run the pair (expected `64 passed`).

Rebasing #687 alone onto `main` first, then #681, is equally valid. What must not happen is merging both and letting the second conflict be resolved by dropping one PR's section: §3 shows both sections are additive and independently collected, so a drop is a silent loss of seven or eight test nodes.

**This section is an assessment, not authorization.** Under GOV-03 all merge execution is human-only.

---

## 6. Identified next gap — recorded, not repaired

`GET /api/version` on the canonical origin is public, read-only, and already publishes the exact deployed revision:

```
$ curl -s https://arkadia-qzu4.onrender.com/api/version
{"schema":"arkadia.version/v1", ..., "source_revision":"bb19aabda34d59594615b0279a45e9cbd3d8204d",
 "revision_source":"RENDER_GIT_COMMIT","revision_conflict":false, ...}
```

That value equals `main` at the moment of measurement. **The harness does not read it.** `grep -n "api/version" scripts/gate2_production_observation.py` returns no match on `main`, on #681, on #687, or on the composed tree, so the `main -> deployment identity` boundary is classified `UNKNOWN` while the evidence needed to classify it is one unauthenticated GET away.

Proposed (not implemented here) design, to be owned by the PR that already owns "bind the oracle to the served app" (#681) rather than by a third competing candidate on the same file:

* probe `GET /api/version` on the observed origin;
* `source_revision == main` **and** `revision_conflict == false` -> `main -> deployment identity: VERIFIED (source_revision == main)`;
* `source_revision != main` -> report **drift**, naming both SHAs; never "stale deployment" without the pair;
* absent/`null` `source_revision`, non-JSON body, or `revision_conflict == true` -> `UNKNOWN` (contradictory evidence fails closed; it must not be promoted to a pass by repetition);
* keep the endpoint's own caveat: a matching revision is necessary evidence of source-to-runtime consistency, **not** proof the application works, and **not** deployment acceptance.

Not implemented this pass because `scripts/gate2_production_observation.py` already carries two open candidates, and adding a third change to that file compounds a conflict this record exists to make resolvable.

---

## 7. Cycle state — what this pass verified about `main`

| Item | Observation | Classification |
|------|-------------|----------------|
| `main` SHA | `bb19aabda34d59594615b0279a45e9cbd3d8204d` | OBSERVED |
| Production revision | `/api/version` `source_revision` == `main`, `revision_conflict: false` | VERIFIED (source↔runtime consistency) |
| Alias reachable | `GET /` with a browser `Accept` -> HTTP 200, 1256 B shell | VERIFIED |
| Full suite on `main` | `19 failed, 4250 passed, 22 skipped, 1 error` (284 s) -> 20 failing/error nodes | OBSERVED |
| Mission-lifecycle block (10 nodes) | **environment-only**: with the locked console toolchain installed (`corepack pnpm install --frozen-lockfile`), `tests/test_mission_lifecycle_adapter_contract.py` -> **10 passed**. The gate that executes it (`prism-console-contract.yml`) installs that toolchain before running the derived domain, so these are not repository debt. | VERIFIED (was previously asserted in the lane docs, not measured) |
| Remaining 10 nodes | 8 are covered by open candidates (#690 -> `test_m01_persistence` + `test_m05_files`; #693 -> the two `test_solspire_r1_governance_convergence` pins; #691 -> `test_solspire_r3_execution_runtime`; #698 -> `test_static_ingestion_idempotency`; #700 -> `test_identity_spine_w1` + `test_m02_reasomate_truth`) | OBSERVED |
| `ERROR tests/test_autonomy.py` | CE-01 `weaver.autonomy` module-vs-package collision, sovereign-reserved | BLOCKED (not agent-repairable) |
| `test_ais_w2_living_gate_grove_handoff::test_no_firebase_persistence_in_gate` | proxy-invalidation awaiting a sovereign decision (documented in-test); repairing it would loosen a persistence boundary | BLOCKED (governance) |
| Deployment build output observed | canonical origin is Render; the Vercel deployment URL is behind SSO | BLOCKED (provider auth) |
| Production acceptance | — | NOT CLAIMED (human authority) |

No node on `main` is both unowned and agent-repairable at this revision.

---

## 8. Reproduction

```bash
git worktree add --detach /tmp/wt681 04f2969b5269d5606f4a42abc7852c5b84d4b5ef
cd /tmp/wt681 && git merge --no-edit be751f9db372b635033a35cbee7c9e691e64c5f8   # one conflicted file
# keep both appended sections, then:
PYTHONPATH=$PWD python -m pytest tests/test_gate2_production_observation.py \
    tests/test_gate2_production_observation_ci_wiring.py -q                    # 64 passed
python scripts/gate2_production_observation.py                                 # marker-set oracle VERIFIED
```

Console-toolchain attribution:

```bash
cd web/arkadia_console && corepack pnpm install --frozen-lockfile
cd ../.. && PYTHONPATH=$PWD/archive/legacy_python \
  python -m pytest tests/test_mission_lifecycle_adapter_contract.py -q          # 10 passed
```

---

## 9. Non-effects

This change adds one evidence document. It modifies no product code, no test, no workflow, no governance document, no `api/main.py` line, and no deployment configuration. It asserts no merge, no deployment, and no acceptance.
