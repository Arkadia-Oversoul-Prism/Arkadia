# ARK-OPS-CONTINUOUS-001 — Cycle 03

- **Contract:** `ARK-OPS-CONTINUOUS-001` rev `2026-11-22`
  (`docs/control-plane/openhands/hourly-weaver/2026-11-22-continuous-reconciliation-contract.md`)
- **Cycle:** 03 — immediate execution + hourly continuation
- **Observed:** 2026-11-23T15:05Z → 15:40Z
- **Authority:** `MERGE_AUTHORITY := NONE`, `DEPLOY_AUTHORITY := NONE`. No merge, no push to
  `main`, no deployment, no acceptance claimed.
- **Predecessors:** `ark-ops-continuous-001-cycle-01`, `…-cycle-02`
- **Nature of this change:** documentation only. No product code, test, workflow, governance
  text, `api/main.py` line or deployment configuration is modified.

---

## 1. Reconstructed state

| fact | measured value | how |
|---|---|---|
| canonical `main` | `bb19aabda34d59594615b0279a45e9cbd3d8204d` | `GET /repos/…/commits/main`; local `HEAD` agrees |
| clone | full history (`is-shallow-repository` → `false`) | `git rev-parse` |
| branch protection | none (`/branches/main/protection` → 404 "Branch not protected") | REST |
| rulesets | `0` | `GET /rulesets` |
| `main` executed checks | `boot-syntax`, `console-contract`, `engineering-scheduler`, `posture-currency`, `test`, `Full-history secret scan` → all `success`; `weaver_evolution` → `skipped` (×4) | `commits/bb19aabd…/check-runs` |
| open PRs | **28**, every one a **draft**, every one `base: main`, every one `MERGEABLE` | `GET /pulls?state=open` |
| obsolete open PRs | **0** — no open head is an ancestor of `main` | `git merge-base --is-ancestor refs/pr/<n> main`, all 28 |
| reviews | `reviewDecision: none`, 0 approvals across the queue | `gh pr list --json reviewDecision` |

Merge authority is unaffected by any of the above: with 0 approvals and no protection, a green
`main` still confers no merge authority (GOV-03). This cycle executed no merge and pushed to no
`main`.

## 2. Production boundary

```
GET https://arkadia-qzu4.onrender.com/api/version  → 200
  source_revision   bb19aabda34d59594615b0279a45e9cbd3d8204d
  revision_source   RENDER_GIT_COMMIT
  revision_conflict false
GET https://arkadia-qzu4.onrender.com/health       → 200 {"status":"radiant",…}
```

**Source ↔ running revision is VERIFIED** for this revision. That is necessary evidence of
consistency; it is **not** proof of application correctness and **not** deployment acceptance.

### 2.1 Served artifact is the active console (new this cycle)

Cycles 01–02 read only `/api/version` and `/health`. This cycle read the served document with a
browser `Accept` header (the canonical origin returns the 40-byte liveness JSON without it — the
documented SPA-mode behaviour, not a fault):

```
GET /  (Accept: text/html,application/xhtml+xml,…) → 200, 1256 B
  <title>ARKADIA</title>
  <script type="module" src="/assets/index-CYGHeCpJ.js">
  <link rel="stylesheet" href="/assets/index-BJojPKi_.css">
GET /assets/index-CYGHeCpJ.js → 200, 426 232 B
```

Marker set (fixed-string `grep`, occurrences in the served bundle):

| marker | occurrences | meaning |
|---|---|---|
| `Surface scaffolded` | 1 | the **console's** `NotYetWired` copy is in the artifact |
| `opportunity-radar` | 2 | the console's Opportunity Radar surface is in the artifact |
| `Engineering Lab` | 5 | the active foundation is named in the artifact |
| `PrismInteriorShell` | **0** | the archived Prism shell is absent |
| `public_prism` | **0** | the archived Prism source path is absent |
| `Arkadia Oversoul Prism` | **0** | the archived Prism identity string is absent |

Present/absent contrast only; magnitudes are reproducibility detail, not a parity oracle. This
is an observation of the served artifact, **not** a deployment-identity or acceptance claim.

### 2.2 Advertised endpoints are healthy anonymously (new this cycle)

Every entry of the console's single registry (`web/arkadia_console/src/lib/endpoints.ts`, **45**
entries) was resolved against the deployed `/openapi.json` (**300** paths) and, where `GET` is
served, probed anonymously:

- **45 / 45** advertised paths resolve to a deployed operation (0 invented).
- **40** `GET` probes: **0** `5xx`, **0** unexpected `404`.
  `200` for public reads, `401` for protected reads (the expected boundary).
