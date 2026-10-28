# Lane-doc task currency — discharge delivered tasks and refresh the snapshot

Pass: 2026-10-28. Base: `origin/main` `4de6fc4d8e52553985a7b5d6183d53f1017f8d44`.
Head: `lane-doc-task-currency-01`.

## 1. What the pointer guard cannot see

`scripts/lane_state.py` judges whether a lane doc's **declared pointer is open**
(`check_lane_docs`), whether a lane that declares idle really is idle, and whether the
snapshot is stale against guarded-path movement (`_freshness_findings`). It does **not**
judge whether the task a doc points at is still to do.

So a doc can be fully green and still instruct a successor agent to resume finished work
or to chase a thread that no longer exists. That is the defect repaired here.

## 2. Measured drift (live at `4de6fc4d`, zero open PRs repository-wide)

`gh pr list --state open` -> count **0**. `lane_state_refresh.py` -> every lane
`doc_guard=idle`, `open_prs=[]`, `unassigned_open_prs=[]`.

| Doc | Stale forward-looking claim | Measured truth |
|---|---|---|
| `AGENT-01` | "once #548 and #555 land or are superseded, re-point `AGENT-03`/`AGENT-04`" | #548 and #555 both **closed unmerged**; #584 already re-pointed both lanes to idle. Handoff discharged. |
| `AGENT-02` | "close #528 once #492 is reviewed" | #528 **closed unmerged**; #492 **merged** (`7030ccb2`). |
| `AGENT-02` | "#548 and #555 ... install their own pointers" | Both closed; paragraph describes a handoff that no longer exists. |
| `AGENT-02` | "next bounded task: wire the reaction write path" (x3) | **Delivered** — `api/transmissions.py` handler, `EngagementBar.tsx` client mounted in `NovaNetPage.tsx`. |
| `AGENT-03` | "next bounded task: load older events control" | **Delivered** — `KnowledgeTimelinePanel.tsx` `loadOlder`/`onLoadOlder`. |
| `AGENT-04` | "Immediate continuation task: traceable run-to-evidence view" | **Delivered** — `LabRunTrace.tsx` + `labRunTrace.ts` (`eb874fd6`). |

### The "truncation" hint, resolved

The task text's truncation hint is `AGENT-02`'s echo-panel notice. Its owning thread was
**PR #528** ("NovaNet echoes panel states total and notices truncation"), which is **closed
unmerged**; the work landed via **#492**. The notice is on `main` —
`NovaNetPage.tsx:59` `ECHO_DISPLAY_LIMIT`, `:248` `data-testid="novanet-echoes-truncation"`
— pinned by `tests/test_prism_novanet_echoes_completeness.py`. The stale artifact was
`AGENT-02`'s disposition sentence, repaired in §3. No separate truncation defect exists.

## 3. Change

Appended a dated `## Task currency — 2026-10-28` block to each of the four lane docs, and
refreshed `lane-state.json` **in the same commit**.

Append, never rewrite: each doc's last-wins `**Active thread:** none` idle declaration
stays authoritative (`declared_idle`, `declared_pr` are position-based). The added blocks
declare no pointer, so they cannot change any lane's disposition.

Same-commit refresh is mandatory, not stylistic: `_freshness_findings` treats a guarded
lane doc changed after the newest snapshot commit as **staleness**, so doc edits landing
without a refresh would redden `main` on merge.

## 4. Proof

| Check | Result |
|---|---|
| `pytest tests/test_lane_instruction_doc_currency.py` | **46 passed** |
| `pytest tests/test_lane_instruction_doc_currency.py tests/test_lane_currency_ci_wiring.py` | **58 passed** |
| `lane_state.py --check --verify-live` | exit **0**, "lane instruction docs consistent with snapshot (4 guarded lanes)" |
| Targeted suites for every discharged task | **118 passed** |
| `pytest tests/architecture -q` | **11 passed** |
| CP10 mutation boundary `--judge` | **PASS** |

### Negative control (the guard is not trivially green)

The oracle's window is computed over committed `main`, so the control must simulate
`main`. Branch `nc-defect` = `origin/main` + the four doc edits **without** the snapshot
refresh, with `refs/remotes/origin/main` moved to it:

- guard -> **1 failed, 45 passed** (`test_live_snapshot_is_fresh_against_current_main`)
- `lane_state.py --check` -> exit **1**, `DRIFT snapshot is stale: 1 commit(s) since it
  was recorded (6d299eb8) changed a guarded lane doc`

The same tree with the refresh included -> **46 passed**, exit 0. So the guard detects the
defect this change avoids, and the control was reverted (`origin/main` restored to
`4de6fc4d`, branch deleted).

## 5. Base correction (a real defect the guard caught in this pass)

The first cut was branched from the **stale local `main`** `6d299eb8`, not live
`origin/main` `4de6fc4d`, and the guard failed with "`base_main` is not an ancestor of
HEAD". Rebased onto `origin/main`; `git merge-base --is-ancestor origin/main HEAD` now
holds. The snapshot's `base_main` is the live `4de6fc4d`.

## 6. Scope and limits

- Docs + snapshot only. No source, no API, no authority, no identity, no deployment
  configuration. `api/main.py` untouched.
- **No production or acceptance claim.** This is a repository-source and guard-verified
  statement about lane instruction currency.
- Recorded, **not repaired** (out of scope): the guard's `current_lanes(state)` scope is
  derived from the snapshot's own `doc_guard` field, so a refresh can widen the gate's
  teeth onto a lane whose doc it does not repair — already noted for sovereign review in
  `docs/control-plane/evidence/lane-currency-truth-01/EVIDENCE.md` §8.
