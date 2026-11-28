# ARK-OPS-CONTINUOUS-001 — cycle 40: Sonata is the fair selection, and a sample's end stops being the read's

**Executed:** 2026-11-28T15:06Z–15:25Z
**Contract:** `docs/control-plane/openhands/hourly-weaver/2026-11-22-continuous-reconciliation-contract.md`
**Portfolio directive:** `PORTFOLIO-WEAVER-2026-11-26-01` (three repositories, one bounded task per pulse)
**Authority:** read-only reconstruction plus one bounded implementation. No merge, no deployment, no acceptance.

## 1. Fresh-sandbox reconstruction

Identity `gh api user` → `Arkadia-Oversoul-Prism`. All three repositories discoverable and
verified; none omitted.

| repository | default branch | head SHA | open PRs | open issues | last_progress_at |
|---|---|---|---|---|---|
| `Arkadia-Oversoul-Prism/sonata` | `feature/sonata-tts-app` | `7c4e6a64` | 5 (all drafts) | 1 | **2026-11-28T12:12:32Z** |
| `Arkadia-Oversoul-Prism/family-safety-network` | `main` | `18c72973` | 14 (all drafts) | 9 | 2026-11-28T13:11:41Z |
| `Arkadia-Oversoul-Prism/Arkadia` | `main` | `8f746f9e` | 64 (all drafts) | 10 | 2026-11-28T14:15:46Z |

Sonata's default branch is **not** `main` — `feature/sonata-tts-app` is what GitHub reports,
and it is what the ledger records. A tool that assumed `main` would have dropped a repository.

## 2. The selection

