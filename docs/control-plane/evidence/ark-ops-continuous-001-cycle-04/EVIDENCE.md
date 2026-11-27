# ARK-OPS-CONTINUOUS-001 — Cycle 04

- **Contract:** `ARK-OPS-CONTINUOUS-001` rev `2026-11-22`
  (`docs/control-plane/openhands/hourly-weaver/2026-11-22-continuous-reconciliation-contract.md`)
- **Cycle:** 04 — immediate execution + hourly continuation
- **Observed:** 2026-11-23T16:06Z → 16:52Z
- **Authority:** `MERGE_AUTHORITY := NONE`, `DEPLOY_AUTHORITY := NONE`. No merge, no push to
  `main`, no deployment, no acceptance claimed.
- **Predecessors:** `ark-ops-continuous-001-cycle-01`, `…-cycle-02`, `…-cycle-03`
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
| open PRs | **28**, every one a **draft**, every one `base: main`, every one `MERGEABLE` | `GET /pulls?state=open` |
| obsolete open PRs | **0** | no open head is an ancestor of `main` |
| reviews | `reviewDecision: none`, 0 approvals across the queue | `gh pr list --json reviewDecision` |

Merge authority is unaffected by any of the above: with 0 approvals and no protection, a green
`main` still confers no merge authority (GOV-03). This cycle executed no merge and pushed to no
`main`.

## 2. Production boundary

```
GET https://arkadia-qzu4.onrender.com/api/version  → 200, 643 B
  source_revision    bb19aabda34d59594615b0279a45e9cbd3d8204d
  revision_source    RENDER_GIT_COMMIT
  revision_conflict  false
  ARKADIA_SOURCE_REVISION  {"status":"absent","value":null}
GET https://arkadia-qzu4.onrender.com/health       → 200 {"status":"radiant","path":"/health"}
```

**Source ↔ running revision is VERIFIED** for this revision. That is necessary evidence of
consistency; it is **not** proof of application correctness and **not** deployment acceptance.

**One unreproduced transient, recorded rather than promoted.** The first `/api/version` probe of
this cycle returned an **empty body** (the command did not request a status code, so the HTTP
status of that read is unknown), while the `/health` probe in the same command succeeded. Two
subsequent probes, each with `-w "status=%{http_code} size=%{size_download}"`, returned
**200 / 643 B** and the full document, identical between runs. Classification: **UNKNOWN — a
single unreproduced read**, not a defect claim and not a boundary failure. It is recorded because
a silent empty body is the shape a real regression would take, and a later cycle should be able to
tell that it was seen once and did not reproduce.

## 3. Verification gates executed on `main`

| surface | result |
|---|---|
| `tests/architecture` | **11 passed** |
| lane currency, offline | `scripts/lane_state.py --check` → exit **0** |
| lane currency, live | `scripts/lane_state.py --check --verify-live` → exit **0**, `4 PR(s) read`, `doc-guard lanes ['1','2','3','4']`, `deferred []` |
| CP10 mutation boundary | new evidence path judged **PASS** (`… --judge` → exit 0) |
| `api/main.py` size | **2597** lines (budget 2600 → **3** lines headroom) |

## 4. Full suite and the two recorded fingerprints

```
PYTHONPATH=$PWD/archive/legacy_python python -m pytest tests/ -q -rEf --continue-on-collection-errors
→ 19 failed, 4250 passed, 22 skipped, 6 warnings, 1 error in 290.59s
```

The failing/error set is **20 nodes**, identical in membership to the recorded `main` baseline.
The repository carries **two** published fingerprints for this one set, and this cycle resolved
*why* they differ — the convention, not the tree:

| convention | sha256 | value recorded by |
|---|---|---|
| sorted raw summary lines **including** the `FAILED ` / `ERROR ` prefix, `"\n".join(...)+"\n"` | `8d70e46e6f076049cacd8bdf16feeb42c6c078377d9d350e6bfbe1a8de4beceb` | cycle 03 |
| same 20 nodes, prefix **stripped**, `"\n".join(...)+"\n"` | `d6101722f624c0eedb48a957375f0b8abbef398f20e93e55e889dd8d9e0893ce` | cycle 02 / this cycle |

Both are correct over the same set; neither is drift. Reproduce either by choosing the
serialisation. Other conventions do **not** reproduce them (`sorted, no trailing newline` →
`4c40c228…`; `space-joined` → `8b2350ee…`), which is what makes the pair attributable rather than
arbitrary.

