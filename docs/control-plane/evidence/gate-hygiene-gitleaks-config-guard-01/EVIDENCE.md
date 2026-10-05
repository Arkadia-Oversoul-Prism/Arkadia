# gate-hygiene — gitleaks config guard (2026-10-05)

Bounded hourly heartbeat. **No production code changed by this PR.** It closes one
measured, repository-owned defect and records the state the next heartbeat must resume from.

## 1. Reconstruction

- `BASE_MAIN` := `b01531b45dd7b1f5952e84d2cd3a4ad2980aa8c4` ("feat(weaver): add governed
  Google Workspace attention bus (#311)"), confirmed by `git fetch --all --prune` and
  `git log -1 origin/main`.
- Clone is **not** shallow (`git rev-parse --is-shallow-repository` → false).
- Working tree clean except one untracked runtime artifact (`attention-events.jsonl`),
  not staged.

### 1.1 Live CI on `main` @ `b01531b`

| check | result |
|-------|--------|
| `mvp2-validation` (run 37323507812, push) | **failure** |
| `Full-history secret scan` (run 37323507770, push) | **success** |

`main`'s own secret scan is green at `b01531b`: PR #311 removed the Google-key literal
from `arkadia-console-android/app/build.gradle.kts`
(`git show b01531b -- …/build.gradle.kts` → fallback changed to `?: ""`).

## 2. Bounded work implemented — root `.gitleaks.toml` guard

### 2.1 Defect (measured, reproduced)

Nothing validated the root `.gitleaks.toml`. A config that fails to parse makes
`gitleaks detect` abort **without scanning**, so the job reports a red secret scan that is
really a configuration fault. PR #311 carried a config whose multi-line `'''` entries never
closed on their line; this is the failure mode recorded in PR #312 §13.2/13.6 and proposed
there as work item 2.

Reproduced locally with stdlib `tomllib`:

```
live .gitleaks.toml parses: True
malformed shape ('''… without closing delimiter on the line):
    tomllib.TOMLDecodeError: Expected "'''" (at end of document)
unanchored shape: parses (and would over-suppress substring matches)
```

### 2.2 Change

`tests/test_gitleaks_config_guard.py` (new, 6 tests) — stdlib-only validator for the root
config, shared by the live-file assertion and the negative controls:

- parses as TOML;
- `[extend].useDefault == true` (default rules still run);
- `[allowlist].regexTarget == "secret"` (exempts the matched value, not the line);
- every `regexes` entry is a non-empty **single-line** string, **anchored** `^…$`, and
  compiles.

Negative controls feed the exact malformed shapes so the guard cannot be disarmed:
multi-line-start entry (does not parse), unanchored entry, `regexTarget = "line"`,
`useDefault = false`. A positive control asserts a well-formed config is accepted.

The guard embeds **no credential-shaped literal** — the placeholder used to exercise the
shape checks is a plain non-secret token.

### 2.3 Proof

| command | result |
|---------|--------|
| `python -m pytest tests/test_gitleaks_config_guard.py -q` | **6 passed** |
| `python -m pytest tests/architecture -q` | **11 passed** (unchanged) |
| `python -m py_compile api/main.py` | OK (boot code untouched) |
| `git ls-files \| python scripts/cp10_mutation_boundary_policy.py --judge` | exit 0 (PASS) |

## 3. Finding recorded, not repaired — Gate-05 / `ew_reviews` contradiction

`mvp2-validation` is red **on `main`**, and the cause is a contradiction between two merged
changes, not baseline debt:

- `tests/test_verification_review_boundary.py` (Gate-05) asserts that **no Review record
  type or table exists** — `test_verification_exists_without_any_review` reads
  `sqlite_master` and fails on `assert not any("review" in t.lower() for t in tables)`.
- PR #294 (merge `abac77d`) added `ew_reviews`, `store.review()`, and `ew_completions`
  referencing `review_id`, explicitly declaring `… ≠ Review ≠ Completion ≠ …` as preserved
  boundaries.

Measured on `b01531b`: `tests/test_verification_review_boundary.py` → **4 failed / 6 passed**
(`test_enterprise_verification_creates_no_review_record`,
`test_enterprise_chain_has_no_review_concept`,
`test_no_review_record_type_or_table_exists_anywhere_in_the_backend`,
`test_verification_exists_without_any_review`).

**Classification: `CONTRADICTED`.** Two canonical changes on `main` disagree about whether a
Review boundary may exist. Resolving it requires a sovereign decision (which boundary is
canonical); it is a sovereign-reserved failure per PR #312 §13.7 and is **not** repaired
here.

## 4. PR #312 secret scan — corrected analysis (do not repeat the tip-side rewrite)

PR #312 (`gate-hygiene/weaver-hourly-reconstruction-2026-10-05-01`, head `3e94a3d`) is red on
`Full-history secret scan` (run 37323507801). The finding is real and **tip-side**:
`gcp-api-key` at `docs/…/gate-hygiene-weaver-hourly-reconstruction-2026-10-05-01/EVIDENCE.md`
line 1015. The literal was introduced into that doc by commit `3e94a3d`.

The action's range is the PR's **own** commits, not a fixed base:

```
gitleaks cmd: gitleaks detect --no-merges --first-parent e06a7ab^..3e94a3d
e06a7ab = the branch's first commit (NOT on main)
```

So the 10 commits `e06a7ab^..3e94a3d` are the scanned set, and `3e94a3d` is inside it.
Per the repository's recorded gate-hygiene rule, **a tip-side redaction cannot clear a
range scan**, force-push is forbidden, and allowlisting a credential-shaped Google-key
literal is exactly what the repo forbids. PR #312 is therefore `BLOCKED`; the compliant
remedy is a **fresh branch that never introduces the literal** (this PR is one), not a
rewrite of #312's tip.

This PR's branch is cut from `main` `b01531b`, whose own scan is green, and introduces no
literal, so its scan must be green.

## 5. Classification

| item | class |
|------|-------|
| root `.gitleaks.toml` unguarded against malformed/over-broad entries | **VERIFIED** (reproduced) |
| guard implemented and proven (`6 passed`) | **VERIFIED** |
| architecture 11/11 · `py_compile` OK · CP10 exit 0 | **VERIFIED** |
| `mvp2-validation` red on `main` (Gate-05 vs PR #294) | **VERIFIED** (contradiction) |
| resolution of the Gate-05 boundary | **CONTRADICTED** — sovereign decision required |
| PR #312 secret scan | **BLOCKED** (tip-side, range-scoped; not fixable by tip rewrite) |
| Gate-2 deployment/build/browser boundary | `BLOCKED` / `UNKNOWN` (unchanged; provider-side) |

## 6. Next authorized action

1. **Sovereign decision** on the Gate-05 / `ew_reviews` contradiction: either retire the
   Gate-05 absence tests in favour of the PR #294 Review boundary, or revert the review
   surface. Not executed here.
2. Sovereign review + merge of this PR (guard) and of the open budget/CP10 companions
   (#308, #313) that repair `main`-measured defects.
3. **Do not** re-attempt a tip-side rewrite of PR #312's literal; open a clean replacement
   record if that evidence is still wanted.

**Forbidden for the next pass:** merging; pushing to `main`; allowlisting any
credential-shaped literal; repairing the sovereign-reserved Gate-05 boundary tests or
`weaver/enterprise_orchestration.py` inside an unrelated pass; duplicating PR #312.
