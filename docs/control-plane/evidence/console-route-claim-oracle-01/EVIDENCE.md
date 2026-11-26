# Console boundary modules: two route claims the route table contradicted

**Workstream:** `console-route-claim-oracle-01`
**Contract:** `ARK-OPS-CONTINUOUS-001` (cycle 05)
**Base:** `main` `bb19aabda34d59594615b0279a45e9cbd3d8204d` (2026-11-22T17:23:48Z)
**Authority:** none claimed. No merge, no deployment, no acceptance.

## 1. What was measured

The active console (`web/arkadia_console`) renders four operator *boundary instances* under
`src/operator/data/`. Each is a claim about the substrate, and the repository already treats a
false claim there as a defect — `tests/test_console_posture_currency.py` opens with exactly that
premise ("a console whose entire value is truthful posture") and exists because three such claims
had drifted.

That guard binds three things: quoted `"METHOD /path"` surface declarations, cited test names, and
deployment flags. **A route named inside a sentence was not judged**, by design: the declaration
regex requires a closing quote so that a path mentioned in prose cannot be read as a declaration (a
false positive that was measured and repaired earlier).

That exclusion is why two false route claims survived on `main`. Measured against the deployed
route table (`GET /openapi.json`, `main` `bb19aabd`, 300 paths):

| file | claim on `main` | route table |
|---|---|---|
| `workeventNotEvidence.ts:80` | `GET /solspire/workspaces/{id}/control-room` | **no `/solspire/workspaces` route exists.** The served path is `/solspire/enterprise/workspaces/{enterprise_id}/control-room` |
| `executionNotWorkEvent.ts:86` | "there is no /solspire/enterprise route" | **15 routes are served** under `/solspire/enterprise`, including the `control-room` projection the same sentence calls the only read path |

The second claim contradicts the substrate *and itself*: it denies the namespace while naming a
route inside it as the graph's only read surface.

Measured prefix evidence:

```console
'/solspire/workspace'    exact=['/solspire/workspace']  under=0
'/solspire/workspaces'   exact=[]                       under=0
'/solspire/enterprise'   exact=[]                       under=15
control-room paths: ['/solspire/enterprise/workspaces/{enterprise_id}/control-room']  ['GET']
```

`/solspire/workspace` (singular) is served; `/solspire/workspaces` (plural) is not. The claim used
the plural — a one-character trap a reader cannot detect, and it resolves to 404.

## 2. Why this is not owned by an open PR

`GET /pulls/{n}/files` across all 28 open PRs: **zero** touch
`web/arkadia_console/src/operator/data/**` or `tests/test_console_posture_currency.py`. The defect
was unowned.

## 3. The repair

Two source corrections, no behavioural change to the application:

- `workeventNotEvidence.ts` — cite the served path
  (`/solspire/enterprise/workspaces/{enterprise_id}/control-room`).
- `executionNotWorkEvent.ts` — scope the absence to the graph rather than denying the namespace:
  "none of the `/solspire/enterprise` routes exposes the graph itself".

The second is not a cosmetic reword. The first attempted repair kept the phrase "no
/solspire/enterprise route exposes the graph itself", and the new detector **rejected it** — the
sentence still literally denied that a `/solspire/enterprise` route exists. The guard caught its
own author's insufficient repair, which is the property the control exists to have.

## 4. The guard, in the file a gate already executes

Extended `tests/test_console_posture_currency.py` — not a new test file, not a new workflow. The
gate `operator-console-posture.yml` already selects `web/arkadia_console/**`, `tests/**` and
`api/**`, so both the data files and the guard are selected by the same trigger with **no workflow
edit**. The wiring guard (`test_console_posture_currency_ci_wiring.py`) derives its inputs from the
guard's own AST; the extension reuses `served_routes()` and `data_files()`, so the derived input set
is unchanged and the coverage assertion still holds (verified: 50 passed across guard + wiring).

Two detectors, both mechanically decidable against the real route table:

| detector | invariant |
|---|---|
| `unresolved_route_tokens` | every `/api/...` or `/solspire/...` token in a data file resolves to a served path **or** a namespace with served paths beneath it |
| `false_absence_claims` | a sentence of the form "no `<path>` route" is false if the app serves paths under that prefix |

Neither needs a hand-maintained allowlist: after the repair, **every** route token in the four
modules resolves. A recorded list would drift; a derived one cannot.

## 5. Controls — each detector proven to bite, on the real files

Live negative control: both source repairs reverted in place, then restored byte-identically.

