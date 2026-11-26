# ARK-OPS-CONTINUOUS-001 — Cycle 11: the Sonata unit-test classpath

**Cycle:** 11 · **Date:** 2026-11-24 · **Contract:** `ARK-OPS-CONTINUOUS-001` (rev. 2026-11-22)
**Branch:** `gate-hygiene/mie-android-unit-test-classpath-01` · **Base:** `main` @ `bb19aabda34d59594615b0279a45e9cbd3d8204d`
**PR:** #719 (draft)

This cycle performs no merge, no deployment and claims no acceptance. Merge execution is
human-only under GOV-03; `main` is connected to production, so a merge is a release event.

## 1. Reconstructed state

| fact | measured |
|---|---|
| canonical `main` | `bb19aabda34d59594615b0279a45e9cbd3d8204d` (2026-11-22T17:23:48Z) |
| local `HEAD` at cycle start | `bb19aabd` (identical; working tree clean) |
| production `/api/version` | `source_revision` = `bb19aabd…`, `revision_conflict: false`, `canonical_deployment: one_reconciled_deployment` |
| `/health` | `200` `{"status":"radiant","path":"/health"}` |
| `main` check-runs | `boot-syntax`, `console-contract`, `engineering-scheduler` x2, `posture-currency`, `test`, `Full-history secret scan` -> all `success`; `weaver_evolution` x5 `skipped` |
| open PRs | **41**, every one a draft, every one `base: main` |
| previous cycles | 09 (`#717`, Gemini model ladder), 10 (`#718`, Knowledge OS 5xx contract) |

The first `/api/version` probe of this cycle exceeded the 30 s soft timeout; the retry of the
same URL answered `200` / 643 B. Recorded as a Render cold-start read, not a defect - `/health`
answered on the first attempt.

Production identity is necessary evidence of source-to-runtime consistency. It is **not** proof
that the application behaves correctly and **not** deployment acceptance.

## 2. The verified gap

The Sonata / MIE Android gate has been **red since 2026-10-05**, and it fails on a unit test
that cannot run on the JVM - not on the application.

```console
$ gh run view 45365917578 --log-failed        # PR #716, 2026-11-24
com.arkadia.sonata.MieMusicalObjectTest > cloneProvenanceAndNameSurviveJson FAILED
    java.lang.RuntimeException at MieMusicalObjectTest.kt:45
> Task :app:testDebugUnitTest FAILED
8 tests completed, 1 failed
Execution failed for task ':app:testDebugUnitTest'.
```

- Same failure on the `main` push run **`37261583101`** (2026-10-05), so it is pre-existing and
  deterministic - not caused by the PR that surfaced it.
