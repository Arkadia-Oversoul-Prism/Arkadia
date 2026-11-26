# ARK-OPS-CONTINUOUS-001 — Cycle 09

- **Contract:** `ARK-OPS-CONTINUOUS-001` rev `2026-11-22`
  (`docs/control-plane/openhands/hourly-weaver/2026-11-22-continuous-reconciliation-contract.md`,
  carried on PR #705's branch — not yet on `main`).
- **Cycle:** 09 — immediate execution + hourly continuation.
- **Observed:** 2026-11-24T15:06Z onward.
- **Authority:** `MERGE_AUTHORITY := NONE`, `DEPLOY_AUTHORITY := NONE`. No merge, no push to
  `main`, no deployment, no acceptance claimed.
- **Predecessors:** cycles 01-08 (`ark-ops-continuous-001-cycle-0{1..5}` on PR #705's branch).
- **Substantive change this cycle:** PR branch `gate-hygiene/arkana-stream-key-resolution-01`
  — evidence at `docs/control-plane/evidence/arkana-stream-key-resolution-01/EVIDENCE.md`.
  This entry is the ledger pointer plus the state record, not a duplicate of that evidence.

---

## 1. Reconstructed state

| fact | measured value | how |
|---|---|---|
| canonical `main` | `bb19aabda34d59594615b0279a45e9cbd3d8204d` | `GET /git/ref/heads/main`; local `HEAD` agrees |
| clone | full history (`is-shallow-repository` -> `false`) | `git rev-parse` |
| open PRs | **43**, every one a **draft**, every one `base: main` | `GET /pulls?state=open` (paginated) |
| branch protection | none (`/branches/main/protection` -> 404) | REST |
| rulesets | `0` | `GET /rulesets` |
| `api/main.py` | untouched this cycle | `git diff --stat` |

Merge authority is unaffected by any of the above: with no protection and no approvals, a
green `main` still confers no merge authority (GOV-03).

## 2. Production boundary

```
GET https://arkadia-qzu4.onrender.com/api/version  -> 200
  source_revision    bb19aabda34d59594615b0279a45e9cbd3d8204d
  revision_source    RENDER_GIT_COMMIT
  revision_conflict  false
```

Source <-> running revision is **VERIFIED** for this revision. That is necessary evidence of
consistency; it is **not** proof of application correctness and **not** deployment acceptance.

**Transient, recorded not promoted.** The first `/api/version` probe of this cycle produced no
bytes within the 30 s tool window (the request was still open); two immediate retries of the
same URL returned `200` with the body above. Classification: **UNKNOWN — a single unreproduced
cold-start read**, not a defect claim.

## 3. Baseline re-derived, not inherited

```console
$ pip install -q -r requirements.txt
$ cd web/arkadia_console && corepack pnpm install --frozen-lockfile   # exit 0
$ PYTHONPATH=$PWD/archive/legacy_python python -m pytest tests/ -q -rEf \
    --continue-on-collection-errors
9 failed, 4260 passed, 22 skipped, 6 warnings, 1 error in 302.78s (0:05:02)
```

**10** failing/error nodes. Every one is owned or reserved — none is a free gap:

| node | disposition |
|---|---|
| `tests/test_autonomy.py` (ERROR) | sovereign-reserved CE-01 (`weaver.autonomy` module-vs-package collision) |
| `test_ais_w2_living_gate_grove_handoff.py::test_no_firebase_persistence_in_gate` | F-01 — deliberately failing, awaiting a **sovereign** decision (re-pinning a persistence boundary is governance, not test hygiene) |
| `test_identity_spine_w1.py::test_node_entry_is_ais_signup_not_a_separate_diagnostic_route` | open PR **#700** |
| `test_m02_reasomate_truth.py::test_oracle_runtime_uses_the_shared_session_key` | open PR **#700** |
| `test_m01_persistence.py::test_deletion_propagates_to_durable_corpus` | open PR **#690** |
| `test_m05_files.py::test_update_file_supports_rename` | open PR **#690** |
| `test_solspire_r1_governance_convergence.py::test_r1_solspire_builders_delegate_to_weaver` | open PR **#693** |
| `test_solspire_r1_governance_convergence.py::test_r1_weaver_governance_is_canonical` | open PR **#693** |
| `test_solspire_r3_execution_runtime.py::test_runtime_is_explicitly_non_governed_and_blocks_mutation_tools` | open PR **#691** |
| `test_static_ingestion_idempotency.py::test_open_loop_content_is_checksum_stable_through_a_vault_round_trip` | open PR **#698** |

Ownership was derived by intersecting the failing node list with `GET /pulls/{n}/files` over
all 43 open PRs — not from prose.

## 4. Gap hunt: what was measured and ruled out

Each probe is recorded so a later cycle does not re-spend the effort.

| probe | measurement | classification |
|---|---|---|
| console `api.*` call sites vs `app.openapi()` | 48 distinct paths; 2 unserved — `/api/codex/categories` (absent, documented in `SpiralCodexPanel.tsx` + pinned by `test_console_spiral_codex_contract.py`) and `/api/job/…` (a template-literal false positive; `/api/job/{job_id}` **is** served) | no gap; already guarded |
| console method/path pairs | 11 method-bearing call sites, 0 genuine mismatches (one path-absent hit was a `${…}` template split, and `/api/job/{job_id}` **is** served) | no gap |
| route ordering vs the SPA catch-all | 64 routes; `/{path:path}` at index 63; **0** routes after it | no gap (no shadowed API route) |
| `NotYetWired` `contract=` strings | all served routes, but each names a capability the *component* does not mount (e.g. session transition), with explicit copy | honest disclosure, not a defect |
| console build | `tsc --noEmit` + `vite build` -> exit 0, 170 modules | no gap |
| `pyflakes` over all tracked non-archive Python | 1 undefined name (owned by PR #720), 1 dead key fallback (**repaired this cycle**), rest are unused locals/imports | one free defect found |

## 5. Substantive change

`api/arkana_stream_routes.py` imported `GOOGLE_API_KEY` from `api.main` and assigned it in an
`except` block, where it is a **dead local** — code that reads as an environment-key fallback
and is not one. Removed, with the error path now logging why per-user resolution was skipped.
The fallback that actually runs (`api.key_pool.acquire_key()`, then the env key) is unchanged.

`tests/test_arkana_stream_key_resolution.py` (7 tests) pins the served route, the absence of a
dead key fallback, the pool contract, and — behaviourally, with only the HTTP boundary patched
— that a provider `429` cools the charged key and is not reported as a success. Two negative
controls and one polarity control prove the detectors bite.

Verification: new guard **7 passed**; arkana + pool suites **51 passed**; gate-integrity bundle
+ `tests/architecture` **292 passed**; `py_compile` exit 0; CP10 boundary judge PASS; console
build exit 0. Full details in the evidence file named above.

## 6. Next-action block

- **Current state:** `main` `bb19aabd`, 43 open draft PRs, production serving `bb19aabd`
  (`revision_conflict false`). Baseline 10 failing/error nodes, all owned or reserved.
- **Evidence:** §1-§5 here; `docs/control-plane/evidence/arkana-stream-key-resolution-01/EVIDENCE.md`.
- **Blockers (unchanged, human-owned):**
  1. **F-01** (`test_ais_w2_living_gate_grove_handoff.py::test_no_firebase_persistence_in_gate`)
     needs a sovereign decision on whether a tab-scoped `sessionStorage` diagnostic handoff is
     inside the persistence boundary. An agent must not re-pin it.
  2. **CE-01** (`tests/test_autonomy.py`) is the `weaver.autonomy` module-vs-package collision,
     reserved to the sovereign.
  3. 43 open PRs await human review/merge; under GOV-03 no agent may merge, and a merge is a
     release event because `main` is connected to production.
- **Authorized next action:** review the new draft PR; if unmerged, the next cycle should pick a
  fresh bounded gap from a measurement (not from a queue count) and re-derive the baseline
  before claiming a delta.
- **Forbidden:** merging, pushing to `main`, deploying, re-pinning F-01, repairing CE-01,
  widening the CP10 allowlist to make a gate pass.
- **Completion condition for this cycle:** the repair and its guard are pushed on an isolated
  branch with evidence recorded; `main` is untouched; the failing-node set is unchanged.
