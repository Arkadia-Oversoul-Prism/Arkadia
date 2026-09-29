# GATE-10 · CP10 mutation boundary — root narrative docs — Evidence

**Gate / workstream:** GATE-10 (GOVERNED EXECUTION) — CP10 verification gate integrity.
**Authorization:** Human sovereign. Merge is human-only; no merge, no push to `main`.
**BASE_MAIN:** `a26af408c269729a57d0a53c6ad39fcf0ca22fdf`
("Merge pull request #104 from Arkadia-Oversoul-Prism/solariun/thread-navigation-01")
**Branch:** `gate10/cp10-allowlist-root-docs`
**Status:** VERIFIED — branch CI green (`validate = success`, step 31 `CP10 mutation boundary` = `success`, run `36479508791`); full-suite failure fingerprint byte-identical; architecture 11/11. Awaiting sovereign review and merge.

## 1. Repository binding (contract steps 01–02)

- `origin/main` = `a26af408c269729a57d0a53c6ad39fcf0ca22fdf`, a real commit; default branch `main`.
- Working tree clean at pass start; HEAD == `origin/main`.
- **Baseline drift recorded:** the contract's stated `BASE_MAIN 6038989` is stale. Live `main`
  is `a26af408`. The stated full-suite baseline (804 passed / 54 failed / 2 errors) is also
  stale; measured live baseline at `a26af408` is **903 passed / 49 failed / 12 skipped / 2 errors**,
  architecture **11/11**. All comparisons in this record use the measured live baseline, not prose.
- Credential check: ambient `github_token` authenticated for read + branch push. No read-only
  HARD STOP (unlike the P1-A incident).

## 2. The defect (reproduced from live CI, not inferred)

`.github/workflows/sg-02-fe-2-v.yml` (`SG-02-FE.2-V`) is **red on canonical `main`** at both
`a26af40` and the preceding `d48ad0e`. It fails at the "CP10 mutation boundary" step:

```
Unexpected path outside legitimate repository surfaces:
AGENTS.md
##[error]Process completed with exit code 1
```

A second, independent source of truth already exists and is unit-tested —
`scripts/cp10_mutation_boundary_policy.py::evaluate_changed_paths`. Its `LEGIT` regex admitted
only paths carrying a directory prefix (`.github/`, `web/`, `docs/`, ...). Top-level narrative
docs such as `AGENTS.md` matched none of them, so any commit that touched repository memory
failed the gate.

**This is drift, not a governance finding.** `tests/test_m02a_ci_gate_integrity.py` already
carries an anti-drift guard (`test_workflow_allowlist_agrees_with_policy_on_product_surfaces`,
added after `enterprises/` was wrongly omitted and rejected EDEN-OPS-02). The guard's corpus
was narrow — it only checked the EDEN-OPS-02 change set — so the identical class of omission
recurred for root docs and the guard did not fire.

