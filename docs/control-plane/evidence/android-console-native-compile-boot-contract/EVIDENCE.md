# Evidence — android console native compile + boot contract

Pass: hourly bounded execution (Weaver). Status: **IMPLEMENTED** — Kotlin compile
VERIFIED by CI; on-device runtime NOT CLAIMED.

## Base / head
- BASE_MAIN (`origin/main`): `fbe9b837d68a31fabb88e125ed9e2d29dd1bfedf` — merge of PR #233
  (`feat/arkadia-console-native`).
- Branch head: `fix/android-console-native-compile` (`14906e1`).
- PR: #235.

Reconstruction note: the first `git log -1` in this pass showed a stale local commit
(`27b5e49`). After `git fetch --all --prune`, origin/main resolved to `fbe9b83`. The
branch was rebased onto the true BASE_MAIN before push.

## Defects (measured, not inferred)
1. **CharSequence/Int shadowing.** `EditText.apply { setTextColor(text) }` resolves `text`
   to the receiver's `CharSequence` property, not the colour `Int` field. `10558cd8`
   qualified two of three sites (lines ~125, ~178); `captureNote` (line ~141) was missed.
   `grep -rn 'setTextColor( *text *)' arkadia-android/` -> 0 after the fix.
2. **Unresolved `MainActivity.EXTRA_PROCESS_TEXT`.** `ProcessTextActivity.kt:23`
   referenced a companion constant that did not exist. Added `const val` in a companion.
3. **Missing `occurred_at`.** `solspire/workevent_router.py:23` declares
   `occurred_at: float` (no default); `solspire/workevent_manager.py:71` is
   `occurred_at REAL NOT NULL`. `ConsoleApi.emitCapture` omitted it -> the POST would be
   rejected. Fix confirmed against the model, not a docstring.
4. **Unreachable PROCESS_TEXT surface.** `AndroidManifest.xml` declared
   `ProcessTextActivity` with no intent-filter, so the OS could never route a selection to
   it. Registered `android.intent.action.PROCESS_TEXT` (+DEFAULT, text/plain), exported.

## Verification performed
| command | result |
| --- | --- |
| `python -m pytest tests/test_android_console_boot_contract.py tests/test_android_console_contract.py -q` | 7 passed |
| `python -m pytest tests/architecture -q` | 11 passed |
| `python -m py_compile api/main.py` | OK (untouched) |
| `grep -rln 'arkadia-android\|MainActivity\|ConsoleApi' tests/ scripts/ conftest.py` | only the new test observes these sources |
| CP10 `scripts/cp10_mutation_boundary_policy.py --judge` | PASS — every changed path admitted |
| Full suite (`PYTHONPATH=archive/legacy_python`, `--continue-on-collection-errors`) | 26 failed / 1356 passed / 20 skipped / 1 collection error |

Negative control: `test_no_shadowed_text_is_passed_to_set_text_color` was **red before the
fix** on the witness line, proving the harness detects the defect it claims to detect.

## Baseline comparison
26F/1356P is a pre-existing fingerprint (steward_filter, solspire governance,
`autonomy` module-vs-package collision). Only the new test observes the Android sources,
so an Android-only diff cannot move that node set. Regression: unchanged.

## CI (build oracle)
- Build APKs run `37136319374` — **success** (Build Debug APK + Build Release APK green;
  Kotlin compile/link proven).
- Full-history secret scan run `37136319375` — **success**.

## External boundary (BLOCKED, unrelated to this diff)
Two commit *statuses* on `14906e1` report `failure`:
`Vercel – console` and `Vercel – arkadia-prism`, both
"Deployment rate limited — retry in 24 hours."
These are provider statuses, not check-runs; the failure is a Vercel plan rate-limit, not
a repository or test failure. Classified BLOCKED on provider access.

## Not verified
- On-device / emulator runtime behaviour of the native console (no device in this sandbox).
- The WorkEvent round-trip against a live server (model contract verified; no live call).

## Next bounded task (proposed, not executed)
Add an instrumented/runtime smoke check or an emulator CI run so the native instrument is
runtime-VERIFIED, not only compiled. Dependency: device access or CI emulator wiring —
BLOCKED until available. Requires sovereign authorization to scope.
