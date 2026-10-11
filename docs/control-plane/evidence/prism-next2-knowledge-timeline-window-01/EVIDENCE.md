# Workstream 3 follow-up — timeline window must contain the latest event · evidence

**Issue:** [#437](https://github.com/Arkadia-Oversoul-Prism/Arkadia/issues/437) — post-merge review of PR #431.
**Branch:** `feat/prism-next2-03-knowledge-timeline-latest`
**Durable task:** `docs/control-plane/parallel-ui/AGENT-03-SOLARIUN-KNOWLEDGE.md`
**Shared contract:** `docs/control-plane/parallel-ui/SHARED-CONTRACTS.md`
**Base / starting `main`:** `17988afdde8460cfcaf778258bc43aed1fc9d21f`
**Authority:** implement, test, commit, report. **No merge, deployment, or acceptance.**

---

## 1. The defect, restated from the measurement

PR #431's panel renders `events[events.length - 1]` as `latest`. The handler it reads
returned `ORDER BY id ASC LIMIT ? OFFSET ?` with `limit` defaulting to `100`, so the
default response was the **oldest** 100 rows and the final row was the newest of *that
page*. Past 100 events the real latest event was not in the response at all.

Measured on the starting `main` (`17988afd`), 130 owner-scoped events, default read:

```
default (pre-repair) -> 100 rows, first id 1, last id 100   newest event id 130
```

So `latest` reported event 100 while the log's newest event was 130 — a false fact about
the log, and the newest 30 events were unreachable without `offset`, which the panel does
not expose.

### Which contract was chosen, and why

Issue #437 offered two options. The **newest-page** contract was chosen because the panel's
job is "what happened most recently" and it has no pagination control; option 2 (adding
pagination UI) would have kept the mislabel while adding a second interaction surface. The
newest-window contract also keeps the response **chronological**, so it is not a breaking
reorder: a caller that renders rows top-to-bottom still sees oldest→newest.

---

## 2. The repair

| File | Change |
|---|---|
| `knowledge/timeline.py` | `query(..., newest_first: bool = False)` — the bounded read selects `id DESC` when set, then reverses, so the window is the newest `limit` rows returned ascending. `offset` pages backwards from the newest event. |
| `api/knowledge_routes.py` | `GET /api/knowledge/timeline` gains `newest_first: bool = True`. The HTTP default is the newest window; the omitted parameter no longer means "oldest page". |
| `pages/knowledge/knowledgeContracts.ts` | `TIMELINE_WINDOW_LIMIT`, `TimelineWindow`, `isWindowSaturated`, `timelineWindowNotice`; handler docblock corrected. |
| `components/knowledge/KnowledgeTimelinePanel.tsx` | requests `limit=${TIMELINE_WINDOW_LIMIT}`; renames the `first` fact to `oldest shown`; renders the saturated/complete window notice. |

**`query()`'s default stays `newest_first=False` deliberately.** `replay_project` calls
`query(limit=10000)` to walk the whole log from its beginning, and the pre-existing
`tests/test_isolation.py` and `tests/test_knowledge_search_boundary.py` bind `query()`
directly. Making newest-first the *layer* default would silently reorient a whole-log replay
while the only caller that needed it was one HTTP route. The window selection is therefore
opt-in at the layer and default-on at the route.

### Measured behaviour after the repair (130 events, live ASGI, no mocks)

```
default              -> 100 rows, first id 31,  last id 130  | newest event id 130
offset=100           ->  30 rows, ids 1..30                  (strictly older than the window)
newest_first=false   -> 100 rows, first id 1,   last id 100  (the explicit opt-out)
anonymous            -> []
limit=501            -> 422
```

The default window now **ends at the log's newest event**, which is the property the
panel's `latest` fact depends on.

### A second false claim in the same facts table

The `first` row read `events[0].created_at`. Under the oldest-page behaviour that happened
to be the log's first event; under a windowed read it is only the oldest event *still
shown*. Left unqualified it would have become the same class of false claim as `latest`.
It is now labelled `oldest shown`.

---

## 3. Tests — `tests/test_knowledge_timeline_window.py`, 19 tests

Live handler over ASGI against a sandboxed database. No mocks.

| Group | Tests |
|---|---|
| The defect | window includes the newest event past the default limit; window **is** the newest page (not merely contains one); response stays chronological; `offset` pages backwards; explicit oldest-first window; `query()` default unchanged for whole-log replay |
| Owner boundary preserved | owner-scoped window past the limit (a second owner's 130 events do not displace it); anonymous `1 = 0` fail-closed with a full log; unknown uid reads nothing; `event_type` filter windows the *filtered* set and stays scoped; `limit=501` → `422` |
| Window honesty | panel derives its request limit from the declared constant; panel states the boundary; saturated and complete copy are different strings |
| Source detectors | bounded-read selector present; handler declares and forwards the default; declared default equals the served default |

### Negative controls — each proven to bite, then reverted byte-identically

| Control | Mutation | Result |
|---|---|---|
| window selection | `knowledge/timeline.py` back to hard-wired `ORDER BY id ASC` + route default `newest_first=False` | **7 failed**, including the primary regression control (`body[-1]["id"] == 130` became `100`) |
| window limit | panel back to `limit=100` literal and `first` label | **2 failed** |
| detector | fed the exact pre-repair clause shapes (hard-wired `ASC`, a `DESC`-only read) and the pre-repair `first` label | reports each; stays silent on the repaired source |

---

## 4. Verification

| Check | Result |
|---|---|
| New suite | **19 passed** |
| New + prior timeline boundary suites | **38 passed** |
| Adjacent knowledge/console suites (9 files) | **127 passed** |
| Full suite, branch | 20 F / 2585 P / 19 S / 1 E |
| Full suite, baseline (changes stashed) | 20 F / 2566 P / 19 S / 1 E |
| Failing/error node set | **identical** — `comm -3` empty, 21 nodes each side |
| Fingerprint (branch) | outcomes `c2b6e0998382af6f3b75011f5fd8de899d966e68624211990eb2e3e0a3a8c5c4`, ids `f76e42de7543de9cf665e1fa838706939bb41316679459bb133e2e27f60e85b4` |
| Architecture suite | **11 passed** |
| `corepack pnpm install --frozen-lockfile && corepack pnpm build` | **succeeded** (77 modules) |
| CP10 mutation-boundary judge | **PASS** (5 paths) |
| `python -m py_compile api/knowledge_routes.py knowledge/timeline.py` | ok |
| `api/main.py` | untouched, 2499 lines (budget 2600) |

The `+19 passed` is exactly the new file. Compared by node **identity**, never counts.
Both full runs used `-rEf`, not `-rf`.

### One real regression the first full run caught, and its repair

The first branch run added a failure the baseline did not have:
`tests/test_console_shell_nav_contract.py::test_design_tokens_are_bypassed_by_page_local_hex_literals`
(Workstream 1's shared shell test). Cause: its detector is
`re.compile(r"#[0-9A-Fa-f]{3,8}\b")`, which matches the **issue number** `#437` written in a
frontend docblock — `437` is valid hex. The reference was reworded to `issue 437` in both
frontend files; the suite then returned to the baseline node set exactly. No shared test was
edited. Recorded because a green-looking change can redden another workstream's guard for a
non-code reason.

---

## 5. Preserved invariants

- **Owner scope.** `_timeline_owner_clause` is untouched: authenticated `user_id = ?`,
  anonymous `1 = 0`. `test_anonymous_window_is_still_fail_closed_past_the_limit` proves a
  130-event log still yields `[]` anonymously, and
  `test_window_is_owner_scoped_past_the_limit` proves a second owner's 130 events do not
  displace the first owner's window.
- **No client-side authorization.** The panel still applies no ownership filter; the window
  change is a query parameter, not a second endpoint, and the path is still derived from
  `endpoints.knowledgeTimeline`.
- **Honest states.** The saturated/complete window notice is separate copy; a filtered `[]`
  and an empty log remain distinguished by viewer identity, as in PR #431.

## 6. Unknowns / not done

- No merge, deployment, or acceptance. The canonical runtime serves `main`, not this branch;
  the endpoint was not probed in production.
- No pagination *control* was added. The panel states that older events exist beyond the
  window rather than offering a way to reach them; a "load older" control would need a
  bounded page state and is a separate slice.
- `GET /api/knowledge/timeline/recent` and `/timeline/replay/{project_id}` were not changed.
  `recent` is already `id DESC` + reverse; `replay_project` keeps its oldest-first walk.
- The `first`→`oldest shown` rename is a **display** change in the panel's facts table. No
  test asserted the old label; the shell hex detector did, indirectly, via the issue number.

## 7. Next bounded task (non-overlapping)

`GET /api/knowledge/projects/{name_or_uuid}` is pinned at the boundary level (fail-closed
`404`) and still has no consumer. A detail panel needs a registry **path builder**, which is
Workstream 1's file — a request, not an edit. Alternatively, a bounded "load older events"
control for this timeline, built on the `newest_first=false` + `offset` contract that now
exists and is tested.