```console
$ sed -i 's#/solspire/enterprise/workspaces/{enterprise_id}/control-room#/solspire/workspaces/{id}/control-room#' \
    web/arkadia_console/src/operator/data/workeventNotEvidence.ts
$ sed -i 's#none of the /solspire/enterprise routes exposes#there is no /solspire/enterprise route exposing#' \
    web/arkadia_console/src/operator/data/executionNotWorkEvent.ts
$ pytest tests/test_console_posture_currency.py -q
2 failed, 30 passed
FAILED ...::test_every_route_a_file_names_resolves[workeventNotEvidence.ts]
FAILED ...::test_no_file_denies_a_route_family_the_app_serves[executionNotWorkEvent.ts]

$ cp back; sha256sum -c orig.sha
web/arkadia_console/src/operator/data/workeventNotEvidence.ts: OK
web/arkadia_console/src/operator/data/executionNotWorkEvent.ts: OK
$ pytest tests/test_console_posture_currency.py -q
32 passed in 1.33s
```

Exactly one node reddens per reverted repair — the detectors are specific, not blanket. The
controls also carry the *positive* polarity, so the detectors are not merely permissive: a served
namespace mention (`no /solspire/enterprise route exposes the graph itself`) and a genuine absence
(`no /solspire/forward-walk route is served`) are both accepted.

## 6. Regression measurement

Same environment, same command, both trees (`-q -rEf --continue-on-collection-errors`):

| tree | result | failing/error nodes | ids sha256 |
|---|---|---|---|
| `main` `bb19aabd` | 19 failed, 4250 passed, 22 skipped, 1 error | **20** | `d6101722…` |
| branch | 19 failed, 4262 passed, 22 skipped, 1 error | **20** | `d6101722…` |

`comm -3 main_nodes branch_nodes` → empty. Zero regression, attributed by node identity rather than
by count.

The `+12 passed` is exactly the guard's new nodes, measured with `--collect-only`:
`tests/test_console_posture_currency.py` collects **32** nodes (was 20) = 8 parametrized nodes
(2 invariants × 4 data files) + 4 controls.

Other gates:

```console
$ git diff --name-only | python scripts/cp10_mutation_boundary_policy.py --judge
Mutation boundary PASS (M02A legitimate-surface + constitutional denylist)     exit 0
$ pytest tests/architecture -q
11 passed
```

### 6.1 CI — runtime-proven, not source-asserted

Head `35a2d8be58bfea21b0328bc142e7be8d3d25bce5`, `commits/<sha>/check-runs`:
**16 of 16** `completed/success`, including `posture-currency` — the gate that executes this guard
— and `validate` (`SG-02-FE.2-V`, which carries the CP10 mutation-boundary judge). So the extended
guard ran in CI and passed there, rather than only in this sandbox.

The trigger is the one that matters: `operator-console-posture.yml` is path-filtered, and this PR
touches `web/arkadia_console/**` and `tests/**`, both of which it selects. No workflow edit was
needed to make the guard execute on the change it judges.

## 7. Limitations

- Source-level and route-table-level only. No browser rendering was observed for the affected
  panels, and no deployment is claimed. Production `source_revision` == `bb19aabd` with
  `revision_conflict: false` at the time of measurement, which is source↔runtime *consistency*,
  not acceptance.
- The lane ownership map does not assign `web/arkadia_console/src/operator/**` or
  `tests/test_console_posture_currency.py` to a lane, so this PR lands in
  `unassigned_open_prs`. That field is derived and printed but judged nowhere, so nothing reddens;
  assigning the operator surface to a lane is a lane-currency change that would need the snapshot
  re-derived in the same commit, and is left as a separate bounded workstream rather than folded in
  here.
- The detectors judge route *tokens*, not semantic truth. A module could still make a false
  non-route claim; this closes the route-claim class only.

## 8. Next-action block

**Current state.** `main` = `bb19aabda34d59594615b0279a45e9cbd3d8204d`; production
`source_revision` identical, `revision_conflict: false`. 28 open drafts, all `base: main`, 0
obsolete. `main`'s own check-runs on `bb19aabd` are green for every gate that ran (`boot-syntax`,
`console-contract`, `posture-currency`, `engineering-scheduler`, `test`, `Full-history secret
scan`).

**Evidence.** Sections 1–6; every command is reproducible as written.

**Blockers.** (a) Merge execution is human-only under GOV-03; 28 drafts plus this one await human
review. (b) `beta-*` / `native-arkadia-golden-workflow` are governed by an external provider.
(c) CE-01 (`weaver.autonomy` module-vs-package collision) and FINDING F-01 are reserved to the
sovereign.

**Authorized next action.** A human reviews the queue for merge. On a later cycle an agent may
re-run the open-PR composition matrix as the queue moves, verify a specific PR against the
then-current `main`, or implement another newly measured, non-reserved defect.

**Forbidden.** Merging; pushing to `main`; force-pushing; deploying; bypassing protection or
required checks; weakening a guard to manufacture green; repairing CE-01 or F-01 without a
sovereign decision; opening a PR whose only product is activity.

**Completion condition.** This cycle is complete when this evidence and the repair are reviewable on
the branch, with `main` unmodified and no merge, deployment or acceptance claimed.
