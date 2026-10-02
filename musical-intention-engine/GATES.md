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
