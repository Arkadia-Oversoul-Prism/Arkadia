# ARK-OPS-CONTINUOUS-001 — cycle 22: production serves the exact bytes this tree builds

**Contract:** `ARK-OPS-CONTINUOUS-001` rev `2026-11-22`
**Base:** `main` @ `fd0a4fdc081064b2074aab9e17b4c7841736dd9f` (2026-11-24T17:30:03Z)
**Measured:** 2026-11-25, this workspace, 13:06-13:45 UTC
**Authority:** read-only against GitHub and production, plus one local build. No merge, no push to
`main`, no deployment, no acceptance. **No new pull request was opened** — every defect found this
cycle is already owned by an open PR (section 3), and section 0.1 forbids adding one to appear
productive.

---

## 1. Reconstructed state — `main` has not moved

| fact | measured value | how |
|---|---|---|
| canonical `main` | `fd0a4fdc081064b2074aab9e17b4c7841736dd9f` | `git rev-parse origin/main` |
| last merge | `#722` — GOV-04 bounded merge delegation | `git log` |
| open PRs | **57** — **56** drafts, **1** non-draft (`#724`) | `GET /pulls?state=open` |
| merged since `#722` | **0** (about 20 h) | commit list |
| `api/main.py` | **2597** lines (budget 2600) | `contents?ref=main` |

The queue is unchanged from cycle 21: `main` is the same SHA, so that cycle's handoff is
**current**, not stale.

