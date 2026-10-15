# Evidence — Prism UI reconciliation: live lane-state reconstruction

**Observed:** 2026-10-15T01:24:32Z
**Repository:** `Arkadia-Oversoul-Prism/Arkadia`
**Current `main` (BASE_MAIN):** `7580bd8f0ca2925518d78775f9a323ff0df8bc66`
("Merge pull request #533 from Arkadia-Oversoul-Prism/aeas/engineering-lab-composition-01", 2026-10-14T12:47:09+01:00)
**Method:** live GitHub REST reads (authenticated) + local `git rev-list` for base lag + `git apply --3way` / `git merge`
composition probes in a detached worktree. Machine-readable companion: [`lane-snapshot.json`](./lane-snapshot.json).
**Purpose:** reconstruct the current live state of the parallel Prism UI workstream — active branch/PR per lane,
mergeability, and contract-doc ownership. **This record mutates no branch and merges nothing.**

## 0. Auth boundary actually used

- Env `GITHUB_TOKEN` is empty/stale. The working credential is the one embedded in the clone remote
  (`https://<credential>@github.com/Arkadia-Oversoul-Prism/Arkadia`), read from `/tmp/ghtok` and sent as
  `Authorization: Bearer $TOK`. Proven: `GET /api/user` → **200**, `login: Arkadia-Oversoul-Prism`.
- `gh auth status` reports "not logged into any GitHub hosts" — `gh` is **not** authenticated here. All reads in
  this record were made with `curl` + the remote credential. No token value is printed anywhere in this file.
- No write was performed. No branch, PR, or deployment was created or modified.

## 1. Headline numbers

| Measure | Value |
|---|---|
| Open PRs | **39** |
| Lanes covered (governing four-lane contract) | 4 UI lanes + 1 non-lane control-plane track |
| Contested files (touched by ≥2 open PRs) | **40** |
| PRs mergeable_state `clean` | 28 |
| PRs `dirty` (textual conflict with current base) | 4 — `#493`, `#501`, `#512`, `#530` |
| PRs `unstable` (failing required check) | 7 — `#482`, `#499`, `#500`, `#502`, `#503`, `#508`, `#535` |
| Draft PRs | 39 of 39 (every open PR is a draft) |

Every open PR is a **draft**. No open PR is marked ready. That is the intended posture under
`docs/control-plane/parallel-ui/SHARED-CONTRACTS.md` §4 ("Keep PRs draft until …").

## 2. Lane assignment and the two numbering systems

The governing contract (`docs/control-plane/parallel-ui/`) defines **four lanes** (W1–W4). This task's prompt
uses a different, older `prism-nextN` numbering. Both are recorded so neither is silently re-mapped.

| Governing lane | Instruction doc | Task-prompt label seen for the same work |
|---|---|---|
| 1 — Shell / navigation / design system / integration seam | `AGENT-01-SHELL.md` | "Lane 1" and "Lane 2 (Nexus/aliases)" |
| 2 — NovaNet / Project Opportunity Radar | `AGENT-02-NOVANET-OPPORTUNITY.md` | "Lane 7" (`#492`), "Lane 2" (`#538`, `#528`) |
| 3 — Solariun / Knowledge OS | `AGENT-03-SOLARIUN-KNOWLEDGE.md` | "Lane 3" |
| 4 — Arkana / Weaver / Engineering Lab | `AGENT-04-ARKANA-WEAVER-LAB.md` | "Lane 8" (`#493`), "Lane 4" |
| (no governing lane) Gate-10 / EAA / control-plane | — | "Lane 10" (`#482`, `#484`) |

**Conclusion:** the task prompt's "Lane 7 / Lane 8 / Lane 10" are per-PR wave labels, **not** the governing
lane identities. `#492` is governing-Lane-2 work; `#493` is governing-Lane-4 work; `#482`/`#484` are not UI-lane
work at all. Any instruction "advance Lane 7" must be read as "advance governing Lane 2".

## 3. Live lane map (measured)

Base lag = `git rev-list --count <pr base sha>..7580bd8f` — how far the PR's merge base has fallen behind current
`main`. High lag is the primary merge-risk signal here: the guarded files (`router.ts`, `App.tsx`,
`knowledgeContracts.ts`, `EngineeringLabPage.tsx`, `AGENTS.md`) are exactly the ones the lagging PRs touch.

### Lane 1 — Shell / navigation / design system / integration seam (`AGENT-01-SHELL.md`) — 11 open PRs

| PR | Branch | mergeable | behind | checks | head |
|---|---|---|---|---|---|
| #496 | `docs/control-plane-live-recovery-2026-10-12` | clean | 8 | 7 | `967f30d9` |
| #497 | `feat/prism-next9-01-nexus-alias` | clean | 8 | 15 | `a14d3fa9` |
| #504 | `gate10/prism-next-wave-composition-reconciliation-01` | clean | 8 | 9 | `a9cefd21` |
| #505 | `feat/prism-next10-01-legacy-alias-families` | clean | 8 | 15 | `8cb030c0` |
| #507 | `feat/prism-l1-legacy-route-coverage-01` | clean | 8 | 9 | `3a19810e` |
| #511 | `feat/prism-rec-02-signin-return-to` | clean | 7 | 15 | `7af66444` |
| #514 | `feat/prism-rec-06-surface-error-boundary` | clean | 7 | 15 | `e48cbf26` |
| #516 | `feat/prism-rec-07-document-title` | clean | 7 | 15 | `dc91354e` |
| #522 | `feat/prism-rec-10-home-entry-threshold` | clean | 3 | 15 | `dcdff997` |
| #523 | `fix/console-authorization-state-forbidden` | clean | 3 | 15 | `309f7c8f` |
| #529 | `feat/prism-l1-lens-strip-keyboard-01` | clean | 2 | 15 | `95eb5b7b` |

**Lane 1 has no single authority PR.** Eleven drafts claim shell-owned files. The branch the task prompt called
`fix/console-authorization-state-forbidden` **does exist** — it is **PR #523**, head `309f7c8f`, `clean`, 3 behind.
(The earlier `fatal: invalid object name` was a local-ref gap, not an absent branch.)

### Lane 2 — NovaNet / Project Opportunity Radar (`AGENT-02-NOVANET-OPPORTUNITY.md`) — 4 open PRs

| PR | Branch | mergeable | behind | checks | head | note |
|---|---|---|---|---|---|---|
| #492 | `feat/prism-next7-02-pipeline-strip` | clean | 8 | 15 | `acfbf521` | task-prompt "Lane 7" |
| #526 | `fix/knowledge-traverse-edge-dedup-01` | clean | 3 | 9 | `cb868ce4` | edge-dedup; also touches Lane 3 test surface |
| #528 | `feat/prism-l2-echoes-completeness-01` | clean | 3 | 15 | `e162371d` | NovaNet echoes |
| #538 | `fix/prism-l2-buyer-recon-status-normalization-01` | clean | **0** | 12 | `1a36f235` | the governed buyer-recon repair; freshest |

### Lane 3 — Solariun / Knowledge OS (`AGENT-03-SOLARIUN-KNOWLEDGE.md`) — 5 open PRs

| PR | Branch | mergeable | behind | checks | head |
|---|---|---|---|---|---|
| #498 | `feat/prism-next9-03-knowledge-timeline-paging` | clean | 8 | 15 | `b7f2749d` |
| #509 | `feat/prism-lane3-project-detail-reader-01` | clean | 8 | 15 | `c057055f` |
| #527 | `feat/prism-l3-graph-provenance-01` | clean | 3 | 15 | `c8320003` |
| #534 | `feat/prism-l3-knowledge-status-read-boundary-01` | clean | 2 | 15 | `fb9bee79` |
| #537 | `fix/prism-l3-reference-search-owner-scope-01` | clean | **0** | 9 | `8f6cb08a` |