`scripts/portfolio_state_refresh.py` (PR #744) derives `last_progress_at` from live
`pushed_at` / newest open-PR `updated_at`. At the selection instant (15:06Z) the oldest
verified value was Sonata's `12:12:32Z`, so the fairness rule selected **sonata** — also
the first tie-break. Sonata had gone longest without a pulse; Arkadia had been worked at
14:15Z and FSN at 13:11Z.

**Note for the next pulse:** this pulse's own push moves Sonata's `last_progress_at` to
`15:18:50Z`, so the re-derived selection at `15:20:21Z` is **FSN** (`13:11:41Z`). The
ledger therefore records the *post-push* derivation while this record states the
*selection-time* one. They are both correct and are not the same number. A push that
exists only to write the ledger competes with real progress for the fairness clock; the
selection must be read from `pushed_at` at the pulse's start, not from the file after it.

## 3. The task: continue #9, the earliest incomplete phase

Within Sonata, §4.2 order is *continue an existing authorized PR first; prefer the earliest
incomplete phase*. S1 is the earliest incomplete phase and `#9` (`fix/s1-tier-truth-001`)
owns it. #9's own text named the next bounded change, twice:

- the review checklist: *"…repairing the live line is acceptable as the next bounded change"*;
- `SONATA_KNOWN_LIMITATIONS.md` **L24**, added by the same PR: *"`Client.onError` still
  delivers the sample's message to the bound screen, which sets `readFailure` and can paint
  `PlaybackPhase.FAILED` … That changes the `SpeechService.Client` contract, which both
  `MainActivity` and `FloatingOverlayService` implement, so it is its own bounded change."*

No new branch and no new PR: the work belongs to the PR that recorded the gap.

## 4. What was measured before the change

`./ci/run-ci.sh --check` at `f488815` (the untouched PR head): **`total_tests=490`,
job1_exit=0, job2_exit=0** — byte-for-byte the count #9's body records for its third
commit. The tracked harness runs in this sandbox once the toolchain is provisioned
(§6), so the baseline is reproduced rather than inherited.

## 5. The change (head `1031701` on `fix/s1-tier-truth-001`)

The live line had **two** defects, not the one L24 named:

| what the user did | in flight | screen said, before |
|---|---|---|
| auditioned a voice, the sample failed | `PREVIEW` | "the read stopped" (`readFailure` → `FAILED`) |
| auditioned a voice, the sample succeeded | `PREVIEW` | nothing — the line stayed on "playing the sample" |
| pressed Read on an empty passage | `READ` | "Nothing to read" (correct) |

`UtteranceAttributionPolicy.liveSurface(inFlight)` answers the live-line question from the
same in-flight fact the stored record already used; the service decides the surface
**before** clearing `inFlight` and delivers through one `notifyTerminal(surface, message)`.
Both implementers carry `Client.onPreviewEnd`: the screen shows the reason as a notice and
repaints the read from its own facts, and the floating player no longer dismisses itself
when a sample ends. `InFlightUtterance.NONE` stays on the read's line deliberately —
"Nothing to read" is dispatched that way, and a message delivered nowhere is not better
than a message on the wrong line.

| check | result |
|---|---|
| `./ci/run-ci.sh` with the change | `total_tests=498`, job1/job2 exit 0, `VERDICT=PASS` |
| delta | **+8** = 4 `UtteranceAttributionTest` methods + 4 `LiveLineAttributionWiringTest` guards |
| negative control (live) — service dispatch restored | `Tests run: 180, Failures: 1`; restored byte-identically → `OK (180 tests)` |
| negative control (live) — `readFailure` back in the screen's sample line | `Tests run: 180, Failures: 2`; restored byte-identically → `OK (180 tests)` |
| CI on `1031701` | `JVM verification (app core + narration core)` **completed/success**; APK and emulator jobs in progress at the time of writing |

One test failed on first run and was **corrected, not weakened**: an agreement property
asserted over `InFlightUtterance.values()` is false for `NONE` by design, so the property
now states its domain.

## 6. Environment finding worth keeping

Cycle 39 recorded *"this execution sandbox has no JDK … so no Kotlin change can be
compiled or tested before push"*. That is **not** a property of the sandbox; it is a
property of not having provisioned it. Measured this pulse:

- Temurin **JDK 17** from `api.adoptium.net` (tarball, extracted to a writable path — `/opt`
  is not writable, `KOTLINC`/`LIB`/`STD` are overridable, so no root is needed);
- **kotlin-compiler-1.9.22** from the GitHub release zip (the `bin/*` scripts arrive
  non-executable; `chmod +x` is required);
- the nine classpath jars from the handoff §4.2 — **androidx `room-common` and `annotation`
  are served by `dl.google.com/dl/android/maven2`, not Maven Central**, and the harness's
  own preflight caught the two 554-byte error pages and reported `RESULT=TOOLCHAIN_BROKEN`
  instead of a compile failure.

After that, `./ci/run-ci.sh` reproduces the recorded baseline exactly. **Do not record
"no JDK" as a blocker again without running the recipe.**

## 7. Next-action block

- **Current state:** sonata `feature/sonata-tts-app` `7c4e6a64`; five open drafts (#9 head
  `1031701`, #10 `e1f952a`, #11 `f85e779`, #12 `206344da`, #13 `5f2c9002`), all mergeable,
  all awaiting human review; #9 now carries S1e + S1f with 498 tests PASS locally and JVM
  verification green in CI. FSN (`13:11:41Z`) is the next fair selection.
- **Evidence:** this file; `ci-evidence.log` in the Sonata commit; the two live negative
  controls; `portfolio-state.json` re-derived at `15:20:21Z`.
- **Blockers:** every merge path needs an owner action (mark ready) and human review —
  GOV-04/ADR-016; physical-device acceptance needs the household Samsung A23 and OPPO;
  S2 (a natural offline neural voice) has no bundled licensed model and cannot be closed by
  policy code.
- **Authorized action:** continue an OpenHands-owned draft; repair an evidence-backed defect
  that no draft owns; refresh this ledger.
- **Forbidden:** merge, push to `main`, force-push, draft conversion, deployment, release,
  acceptance, opening a PR for a slice an open draft already owns.
- **Completion condition:** a bounded change on an existing owned branch with targeted tests,
  a reproduced baseline, live negative controls, and this record appended to the ledger PR —
  with no merge, deployment or acceptance claimed.
