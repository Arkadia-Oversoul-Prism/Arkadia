# ARK-OPS-CONTINUOUS-001 — cycle 24: no drift on `main`, and one composition blocker closed

**Contract:** `ARK-OPS-CONTINUOUS-001` rev `2026-11-22`
**Base:** `main` @ `cb2841956bcc0397007b9efffbaa8cc6d0801836` (2026-11-26T00:16:37Z)
**Measured:** 2026-11-26, 04:05–05:10 UTC, this workspace
**Authority:** `MERGE_AUTHORITY := NONE`, `DEPLOY_AUTHORITY := NONE`. No merge, no push to
`main`, no deployment, no acceptance, no draft conversion. **No new pull request was
opened.** One existing PR was extended (#705) and one existing PR was repaired (#742, §5).

---

## 0. Governance conflict, still preserved

Cycle 23 recorded that this contract (§0.1, `MERGE_AUTHORITY := NONE`) and `AGENTS.md`
GOV-04 (bounded delegation, active since `fd0a4fdc`) disagree on who may execute a merge.
Nothing changed this cycle. **The stricter bound was applied**: no merge was executed, no
PR was made ready, and §3 is advisory only.

---

## 1. Reconstructed state — zero drift since cycle 23

| fact | measured value | how |
|---|---|---|
| canonical `main` | `cb2841956bcc0397007b9efffbaa8cc6d0801836` | `git rev-parse origin/main`; also the live default-branch read |
| clone | full (`is-shallow-repository` → `false`) | `git rev-parse --is-shallow-repository` |
| working tree | clean | `git status --porcelain` |
| merges since cycle 23 | **0** — `main` is byte-identical to cycle 23's base | cycle 23 recorded the same SHA |
| open PRs | **63** — 62 drafts, **1 ready** (`#679`) | `search/issues is:pr is:open` |
| `api/main.py` | 2 597 lines (budget 2 600) | unchanged |

Cycle 23's handoff named `cb284195` and it is still `main`, so the handoff was **not**
stale this time — the first time in three cycles. State was re-derived anyway rather than
inherited.

### 1.1 A docs-only merge runs almost no gate — measured, not inferred

`cb284195` touched exactly one file
(`docs/control-plane/openhands/hourly-weaver/2026-11-21-weekly-closure-directive.md`).
Its check-run list carries **two** entries:

```
Full-history secret scan  => success
weaver_evolution          => skipped
```

Every other gate is path-filtered and did not select this commit. So "`main` is green at
`cb284195`" is a true statement about **one** check, not about the code. This is the same
class already recorded for the console-contract and economic-seam domains: a
content-derived or path-filtered gate has no execution at a revision that does not touch
its paths. Recorded, not repaired — it is gate *coverage*, not a failing gate.

---

## 2. Production boundary — revision identity VERIFIED, acceptance NOT CLAIMED

```
GET https://arkadia-qzu4.onrender.com/api/version -> 200
  source_revision    cb2841956bcc0397007b9efffbaa8cc6d0801836
  revision_source    RENDER_GIT_COMMIT
  revision_conflict  false
  canonical_deployment  one_reconciled_deployment
GET /health -> 200
```

Deployed revision equals `main`. Necessary evidence of source↔runtime consistency; not
proof of correct behaviour, and not acceptance.

**Cold-start caveat, reproduced.** A `--max-time 30` probe of `/api/version` returned
**nothing**; the same probe at `--max-time 110` returned `200` with the payload above.
Identical to cycle 23's observation at 25 s vs 60 s. A timeout on this endpoint is
**unproven**, not "down".

---

## 3. Candidate eligibility — `#679` unchanged and still ELIGIBLE_TO_MERGE (advisory)

| property | measured |
|---|---|
| open, non-draft, base `main` | `isDraft=false`, base `main` |
| exact head | `a9bef9aa84df3578181bf8e5ba52625596733ec1` — **unchanged** since cycle 23 |
| mergeability | `MERGEABLE` / `CLEAN` |
| reviews | 0; `reviewDecision` empty |
| diff | +193/−11 over 4 files (`KnowledgeGraphPanel.tsx`, `knowledgeContracts.ts`, one test, one evidence doc) |
| composition against `main` | merged into a detached worktree at `cb284195` with zero conflicted files (cycle 23); `main` has not moved since, so that result still binds |

`ELIGIBLE_TO_MERGE` is an advisory assessment only. It is not permission, approval, or
execution. The blocker is unchanged and human: 62 of 63 candidates are drafts, and no
agent may convert a draft (GOV-04: drafts must be made ready by their owner).

---

## 4. Failing/error node set — identical to cycle 23, still fully owned or reserved

`python -m pytest tests/ -q -rEf --continue-on-collection-errors` at `cb284195`:

```
22 failed, 4251 passed, 22 skipped, 1 error in 294.37s (0:04:54)
```

**23 nodes**, and the per-file distribution is byte-identical to cycle 23's:

| nodes | file | owner / class |
|---|---|---|
| 10 | `test_mission_lifecycle_adapter_contract.py` | environment-only — needs `web/arkadia_console/node_modules/typescript` |
| 2 | `test_prism_w4_lab_pr_state.py` | open `#683` |
| 2 | `test_solspire_r1_governance_convergence.py` | open `#693` |
| 1 | `test_solspire_r3_execution_runtime.py` | open `#691` |
| 1 | `test_m05_files.py::test_update_file_supports_rename` | open `#690` |
| 1 | `test_static_ingestion_idempotency.py` | open `#698` |
| 1 | `test_gov04_bounded_merge_delegation.py` | open `#725` |
| 1 | `test_identity_spine_w1.py::…node_entry_is_ais_signup…` | open `#700` |
| 1 | `test_m02_reasomate_truth.py::…shared_session_key` | open `#700` |
| 1 | `test_ais_w2_living_gate_grove_handoff.py::test_no_firebase_persistence_in_gate` | sovereign-reserved FINDING F-01 |
| 1 | `test_m01_persistence.py::…deletion_propagates_to_durable_corpus` | sovereign-reserved FINDING F-01 |
| 1 (ERROR) | `test_autonomy.py` | sovereign-reserved CE-01 `weaver.autonomy` collision |

**Node identity matches; no new failure, none repaired.** My fingerprint of the sorted
node-id list is `17b3b70467b8d5c3730770b25518f00fa8c257ab0e3fdd48299bc8e8d6713a1d`
(23 ids, `\n`-joined, trailing newline). Cycle 23 recorded
`013c588c213eecd626f5b89e9ca0c0447b3fe75c1d11ddb741bf00c3a173ec09` under a different
hashing convention. **The two values are not comparable and neither is wrong** — the
load-bearing comparison is the node *set*, and it is identical. Stated explicitly so a
later cycle does not read the difference as drift.

**No unowned, non-reserved, safely repairable defect exists on `main` at this revision.**

---

## 5. New this cycle — one composition blocker, proven and closed

### 5.1 The queue composes worse than each PR suggests

`GET /pulls/<n>/files` over all 63 open PRs gives **290** changed paths, **274** unique.
**14** paths are touched by more than one open PR. Classifying those against `main`:

| duplicate path | PRs | on `main`? |
|---|---|---|
| `.bootstrap/01_STATE.md` | #716, #693 | yes |
| `.github/workflows/canonical-render-browser-smoke.yml` | #728, #689 | yes |
| `.github/workflows/economic-seam-engine.yml` | #734, #718 | yes |
| `.github/workflows/prism-console-contract.yml` | #728, #707 | yes |
| `MISSION.md` | #716, #693 | yes |
| `NEXT_AGENT.md` | #716, #693 | yes |
| `api/arkana_stream_routes.py` | #721, #717 | yes |
| `api/main.py` | #729, #717, #711, #701 | yes |
| **`docs/control-plane/evidence/ark-ops-continuous-001-cycle-23/EVIDENCE.md`** | **#742, #705** | **no — both ADD it** |
| `scripts/gate2_production_observation.py` | #687, #681 | yes |
| `scripts/lane_state_refresh.py` | #684, #682 | yes |
| `solspire/console_router.py` | #713, #710 | yes |
| `tests/test_gate2_production_observation.py` | #687, #681 | yes |
| `web/arkadia_console/src/lib/endpoints.ts` | #704, #692 | yes |

A shared path that already exists on `main` is a *possible* conflict that git may resolve.
A shared path that **both PRs add** is a *guaranteed* add/add conflict. Exactly one such
path existed, and it is the contract's own ledger.

### 5.2 Proven, in both merge orders

```
$ git worktree add --detach /tmp/wt pr/705 && cd /tmp/wt && git merge --no-edit pr/742
CONFLICT (add/add): Merge conflict in docs/control-plane/evidence/ark-ops-continuous-001-cycle-23/EVIDENCE.md
$ git worktree add --detach /tmp/wt2 pr/742 && cd /tmp/wt2 && git merge --no-edit pr/705
CONFLICT (add/add): Merge conflict in docs/control-plane/evidence/ark-ops-continuous-001-cycle-23/EVIDENCE.md
```

Both PRs report `mergeable: true` against `main`, because GitHub compares each PR with
`main` and never with the other. Neither PR's own CI could observe this.

The two documents are different records, not a duplicate:

```
#705  "cycle 23: the queue is not frozen, and one candidate is eligible"  (12 405 B, 196 lines)
#742  "cycle 23: the home portal grid printed five labels twice"          ( 8 106 B, 170 lines)
```

### 5.3 Repaired in #742 — `27467ed7`

The corpus already resolves this shape by convention: a fix record carries a descriptive
suffix beside the bare reconciliation record (`cycle-06-root-doc-link-integrity-01` +
`cycle-06`, `cycle-09-gemini-model-ladder-01` + `cycle-09`,
`cycle-20-pr-wave-dry-run` + `cycle-20`). #742's record is a fix record, so it took the
suffix:

```
…-cycle-23/                                    <- #705, reconciliation record (unchanged)
…-cycle-23-home-portal-label-duplication-01/   <- #742 (renamed, content byte-identical)
```

Verified after the repair: `git merge --no-edit 27467ed7` from `pr/705` exits **0**, zero
unmerged files, both records present; `tests/test_prism_home_entry_contract.py` is
**10 passed**. Nothing in the branch or in `tests/` referenced the old path
(`git grep` → 0 matches), so the rename is inert.

### 5.4 Ledger fragmentation — indexed, not repaired

Cycle records are carried by **16 different open PRs**, and cycles **06, 07, 08, 09, 20,
23** each appear twice. A reader of #705 alone sees 12 of the 23 cycles and cannot tell
an unrecorded cycle from one recorded elsewhere — the false-absence shape this repository
already treats as a defect class. `docs/control-plane/evidence/ark-ops-continuous-001/LEDGER.md`
now indexes every cycle to its carrying PR, states the derivation command, and records the
two-record convention and its limits. It is a snapshot of open PRs, not of history.

---

## 6. Runtime read-surface sweep — production, read-only

97 GET routes from the served `/openapi.json` (300 paths, 160 GETs) were probed after
excluding path-parameterised routes and any route whose name implies a side effect
(`generate`, `forge`, `tts`, `run`, `execute`, `ingest`, `upload`, `sync`, `reset`, …):

| status | count |
|---|---|
| 200 | 33 |
| 401 | 56 |
| 403 | 3 (`Sovereign gate closed.`, `Sovereign key required` ×2) |
| 422 | 4 (missing required query parameter) |
| **502** | **1** |

The single 5xx:

```
GET /api/codex/github-tree -> 502
{"error":"Client error '401 Unauthorized' for url
 'https://api.github.com/repos/Arkadia-Oversoul-Prism/Arkadia/git/trees/main?recursive=1' …"}
```

Two defects in one response — the route is broken, **and** it returns the caught
exception's text. **Both are already owned**: the credential fallback by open `#701`
(`api/github_corpus.py`), and the 5xx disclosure contract by open `#729`, whose own
evidence already names this exact route and attributes it to `#701`. Independently
re-confirmed here; not re-filed.

Also measured, all clean:

- **Console endpoint registry:** all **45** advertised paths in
  `web/arkadia_console/src/lib/endpoints.ts` resolve to a path in the **production**
  openapi (`{param}` normalised on both sides, `/api` significant on both). 0 unserved.
- **Console surfaces:** all **15** declared paths in `surfaces.ts` serve the SPA shell
  (`200`, 1 256 B, `id="root"` present) from the canonical origin.

**Harness caveat (recorded so a later cycle does not repeat it).** The first surface
sweep read only the first 400 bytes of each response and reported `id="root"` absent for
**all 15** surfaces — a false positive caused by truncation, not a defect. A full read of
the same responses shows 1 256 B with `id="root"`. The instrument was wrong, not the app.

---

## 7. What this cycle did not do, and why

- **No repair of any failing node.** All 23 are owned by an open PR or sovereign-reserved;
  a second repair would conflict with reviewed work.
- **No `api/main.py` extraction.** 2 597/2 600 is nearly exhausted, but extracting a route
  block is an architecture change needing its own authorization and a full boot
  verification — not the smallest maintainable change inside a 30-minute cycle.
- **No new PR.** Every defect found is owned or reserved, and §0.1 forbids opening one to
  appear productive.
- **No draft conversion, no merge, no deployment, no acceptance.**

---

## 8. Next-action block

**Current state.** `main` = `cb284195`, unchanged since cycle 23. Production revision =
`cb284195` (VERIFIED, revision identity only). 63 open PRs: 62 drafts, 1 ready. `#679` is
`ELIGIBLE_TO_MERGE` (advisory), head unchanged, 16/16 checks, no required review.
`#742` head is now `27467ed7` with the ledger collision closed.

**Evidence.** §1–§6 of this record; the two-order add/add merge transcript (§5.2); the
post-repair merge exit 0 (§5.3); the 97-route production sweep (§6); the 23-node set
matching cycle 23 by identity (§4).

**Blocker.** Human, unchanged: nothing merges until a human reviews a candidate (`#679`
is the only ready one) or makes another draft ready. Not an engineering gap, and no agent
may cross it.

**Authorized action for the next cycle.** Re-derive `main`, the production revision, and
the queue (one read each); re-run the full suite and re-classify the node set by owner;
re-assess any newly-ready candidate with the §3 procedure; before trusting the queue,
re-run the duplicate-path scan in §5.1 and check any new **added** path shared by two open
PRs. Record the result here. Do **not** open a PR unless a defect is found that is neither
reserved nor owned.

**Forbidden.** Merge execution, draft conversion, push to `main`, force-push,
protection/check bypass, deployment, provider configuration, acceptance, and any claim of
production parity beyond revision identity.

**Completion condition.** State re-derived; the node set re-classified by identity with
zero drift; one composition blocker proven and closed; the ledger indexed so the next
agent can resume from the repository; the human blocker named.
