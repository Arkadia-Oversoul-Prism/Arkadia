# EVIDENCE — gate hygiene / SH-02 batch 5 (spiral-grove chambers + projections)

**Gate/workstream:** `SH-02` (baseline `STALE_ASSERTION` migration), batch 5
**Branch:** `gate-hygiene/baseline-stale-assertion-repair-spiral-grove-05`
**Base:** `main` @ `4164573586860b9c7e04e1815bca4957559046a2`
**Authority:** test-only edit; no merge, no `main` push, human-sovereign merge only.

## Objective

Repair the next bounded batch of stale source-level string assertions classified
`STALE_ASSERTION` in the baseline classification ledger, without widening scope into
`DRIFT` / product-decision nodes.

## Scope decision (why these three nodes, and nothing else)

The classification ledger
(`docs/control-plane/evidence/gate-hygiene-baseline-test-debt-classification-01/BASELINE_TEST_DEBT_CLASSIFICATION.md`)
lists nodes **24, 25, 26** as `STALE_ASSERTION`:

| Node | Test | Bucket |
| --- | --- | --- |
| 24 | `test_spiral_grove_chambers.py::test_chamber_does_not_invoke_autonomous_generation_or_adjudication` | `STALE_ASSERTION` |
| 25 | `test_spiral_grove_frontend_projection.py::test_activity_draft_persistence_is_local_and_not_evidence` | `STALE_ASSERTION` |
| 26 | `test_spiral_grove_learning_path_projection.py::test_evidence_assessment_state_are_downstream` | `STALE_ASSERTION` |

All three assert the same dropped copy string against the same source file:

- asserted: `'Evidence is separate.'` and
  `'Evidence submission, assessment, and capability-state updates remain separate downstream stages.'`
- present in `CapabilityChamber.tsx`: `0` occurrences of either.

They were the only unclaimed `STALE_ASSERTION` cluster in the ledger: the
`test_prism_pass_c_surface_ownership.py` cluster is closed by merged PR #127, the
`test_ais_w6_future_skills_challenge.py` node is repaired on
`gate-hygiene/baseline-stale-assertion-repair-future-skills-04`, and the remaining
clusters are owned by open PR #130 or are `SH-08` / `DRIFT` product decisions. The
`test_prism_interior_shell.py` nodes are separately repaired on
`gate-hygiene/sh02d-prism-interior-shell`.

Repairing an unclaimed node while its siblings sit on unpublished branches would
duplicate that work, so those two branches are left untouched by this PR (see
"Out of scope" below).

## Governance boundary — what is (and is not) being repaired

This is a **copy-string re-pin**, not a boundary relaxation. The governance property
the three tests exist to protect is verified intact in the current source:

| Property | Marker in `CapabilityChamber.tsx` | State |
| --- | --- | --- |
| activity contract is the chamber's concern | `SG-03 activity contract` | present (2) |
| the chamber does not mutate learner capability state | `mutate learner capability state` | present (1) |
| the chamber does not generate exercises | `generateExercise` | **absent** (0) |
| the chamber does not adjudicate evidence | `createEvidence` | **absent** (0) |
| evidence submission/assessment are downstream | SG-03 downstream-stages prose | present |

Only the prose was reworded; no capability, no autonomy, and no adjudication was added.

## Change

Instead of pinning one paraphrase, each assertion now requires the boundary prose to
still **name evidence submission and assessment as downstream stages**, and accepts
either of the two wordings the source has legitimately carried:

```python
re.search(r"Evidence submission, assessment, and capability-state "
          r"(?:mutation|updates) remain (?:explicit|separate explicit) downstream stages\.", chamber)
```

The `mutate learner capability state` marker in the chambers test is likewise made
quote-tolerant (`mutate[s]?`), and the chambers test gains a docstring recording why the
copy was re-pinned.

This keeps teeth: a future edit that removes or weakens the boundary wording still
fails. It does not merely match "any prose".

## Verification

All commands run from the repository root.

### Targeted (the three repaired nodes + their files)

```
python -m pytest tests/test_spiral_grove_chambers.py \
                 tests/test_spiral_grove_frontend_projection.py \
                 tests/test_spiral_grove_learning_path_projection.py -q
-> 24 passed
```

### Protected architecture fitness

```
python -m pytest tests/architecture -q
-> 11 passed
```

(Architecture is 11/11 at this commit. The task brief's "expect 10/10" is stale; the
suite has grown. No architecture test was touched by this PR.)

### Negative controls (the assertions must still fail when the boundary is broken)

Both controls mutate `CapabilityChamber.tsx` **only**, run the three repaired nodes, then
restore the file.

| Control | Mutation | Result |
| --- | --- | --- |
| A — removed | boundary prose replaced with the old `Evidence is separate.` wording | **3 failed** |
| B — weakened | boundary prose replaced with `Evidence submission and assessment happen right here in the chamber.` | **3 failed** |

Control B is the load-bearing one: it proves the new regex is not a paraphrase match.

### Full suite — baseline comparison

Baseline captured on a clean `/tmp/mainwt` worktree at `main` @ `41645735` with the same
interpreter, `PYTHONPATH`, and `--ignore` set, so the fingerprints are directly comparable.

| | failed | passed | skipped |
| --- | --- | --- | --- |
| baseline (`main` @ `41645735`) | 39 | 1018 | 13 |
| this branch | 36 | 1021 | 13 |
| delta | **-3** | **+3** | 0 |

Per-node delta (`comm` on sorted `FAILED`/`ERROR` node lists):

- **removed:** the three nodes above — exactly the intended change set;
- **added:** none — **zero regressions**.

The two collection errors (`test_autonomy.py`, `test_render_codex.py`) are the documented
pre-existing baseline and were ignored identically in both runs.

### Build

`vite build` remains environment-blocked (no npm registry access in the sandbox); no
frontend source was modified, so this is not a changed regression surface.

## Remaining uncertainty

UTF-8 mojibake and em-dash encoding in `CapabilityChamber.tsx` are inconsistent across
near-identical strings. Two other assertions in the same three files pin version strings
carrying un-rendered `...` sequences (e.g. `learningActivityVersion: 'SG-03-activity-v1...'`).
They currently pass and are **out of scope** for this bounded pass; recorded here as a
candidate follow-up, not repaired.

## Out of scope (and why) — carried forward, not silently widened

Two unpublished branches hold complete, unclaimed repairs of adjacent `STALE_ASSERTION`
clusters. They are each 1 commit ahead of `main` and share `main` as merge-base, but have
**no PR**:

| Branch | Head | Repaired node(s) | PR |
| --- | --- | --- | --- |
| `gate-hygiene/baseline-stale-assertion-repair-future-skills-04` | `cefb2f5` | `test_ais_w6_future_skills_challenge.py` (node 9) | none |
| `gate-hygiene/sh02d-prism-interior-shell` | `8d1c386` | `test_prism_interior_shell.py` (nodes 10-12) | none |

This PR deliberately does **not** re-do that work and does **not** contain it. It is
recorded so state is reconstructed from evidence rather than memory. Publishing or
reconciling them is a separate bounded action.

## Authorization required

**Human sovereign merge.** No merge performed. No push to `main`. No force-push.
