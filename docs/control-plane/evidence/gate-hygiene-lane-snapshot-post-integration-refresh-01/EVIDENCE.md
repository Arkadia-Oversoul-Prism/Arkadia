# EVIDENCE — lane snapshot re-derivation after the #664–#667 merge wave

**Pulse:** Weaver hourly bounded execution, 2026-11-20T03:05Z
**Base:** `main` `5f40e65c7a13b934f63f24310ffda90d5b18b351`
("integration: EWOR evidence baseline for #663–#667 (#668)")
**Branch:** `gate-hygiene/lane-snapshot-post-integration-refresh-01`
**Disposition:** REPAIRABLE → repaired. Merge execution remains human-only (GOV-03).

---

## 1. Defect — `lane-doc-currency` is RED on `main`

Measured on `main` itself, not inferred from a PR:

```
$ gh run list --workflow lane-doc-currency.yml --branch main --limit 3
44663630663  failure  5f40e65c  2026-11-20T02:50:39Z   <-- current main
44659975080  success  a6fe4dda  2026-11-20T02:19:39Z
44044579030  failure  f9bd8da9  2026-11-17T08:11:11Z
```

The failing step is `Verify lane PR state against GitHub (authoritative oracle)`
(`python scripts/lane_state.py --check --verify-live`), which exits **1** with **8**
`DRIFT` findings:

```
DRIFT PR #664 (lane 4 open_prs) is recorded as open but is MERGED (merge commit 210637e8)
DRIFT PR #665 (lane 1 open_prs) is recorded as open but is MERGED (merge commit caac3949)
DRIFT PR #666 (lane 2 open_prs) is recorded as open but is MERGED (merge commit 4dd4c05d)
DRIFT PR #667 (lane 3 open_prs) is recorded as open but is MERGED (merge commit 97dbe012)
DRIFT lane 1 (AGENT-01-SHELL.md) declares PR #665, which is MERGED
DRIFT lane 2 (AGENT-02-NOVANET-OPPORTUNITY.md) declares PR #666, which is MERGED
DRIFT lane 3 (AGENT-03-SOLARIUN-KNOWLEDGE.md) declares PR #667, which is MERGED
DRIFT lane 4 (AGENT-04-ARKANA-WEAVER-LAB.md) declares PR #664, which is MERGED
```

Reproduced locally at the same SHA: `--check` exit 0, `--check --verify-live` exit **1**,
8 DRIFT.

### Cause — the snapshot aged inside one merge wave

The snapshot is **derived**, and it was correct when written. `lane-state.json` records
`observed_at 2026-11-16T18:18:03Z` / `base_main f9bd8da9`, and was last re-derived by PR
#663 (merged `a6fe4dda`, 02:19:37Z). The four lane PRs merged **seven to eight minutes
later**:

| PR | merged_at | merge commit |
|---|---|---|
| #663 (snapshot refresh) | 02:19:37Z | `a6fe4dda` |
| #666 | 02:22:22Z | `4dd4c05d` |
| #667 | 02:25:14Z | `97dbe012` |
| #664 | 02:26:48Z | `210637e8` |
| #665 | 02:27:24Z | `caac3949` |
| #668 (integration) | 02:50:36Z | `5f40e65c` |