- **5** entries are `POST`-only by design (`arkanaResonance`, `arkanaResonanceStream`,
  `knowledgeSearch`, `tts`); no method mismatch.

### 2.3 Inline console literals are served

A sweep of `web/arkadia_console/src` outside `endpoints.ts` (excluding tests and doc comments)
found **15** distinct inline API paths. **14** resolve to a deployed operation. The single
exception, `/api/codex/categories`, is *not served* and its own file
(`components/novaNet/SpiralCodexPanel.tsx`) states that explicitly — an honest disclosure, not a
defect.

## 3. Verification gates executed on `main`

| surface | result |
|---|---|
| `tests/architecture` | **11 passed** |
| gate-integrity bundle (`test_m02a_ci_gate_integrity`, `test_ci_gate_trigger_coverage`, `test_boot_syntax_boundary`, `test_workflow_injection_boundary`, `test_ci_verdict_step_integrity`) | **259 passed** |
| lane currency, offline | `scripts/lane_state.py --check` → exit **0**; 4 guarded lanes consistent |
| lane currency, live | `scripts/lane_state.py --check --verify-live` → exit **0**, `4 PR(s) read`, `doc-guard lanes ['1','2','3','4']`, `deferred []` |
| console contract domain | `scripts/console_contract_domain.py` → **74** guards (derived, not restated) |
| console endpoint registry guard | `tests/test_console_endpoint_registry_contract.py` → **21 passed**; `RECORDED_ADVERTISED_DRIFT` empty |
| `AGENTS.md` encoding audit | `scripts/agents_md_encoding_audit.py` → exit **1**; Cyrillic `0 → 0`; oracle `6c43218a48a4` `alterations=0`, `reproduced=True` |

The `base main: b842892b` line printed by `lane_state.py` is **not** staleness: the oracle's
criterion is "a guarded lane doc changed after the snapshot was last written", and no guarded doc
moved in that window.

## 4. Full suite and classification of every failing node

```
PYTHONPATH=$PWD/archive/legacy_python python -m pytest tests/ -q -rEf --continue-on-collection-errors
→ 19 failed, 4250 passed, 22 skipped, 1 error in 286.79s
```

Sorted `FAILED`/`ERROR` node ids joined with `\n` **plus a trailing newline** hash to
`8d70e46e6f076049cacd8bdf16feeb42c6c078377d9d350e6bfbe1a8de4beceb` — **20 nodes**, identical to
the recorded `main` baseline. The convention is stated because cycle 02 recorded `d6101722…` over
the same set (a different join/serialisation, not a delta). **No new suite drift this cycle.**

| node(s) | count | classification |
|---|---|---|
| `ERROR tests/test_autonomy.py` | 1 | **sovereign-reserved** — CE-01 `weaver.autonomy` module-vs-package collision |
| `tests/test_ais_w2_living_gate_grove_handoff.py::test_no_firebase_persistence_in_gate` | 1 | **sovereign-reserved** — FINDING F-01 persistence boundary |
| `tests/test_identity_spine_w1.py::…`, `tests/test_m02_reasomate_truth.py::…` | 2 | repaired by open **#700** |
| `tests/test_m01_persistence.py::…`, `tests/test_m05_files.py::…` | 2 | repaired by open **#690** |
| `tests/test_solspire_r1_governance_convergence.py::…` | 2 | repaired by open **#693** |
| `tests/test_solspire_r3_execution_runtime.py::…` | 1 | repaired by open **#691** |
| `tests/test_static_ingestion_idempotency.py::…` | 1 | repaired by open **#698** |
| `tests/test_mission_lifecycle_adapter_contract.py::…` | 9 | **environment-only** — needs `web/arkadia_console/node_modules/typescript`, absent in this sandbox; `prism-console-contract.yml` provisions it before running |

No unclaimed, non-reserved defect is left in the failing set.

## 5. Composition of the queue, re-measured at today's heads

Cycle 02 measured **378** pairs (28 PRs). `#681` moved after that measurement
(`84255528`, 14:22Z), so the matrix was re-run rather than inherited:

```console
$ git fetch origin '+refs/pull/*/head:refs/pr/*'
$ python /tmp/opi694.py --conflicts --git-repo . \
    $(for n in 675 679 680 681 682 683 684 685 686 687 688 689 690 691 \
               692 693 694 695 696 697 698 699 700 701 702 703 704 705; do
        printf -- '--ref %s=refs/pr/%s ' $n $n; done)
378 pair(s) judged
  CLEAN 377 · CONFLICT 1 · UNPROVABLE 0
  681 x 687   CONFLICT   tests/test_gate2_production_observation.py
```

