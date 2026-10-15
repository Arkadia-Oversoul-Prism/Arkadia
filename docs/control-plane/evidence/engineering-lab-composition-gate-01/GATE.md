# Engineering Lab composition gate — AEAS execution directive

Observed 2026-10-15. Mode: evidence-bound implementation and verification.
Merge authority NOT GRANTED. EAA/dispatch authority NOT GRANTED.

## 1. Outcome

**BLOCKED** — on the directive's premise, not on a candidate defect.

**Why BLOCKED and not INCONCLUSIVE.** `BLOCKED` is "required evidence or execution
capability is unavailable"; `INCONCLUSIVE` is "results do not establish either pass or
failure". Here the results establish a great deal — what is unavailable is the *source
material the directive names*. **Six of the seven named source PRs were closed unmerged
at ~17:03Z on 2026-10-15**, about an hour before this pass began, each with a recorded
disposition of "CLOSE AS SUPERSEDED" by merged **#533** (merge commit
`7580bd8f0ca2925518d78775f9a323ff0df8bc66`). Their content is on `main` through that
merge, not through their own heads. The seventh (#525) is open and was already decided
HELD in the prior pass.

A single "combined candidate" that reconciles seven source heads cannot be built when
six of those heads are closed and their artifacts are absent from `main`. That is a
capability/premise block, stated plainly rather than worked around.

**What is *not* blocked, and was done instead.** The substantive Engineering Lab
composition is **already on `main`** (via #533) and its governing invariant was
verified directly on `main` — exactly one canonical work-loop render site. On top of
that, four separately-scoped bounded repairs were rebuilt against current `main` and
validated at exact heads (section 5).

Acceptance-gate boxes, honestly:

| Gate item | Status |
|---|---|
| Baseline and all source heads recorded | satisfied |
| All seven source PRs have evidence-backed reconciliation decisions | satisfied (6 "already present via #533", 1 "held") |
| No unresolved conflicts remain | satisfied (test conflicts resolved as unions) |
| Exactly one canonical work-loop mount verified | satisfied (on `main`) |
| Operational/authority/grammar/Weaver/composition contracts pass | satisfied via #533 on `main` (17 passed) |
| Relevant regressions pass | satisfied (node set identical) |
| Frontend production build completes | satisfied (2 candidates + control) |
| Results tied to exact final candidate SHA | satisfied |
| Changed-file inventory and test evidence retained | satisfied |
| No unauthorized merge / production / unrelated disposition change | satisfied |
| **One coherent candidate composed from the seven named heads** | **BLOCKED — six heads closed unmerged** |

## 2. Baseline

| Item | Value |
|---|---|
| `main` at pass start | `341867ebe4ea80ead557ca632707833b7620430a` |
| `main` at pass end | `341867ebe4ea80ead557ca632707833b7620430a` (unmoved) |
| Frozen base from prior pass | `7580bd8f0ca2925518d78775f9a323ff0df8bc66` (ancestor of `main`) |
| Accepted composition | #533, merge `7580bd8f`, head `8d52eb3f` |

## 3. Source PR reconciliation

| PR | Head SHA | State at pass | Disposition | Evidence |
|---|---|---|---|---|
| #512 | `f8da515842` | CLOSED unmerged 17:03:40Z | **already present** (via #533) | closure comment: superseded by #533; own tests pass vs main tree |
| #530 | `f54d463c6a` | CLOSED unmerged 17:03:52Z | **already present** (via #533) | closure comment: 7 render-integrity tests pass vs main |
| #524 | `aad8a986e3` | CLOSED unmerged 17:03:46Z | **already present** (via #533) | closure comment: 8 tests pass vs main |
| #493 | `255d665f4f` | CLOSED unmerged 17:03:30Z | **already present** (via #533) | closure comment: 22+27+12+5 tests pass vs main |
| #501 | `31d66332c7` | CLOSED unmerged 17:08:02Z | **already present** (via #533) | closure comment: canonical work-loop mount + test on main via #533 |
| #525 | `daef33c4d0` | OPEN draft | **held** (prior decision) | Arrangement D proved capability deliverable at one render site; not integrated |
| #504 | `a9cefd2142` | CLOSED unmerged 17:03:35Z | **already present** (via #533), evidence doc excluded | closure comment: 3+11 tests pass vs main; evidence-doc insertion recorded as excluded |

Artifact check against `341867eb` (the six closed PRs' own artifacts):

```
web/arkadia_console/src/components/lab/LabWorkLoop.tsx            absent   (#525-only, held)
web/arkadia_console/src/components/lab/ExecutionLoop.tsx          ON MAIN  (#533)
web/arkadia_console/src/pages/EngineeringLabPage.tsx              ON MAIN  (#533)
web/arkadia_console/src/components/lab/LabOperationalReadings.tsx absent
web/arkadia_console/src/components/lab/AutomationGrammar.tsx      absent
tests/test_prism_w4_lab_read_model.py                             ON MAIN  (#533)
tests/test_prism_w4_lab_composition.py                            absent
```

## 4. The one-canonical-work-loop invariant, verified on `main`

- Sole render site: `web/arkadia_console/src/pages/EngineeringLabPage.tsx:47`
  (`<ExecutionLoop stages={readLoopStages(...)} />`), imported at line 11.
- Only importer of `ExecutionLoop` in the tree: `EngineeringLabPage.tsx`.
- `tests/test_prism_w4_lane4_render_integrity.py` + `tests/test_prism_w4_canonical_loop_mount.py`:
  **17 passed**, 2 errors (API-level, dependency-limited in this environment).
  Includes `test_the_canonical_loop_is_rendered_by_the_lab_page` and
  `test_no_lane4_projection_is_orphaned`.
- `LabWorkLoop.tsx` (the #525 read model) is **absent** from `main`, so no second
  mount exists.

## 5. Bounded repairs produced this pass

Four candidates, each rebuilt against current `main` (`341867eb`) rather than revived
as-is. All pushed to review branches; **none merged**.

| Unit | Branch | Head SHA | Origin | Focused result |
|---|---|---|---|---|
| A | `gate10/history-depth-repair-02` | `b63f74e8` | #482 | guard 17 passed |
| B | `ui/alias-families-union-02` | `e350316d` | #505 (rebased over merged #497) | 38 passed |
| C | `ui/return-to-error-boundary-02` | `35951e6e` | #514 (rebased over merged #511) | 59 passed |
| D | `eaa/chain-composition-02` | `a68fefbd` | #535 | 43 passed |

Each branch's test conflict was resolved as a **union** of both parents' probe sets,
not by reviving the stale branch. See `UNITS.md` for per-unit detail.

## 6. Verification table

| Check | Tested SHA | Result |
|---|---|---|
| `provider-routing.yml` (judging) | `b63f74e8` | **failure**, 9 nodes — 5 fewer than `main`'s 14, 0 new |
| `provider-routing.yml` (judging) | `341867eb` (baseline) | failure, **14** nodes |
| `prism-console-contract.yml` | `e350316d` | success |
| `prism-console-contract.yml` | `35951e6e` | success |
| `lab-security-contract.yml` | `a68fefbd` | success |
| `gitleaks-config-guard.yml` | `a68fefbd` | success |
| `weaver-mvp2-validation.yml` | `a68fefbd` | success |
| `boot-syntax.yml` | `b63f74e8` | success |
| full suite, candidate A vs baseline | `b63f74e8` vs `341867eb` | node set `9de837ea…` **identical** (214 nodes, `comm -3` empty) |
| full suite, candidate D vs baseline | `a68fefbd` vs `341867eb` | node set `9de837ea…` **identical** |

`provider-routing` is a *judging* surface: it stays red on pre-existing repository
debt by design. The measurement that matters is the node set, and the repair's effect
is decisive:

- CI at `main` `341867eb`: **14** failing/error nodes.
- CI at candidate A `b63f74e8`: **9** nodes.
- `comm -23 main candidate` (removed by the repair): the four
  `test_agents_md_encoding_adjudication.py` nodes **and**
  `test_lane_instruction_doc_currency.py::test_detector_flags_a_merged_pr_left_recorded_as_open`
  — all five are shallow-checkout artifacts.
- `comm -13 main candidate` (introduced by the repair): **empty**.

The CI log names the mechanism verbatim for the lane-doc node:

```
AssertionError: ['lane 1: PR #423 cannot be adjudicated -- merge commit 972c3423
is not in this clone (shallow checkout?); liveness is UNKNOWN, not a pass']
```

The repair (`fetch-depth: 0`) removes exactly the five nodes whose oracles read git
ancestry, and introduces none. The 9 remaining nodes are pre-existing debt present at
`main` too.

## 7. Frontend production build

| Tree | SHA | Result |
|---|---|---|
| candidate B | `e350316d` | **success** — `index-4-WtClOi.js` (144,301 B) |
| candidate C | `35951e6e` | **success** — `index-CraRQ7Av.js` (145,491 B) |
| `main` (negative control) | `341867eb` | success — `index-C6Of8UdF.js` (143,961 B) |

Marker presence/absence, candidate C vs the `main` control:

| Marker | C | `main` |
|---|---|---|
| `surface-error-boundary` | 1 | **0** |
| `surface-error-reload` | 1 | **0** |
| `arkadia.returnTo` | 1 | 1 (from merged #511) |

The control proves the boundary markers discriminate the change rather than reading a
stale artifact. Candidate B's alias markers (`/knowledge-os`, `/living-gate`, `/nexus`,
`/gate`, `/home`) are each present in its bundle.

## 8. Safety declaration

- **No merge** was performed. `main` is unmoved at `341867eb`.
- **No production change** and no deployment was triggered.
- **No EAA/dispatch PR advanced** (#502, #503, #508, #500, #499, #496 untouched).
- **No unrelated PR disposition changed.** #535 and #525 remain open drafts.
- Four review branches were published at explicit SHAs (no force-push). Publishing
  review branches is not a merge and carries no production effect.
- The six closed PRs were closed by the repository owner *before* this pass; this pass
  changed none of them.

## 9. Remaining blockers / next authorized action

- **Premise blocker:** the directive names six closed PRs as live candidates. Re-scope
  the directive against `main` (`341867eb`), which already carries the composition via
  #533.
- **Queue:** #542/#543 (Knowledge OS route overlap) and #538/#544 (buyer-recon overlap)
  each need combining; not attempted in this pass (see `QUEUE.md`).
- **Next authorized action:** human review of the four candidate branches; a separate
  acceptance decision. No merge.
