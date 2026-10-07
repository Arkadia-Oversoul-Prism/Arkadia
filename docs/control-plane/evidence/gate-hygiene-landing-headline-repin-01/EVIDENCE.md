# gate-hygiene · landing-headline re-pin 01

Bounded objective: restore the full-suite test-debt fingerprint on `main` to its
recorded canonical value by re-pinning one stale source-level literal.

Authority: test + evidence only. No merge, no authorization, no identity change,
no authority-model change, no new mutation or authorization path, no production
infrastructure.

## 1. Reconstruction (measured, not prose)

| fact | value |
|---|---|
| BASE_MAIN at pass start | `74e8ea53a30213db8783e6733679d2f11903de0b` |
| `origin/main` at pass start | `1a9d5ce5646534bb24727bba81711accca885606` |
| `origin/main` after the GATE-07 batch merged | **`af3a3541d9fedf8c2d38bb7a0aac56856a879523`** |
| merge #334 | `75d18b2deadd3a582196d2f0b23ab023e670b96a` (parents `1a9d5ce`, `9ce560b`) |
| merge #346 | `af3a3541d9fedf8c2d38bb7a0aac56856a879523` (parents `75d18b2`, `67aec9d`) |
| open PRs | **#337**, **#338** only — both AEAS, both `CONFLICTING/DIRTY`, separate workstream |
| `tests/architecture` on the repair branch | **11 passed** |
| `api/main.py` | 2434 lines (budget 2600) — untouched by this change |

