# ARK-OPS-CONTINUOUS-001 — Cycle 02

- **Contract:** `ARK-OPS-CONTINUOUS-001` rev `2026-11-22`
  (`docs/control-plane/openhands/hourly-weaver/2026-11-22-continuous-reconciliation-contract.md`)
- **Cycle:** 02 — immediate execution + hourly continuation
- **Observed:** 2026-11-23T13:05Z → 13:45Z
- **Authority:** `MERGE_AUTHORITY := NONE`, `DEPLOY_AUTHORITY := NONE`. No merge, no push to
  `main`, no deployment, no acceptance claimed.
- **Predecessor:** `docs/control-plane/evidence/ark-ops-continuous-001-cycle-01/EVIDENCE.md`

---

## 1. Reconstructed state

| fact | measured value | how |
|---|---|---|
| canonical `main` | `bb19aabda34d59594615b0279a45e9cbd3d8204d` | `GET /repos/…/commits/main` |
| local checkout | `bb19aabd`, tree clean | `git log -1`, `git status --porcelain` |
| production revision | `source_revision = bb19aabd…`, `revision_conflict: false` | `GET https://arkadia-qzu4.onrender.com/api/version` |
| `main` executed checks | `boot-syntax`, `console-contract`, `engineering-scheduler`, `posture-currency`, `test`, `Full-history secret scan` → all `success` | `commits/<full-sha>/check-runs` |
| open PRs | **28**, all `base: main`, all drafts, all `MERGEABLE` | `gh pr list` + `pulls/{n}/files` |
| hourly automation | `ACTIVE`, cron `5 * * * *`, `timeout 1800` | `GET /api/automation/v1/6bc8f514-…` |

`main` did not move during the cycle. Production tracked it. The recurring continuation is
verified to exist and be enabled, not assumed.

## 2. Verification gates

| suite | result |
|---|---|
| `tests/architecture` | **11 passed** |
| `tests/test_console_endpoint_registry_contract.py` | **21 passed**; `RECORDED_ADVERTISED_DRIFT` is now the **empty set** |
| `scripts/lane_state.py --check --verify-live` | exit **0**; 4 live PRs read; 4 doc-guard lanes consistent |
| `scripts/console_contract_domain.py` | **74** guards derived; `prism-console-contract.yml` executes the derived domain (not a restated list) |
| full suite (`-q -rEf --continue-on-collection-errors`) | **19 failed, 4250 passed, 22 skipped, 1 error** |

The full-suite failing/error **node set is 20 nodes**, sha256
`d6101722f624c0eedb48a957375f0b8abbef398f20e93e55e889dd8d9e0893ce` — the recorded baseline,
unchanged from cycle 01's outcome-set `8d70e46e…` (the two hashes are the `ids` and `outcomes`
conventions over the same 20 nodes; they are not a delta). Attribution is by node identity,
never by totals.

The `base main: b842892b` line printed by `lane_state.py` is **not** staleness: the oracle's
criterion is "a guarded lane doc changed after the snapshot was last written", not
`base_main == main`, and no guarded doc moved in that window.

## 3. Gap closed this cycle — the unmeasured composition pair, and a superseded measurement

### 3.1 The whole open queue is now measured, not the 16 PRs of an earlier pass

`#694` built a generic pairwise composition oracle but measured the queue when it held
**16** PRs (120 pairs). The queue is now **28** PRs (**378** pairs), so 258 pairs had never
been judged. Re-running `#694`'s own oracle over the current queue:

| | `#694` body (16 PRs) | this cycle (28 PRs) |
|---|---|---|
| pairs judged | 120 | **378** |
| `CLEAN` | 119 | **377** |
| `CONFLICT` | 1 | **1** |
| `UNPROVABLE` | 0 | **0** |

The single conflict is identical in classification:

```
681 x 687         CONFLICT    tests/test_gate2_production_observation.py
```

That is the exact pair `#703` exists to adjudicate. **No new conflict entered the queue as it
nearly doubled** — the strongest available evidence that the oracle is not fitted to the one
pair it was written against. Recorded as a correcting comment on `#694`
(issue comment `7102351441`), because a stale citation is a defect to correct rather than
reconcile.

Reproduction (read-only):

```console
$ git fetch origin '+refs/pull/*/head:refs/pr/*'
$ python scripts/open_pr_inventory.py --conflicts \
    $(for n in 675 679 680 681 682 683 684 685 686 687 688 689 690 691 \
               692 693 694 695 696 697 698 699 700 701 702 703 704 705; do
        printf -- '--ref %s=refs/pr/%s ' $n $n; done)
378 pair(s) judged
```

### 3.2 The one file-overlap pair is verified semantically, not only textually

The oracle is textual by design. Independent file-overlap measurement over the 28 PRs found
exactly three shared paths — `scripts/gate2_production_observation.py` and
`tests/test_gate2_production_observation.py` (`#681`/`#687`, already adjudicated by `#703`),
and `web/arkadia_console/src/lib/endpoints.ts` (`#692`/`#704`), which **no open PR measured**.

