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

---

## 7. Follow-on defect: the dependency repair unmasked a pitch-detection bug

**Measured on this PR's own workflow run `37036927785` (`pull_request`, 2026-10-02T16:52:52Z).**

The dependency change did what it was scoped to do — the unit test compiled and executed for
the first time — and then **failed**, exposing a real product defect:

```
MieMusicalInterpreterTest > sustained440HzToneProducesMelodyCandidate FAILED
    java.lang.AssertionError at MieMusicalInterpreterTest.kt:22
1 test completed, 1 failed
> Task :app:testDebugUnitTest FAILED
Caused by: ...MarkedVerificationException: There were failing tests.
```

`testDebugUnitTest` is red for a *product* reason now, not a build-configuration reason. The
missing dependency had been masking a failing assertion.

### 7.1 Root cause (measured, not inferred)

`MieMusicalInterpreter.estimatePitch` kept the lag with the highest correlation, scanning from
the smallest lag upward and replacing the incumbent on `corr > bestCorr`. Because a periodic
signal correlates strongly at **every multiple of its period**, the global maximum is often a
subharmonic. Replicating the algorithm exactly (Python, same frame/lag arithmetic, same
int16 wrap and `/32768f` normalisation) reproduces the failure and shows it is systematic:

| Synthetic input | Reported | True |
|---|---|---|
| 440 Hz, 1500 ms | 146.8 Hz (`lag = 109` ≈ 3 periods) | 440 Hz |
| 220 Hz, 1500 ms | 73.4 Hz | 220 Hz |
| 880 Hz, 1500 ms | 80.0 Hz | 880 Hz |
| 110 Hz, 1500 ms | 110.3 Hz | 110 Hz |

110 Hz passed only because its first peak (lag 145) is the sole in-range peak; above that the
error is near-universal. This is the classic autocorrelation octave/subharmonic error.

### 7.2 Repair

`estimatePitch` now computes the correlation curve once, finds the global peak, and returns the
**first local maximum within `PEAK_RATIO = 0.85` of that peak** — the smallest lag that nearly
matches — with parabolic interpolation on the three samples around the peak for sub-sample
resolution. `sqrt` import and the 0.35 voicing floor are unchanged.

Measured before/after with the same replication:

| Input | Before | After |
|---|---|---|
| 440 Hz | 146.8 Hz | 440.0 Hz |
| 220 Hz | 73.4 Hz | 220.0 Hz |
| 880 Hz | 80.0 Hz | 888.9 Hz |
| 110 Hz | 110.3 Hz | 110.0 Hz |
| 440 Hz + harmonics (1, .5, .33) | 146.8 Hz | 440.0 Hz |
| 220 Hz + harmonics (1, .7, .5, .3) | 73.4 Hz | 220.0 Hz |
| 440 Hz + uniform noise 0.1 | 146.8 Hz | 440.1 Hz |
| white noise | (no pitch) | no pitch → `rhythm_or_percussive_candidate` |
| silence | (no pitch) | no pitch → `ambiguous` |

The 0.35 voicing floor still rejects noise: on white noise the maximum correlation is well
below it, so no pitch is emitted and the negative control holds.

### 7.3 Regression tests added

| Test | Purpose |
|---|---|
| `lowerTonesAreNotReportedAsSubharmonics` | 110/220/440/880 Hz within ±3% — fails on the old code at all but 110 Hz |
| `broadbandNoiseIsNotAMelodyCandidate` | negative control: noise must not classify as melody |

### 7.4 Design limits, recorded rather than fixed

`maxLag = SAMPLE_RATE / 55` = 290 samples caps detection at ≈55 Hz, and `minLag` bounds it at
≈1000 Hz. Both are pre-existing constants and are unchanged by this repair; the ~890 Hz result
for an 880 Hz input reflects one-sample lag quantisation that the parabolic interpolation only
partly recovers. Widening either limit is a separate, evidence-driven decision.

### 7.5 Status

Gate 02 ("Interpretation") was marked CI VERIFIED on a revision where the interpretation test
could not compile, so no assertion had ever run. It is corrected to **CI PENDING / DEVICE
PENDING** in `GATES.md`. A green `testDebugUnitTest` on the post-repair tree is the completion
condition for the CI half; the device half stays with the sovereign.

### 7.6 Completion condition met

Run `37038160736` (`pull_request`, `2026-10-02T17:03:49Z`, `success`) on head
`66420ef0a63e595ab30a72297e489bc4611ad066`:

```
> Task :app:testDebugUnitTest
BUILD SUCCESSFUL in 1m 29s      (assembleDebug: BUILD SUCCESSFUL in 26s)
```

Status: **VERIFIED for the CI half.** `testDebugUnitTest` and `assembleDebug` both pass and
the debug APK uploads. All three interpretation tests execute and pass. Gate 02 is re-marked
CI VERIFIED / DEVICE PENDING.

What this does **not** prove, stated explicitly: nothing about a physical device. No mic
capture, no playback, no real-world pitch accuracy has been observed. The device boundary is
the binding one and rests with the sovereign.
