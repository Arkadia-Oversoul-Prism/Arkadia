# Cycle 08 — operational documents named a retired deployment host as production

**Contract:** `ARK-OPS-CONTINUOUS-001` (rev. 2026-11-22), cycle 08.
**Base:** `main` @ `bb19aabda34d59594615b0279a45e9cbd3d8204d` (2026-11-24).
**Authority:** implementation and evidence only. No merge, no deployment, no acceptance.
**Merge execution:** human-only under GOV-03.

---

## 1. The measured defect

`architecture/runtime_manifest.yaml` is the machine-readable record of ADR-016's single
canonical deployment. It declares:

```yaml
canonical_deployment_identity:
  service_url: https://arkadia-qzu4.onrender.com
runtime_verification:
  observed:
    - host: arkadia-qzu4.onrender.com   # canonical
    - host: arkadia-kw64.onrender.com   # status: legacy_noncanonical
    - host: arkadia-prism.vercel.app    # status: archived_noncanonical
```

`api/main.py` agrees: with `ENVIRONMENT=production` and no `CORS_ALLOWED_ORIGINS`, the
only allowed origin is `https://arkadia-qzu4.onrender.com` (`api/main.py:261`).

The operational documents did not agree. Measured before the repair, with
`python -m pytest tests/test_root_doc_deployment_host_currency.py -q`:

```
1 failed, 7 passed

.agents/memory/phase0-security.md:54  the only allowed origin is arkadia-kw64 (stated as a RULE)
.bootstrap/01_STATE.md:41             Backend LIVE: arkadia-kw64
.bootstrap/01_STATE.md:55             VITE_API_URL must be updated to arkadia-kw64 (Vercel)
.bootstrap/01_STATE.md:232            Production: LIVE at arkadia-kw64
CURRENT_STATE.md:72                   ... now point to arkadia-kw64
DEPLOYMENT_OPTIONS.md:146             ... references arkadia-n26k
MISSION.md:10                         | Backend | **LIVE** — arkadia-kw64 |
MISSION.md:30                         VITE_API_URL=arkadia-kw64
MISSION.md:93                         All production references point to arkadia-kw64
NEXT_AGENT.md:18                      Production proof (Gate A) | PASSING — arkadia-kw64
RECONCILED-BOUNDARY-MAP-01.md:40      The live host arkadia-kw64 ...
RECONCILED-BOUNDARY-MAP-01.md:299     Live host runs pre-hardening code (arkadia-kw64)
UPTIMEROBOT_SETUP.md:15               monitor URL: arkadia-kw64
arkadia-console-android/README.md:48  pinned to the live Oracle endpoint arkadia-kw64
sonata-android/README.md:73           backend URL (e.g. arkadia-kw64)
```

15 blocks across 11 documents. Two are more than stale prose:

* `MISSION.md:93` asserted "All production references point to
  `https://arkadia-kw64.onrender.com`". Measured:
  `git grep -l arkadia-qzu4.onrender.com | wc -l` → **85** tracked files name the
  canonical host. The claim was false about the repository it describes.
* `.agents/memory/phase0-security.md:54` stated the wrong origin as a **rule**. That
  file is agent memory: a rule that contradicts `api/main.py` misdirects the next agent
  rather than merely dating a paragraph.

### Runtime observation of both hostnames (recorded, not adopted)

Both hostnames answered `GET /api/version` on 2026-11-24 with
`source_revision: bb19aabda34d59594615b0279a45e9cbd3d8204d`, `revision_conflict: false`,
and `canonical_deployment: one_reconciled_deployment`. They are **not** the same
instance: `rndr-id` differed (`797a4af6-40fc-4b07` vs `00193e3c-aff3-4570`).

Under ADR-016 this is **drift to be recorded, not adopted**. An observed hostname is not
proof of canonical ownership. No action was taken on the second service; retiring it is
a human decision.

## 2. What was changed

| path | change |
|---|---|
| `tests/test_root_doc_deployment_host_currency.py` | new guard: every operational document must name the canonical origin (or mark a retired host historical) when it mentions one. Oracle derived from the manifest, never restated. |
| `tests/test_root_doc_deployment_host_ci_wiring.py` | new wiring guard: some workflow must execute the guard, select every input it reads, be dispatchable, and have a step that can fail. |
| `.github/workflows/root-doc-deployment-host.yml` | new gate. `paths:` names both guards, the workflow itself, the manifest, `**/*.md` and `*.md`. |
| `architecture/runtime_manifest.yaml` | `historical_targets` gains `arkadia-n26k.onrender.com`, with the evidence for that classification. |
| `MISSION.md`, `NEXT_AGENT.md`, `UPTIMEROBOT_SETUP.md`, `.bootstrap/01_STATE.md`, `.agents/memory/phase0-security.md`, `CURRENT_STATE.md`, `DEPLOYMENT_OPTIONS.md`, `RECONCILED-BOUNDARY-MAP-01.md`, `arkadia-console-android/README.md`, `sonata-android/README.md` | the retired-host claims now name the canonical origin, or are marked historical. |

