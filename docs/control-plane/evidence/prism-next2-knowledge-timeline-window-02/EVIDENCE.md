# Workstream 3 follow-up — the timeline window is not the log · evidence

**Issue:** [#437](https://github.com/Arkadia-Oversoul-Prism/Arkadia/issues/437) — post-merge review of PR #431.
**Branch:** `feat/prism-next2-03-knowledge-timeline-latest-2`
**Starting / target `main`:** `7b67215735945584e89fec50f97fe74dddfcbf28`
**Authority:** implement, test, commit, report. **No merge, deployment, or acceptance.**

---

## 1. The environment moved during this pass — read this first

The task was to implement issue #437 on a fresh branch from current `main`. That
branch was created and PR #445 opened against `main` `17988afd`. **While this pass
ran, `main` advanced and issue #437 was fixed independently.**

| Observation | SHA / time |
|---|---|
| My starting `main` | `17988afdde8460cfcaf778258bc43aed1fc9d21f` (2026-10-11T15:20:46+01:00) |
| The independent fix, merged | PR **#442** "fix(knowledge): show the latest bounded timeline window", merge commit `56ada9dd1511c788ade4a461b152a6d9ab6f6029` (2026-10-11T16:16:54+01:00) |
| Issue #437 state | **closed** 2026-10-11T15:19:32Z |
| `main` at the time of re-measurement | `7b67215735945584e89fec50f97fe74dddfcbf28` |

My PR #445's core change (`knowledge/timeline.py` ordering + a `newest_first`
parameter) therefore **duplicated** a merged fix. A PR that re-lands an
already-merged change is not a repair. This pass was re-scoped: my branch was
discarded, a fresh branch was cut from current `main`, and the work below is
built **on top of** #442 rather than beside it.

This is recorded rather than quietly rebased because the earlier PR body and
issue comment cited my own measurement as the fix; a reader arriving later must
be able to see that `main` already carried one.

## 2. What #442 fixed, verified here rather than assumed

`knowledge/timeline.py::query()` now reads:

```sql
SELECT * FROM (SELECT * FROM timeline {where} ORDER BY id DESC LIMIT ? OFFSET ?)
  AS latest_page ORDER BY id ASC
```

Measured on `main` `7b672157`, 130 owner-scoped events:

```
default       -> 100 rows, first id 31,  last id 130  | newest event id 130
offset=100    ->  30 rows, ids 1..30                  (strictly older than the window)
anonymous     -> []
```

So the #437 defect — `latest` naming the newest row of the *oldest* page — is
**fixed on `main`**, and `query()`'s own default now serves the newest window
(`query(limit=3)` → `[128, 129, 130]`). `replay_project` still walks the log from
its beginning (it filters by project, so a windowed read is immaterial to it).

**Nothing under `knowledge/` was changed in this slice** — the measurement above
is main's behaviour, not mine.

## 3. The residual defect this slice addresses

#442 corrected the *order* and one label. Two false claims in the same reader
survived it:

1. **`first` is still labelled as the log's first event.** Main's facts table
   reads `{ label: "first", value: events[0].created_at }`. Under the newest
   window `events[0]` is the oldest event *still shown*; the log's actual first
   event is not in the response at all. This is the same class of false claim as
   the `latest` mislabel #437 removed — #442 moved the window without moving this
   label with it.
2. **The window's extent is never stated.** Main's static paragraph says older
   events "require an explicit offset query", but nothing derives from the
   *response* whether the window is saturated. A saturated page therefore reads
   as the complete log.

Both are reader-side; no handler change is needed or made.

## 4. The change

| File | Change |
|---|---|
| `pages/knowledge/knowledgeContracts.ts` | docblock corrected for the newest-window read; `TIMELINE_WINDOW_LIMIT`, `TimelineWindow`, `isWindowSaturated`, `timelineWindowNotice` added |
| `components/knowledge/KnowledgeTimelinePanel.tsx` | requests `limit=${TIMELINE_WINDOW_LIMIT}`; renames `first` → **`oldest shown`**; adds a `window` fact (`newest`/`complete`) and a window-extent notice |
| `.github/workflows/prism-console-contract.yml` | adds `tests/test_knowledge_timeline_window.py` to both `paths` filters and to the executing pytest step (see §4a) |
| `tests/test_knowledge_timeline_window.py` | **new** — 18 tests |

`events[events.length - 1]` remains `latest` and is now **pinned true** by a test,
so the #442 property is asserted rather than assumed to survive.

### 4a. The gate the new test joined, discovered by running CI rather than reasoning

The first push reddened `console-contract`. `tests/test_prism_console_ci_wiring.py`
derives its guard domain from `git ls-files` at test time: a test module belongs to
the console-contract domain when it *names* the console
(`web/arkadia_console`, `"arkadia_console"`, …). My new test reads
`web/arkadia_console/src/...` to assert the panel's labels, so it entered that
domain legitimately — and the guard requires the executing gate to select the
domain **in the same change**:

```
no workflow executes the whole console-contract domain
  -> 2 failed, 17 passed  (tests/test_prism_console_ci_wiring.py)
```