So the snapshot recorded four PRs as `open_prs` that were still open at derivation time and
merged minutes later. This is the structural class already recorded in `AGENTS.md` ("a lane
snapshot that records its own PR open reddens `main` the instant it merges"), recurring here
because four lane PRs merged after the refresh rather than one.

**This is not a guard defect.** The guard read its input correctly; its input was stale. The
repair re-derives the input and re-points the docs — the oracle is not weakened.

## 2. Repair

Confined to the snapshot's own guarded surface (`docs/control-plane/parallel-ui/**`):

1. **Snapshot re-derived, not hand-edited.** `scripts/lane_state_refresh.py --write
   --base-main 5f40e65c…`. All four lanes move `open_prs` → `merged_prs`, `doc_guard`
   becomes `idle`, `active_pr`/`active_branch` become `None`, and the stale
   `unassigned_open_prs` entries for the merged #663 are cleared. Hand-editing is not
   equivalent: the next refresh would disagree with it.
2. **All four lane docs gain an appended `**Active thread:** none` block.** The declaration
   is *appended*, never a rewrite of the superseded pointer — `declared_idle()` is
   last-wins by position, so the earlier `**Active PR:** #66x` blocks stay byte-identical as
   provenance. Precedent for repairing all four docs in one snapshot change: `b5bc34cb`.

No guard, workflow, test, or CI logic changed. `scripts/lane_state.py`,
`scripts/lane_state_refresh.py`, `tests/test_lane_instruction_doc_currency.py` and
`.github/workflows/lane-doc-currency.yml` are untouched.

## 3. Verification

| Check | Before | After |
|---|---|---|
| `python scripts/lane_state.py --check` | exit 0 | exit **0** |
| `python scripts/lane_state.py --check --verify-live` | exit **1**, 8 DRIFT | exit **0**, 0 DRIFT |
| `tests/test_lane_instruction_doc_currency.py` + `tests/test_lane_currency_ci_wiring.py` + `tests/test_lane_aggregate_pr_classification.py` | — | **82 passed** |
| `tests/architecture` | — | **11 passed** |
| `python -m py_compile api/main.py` | — | **OK** (2591 lines, budget 2600) |
| CP10 mutation boundary (`--judge`) | — | **PASS** |

### Negative control — the guard bites on the pre-repair state

The offline check alone does **not** discriminate (pre-repair, the docs agreed with the
stale snapshot, so `--check` was already exit 0). The defect lives in the **live** oracle, so
the control was run there:

```
$ git checkout HEAD -- docs/control-plane/parallel-ui/   # pre-repair state
$ python scripts/lane_state.py --check --verify-live
PRE_REPAIR_VERIFY_LIVE_EXIT=1
DRIFT count = 8          # exactly the CI findings, same PRs, same merge commits
```

The repair was then restored byte-identically and both checks returned to exit 0 / 0 DRIFT.
The control therefore proves the oracle detects the defect it claims to detect, rather than
merely passing on the repaired tree.

## 4. Recorded, not repaired

Two other non-success checks exist on `main` `5f40e65c` and are **not** attributable to this
change:

- **`browser`** (`canonical-render-browser-smoke.yml`) has failed on **every** `main`
  revision since `b9297ab9` (2026-11-06) — 12 consecutive runs. Cause, read from the step
  log: every canonical route returns HTTP 200 with content, but each page logs two
  `Failed to load resource: the server responded with a status of 401` console errors from
  an anonymous session, and the harness treats any console error as `FAIL`. That is a
  production-runtime/auth-boundary observation, not repository-source debt. Out of scope for
  a lane-currency repair; recorded as a separate proposed workstream.
- **PR #657** (`feat/chief-agent-foundation-001`, draft) is the only open PR. It touches 14
  authority surfaces (`api/main.py`, `api/executive_routes.py`, `api/lab_routes.py`,
  `api/openapi_security.py`, `lab/engineering_lab/*`, `weaver/*`,
  `scripts/cp10_mutation_boundary_policy.py`, `solspire/voice_pipeline.py`) plus 26
  `executive_office/` files. Classified **HUMAN_AUTHORITY_REQUIRED** on M4/M12 scope,
  independent of CI. It is 16 commits behind `main`; a diff against `main` reads as
  destructive and is pure staleness — measure against its own merge base `a1009ddf`.

## 5. Composition hazard — measured, and it constrains merge order

The repair appends a block to the **end** of each of the four lane docs. A lane PR branched
from the *pre-repair* `main` and carrying its own appended `**Active PR:**` block therefore
conflicts textually at EOF. Measured in a detached worktree at `5f40e65c`:

```
$ git merge --no-edit gate-hygiene/lane-snapshot-post-integration-refresh-01
Auto-merging docs/control-plane/parallel-ui/AGENT-01-SHELL.md
CONFLICT (content): Merge conflict in docs/control-plane/parallel-ui/AGENT-01-SHELL.md
```

The hazard is an artifact of the stale base, not of the repair: a lane PR opened from the
**repaired** `main` merges with zero conflicts and the guard judges it correctly —

```
$ (probe branch from repaired main appending **Active PR:** #999)
$ python scripts/lane_state.py --check
  DRIFT lane 1 (AGENT-01-SHELL.md): declares PR #999, which is not an open lane PR in the
  snapshot (open: [])
```

which is the *correct* finding (a pointer was declared and the snapshot has not been
re-derived for it yet). Two consequences for the next pulse:

1. **Open the next lane PR from `main` after #669 merges**, never from the pre-#669 tree.
   This is already the lane-scheme rule (N4 — branch from freshly fetched `main`); the
   measurement shows it is now load-bearing for merge cleanliness as well.
2. **A lane PR that appends its own pointer and a snapshot refresh must land together**, or
   the pointer will be judged against a snapshot that does not yet list it. That is the same
   one-change rule §2 of this record applies to the repair itself.

## 6. Boundaries preserved

- No merge was executed. GOV-03 makes merge execution human-only; this PR is `draft` and
  stays draft until a human reviews and merges it.
- No deployment, no production mutation, no Vercel interaction (ADR-016: the sole canonical
  origin is `https://arkadia-qzu4.onrender.com`).
- No authority, identity, K15/K3, approval-enforcement, or constitutional surface touched.
- No lane PR was opened: all four lanes are now idle, and this change *is* the
  reconciliation that had to precede lane continuity. Lane continuity is the next pulse's
  first action.

---

## 7. Refresh after the #657 merge — 2026-11-20T04:56Z

**This section supersedes §4's snapshot measurements and §3's open-PR inventory. Sections 1–6
are retained unedited as the provenance of the original repair.**

### 7.1 Why the refresh was required

The measurements above were taken at `main` `5f40e65c`. `main` has since advanced to
`b842892b9fc64dede5e655db0d293da77248a430` (squash of PR #657, the Arkadia Chief Agent
founding scaffold), so this PR was 1 commit behind and its snapshot's `base_main` named a
superseded revision.

Two facts made a refresh necessary rather than cosmetic:

1. The snapshot recorded **PR #657 as `unassigned_open_prs`**. #657 is now merged, so that
   entry named an open thread that no longer exists.
2. The recorded evidence predated the merge, so no statement in it was a measurement of the
   tree the merge produced.

### 7.2 What changed

```
$ git rebase origin/main            # clean, no conflicts
$ python scripts/lane_state_refresh.py --write --base-main b842892b9fc6...
wrote docs/control-plane/parallel-ui/lane-state.json
```

Re-derivation — not a hand-edit. The snapshot diff against the rebased head is **one file,
7 insertions / 7 deletions**:

```
- "observed_at": "2026-11-20T03:09:11Z"
- "base_main":   "5f40e65c7a13b934f63f24310ffda90d5b18b351"
+ "observed_at": "2026-11-20T04:56:38Z"
+ "base_main":   "b842892b9fc64dede5e655db0d293da77248a430"

  "unassigned_open_prs": [
-   { "number": 657, "title": "feat: establish Arkadia Chief Agent founding scaffold", ... }
+   { "number": 669, "title": "fix(lane-currency): re-derive the lane snapshot ...", ... }
  ]
```

The four lane docs and the four `merged_prs` lists are **unchanged** — the #664–#667
reconciliation this PR was written to perform still holds. Only the two derived scalar fields
and the `unassigned_open_prs` membership moved.

### 7.3 Why #657 touches none of this PR's files

Measured, not assumed:

```
$ git log --oneline 5f40e65c..b842892b -- docs/control-plane/parallel-ui/ \
      scripts/lane_state.py scripts/lane_state_refresh.py \
      tests/test_lane_instruction_doc_currency.py tests/test_lane_currency_ci_wiring.py
0
```

#657 changes zero files under `docs/control-plane/parallel-ui/` and zero lane-currency
surfaces, so the rebase was textually trivial. The refresh is a **record-currency**
requirement (the snapshot named a merged PR open), not a conflict repair.

### 7.4 Verification on the rebased head

```
$ python scripts/lane_state.py --check
base main: b842892b… (current: b842892b…)
lane instruction docs consistent with snapshot (4 guarded lanes)          exit 0

$ python scripts/lane_state.py --check --verify-live
live PR state: 4 PR(s) read from Arkadia-Oversoul-Prism/Arkadia (0 claimed-open + declared doc pointers)
lane instruction docs consistent with snapshot (4 guarded lanes)          exit 0

$ python -m pytest tests/test_lane_instruction_doc_currency.py tests/test_lane_currency_ci_wiring.py -q
67 passed

$ python -m pytest tests/architecture -q
11 passed

$ python -m pytest tests/test_m02a_ci_gate_integrity.py -q
76 passed

$ git diff --name-only | python scripts/cp10_mutation_boundary_policy.py --judge
Mutation boundary PASS (M02A legitimate-surface + constitutional denylist)   exit 0
```

`base_main == current main` and both gate modes are green — the two conditions the original
head satisfied only against the older `main`.

### 7.5 The snapshot now records this PR, and that is safe post-merge

Re-derivation necessarily writes the snapshot while this PR is open, so `unassigned_open_prs`
now names **#669 itself**. Checked against the live decision function rather than assumed:

```
$ python -c "import lane_state as L; print(L.claimed_open_prs(state))"
{}                              # empty -> #669 is in no judged open-claim
```

`claimed_open_prs` collects only `lanes[*].open_prs` and `lanes[*].deferred_to_pr`.
`unassigned_open_prs` is **written and printed but judged nowhere** (`grep -rn
unassigned_open_prs scripts/lane_state.py` → no reader). So #669's presence there cannot
redden `lane-doc-currency` after this PR merges, unlike the `open_prs` self-inclusion defect
recorded in `AGENTS.md` for #610/#614.

This is stated as a limitation, not a guarantee: if a future change wires `unassigned_open_prs`
into a judgement, this snapshot becomes a self-referential open-claim and will need
re-derivation. That wiring is a separate bounded workstream — it changes what the gate judges.

### 7.6 Boundaries preserved by this refresh

- No merge executed. GOV-03 reserves merge execution to a human; this PR remains **draft**.
- No deployment, no production mutation, no Vercel interaction (ADR-016).
- No change to the guard, its decision logic, or any authority surface. The repair remains
  scoped to one snapshot plus four appended doc blocks.
- The four lane docs are untouched by this refresh; their appended `**Active thread:** none`
  blocks from §3 stand byte-identical.
