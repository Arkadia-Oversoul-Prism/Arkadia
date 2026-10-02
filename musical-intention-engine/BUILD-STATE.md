# MIE · Build State

**Pass:** MVP-01  
**Branch:** feature/mie-mvp-01  
**Repository:** Arkadia-Oversoul-Prism/Arkadia

## Gate 00 reconciliation · 2026-10-02

The living Prism was inspected before implementation.

### What exists

- `sonata-android/` is the existing Android application substrate.
- It is a native Kotlin Android 10+ app using Gradle/Kotlin/Material components.
- Existing Sonata functionality is voice/TTS + Knowledge OS.
- The repository has no source-backed implementation of the observed Gate 01 MIE capture screen in `main`.
- The observed hold-to-capture prototype therefore cannot be safely "reused" by path reference. Rebuilding its known behavior in the native Android substrate is the smallest reconciled implementation rather than silently assuming missing code exists.
- The nested `sonata-android/.github/workflows/build-apk.yml` is not a root GitHub Actions workflow. A root MIE build workflow is therefore required for automated APK verification.

### Reconciled placement

```
Arkadia Prism
  └── sonata-android
       ├── existing Sonata / Knowledge OS
       └── MIE instrument surface
            ├── capture
            ├── interpretation
            └── musical object
```

MIE remains documented and experimentally bounded under `musical-intention-engine/`. The native Android projection lives in the existing Android substrate rather than creating a second APK project.

### Implemented causal bridge

```
HUMAN
  ↓
HOLD TO CAPTURE
  ↓
16 kHz mono PCM
  ↓
WAV SOURCE
  ↓
deterministic pitch / energy / zero-crossing analysis
  ↓
MUSICAL OBJECT JSON
  ↓
PLAY ORIGINAL
```

The implementation currently preserves source audio and records interpretation confidence and provenance. It deliberately does not yet claim full melody transcription or transformation.

### Current gate

**MVP-GATE-02: CI VERIFIED / DEVICE VERIFICATION REQUIRED**

### Commits

- `41197008` — MIE MVP-01 documentation/directive
- `44702f3` — Android capture → musical object bridge
- `a336ec30` — compile reconciliation / TTS source normalization

### Not yet verified

- real-device microphone permission flow;
- real-device capture reliability;
- real-device playback;
- pitch accuracy on actual humming;
- real-device APK installation and execution;
- user-measured TTMI / TTCS / ITS;
- transformation.

### Hard truth

The original screenshot proves that the earlier prototype captured audio on a phone. It does **not** prove that the source implementation is present in the current Prism branch. That implementation was not found, so this pass records the absence instead of inventing provenance.

## Build verification note

The first CI build exposed repository-level Kotlin/manifest drift in the existing Sonata surface in addition to the new MIE files. The current pass is repairing those concrete compile blockers rather than weakening the test. The MIE boundary remains unchanged.

## Next causal step

Build and install the APK, then run EXP-002 on a real Android phone:

1. hum one sustained note;
2. capture for 2–5 seconds;
3. release;
4. verify the object reports a pitch candidate;
5. play the original;
6. inspect the generated object JSON;
7. record whether the interpretation corresponds to what was actually intended.

Only after this evidence should the transformation boundary advance.


## CI evidence · 2026-10-02

Workflow: **Build MIE Android MVP**  
Run: `37007483734`  
Commit: `a336ec30`  
Result: **SUCCESS**

Verified in CI:
- Kotlin unit tests: SUCCESS
- Sonata/MIE debug APK build: SUCCESS
- Debug APK artifact upload: SUCCESS

Artifact:
`mie-mvp-01-debug-1122a6b7a381e0e790167f9e7b70a09c4d355e04`

This proves build integrity. It does not prove physical-device behavior.

## Device evidence status

**PENDING HUMAN DEVICE RUN**

The APK is ready for installation. The next observation must come from the target Android phone, not from CI.

## CI evidence reconciliation · 2026-10-02 (measured at `886759f`)

The run cited above (`37007483734`, commit `a336ec30`, `2026-10-02T12:34:23Z`) is a real
SUCCESS, but its scope is narrower than the section implies. Measured, not inferred:

- `MieMusicalInterpreterTest.kt` did **not exist** at `a336ec30`. It was added later by
  `bd98696` (`2026-10-02T16:30:30Z`) — four hours after that run. "Kotlin unit tests:
  SUCCESS" therefore describes a tree in which the unit test was absent, and does not
  describe the current tree.
- `sonata-android/app/build.gradle.kts` declared **no** `testImplementation` dependency and
  `sonata-android/gradle/libs.versions.toml` had **no** JUnit entry — in all of history, not
  merely at the tip. `MieMusicalInterpreterTest.kt` imports `org.junit.Assert.*` and
  `org.junit.Test`, so `./gradlew testDebugUnitTest` cannot compile on the current tree.
- Consequence: the **Build MIE Android MVP** workflow is **FAILURE** on current `main`
  (`886759f`). The Gate 01/02/03 "CI VERIFIED" wording above is superseded for the current
  tree; it holds only for the pre-`bd98696` revision that the run actually measured.

The APK-build step itself was green at `a336ec30`; the red is the test-compile step, which
predates nothing — it is a missing declaration, not a regression introduced by MIE work.

Repair: PR on branch `mie/mvp-01-android-test-dependency-01` adds `junit = "4.13.2"` to the
version catalog and `testImplementation(libs.junit)` to the app module. The APK artifact for
the current tree remains unproven until that PR is merged and a new workflow run completes —
this document must not claim APK readiness for `886759f` on the strength of `37007483734`.

## Pitch-detection defect · 2026-10-02 (measured on PR #214, run `37036927785`)

Declaring the JUnit dependency let `MieMusicalInterpreterTest.kt` **compile and run** for the
first time. It then **failed**, exposing a real product defect the compile error had masked:

```
MieMusicalInterpreterTest > sustained440HzToneProducesMelodyCandidate FAILED
    java.lang.AssertionError at MieMusicalInterpreterTest.kt:22
1 test completed, 1 failed
> Task :app:testDebugUnitTest FAILED
```

Line 22 asserts `result.pitchHz in 430f..450f`. Measured behaviour of
`MieMusicalInterpreter.estimatePitch` on synthetic tones (algorithm replicated exactly in
Python; `lag` in samples at 16 kHz):

| Input | Reported | True | Cause |
|---|---|---|---|
| 440 Hz | 146.8 Hz | 440 Hz | `bestLag = 109` ≈ 3 periods |
| 220 Hz | 73.4 Hz | 220 Hz | ≈ 3 periods |
| 880 Hz | 80.0 Hz | 880 Hz | ≈ 11 periods |
| 110 Hz | 110.3 Hz | 110 Hz | correct (lag 145 is the only peak in range) |

The search kept the **largest** lag whose correlation exceeded the running best. A periodic
signal correlates strongly at *every* multiple of its period, so the global maximum is
frequently a subharmonic, not the fundamental. This is the classic autocorrelation
octave/subharmonic error, not a fixture artefact.

Repair: `estimatePitch` now takes the **first local maximum within `PEAK_RATIO` (0.85) of the
global peak** — the smallest lag that nearly matches — with parabolic sub-sample interpolation
for resolution finer than one sample. Measured after the change (same replication):

| Input | Before | After |
|---|---|---|
| 440 Hz | 146.8 Hz | 440.0 Hz |
| 220 Hz | 73.4 Hz | 220.0 Hz |
| 880 Hz | 80.0 Hz | 888.9 Hz |
| 110 Hz | 110.3 Hz | 110.0 Hz |
| 440 Hz + harmonics | 146.8 Hz | 440.0 Hz |
| 440 Hz + noise | 146.8 Hz | 440.1 Hz |
| white noise | — | no pitch (rhythm candidate) |
| silence | — | no pitch (ambiguous) |

Boundary of the design: `maxLag = SAMPLE_RATE / 55` = 290 samples caps the detectable range at
~55 Hz; 1320 Hz sits above the `SAMPLE_RATE / 1000` ceiling for a *different* reason and was
never in range. Both limits are pre-existing and unchanged.

Two regression tests were added: `lowerTonesAreNotReportedAsSubharmonics` (110/220/440/880 Hz
within ±3%) and `broadbandNoiseIsNotAMelodyCandidate` (negative control).