```console
$ git worktree add --detach /tmp/wt-704 refs/pr/692
$ git -C /tmp/wt-704 merge --no-edit refs/pr/704
   → zero unmerged files
$ pytest $(python scripts/console_contract_domain.py) -q
  composed: 10 failed, 1297 passed, 4 skipped
  main:     10 failed
$ diff main_failed composed_failed → empty
```

Textual and semantic verdicts agree. The diffs land in different regions of `endpoints.ts`
(`#692` adds `solspireProposals` beside `solspireProjects`; `#704` adds the `messages` /
`messagesInbox` pair plus a `messagesThread()` helper).

Both advertised contracts are **genuinely served**, so neither PR repeats the
"advertised but unserved" defect class:

| advertised | served by |
|---|---|
| `/api/messages`, `/api/messages/thread/{peer_uid}`, `/api/messages/inbox` | `api/messages.py` (`POST /api/messages`, `GET /api/messages/thread/{peer_uid}`, `GET /api/messages/inbox`), mounted at `api/main.py:354-356` |
| `/solspire/proposals` | `solspire/proposal_router.py` (`prefix="/proposals"`, `GET ""`) under the `/solspire` prefix |

The 10 shared failures are `tests/test_mission_lifecycle_adapter_contract.py` —
**environment-only** (missing `web/arkadia_console/node_modules/typescript`) and present on
`main` itself. Zero regression, attributed by node identity.

## 4. Investigated and found already closed (not re-opened)

| candidate gap | measured state |
|---|---|
| CP10-B broad-suite step executing zero tests | **repaired** — `sg-02-fe-2-v.yml:246` carries `--continue-on-collection-errors` |
| console-contract gate executing a restated domain | **repaired** — the gate runs `$(python scripts/console_contract_domain.py)`, 74 guards, derived not restated |
| console advertising an unserved contract | **repaired** — `RECORDED_ADVERTISED_DRIFT` is the empty set; 21 guards pass |
| lane snapshot freshness printed but not judged | **repaired** — `_freshness_findings` fails closed and is scoped to guarded-doc movement |
| baseline node-set fixture stale | covered by open `#693` (drops five repaired nodes) |
| recurring hourly continuation missing | **present** — automation `ACTIVE`, `5 * * * *`, `timeout 1800` |

No candidate was re-repaired, and no guard was weakened.

## 5. Why this cycle did not open a new code PR

All **20** failing/error nodes are classified and every non-reserved one is repaired by an
open PR (`#700`, `#693`, `#690`, `#691`, `#698`). The residue is 1 CE-01 `weaver.autonomy`
collision and 1 FINDING F-01 persistence boundary, both **sovereign-reserved**, plus the
environment-only set that passes in CI where `pnpm install` provisions `node_modules`.

The queue's blocker is **human merge throughput across 28 drafts**, not outstanding repair
work. Opening a 29th code PR would add review load without closing a verified gap, which
`ARK-OPS-CONTINUOUS-001` §0.1 explicitly forbids. The cycle's product is therefore a
**measurement that retires a real release risk** (378-pair composition) and its durable
record, appended to this PR rather than spawned as a new one.

## 6. Next-action block

**Current state.** `main` = `bb19aabda34d59594615b0279a45e9cbd3d8204d`; production
`source_revision` identical, `revision_conflict: false`. `main`'s executed checks green.
Full-suite failing set = recorded baseline (20 nodes, `d6101722…`), fully classified.
**28** open drafts, all `MERGEABLE`, 0 obsolete, 0 attributable CI failures. Composition
measured: 377/378 pairs `CLEAN`, the one `CONFLICT` (`#681 × #687`) already owned by `#703`.

**Evidence.** Sections 1–5; every command above is reproducible as written.

**Blockers.** (a) Merge execution is human-only (GOV-03) and 28 drafts await human review.
(b) `beta-*` / `native-arkadia-golden-workflow` results are governed by an external provider
and cannot be made deterministic from this repository. (c) CE-01 and FINDING F-01 are
reserved to the sovereign.

**Authorized next action.** A human reviews the queue for merge; the advisory order is
`#681`/`#687` one-then-rebase-the-other (keep both appended sections), everything else in any
order. On a later cycle an agent may re-run the 378-pair matrix as the queue moves, verify a
specific PR against the then-current `main`, or implement a newly measured, non-reserved
defect.

**Forbidden.** Merging; pushing to `main`; force-pushing; deploying; bypassing protection or
required checks; weakening a guard to manufacture green; repairing CE-01 or F-01 without a
sovereign decision; opening a PR whose only product is activity.

**Completion condition.** This cycle is complete when this evidence is reviewable on the
existing contract-record branch, with `main` unmodified and no merge, deployment or
acceptance claimed.