**Bounded blast radius.** Exactly one file was ever the offender (`AGENTS.md`); every other
path in both rejected change sets was already admitted. No authority model, identity boundary,
governance code, or new mutation/authorization path is involved. No trajectory move is
implicated: `AGENTS.md` is ordinary repository memory, written by ordinary work (PR #97, PR #104).

## 3. The bounded change

| File | Change |
|---|---|
| `scripts/cp10_mutation_boundary_policy.py` | add `[^/]+\.md$` alternative to `LEGIT` |
| `.github/workflows/sg-02-fe-2-v.yml` | add the same alternative to the inline `legit=` copy |
| `tests/test_m02a_ci_gate_integrity.py` | extend the drift guard to the real corpus |

`[^/]+\.md$` is deliberately **not** a blanket `*.md` bypass: `re.match` anchors at the start
and the pattern forbids `/`, so only root-level files qualify. Nested paths continue to resolve
through their own directory prefix, and the private `vault/` surface stays rejected.

## 4. Proof (runtime evidence)

**Rejected change set now passes — policy and workflow shell agree:**

```
$ python3 -c "from scripts.cp10_mutation_boundary_policy import evaluate_changed_paths; \
    print(evaluate_changed_paths(['AGENTS.md', ...]))"
(True, 'PASS')

$ printf '%s\n' <same set> | grep -vE "$legit"      # the workflow's own check
offenders-exit=0                                     # no offenders
```

**Negatives still rejected** (boundary did not widen into a bypass):

```
OFFENDER: vault/Ideas/x.md
OFFENDER: secret-backdoor/bin/x
```

**Self-check — this PR's own diff passes its own gate:** `(True, 'PASS')` on
`['.github/workflows/sg-02-fe-2-v.yml', 'scripts/cp10_mutation_boundary_policy.py',
'tests/test_m02a_ci_gate_integrity.py']`.

**Targeted tests:** `pytest tests/test_m02a_ci_gate_integrity.py -q` → **18 passed** (14 pre-existing + 4 new).

**Architecture fitness:** `pytest tests/architecture -q` → **11/11 passed** at BASE_MAIN *and* after the change. No `REGISTERED_ARCHITECTURAL_DEBT` touched.

**CI confirmation (the decisive evidence).** Before/after pair on the same workflow:

| | run | head | result |
|---|---|---|---|
| `main` (before) | [`36476846137`](https://github.com/Arkadia-Oversoul-Prism/Arkadia/actions/runs/36476846137) | `a26af408` | **failure** |
| this branch (after) | [`36480289928`](https://github.com/Arkadia-Oversoul-Prism/Arkadia/actions/runs/36480289928) | `370f442` | **success** |

On the branch run, `validate = success` and specifically **step 31 `CP10 mutation boundary` →
`success`** — the exact step that failed on `main`. No step in the job failed. Re-confirmed green
at each of the branch's three heads (`3839d53`, `9717868`, `370f442`). The gate is restored, not
suppressed: `continue-on-error` semantics are untouched and every verdict step remains enforced by
`steps.<id>.outcome` (asserted by `test_continue_on_error_gates_are_still_enforced_by_outcome`).

**Full-suite fingerprint — regression boundary held.** `api/main.py` untouched, so no boot-code
compile gate is required; `py_compile` on both changed Python files passed regardless.

| | passed | failed | skipped | errors | failing/error nodes sha256 |
|---|---|---|---|---|---|
| baseline `a26af408` | 903 | 49 | 12 | 2 | `256204af…83fca` |
| after change | 907 | 49 | 12 | 2 | `256204af…83fca` |

Passed count rises by exactly 4 (the new tests); **failed/error fingerprint is byte-identical**.
No baseline failure was fixed, masked, or newly attributed.

## 5. Pass 2 — omitted merged surfaces (`knowledge/`, `spiral_grove/`, root `conftest.py`)

Pass 1 restored the gate for the change sets already on `main`. Auditing the *open* PRs revealed the
allowlist was still an incomplete inventory, so `main` would have gone red again on the very next
merge:

| surface | rejected | evidence |
|---|---|---|
| `knowledge/` | yes | PR #109 changes `knowledge/static_ingestion.py`; step prints `Unexpected path outside legitimate surfaces` |
| `spiral_grove/` | yes | **self-contradiction**: the workflow triggers on `spiral_grove/**`, yet its own allowlist rejects `spiral_grove/__init__.py` |
| `conftest.py` (root) | yes | root test-session fixture; committed by ordinary work |
| `AGENTS.md` | yes | (pass 1 — already on `main`) |

`knowledge/` is the Knowledge OS corpus engine (GATE-01 canonical authorship, GATE-05) and
`spiral_grove/` is the Spiral Grove engine (SG-03). Both are tracked, active, and merged into `main`.
A gate that rejects the branch it is written to watch is unsound, not strict.

**Change** — two literals added to the single shared allowlist and its workflow mirror:
`conftest\.py` (root-only: `somewhere/conftest.py` still fails) and `knowledge/`, `spiral_grove/`
(directory-prefix anchored, so `knowledge_evil/` and `.knowledge/` still fail).

**Exact-CI simulation** (the real `grep -vE "$legit"` from the workflow, not a re-implementation):

| changeset | before | after |
|---|---|---|
| `main` tip = PR #104 change set | FAIL | PASS |
| PR #109 change set | FAIL | PASS |
| `spiral_grove/learning_path.py` | FAIL | PASS |
| root `conftest.py` | FAIL | PASS |
| `secret-backdoor/bin/x`, `vault/Ideas/x.md` | FAIL | **still FAIL** |
| `knowledge_evil/x.py`, `.knowledge/x.py`, `somewhere/conftest.py` | FAIL | **still FAIL** |
| `SolSpireExperienceV3.tsx` | forbidden stage | **still forbidden** (separate `forbid` stage) |

**Regression boundary held.** Full suite, this worktree vs. baseline `a26af408`, same invocation:

| | passed | failed | skipped | errors | failing/error fingerprint |
|---|---|---|---|---|---|
| baseline `a26af408` | 903 | 49 | 12 | 2 | `e1ed0b1ea635` |
| after pass 2 | 913 | 49 | 12 | 2 | `e1ed0b1ea635` |

Passed rises by exactly 10 (the new tests); the failing-node fingerprint is **byte-identical**
(`diff` of sorted `FAILED` lines is empty). No baseline debt fixed or newly attributed.

`tests/test_m02a_ci_gate_integrity.py` gained 6 tests locking this in, including a drift assertion
that the workflow's inline copy and the policy script agree on the newly admitted surfaces **and**
on the lookalike negatives. `tests/architecture` = 10/10.

## 6. Pass 3 — close the bug class: the allowlist becomes an inventory

Passes 1 and 2 made the allowlist admit the surfaces known to be missing. Pass 3 stops patching
symptoms and **asserts the invariant**: every path the repository actually tracks must be admitted,
and the workflow's inline mirror must agree with the policy script on all of them.

This defect class had already recurred three times — `enterprises/` (EDEN-OPS-02), root narrative
docs (EL-01..10 PR #97), root docs again (Solariun PR #104) — because each fix enumerated the
symptom rather than the invariant. The pass-3 tests would have caught all three on the PR that
introduced each omission.

**Principle.** The gate's teeth are the `forbid` stage (constitutional V2/V3 dual shells) and the
rejection of **unknown** roots. Breadth in the admit-list is not a weakness: an inventory that
omits a tracked surface does not tighten the boundary, it reddens `main` on the next unrelated
merge. Boundary integrity is therefore enforced by *completeness plus negatives*, not by scarcity.

**Completeness audit** (workflow's real `legit` regex vs. `git ls-files`):

| | value |
|---|---|
| tracked paths | 1394 |
| rejected by the completed allowlist | **0** |
| vault scaffold admitted | 14/14 |
| lookalike/negative probes rejected | 8/8 |

**Negatives still rejected:** `knowledge_evil/x.py`, `.knowledge/x.py`, `spiral_grove_evil/x.py`,
`conftest_evil.py`, `somewhere/conftest.py`, `vault/Ideas/2026-01-01.md`, `secret-backdoor/bin/x`,
`terraform/main.tf`, `deploy.sh`, `EVIL/x.md`. `vault/` admits only `Index/`, `Templates/` and
`[A-Za-z]+/.gitkeep` — generated notes stay outside. `SolSpireExperienceV3.tsx` / `V2` remain
forbidden by the separate `forbid` stage, asserted by test.

**Why the inventory grew substantially.** Auditing the tracked tree surfaced surfaces no pass had
enumerated: `arkadia-android/`, `sonata-android/`, `app/`, `architecture/`, `arkana_rasa/`,
`arkana_space/`, `bot/`, `codex/`, `collective/`, `corpus/`, `forge/`, `governance/`,
`openclaw/`, `orchestration/`, `providers/`, `sanctum/`, `static/`, `data/`, `archive/`,
`artifacts/`, `attached_assets/`, `.agents/`, `.bootstrap/`, `.replit_integration_files/`, and the
root config files (`entrypoint.sh`, `firestore.rules`, `github_corpus.py`, `railway.json`,
`vercel.json`, `.replit`, `.env.example`, `render.yaml`, `Dockerfile`). Every one was already
tracked on `main` and would have failed the gate the moment it was next touched. This is a
**classification** of existing surfaces, not a widening to new ones — no `forbid` rule was relaxed.

**New tests** (+5) in `tests/test_m02a_ci_gate_integrity.py`:

| test | asserts |
|---|---|
| `test_allowlist_covers_every_tracked_surface` | no tracked path is rejected |
| `test_workflow_allowlist_agrees_with_policy_on_every_tracked_surface` | mirror/policy admit identically |
| `test_vault_scaffold_is_admitted_but_generated_notes_are_not` | scaffold in, generated notes out |
| `test_allowlist_rejects_unknown_lookalike_roots` | lookalikes still rejected |
| `test_workflow_still_forbids_constitutional_dual_shell` | V2/V3 stay forbidden |

**Regression boundary held** — full suite, this worktree vs. baseline `a26af408`, same invocation:

| | passed | failed | skipped | errors | failing-node fingerprint |
|---|---|---|---|---|---|
| baseline `a26af408` | 903 | 49 | 12 | 2 | `e1ed0b1ea635` |
| after pass 3 | 918 | 49 | 12 | 2 | `e1ed0b1ea635` |

Passed rises by exactly 15 (the 10 accumulated new tests + 5 pass-3 tests); failed/skipped/errors
unchanged; the failing-node fingerprint is **byte-identical**. `tests/architecture` = 11 passed.
`py_compile` on changed Python is clean; `api/main.py` untouched (2519 lines, under the 2600 budget).

## 7. Composability risk (recorded)

The gate couples two copies of one policy: the inline `legit`/`forbid` regexes in
`.github/workflows/sg-02-fe-2-v.yml` and `scripts/cp10_mutation_boundary_policy.py`. Nothing but a
test forces them to agree, so an edit to one silently diverges from the other. Pass 3 narrows the
window (the drift test now checks **every tracked path**, not a hand-picked sample) but does not
remove the coupling. The structural fix — having the workflow invoke the tested policy module
instead of duplicating its regexes, so the shell literal survives only as a mirror assertion — is
the recommended next bounded task. It is deliberately **not** done here: it changes how the gate
executes, and this pass must not alter execution semantics while restoring a red `main`.

## 8. Merge-order hazard (recorded, not resolved here)

`docs/phase1/CONTINUATION_LEDGER.md` is appended to by **both** this PR (+96 lines) and PR #109
(+79 lines). They will conflict textually at the end of the file. Both branches are otherwise clean
and pass CP10 under this policy. Resolution is a human merge decision — **merge this PR first**,
then rebase #109 (or vice-versa) — not something this pass should decide unilaterally.

## 9. Remaining uncertainty

- The baseline 49 failures + 2 collection errors (`tests/test_autonomy.py`,
  `tests/test_render_codex.py`) are pre-existing debt and are **not** addressed here. Several
  appear to be stale assertions rather than defects; classifying them is a candidate separate
  bounded workstream (see `PARKING_LOT.md`).
- Frontend `pnpm build` was not run (environment-blocked at this pass); the change does not
  touch `web/`.
- PRs `#71`, `#6`, `#5` remain open and untouched; an existing draft branch
  `gate10/cp10-weaver-ci-gate-integrity` is already contained in `main` and was not reused to
  avoid assuming its intent.

## 10. Authorization required

Sovereign review and merge only. This branch makes no consequential external action.
