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
