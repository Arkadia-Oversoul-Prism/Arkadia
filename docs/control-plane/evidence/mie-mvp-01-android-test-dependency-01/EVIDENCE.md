# MIE · MVP-01 · Android test-dependency repair 01

**Status:** IMPLEMENTED — sovereign review required (CI proof pends the PR's own workflow run)
**Date:** 2026-10-02
**Base main:** `886759f2de6a1edd062c878ebdf448d0ed4e0330`
**Branch:** `mie/mvp-01-android-test-dependency-01`
**Workstream:** issue #209 (MIE MVP-01) — unblock the Gate 01–03 CI boundary
**Gate:** MIE MVP-GATE-01/02/03 (evidence integrity) · gate-hygiene class

## 1. Objective

Restore compilation of the Sonata/MIE local JVM unit test so the **Build MIE Android MVP**
workflow (`mie-android-build.yml`) can pass on the current tree, and reconcile the
`BUILD-STATE.md` / `GATES.md` "CI VERIFIED" claims with measured evidence.

## 2. Evidence-backed defect

`mie-android-build.yml` runs `./gradlew testDebugUnitTest` before `assembleDebug`, so a
test-compilation failure fails the whole job and no APK artifact is produced.

The tree contains one test source:

```
sonata-android/app/src/test/java/com/arkadia/sonata/MieMusicalInterpreterTest.kt
```

It imports `org.junit.Assert.*` and `org.junit.Test`. The app module declares no test
dependency of any kind, and the version catalog has no JUnit entry:

```
$ grep -rn "junit" sonata-android --include=*.kts --include=*.toml --include=*.gradle
(no output)
$ grep -n "testImplementation" sonata-android/app/build.gradle.kts
(no output)
```

`git log --all -- sonata-android/gradle/libs.versions.toml` shows JUnit was never present in
any revision, so this is a missing declaration, not a regression introduced by the test.

### 2.1 The published CI success measured a different tree

`musical-intention-engine/BUILD-STATE.md` cited run `37007483734` (commit `a336ec30`,
`2026-10-02T12:34:23Z`) as SUCCESS and concluded "Kotlin unit tests: SUCCESS". Measured:

```
$ gh run view 37007483734 --json headSha,conclusion
sha=a336ec30c307fdfb319d211743214b9a24a54bd2  completed/success
$ git log -1 --format='%h %ci %s' bd98696
bd98696 2026-10-02 16:30:30 +0100  test(mie): add deterministic musical interpretation regression
```

The unit test was added four hours **after** the run that reported unit-test success. The
run is real; the conclusion drawn from it is not transferable to the current tree. The
**Build MIE Android MVP** workflow is FAILURE on `main` at `886759f`.

## 3. Change

Minimal, additive — no runtime or product code is touched:

| File | Change |
|---|---|
| `sonata-android/gradle/libs.versions.toml` | `junit = "4.13.2"` version; `junit = { group = "junit", name = "junit", version.ref = "junit" }` library |
| `sonata-android/app/build.gradle.kts` | `testImplementation(libs.junit)` |
| `musical-intention-engine/BUILD-STATE.md` | appended reconciliation section (the prior CI section is preserved, not rewritten) |
| `musical-intention-engine/GATES.md` | appended reconciliation section superseding gates 01–03 "CI VERIFIED" for the current tree |

`junit:junit:4.13.2` is the standard Android JVM unit-test dependency; it resolves from
`mavenCentral()`, already configured in `settings.gradle.kts`.

## 4. Verification

Run in this sandbox (node 24, Python 3.13):

| Command | Result |
|---|---|
| `python -c "import tomllib; ..."` over the edited catalog | PASS — `junit 4.13.2` parses |
| `python scripts/cp10_mutation_boundary_policy.py --judge` on the diff | PASS — both paths admitted |
| `python -m py_compile api/main.py` | PASS (boot code untouched; 2582 lines, budget 2600) |

**Not run — environment-blocked.** `./gradlew testDebugUnitTest` and `assembleDebug` cannot
run in this sandbox: no JDK (`java: command not found`) and no Android SDK
(`ANDROID_HOME` unset). The authoritative proof is the path-filtered
`mie-android-build.yml` run that this PR triggers, since it touches `sonata-android/**`.
That result is the completion condition for this pass and is reported in the PR thread.

## 5. Regression boundary

- `sonata-android/**` is unchanged apart from the two additive dependency lines; the MIE
  boundary and all product source are untouched.
- No Python test surface, no architecture layer, no `api/main.py`, and no constitutional
  file is modified.
- The two documentation edits are **appended** sections; no existing line was rewritten, so
  any external reference to the prior wording still resolves.

## 6. Authority boundary

No merge, no push to `main`, no force-push. The APK/CI boundary and the real-device
boundary (mic permission flow, capture reliability, playback, pitch accuracy, TTMI/TTCS/ITS)
remain open and are **not** claimed here. Merge authority rests with the sovereign.