### Design decisions worth stating

* **The oracle is derived.** `canonical_host()` and `retired_hosts()` read
  `architecture/runtime_manifest.yaml`. If the canonical origin moves, the guard follows
  it; a stale hardcoded list cannot make the check vacuous.
* **Unit of judgement is a paragraph, or a table row.** A per-line unit would force every
  wrapped line to repeat the canonical origin — the guard would dictate formatting. A
  table row is its own unit because a row *is* the claim; otherwise one correct row
  would vouch for a wrong one in the same table.
* **Scope is stated, not implied.** The domain is every tracked `*.md` outside
  `archive/` and `docs/` — the two record trees, which legitimately quote the host that
  was canonical when they were written (`docs/ARKADIA_CANONICAL_RUNTIME_CONTRACT.md` is a
  frozen Phase-4B proof). **Limitation:** a new *operational* guide placed under `docs/`
  would not be judged. Recorded rather than hidden.
* **Not repaired here:** `arkadia-console-android/app/build.gradle.kts:20` still defaults
  `ORACLE_BASE_URL` to the retired host, and `app/src/main/res/layout/activity_auth.xml:78`
  displays it. Changing a shipped application's default endpoint is a product decision,
  not a documentation correction; the README now states the fact and the decision is
  proposed, not taken.

## 3. Verification

| command | result |
|---|---|
| `pytest tests/test_root_doc_deployment_host_currency.py -q` | **8 passed** |
| `pytest tests/test_root_doc_deployment_host_ci_wiring.py -q` | **10 passed** |
| gate-integrity bundle (m02a, trigger coverage, workflow injection, verdict step integrity, collection continuation, baseline fingerprint, repo hygiene) | **401 passed** |
| `pytest tests/architecture -q` | **11 passed** |
| `python scripts/lane_state.py --check` | exit **0**; 4 doc-guard lanes consistent |
| `printf '<changed paths>' \| python scripts/cp10_mutation_boundary_policy.py --judge` | `Mutation boundary PASS`, exit **0** |
| `wc -l api/main.py` | **2597** (unchanged; budget 2600) |
| full suite `-q -rEf --continue-on-collection-errors` | `19 failed, 4275 passed, 22 skipped, 1 error`; node set **20**, ids-sha256 `d6101722…` = the recorded baseline at this SHA |

### Regression attribution

* **Failing/error node set is unchanged.** 20 nodes,
  `d6101722f624c0eedb48a957375f0b8abbef398f20e93e55e889dd8d9e0893ce`, identical to the
  recorded baseline for `main` @ `bb19aabd`. Zero nodes only on the branch.
* **The `+25 passed` is entirely new nodes.** `--collect-only` over `tests/`: main
  **4290**, branch **4315** → **+25**, which equals the passed delta. Decomposition:
  18 new nodes in the two guard files, and 7 that the generic workflow-scanning suites
  gain by construction from one new workflow file (`test_ci_gate_trigger_coverage` +3,
  `test_ci_suite_collection_continuation` +2, `test_workflow_injection_boundary` +1, and
  one more in the same class).

### Negative controls (live, against the real files)

| control | measured |
|---|---|
| revert `MISSION.md:10` to the pre-repair table row | `1 failed, 7 passed` — the guard names `MISSION.md:10` |
| restore byte-identically | `8 passed` |
| drop `architecture/runtime_manifest.yaml` from the workflow's `paths:` | `1 failed, 9 passed` — `{'root-doc-deployment-host.yml': ['architecture/runtime_manifest.yaml']}` |
| replace the executing step with `echo pytest …` | `1 failed, 9 passed` — no gate remains |
| restore byte-identically (`diff -q` against the pre-control copy) | `10 passed` |

## 4. Limitations

* Documentation + tests + one workflow. No application code, no `api/main.py` change, no
  governance text, no deployment configuration.
* The `docs/**` exclusion means an operational guide added under `docs/` escapes the
  guard. Stated in the guard's docstring.
* The production probes are source↔runtime consistency observations for two hostnames;
  they are **not** deployment acceptance, and a `200` is not proof of application
  correctness.
* `main` has no branch protection and no rulesets; that creates no merge authority.

## 5. Next authorized action

Human review. The advisory queue order is unchanged: `#681`/`#687` one-then-rebase the
other; the rest are `CLEAN` in any order. Proposed but **not** performed: re-point
`arkadia-console-android`'s `ORACLE_BASE_URL` default to the canonical origin, and retire
the second Render service serving the same revision — both are human decisions.

No agent merge, no push to `main`, no deployment, no acceptance.
