# NovaNet echoes panel — states the public total and notices truncation (composed into PR #492)

Workstream 2 (NovaNet & Project Opportunity Radar), durable instruction
`docs/control-plane/parallel-ui/AGENT-02-NOVANET-OPPORTUNITY.md`, shared contract
`docs/control-plane/parallel-ui/SHARED-CONTRACTS.md`.

Bounded objective: the Crystal-Matrix echoes panel (`NovaNetPage.tsx`, section
`echoes`) rendered a bare `public.slice(0, 8)` of `EchoesFeed.public` with **no
stated total and no notice**. A reader could not tell the panel was showing a
subset — an incomplete render presented as if it were the whole stream. This is
the same truthfulness class the sibling transmissions panel already satisfies
(it renders all returned posts).

The change single-sources the render bound (`ECHO_DISPLAY_LIMIT`), states the
public total in the panel header, and renders a truncation notice (testid
`novanet-echoes-truncation`) when the total exceeds the bound.

Authority: human retains merge, production deployment, and acceptance. Nothing
here claims any of the three.

## Revision binding

- Work branch: `feat/prism-next7-02-pipeline-strip` (draft PR #492, base `main`).
- `origin/main` at the start of this pass: `7580bd8f0ca2925518d78775f9a323ff0df8bc66`.
- Branch head before this composition: `b6572df4`.
- Composed head after this composition: `75fcc947`.
- Source slice: PR #528 (`feat/prism-l2-echoes-completeness-01`, commit
  `e162371df67b52769ce291fe71407875386ea438`), cherry-picked with `-x`.
- PR #492 state (read-only, `GET /pulls/492`): `open`, `draft: true`,
  `merged: false`, head `b6572df4`, base `49809f45`.
- PR #528 state (read-only, `GET /pulls/528`): `open`, `draft: true`,
  `merged: false`, head `e162371d`, base `3ca8582a`.
- Environment: node `v24.21.0`, pnpm `10.26.1`, pytest `9.1.1`.

## 1. Why this is a composition, not a duplicate

`NovaNetPage.tsx` is owned by workstream 2 (this lane). Measured with
`git rev-parse <rev>:web/arkadia_console/src/pages/NovaNetPage.tsx`:

| Revision | blob |
|---|---|
| `main` / `49809f45` / `3ca8582a` | `ef3ccf6929` |
| PR #492 head `b6572df4` | `2f7b75ab5d` |
| PR #528 head `e162371d` | `34f61d4451` |

Both PRs branch from the **same base blob** (`ef3ccf69`): PR #492 from
`49809f45` and PR #528 from `3ca8582a`. They are siblings, not a stack — the
echoes-completeness slice and the author-controls / engagement / composer slices
are two independent reconciliations of the same file from one ancestor. Merged
unreconciled, whichever landed second would conflict textually.

`main`'s eight commits since `49809f45` touch no NovaNet file
(`git log 49809f45..main -- web/arkadia_console/src/pages/NovaNetPage.tsx` is
empty), so `main`'s blob is unchanged and the conflict is purely the two lane
branches.