### Lane 4 — Arkana / Weaver / Engineering Lab (`AGENT-04-ARKANA-WEAVER-LAB.md`) — 10 open PRs

| PR | Branch | mergeable | behind | checks | head | note |
|---|---|---|---|---|---|---|
| #493 | `feat/prism-next8-04-automation-grammar` | **dirty** | 8 | 15 | `255d665f` | task-prompt "Lane 8" |
| #501 | `feat/prism-next9-04-canonical-loop-mount` | **dirty** | 8 | 15 | `31d66332` | |
| #515 | `feat/prism-rec-05-arkana-provenance` | clean | 7 | 15 | `757cc677` | |
| #512 | `feat/prism-l4-lab-operational-projection-01` | **dirty** | 3 | 15 | `f8da5158` | |
| #524 | `feat/prism-l4-lab-governance-readings-01` | clean | 3 | 15 | `aad8a986` | |
| #525 | `feat/prism-rec-12-lab-authority-boundary` | clean | 3 | 15 | `daef33c4` | |
| #530 | `gate-lane4/render-integrity-01` | **dirty** | 3 | 15 | `f54d463c` | |
| #531 | `feat/prism-w4-arkana-project-turn-visibility` | clean | 3 | 11 | `d0a8902d` | |
| #532 | `feat/prism-w4-arkana-thread-time-truth` | clean | 3 | 15 | `aec31cb1` | |
| #536 | `feat/prism-l4-run-artifact-trace-01` | clean | **0** | 15 | `5490b0b5` | |

All four `dirty` PRs in the repository are in **this lane**, and all four touch
`web/arkadia_console/src/pages/EngineeringLabPage.tsx` (see §5). Lane 4 is the concentrated merge-risk lane.

### Control-plane track (not a UI lane) — 8 open PRs

| PR | Branch | mergeable | behind | failing check |
|---|---|---|---|---|
| #482 | `gate10/history-depth-ci-wiring-01` | unstable | 10 | `provider-routing` |
| #484 | `gate10/beta-evidence-bundle-race-01` | clean | 22 | — |
| #499 | `fix/weaver-schema-status-semantics-2026-10-12` | unstable | 8 | `provider-routing` |
| #500 | `feat/gate-l4-openhands-dispatch-adapter` | unstable | 8 | `provider-routing` |
| #502 | `feat/engineering-acceptance-authority` | unstable | 8 | `provider-routing` |
| #503 | `test/eaa-base-baseline-49809f4` | unstable | 8 | `trigger-coverage` |
| #508 | `feat/eaa-readonly-github-evidence-adapter` | unstable | 8 | `provider-routing` |
| #535 | `eaa/chain-composition-01` | unstable | **0** | `provider-routing` |

`#535` is the composed EAA/dispatch chain (31 files) built on the **current** `main`; it subsumes the file sets
of `#500`, `#502`, `#503`, `#508`, `#499` on the same paths (see §5). Its `provider-routing` failure is shared with
five of those siblings.

## 4. Mergeability — what "clean" does and does not mean here

- **`clean` = GitHub found no textual conflict against the PR's *own recorded base*, not against current `main`.**
  Every `clean` PR above is 2–22 commits behind `main`. `clean` here is a statement about a stale base.
- **Measured counterexample.** Two `clean`, 8-behind Lane-1 PRs conflict with each other on the current file:

  ```
  $ git merge --no-commit --no-ff pr505   # in a worktree at pr497's head a14d3fa9
  merge 505+497: CONFLICT -> tests/test_console_shell_nav_contract.py
  ```

  `#497` and `#505` are each `clean` and each 8 commits behind; composed they conflict on the shared shell
  contract test. `git apply --3way` of `#505` onto `#497`'s head likewise reports
  `Applied patch to 'tests/test_console_shell_nav_contract.py' with conflicts` (while `router.ts` applied cleanly).
- Conversely, removing the shared-file overlap removes the conflict: `#507`, `#529` compose cleanly with `#497`,
  `#505`, and each other (5 of 6 pairwise probes clean; only the `#505`×`#497` pair conflicts).
- `dirty` (`#493`, `#501`, `#512`, `#530`) means GitHub already found a conflict against the branch's own base —
  the stronger signal, and it is confined to Lane 4.
- **No PR in any lane may be treated as merge-ready from `mergeable_state: clean`.** The contract's own gate
  (`SHARED-CONTRACTS.md`: "A draft is not merge-ready merely because its checks are green") is the correct reading:
  reconcile the base, inspect overlap, re-verify checks on the current head.

## 5. Cross-PR file contention (the composition hazard, measured)

40 files are touched by ≥2 open PRs. The load-bearing clusters:

| File | PRs | Reading |
|---|---|---|
| `web/arkadia_console/src/pages/EngineeringLabPage.tsx` | **5** — #493, #501, #512, #524, #530 | four of these five are the `dirty` set; this file is why Lane 4 cannot merge piecemeal |
| `web/arkadia_console/src/pages/knowledge/knowledgeContracts.ts` | **4** — #498, #509, #527, #534 | Lane 3 serializes on one contract module |
| `tests/test_console_shell_nav_contract.py` | 3 — #497, #505, #512 | the measured Lane-1 conflict target |
| `web/arkadia_console/src/lib/router.ts` | 2 — #497, #505 | alias-table contention; applies cleanly but is still a shared ownership file |
| `web/arkadia_console/src/App.tsx` | 2 — #511, #514 | Lane-1 seam |
| `web/arkadia_console/src/pages/NovaNetPage.tsx` | 2 — #492, #528 | Lane 2 |
| `AGENTS.md` | 3 — #482, #504, #538 | global instruction file; the contract forbids duplicating it from feature PRs |
| EAA/dispatch family (`weaver/openhands_dispatch.py`, `weaver/engineering_acceptance.py`, `weaver/engineering_router.py`, `weaver/github_readonly_evidence_adapter.py`, `docs/control-plane/gate-l4/*`, `.github/workflows/{eaa-base-baseline,engineering-acceptance-authority,gate-l4-dispatch-contract}.yml`, …) | 2 each — each of #499/#500/#502/#503/#508 paired with **#535** | `#535` is the composition of all five; merging #535 obsoletes them, merging any one first re-creates the overlap |

**Interpretation:** the four-lane ownership rule is being honoured at the *directory* level but not at the *file*
level. Lane-internal PR fan-out (11 Lane-1 drafts; 5 of them on `router.ts`/shell contracts) means "one lane, one
PR" is not currently true. That is a coordination defect to record, not to repair inside a lane.

## 6. Contract-doc ownership map (as written)

