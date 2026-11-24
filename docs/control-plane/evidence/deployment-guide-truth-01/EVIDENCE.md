# Deployment guide truth — `DEPLOYMENT_GUIDE.md` described an application that does not exist

- **Contract:** `ARK-OPS-CONTINUOUS-001` (cycle 05)
- **Branch:** `docs/deployment-guide-truth-01`
- **Base:** `main` = `bb19aabda34d59594615b0279a45e9cbd3d8204d`
- **Observed:** 2026-11-24T00:07Z onward
- **Merge / deploy authority:** none. This record claims no merge, no deployment and no acceptance.

## 1. Reconstructed state (measured, not inherited)

| fact | measured |
|---|---|
| canonical `main` | `bb19aabda34d59594615b0279a45e9cbd3d8204d` (unchanged during the cycle) |
| production `/api/version` | `200`, 643 B, `source_revision` = `bb19aabd…`, `revision_source` = `RENDER_GIT_COMMIT`, `revision_conflict: false` |
| `main` check-runs | `boot-syntax`, `console-contract`, `engineering-scheduler` (×2), `posture-currency`, `test`, `Full-history secret scan` → all `success`; `weaver_evolution` `skipped` (×5) |
| open PRs | **31**, all drafts, all `base: main` |
| composition (pairwise) | **465** pairs judged: **464 `CLEAN`**, **1 `CONFLICT`** (`681 × 687`, `tests/test_gate2_production_observation.py`), **0 `UNPROVABLE`** |
| full suite | `19 failed, 4250 passed, 22 skipped, 1 error` in 287 s |
| failing/error node set | **20** nodes; outcomes `sha256 8d70e46e6f076049cacd8bdf16feeb42c6c078377d9d350e6bfbe1a8de4beceb`; ids `sha256 d6101722f624c0eedb48a957375f0b8abbef398f20e93e55e889dd8d9e0893ce` |

Both published fingerprints reproduce exactly at this SHA, so the baseline is unchanged and the
queue's single conflict is the pair `#703` adjudicates.

The 20 nodes remain fully classified and **none is an unowned, non-reserved defect**: 10
environment-only (`tests/test_mission_lifecycle_adapter_contract.py`, missing
`web/arkadia_console/node_modules/typescript`), 1 sovereign-reserved CE-01 (`ERROR
tests/test_autonomy.py`), 1 sovereign-reserved F-01 (`test_ais_w2_living_gate_grove_handoff.py`), and
8 repaired by open PRs `#690`, `#691`, `#693`, `#698`, `#700`.

Note the first `/api/version` probe timed out at 25 s and returned `200` in **2.0 s** on retry: a
cold start, not an outage. Recorded because a timeout reads as `UNREACHABLE` if it is not retried.

## 2. The defect

`DEPLOYMENT_GUIDE.md` is the repository's top-level deployment instruction. Measured against the
tree, it described a different application:

```
$ for f in arkana_app.py codex_brain.py arkadia_drive_sync.py \
           arkadia_console.py models.py db.py; do
    printf '%-24s ' "$f"; test -e "$f" && echo EXISTS || echo MISSING; done
arkana_app.py            MISSING
codex_brain.py           MISSING
arkadia_drive_sync.py    MISSING
arkadia_console.py       MISSING
models.py                MISSING
db.py                    MISSING
```

Six of the seven "Core Components Built" do not exist at any path. (`arkadia_console.py` survives
only as `archive/legacy_python/arkadia_console.py`.) The required-environment block named
`ARKADIA_FOLDER_ID` and `GDRIVE_SERVICE_ACCOUNT_JSON`, and

```
$ grep -rn "ARKADIA_FOLDER_ID\|GDRIVE_SERVICE_ACCOUNT_JSON" \
        --include=*.py --include=*.json --include=*.sh . | grep -v archive/
(no match)
```

no module reads either. Deploy instructions pointed at the placeholder host
`https://your-app.onrender.com`, and the closing line asserted the system was "completely
functional and ready for immediate deployment" — an unconditional acceptance claim, which
`docs/adr/ADR-016-single-canonical-deployment.md` reserves to a human.

A reader following that guide cannot deploy Arkadia; an agent reading it would describe a runtime
that does not exist. No open PR touched the file.

## 3. The repair (2 paths)