`api/main.py` budget pressure was re-measured because four open PRs touch it. All four are inside
the budget **on their own blob**: `#701` 2593, `#711` 2597, `#717` 2592, `#729` 2598. No
composition breach is implied by the per-blob measurements, and the worst case (main 2597 with
`#729`'s +1) leaves one line.

## 2. Production parity — artifact byte identity, not revision metadata

Cycle 21 established the *revision* boundary with `GET /api/version`. That is necessary evidence
and it re-verifies here, but it is metadata the process reports about itself. This cycle measures
the **artifact**.

```
GET /api/version                 -> 200
  source_revision   fd0a4fdc081064b2074aab9e17b4c7841736dd9f
  revision_source   RENDER_GIT_COMMIT
  revision_conflict false

GET /  (Accept: text/html,...)   -> 200, 1256 B   (SPA shell)
  manifest: assets/index-BJojPKi_.css, assets/index-CYGHeCpJ.js
```

A clean build of **this tree** (`web/arkadia_console`, `corepack pnpm install --frozen-lockfile`
then `tsc --noEmit && vite build`, exit 0, 170 modules) emits **the same two asset names**, and
their bytes are identical to what the origin serves:

| asset | served | local build | sha256 |
|---|---|---|---|
| `index-CYGHeCpJ.js` | 426,232 B | 426,232 B | `63a28f23bbb433f995632eecb3fc0995cceebb205bf0531de89cf572aba5a4e5` |
| `index-BJojPKi_.css` | 91,922 B | 91,922 B | `4948b2fa145b04cc10591e61f8a486e097523fab9dd28015081f9f54053f1e37` |

Asset names are content-addressed here and the hashes agree, so the served bundle is the build of
this revision rather than a build that merely shares a revision label. This is a **stronger** claim
than cycle 21 recorded, and it is a different claim from application correctness.

A cold start was observed and is not a defect: the first `/api/version` probe timed out at 25 s; the
same URL answered `200` in 10.2 s on retry. Recorded so the timeout is not re-read as an outage.

### 2.1 Marker-set oracle against the live bundle — VERIFIED

Scoring the **console** marker list (`MARKER_APPS["arkadia-console"]`) against the served JS:

| literal | polarity | served | source |
|---|---|---|---|
| `Protected surface` | present | 1 | present |
| `Sign in to continue` | present | 1 | present |
| `Go to sign in` | present | 1 | present |
| `Reading canonical contract` | present | 1 | present |
| `Human authority remains the decision boundary` | present | 3 | present |
| `Arkadia is temporarily unreachable` | present | 2 | present |
| `Enter the enterprise layer.` | **control, must be absent** | **0** | absent |

Every positive literal is present and the control is correctly absent, so the oracle reads
`VERIFIED (marker set observed in served artifact)`. Both polarities were honoured: a
polarity-blind scorer would have failed the control.

## 3. The Gate-2 harness cannot see this — and the repair is already written

Run against the same live origin, `scripts/gate2_production_observation.py` on `main` reports:

```
artifact app: UNDETERMINED   scoring against: no declared marker list
no artifact fetched -> no marker set read (NOT OBSERVED)
!! STALE marker list -- literals gone from source: [7 Prism literals]
SG-04 REGRESSION  in source: False   NOT EVALUABLE
main -> deployment identity            UNKNOWN
deployment build output observed       UNKNOWN
build <-> source lineage               UNKNOWN
```

The cause is structural and is **not** a marker regression. App identity is read from the project
suffix on a GitHub **deployment record**, and the canonical runtime is Render, which publishes no
such record — so `prod == []`, `deployed_app is None`, and every downstream classifier takes its
undetermined branch. The `STALE marker list` line is therefore expected: it is the **Prism** list
being compared with the **console** source. Reading it as a Prism divergence would be a category
error.

**This defect is owned, and the owner is further along than a proposal.** `#681`
(`gate2/served-artifact-app-identity-01`, head `842555285b69688f2f063115b30fb1d622f21e30`) states
the same diagnosis and adds `detect_served_app` (identity from the served shell's declared
`<title>`, failing closed on zero or ambiguous matches), and it also implements the boundary this
cycle would otherwise have proposed — `classify_runtime_revision` over `GET /api/version`
(`scripts/gate2_production_observation.py:328-381` in that tree). Both gaps are therefore **not**
duplicated here.

Independently corroborated at its head and against live production:

- `detect_served_app` is **absent** from `main` (`hasattr(...) -> False`), so `#681` is genuinely
  unmerged and its repair is not already in the tree;
- the marker set it promises to score is the one that scores `VERIFIED` against the served bundle
  in section 2.1, measured here, not quoted from its evidence;
- `#681`'s own `gate2-observation` check is `success` at its head.

## 4. Composition finding — `#681` and `#687` do not compose as they stand

Both are green-enough and both edit the same harness. Measured by merging `#687`'s head
(`be751f9d`) into `#681`'s head in a detached worktree:

```
Auto-merging scripts/gate2_production_observation.py      (clean)
CONFLICT (content): Merge conflict in tests/test_gate2_production_observation.py
```

Two conflicted regions, both **union-resolvable**:

1. the import block — `RUNTIME_REVISION_BOUNDARY` (`#681`) vs `classify_alias` (`#687`) on the
   same line: keep both;
2. both PRs **append a new test section at end-of-file**, so the tails collide: keep both sections.

Neither PR is wrong alone, and merge order is semantically free. This is the recorded
"append-append / adjacent-constant" composition class, not a design disagreement. The human merge
decision needs the resolution, not a choice between them.

## 5. Local baseline — every failing node is owned, reserved, or environmental

Full suite at `main` `fd0a4fdc`:
`22 failed, 4251 passed, 22 skipped, 1 error in 292.17s` — **23** failing/error nodes.

| failing file | nodes | owner |
|---|---|---|
| `test_mission_lifecycle_adapter_contract.py` | 10 | **none** — environment: `web/arkadia_console/node_modules/typescript` absent; the test transpiles the real adapter with the repo's own compiler |
| `test_autonomy.py` (ERROR) | 1 | **none** — CE-01 `weaver.autonomy` module-vs-package collision, sovereign-reserved |
| `test_ais_w2_living_gate_grove_handoff.py` | 1 | **none** — F-01 proxy invalidation awaiting a sovereign decision; deliberately left failing |
| `test_identity_spine_w1.py`, `test_m02_reasomate_truth.py` | 2 | `#700` |
| `test_m01_persistence.py`, `test_m05_files.py` | 2 | `#690` |
| `test_prism_w4_lab_pr_state.py` | 2 | `#683` |
| `test_solspire_r1_governance_convergence.py` | 2 | `#693` |
| `test_solspire_r3_execution_runtime.py` | 1 | `#691` |
| `test_static_ingestion_idempotency.py` | 1 | `#698` |
| `test_gov04_bounded_merge_delegation.py` | 1 | `#725` |

Ownership was derived by intersecting the failing file list with the changed-file inventory of all
57 open PRs, not by title. The three unowned files are two governance reservations and one
missing-dependency environment gap; **none is an ordinary defect an agent may repair**, and none
was touched.

## 6. What this cycle does and does not establish

**Established:** `main` is unchanged and production serves the byte-identical build of it; the
console marker oracle is `VERIFIED` against the live artifact with its control correctly absent;
the Gate-2 harness's `UNDETERMINED` reading is a known, owned identity defect rather than a marker
regression; `#681` and `#687` conflict and the conflict is union-resolvable; the 23 local failing
nodes are owned, reserved, or environmental.

**Not established:** merge eligibility, M1-M13, review sufficiency, browser-rendered correctness,
or acceptance. A byte-identical artifact is not proof that the application behaves correctly, and
no browser was driven this cycle.

## 7. Next action

1. **Human:** the three textual conflicts and two semantic composition defects handed off by cycle
   20 remain open; add this cycle's `#681`/`#687` pair to that list. Resolution is union of both
   imports and both appended test sections; order is free.
2. **Human:** decide the two cycle-21 proposals (external-beta gate scoping; provider
   unavailability reported as `BLOCKED`).
3. **Human:** merge order for the `#716` / `#719` dependency.
4. **Weaver:** the standing blocker remains **human merge authority**. This cycle found no unowned
   engineering defect: the two gaps it discovered (served-app identity, runtime revision identity)
   are both already implemented in `#681`, and the remaining failing nodes are governed
   reservations or a local dependency gap. Further engineering does not advance the queue.

## 8. Reproduce

```
git rev-parse origin/main                                  # fd0a4fdc...
curl -s https://arkadia-qzu4.onrender.com/api/version
cd web/arkadia_console && corepack pnpm install --frozen-lockfile && corepack pnpm build
curl -s -o /tmp/served.js https://arkadia-qzu4.onrender.com/assets/index-CYGHeCpJ.js
sha256sum /tmp/served.js dist/assets/index-CYGHeCpJ.js     # equal
python scripts/gate2_production_observation.py             # UNDETERMINED on main
PYTHONPATH=$PWD/archive/legacy_python python -m pytest tests/ -q -rEf \
  --continue-on-collection-errors
```

## 9. Operational note — the working credential moved

`GITHUB_PERSONAL_ACCESS_TOKEN` answered `401 Bad credentials` throughout this cycle while
`GITHUB_TOKEN` answered `200`. The previously recorded guidance ("the PAT secret is the working
fallback") is **reversed at this measurement**: use `GITHUB_TOKEN` and re-probe both before
classifying any GitHub read as `BLOCKED`.

## 10. Verification of this change

```
printf 'docs/control-plane/evidence/ark-ops-continuous-001-cycle-22/EVIDENCE.md\n' \
  | python scripts/cp10_mutation_boundary_policy.py --judge
python -m pytest tests/test_m02a_ci_gate_integrity.py -q
```

Recorded in the commit message after execution.