| Document | Owner per contract | Live PRs that edit it |
|---|---|---|
| `docs/control-plane/parallel-ui/SHARED-CONTRACTS.md` | Lane 1 / coordinator | #496, #535 |
| `docs/control-plane/overnight/PRISM-UI-RECONCILIATION.md` | coordinator-owned governance | #496, #535 |
| `docs/control-plane/overnight/PRISM-UI-SLICE-A-SHELL-INVENTORY.md` | Lane 1 | *(no open PR names it)* |
| `docs/control-plane/overnight/PRISM-UI-INVENTORY.md` | coordinator-owned integration artifact | *(no open PR names it)* |
| `docs/control-plane/parallel-ui/AGENT-01-SHELL.md` | Lane 1 | *(no open PR)* |
| `…/AGENT-03-SOLARIUN-KNOWLEDGE.md` | Lane 3 | #526 |
| `…/AGENT-04-ARKANA-WEAVER-LAB.md` | Lane 4 | #536 |
| `AGENTS.md` (global amendment) | global — do not duplicate from feature PRs | #482, #504, #538 |
| `tests/test_console_shell_nav_contract.py` | Lane 1 | #497, #505, #512 |

**Doc-vs-live drift (all three instruction docs are stale):**

| Doc | Declared active PR/head | Live state |
|---|---|---|
| `AGENT-01-SHELL.md` | branch `feat/prism-next2-01-shell-contract-map`, PR **#429** | #429 is **merged** (2026-10-11). Live Lane-1 work is #497/#505/#507/#529/#511/#514/#516/#522/#523/#496/#504. |
| `AGENT-02-NOVANET-OPPORTUNITY.md` | branch `feat/prism-next2-02-opportunity-entry-flow`, PR **#430** | #430 is **merged**. Live Lane-2 work is #492/#528/#538/#526. |
| `AGENT-03-SOLARIUN-KNOWLEDGE.md` | branch `feat/prism-next2-03-knowledge-timeline`, PR **#431**, then §"2026-10-11" names **#450** head `22b15091` | #431 **merged**; #450 **closed without merge**, head `22b15091` ≠ its live head. Live Lane-3 work is #498/#509/#527/#534/#537. |
| `AGENT-04-ARKANA-WEAVER-LAB.md` | "PR **#428**" | #428 is **merged**. Live Lane-4 work is #501/#512/#524/#525/#530/#531/#532/#536/#515/#493. |
| `SHARED-CONTRACTS.md` §1 branch map | refreshed 2026-10-11 at `f390526a`; heads `46326ba4`/`d40de704`/`f5f8b70e`/`dcb3e2f2` for #429–#432 | `main` has advanced 8 commits to `7580bd8f`; those heads are 3 merges stale. PR #496 carries the only fresh map, and it is unmerged. |

The owner assignment is intact; the **active-thread pointers are not.** A pulse that follows `AGENT-0N`
verbatim would work on a merged PR.

## 7. Contract-doc content (what the governing docs actually require)

- `SHARED-CONTRACTS.md` — 4 lanes with **exclusive file ownership** (§1); shared frontend/API contract (§3: one
  route registry, one shell, API evidence before UI claims, canonical client, honest states, real controls,
  evidence chain, preserve history, Render-only deployment invariant); parallel coordination protocol (§4:
  one new branch per wave from fresh `main`, no cross-lane merges/force-push, keep drafts); PR exit criteria (§5).
  §6 explicitly supersedes the older single-PR rule for the four named lanes only.
- `PRISM-UI-RECONCILIATION.md` — workstream-wide directive; the task prompt's amendment already binds this file
  and ADR-016 as the current operational contract, with Vercel **not** a production target.
