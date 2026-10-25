# Lane-state refresh — clear the `#563` drift on `main` (lane-state-refresh-01)

## Objective

`main`'s committed lane snapshot declares PR #563 as an open lane-3 thread. #563 was
**closed without merging** at `2026-10-25T05:16:10Z`, *after* the snapshot was written
(`observed_at 2026-10-25T04:48:21Z`, merged as `3a1088c5` at `05:13:01Z`). The guard's
authoritative oracle therefore reports a blocking `DRIFT` finding, and `main` is red the
next time the gate runs. This pass re-measures the snapshot from live GitHub PR state and
commits the refresh.

## Measured at

- base `main`: `36f53be22d753ffe269f05cbf3fb39212f744207`
- branch: `gate-hygiene/lane-state-refresh-01`

## 1. Correction of the inherited premise: `main` is *latently* red, not observed-red

The inherited premise was "`main` lane-currency is currently RED". That is **half right and
materially mis-stated**. `main`'s most recent run of the gate was a **success**
(run `40164716935`, `2026-10-25T05:13:04Z`, commit `3a1088c5`). What is true is that the
snapshot it shipped went stale **three minutes later**, and the gate is **path-filtered**
so nothing since has executed it:

| fact | value |
|---|---|
| snapshot `observed_at` | `2026-10-25T04:48:21Z` |
| `3a1088c5` merged | `2026-10-25T05:13:01Z` (gate run: **success**) |
| #563 closed unmerged | `2026-10-25T05:16:10Z` |
| `main` HEAD `36f53be2` | touches only `docs/control-plane/evidence/lane-currency-truth-01/EVIDENCE.md` → **0** filter paths |

So the correct classification is **latent red / unexecuted**, not observed red. This matters
because it changes what the repair must be: the snapshot is wrong on its face, and the gate
would fail the moment any lane-doc or `scripts/lane_state*.py` path is touched — which the
four open lane PRs all do.

## 2. The blocking finding, reproduced

Pre-repair (`main`'s committed snapshot), `python scripts/lane_state.py --check --verify-live`:

```
live PR state: 16 PR(s) read ... (14 claimed-open + declared doc pointers)
  DRIFT PR #563 (lane 3 open_prs) is recorded as open but is CLOSED without merging;
  the thread is dead -- re-measure the lane PRs and re-point the lane, do not send an
  agent to it
exit 1
```

## 3. Repair and negative control

`scripts/lane_state_refresh.py --write` (the helper shipped by `3a1088c5` precisely to
remove hand-transcription) re-derives the snapshot from live PR state. Diff is **one file,
+25/-12** — `docs/control-plane/parallel-ui/lane-state.json` only:

- `#563` removed from lane 3 `open_prs`, added to `closed_unmerged`
- lane 3 `active_pr` `563 → 548` (branch `integration/knowledge-search-graph-boundaries-01`)
- `#567`/`#568` recorded as unassigned open PRs
- `observed_at` and `base_main` re-measured

Negative control — revert the refresh, the guard must re-redden, then restore:

| tree | `--check --verify-live` exit |
|---|---|
| pre-repair (`main`'s snapshot) | **1** |
| post-repair | **0** |

A repair that does not flip the exit code is not a repair; this one does, and reverting it
reproduces the original failure.

Post-repair the guard reports `lane instruction docs consistent with snapshot (2 guarded
lanes)` plus **two non-blocking NOTEs** (lane 3 declares closed #450; lane 4 declares merged
#428). Those NOTEs are pre-existing and belong to the *lane owners*, not to this guard — the
guard itself says "lane not owned by this guard; reported, not blocking". They are recorded,
not repaired, here.

## 4. Verification

| check | command | result |
|---|---|---|
| targeted lane guard | `pytest tests/test_lane_instruction_doc_currency.py tests/test_lane_currency_ci_wiring.py -q -rEf` | **49 passed** |
| architecture fitness | `pytest tests/architecture -q` | **11 passed** |
| CP10 mutation boundary | `printf '<paths>' \| python scripts/cp10_mutation_boundary_policy.py --judge` | **PASS** |
| guard offline | `python scripts/lane_state.py --check` | exit **0** |
| guard live oracle | `python scripts/lane_state.py --check --verify-live` | exit **0** (was 1) |

`api/main.py` is untouched, so no boot-syntax or line-budget exposure.

## 5. Relationship to the stacked chain — why this is the minimal slice

Four open PRs contend for this file (`#548`, `#553`, `#555`, `#568`). Measured against the
live API, **all three** of `#548`/`#553`/`#555` already have a snapshot with **0** occurrences
of `563` — they carry equivalent refreshes as passengers. `#568` carries the refresh *plus*
two larger changes, and **`#568` is itself red** on its own new stacked-base detector step:

```
DRIFT PR #508 (lane 4 open_prs) targets base branch 'feat/engineering-acceptance-authority',
not 'main'; it is STACKED, so merging it would land its base branch's commits unreviewed
```

That is a real and separate finding about the `#502 → #508` stack, and it is **not** this
slice. This PR is deliberately the smallest change that clears `main`'s latent red:
snapshot refresh only, no guard-logic change, no lane-doc re-point, no stacked-base policy.
`#568`'s enforced-set derivation and stacked-PR detector stay open for sovereign review as
their own bounded workstream — this PR neither duplicates nor pre-empts them.

## 6. Remaining uncertainty / not claimed

- **Not claimed:** that this restores `main` to green *in CI*. The gate is path-filtered; the
  proof here is local execution of the same oracle plus the exit-code negative control.
- **Not claimed:** any disposition of the `#502 → #508` stack, the `#567`/`#568` stack, or the
  four lane docs' declared pointers. `AGENT-01-SHELL.md` still declares closed `#507` on its
  `**Active PR:**` line while also declaring open `#562`; the guard passes today because it
  resolves the doc's pointer to `#562`, but that dual declaration is a **recorded observation
  for the lane-1 owner**, not repaired here.
- The refresh is a point-in-time measurement (`observed_at 2026-10-25T13:26:10Z`); it goes
  stale as lane PRs move, which is why the refresh helper exists.

## 7. Note-count reconciliation (inherited discrepancy)

An inherited note asserted **3** NOTEs where the shipped docs and CI report **2**. Measured
here: **2** NOTEs (lane 3 → closed `#450`, lane 4 → merged `#428`). The "3" figure does not
reproduce at `36f53be2`; the 2-NOTE observation supersedes it. No third NOTE appears in the
pre-repair or post-repair output.

## Authority

No merge, no deployment, no acceptance. Draft PR; human merge authority retained.
