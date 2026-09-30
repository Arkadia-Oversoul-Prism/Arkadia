# WORKSTREAM_STATE — `gate-hygiene` / SH-02 (baseline STALE_ASSERTION migration)

Persisted so the next hourly heartbeat reconstructs from evidence, not memory.
**Reconstruct live state anyway (contract §14) — do not trust this file over the repository.**

Supersedes the pass record at
`docs/control-plane/evidence/gate-hygiene-baseline-stale-assertion-repair-spiral-grove-05/WORKSTREAM_STATE.md`
and the `SH-02` rows of
`docs/control-plane/evidence/gate-hygiene-baseline-ledger-correction-01/WORKSTREAM_STATE.md`.

## Pass record — 2026-09-29 (heartbeat, ~23:06Z) — correction pass, docs-only

Continues the same PR (#140). Re-measured this PR’s **own** load-bearing premises before
selecting work; **two were false** and are withdrawn. The §4 disposition is **unchanged**.

- **Falsified premise 1 — “grafted clone”.** The clone is complete (§11.1). The derived
  claim “every *X is an ancestor of `df7a99a`* sentence is UNKNOWN” was wrong and is
  **replaced with verified measurements**: `a26af408` is an ancestor at distance 149;
  `d48ad0e` resolves, is the PR #97 merge, and its 24-path diff **passes** the current CP10
  policy judge. Both historical claims are now **closed, not carried**.
- **Resolved uncertainty — `F-02` provenance (§11.2).** Bisected: red at the **root commit**
  `9ab26fc`, both files byte-identical to genesis. Strongest available answer; it *strengthens*
  the §4.3 disposition rather than changing it.
- **Resolved uncertainty — historical SG-04 SHAs (§11.3).** `74f5494`/`1b63994`/`06ad5f2`
  resolve; `mount=1` on each vs `mount=0` on `main`; `06ad5f2` is an ancestor of `main`.
  §5’s `SH-08` premise is **independently corroborated**.
- **Fingerprint re-measured, unchanged:** `32 failed / 1025 passed / 13 skipped / 2 errors`;
  `tests/architecture` **11/11**; `api/main.py` **2519 / 2600**, `py_compile` clean.
- **No new bounded task inside `SH-02`.** Queue remains exhausted (19 green / 12 carried by
  open PRs / 4 decisions / 0 to batch). `F-02` and `SH-08` remain sovereign decisions.

## Pass record — 2026-09-29 (heartbeat, ~21:06Z)

- **`BASE_MAIN` = `df7a99a067382401c00de5e7bbaaac0125ba2088`** (merge of PR #131). Local
  `main`, `origin/main`, `origin/HEAD` all agree; working tree clean.
- **The clone is COMPLETE, not grafted** — corrected in the hour-23:06Z pass; the earlier
  “grafted” reading was a tooling artifact. `df7a99a` has two parents (`94afda6`,
  `ddb30d0`); 1393 commits reachable; root `9ab26fc`; not shallow, no grafts, no
  alternates. `git merge-base` is therefore well-defined, and *“`X` is an ancestor of
  `df7a99a`”* is **verifiable and true** (`a26af408` → distance 149). EVIDENCE.md §11.1.
- **Fingerprint:** `32 failed / 1025 passed / 13 skipped / 2 collection errors`;
  `tests/architecture` **11/11**; `api/main.py` **2519 / 2600**, `py_compile` clean;
  `vite build` environment-blocked.
- **Selected task:** settle the `SH-02` queue denominator before selecting another batch.
  **Result: the `SH-02` candidate set is exhausted (0 open batch candidates).**
- **Publication:** branch `gate-hygiene/sh02-queue-disposition-01` → **docs-only**. No merge,
  no push to `main`, no force-push.

## The `SH-02` denominator — 35 nodes, 4 dispositions, 0 residue

| disposition | count | next action |
|---|---|---|
| **GREEN on `main`** | **19** | none, ever — do not re-repair |
| **IN_OPEN_PR** | **12** | finish by **merging** the carrier PR |
| **RESIDUAL** | **4** | needs a **sovereign/architectural decision**, not a batch |
| **open SH-02 batch** | **0** | — |

Derivation (reproducible): base node list from
`PYTHONPATH=<repo>/archive/legacy_python python -m pytest tests/ -q -p no:cacheprovider
--continue-on-collection-errors | grep -E '^(FAILED|ERROR) ' | sed 's/ - .*//' | sort`,
intersected with the ledger's 35 `STALE_ASSERTION` rows and with four branch fingerprints
(`base_nodes − branch_nodes` = nodes the branch fixes). Full tables:
`docs/control-plane/evidence/gate-hygiene-sh02-queue-disposition-01/EVIDENCE.md` §4.

### IN_OPEN_PR carriers (all based on `df7a99a`; none needs a rebase)

| PR | branch @ head | nodes | ledger rows |
|---|---|---|---|
| #133 | `gate-w2/living-gate-grove-handoff` @ `b8e6afc` | 5 | 3–6, 8 |
| #135 | `gate-hygiene/sh02d-prism-interior-shell-rebase-01` @ `90544c9` | 3 | 10–12 |
| #136 | `gate-hygiene/sh02e-agent-run-capability-onboarding-repair` @ `a919651` | 2 | 1, 2 |
| #137 | `gate-hygiene/sh02f-solspire-p1-experience-01-repair` @ `28686cb` | 2 | 22, 23 |

### RESIDUAL (4) — decisions, not batches

- `test_ais_w2_living_gate_grove_handoff.py::test_no_firebase_persistence_in_gate` — **`F-01`**,
  already logged; #133 deliberately leaves it red (proxy-invalidation).
- `test_steward_filter.py` ×3 (`test_blocks_identity_claims`, `test_allows_mythic_with_action`,
  `test_compress_to_choices`) — **`F-02`**, new: the underlying behaviour, not only the
  assertion, has diverged (`"transcended"` vs the forbidden `"transcendent"`; Rule 4 strict
  mythic-density blocking a passing action sentence; `compress_to_choices` splitting on `\n`
  only). The ledger's own `SH-06` called this "borderline: arguably a real content-hygiene
  hole" — this pass confirms it and folds `SH-06` into `F-02`.
  **Bisected (hour-23:06Z pass):** `weaver/filters/steward.py` and `tests/test_steward_filter.py`
  each have exactly one commit in all history — the root commit `9ab26fc` — and both are
  byte-identical to it. The three nodes are red **at the root commit**, on a parentless tree.
  `F-02` is not a regression introduced by any commit; the filter and its test were authored
  together, contradictorily, at genesis. See EVIDENCE.md §11.2.

## Repair queue (`SH-*`)

| id | task | bucket | state |
|---|---|---|---|
| `SH-01` | `SOLSPIRE_PROJECTS_DB` env leak | REAL_DEFECT | **already fixed on main** |
| `SH-02` | 35 stale string assertions, bounded batches | STALE_ASSERTION | **EXHAUSTED** — 19 green / 12 carried by open PRs / 4 decisions / 0 to batch |
| `SH-02b` | `test_prism_pass_c_surface_ownership.py` (6 nodes) | STALE_ASSERTION | **done** (PR #127, merged) |
| `SH-03` | `"DERIVED"` vs `"DERIVED_BOUNDED_SEMANTIC"` contract split | DRIFT | awaits product decision |
| `SH-04` | is `CapabilityRegistry` cycle detection reachable? | DRIFT | **RESOLVED — no defect** (test is wrong about ordering) |
| `SH-05` | fate of `test_gate_serve_script` / `test_gate_status` | ENV | sovereign call |
| `SH-06` | should `steward_filter` stem-match `transcend*`? | STALE_ASSERTION | **folded into `F-02`** |
| `SH-07` | shared-session key in `ArkanaCommune.tsx` | DRIFT (high) | awaits architectural gate |
| `SH-08` | **which activity surface is canonical?** | CONTRADICTION | sovereign decision — **now scoped to 4 nodes, see below** |
| `F-01` | `test_no_firebase_persistence_in_gate` proxy-invalidation | DRIFT | sovereign decision |
| `F-02` | `test_steward_filter.py` ×3 — behaviour divergence, not copy drift | REAL_DEFECT (proposed) | **NEW** — sovereign/product decision |
| `R1/R2/R3` | solspire recon: `pass_id` delegation, `commit_file` `code`, `MUTATION_DISABLED` | REAL_DEFECT | separate workstream, workflows inert for `main` |

## `SH-08` — scope corrected, premise partially falsified

- **Reproduced:** `<ActivityRuntime/>` is **not mounted** on `main`
  (`grep -c '<ActivityRuntime'` → `0`; only a dangling `import` at
  `CapabilityChamber.tsx:4`). §11.1's mount finding stands.
- **Falsified (this pass):** §11.1's proposed reclassification of ledger rows 24–26
  (`spiral_grove_chambers`, `spiral_grove_frontend_projection`,
  `spiral_grove_learning_path_projection`) from `STALE_ASSERTION` → `CONTRADICTION`. Those
  three nodes are **green on `main`** (`3 passed`), each asserting a machine-readable marker
  plus a rewording-tolerant regex — the signature of an **already-migrated `SH-02`
  assertion**. Corrected disposition: **green, do not touch**.
- **Therefore `SH-08` = 4 nodes, not 7:** the four in
  `tests/test_spiral_grove_activity_runtime.py` (absent from the ledger; red on `main`).
- **The sovereign question narrows to:** re-mount `<ActivityRuntime/>` (an existing
  unreferenced component plus a never-implemented `data-testid="activity-surface-*"` contract)
  ahead of the inline surface `main` ships? **Product/UI decision, CP10-fenced
  (`sg-02-fe-2-v.yml`) → OUT_OF_SCOPE for this workstream. Do not act.**
- **Do not silently adopt this correction into the ledger.** Reclassifying the ledger is an
  edit to a different workstream's artefact; it is recorded in this pass's EVIDENCE.md §5 and
  proposed for a follow-up, not applied.

## Next bounded task

**None inside `SH-02`.** The migration is complete or transferred:

1. **Merge sequencing (sovereign).** The four carriers in §"IN_OPEN_PR" retire 12 rows.
   PR #139 records `#133 → #138 → #135 → #136 → #137 LAST`. Observed: `#137` is the smallest
   carrier (2 nodes) and the only one touching `tests/test_solspire_p1_experience_01.py`, so it
   cannot collide with the other three on content; merging it earlier reduces the residual
   conflict surface. **Flagged, not acted on** — merge order is sovereign authority.
2. **`F-02` (sovereign/product).** Decide whether `weaver/filters/steward.py` should
   stem-match `transcend*`, whether Rule 4 strict mythic-density should outrank Rule 3 action
   language, and whether `compress_to_choices` should split sentences rather than lines.
3. **`SH-08` (sovereign/product).** As narrowed above.
4. **Nothing else.** Do **not** invent a "batch 6". Do **not** repair the 19 green nodes. Do
   **not** touch `DRIFT`, `ENV/ARTIFACT`, or the `R1/R2/R3` recon nodes from this workstream.

## Rules unchanged

Re-point an assertion at the surface that now owns the behaviour; run a negative control
proving the repaired assertion can still fail. Test-only edits; **never** touch `api/main.py`,
`LAYER_MAP.py`, ADRs, `web/public_prism/**` capability code, or governance files from this
workstream. Never merge, never push `main`, never force-push. Human sovereign retains merge,
authorization, identity-boundary, authority-model, and constitutional authority.
