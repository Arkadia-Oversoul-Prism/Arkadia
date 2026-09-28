# GATE-10 · CP10 mutation boundary — root narrative docs — Evidence

**Gate / workstream:** GATE-10 (GOVERNED EXECUTION) — CP10 verification gate integrity.
**Authorization:** Human sovereign. Merge is human-only; no merge, no push to `main`.
**BASE_MAIN:** `a26af408c269729a57d0a53c6ad39fcf0ca22fdf`
("Merge pull request #104 from Arkadia-Oversoul-Prism/solariun/thread-navigation-01")
**Branch:** `gate10/cp10-allowlist-root-docs`
**Status:** VERIFIED (fix proven against the exact failing change set; full-suite fingerprint unchanged)

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

**Full-suite fingerprint — regression boundary held.** `api/main.py` untouched, so no boot-code
compile gate is required; `py_compile` on both changed Python files passed regardless.

| | passed | failed | skipped | errors | failing/error nodes sha256 |
|---|---|---|---|---|---|
| baseline `a26af408` | 903 | 49 | 12 | 2 | `256204af…83fca` |
| after change | 907 | 49 | 12 | 2 | `256204af…83fca` |

Passed count rises by exactly 4 (the new tests); **failed/error fingerprint is byte-identical**.
No baseline failure was fixed, masked, or newly attributed.

## 5. Remaining uncertainty

- The baseline 49 failures + 2 collection errors (`tests/test_autonomy.py`,
  `tests/test_render_codex.py`) are pre-existing debt and are **not** addressed here. Several
  appear to be stale assertions rather than defects; classifying them is a candidate separate
  bounded workstream (see `PARKING_LOT.md`).
- Frontend `pnpm build` was not run (environment-blocked at this pass); the change does not
  touch `web/`.
- PRs `#71`, `#6`, `#5` remain open and untouched; an existing draft branch
  `gate10/cp10-weaver-ci-gate-integrity` is already contained in `main` and was not reused to
  avoid assuming its intent.

## 6. Authorization required

Sovereign review and merge only. This branch makes no consequential external action.
