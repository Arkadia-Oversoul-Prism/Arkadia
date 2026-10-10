# gate-hygiene · gate2-deployment-window-01

**Boundary:** the Gate-2 production-observation harness (`scripts/gate2_production_observation.py`)
reported `main -> deployment identity := UNKNOWN` while `main` **was** deployed and
byte-identical in `sha`. The classification was wrong in the dangerous direction: it read as
*no deployment evidence* rather than *deployed*.

**Scope:** one harness fetch path + its fitness tests. No runtime, API, schema, or authority
surface. `api/main.py` untouched.

## 1. Defect

`/deployments` is ordered by creation time across **every** environment and is paginated. The
pre-repair harness read a single fixed window and filtered it client-side:

```python
deps = api(f"/deployments?per_page={max(args.limit * 5, 50)}", token)   # 60 records
prod = production_deployments(deps, args.limit)
```

On the day of measurement the newest Production deploy sat at **index 71** of the unfiltered
list — past the 60-record window — because the Preview/branch cohort is the dominant producer.

## 2. Measured before / after

Same repository, same `main` @ `24a00f856a0286cbb464a4b585117dd57a2646fa`, same token:

| Harness | `main -> deployment identity` | Production records seen | Newest Production SHA |
|---|---|---|---|
| pre-repair (`origin/main`) | **UNKNOWN** | 0 | — |
| repaired (this branch) | **VERIFIED** | 4 | `24a00f85…` (== `main`) |

Independent slice confirmation of the window size:

```
first  60 unfiltered records -> 0 Production
first 100 unfiltered records -> 4 Production
```

Seven newest Production records on record, newest-first, all `sha == main` or descendants:

```
6939001431  24a00f856a02…  2026-10-08T15:00:08Z   Production – console     (index 71 unfiltered)
5732732375  24a00f856a02…  2026-10-08T14:59:59Z
…
```

So the newest Production deploy names `main` exactly and the pre-repair `UNKNOWN` was a
**harness artifact**, not a deployment gap.

## 3. Repair

- `DEPLOYMENT_SCAN_PAGES = 5` — newest-first page walk, bounded (≤ 500 records, never the full
  history).
- `fetch_deployments(token)` — pages `/deployments?per_page=100&page={n}` until a Production
  record appears, the page cap is reached, or the server runs out of pages; returns
  `(records, error_or_None)`.
- `production_deployments_within(payload, limit, scan_ceiling)` — the label+sha filter, plus a
  window guard: a window shorter than the ceiling that carries **no** Production record returns
  `[]` (unprovable absence → `UNKNOWN`), never a `STALE` claim drawn from a truncated view.
- `production_deployments(payload, limit)` is retained as a thin wrapper (`scan_ceiling =
  limit`) so the existing single-source-of-truth call sites and their tests still hold.
- `main()` wires the paged fetch and the guarded predicate; a fetch error still classifies
  `BLOCKED` with the reason recorded.

## 4. Proof

```
python -m pytest tests/test_gate2_production_observation.py -q
  -> 24 passed      (19 before; +5 new)
python -m pytest tests/test_gate2_{production,backend,browser}_observation.py -q
  -> 56 passed
python -m pytest tests/architecture -q
  -> 11 passed
python -m py_compile scripts/gate2_production_observation.py -> OK
```

New tests:

- `test_window_over_fetched_records_yields_production_records` — positive shape.
- `test_window_exhausted_without_production_yields_nothing` — absence stays unprovable, not
  `STALE`.
- `test_negative_control_truncated_window_hides_a_production_record` — **negative control**:
  feeds the pre-repair shape a window whose Production record sits one past it and asserts the
  unguarded predicate yields nothing; the same payload with the guard yields a record. The
  guard is therefore not vacuous.
- `test_fetch_pages_until_a_production_record_appears` / `test_fetch_scan_stays_bounded` —
  paging present, scan capped.
- `test_deployments_are_fetched_unfiltered` (pre-existing) still pins the unfiltered fetch.