| path | change |
|---|---|
| `DEPLOYMENT_GUIDE.md` | Rewritten against the actual deployment: `web/arkadia_console` + `api/main.py` + `api/frontend_routes.py` + `entrypoint.sh`, built by the root `Dockerfile`; the canonical Render origin; `GET /api/version` as the revision probe; the environment variables the code actually reads; the verified route table retained and `/api/version` added; explicit "deployment ≠ verification ≠ acceptance" and "no second canonical deployment" statements. |
| `tests/test_deployment_guide_truth.py` | Guard (18 nodes): every repository path the guide names in an inline code span must resolve on disk; the guide must name the canonical origin and the revision probe; it must present no second deployment as production and must not claim production acceptance. |

The guard is placed in the **derived console-contract domain** (`scripts/console_contract_domain.py`,
74 → **75** guards) because the guide's central claim is *which* application is deployed. That
domain is executed by a **blocking** step in `prism-console-contract.yml`, whose `paths` filter
selects `tests/**` — so the guard is judged, not merely executed.

## 4. Verification

```
pytest tests/test_deployment_guide_truth.py -q
→ 18 passed
```

**Live negative control on the real artifact** — restore `main`'s guide, re-run, restore:

```
git show main:DEPLOYMENT_GUIDE.md > DEPLOYMENT_GUIDE.md
pytest tests/test_deployment_guide_truth.py -q
→ 4 failed, 14 passed
   test_every_repository_path_named_by_the_guide_exists
   test_guide_names_the_canonical_origin_and_the_revision_probe
   test_guide_presents_no_second_deployment_as_production
   test_guide_does_not_claim_production_acceptance
restore → 18 passed
```

So the detector reddens on the defect it exists to catch and is silent on the repair.

```
python scripts/console_contract_domain.py | grep -c .
→ 75            (was 74; the new guard is admitted)

python -m pytest -q --collect-only $(python scripts/console_contract_domain.py)
→ 1306 tests collected            (no collection error)

python -m pytest -q -rEf --continue-on-collection-errors $(python scripts/console_contract_domain.py)
→ 10 failed, 1292 passed, 4 skipped in 49 s
   the 10 failures are exactly tests/test_mission_lifecycle_adapter_contract.py
   (environment-only: no web/arkadia_console/node_modules/typescript);
   deployment_guide does not appear in the failure list

pytest tests/test_prism_console_ci_wiring.py tests/test_deployment_guide_truth.py \
       tests/test_gate_filter_selection.py tests/test_ci_gate_trigger_coverage.py \
       tests/test_m02a_ci_gate_integrity.py tests/architecture tests/test_boot_syntax_boundary.py
→ 294 passed

printf 'DEPLOYMENT_GUIDE.md\ntests/test_deployment_guide_truth.py\n' \
  | python scripts/cp10_mutation_boundary_policy.py --judge
→ Mutation boundary PASS   (exit 0)

python -m py_compile api/main.py tests/test_deployment_guide_truth.py
→ OK
```

The full-suite baseline was measured **once** on this pulse (`main` @ `bb19aabd`) and reproduces the
recorded node set exactly; the branch is attributed by a targeted run, not a second full pass.

## 5. Limitations

- Documentation + one test file. No production code, no workflow, no governance text, no
  `api/main.py` line, no deployment configuration changed.
- The production observation is source↔runtime **consistency** at one instant. It is not proof of
  correct application behaviour and not acceptance.
- `DEPLOYMENT_OPTIONS.md` was read and left alone: its platform-comparison framing is historical, and
  its `/api/heartbeat` health-check reference is still correct (`api/main.py` serves it).
- The 10 environment-only nodes stay failing on a tree without the console toolchain. They pass in CI,
  which provisions it; changing them to skips would be a separate decision and would collide with
  `#693`, which owns the recorded baseline set and its four published fingerprint documents.
- `scripts/prism_coherence_check.py` still exits 1 with structural findings and scans the working
  tree (it even reports `.pytest_cache/README.md`). Its scope decision is sovereign and remains
  recorded, not repaired.

## 6. Next authorized action

Human review of the 31-PR queue. Advisory composition order unchanged: `#681`/`#687`
one-then-rebase-the-other; the other 464 pairs are `CLEAN` in any order. No agent merge, no push to
`main`, no deployment, no acceptance.