(The oracle is `scripts/open_pr_inventory.py --conflicts`, read from open **#694**'s head — it is
not yet on `main`. Read-only: tree merges in a temp worktree, no mutation.)

Unchanged: the single conflict is the pair **#703** exists to adjudicate, and it persists at
`#681`'s new head. Textual composition is not semantic compatibility; #703 carries the semantic
measurement.

Non-passing checks on the eight `UNSTABLE` PRs (`#681`, `#689`, `#690`, `#693`, `#696`, `#699`,
`#700`, `#703`) were re-listed this cycle: every one belongs to the external N-ATLAS family
(`native-arkadia-golden-workflow`, `beta-beta-0{1,2}-*`, `bundle-beta-evidence`). None is a
function of the PR's own tree, and `main` itself carries no such red.

## 6. Classified finding — not repaired (bounded scope)

`scripts/prism_coherence_check.py` **exits 1 on `main`** with **31** findings, and is executed by
**no** workflow and covered by **no** test (`grep -rn prism_coherence_check .github/ tests/` → 0).
Its domain is *every* `README.md` in the repository, including `archive/`, `research/`, `vault/`
(gitignored runtime output) and retired trees, so its findings are structural rather than drift —
e.g. `research/oversoul_prism_*/README.md` are historical records that will never carry the
required identity markers.

Repairing it therefore requires a **scope decision** (which READMEs are "documented surfaces"?),
and narrowing a guard to make it green is exactly the move the contract forbids. **Proposed, not
executed**; the owner is the sovereign. Recorded here so a later cycle does not re-derive it as a
new discovery.

## 7. Why this cycle did not open a new code PR

Bounded reconnaissance over the classes that have produced repairs in this repository found no
unowned, implementable defect:

| class | measured state |
|---|---|
| failing/error nodes | 20, all classified; every non-reserved one owned by an open PR (§4) |
| advertised-but-unserved console contracts | **0** of 45 registry entries; inline sweep 14/15 served, the 15th honestly disclosed (§2.2–2.3) |
| production 5xx / unexpected 404 | **0** across 40 anonymous `GET` probes (§2.2) |
| `steps.<id>.outcome` read inside a `run:` block | only `sg-02-fe-2-v.yml`, owned by open **#695** |
| test files executed by no workflow | **0** of 341 |
| obsolete open PRs | **0** |
| composition conflicts | 1, owned by **#703** |

The queue's blocker is **human merge throughput across 28 drafts**, not outstanding repair work.
Opening a 29th code PR would add review load without closing a verified gap, which
`ARK-OPS-CONTINUOUS-001` §0.1 explicitly forbids.

## 8. Next-action block

**Current state.** `main` = `bb19aabda34d59594615b0279a45e9cbd3d8204d`; production
`source_revision` identical, `revision_conflict: false`, served artifact identified as the active
console. `main`'s executed checks green. Full-suite failing set = recorded baseline (20 nodes,
`8d70e46e…`), fully classified. **28** open drafts, all `MERGEABLE`, 0 obsolete, 0 attributable CI
failures. Composition: 377/378 pairs `CLEAN`; the one `CONFLICT` (`#681 × #687`) owned by `#703`.

**Evidence.** Sections 1–7; every command above is reproducible as written.

**Blockers.** (a) Merge execution is human-only (GOV-03); 28 drafts await human review.
(b) `beta-*` / `native-arkadia-golden-workflow` results are governed by an external provider and
cannot be made deterministic from this repository. (c) CE-01 and FINDING F-01 are reserved to the
sovereign. (d) `scripts/prism_coherence_check.py`'s scope is a sovereign decision (§6).

**Authorized next action.** A human reviews the queue for merge; the advisory order is unchanged —
`#681`/`#687` one-then-rebase-the-other (keep both appended sections), everything else in any
order. On a later cycle an agent may re-run the 378-pair matrix as the queue moves, verify a
specific PR against the then-current `main`, or implement a newly measured, non-reserved defect.

**Forbidden.** Merging; pushing to `main`; force-pushing; deploying; bypassing protection or
required checks; weakening a guard to manufacture green; repairing CE-01 or F-01 without a
sovereign decision; opening a PR whose only product is activity.

**Completion condition.** This cycle is complete when this evidence is reviewable on the existing
contract-record branch, with `main` unmodified and no merge, deployment or acceptance claimed.
