# ARK-OPS-CONTINUOUS-001 — cycle 28: Sonata's screen reaches the engine

**Contract:** `ARK-OPS-CONTINUOUS-001` rev `2026-11-22`
**Portfolio directive:** `PORTFOLIO-WEAVER-2026-11-26-01`
**Base:** `main` @ `8f746f9eab6df51733f6d43c8bab26af63eb6471`
**Branch:** `gate-hygiene/portfolio-state-ledger-01`, entered at
`57327734f6fbdd1d973f1df414df9a4b556a534d`
**Pulse:** 2026-11-27T08:06Z
**Authority:** `MERGE_AUTHORITY := NONE`, `DEPLOY_AUTHORITY := NONE`. No merge, no push to
`main`, no deployment, no acceptance, no draft conversion. No new pull request was opened
for the ledger; the existing PR #744 was extended.

This is a **reconciliation/implementation** record, so it takes the bare
`…-cycle-NN` path. The work itself landed in the selected repository (`sonata`), not here.

Files this record touches in Arkadia:

```
docs/control-plane/openhands/hourly-weaver/portfolio-state.json   (re-derived)
docs/control-plane/evidence/ark-ops-continuous-001-cycle-28-sonata-screen-reaches-engine-01/EVIDENCE.md  (new)
```

---

## 1. Reconstruction and selection

Live from GitHub at 2026-11-27T08:06Z, not from memory:

| Repository | Default branch | Head | Open PRs | `last_progress_at` |
|---|---|---|---|---|
| `sonata` | `feature/sonata-tts-app` | `7c4e6a64e39e` | 1 (#9) | 2026-11-27T04:17:56Z |
| `family-safety-network` | `main` | `18c729735fd4` | 6 | 2026-11-27T06:13:11Z |
| `Arkadia` | `main` | `8f746f9eab6d` | 63 | 2026-11-27T06:16:47Z |

Sonata was oldest, so the fairness rule selected it (tie-break order never reached).
The selection was re-derived, not remembered: `scripts/portfolio_state_refresh.py` is the
only writer, and its `--write` run at 08:29:06Z now records Sonata at 08:28:27Z and
selects **FSN** next.

## 2. Selected task

Sonata `docs/SONATA_KNOWN_LIMITATIONS.md` L1 item 3 — *"`EngineFactory` is not called
from the UI"* — and the ledger's own next-slice note. Measured, not assumed:

```
$ grep -rn EngineFactory app/src --include=*.kt
app/src/main/kotlin/com/arkadia/sonata/EngineFactory.kt    # the definition, and only this
```

One hit. The production engine was constructible and tested and unreachable, so no user
action could produce a stored narration. This is the class the ledger had already named:
*a correct component that nothing constructs is not a feature.*

## 3. What landed (in `sonata`, PR #10 — draft)

| File | Role |
|---|---|
| `NarrationPresenter.kt` (new, JVM) | `NarrationOutcome` → the line the user reads, plus a `saved` flag |
| `NarrationPresenterTest.kt` (new, JVM) | 4 tests, including "a Success that names no file is not saved" |
| `MainActivity.kt` | `saveNarration()`: lazy engine, narration off the main thread, report via the presenter; `onDestroy` cancels and shuts down |
| `activity_main.xml`, `strings.xml` | One `Save narration` control and its state line |
| `RegressionTest.kt` | **R14** — fails if the wiring is removed |

## 4. Evidence (measured locally, then in CI)

| Check | Result |
|---|---|
| Base | `total_tests=441`, job1/job2 exit 0 |
| + presenter and tests | `total_tests=445` |
| + R14 guard | **`total_tests=446`**, job1/job2 exit 0 |
| Negative control — blank-path guard disabled | job 1 **exit 1**; `1) a_success_with_no_path_is_not_reported_as_saved` |
| Negative control — `narrate(` renamed | job 2 **exit 1**; `1) R14 the screen reaches the offline engine` at `RegressionTest.kt:300` |
| Composed with open PR #9 | **`total_tests=452`**, zero failures (`441 + 6 + 5`) |

Both negative controls ran on the real files and were restored byte-identically (`diff`
empty, `grep -c` back to 1, harness back to 446).

## 5. CI, observed — one red and one green at one SHA

| Run | Result |
|---|---|
| `45965117961` JVM verification | success |
| `45965306042` Build Release APK + instrumented tests (`pull_request`) | success |
| `45965117945` Build Release APK (first, `push`) | failure — **not attributable** |

The red: `397 tests completed, 29 failed`, and **all 29** carry
`java.lang.AssertionError at MavenArtifactFetcher.java:129` →
`IOException at HttpURLConnection.java:2059` — Robolectric could not download its
`android-all` jar. The 29 are 23 `SonataRepositoryTest` + 6 `FloatingOverlayServiceTest`;
`NarrationPresenterTest` is not among them, and the base branch passed the same workflow
twice earlier the same day.

That red still settled the compile question: `> Task :app:compileDebugKotlin` and
`> Task :app:compileDebugUnitTestKotlin` both succeeded in it, and the retry passed the
whole job. `gh pr checks` alone would have shown only the latest run.

## 6. Not claimed

- **No physical-device validation.** Instrumented tests pass on an API 34 emulator.
- **No library catalogue.** A narration is written and recorded; no screen lists it yet,
  so "Save → Catalogue → Replay" is half reached.
- **No neural voice.** The registry is still empty; this is the platform tier.
- **No merge, deployment or acceptance.** PR #10 is a draft awaiting owner action.

## 7. Next legal task

`family-safety-network` (oldest verified `last_progress_at` after this cycle's derivation,
2026-11-27T06:13:11Z), at its earliest incomplete phase — F1 release-blocking security or
F2 privacy/consent, whichever the live issues and threat model support. No FSN work was
started in this pulse; one pulse, one task.

## 8. Human decisions required

- **Sonata PR #10**: review, and decide whether #9 or #10 lands first. Both touch
  `MainActivity.kt`; the source auto-merges, only the two append-only logs conflict.
- Nothing in this cycle requested or implied merge, deployment or acceptance authority.
