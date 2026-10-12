# gate10 — history-depth CI wiring

**Branch:** `gate10/history-depth-ci-wiring-01`
**Commit:** `c3af93b1492d766b201f4baacfeb0440e1f08a45`
**BASE_MAIN:** `6109c72ab9eedc2593d2cc6c50ebd01596c80072` (2026-10-12T05:36:48Z)
**PR:** #482 (draft)
**Verification state:** VERIFIED (repository-source + CI runtime observation). No production claim.

---

## 1. Defect

`provider-routing.yml` is the only whole-suite **judging** surface in the repository
(`python -m pytest tests/ -q -rEf --continue-on-collection-errors`, step 8 "Broader test
suite", no `continue-on-error`). It used the default depth-1 checkout.

`tests/test_agents_md_encoding_adjudication.py` resolves pinned revisions out of git
history through `scripts/agents_md_encoding_audit.py`. On a shallow clone
`git cat-file -t 6c43218a48a4` fails, so `exit_code()` returns **2** ("undecided") where a
provably clean file earns **1**.

## 2. Evidence — same SHA, same environment

| measurement | result |
|---|---|
| local, full clone | 17 failed / 2879 passed / 20 skipped / 1 error |
| main CI run `38224653480` (head `6109c72a`) | 21 failed / 2859 passed / 21 skipped / 1 error |
| `comm -13` local vs CI | exactly the 4 adjudication nodes |
| `comm -23` local vs CI | empty |
| `--depth 1` clone, same commit, adjudication file | `4 failed, 13 passed, 6 skipped` |
| full history, same commit, same file | `18 passed, 5 skipped` |

Node-set sha256: main CI `4d72c6b79c85ac97e4114aedd06479fee755ebf40b7dc60626f58ff3379b456f`
(22 nodes); local `7eaa2c116c12b9e0a3993229db647bb76655c95983534db58a6fb171ceed6f6c` (18 nodes).

**A correction.** An earlier draft of this record carried `18 failed / 2877 passed` for the
local full clone — an inherited figure, not a measurement. Re-measured directly on the
pristine `6109c72a` tree: `17 failed / 2879 passed`. The node *set* is unchanged by the
correction (sha256 identical), so no conclusion moves; the number was simply wrong. Both
the before-tree and after-tree measure `2879 passed`.

## 3. Repair

`.github/workflows/provider-routing.yml`:

- `fetch-depth: 0` on the checkout (+12, with rationale comment)
- `tests/test_history_depth_ci_wiring.py` added to the `pull_request` path filter (+1)
- `tests/test_history_depth_ci_wiring.py` added to the `push` path filter (+1)

No `continue-on-error` touched. No step added or removed. No command changed.

## 4. Runtime proof — the repair was observed, not asserted

Branch CI run `38228844451`, `event=pull_request`, head `c3af93b1`:

- `provider-routing` **triggered on the pull_request event** — the self-selection repair
  bites at runtime, not merely in a source assertion.
- Step 8 log contains **zero** occurrences of `test_agents_md_encoding_adjudication`.
- Result: `17 failed, 2883 passed, 16 skipped, 2 warnings, 1 error in 212.62s`.

Node-set delta, main CI (22) vs branch CI (18):

```
comm -23 (fixed by branch):  4 nodes, all tests/test_agents_md_encoding_adjudication.py
comm -13 (newly broken):     empty
```

The job is still `failure` — on **pre-existing, unrelated** debt (the
`ERROR tests/test_autonomy.py` CE-01 module-vs-package collision and the sqlite
contamination class owned by open PR #481). This PR does not claim a green job; it claims
the four clone-depth nodes are gone and nothing new appeared.

## 5. Guard

`tests/test_history_depth_ci_wiring.py` — 15 tests, generic over the repository.

Domains derived, not listed:

- **executing** — workflows whose steps actually invoke pytest over a corpus containing a
  history-dependent guard (tokenised command; `pytest` must be the invoked word)
- **judging** — executing workflows minus those whose step *or* job carries
  `continue-on-error` / `if: false`

Assertions: every executing workflow fetches full history; every judging workflow selects
itself and the guard in its `pull_request` paths filter.

Controls: a prose mention is not an execution; a shallow checkout is not full history; an
unrelated workflow is not in the domain; and a positive control asserting the two domains
are genuinely distinct — if they collapse, the exemption detector stopped working and the
fetch-depth invariant would silently narrow.

**Live negative control on the pristine workflow** (detached worktree at `6109c72a`,
guard copied in): `2 failed, 13 passed`. With the repair: `15 passed`.

Measured domains at `6109c72a`: executing `['provider-routing.yml', 'sg-02-fe-2-v.yml']`,
judging `['provider-routing.yml']`, guards
`{'tests/test_agents_md_encoding_adjudication.py': '6c43218a48a4'}`.

## 6. Regression boundary

`tests/test_gate_filter_selection.py`, `tests/test_ci_gate_trigger_coverage.py`,
`tests/test_ci_suite_collection_continuation.py` and the new guard → **194 passed**.
`tests/architecture` → **11 passed**. `python -m py_compile api/main.py` clean;
`api/main.py` untouched (2505 lines, budget 2600).

The AGENTS.md append is insert-only and therefore node-neutral, proven rather than assumed:
`pytest tests/ --collect-only --continue-on-collection-errors` gives **2915 collected on both
trees** (the bare form interrupts at the CE-01 collection error and under-reports, so the
continuation flag is required), and the full-suite failing/error node set hashes identically
before and after. The `+24 passed` between main CI and branch CI is attributed by
`--collect-only` per file: the four generic workflow-scanning suites collect **87 / 48 / 45 / 7
on both trees**, and the new guard collects **15** — so the delta is the new file's nodes and
nothing else.

## 7. Not done here — deliberately

1. The CP10-B execution defect (`sg-02-fe-2-v.yml` step `CP10-B broader backend regression`
   runs the whole suite without `--continue-on-collection-errors`, so it executes zero
   tests) is **not repaired**. Confirmed the flag is still absent on `main`. It is a
   separate bounded repair on a separate file.
2. The sqlite contamination class is owned by open **PR #481**; not touched, not duplicated.
3. **PR #462 was closed by the sovereign with an explicit precondition.** This pass did not
   re-open, re-run, or modify it. PR #482 is a different file, different defect and
   different repair, but the same *family* (a whole-suite CI surface that misreports). It is
   opened as a **draft** and no merge is solicited. If the sovereign intends that family to
   be paused, #482 should be closed and will not be re-opened.

## 9. Guard inputs must select the gate — `AGENTS.md` was named by no filter

The guard in §4 derives its domain from the repository, but until this pass it asserted only
that a *guard file* selects the workflows that execute it. That is half the invariant: a
guard's verdict is a function of its **inputs**, so an input whose edit does not execute the
guard changes what the guard asserts without running it.

Measured on this branch's own second commit — which touched `AGENTS.md` and the evidence
record and nothing else: `grep -rn "AGENTS.md" .github/workflows/` returns matches in
`baseline-preflight.yml` and `baseline-fingerprint.yml` **in comments only**, and no `paths`
filter anywhere in the repository names it. `tests/test_agents_md_encoding_adjudication.py`
reads `AGENTS.md`, so an `AGENTS.md`-only commit altered a judged guard's subject while
running no whole-suite surface.

Repair, both halves derived rather than restated:

- `_guard_inputs(guard)` reads the guard's own source **by AST** and returns every string
  constant that names a path in `git ls-files`. A hand-maintained list would drift, and a
  drifted list makes the completeness assertion vacuous — the defect class the repository
  already recorded for `FINGERPRINT_DOCS` and for the console-contract domain. Test files are
  excluded: siblings are selected by the guard's directory, so naming them would make the
  rule unsatisfiable.
- `provider-routing.yml` (the sole *judging* whole-suite surface) selects `AGENTS.md`.

**Negative controls.** (1) `test_negative_control_a_guard_input_the_filter_omits_is_reported`
trims the real filter and requires each real input to become deselected, so the assertion
cannot be disarmed by narrowing the filter. (2) Live control on the **real** workflow file:
removing the `AGENTS.md` line reddens
`test_a_workflow_selects_every_input_its_guard_reads[provider-routing.yml]`
(**1 failed, 16 passed**); restoring it byte-identically returns **17 passed**. The detector
was first run against the unmodified gap and failed there (**1 failed, 15 passed**) — it bit
on the real defect before any synthetic one.

**Regression boundary.** Fresh `main` (`6109c72a`) measured in the same environment, same
extraction convention (`grep -E '^(FAILED|ERROR) ' | sort | sha256sum`):
node set `c853c9a6d431a4166e4d2c1d3cca8f3fef5e094105f5e6eeaa028e2aa471891e` (18 nodes) on
**both** trees, `comm -3` empty. Suite totals `17 failed / 2864 passed` on `main` vs
`17 failed / 2881 passed` on the branch — the `+17` is attributed by `--collect-only`, not by
the count: `tests/test_history_depth_ci_wiring.py` collects **17** on the branch and **0** on
`main`, and the repository total moves `2900 → 2917`. The four generic workflow-scanning
suites gain nothing; `tests/architecture` is **11 passed**; `python -m py_compile api/main.py`
clean; `api/main.py` untouched (2505 lines, budget 2600).

**Do not cite this fingerprint as the inherited one.** The inherited pass recorded a *different*
extraction convention (`FAILED` only, no `ERROR` lines) and a 15-node guard. The recorded
`7eaa2c11…` is a **`FAILED`-only digest**, not the `FAILED|ERROR` digest above; both are correct
for their own convention, and comparing them across conventions is not a regression signal.

## 10. Runtime proof — CI `provider-routing` on this head, and the four adjudication nodes

The `fetch-depth: 0` repair in §5 was a **source** claim until this pass. It now has a runtime
observation at head `8f1dd97aee8fe99d8369b265491977a09f1ea2b3`, run `38232115303`, job
`114753846310`, step `Broader test suite`:

| tree | run | summary | nodes | ids sha256 |
|---|---|---|---|---|
| `main` `6109c72a` | `38224653480` | 21 failed / 2859 passed | **22** | `4d72c6b79c85ac97e4114aedd06479fee755ebf40b7dc60626f58ff3379b456f` |
| branch `8f1dd97a` | `38232115303` | 17 failed / 2885 passed | **18** | `7eaa2c116c12b9e0a3993229db647bb76655c95983534db58a6fb171ceed6f6c` |

`comm -3` of the two CI node-id sets is **exactly the four** `tests/test_agents_md_encoding_adjudication.py`
nodes — and nothing else:

```
test_cli_summarises_the_oracle_without_crashing
test_corruption_origin_is_re_derivable
test_exit_code_does_not_call_a_divergent_clean_file_verified
test_live_file_verdict_matches_its_state
```

This is the repair doing what it claims, observed in CI rather than argued: on `main`'s
depth-1 checkout those four nodes are red; on this head the full-history checkout makes them
green, and **no other node changes**. The branch's CI node set is byte-identical to the
branch's local node set (`7eaa2c11…` both) — the four clone-depth artifacts are gone, which is
why the branch carries **18** nodes against `main`'s **22**.

**Note the direction.** The branch *reduces* the CI failure count by 4 relative to `main`
without touching any of the four files it repairs — the fix is a checkout depth, not a test
edit. The remaining 17 failures are pre-existing debt owned elsewhere (voice/sqlite, Lab
authority pins, SolSpire R1/R3 pins, `test_autonomy.py` collection error) and are **not**
repaired here.

**`provider-routing` is red on `main` itself** (`38224653480`, measured at `6109c72a`), so its
red status on this branch is pre-existing, not branch-caused. Classify accordingly.

**Convention discipline — three digests, none comparable across conventions.** All measured on
the same trees:

| convention | branch value |
|---|---|
| `FAILED|ERROR` with pytest reason text | `c853c9a6…` |
| node ids only (reason stripped) | `7eaa2c11…` |
| `FAILED` only, ids only | `37ad6b6f…` |

§9's regression claim uses the first; the CI comparison above uses the second. Both are
correct. A digest quoted without its convention is not a measurement.

## 12. Attribution of the two `n-atlas-external-beta` failures on this head

Head `a3c630a2` carried two red checks that `8f1dd97a` (12 minutes earlier, same branch,
same workflow) did not: `beta-beta-02-hausa` and `bundle-beta-evidence`. Both are
**pre-existing and not caused by this change**. The branch does not touch the beta
workflow — `git diff --name-only 6109c72a a3c630a2` lists only `provider-routing.yml`,
`AGENTS.md`, this file and `tests/test_history_depth_ci_wiring.py`.

**`beta-beta-02-hausa` — transient external runtime.** The evidence payload names
`runtime https://koladeodunope-ednai-natlas-runtime.hf.space`, `provider ednai_zerogpu`,
and fails with `RUN_FAILED reason="external runtime did not return usable inference"`
with `errors: []` — an empty error list, i.e. no transport error to attribute. A re-run
of the failed jobs on the *same commit* returned `beta-beta-02-hausa success` and
`beta-beta-01-english success`. The sibling commit `8f1dd97a` also passed it. A failure
that does not reproduce on the same SHA is environmental, not branch-caused. Recorded as
`ENVIRONMENTAL` / pre-existing.

**`bundle-beta-evidence` — a latent race in the workflow, pre-existing on `main`.**
The job runs `needs: beta` with `if: always()` and downloads every artifact matching
`pattern: "*-evidence"`. That pattern selects **three** artifacts
(`beta-01-english-evidence`, `beta-02-hausa-evidence`, `natlas-native-golden-evidence`),
while the guard asserts `if len(files) != 2 or any(s != "PASS" ...): sys.exit(1)`.
Because the bundle job is gated on `needs: beta` and the golden job is gated on
`needs.beta.result == 'success'`, both become runnable at the same moment, and whether
the third artifact is uploaded before the bundle step lists `evidence/*.json` is a race.
Measured:

| run | head | bundle start→end | golden start→end | bundle |
|---|---|---|---|---|
| `38088702840` | `4f09b558` | 21:43:43→21:43:49 | 21:43:43→21:44:24 | success |
| `38232115080` | `8f1dd97a` | 09:47:26→09:47:30 | 09:47:26→09:48:12 | success |
| `38233402572` | `a3c630a2` | 10:06:20→10:06:27 | 10:03:48→10:04:30 | failure |

The two passing runs finished the bundle job in 6 s and 4 s, *before* the golden job
completed — they listed two files. The failing run started the bundle job after the
golden job had already uploaded, listed **three** files
(`['native-golden.json','beta-01-english.json','beta-02-hausa.json']`) and failed on
`len(files) != 2`. The second bundle re-run printed
`statuses: ['PASS','PASS','FAILED']` — its third file was the golden evidence, read
before its `status` field was final, which is the same race from the other side.

So the guard's real invariant is "the two beta evidence files are present and PASS"; the
`!= 2` count encodes an assumption about timing that the `*-evidence` glob does not
guarantee. This defect is **not repaired here** — it is pre-existing on `main`, it is
outside this gate's scope, and it is proposed as a separate bounded workstream. Discovery
does not authorize execution.

## 13. Authority

No merge, no deployment, no acceptance. Human authority final.

## 14. Reconciliation against current `main` (2026-10-12, hourly pulse)

The branch had gone `DIRTY`/`CONFLICTING` (`mergeable=false`) because `main` had advanced
past its base. Re-measured live:

- `BASE_MAIN` = `ee684fffe6f4f1670a7d9e8928e9c5fc323b4c2a` (PR #487 merge, `cp10-broad-suite-reach-01`).
- Merge base of the branch and `main` = `6109c72ab9eedc2593d2cc6c50ebd01596c80072`.
- `main` appended a new hygiene section to `AGENTS.md` (`## A fix you are authorized to
  write can land on main while you write it`); this branch appended its own
  (`## A judging CI surface on a shallow clone fails a clean file`). Both are append-only
  prose, so the conflict is a pure append collision.

Resolution: merge `origin/main` into the branch and keep **both** appended sections in
order (branch section first, `main`'s section second). No oracle-carried line was
rewritten; the AGENTS.md encoding invariant holds (`cyrillic == 0`).

Verification on the reconciled tree:

- `tests/test_history_depth_ci_wiring.py` -> **17 passed**.
- Full suite (`pytest tests/ -q -rEf --continue-on-collection-errors`) ->
  `97 failed, 1908 passed, 21 skipped, 105 errors`.
- Failing/error **node set** identical to `BASE_MAIN`: **202** nodes on both trees,
  `sha256 533ed749a3b5b2bcbee341b2abbf29e0e64b52f2c11ddf4ab7977a85585ac20b`, `comm -3` empty.
  The `+17 passed` is exactly this branch's new guard file. Zero regression.
- Architecture suite: `11 passed`.

Authority: no merge, no deployment, no acceptance. Human authority final.

## 15. CI attribution on the reconciled head `cd5147dd` (provider-routing)

`provider-routing` remains red on the reconciled head — as it is red on `main` itself
(`workflow_dispatch` run `38249795854` at `26521e24`, before the recent merges). Comparing
the two job logs:

| Tree | Step 8 (`Broader test suite`) |
|---|---|
| `main` `26521e24` | `21 failed, 2866 passed, 21 skipped, 1 error` |
| branch `cd5147dd` | `8 failed, 2979 passed, 16 skipped, 1 error` |

- **Every one of the 9 failing/error nodes on the branch is also in `main`'s CI failure
  set** (`comm -23` empty) — zero branch-caused failures.
- The `fetch-depth: 0` repair is proven live: `tests/test_agents_md_encoding_adjudication.py`
  contributes **4** failing nodes in `main`'s job log and **0** in the branch's. That is
  exactly the defect this PR repairs.
- The remaining red is pre-existing sovereign-owned debt (the CE-01 `weaver.autonomy`
  module-vs-package collection error, the `test_engineering_lab_api.py` authority-boundary
  pins, `test_solspire_r1/r3` governance pins, Landing/identity copy pins) and is **not**
  repaired here.

This is a repository-source/CI-log observation. No merge, no deployment, no acceptance.