So the wiring was added to `.github/workflows/prism-console-contract.yml`.
This is the guard working correctly, not a false positive: without it my new test
would have been a guard that *no workflow executes*.

**Verified rather than asserted:** the domain now has 17 entries including mine,
`prism-console-contract.yml` is the complete gate, and the guard passes. A negative
control — removing only the step line while leaving the `paths` entries — reddens
both wiring tests (**2 failed**, then reverted byte-identically).

**A measurement defect this exposed, corrected.** My first full-suite parity run
below happened while the test file was still **untracked**, so `git ls-files`
excluded it from the derived domain and the guard passed *vacuously* — the same
19-node result, with no hint of the omission. The failure only appeared once the
file was committed. Both full-suite runs were therefore **re-measured with the
file tracked**; the parity claim in §6 is the re-measured one. The guard is
derived from tracked content precisely because that is the corpus CI judges, but
it means an untracked new guard is invisible to it until commit.

## 5. Tests — 18, live handler over ASGI, no mocks

| Group | Tests |
|---|---|
| #442's contract pinned | `latest` is the log's newest event past the window limit (**primary control**); the window **is** the newest page; it stays chronological; `offset` pages backwards and does not repeat rows; the window's first row is *not* the log's first event |
| Owner boundary intact | owner-scoped window past the limit (a second owner's 130 events do not displace it); anonymous `1 = 0` fail-closed with a full log; unknown uid reads nothing; `event_type` windows the filtered set and stays scoped; `limit=501` → `422` |
| Reader honesty | request limit derives from the declared constant; the extent is described; saturated and complete copy never share wording |
| Source detectors | the `first` mislabel detector; the extent detector **matches calls, not imports**; `latest` still read from the final row |

### Negative controls — each measured, then reverted byte-identically

| Control | Mutation | Result |
|---|---|---|
| query ordering | `knowledge/timeline.py` back to hard-wired `ORDER BY id ASC LIMIT ?` | **5 failed**, incl. the primary control (`latest` id 651 ≠ 681) |
| fail-closed clause | `1 = 0` → `1 = 1` in `knowledge/timeline.py` | **1 failed** — a real leak: 100 owner events returned to an anonymous caller |
| limit binding | panel back to a bare `limit=100` literal | **1 failed** |
| panel labels | `oldest shown` → `first`, extent fact and notice removed | **1 failed** |
| detector weakness | extent helper removed from the call site but left in the import | **caught** — the first detector passed it (`timelineWindowNotice` matched the import line); the detector now matches invocations, and the import-only shape is a permanent negative control |

The last row is the control that earned its keep: the initial `declares_window_extent`
was a substring check that an unused import satisfied. Rewritten to
`re.findall(r"\b(isWindowSaturated|timelineWindowNotice)\s*\(", source)`, it bites
on call-site removal and the import-only shape is asserted as a control.

## 6. Verification

| Check | Result |
|---|---|
| New suite | **18 passed** |
| New + adjacent knowledge/console suites (6 files) | **118 passed** |
| `tests/test_prism_console_ci_wiring.py` (the gate the new test joins) | **21 passed** |
| Full suite, branch (test file **tracked**) | 18 F / 2623 P / 17 S / 1 E |
| Full suite, baseline (changes stashed) | 18 F / 2605 P / 17 S / 1 E |
| Failing/error node set | **identical** — `diff` empty, 19 nodes each side, both `sha256 204d0a4e31b89185b9e06b5d4cb027b156976df8cb7aafe42546a8703806736b` |
| Architecture suite | **11 passed** |
| `corepack pnpm build` | **succeeded** |
| CP10 mutation-boundary judge | **PASS** |
| `python -m py_compile` | ok |
| `api/main.py` | untouched, 2499 lines (budget 2600) |

The `+18 passed` is exactly the new file. Compared by node **identity**, never
counts; both runs used `-rEf` (not `-rf`, which suppresses the `ERROR` summary).
The branch run was repeated once the test file was tracked (§4a); the node set is
unchanged from the untracked run, and the console-contract guard is green in the
tracked run.

## 7. Preserved invariants

- **Owner scope.** `_timeline_owner_clause` is untouched; the `1 = 0` control above
  demonstrates the guard still detects a leak.
- **No client-side authorization.** The panel applies no ownership filter; the
  limit is a query parameter on the same registry-derived path.
- **#442's `latest`.** Asserted by test, not merely left in place.
- **Whole-log replay.** `replay_project` semantics unchanged; no backend edit.

## 8. Unknowns / not done

- No merge, deployment, or acceptance. The canonical runtime serves `main`, not
  this branch; the endpoint was not probed in production.
- No "load older events" control. The panel states older events exist beyond the
  window; reaching them would need bounded page state and is a separate slice —
  the `offset` contract for it is now measured and tested.
- PR #445 (my earlier duplicate) should be **closed, not merged**; its core change
  is already on `main` as `56ada9dd`.

## 9. Next bounded task (non-overlapping)

A bounded "load older events" control on the `offset` contract measured here; or
`GET /api/knowledge/projects/{name_or_uuid}`, which is pinned fail-closed at the
boundary level and still has no consumer but needs a registry path builder
(Workstream 1's file) — a request, not an edit.
