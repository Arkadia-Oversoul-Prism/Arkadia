# ARK-OPS-CONTINUOUS-001 — cycle 07: the live root map advertised an archived frontend

Cycle 07 of the continuous reconciliation contract (rev 2026-11-22). This cycle's
substantive product is a repair, not a record: `PROJECT_INDEX.md` — which declares
itself the map an agent reads *instead of* exploring the tree, and binds itself to
the codebase with "Never let it drift from the codebase" — named a frontend that
does not exist and omitted the one that does.

Merge authority: **none**. Deploy authority: **none**. This record claims no merge,
no deployment and no acceptance.

## Reconstructed state

| fact | measured |
|---|---|
| canonical `main` | `bb19aabda34d59594615b0279a45e9cbd3d8204d` |
| production `GET /api/version` | `200`, 643 B, `source_revision` == `main`, `revision_conflict: false` |
| `main` check-runs | `boot-syntax`, `console-contract`, `engineering-scheduler`, `posture-currency`, `test`, `Full-history secret scan` → all `success`; `weaver_evolution` skipped |
| open PRs | **37**, all drafts, all `base: main` |
| PR heads verified | 37 local refs, 37 matched the live `headRefOid`, 0 mismatched |

Production revision equality is necessary evidence of source↔runtime consistency.
It is not proof of correct application behaviour and not deployment acceptance.

## The defect

`PROJECT_INDEX.md` @ `bb19aabd`:

```
## Presentation
```
web/public_prism/        React/Vite SPA — npm run dev on port 5173
  src/components/        UI components
  src/views/             Page views
  src/contexts/          React contexts (voice, oracle, auth)
```

## Configuration
```
web/public_prism/package.json   Frontend dependencies
```

`web/public_prism/` was archived into `archive/frontend/arkadia-prism/` by
`c081d200` (2026-10-11, "Frontend rebuild: archive Prism UI, scaffold canonical
Arkadia Console"). `git log -1 -- web/public_prism/` returns that commit and no
later one; the tree does not exist at `main`.

The active console is `web/arkadia_console/` (`arkadia-console`, Vite dev port
**5100**), which the map never named. `web/console/` still exists and is retired
(`.github/workflows/operator-console-posture.yml`: "`web/console` is retired").

Two secondary currency defects in the same map:

| claim @ `bb19aabd` | measured |
|---|---|
| `api/main.py — 2506 lines` | `wc -l api/main.py` → **2597** |
| `docs/phase1/...`, `tests/architecture/...` etc. | all present — no other drift |

### Why nothing caught it

`grep -rln "PROJECT_INDEX" tests/ scripts/ .github/` → **no match** on `main`.
The only root-document gate is `root-doc-link-integrity.yml` (#714, open), which
reads inline markdown *links* and explicitly excludes fenced code blocks — and
this claim lives inside a fenced block. So the map's own currency contract was
enforced by nothing.

## The repair

`PROJECT_INDEX.md`:

* Presentation → `web/arkadia_console/` (active console, port 5100) with its real
  subdirectories (`src/components/`, `src/pages/`, `src/contexts/`, `src/lib/`,
  `src/operator/` — each verified present), plus `web/console/` labelled retired;
* Configuration → `web/arkadia_console/package.json`;
* `api/main.py` line claim → the stale hard number is **removed** rather than
  replaced. A doc pinned to a line count drifts on the next commit; the budget
  itself is pinned by `tests/architecture/test_layer_boundaries.py`, which the map
  now points at.

`REPOSITORY_SNAPSHOT.md` carries the same `web/public_prism/` claim and is
**deliberately not rewritten**: its header says "Last generated: Phase 1, B0.5
complete (2026-07-25)". It is a point-in-time record, and editing it to look
current would contradict its own header. The guard excludes documents carrying a
generation marker and states that exclusion.

## The guard

`tests/test_root_doc_module_map_currency.py` (39 nodes):

* **derived domain** — root `*.md` at test time, minus documents carrying
  `Last generated:`. A newly added root document is judged by the same rule; the
  document list is not restated anywhere.
* **invariant** — every `web/...` entry *inside a fenced code block* must exist.
  Prose mentions and inline examples are not claims and are not judged, so a
  document may discuss an archived surface honestly.
* **controls** — the pre-repair snippet, verbatim, must be reported as
  `['web/public_prism/', 'web/public_prism/package.json']`; a synthetic map of
  present surfaces must be clean; a prose mention must be clean; a dated snapshot
  must be excluded *and* enrolled once its marker is removed.
* **wiring** — `test_the_gate_selects_every_input_its_guard_reads` requires the
  `pull_request` and `push` filters to name `*.md`, `web/**`, the guard and the
  gate itself; `test_the_gate_executes_the_guard` requires an *invoked* `pytest`
  whose arguments contain the guard (a tokeniser, so `echo pytest <guard>` and a
  comment do not count — proven by a control); `test_the_gate_cannot_be_disarmed`
  rejects step- and job-level `continue-on-error` and `if: false`.

`.github/workflows/root-doc-module-map.yml` executes it, is `workflow_dispatch`able,
and is selected by every input the guard reads.

## Checks run

| command | result |
|---|---|
| `pytest -q tests/test_root_doc_module_map_currency.py` | **39 passed** |
| live negative control: `git checkout -- PROJECT_INDEX.md` | **2 failed, 37 passed** (`test_a_live_root_map_declares_only_present_web_surfaces[PROJECT_INDEX.md]`, `test_the_map_names_the_active_console`), restored byte-identically (`sha256 4c5ae375…` before and after) |
| `pytest -q tests/architecture tests/test_prism_console_ci_wiring.py` | **45 passed** |
| gate-integrity bundle (trigger coverage + its wiring, suite collection continuation, verdict-step integrity + its wiring, filter selection, workflow injection, boot-syntax wiring, m02a) | **439 passed** |
| `python scripts/console_contract_domain.py` | **74 → 75** guards; the new guard joins the derived domain, so the console-contract gate executes it without an edit |
| `python scripts/cp10_mutation_boundary_policy.py --judge` on the changed paths | `Mutation boundary PASS`, exit `0` |
| full suite on `main` @ `bb19aabd`, `-q -rEf --continue-on-collection-errors` | **19 failed, 4250 passed, 22 skipped, 1 error** in 284.64 s; **20** failing/error nodes, outcomes `8d70e46e…` / ids `d6101722…` — the recorded baseline, reproduced exactly |

## Queue composition (re-derived, not inherited)

Cycle 05 judged 31 PRs / 465 pairs. The queue is now 37 / **666** pairs, so **201**
pairs had never been judged:

```
666 pair(s) judged
  CLEAN 665 · CONFLICT 1 · UNPROVABLE 0
  681 x 687   CONFLICT   tests/test_gate2_production_observation.py
```

The 201 newly judged pairs contain no conflict. The queue's only ordering
constraint is unchanged and is the pair #703 adjudicates.

## Limitations

* `web/**` in the gate's `paths` filter is deliberately broad: the guard reads
  the existence of the `web/` tree, so a deletion there must re-run the judge.
* The guard checks existence, not the accuracy of each one-line description.
* `REPOSITORY_SNAPSHOT.md` still names `web/public_prism/`; that is a recorded
  decision (dated record), not an unclosed gap.
* `main` has no branch protection and no rulesets. That creates no merge
  authority.

## Next authorized action

Human review of the queue. No agent merge, no push to `main`, no deployment, no
acceptance.