### 4.1 Classification of every failing node

| node(s) | count | classification |
|---|---|---|
| `ERROR tests/test_autonomy.py` | 1 | **sovereign-reserved** — CE-01 `weaver.autonomy` module-vs-package collision |
| `tests/test_ais_w2_living_gate_grove_handoff.py::test_no_firebase_persistence_in_gate` | 1 | **sovereign-reserved** — FINDING F-01 persistence boundary |
| `tests/test_identity_spine_w1.py::…`, `tests/test_m02_reasomate_truth.py::…` | 2 | repaired by open **#700** |
| `tests/test_m01_persistence.py::…`, `tests/test_m05_files.py::…` | 2 | repaired by open **#690** |
| `tests/test_solspire_r1_governance_convergence.py::…` | 2 | repaired by open **#693** |
| `tests/test_solspire_r3_execution_runtime.py::…` | 1 | repaired by open **#691** |
| `tests/test_static_ingestion_idempotency.py::…` | 1 | repaired by open **#698** |
| `tests/test_mission_lifecycle_adapter_contract.py::…` | **10** | **environment-only** — needs `web/arkadia_console/node_modules/typescript`, absent in this sandbox; `prism-console-contract.yml` provisions it before running |

**Correction to cycle 03's record.** Cycle 03's table listed **9** mission-lifecycle nodes and its
rows summed to **19** while the stated set was **20**. Measured this cycle: the file contributes
**10** nodes, and `2+2+2+1+1+10+1+1 = 20`. The total was right; the per-row count was wrong. The
10-node figure supersedes the 9-node figure.

No unclaimed, non-reserved defect is left in the failing set.

## 5. Composition of the queue, re-measured at today's heads

```console
$ git fetch origin '+refs/pull/*/head:refs/pr/*'
$ python /tmp/opi.py --conflicts --git-repo . \
    $(for n in 675 679 680 681 682 683 684 685 686 687 688 689 690 691 \
               692 693 694 695 696 697 698 699 700 701 702 703 704 705; do
        printf -- '--ref %s=refs/pr/%s ' $n $n; done)
378 pair(s) judged
  CLEAN 377 · CONFLICT 1 · UNPROVABLE 0
  681 x 687   CONFLICT   tests/test_gate2_production_observation.py
```

(`scripts/open_pr_inventory.py` is read from open **#694**'s head; it is not yet on `main`.
Read-only: tree merges in a temp worktree, no mutation. The labels above resolve to **28** distinct
open PR numbers, and `C(28,2) = 378` is the row count — 676/677/678 are commits on `main`, not
PRs.)

Unchanged from cycle 03: the single textual conflict is the pair **#703** exists to adjudicate.
Textual composition is not semantic compatibility; #703 carries the semantic measurement.

### 5.1 `api/main.py` budget under composition

The budget is the tightest it has been, so it was measured per-tree rather than assumed:

| tree | `api/main.py` lines | verdict |
|---|---|---|
| `main` | **2597** | within 2600 (3 lines headroom) |
| **#701** (the only open PR touching the file) | **2593** (`15 insertions, 19 deletions`) | within budget — composition does **not** breach it |

**#696** already repairs the stale docstring in `tests/architecture/test_layer_boundaries.py`
that read `Current size: ~2506 lines. Budget: 2600 (headroom for legitimate additions)` while the
file measured 2597 — a 3-line, not 94-line, headroom. It cites the same measurement this cycle
made. That defect is therefore **owned**, and this cycle did not duplicate it.

## 6. Bounded reconnaissance — one class measured and confirmed *owned*

Reconnaissance targeted the class the queue has been closing: a console surface telling the user a
backend contract is missing when the backend serves it. Every `NotYetWired` panel's `contract=`
literal was resolved against the live route table (`app.openapi()["paths"]`, 300 paths):

| panel | advertised contract | served? |
|---|---|---|
| `pages/SolSpirePage.tsx:113` | `/solspire/enterprise/workspaces` | **SERVED** |
| `pages/SolSpirePage.tsx:120` | `/solspire/voice/events` | **SERVED** |
| `pages/SolSpirePage.tsx:128` | `/solspire/proposals` | **SERVED** |
| `pages/SolSpirePage.tsx:132` | `/solspire/workevents` | **SERVED** |
| `pages/WeaverPage.tsx:23` | `/api/lab/engineering/sessions/{id}/execute` | **SERVED** as `…/{session_id}/execute` |
| `components/lab/LabCapabilityDisclosure.tsx:11` | `/api/lab/engineering/sessions/{session_id}/transition` | **SERVED** |

