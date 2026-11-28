# ARK-OPS-CONTINUOUS-001 — cycle 31: Sonata's retry path stops claiming silence as stored audio

**Contract:** `ARK-OPS-CONTINUOUS-001` rev `2026-11-22`
**Portfolio directive:** `PORTFOLIO-WEAVER-2026-11-26-01`
**Base:** `main` @ `8f746f9eab6df51733f6d43c8bab26af63eb6471` (Arkadia)
**Branch:** `gate-hygiene/portfolio-state-ledger-01`
**Pulse:** 2026-11-28T01:06Z
**Authority:** `MERGE_AUTHORITY := NONE`, `DEPLOY_AUTHORITY := NONE`. No merge, no push to any
canonical branch, no deployment, no acceptance, no draft conversion. The ledger's own PR #744
was extended rather than duplicated.

This is a **reconciliation/implementation** record, so it takes the bare `…-cycle-NN` path.
The work itself landed in the selected repository (`sonata`), not here.

Files this record touches in Arkadia:

```
docs/control-plane/openhands/hourly-weaver/portfolio-state.json                                    (re-derived)
docs/control-plane/openhands/hourly-weaver/portfolio-cursor.json                                   (authored judgement)
docs/control-plane/evidence/ark-ops-continuous-001-cycle-31-sonata-empty-audio-truth-01/EVIDENCE.md (new)
```

---

## 1. Reconstruction and selection

Live from GitHub at 2026-11-28T01:07Z, not from memory:

| Repository | Default branch | Head | Open PRs | `last_progress_at` |
|---|---|---|---|---|
| `sonata` | `feature/sonata-tts-app` | `7c4e6a64e39e` | 2 | 2026-11-27T16:19:14Z |
| `family-safety-network` | `main` | `18c729735fd4` | 9 | 2026-11-28T00:17:44Z |
| `Arkadia` | `main` | `8f746f9eab6d` | 64 | 2026-11-28T00:21:11Z |

Sonata was oldest, so the fairness rule selected it; the tie-break order was never
reached. Selection was derived by hand from the GitHub API and then re-derived by
`scripts/portfolio_state_refresh.py` — both agreed.

**One stale field was corrected, not reconciled.** The committed snapshot recorded
Arkadia's `pushed_at` as `2026-11-27T17:12:43Z`; live is `2026-11-28T00:21:11Z`
(PR #744's own push). The ordering is unchanged — Arkadia is newest either way — so the
selection is unaffected, but the field was stale and `--write` replaced it.

## 2. Selected task, and why it is not a duplicate

Both of Sonata's open drafts are **CI-green and awaiting human review**:

- `#9` (`fix/s1-tier-truth-001`, head `3e034ca`) owns the service/lifecycle slice —
  `SpeechService`, `Prefs`, `TtsEngine`, `MainActivity`, `PlaybackPhase`, `ReadOutcome`.
- `#10` (`feat/save-narration-reachable-01`, head `e1f952a`) owns the screen→engine slice —
  `EngineFactory`, `MainActivity`, presenters, data layer.

`engine/OfflineEngine.kt` is touched by neither, so a slice there cannot duplicate an open
draft. The cursor's own `next_legal_task` named S2 as the next unowned slice; S2 needs a
bundled licensed model plus a device measurement, which this sandbox cannot supply. The
slice selected instead is a **recorded defect inside the S3/S4 recovery path**, which is
implementation-shaped and verifiable here.

## 3. The defect

`OfflineEngine` has two completion paths, `narrate` and `retry`, and the rule "a
`Success` with no samples is a failure" was written in one of them. `retry` had no such
check.

`WavWriter.wrap` returns a 44-byte header-only WAV for an empty payload — its `require`
calls guard the sample rate, channels and bit depth, not the payload size.
`completeNarration` accepts `GENERATING → COMPLETE`, and `LibraryRules.isPlayable` asks
only for `COMPLETE` plus a non-blank `audioPath`.

Measured on the base tree, driving `retry` with `pcm = ByteArray(0)`:

```
outcome        = Success
row.status     = COMPLETE
row.audioPath  = <tmp>/1.wav
row.durationMs = 0
store.allIds() = [1]
bytesFor(1)    = 44
isPlayable     = true
```

That is S4's acceptance criterion *"No false claim of stored audio when none exists"*
failing, and it contradicts the engine's own documented ordering rule.

## 4. The repair

`refuseEmptyAudio` states the rule once and both paths call it, so they cannot drift apart
again. The distinct message each path emits when the **transition** is refused is unchanged
— `"This narration was interrupted and must be retried"` and `"This narration could not be
completed"` describe genuinely different situations.

After the repair the same measurement reads `Failure`, `FAILED`, `audioPath = null`,
`store.allIds() = []`, `isPlayable = false`.

## 5. Evidence

Sonata PR `#11`, branch `fix/engine-empty-audio-truth-01`, base `7c4e6a64`, head `f85e779`.

| Check | Command | Result |
|---|---|---|
| Baseline, unmodified `7c4e6a64` | `bash ci/run-ci.sh --check` | `total_tests=441`, job1/job2 exit 0 |
| Two tests added, repair absent | `bash ci/run-ci.sh --check` | job1 exit **1** — `retry refuses a model that produced no audio` fails at `assertTrue(outcome is Failure)` |
| Repair applied | `bash ci/run-ci.sh --check` | `total_tests=443`, job1/job2 exit 0 |
| **Negative control** — rule disabled at its definition (`if (true) return null`) | `bash ci/run-ci.sh` | `Tests run: 274, Failures: 2` — exactly the two new nodes |
| Rule restored | `sha256sum OfflineEngine.kt` | `77dd8f4d…`, identical to the repaired file |

The `441 → 443` delta is exactly the two new nodes; the change adds tests to an existing
file and no new source files. The negative control disables the behaviour at its
**definition** rather than at a call site, so both paths are exercised.

Toolchain, provisioned in this sandbox because none was present: Temurin `17.0.21.1`
(matching the §8.3 record), kotlinc `1.9.24`, jars from Maven Central and Google Maven.
`ci-evidence.log` was regenerated and committed; it had last been written at `744a995` on
kotlinc `1.9.22`, so its source counts move `47/17 → 49/20` — the tree advancing between
those commits, not this change.

## 6. Not claimed

- **No device validation.** No hardware here. CI is not device evidence.
- **No Gradle or Android SDK build.** `android_sdk=ABSENT` is recorded in the evidence log.
- **`retry` has no production caller yet.** `grep -rn '\.retry(' app/src/main/kotlin`
  returns nothing. This is a boundary repaired before the recovery UI is wired to it, not a
  user-visible fix today. It becomes reachable exactly when S3/S4 wire "resume after process
  death", which is when a silent `COMPLETE` would be hardest to notice.
- **No neural model, no voice-quality change.** L1 and L4 of `SONATA_KNOWN_LIMITATIONS.md`
  stand as written.
- **No merge.** PR #11 is a draft; marking it ready is the owner's action.

## 7. Next legal task

S2 — a natural offline neural voice — is unstarted and remains the next unowned slice. The
`engine/` package already carries the compatibility gate and no model file, so the first
real step is a bundled licensed model plus a device measurement, not more policy code.

The fairness clock now reads FSN as oldest (`2026-11-28T00:17:44Z`), so the next pulse
should select `family-safety-network` unless a human decision changes that.

PRs #9, #10 and #11 all await human review. None should be duplicated.