## 5. Live boundary after repair

```
current main resolved            VERIFIED
main -> deployment identity      VERIFIED
deployment build output observed BLOCKED   (Vercel Deployment Protection / SSO)
alias reachable                  VERIFIED
alias -> deployment SHA binding  UNKNOWN (immaterial: all candidates share frontend source)
build <-> source lineage         VERIFIED (marker set matches, source closed)
browser-rendered UI correctness  UNKNOWN
production acceptance            NOT CLAIMED (human authority)
```

The standing Gate-2 open boundary — **deployment build output observed** — remains `BLOCKED` on
provider auth. This repair does **not** close it and does not claim production parity; it
removes a harness artifact that was masquerading as deployment absence and inflating the
`UNKNOWN` count.

## 6. Regression boundary

Failing/error node **set** compared against a freshly measured `main` `24a00f85` baseline in a
detached worktree (`tests/` with `--continue-on-collection-errors`, after `git merge-base`):

```
main   24a00f85 : 79 failed, 1180 passed, 21 skipped, 54 errors   133 failing/error nodes
branch         : 79 failed, 1185 passed, 21 skipped, 54 errors   133 failing/error nodes
comm -3 /tmp/main_nodes.txt /tmp/branch_nodes.txt                 (empty)
```

Counts are environment-dependent — absolute totals here (79F/54E) are a local dependency delta,
not the gate baseline — so only node identity is load-bearing: **zero node-set delta**. The
`+5 passed` is exactly the five new tests. Do not read the absolute failure count as a
regression.

## 7. CI

On head `8d774a9f` all six check-runs pass (`Full-history secret scan`,
`native-arkadia-golden-workflow`, `bundle-beta-evidence`, both `beta-*`, Vercel Preview
Comments). `mergeable: MERGEABLE`.

The only non-success is the `Vercel – arkadia-prism` **commit status**
(`Vercel – console` is success). That status is a pre-existing chronic condition on `main`,
not attributable to this change: it reads `failure` on 7 of the 8 most recent `main`
commits (`06c4d8a1`, `44137991`, `4edab519`, `f96d5fd2`, `2c6f6f1e`, `a27c6c80`, `427a9287`)
and `success` on the tip `24a00f85` alone. The head here is `docs`/`scripts`/`tests` only and
cannot plausibly cause a Vercel build failure. Classified as pre-existing; do not read it as a
regression of this PR.

`sg-02-fe-2-v.yml` (CP10 mutation boundary) is **path-filtered** to
`web/public_prism/**`, `spiral_grove/**`, `lab/**`, `api/lab_routes.py` and named test files;
this PR touches none of them, so its absence from the check list is expected, not a gap. The
boundary itself was still executed locally and passed (see §4 and the commit body).

## 8. Composition with PR #366 (same file)

This PR and **#366** (`gate-hygiene/gate2-marker-oracle-soundness-01`) both edit
`scripts/gate2_production_observation.py` and `tests/test_gate2_production_observation.py`.
Measured: `git apply --3way` of #366's patch onto this head in a detached worktree yields `UU`
on **both** files (1 conflicted region in the script, 2 in the test).

They are **independently necessary**, not duplicates:

- **#368 (this PR)** — *deployment-window* correctness. `/deployments` is ordered by creation
  time across **every** environment; a busy Preview cohort pushes the newest Production record
  off a single page, so the link read `UNKNOWN` while main **was** deployed. The repair is real
  **pagination** (`per_page=100&page=N`).
- **#366** — *marker-oracle* soundness. It does **not** paginate; it widens the fixed window
  (`per_page = max(args.limit*5, 50)`), which is strictly weaker. It repairs a different defect:
  the harness scored the **console** artifact against **Prism** literals after the root
  `vercel.json` was repointed at `404452e0`.

The conflict is the adjacent constant block at `BUILD_INPUTS`: this PR adds
`DEPLOYMENT_SCAN_PAGES`; #366 adds `KNOWN_FRONTENDS`/`MARKER_APP`.