- Task-prompt amendment (2026-10-11) — sole canonical origin `https://arkadia-qzu4.onrender.com`; branch
  `feat/prism-ui-reconciliation-overnight-01` is the long-lived workstream branch (its PR **#418 is merged**);
  no production deployment/merge/acceptance is authorized by the UI workstream.
- `#496` (unmerged, `docs/control-plane-live-recovery-2026-10-12`) is the only PR that attempts to refresh the
  live lane map. Merging it would clear the §6 drift; it also adds one `.gitleaks.toml` allowlist entry
  (`^NovaNet/Solariun$`, `regexTarget = "secret"`) and a portfolio doc.

## 8. Result classification

| Boundary | State | Basis |
|---|---|---|
| Repository topology / ancestry | **VERIFIED** | clean clone on `main`, `FETCH_HEAD` ancestry resolves, `main` = `7580bd8f` |
| Lane/PR inventory | **VERIFIED** | 39 open PRs enumerated with head/base SHAs, per-PR check-runs and mergeable_state |
| Mergeability of each PR *against its own base* | **VERIFIED** | live `mergeable_state` per PR |
| Composition safety across lanes | **PARTIALLY MEASURED** | one lane measured fully (#497×#505 conflict; #507/#529 clean); 40 contested files identified; other lanes not composed this pass |
| Contract-doc ownership | **VERIFIED (with drift)** | owner map read from committed docs; three of four instruction docs point at merged/closed PRs |
| "Lane 1 Slice A implemented + tests passing" (from the task prompt) | **NOT RE-VERIFIED THIS PASS** | `tests/test_console_shell_nav_contract.py` was not executed in this environment; the pass recorded state, not test outcomes |
| Runtime / production / deployment identity | **NOT CLAIMED** | no runtime probe performed; out of scope for a state reconstruction |

## 9. What this pass did NOT do, and why

- **No branch, no PR, no commit to any lane.** This pass is a reconstruction; the deliverable is durable evidence.
- **No full-suite or targeted pytest run.** The pass's budget went to live-state derivation across 39 PRs; test
  re-execution per lane is the next bounded task and is explicitly *not* claimed here.
- **No repair of the doc drift.** Correcting `AGENT-0N-*.md` active-PR pointers is Lane-1/coordinator-owned
  (the docs sit under Lane 1's instruction ownership and `SHARED-CONTRACTS.md` is coordinator-owned). It is
  recorded as the next bounded task rather than executed from a non-owning lane.

## 9a. Check-run closure on this record's head

Recorded after push, on head `c07ee677` (branch `prism-lane-state-reconstruction-01`), read from
`commits/<sha>/check-runs`:

| Check-run | Conclusion |
|---|---|
| Full-history secret scan | success |
| beta-beta-01-english | success |
| beta-beta-02-hausa | success |
| bundle-beta-evidence | success |
| provider-forensics | success |
| native-arkadia-golden-workflow | success |

6/6 `completed/success`; PR `mergeable_state: clean` against `main` `7580bd8f`. `main`'s own baseline
(`console-contract`, `boot-syntax`, `production-read-only-probe`, `browser`, `validate`, `test`) is likewise
`success` at this SHA — this branch introduces no new red gate. PR: **#539** (draft).

## 10. Next bounded task (one, explicit)

**Repair the lane instruction-doc drift** — update `AGENT-01..04` active-branch/PR pointers (and, if the
coordinator accepts it, the `SHARED-CONTRACTS.md` §1 branch map) to the live lane map in §3 above, on a
Lane-1/coordinator-owned branch from current `main` `7580bd8f`, guarded by a test that fails when an instruction
doc names a merged/closed PR as its active thread.

- **Scope:** `docs/control-plane/parallel-ui/AGENT-0{1,2,3,4}-*.md` (+ `SHARED-CONTRACTS.md` if authorized) and
  one new guard test under `tests/`.
- **Authority:** Lane 1 / coordinator doc ownership. No cross-lane source edit. No merge, deploy, or acceptance.
- **Evidence:** the stale-pointer set in §6, re-derived live at authoring time; guard negative control that feeds
  it a merged-PR pointer and asserts failure.
- **Regression boundary:** documentation + one new test file; no runtime, API, or authority surface.

---

## 11. Refresh — 2026-10-15T05:57:03Z (supersedes the inventory numbers in §1 and §3)

**Appended, not rewritten.** The §1/§3 tables are the 01:24:32Z observation and are left byte-identical as
provenance; the numbers below supersede them. Re-derived from live GitHub REST reads at `main` `7580bd8f`
(unchanged) plus local `git rev-list` for base lag. `lane-snapshot.json` in this directory has been regenerated
to the same schema with the current data.

### 11.1 Delta vs §1/§3

| Measure | §1 (01:24:32Z) | §11 (05:57:03Z) |
|---|---|---|
| Open PRs | 39 | **43** |
| L1 shell / nav | 11 | 11 |
| L2 NovaNet / opportunity | 4 | 3 |
| L3 Solariun / Knowledge | 5 | **7** |
| L4 Arkana / Weaver / Lab | 10 | **11** |
| Control-plane track | 8 | **11** |
| `clean` | 28 | 32 |
| `dirty` | 4 — #493, #501, #512, #530 | **4 — unchanged, same set** |
| `unstable` | 7 — #482, #499, #500, #502, #503, #508, #535 | **7 — unchanged, same set** |
| Contested files (≥2 PRs) | 40 | **40 — unchanged membership** |
| Draft | 39 of 39 | **43 of 43** |

**No head moved.** Every PR present in both observations has an identical `head`, `mergeable_state`,
`behind_main` and check count. The entire delta is four new PRs plus three lane re-classifications:

| PR | Branch | Lane | state | behind | checks |
|---|---|---|---|---|---|
| #540 | `feat/prism-l1-lane-doc-currency-01` | L1 | clean | 0 | 12 |
| #541 | `feat/prism-l4-weaver-self-withdrawal-01` | L4 | clean | 0 | 15 |
| #542 | `fix/prism-l3-graph-analytics-owner-scope-01` | L3 | clean | 0 | 11 |
| #539 | `prism-lane-state-reconstruction-01` | control-plane | clean | 0 | 6 |

**§3 lane-assignment corrections (measurement, not re-mapping).** Three PRs in §3's tables were filed under the
wrong lane. Each is moved here with the reason stated, so the earlier placement is not silently overwritten:

- **#496** (`docs/control-plane-live-recovery-2026-10-12`) — §3 listed it under Lane 1. It edits
  `SHARED-CONTRACTS.md` + `PRISM-UI-RECONCILIATION.md`, which the contract assigns to the **coordinator**, so it
  belongs to the control-plane track, not to a UI lane.
- **#504** (`gate10/prism-next-wave-composition-reconciliation-01`) — §3 listed it under Lane 1. It is a
  `gate10/` composition-reconciliation PR: control-plane, not shell.
- **#526** (`fix/knowledge-traverse-edge-dedup-01`) — §3 listed it under Lane 2 with a note that it "also touches
  Lane 3 test surface". Its changed files are knowledge-graph traversal and its subject is knowledge-edge dedup:
  **Lane 3**, not Lane 2.

Consequence for lane counts: L1 11→11, L2 4→3, L3 5→7, L4 10→11, control-plane 8→11. Only #526, #496 and #504
moved lanes; the L1 and L4 *increases* are new PRs (#540, #541), not re-classification.

### 11.2 The one uncounted PR of §1 is now accounted for

§1 reported `Open PRs = 39` while its own §3 tables enumerated 38. The refreshed snapshot enumerates **43 of
43** (sum of lane counts equals the headline). The gap was a counting convention, not a missing PR, and it is
closed: the machine-readable snapshot is now the single enumeration, and its per-lane counts sum to
`open_pr_count`.

### 11.3 Mergeability reading is unchanged, and still not a merge signal

All four `dirty` PRs remain in **Lane 4** and all four still touch
`web/arkadia_console/src/pages/EngineeringLabPage.tsx`. §4's warning stands verbatim: `clean` is a statement
about the PR's *own* recorded base, and 15 PRs are 8 commits behind `main`. `behind_main` distribution now:
`0:8, 2:2, 3:12, 7:4, 8:15, 10:1, 22:1`.

The two failing checks are unchanged and pre-existing: `provider-routing` (6 PRs — #482, #499, #500, #502,
#508, #535) and `trigger-coverage` (1 — #503). No new failing check appeared with the four new PRs.

### 11.4 Lane 3 contention did not grow

Lane 3 rose from 5 to 7 open PRs, but `knowledgeContracts.ts` still has exactly the same four claimants
(#498, #509, #527, #534). The two new Lane-3 PRs touch **no contested file**:

- **#526** — edge-dedup on the traversal path; disjoint from the contract module.
- **#542** — `api/knowledge_routes.py`, `knowledge/graph_health.py`, one new test file, one evidence file. All
  four paths are currently sole-owned; #542 composes with every open PR in the repository.

### 11.5 Doc-drift status moved — and the fix is already in flight

§10 named "repair the lane instruction-doc drift" as the next bounded task. It has since been **taken**:
**#540** (`feat/prism-l1-lane-doc-currency-01`, Lane 1) adds `scripts/lane_state.py`,
`docs/control-plane/parallel-ui/lane-state.json`, a `.github/workflows/lane-doc-currency.yml` gate and
`tests/test_lane_instruction_doc_currency.py`. Its snapshot already carries the live lane map for all four
lanes and marks Lane 3's doc **`doc_guard: deferred`, `deferred_to_pr: 526`** — i.e. #540 deliberately does
*not* edit `AGENT-03-SOLARIUN-KNOWLEDGE.md` while #526 owns that doc.

**This is why the Lane-3 pulse did not edit `AGENT-03-SOLARIUN-KNOWLEDGE.md`.** Editing it from a non-owning
lane would (a) violate `SHARED-CONTRACTS.md` exclusive file ownership and (b) collide with #540's own guard,
which requires the doc to agree with its snapshot. The drift is therefore **IN FLIGHT on Lane 1 (#540)**, not
open — §10's task is superseded.

### 11.6 Result classification for the refresh

| Boundary | State | Basis |
|---|---|---|
| Live inventory (43 PRs, per-lane, head/base/state) | **VERIFIED** | live REST reads; per-lane counts sum to the headline |
| Delta vs the 01:24:32Z observation | **VERIFIED** | head/state/behind/checks compared PR-by-PR; no head moved |
| Lane re-classification of #496/#504/#526 | **VERIFIED** | changed-file lists read from `/pulls/{n}/files` |
| Cross-lane composition safety | **UNCHANGED FROM §4** | still one lane measured fully; not re-composed this pass |
| Lane-3 doc-drift repair | **IN FLIGHT — #540** | not open; do not duplicate |
| Runtime / production / deployment identity | **NOT CLAIMED** | no runtime probe; out of scope for a state reconstruction |

### 11.7 Addendum — this addendum mutates no branch

Like §0/§9, this refresh is a **read + record**. It regenerated `lane-snapshot.json` and appended this section
on the PR's own branch. It created, merged, closed, retargeted and pushed **no** lane branch, and probed no
deployment. The one open question it does not answer — whether the 15 PRs 8 commits behind `main` still compose
— is left explicitly unmeasured rather than assumed.

---

## 12. Refresh — 2026-10-15T06:24:32Z (supersedes §1 and §3 inventory numbers again)

**Observed:** 2026-10-15T06:24:32Z · **`main`:** `7580bd8f0ca2925518d78775f9a323ff0df8bc66` (**unchanged** from §11 —
no merge landed between the 05:57Z and 06:24Z observations) · **open PRs:** **44** (was 43).

### 12.1 Correction — the §0 auth-boundary claim is wrong and must not be repeated

§0 states "`gh auth status` reports 'not logged into any GitHub hosts' — `gh` is **not** authenticated here."
**That is contradicted by measurement at this observation:**

```
$ gh auth status
github.com
  ✓ Logged in to github.com account Arkadia-Oversoul-Prism (GH_TOKEN)
  - Active account: true
  - Git operations protocol: https
$ GH_TOKEN="$github_token" gh api user --jq .login
Arkadia-Oversoul-Prism
```

The env `GITHUB_TOKEN` **is** empty (`${#GITHUB_TOKEN}` → `0`), and the automation contract already warns that an
empty env token is *not* a blocker. §0 reached the right conclusion by the wrong route (it fell back to the clone
remote credential) but recorded a false premise. **All §12 reads were made with `gh` + the ambient
`GH_TOKEN`/`github_token`.** Corrected here rather than rewritten in §0, because §0 is a dated observation and the
correction is the auditable fact. No token value is printed.

### 12.2 Lane 2 — defect verification (the pass's substantive measurement)

Lane 2 was the selected lane (least-recently-advanced: `#538` at 2026-10-14T22:31Z). `#538`
(`fix/prism-l2-buyer-recon-status-normalization-01`, head `1a36f235`, behind **0**) repairs status normalisation
only. Its diff against `main` is **one file, `solspire/buyer_recon.py`, +10/-3** — it normalises `status` into a
local `normalized` mapping and persists it upper-case. **It does not touch the evidence branch of the same
method.** Measured behaviour, `main` `7580bd8f` vs `#538` head `1a36f235`, same probe, isolated DB
(`SOLSPIRE_PROJECTS_DB=/tmp/p*.db`):

| # | Existing | Patch | `main` result | `#538` result | Verdict |
|---|---|---|---|---|---|
| A | `evidence=[{"kind":"old"}]` | `{"evidence":[{"kind":"new"}]}` | `[{"kind":"old"}]` | `[{"kind":"old"}]` | **evidence patch is a silent no-op** |
| B (negative control) | `evidence=[]` | `{"evidence":[{"kind":"new"}]}` | `[{"kind":"new"}]` | `[{"kind":"new"}]` | persists *only* because the row was empty |
| C | `evidence=[{"kind":"old"}]` | `{"evidence":[]}` | `[{"kind":"old"}]` | `[{"kind":"old"}]` | clearing evidence is a silent no-op |
| D | `status="CONTACTED"` | `{"status":"conversation"}` | `'conversation'` | `'CONVERSATION'` | `#538` genuinely fixes this |
| E | `prospect="A"` | `{"prospect":""}` | `''` | `''` | blank accepted; `create_entry` rejects blank |

**Mechanism (read from source, `solspire/buyer_recon.py::update_entry`).** `current` is seeded from
`self._entry(row).to_dict()`, so `current["evidence"]` is a **list**. The final loop then serialises with
`json.dumps(current.get("evidence") or patch.get("evidence") or [])` — the truthy existing list always wins, so a
non-empty `evidence` patch is discarded (rows A and C). Row B passes only because `[] or patch[...]` falls through
to the patch: **the negative control is what proves this is a precedence defect rather than "patches are
ignored."** `#538`'s change from `patch` to `normalized` is a *different* key (`normalized` has no `evidence` in
row A), so the defect survives the repair. Row E is a validation asymmetry: `create_entry` enforces
`prospect.strip()` non-empty; `update_entry` does not.

**Reachability.** `BuyerReconEntryPatch` is `ConfigDict(extra="allow")` with **no declared fields**, so
`{"evidence": [...]}` and `{"prospect": ""}` both reach the manager from
`PATCH /solspire/buyer-recon/entries/{id}` and `PATCH /solspire/buyer-recon/projects/{id}/entries/{entry_id}`.
This is not a dead branch — it is the documented patch surface. **No test pins it:** `update_entry` appears in
`tests/test_buyer_recon_router_board_scope.py:159` (board scoping) and in
`tests/test_prism_opportunity_entry_flow.py:773` (a *source-level string* assertion about status validation), and
both files pass on `main` (`22 passed in 1.73s`). So the defect is real, reachable, and **unpinned by any test** —
the negative control in row B is what makes that a finding rather than a guess.

**Classification:** `VERIFIED` as a defect present on `main` and still present at `#538`'s head.
**Not repaired by this pass** — `solspire/buyer_recon.py` is **Lane 2 owned** and this pass is a Lane-state
reconstruction whose hard constraint is that no lane source may be modified. Recorded as the next bounded Lane-2
task in §13.

### 12.3 Inventory delta vs §11 (05:57Z → 06:24Z)

- Open PRs **43 → 44**; the new PR is **#543** `gate03/knowledge-timeline-bounded-limit-01`
  (created 2026-10-15T06:27:47Z, **`unstable`**, behind 0, 11 checks) — governing **Lane 3**
  (`knowledge/timeline.py`, `api/knowledge_routes.py`, `tests/test_knowledge_timeline_boundary.py`).
- Lane distribution: **L1 11 · L2 3 · L3 8 · L4 11 · control-plane 11**.
  **Correction to a first reading of this pass.** A fresh keyword classifier initially reported
  **L1 9 · L2 3 · L3 8 · L4 17 · control-plane 7**; that was a *classifier defect*, not lane drift. It
  bucketed by file path only, so the explicitly lane-prefixed branches `feat/prism-l1-legacy-route-coverage-01`
  (#507) and `feat/prism-l1-lane-doc-currency-01` (#540) fell through to `control-plane`, and six
  `feat/eaa-*` / `feat/gate-l4-*` PRs (#496, #499, #500, #502, #508, #535) were pulled into `L4` by the
  `lab`/`weaver` substring in their paths. The re-derivation now preserves the prior snapshot's
  assignment and rule-classifies only genuinely new PRs, so #543 is the sole rule-classified addition.
  §3's Lane-2 count of 4 included
  `#526`, which is Knowledge-OS work; the live Lane-2 set is `#492`, `#528`, `#538`.
  **This is the third count correction in this record (Lane 3 was 5, then 7, now 8).** The cause is the same
  each time — a lane classifier keyed on paths rather than on the lane's own branch prefix — and it is the
  reason §3's per-lane numbers should be read as indicative, not as a stable series.
- **Correction: "branch prefix outranks a path heuristic" is FALSE as a governing rule — retracted.**
  An earlier revision of this section asserted that *"a PR's branch prefix is the lane's own declaration
  and outranks a path heuristic."* **Counterexample, measured:** **#500** is
  `feat/gate-l4-openhands-dispatch-adapter` — a branch whose own prefix declares **L4** — yet its lane is
  **`control-plane`** in **both** `d6e9e072` and `HEAD`. Its changed files are
  `weaver/openhands_dispatch.py`, `tests/test_gate_l4_*.py`, `.github/workflows/gate-l4-dispatch-contract.yml`
  and `docs/control-plane/gate-l4/**` — i.e. Weaver/control-plane surfaces, which is why control-plane is
  correct and the prefix is not. Symmetrically, #507 and #540 are `feat/prism-l1-*` and *are* L1, but #535
  (`eaa/chain-composition-01`) and #543 (`gate03/…`) carry no lane token at all. **No single rule reproduces
  the assignment in both directions**; the honest description is that the lane field is a **preserved prior
  assignment** with new PRs rule-classified, which is what the snapshot generator actually does. Recorded
  because the false rule would license a future pass to "fix" #500 to L4 and corrupt the record.
- `mergeable_state`: **32 clean · 8 unstable · 4 dirty**; dirty = `#493`, `#501`, `#512`, `#530` (unchanged set).
  unstable = `#482`, `#499`, `#500`, `#502`, `#503`, `#508`, `#535`, **`#543`**.
- **Schema disclosure — RETRACTED, corrected below (this record's own prior claim was FALSE).** The
  earlier revision of this section asserted that the snapshot committed at `f2fec7c5` was
  *structurally broken* — that its top-level keys were the five lane names instead of the document
  schema, and that `observed_at_utc`, `repository`, `main_sha`, `open_pr_count`, `lanes` and
  `contested_files` were "all absent". **That claim is disproven.** `git show f2fec7c5:<snapshot>`
  carries **all 16** top-level schema keys:
  `observed_at_utc, repository, main_sha, main_moved_since_previous_observation,
  previous_observation_utc, open_pr_count, mergeable_state_counts, dirty_prs, unstable_prs, lanes,
  contested_files, lane_selected_this_pass, lane_selection_basis, lane2_defect_probe, auth_boundary,
  mutations_this_pass`. The top-level key **set** is identical at `f2fec7c5` and `HEAD`
  (`set(a) == set(b)` -> `True`); only the **order** differs, and a consumer reading
  `snapshot["main_sha"]` at `f2fec7c5` succeeds. No schema repair was performed or needed.
  Two *real* shape differences do exist and are the entire cause of the large raw diff:
  the `lanes` **key name** was `CP` at `f2fec7c5` and is `control-plane` at `HEAD`, and
  `contested_files` is a **dict** at `f2fec7c5` and a **list** at `HEAD`. Both are deliberate
  re-normalisations in this record, not repairs of breakage.
- **Lane re-derivation — the false claim carried a true fact inside it.** The lane-membership churn
  is **8 moves, not 13**, and the direction was **the reverse of what was stated**. Measured
  mechanically across the three revisions:
  `d6e9e072 -> f2fec7c5` = 8 moves (`#496, #499, #500, #502, #507, #508, #535, #540`);
  `f2fec7c5 -> HEAD` = the **same 8** moves; and **`d6e9e072 -> HEAD` = 0 moves**.
  So `f2fec7c5` was the **anomalous** revision (the "buggy classifier" snapshot), and `HEAD` is a
  **restoration to the `d6e9e072` assignment** — the opposite of the earlier framing, which described
  the moves as "all of them the buggy classifier's" belonging to the earlier revision. Per-lane counts:
  `d6e9e072` = L1 11 · L2 3 · L3 7 · L4 11 · control-plane 11 (43 PRs);
  `f2fec7c5` = L1 9 · L2 3 · L3 8 · L4 17 · control-plane 7 (44 PRs);
  `HEAD` = L1 11 · L2 3 · L3 8 · L4 11 · control-plane 11 (44 PRs). The **+1 L3 and +1 total** versus
  `d6e9e072` is **#543** (`api/knowledge_routes.py`, `knowledge/timeline.py`,
  `tests/test_knowledge_timeline_boundary.py`) — Lane 3. The **0 per-PR key-order differences** claim
  was **verified true** and stands.
- **Why the false claim was made (recorded so it is not repeated).** The revision was mis-diagnosed by
  reading the `lanes` **key names** (`CP`, `L2`, `L4`, `L1`, `L3`) as if they were the document's
  top-level keys, then inferring the rest of the schema was absent. The top-level key set was never
  re-read. **A key-name observation about one nested object is not a schema observation** — the
  correction is `set(json.load(...))`, which is the check that should have preceded the disclosure.
- Contested files (touched by ≥2 open PRs): **40 → 42**. New: `api/knowledge_routes.py` (`#542`, `#543`) and
  `tests/test_knowledge_timeline_boundary.py` (`#498`, `#543`).
- Highest-contention surfaces unchanged: `EngineeringLabPage.tsx` **5×** (`#493`, `#501`, `#512`, `#524`, `#530`),
  `knowledgeContracts.ts` **4×** (`#498`, `#509`, `#527`, `#534`), `AGENTS.md` **3×** (`#482`, `#504`, `#538`),
  `test_console_shell_nav_contract.py` **3×** (`#497`, `#505`, `#512`).
- `main` **has not moved**; every PR's base lag in §3/§11 still holds at this observation.

### 12.4 Contract-doc ownership — one correction

`AGENT-01-SHELL.md` is no longer unclaimed: **#540** `feat/prism-l1-lane-doc-currency-01` (Lane 1, behind 0,
`clean`, 12 checks) edits it (+7/-4) and adds `scripts/lane_state.py`, `docs/control-plane/parallel-ui/lane-state.json`,
`tests/test_lane_instruction_doc_currency.py` and `.github/workflows/lane-doc-currency.yml`. §10's "next bounded
task: repair the lane instruction-doc drift" is therefore **already in flight on #540** — do not open a competing
doc-currency PR. `AGENTS.md` remains global and is still edited from three feature PRs (`#482`, `#504`, `#538`).

### 12.5 Self-audit of §12.3 — four claims were wrong; corrections and evidence

This sub-section exists because §12.3 was published (commit `b594bd27` and PR comment
`6186151005`) carrying claims that this pass then **disproved by re-measurement**. The audit
method is `git show <rev>:<snapshot>` + `set(json.load(...))` + live `gh` per-PR reads; every
number below is reproducible with those three commands.

| # | §12.3 claim | Measured truth | Verdict |
|---|---|---|---|
| 1 | `f2fec7c5` was *structurally broken*; schema keys "all absent" | `f2fec7c5` carries **all 16** top-level keys; `set(f2fec7c5) == set(HEAD)` -> `True`; `snapshot["main_sha"]` reads fine | **FALSE — retracted** |
| 2 | "13 lane moves, all of them the buggy classifier's" (moves belong to the *later* revision) | **8** moves, and they belong to **`f2fec7c5`**; `d6e9e072 -> HEAD` = **0 moves** | **FALSE — retracted** |
| 3 | "A PR's branch prefix … outranks a path heuristic" | **#500** is `feat/gate-l4-*` yet `control-plane` in **both** revisions | **FALSE — retracted** |
| 4 | §12.3 heading window `(05:57Z → 06:24Z)`, `observed_at_utc` `06:24:32Z` | **#543 was created `06:27:47Z`** — after the stated observation instant | **CONTRADICTED** |

**On (1) and (2) — the false claim and the true fact inside it.** The lane-membership churn was
described with the wrong magnitude *and* the wrong direction. Measured across the three revisions:

- `d6e9e072 -> f2fec7c5` = **8** moves: `#496, #499, #500, #502, #507, #508, #535, #540`
- `f2fec7c5 -> HEAD` = **the same 8** moves
- **`d6e9e072 -> HEAD` = 0 moves**

So `f2fec7c5` is the **anomalous** revision and `HEAD` is a **restoration to the `d6e9e072`
assignment** — the exact opposite of "all of them the buggy classifier's" belonging to the prior
snapshot. Per-lane counts: `d6e9e072` = L1 11 · L2 3 · L3 7 · L4 11 · control-plane 11 (43 PRs);
`f2fec7c5` = L1 9 · L2 3 · L3 8 · L4 17 · control-plane 7 (44 PRs); `HEAD` = L1 11 · L2 3 · L3 8 ·
L4 11 · control-plane 11 (44 PRs). The **+1 L3 / +1 total** vs `d6e9e072` is **#543**, Lane 3. The
"**0 per-PR key-order differences**" claim was **verified true** and stands.

Two *real* shape differences — not breakage — are the entire cause of the large raw diff: the
`lanes` **key name** is `CP` at `f2fec7c5` vs `control-plane` at `HEAD`, and `contested_files` is a
**dict** at `f2fec7c5` vs a **list** at `HEAD`.

**On (3) — the rule is falsified by its own dataset.** #500 (`feat/gate-l4-openhands-dispatch-adapter`)
declares L4 in its branch prefix yet is `control-plane` in both revisions, because its changed files
are `weaver/openhands_dispatch.py`, `tests/test_gate_l4_*.py` and `docs/control-plane/gate-l4/**` —
Weaver/control-plane surfaces. #535 (`eaa/chain-composition-01`) and #543 (`gate03/…`) carry no lane
token at all. **No single rule reproduces the assignment in both directions.** The accurate
description is that the lane field is a **preserved prior assignment** with genuinely new PRs
rule-classified. This matters: the retracted rule would license a future pass to "correct" #500 to L4
and corrupt the record.

**On (4) — the snapshot contains content that postdates its own observation timestamp.** The heading
window is `05:57Z → 06:24Z` and `observed_at_utc` is `06:24:32Z`, but `#543` was created at
`06:27:47Z`. The `#543` record therefore cannot have been observed at the stamped instant; the stamp
was not advanced when the record was refreshed. **The inventory content is correct; the timestamp
label is not.** Treat `observed_at_utc` in this record as a lower bound on the observation, not an
exact instant, and re-stamp it on the next refresh.

**Live drift since the snapshot (measured, not repaired).** At this audit the live mergeability is
**33 clean · 7 unstable · 4 dirty** against the snapshot's **32 · 8 · 4**: **`#543` has moved
`unstable → CLEAN`** (its 11 checks concluded; `failing_checks` was already empty). The dirty set is
unchanged (`#493`, `#501`, `#512`, `#530`). This is ordinary check-run convergence, **not** a defect
in the snapshot — the snapshot was correct when taken — but it is why the snapshot's
`mergeable_state_counts` should be read as a timestamped reading.

**Process note, recorded so it is not repeated.** All three false claims share one root cause: a
**nested key-name observation** (`lanes` keys, branch-prefix tokens) was promoted to a **whole-document
schema or governing-rule claim** without re-reading the top level. The correct check is
`set(json.load(...))` for schema and a full-dataset counterexample search for a rule. Publishing
before that check is what produced the retraction.

### 12.6 Classification for this refresh

| Boundary | State | Basis |
|---|---|---|
| `main` / ancestry | **VERIFIED** | `gh api commits/main` → `7580bd8f`, unchanged across two observations |
| Lane/PR inventory (44 PRs) | **VERIFIED** | live per-PR `gh api`, head/base SHAs, check-runs, mergeable_state |
| Cross-lane file contention | **VERIFIED (counts)** | per-PR `/files`, unioned; **composition safety not re-probed this pass** |
| Lane-2 `update_entry` evidence-patch defect | **VERIFIED (defect exists)** | 5-case probe with negative control, on `main` and on `#538` head |
| Lane-2 repair | **NOT PERFORMED** | lane source is off-limits to this reconstruction pass |
| §12.3's schema / lane-move / branch-prefix claims | **CONTRADICTED** | retracted in §12.5 with counterexamples |
| §12.3's `observed_at_utc` stamp | **CONTRADICTED** | content postdates the stamp (#543 created `06:27:47Z`) |
| Runtime / production / deployment | **NOT CLAIMED** | no runtime probe; out of scope |
| §0's `gh` auth premise | **CONTRADICTED** | corrected in §12.1 |

**No branch, PR, or lane source was modified by this refresh.** The only files written are this evidence record
and its `lane-snapshot.json` companion, on the existing draft branch `prism-lane-state-reconstruction-01`.

## 13. Next bounded task (revised)

**Lane 2 — repair `BuyerReconManager.update_entry` patch semantics**, on a Lane-2-owned branch from live `main`
(`7580bd8f`), scope limited to `solspire/buyer_recon.py` + `tests/test_buyer_recon_board_contract.py`:
1. give the patch precedence over the seeded `current` value for `evidence`
   (`json.dumps(patch["evidence"] if "evidence" in patch else current.get("evidence") or [])`);
2. reject a blank `prospect` the way `create_entry` does (parity, not new policy);
3. keep `#538`'s status normalisation — it is complementary, and merging `#538` first is the cheapest order.
Required evidence: a regression test per case (A, C, E) **plus the row-B negative control**, so the test proves
the patch is honoured rather than that evidence is ignored. Authority: none required — Lane-2 owns this file.
Do **not** fold this into `#538`; `#538` is a reviewed bounded repair and this is a separate defect.


## 14. Refresh — 2026-10-15T11:28:29Z (supersedes §13's next-bounded-task, and reclassifies four "conflicts")

Base `main` is **unchanged** at `7580bd8f0ca2925518d78775f9a323ff0df8bc66`. The lane inventory of
§12 is unchanged (L1 `[507,529,540]` · L2 `[528,538,544]` · L3 `[527,534,537,542]` ·
L4 `[512,524,536,541]`). Open PRs moved **44 → 45**: `set(now) - set(snapshot) == {544}` and the
removal set is empty, so exactly one PR (#544) is new and none closed. What changed is the
**interpretation** of two things this record previously reported without following through: the four
`CONFLICTING/DIRTY` lane PRs, and §13's chosen next task.

### 14.1 §13's next bounded task is already in flight — do not open a competing Lane-2 task

§13 proposed repairing `BuyerReconManager.update_entry` patch semantics on a new Lane-2 branch.
**That work already exists as PR #544** (`prism-l2-evidence-patch-replacement-01`), which this
record's own §12 inventory listed and did not connect to §13:

| Field | Measured |
|---|---|
| PR / branch | **#544** `prism-l2-evidence-patch-replacement-01`, `state=open`, `draft=true` |
| Head / base | `73575cd781d871b213b8dc5a9e1b93afeba88f2a` / `7580bd8f` (current `main`) |
| Created | `2026-10-15T07:28:35Z` — **63 minutes after** §13 was written |
| Files | `solspire/buyer_recon.py`, `tests/test_prism_opportunity_entry_flow.py`, `AGENTS.md`, and three evidence docs |

So §13 is **superseded as a task assignment**: opening it would duplicate a Lane-2 branch that
already targets the same file with the same scope. §13's *analysis* stands; its *instruction* does
not. This is the second time in this record that a "next task" was overtaken by a concurrent lane
pulse — the pattern is that this workstream advances faster than a 6-hourly evidence refresh, and a
task proposal must be re-checked against live PRs before it is repeated.

### 14.2 The four `CONFLICTING/DIRTY` lane PRs are **superseded**, not unresolved conflicts

§4 recorded `#493` and `#501` as `CONFLICT` and §5 quantified `EngineeringLabPage.tsx` contention.
This refresh measured *what the conflict actually consists of*, and the answer changes the
disposition. PR #533 (`aeas/engineering-lab-composition-01`, head `8d52eb3f`, merge commit
`7580bd8f` — **confirmed an ancestor of `main`** by `git merge-base --is-ancestor`) already composed
the seven L4 candidates. Comparing each dirty PR's own head against current `main`, per file:

| PR | File | PR-head blob | main blob | Content unique to the PR head |
|---|---|---|---|---|
| #493 | `components/lab/LabAutomationGrammar.tsx` | `5af30fef` | `5af30fef` | **identical** |
| #493 | `components/lab/labAutomationGrammar.ts` | `6fc78bf5` | `6fc78bf5` | **identical** |
| #493 | `pages/EngineeringLabPage.tsx` | `e53a2250` | `4ff0fa78` | 3 lines — the inline `rows={Object.entries(overview.data).slice(0, 12).map(...)}` Facts expression |
| #493 | `tests/test_prism_next_wave_composition_reconciliation_01.py` | `cad8bd65` | `3305ec80` | 42 lines; `main` is the larger/superset file (340 vs 109 lines) |
| #501 | `pages/EngineeringLabPage.tsx` | `1f851406` | `4ff0fa78` | 3 lines — same inline expression |
| #512 | `components/lab/LabOperationalSurfaces.tsx` | `06e3a522` | `06e3a522` | **identical** |
| #512 | `components/lab/labOperational.ts` | `c5ae3215` | `c5ae3215` | **identical** |
| #512 | `pages/EngineeringLabPage.tsx` | `cbf272c9` | `4ff0fa78` | **0 lines** |
| #530 | `pages/EngineeringLabPage.tsx` | `502e23f9` | `4ff0fa78` | 4 lines — same inline expression, plus a stale docstring line |

The unique residue is not competing design. `main` replaces the inline expression with the shared
helper `scalarOverview(overview.data)` (`components/lab/labOperational.ts:229`, imported at
`EngineeringLabPage.tsx:10`), and `#530`'s extra line is an older docstring ("read straight from the
overview payload") where `main` reads "read directly from the overview response". Every residue line
is **an earlier form of content `main` already carries in a later form**. `#512` has zero page
residue and byte-identical component blobs.

**Consequence for the disposition:** these four are not conflicts awaiting a resolution — they are
**superseded candidates for close**. `CONFLICTING/DIRTY` here is an artifact of a stale base
(`49809f4`/`3ca8582`) plus git's inability to see that the "conflicting" content is already present
in a superseding form. Closing or merging them is a **human-sovereign action**; this pass
recommends and does not perform it. A repair or rebase of any of the four would re-introduce content
that `main` has already moved past.

### 14.3 `AGENTS.md` is contested by **five** open PRs, and the contention is an append-anchor collision

This pass re-derived the contention set from scratch rather than trusting §5's or §12's list: over
all 45 open PRs, `GET /pulls/{n}/files`, unioned by path. **45 paths are touched by more than one
open PR.** `AGENTS.md` is touched by **five**: `#482`, `#504`, `#538`, `#540`, `#544` — §12's
snapshot recorded three (`482, 504, 538`) because it predates `#540` and `#544`.

The five are not independent: each appends a lesson block at the **same tail anchor**.

- `main` `AGENTS.md` = **1560** lines, ending at the `security-lab-remote-userinfo-redaction-01` bullet;
- **#540** appends **+28** lines (a `lane_state.py` guard-hygiene lesson);
- **#544** appends **+21** lines (a composition-is-a-branch-merge lesson).

Merge-probed in a detached worktree at `7580bd8f` (`user.email`/`user.name` set first — see §14.4):

| Step | Result |
|---|---|
| `git merge --no-commit --no-ff` **#540** alone | *"Automatic merge went well"* — 0 conflicts |
| `git merge --no-commit --no-ff` **#544** on top | **CONFLICT (content) in `AGENTS.md`**; 0 other conflicted paths |

The conflict is **textual only**: both are append-only additions at one anchor, so the resolution is
mechanical (keep both blocks, in either order). Git cannot auto-merge it because the two hunks share
the same trailing context. **Generalise the hazard rather than the instance:** `AGENTS.md` is a
single file that every lane pulse is instructed to append its lesson to, so a five-way append
contention is the *expected* steady state of this workstream, not an accident. Each PR is green
alone; the collision exists only in composition, and only the composition reveals it. Recorded as a
**decision for the sovereign**, not a repair: the mechanical resolution (concatenate both blocks) is
safe, but who performs it and in which merge order is a human call.

The same derivation found two other contention classes worth naming, because they are *code*, not
docs:

| Path | PRs | Note |
|---|---|---|
| `web/arkadia_console/src/pages/EngineeringLabPage.tsx` | `493, 501, 512, 524, 530` | five-way; §14.2 shows four of the five are superseded |
| `web/arkadia_console/src/pages/knowledge/knowledgeContracts.ts` | `498, 509, 527, 534` | four-way; all four are L3/Lane-3, i.e. **within-lane** contention |
| `web/arkadia_console/src/App.tsx` | `511, 514` | the Lane-1 seam file — cross-lane edits here must be Lane-1-coordinated |
| `tests/test_prism_opportunity_entry_flow.py` | `492, 538, 544` | Lane-2; `#538` and `#544` are both open and both target `solspire/buyer_recon.py` |

### 14.4 Method corrections for this record's own tooling (third such audit)

§12.5 retracted four claims from §12.3. This pass retracts four **measurement-method** errors made
while producing this refresh, recorded so the next pass does not repeat them:

| # | What was run | What it actually measured | Correct form |
|---|---|---|---|
| 1 | `git diff <head>~1 <head>` on a `--depth=1`-fetched PR head | **0 files for all four PRs** — a depth-1 fetch has `parents=1`, so `~1` does not resolve to the real parent | fetch the **branch** with `--depth=N`, or read changed files from the API |
| 2 | Parsing `diff --git` / `+++ b/` with a regex for `b/…` | false "NEW FILE on main" for `web/arkadia_console/...` — the `b/` inside `web/` matched | `git apply --numstat <patch>` or `GET /pulls/{n}/files` |
| 3 | `git merge` in a fresh worktree | died with *"unable to auto-detect email address"*, which reads as a merge failure | set `user.email`/`user.name` in the worktree first |
| 4 | `git fetch --depth=1 origin <sha>` then `git merge <sha>` | *"refusing to merge unrelated histories"* — a bare-SHA fetch yields a parentless commit | fetch `refs/remotes/x/<name>` from the branch, then merge that ref |

Correction (1) is the one that matters: it produced a **false "0 files changed"** for four PRs
simultaneously, and the shape of the false result (uniformly zero) is what exposed it.

### 14.5 Classification for this refresh

| Boundary | State | Basis |
|---|---|---|
| `main` / ancestry | **VERIFIED** | `7580bd8f`, unchanged across three observations; `8d52eb3f` confirmed ancestor |
| Lane/PR inventory (44→45 PRs) | **VERIFIED** | live per-PR `gh api`; L1/L2/L3/L4 sets identical to §12; delta = `{544}` only |
| §13's next bounded task | **CONTRADICTED** | superseded by PR #544 (created `07:28:35Z`, same file/scope) |
| `#493`/`#501`/`#512`/`#530` "conflicts" | **RECLASSIFIED → superseded** | per-file blob comparison vs `main`; residue is earlier forms of content `main` carries |
| `AGENTS.md` five-way contention (`482,504,538,540,544`) | **VERIFIED (textual)** | merge probe: 540 clean, 544 on top conflicts in exactly one file |
| Cross-PR path contention (45 shared paths) | **VERIFIED (counts)** | per-PR `/files` unioned; **composition safety not probed beyond `AGENTS.md`** |
| Disposition of the four superseded PRs | **NOT PERFORMED — sovereign** | close/merge is a human action; recommendation only |
| Runtime / production / deployment | **NOT CLAIMED** | no runtime probe; out of scope |

**No lane source was modified by this refresh.** Files written: this record and its
`lane-snapshot.json` companion, on the existing draft branch `prism-lane-state-reconstruction-01`.

