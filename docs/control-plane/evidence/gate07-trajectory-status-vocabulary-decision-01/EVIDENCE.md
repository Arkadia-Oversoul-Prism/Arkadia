# EVIDENCE — gate07/trajectory-status-vocabulary-decision-01

Workstream: `gate07/durable-weaver-loop` (GATE-07)
Move class: bounded **verification + decision record** (no gate promotion, no authority
change, no subject-PR mutation)
Base: `main` @ `4587890efe0a4090aa9ffbf55413bcb4fe01e2bd` (#327)
Branch: `gate07/trajectory-status-vocabulary-decision-01`
Authority: verification and evidence only — no merge, no push to `main`, no code change to
PR #329 / #330 / #331.

## 1. Purpose

A vocabulary defect is live on `main`: the trajectory schema admits a move status the
router cannot route. PR #330 records it as a *proposed* workstream. This pass does three
things the prior records do not:

1. establishes that the obvious repairs are **not behaviour-equivalent** (so the choice is
   a semantic decision, not a cosmetic one);
2. identifies the **authority-bearing** option and classifies it;
3. records a baseline fingerprint measured twice, and reconciles a documented
   discrepancy with a prior record.

Nothing here is executed against the router or the trajectory.

## 2. Reconstruction (live, this pass)

| item | measured value |
|---|---|
| `main` | `4587890efe0a4090aa9ffbf55413bcb4fe01e2bd` (#327) |
| working tree | clean (`git status --porcelain --untracked-files=no` empty) |
| PR #329 | open, `mergeable: true`, `UNSTABLE`, head `9c7c57644f1b…` |
| PR #330 | open, `mergeable: true`, `UNSTABLE`, head `918337cc9945…` |
| PR #331 | open, `mergeable: true`, `UNSTABLE`, head `be1f3f053f4d…` |
| `api/main.py` | untouched; `py_compile` OK |

## 3. The defect, re-derived against source (not PR prose)

Router constants (`weaver/engineering_router.py:22-23`):

```
ACTIVE_STATUSES = {pending, revision_required, in_progress}
TERMINAL_DONE   = {completed, accepted, merged}
```

Schema enum (`docs/control-plane/trajectory.schema.json`):

```
{aborted, accepted, blocked, completed, failed, in_progress,
 merged, merged_acceptance_pending, pending, revision_required}
```

`select_next_move()` (`:99-158`) iterates the moves in order. A move is *done* only if its
status is in `TERMINAL_DONE` **or** the completion index marks it done. A move whose status
is outside `ACTIVE_STATUSES ∪ TERMINAL_DONE` is appended to `unrecognized` and skipped. When
no move is returned, the `unrecognized` names are emitted as a blocker instead of the
fallback — the truthfulness fix merged as #322.

Live trajectory `docs/control-plane/TRAJECTORY-CONSOLE-COMPLETION-01.yaml`:

```
G12-A merged_acceptance_pending   G12-B in_progress   G12-C merged_acceptance_pending
G14   pending                     G15   pending       G16   pending
```

Measured routing outcome (live data, unmodified router):

```
selected move: None
blockers: ["unrecognized move status: G12-A ('merged_acceptance_pending'),
            G12-C ('merged_acceptance_pending') — cannot route; expected one of
            accepted, completed, in_progress, merged, pending, revision_required"]
```

## 4. The finding: the repairs are not behaviour-equivalent

The vocabulary seam is guarded in **one direction only**.

`tests/test_trajectory_schema_conformance.py::test_schema_move_enum_covers_the_router_vocabulary`
asserts `router ⊆ schema` — it holds:

```
router ⊆ schema : True
schema ⊆ router : False   (not asserted anywhere)
schema-legal but router-unroutable: [aborted, blocked, failed, merged_acceptance_pending]
```

Three candidate repairs were applied in memory to a copy of the live trajectory and the
router was re-run on each. They produce **three different results**:

| # | repair | selected move | blockers | consequence |
|---|---|---|---|---|
| A | trajectory data: `merged_acceptance_pending` → `merged` | **G12-B** | `[]` | correct frontier; records G12-A/C as merged |
| B | router `TERMINAL_DONE += merged_acceptance_pending` | **G12-B** | `[]` | correct frontier, same routing as A |
| C | router `ACTIVE_STATUSES += merged_acceptance_pending` | **G12-A** | `[]` | **wrong move** — selects an already-merged move |
| — | no repair (current `main`) | `None` | unrecognized-status blocker | correct *naming*, no frontier selected |

Candidate C is the dangerous one and the least visible: adding the status to
`ACTIVE_STATUSES` makes the guard pass and silences the blocker, while making the hourly
session select a move whose pull request (#315) was **already merged** on
2026-10-05T17:33:12Z. The router's own docstring states it "does not invent moves, reorder,
expand scope" — C makes it route *backwards*.

So `merged_acceptance_pending` is not a synonym for `merged` in the router's model: it
encodes "the PR merged but repository acceptance evidence is not yet recorded", a state the
router has no vocabulary for. A and B are equivalent *for this trajectory* but not in
general — B would mark such a move terminal and let dependents proceed with no acceptance
evidence; A records the acceptance claim in the trajectory data, which is the artifact the
completion index is meant to carry (`docs/control-plane/evidence/*/ACCEPT.json`).

## 5. Authority classification (the reason this is not executed)

Repair A changes the live trajectory's completion claim and enables autonomous routing to
**G12-B** (`durable-offline-queue-state-machine`), which would then be implemented by the
hourly session. The governance block of that trajectory lists `autonomous_next_move` as
forbidden. Repair A therefore carries an authority implication the router-only repair (B)
does not: it asserts completion on behalf of the sovereign.

This is why the repair is **not executed here** — not because the change is large (A is a
two-line data edit) but because it decides an authority question. The contract classifies
this correctly as a human-authority decision, and the existing blockers message — now that
#322 landed — already fails closed and names the cause.

## 6. Candidate resolution (decision-ready, not executed)

- **Recommended:** repair **A** — set G12-A and G12-C to `merged` in
  `TRAJECTORY-CONSOLE-COMPLETION-01.yaml`, justified by PR #315 (merged
  `2026-10-05T17:33:12Z`) and PR #316 (merged `2026-10-05T17:36:09Z`), with the acceptance
  evidence recorded under `docs/control-plane/evidence/*/ACCEPT.json`.
- **Rejected:** repair **C** — routes an already-merged move and silences the blocker.
- **Acceptable but weaker:** repair **B** — no authority implication, but it conflates
  "merged" with "accepted" and lets dependents proceed without acceptance evidence.
- **Do not:** close the seam by making the router vocabulary equal the schema enum. The
  schema's `aborted` / `blocked` / `failed` are *terminal-not-done* states; widening
  `TERMINAL_DONE` to absorb them would let a blocked move's dependents proceed.

Independent of the choice, the seam's untested direction should be pinned: a guard that
every **schema-legal** move status is either routable or explicitly named as unroutable, so
a future schema addition cannot silently create a frontier the router cannot route.

## 7. Baseline fingerprint (measured twice, this pass)

Command: `python -m pytest tests/ -q -rEf --continue-on-collection-errors`
Fingerprint: `python scripts/baseline_fingerprint.py <log>`

```
main 4587890 : 14 failed, 1580 passed, 21 skipped, 1 error   (136.03s / 135.5s)
tests/architecture : 11 passed

outcomes fingerprint : 093938e8aa68086d838772a048564f44239643da7122401f697aa201573c4ce8
ids fingerprint      : 5f186112cb1638a8e75e92a3b3b5eaade09dad00a27db5c8f2456e39201f35dc
```

Two independent runs produced the **identical** outcomes fingerprint — the baseline is
stable in this environment (it is not the documented intermittent one).

### 7.1 Reconciliation with PR #330

PR #330 measures **10 failed / 11 nodes / `f3e73647…`** at this same SHA; this pass measures
**14 failed / 15 nodes / `093938e8…`**. The delta is **+4**, and all four are
`tests/test_agents_md_encoding_adjudication.py`:

```
test_live_file_verdict_matches_its_state
test_corruption_origin_is_re_derivable
test_cli_summarises_the_oracle_without_crashing
test_exit_code_does_not_call_a_divergent_clean_file_verified
```

`tests/fixtures/baseline_node_set.txt` (10 nodes) reproduces the **documented canonical ids
fingerprint** `124bfdfd078fe878fe7c9de358ba271e977c4f7b73909b9d7d016b9ae9c1e87f` exactly
(computed, not remembered). Removing the four `agents_md` nodes from this pass's 15 yields
**11 nodes**, matching PR #330's count — so the node-set *shape* agrees and only the
`agents_md` family differs.

The `agents_md` tests audit the live `AGENTS.md` against an oracle revision and are
explicitly recorded as clone-depth / revision-access dependent. This clone is **not**
shallow (`git rev-parse --is-shallow-repository` → `false`). Their failure is attributable
to the live file's encoding state in this checkout, not to any node introduced by gate07
work. The environment-independent claim is therefore: **zero gate07-attributable node
delta**; the `agents_md` difference is a pre-existing, separately-recorded class
(`AGENTS.md` encoding adjudication), not a gate07 regression.

## 8. What this pass did not do

- No change to `weaver/engineering_router.py`, any `TRAJECTORY-*.yaml`, or the schema.
- No mutation of PR #329 / #330 / #331; no merge; no push to `main`.
- No repair of the `agents_md` encoding class (separate recorded workstream).
- No repair of the `test_ais_capability_profile_onboarding` test-side literal pin.

## 9. Verification commands

```
python -m py_compile api/main.py
python -m pytest tests/architecture -q -rEf
python -m pytest tests/ -q -rEf --continue-on-collection-errors
python scripts/baseline_fingerprint.py <log>
printf '<changed paths>' | python scripts/cp10_mutation_boundary_policy.py --judge
```

CP10 mutation boundary judge over this pass's changed paths: **PASS**.