The composition was performed on the PR #492 branch (the older, larger lane
branch) so the lane keeps **one** NovaNetPage thread rather than two competing
edits to the same file. `git cherry-pick -x e162371d` auto-merged both hunk sets
(the #492 hunks are at lines 7/17/54/70/87; #528's at 32/97/113 — no overlap).
The composed file retains **both** the #492 author/engagement/composer slices and
the #528 completeness slice.

## 2. Proof — the composed file carries both slices

`grep -n` of the composed `NovaNetPage.tsx` (head `75fcc947`):

- `ECHO_DISPLAY_LIMIT = 8` (line 50) — the single-sourced bound.
- `echoes.data.public.slice(0, ECHO_DISPLAY_LIMIT)` (line 164) — no bare `8`.
- `data-testid="novanet-echoes-truncation"` (line 174) — the notice.
- `import { AuthorControls }` (25), `EngagementBar` (26),
  `TransmissionComposer` (27) — the #492 slices survive.

The guard `tests/test_prism_novanet_echoes_completeness.py` (3 nodes) is the
source-level detector, and it carries a **negative control**
(`test_negative_control_detector_flags_the_pre_change_form`) that reconstructs the
pre-change silent-cap render and asserts the detector flags it — the guard cannot
be disarmed by rewriting the source without reddening that control.

## 3. Gate wiring — the new guard is auto-admitted

The console-contract gate (`.github/workflows/prism-console-contract.yml`)
derives its executed inventory from `scripts/console_contract_domain.py`
(`derive_domain`), which scans every tracked `tests/test_*.py` for the console
needles. `tests/test_prism_novanet_echoes_completeness.py` names
`web/arkadia_console/src/pages/NovaNetPage.tsx`, so it is admitted without editing
the workflow. Measured:

```
$ python scripts/console_contract_domain.py | grep echoes_completeness
tests/test_prism_novanet_echoes_completeness.py
```

This is the class the AGENTS.md lesson records (a hand-maintained gate list drifts
when a new guard arrives); the derivation removes it here. No workflow edit is
required and none was made.

## 4. Verification (measured at composed head `75fcc947`)

| Check | Command | Result |
|---|---|---|
| Derived console-contract domain | `python -m pytest -q $(python scripts/console_contract_domain.py)` | **473 passed** |
| New guard | `python -m pytest tests/test_prism_novanet_echoes_completeness.py -q -rEf` | **3 passed** |
| Lane-2 guards | author_controls + engagement_readings + transmission_composer + opportunity_entry_flow | **117 passed** |
| Architecture fitness | `python -m pytest tests/architecture -q` | **11 passed** |
| Console build | `corepack pnpm install && corepack pnpm build` | **built in 1.59s**; `novanet-echoes-truncation` present in `dist/assets/index-*.js` |

The build output `web/arkadia_console/dist/` is untracked (`git ls-files
web/arkadia_console/dist` → 0 paths), so the local build leaves a clean tree.

## 5. Regression boundary — full-suite node set

One full-suite pass at head `75fcc947`
(`python -m pytest tests/ -q -rEf --continue-on-collection-errors`):

```
8 failed, 3035 passed, 17 skipped, 1 error in 212.01s
```

Sorted FAILED/ERROR node set (9 nodes), sha256
`c280ddc616fe4f4e9110bf4e6b6e538783a83d3764148d8a6d7ac45f6e8bc46b`:

```
ERROR  tests/test_autonomy.py
FAILED tests/test_ais_w2_living_gate_grove_handoff.py::test_no_firebase_persistence_in_gate
FAILED tests/test_engineering_lab_api.py::test_lab_mutation_endpoints_are_exactly_the_lab_state_set
FAILED tests/test_engineering_lab_api.py::test_lab_router_is_read_only_and_authenticated
FAILED tests/test_identity_spine_w1.py::test_node_entry_is_ais_signup_not_a_separate_diagnostic_route
FAILED tests/test_m02_reasomate_truth.py::test_oracle_runtime_uses_the_shared_session_key
FAILED tests/test_solspire_r1_governance_convergence.py::test_r1_solspire_builders_delegate_to_weaver
FAILED tests/test_solspire_r1_governance_convergence.py::test_r1_weaver_governance_is_canonical
FAILED tests/test_solspire_r3_execution_runtime.py::test_runtime_is_explicitly_non_governed_and_blocks_mutation_tools
```

This set is **byte-identical** to the set recorded on this branch at `d4b9c1fe`
(same 9 nodes, same `c280ddc6…` sha256; see
`docs/control-plane/evidence/prism-novanet-transmission-composer-01/EVIDENCE.md`
§5). Zero node-set delta — the composition introduces no regression. The eight
pre-existing failures and the CE-01 `tests/test_autonomy.py` collection error are
**recorded, not repaired** (baseline debt is not attributed to this change).

## 6. Scope

Files changed by this composition (one commit, `75fcc947`):

- `web/arkadia_console/src/pages/NovaNetPage.tsx` — +43/−11 (the #528 slice).
- `tests/test_prism_novanet_echoes_completeness.py` — new, 60 lines (the #528 guard).

No shared file (`App.tsx`, `router.ts`, `surfaces.ts`, `endpoints.ts`,
`types.ts`, `SurfaceLenses.tsx`) is touched. No route, endpoint, type, or
authority is added. No other lane's owned surface is edited.

## 7. Remaining uncertainty / next action

- PR #528 remains open and is now **superseded** by this composition. It should be
  closed by the human sovereign (agents do not close PRs) once #492 is reviewed;
  closing it is recorded as the recommended disposition, not performed here.
- This is a **draft** PR. It does not claim merge, deployment, or production
  acceptance. A human merges.