**Recommended merge order (sovereign's call):** #366 first, then rebase this PR onto it and
keep both the page loop and `KNOWN_FRONTENDS`/`MARKER_APP`. Do **not** merge both unreconciled,
and do not open a third PR on this file.

`build <-> source lineage` remains `VERIFIED` by **ancestry closure** regardless of the marker
table; the ABSENT marker rows in a live run are the Console artifact (the harness falls back to
`alias_bundle`, `assets/index-*.js`, because the Prism build emits `dist/assets/index-*.js`),
not a Prism divergence.

## 9. Authority boundary

Harness + test source only. No merge. Branch
`gate-hygiene/gate2-deployment-window-01` → PR against `main`. Human merges.

## 10. Composition pass — #366 reconciled into this branch (bounded execute)

Per the recommendation in §8, the marker-oracle repair (#366) is now **composed into this
branch**, not left as a competing PR on the same two files.

Composition sequence (merge only; **no force-push, no rebase of published history**):

1. Branch was based on stale `24a00f85`. Merged **current `main`** (`43c3e2b1`) in —
   conflict only in `AGENTS.md` (a tail-append collision); resolved by keeping **both**
   sections (this workstream's lesson + main's baseline-fingerprint lesson).
2. Merged `origin/gate-hygiene/gate2-marker-oracle-soundness-01` (#366) in — `UU` on **both**
   instrument files, exactly as §8 predicted. Resolved by keeping **both** additive edits:
   - `scripts/gate2_production_observation.py`: the `DEPLOYMENT_SCAN_PAGES` page loop **and**
     `KNOWN_FRONTENDS`/`MARKER_APP`/`classify_marker_oracle`/`frontend_of`.
   - `tests/test_gate2_production_observation.py`: both import sets and both test blocks.
3. `main` did **not** touch either instrument file between `24a00f85` and `43c3e2b1`
   (`git diff --stat 24a00f85 43c3e2b1 -- <files>` empty), so the resolution is not stale.

Delta of the composition against the pre-merge branch tip is **#366's own repair only**
(docstring widening, `KNOWN_FRONTENDS`/`MARKER_APP`, `frontend_of`, `last_build_input_commit(app)`,
`classify_marker_oracle`, and the honest `classification_source_lineage` wording).

### Measured verification (this environment)

| Check | Command | Result |
|---|---|---|
| instrument unit tests | `pytest tests/test_gate2_production_observation.py -q -rEf` | **39 passed** |
| architecture fitness | `pytest tests/architecture -q -rEf` | **11 passed** |
| script compiles | `python -m py_compile scripts/gate2_production_observation.py` | OK |
| end-to-end harness | `python scripts/gate2_production_observation.py` | runs; reports `marker-set oracle NOT OBSERVED (artifact is 'console')` — the soundness repair is live, no false `VERIFIED` |

Full suite, **failure/error node-set** comparison (not counts) on the same command
(`pytest tests/ -q -rEf --continue-on-collection-errors`):

- branch: 78 failed / 1232 passed / 21 skipped / 57 errors
- `main` `43c3e2b1` (detached worktree): 78 failed / 1212 passed / 21 skipped / 57 errors
- failing/error node set sha256 **identical** on both:
  `d13fafb499059b3ddbf56982da2e17eda354f579b01f07d2263c2b03392f002f` (135 nodes, 0-only-on-either side)
- **+20 passed** == exactly the composed gate2 test additions. **Zero regression.**

The large baseline failure/error totals are pre-existing environmental debt
(`ModuleNotFoundError` for `weaver.*` suites, missing optional deps) present identically on
`main`; they are recorded, not repaired (AGENTS.md "baseline debt" rule).

### Disposition

- This branch (PR #368) now carries **both** instrument repairs.
- **PR #366** is superseded by this composition; it should be **closed** by the sovereign
  once #368 merges (its content is byte-present on this head). No third PR was opened.
- Merge remains the sovereign's exclusive action. No merge, no self-authorization.