The AEAS PRs (#337 `aeas-01-native-operator-surface`, #338 `aeas-browser-runner-01`)
are *not* the active bounded workstream for this pass: both are `CONFLICTING` against
`main`, both are large (+132/-3 and +1745/-3), and their own bodies scope them as the
staging boundary for Render browser verification while Vercel quota is unavailable —
an external/provider boundary, not repository work. This pass therefore does not touch
them.

### Continuation pass re-verification (2026-10-07, later UTC)

A continuation pass re-derived every link above from live evidence rather than prose,
and reproduced all of them. `origin/main` is still `af3a354`; this branch's base is
`af3a354` (not 9 commits stale); `api/main.py` is 2434/2600 and `py_compile` is clean;
the branch head is `5f22022`.

The previous pass's `BASE_MAIN` column (`74e8ea53`) is the **automation's fresh clone**
taken at 17:05 UTC, *before* the 17:34–17:52 merges landed — it is a stale clone SHA,
not this branch's base. The live base is `af3a354`, and the repair targets
(`tests/test_ais_capability_profile_onboarding.py` and the two evidence files) are
untouched by those merges, so the repair remains valid and applicable.

Independently re-measured in this pass:

| check | result |
| --- | --- |
| unpatched `af3a354` full suite | 10F / 1760P / 21S / 1E — **11** nodes, `f3e73647…` |
| repaired branch full suite | 9F / 1761P / 21S / 1E — **10** nodes, `9a54f5b4…` |
| node-set delta | exactly **1 removed** (the repaired node), **0 introduced** |
| `tests/architecture` | **11 passed** |
| negative control (unpatched) | `1 failed, 3 passed` on the target file |
| CP10 boundary judge on changed paths | **PASS** (exit 0) |
| `main`/branch merge diff | evidence + test only, no boot code |

The repaired node set equals `tests/fixtures/baseline_node_set.txt` byte-for-byte, and
the repaired fingerprint pair is exactly the canonical pair recorded in `AGENTS.md`.

## 2. The defect

`main` @ `af3a354` carries **11** failing/error nodes, but
`tests/fixtures/baseline_node_set.txt` records **10**. The extra node is

```
tests/test_ais_capability_profile_onboarding.py::test_home_is_offer_led_and_keeps_arkadia_entry_points
```

It is a **test-side stale literal**, not a product defect. The test asserts a
landing-page headline that no longer exists in the source it reads:

```
assert "One intelligence. Four ways to work with it." in landing
```

Timeline, from `git log -S` on each file:

| commit | date | event |
|---|---|---|
| `31a0c8a` | 2026-09-06 | introduced the headline `One intelligence. Four ways to work with it.` |
| `479e8de` | 2026-09-29 | SH-02e **re-pinned the test onto that headline** (`Learn. Build. Prove. Launch.` → this literal) |
| `2b87e8e` | 2026-10-04 | **#276 canonical Oversoul identity removed the headline** and replaced it with `One Prism. Many ways to work with it.` — **no test-side re-pin followed** |

So the SH-02e pin was correct when written and was invalidated four days later by a
*source* change that did not touch the test. `2b87e8e` is an ancestor of `main`
(`git merge-base --is-ancestor 2b87e8e origin/main` → true).

Verified in isolation on `af3a354` before the fix:

```
tests/test_ais_capability_profile_onboarding.py ..F.   [100%]
1 failed, 3 passed
```

and the fixture relationship is exact — the live 11-node set minus this node is
byte-identical to the recorded 10-node fixture (`diff` → identical).

## 3. The repair

One line in `tests/test_ais_capability_profile_onboarding.py`, re-pinned onto the
live headline:

```diff
-    assert "One intelligence. Four ways to work with it." in landing
+    assert "One Prism. Many ways to work with it." in landing
```

plus a comment recording the second drift. No coverage is lost: the assertion still
pins the architecture headline and the three entry-point anchors (`Spiral Grove`,
`SolSpire`, `NovaNet`) plus the `arkadia-home-landing` mount testid are unchanged.

## 4. Verification

| check | command | result |
|---|---|---|
| repaired file | `pytest tests/test_ais_capability_profile_onboarding.py -q` | **4 passed** |
| architecture fitness | `pytest tests/architecture -q` | **11 passed** |
| fingerprint guard | `pytest tests/test_baseline_fingerprint.py -q` | **24 passed** |
| CP10 mutation boundary | `scripts/cp10_mutation_boundary_policy.py --judge` on the changed path | **PASS** |
| full suite | `pytest tests/ -q -rEf --continue-on-collection-errors` | **9 failed / 1761 passed / 21 skipped / 1 error** |

### Fingerprint (the load-bearing evidence)

Derived with `scripts/baseline_fingerprint.py` — a read-only parser, not a re-run:

| tree | nodes | outcomes fingerprint | ids fingerprint |
|---|---|---|---|
| pre-fix `af3a354` (`/tmp/main354`) | 11 | `f3e73647…` | `92d344d0…` |
| **repaired** | **10** | **`9a54f5b478d1135f27ab9e54d95706f03eae1ceb5d4c1f3ae075bffc4208ab38`** | **`124bfdfd078fe878fe7c9de358ba271e977c4f7b73909b9d7d016b9ae9c1e87f`** |

The repaired pair is **exactly** the canonical pair recorded for the repository in
`AGENTS.md` ("Canonical pair at `1b7c089`: `9a54f5b4…` / `124bfdfd…`"). The node set
now equals `tests/fixtures/baseline_node_set.txt` exactly. The delta is `-1 node`
(the repaired one); **no node was introduced**.

### Negative control

The repair is only meaningful if the assertion it re-pins can fail. `2b87e8e`
removed the pinned literal while the test was live, and the node went red on `main`
for three days — that is the observed negative control: the assertion detected the
source change. It is not being weakened; it is being pointed at the current source.

### CI ground truth (recorded, not claimed as parity)

`main` @ `af3a354` is protected by only two unfiltered workflows; `git`-level
verification of the merge:

- workflow runs on `af3a354`: `_diagnose_blank_frontend` (push, **success**),
  `security-secret-scan` (push, **success**) — `total_count 2`.
- check-runs on `af3a354`: `Full-history secret scan` **success**, `browser` **success**.
- #346's own head `67aec9d` passed the full-history secret scan; its diff is
  evidence-only (`docs/control-plane/evidence/…`), and it is the *second parent* of
  the merge, so it cannot have altered the frontend source.
- `tests/architecture/**` is executed by exactly one workflow,
  `provider-routing.yml`, path-filtered to `weaver/**` / `providers/**`; a commit
  touching only test/docs does not run it. That is a repository convention, not a
  gate — the architecture suite was therefore run locally (**11 passed**).

**Merges are behaviour-preserving.** The node-set identity is the proof: the branch
tree `9ce560b` (`gate07/router-schema-vocabulary-closure`) and the merged `main`
`af3a354` produce **identical** failing/error node sets (`92d344d0…`, 11 nodes).
Neither merge introduced a failure. #334's diff
(`.github/workflows/weaver-mvp2-validation.yml`, evidence, `tests/test_router_schema_vocabulary_closure.py`)
is present on `main` (`git cat-file -e af3a354:tests/test_router_schema_vocabulary_closure.py`).

## 5. CI on the PR head — Vercel failure is a provider boundary, not this diff

`gh pr view 347` reports `mergeable=MERGEABLE/UNSTABLE`. The `UNSTABLE` is the two
Vercel commit statuses. They must be attributed, not assumed:

| status context | on `main` `af3a354` | on this PR head `7611786` | `target_url` |
|---|---|---|---|
| `Vercel – arkadia-prism` | success | **failure** | `vercel.com/arkadia-prism?upgradeToPro=build-rate-limit` |
| `Vercel – console` | failure | failure | `vercel.com/arkadia-prism?upgradeToPro=build-rate-limit` |
| `Full-history secret scan` (check-run) | success | **success** | — |

Both failures carry the **same** `?upgradeToPro=build-rate-limit` target — the Vercel
free-tier **build rate limit**, i.e. an external provider quota boundary. This is the
same boundary the two open AEAS PRs name in their own bodies ("Render browser
verification while Vercel quota is unavailable").

It is **not attributable to this diff**: the PR changes exactly three paths, all of
them under `tests/` and `docs/` (`gh pr view 347 --json files`), and contains **no**
`web/public_prism/**` build input. `sg-02-fe-2-v.yml` is path-filtered and correctly
does not run. The `arkadia-prism` flip success→failure between `af3a354` and this head
is quota exhaustion over time, not a source change — `af3a354`'s own status was
recorded while quota was still available.

The required gate for this PR — the full-history secret scan — is **success**. The
Vercel boundary is recorded as `BLOCKED` (provider), and per the standing rule a
provider `BLOCKED` is not converted into a repository defect.

## 6. Remaining uncertainty

- The **other 10 debt nodes are untouched and unattributed here** — this pass
  repairs exactly one drifted node. They are the recorded baseline and are not
  regressions of this work.
- `tests/test_autonomy.py` remains the CE-01 `weaver.autonomy` module-vs-package
  collection error, **reserved to the sovereign**. It interrupts a bare
  `pytest tests/` run (exit 2), which is why `--continue-on-collection-errors` is
  required to reach the counts above.
- The two AEAS PRs remain open, conflicting, and out of scope for this pass.
- No runtime/deployment claim is made. This is a repository-source + local-test
  claim only.

## 7. The AEAS PRs are an authority boundary, not an engineering task

The previous pass recorded both AEAS PRs (#337, #338) as `CONFLICTING/DIRTY` and left
their disposition open. Reconstruction closes that question: they must **not** be
composed into a superset, and the reason is governance, not conflict mechanics.

- `docs/control-plane/AEAS-v0.1.1.md` (on `main` `af3a354`) declares `Status: FROZEN`,
  **`Implementation: NOT AUTHORIZED`**, `Authority Ceiling: LEVEL 2 (specification
  only)`, and `Human Authorization: REQUIRED FOR ALL EXECUTION`. Its freeze declaration
  states: "No implementation is authorized by this freeze."
- The normative authorization-provenance chain (spec §1) is
  `ARCHITECT → AUTHORIZATION RECORD → ENGINEERING LAB → WORKER → EVIDENCE`, and "A task
  without such a record is not authorized and must not be dispatched."
- Both PRs are *AEAS implementations*. `#337` = "AEAS-01 native Engineering Lab operator
  surface" (`api/lab_routes.py`, `App.tsx`, `ArkadiaNavigation.tsx`,
  `EngineeringLabPage.tsx`); `#338` = "AEAS browser runner 01: isolated execution
  instrument" (`tools/aeas-browser-runner/**`, `api/lab_routes.py`, plus the same three
  frontend files). Neither body cites an architect-originated authorization record.
- The only AEAS acceptance artifact on `main` is
  `docs/control-plane/evidence/m07-aeas-freeze/ACCEPT.json`, which records
  `aeas_implementation_activated: false` and `implementation_not_authorized: true`.

Live mergeability was also re-measured (correcting the previous pass, which recorded
both as `CONFLICTING`): `#337` is `MERGEABLE/UNSTABLE` (the `UNSTABLE` is the Vercel
build-rate-limit status of §5); only `#338` is `CONFLICTING/DIRTY`. Even so, composition
is mechanically blocked — applying `#337` then `#338` on `af3a354` yields 29 conflict
regions (`lab_routes.py` 5, `EngineeringLabPage.tsx` 17, `App.tsx` 4,
`ArkadiaNavigation.tsx` 3), and the two heads diverge from merge-base `17e626c`
(Merge PR #333) with `#337` not an ancestor of `#338`.

**Classification: #337 / #338 = `BLOCKED` (authority).** Advancing them requires an
architect-originated authorization record naming the bounded AEAS task. No composition,
rebase, or conflict resolution was performed in this pass.

## 8. Next bounded task (proposed, not executed)

Attribution of the remaining 10 baseline debt nodes against the recorded fixture —
each classified STALE_ASSERTION / REAL_DEFECT / ENVIRONMENT before any repair, one
node per bounded pass. Not begun here (scope discipline).