Six panels: five exact path matches and one served under a different parameter name. **The
per-panel `note` copy is already honest in every case** — each states "… are served, but the
console has no X projection yet". The only false claim was the **shared eyebrow**
(`Surface scaffolded · contract not yet wired`) and its `Expected contract:` label, which assert
the *contract* is absent for all six.

**This is owned, not a gap to fill.** Open **#685** replaces that shared copy with
`Surface scaffolded · interface not built` / `Backend contract:` and adds the class guard
`test_shared_placeholder_does_not_call_a_served_contract_unwired` to
`tests/test_console_endpoint_registry_contract.py`; **#692** wires the served proposal ledger in
`SolSpirePage.tsx`. Verified this cycle at **#685**'s own head:

```console
$ git worktree add --detach /tmp/wt685 refs/pr/685
$ pytest tests/test_console_endpoint_registry_contract.py -q
22 passed in 1.71s
```

and its guard **bites** — reverting only the shared copy on that same tree:

```console
$ sed -i 's/Surface scaffolded · interface not built/Surface scaffolded · contract not yet wired/' \
    web/arkadia_console/src/components/ui.tsx
$ pytest tests/test_console_endpoint_registry_contract.py -q
1 failed, 21 passed            # test_shared_placeholder_does_not_call_a_served_contract_unwired
$ git checkout -- web/arkadia_console/src/components/ui.tsx
$ pytest tests/test_console_endpoint_registry_contract.py -q
22 passed in 1.31s
```

A live negative control on the real file, restored byte-identically. Opening a second PR for this
class would duplicate reviewed work and add review load, which §0.1 forbids.

## 7. Why this cycle did not open a new code PR

| class probed this cycle | measured state |
|---|---|
| failing/error nodes | 20, all classified; every non-reserved one owned by an open PR (§4.1) |
| `NotYetWired` panels advertising a served contract | **6**, shared copy owned by **#685** (+ #692); guard verified live (§6) |
| stale `api/main.py` budget docstring | owned by **#696**; composition measured, not breached (§5.1) |
| scripts executed by no workflow | 14; each is read-only/operator-only or already classified — `prism_coherence_check.py` needs a sovereign scope decision (cycle 03 §6); `validate_oversoul_prism_12x12_registry.py` exits **0**; `prism_endpoint_inventory.py` exits **0** with `httpx` installed |
| obsolete open PRs | **0** |
| composition conflicts | 1, owned by **#703** (§5) |

The queue's blocker remains **human merge throughput across 28 drafts**, not outstanding repair
work.

## 8. Next-action block

**Current state.** `main` = `bb19aabda34d59594615b0279a45e9cbd3d8204d`; production
`source_revision` identical, `revision_conflict: false`. `tests/architecture` 11 passed; lane
currency exit 0 both offline and live; full suite `19 failed, 4250 passed, 22 skipped, 1 error`
with a 20-node failing set identical in membership to the recorded baseline. **28** open drafts,
all `MERGEABLE`, 0 obsolete, 0 attributable CI failures. Composition: 377/378 pairs `CLEAN`; the
one `CONFLICT` (`#681 × #687`) is owned by `#703`. `api/main.py` at 2597/2600; #701 composes to
2593.

**Evidence.** Sections 1–7; every command above is reproducible as written.

**Blockers.** (a) Merge execution is human-only (GOV-03); 28 drafts await human review.
(b) `beta-*` / `native-arkadia-golden-workflow` results are governed by an external provider and
cannot be made deterministic from this repository. (c) CE-01 and FINDING F-01 are reserved to the
sovereign. (d) `scripts/prism_coherence_check.py`'s scope is a sovereign decision.

**Authorized next action.** A human reviews the queue for merge; the advisory order is unchanged —
`#681`/`#687` one-then-rebase-the-other (keep both appended sections), everything else in any
order. On a later cycle an agent may re-run the 378-pair matrix as the queue moves, verify a
specific PR against the then-current `main`, or implement a newly measured, non-reserved defect.

**Forbidden.** Merging; pushing to `main`; force-pushing; deploying; bypassing protection or
required checks; weakening a guard to manufacture green; repairing CE-01 or F-01 without a
sovereign decision; opening a PR whose only product is activity.

**Completion condition.** This cycle is complete when this evidence is reviewable on the existing
contract-record branch, with `main` unmodified and no merge, deployment or acceptance claimed.
