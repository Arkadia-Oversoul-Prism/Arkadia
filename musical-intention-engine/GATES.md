# MIE · MVP-01 Gates

| Gate | Boundary | Current status | Required evidence |
|---|---|---|---|
| 00 | Reconnaissance | COMPLETE | verified build state |
| 01 | Capture | CI VERIFIED / DEVICE PENDING | reliable Android capture/replay |
| 02 | Interpretation | CI VERIFIED / DEVICE PENDING | type + confidence + evidence |
| 03 | Materialization | CI VERIFIED / DEVICE PENDING | inspectable MusicalObject |
| 04 | Transformation | NOT STARTED | one meaningful reversible change |
| 05 | Change loop | NOT STARTED | repeatable compare/keep/revise |
| 06 | Continuity | NOT STARTED | ancestry back to original |
| 07 | Mobile instrument | NOT STARTED | real-device usability |
| 08 | Measurement | NOT STARTED | TTMI/TTCS/ITS/IP/RC/DWM protocol |
| 09 | Experiment run | NOT STARTED | hum/tap/speak/repeat evidence |
| 10 | Integrity review | NOT STARTED | product-hypothesis review |

A gate is not passed because code exists. It requires implementation, test, evidence, and observation.

## Reconciliation · 2026-10-02 (measured at `886759f`)

The "CI VERIFIED" status on gates 01–03 is **superseded for the current tree**. The
successful run it rests on (`37007483734`, `a336ec30`) predates `bd98696`, the commit that
added `MieMusicalInterpreterTest.kt`; the Sonata app module declares no test dependency, so
the current tree fails `testDebugUnitTest` to compile and the MIE workflow is red on `main`.

Status while the repair PR is open:

| Gate | Boundary | Current status | Note |
|---|---|---|---|
| 01 | Capture | DEVICE PENDING | APK build unproven on the current tree |
| 02 | Interpretation | DEVICE PENDING | unit test does not compile on `main` |
| 03 | Materialization | DEVICE PENDING | as above |

Gates 04–10 are unchanged. CI VERIFIED may be re-asserted only after a workflow run on the
post-repair tree succeeds; the device boundary remains the binding one regardless.

## Gate 02 correction · 2026-10-02 (PR #214, run `37036927785`)

Gate 02's "CI VERIFIED" was never sound: at the revision it rested on, the interpretation unit
test did not compile, so no interpretation assertion had ever executed. Once the test ran it
failed, and measurement showed `MieMusicalInterpreter` reported a subharmonic for every tone
above ~150 Hz (440 Hz → 146.8 Hz). Gate 02 was therefore **not** verified at any point.

| Gate | Boundary | Status after repair | Note |
|---|---|---|---|
| 02 | Interpretation | CI VERIFIED / DEVICE PENDING | subharmonic defect repaired; 3 tests green in run `37038160736` |

The repair and its regression tests are on PR #214. Gate 02 may be marked CI VERIFIED only
after that run succeeds; the device boundary remains binding regardless.

### CI VERIFIED · measured at `66420ef`

Run `37038160736` (`pull_request`, `2026-10-02T17:03:49Z`, `success`) on head `66420ef`:

```
> Task :app:testDebugUnitTest
BUILD SUCCESSFUL in 1m 29s
```

All three interpretation tests pass — `sustained440HzToneProducesMelodyCandidate`,
`lowerTonesAreNotReportedAsSubharmonics`, `broadbandNoiseIsNotAMelodyCandidate`. This is a
narrower claim than the superseded gate 01–03 row above: it verifies **interpretation** on a
tree where the interpretation test actually executes. Gates 01 and 03 ride on the same run's
APK build, which also succeeded, but neither has an independent assertion of its own; they
remain DEVICE PENDING.