- It surfaced on a **docs-only** PR (#716) because `mie-android-build.yml` is path-filtered to
  `sonata-android/**`; a README edit is enough to trigger it.
- `MieMusicalObjectTest.kt:45` is `val json = result.toJson()`. `toJson()` builds an
  `org.json.JSONObject`, an Android **framework** class that is a throwing stub
  (`Method ... not mocked`) on the JVM unit-test classpath.
- The workflow runs `testDebugUnitTest` **before** `assembleDebug`, so the failure also
  suppresses the APK. **No Sonata debug APK has been produced by CI since 2026-10-05.**

### The invariant was known and was re-broken

| commit | date | what it did |
|---|---|---|
| `3de223c6` | 2026-10-03 | *"MIE Gate 05: keep unit test independent of Android JSON runtime"* - removed `org.json.JSONObject` from the test precisely because it cannot run on the JVM |
| `33c59362` | 2026-10-05 | *"test(mie): cover Gate 06 object controls provenance"* - reintroduced `org.json.JSONObject` in a new test, with no dependency and no guard |

The invariant existed only in a commit message, so nothing caught the regression. This is the
same class the ledger already records for this repository: **a property recorded in prose is not
a property that is executed.**

## 3. The repair

| path | change |
|---|---|
| `sonata-android/gradle/libs.versions.toml` | `json = "20240303"`; `org-json = { group = "org.json", name = "json", ... }` |
| `sonata-android/app/build.gradle.kts` | `testImplementation(libs.org.json)` |
| `tests/test_android_unit_test_classpath.py` | **new** guard, 7 nodes |
| `.github/workflows/mie-android-build.yml` | executes the guard; selects it in both `paths` filters |

The test keeps its genuine JSON assertion (asserting on the data class instead would not test
the serialization the test exists for). The guard binds the class so a future test cannot
silently reintroduce it.

### The guard is derived, not restated

- **Domain** - `git ls-files -z -- '*.kt'` filtered to paths containing `/src/test/`, so a new
  Android module or test file joins the domain without an edit.
- **Satisfier** - resolved from the module's own Gradle files: a literal coordinate
  (`arkadia-webview-poc` declares `testImplementation("junit:junit:4.13.2")`) or a version-catalog
  accessor resolved through the nearest `gradle/libs.versions.toml`.
- **Detector reads references, not imports.** The failing line calls `org.json.JSONObject`
  fully qualified and carries **no** `import org.json`, so an import-only scan is silent on the
  exact defect the guard exists for. That is why `grep -rn "^import org.json" src/test` finds
  nothing while the defect is real.
- `android.*` has no JVM substitute, so a reference to it is *reported*, never satisfied.

## 4. Verification

| command | result |
|---|---|
| `python -m pytest tests/test_android_unit_test_classpath.py -q` | **7 passed** |
| live negative control - delete `testImplementation(libs.org.json)` from the real build file | **2 failed, 5 passed**; the two nodes are `test_no_unit_test_references_a_framework_class_it_cannot_run` and `test_the_json_assertion_is_backed_by_a_real_implementation`. File restored byte-identically -> **7 passed** |
| gate-integrity bundle (`ci_gate_trigger_coverage`, `m02a_ci_gate_integrity`, `workflow_injection_boundary`, `gate_filter_selection`) | **279 passed** |
| `python -m pytest tests/architecture -q` | **11 passed** |
| `git diff --cached --name-only \| python scripts/cp10_mutation_boundary_policy.py --judge` | `Mutation boundary PASS`, exit `0` |
| full suite, same environment, both trees (`-q -rEf --continue-on-collection-errors`) | `main`: **145 failed, 2715 passed, 23 skipped, 144 errors**; branch: **145 failed, 2725 passed, 23 skipped, 144 errors** |
| sorted failing/error node sets | **191** nodes each; ids sha256 `2dc8ff61d3bf9e03cdd58624b479b29db0c80899d799261638b5d583a283e71c` on **both**; zero nodes only-on-branch, zero only-on-main |
| `--collect-only` | main **2928**, branch **2938** (+10) |

The absolute counts are this sandbox's dependency set, not CI's, and are not comparable to the
19F/1E recorded in cycles 01-05. The environment-independent claim is the node-set identity, and
it holds. The `+10` decomposes exactly: **7** new guard nodes, plus **3** the generic
`test_ci_gate_trigger_coverage.py` gains because `mie-android-build.yml` now *runs pytest* and
therefore becomes a subject of its three pytest-workflow invariants
(`test_push_and_pull_request_filters_are_identical`, `test_pr_pytest_workflow_is_selected_by_its_own_file`,
`test_architecture_fitness_is_selected_by_the_surfaces_it_judges`) - all three pass. Measured by
diffing `--collect-only` node ids per file, not inferred from the count delta.


### The decisive measurement: the Android job, on the environment that failed

Run **`45391499341`** on head `921a941d` - `event=pull_request`, `conclusion=success`:

| step | conclusion | evidence in the log |
|---|---|---|
| `Unit-test classpath guard` | success | `7 passed in 0.08s` |
| `Unit tests` (`./gradlew testDebugUnitTest`) | success | `BUILD SUCCESSFUL in 1m 49s` (was `8 tests completed, 1 failed`) |
| `Build debug APK` (`./gradlew assembleDebug`) | success | `BUILD SUCCESSFUL in 44s` |
| `Upload debug APK` | success | artifact `mie-mvp-01-debug-ab2cdd95...`, **5 518 524 B** |

All **13** check-runs on `921a941d` are `completed/success`, including `Full-history secret scan`,
`console-contract`, `test`, `trigger-coverage` and `verdict-step-integrity`.

This is a behavioural result, not a source assertion: the workflow that failed on `main` and on
#716 now passes, and produces the artifact it had been suppressing for seven weeks. It reproduced
on the docs-only head `70a1e175` as well (`Build MIE / Sonata debug APK` = `success`).

### The two non-passing checks on the docs head are external, and proven not attributable

On head `70a1e175`, `beta-beta-01-english` and `bundle-beta-evidence` are `failure`. They are the
same workflow (`n-atlas-external-beta.yml`), and the second is a downstream verdict on the first
(`statuses: {'beta-01-english.json': 'FAILED', 'beta-02-hausa.json': 'PASS'}`).

| evidence | reading |
|---|---|
| run `45391499277` @ `921a941d` (this branch, 12:13Z) | `success` |
| run `45393383348` @ `70a1e175` (this branch, 12:25Z) | `failure`; the re-run at the same head also failed |
| same run, sibling prompt `beta-02-hausa` | `PASS` — one prompt passed while the other failed, in one job |
| run `45393383348` evidence file | `"errors": []` — the request completed; the verdict is a model-output judgement |
| `gate-hygiene/knowledge-5xx-error-contract-01` (#718), same day | `failure` 11:26, `failure` 11:32, `success` 11:35 — three conclusions on one unchanged tree |
| `gate-hygiene/root-doc-module-map-currency-01` (#715), same day | `success` 07:16, `success` 07:23, `failure` 08:15, `failure` 08:20 |
| final head `d638720e`: `beta-*` and `bundle-beta-evidence` | all **success** (the 12:25Z failure did not persist) |
| final head `d638720e`: `native-arkadia-golden-workflow` | `failure`, run `45394410722`: `ModelUnavailable: N-ATLaS Gradio runtime error: provider emitted error event with null/empty data (event_id=98a5d157…, raw_data='null', events=['error'])` — the same job was `success` at `921a941d` on this PR at 12:13Z |

The head that failed (`70a1e175`) changes exactly one file: this evidence document. It cannot
alter an external N-ATLAS inference. Recorded as external-provider flakiness, **not** as a defect
in this change and **not** as a pass.


## 5. Limitations

- The repair is a **test-classpath** declaration. It changes no application behaviour, no route,
  and no deployment configuration. `api/main.py` is untouched.
- The guard is structural; it does not execute Gradle. `testDebugUnitTest` in the workflow
  remains the behavioural oracle, and it is path-filtered to `sonata-android/**`.
- An unresolvable catalog accessor (a bundle or a platform) is skipped rather than guessed, so a
  future test dependency hidden inside a bundle would not be resolved by this guard.
- A green Android job proves the Sonata module builds an APK. It does not prove the app runs,
  and it is not deployment acceptance.
- `sonata-android/app/src/main/kotlin/com/arkadia/sonata/ArkadiaRepository.kt:125` emits a
  compiler warning (`inferred type is Nothing? but String was expected` on
  `optString("note_id", null)`). It is a warning, it is outside this cycle's bounded objective,
  and it is recorded here rather than repaired.

## 6. Recorded, not repaired (unchanged from cycles 03-08)

- `scripts/prism_coherence_check.py` exits 1 with findings and is executed by no gate; its scope
  decision (which READMEs count as documented surfaces) is sovereign.
- CE-01 `weaver.autonomy` module-vs-package collision; FINDING F-01 persistence boundary - both
  sovereign-reserved.
- `arkadia-console-android/app/build.gradle.kts` still defaults `ORACLE_BASE_URL` to the retired
  host; a second Render service answers on that host at the same revision (ADR-016 drift to
  record, not adopt).

## 7. Next authorized action

Human review of the queue. #719 is a draft with 13/13 checks green; it is **not** merge-ready by
agent action, and an agent marking it ready would be prohibited.

No agent merge, no push to `main`, no deployment, no acceptance.
