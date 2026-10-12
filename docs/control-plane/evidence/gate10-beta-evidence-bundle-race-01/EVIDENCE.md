# GATE-10 — beta evidence bundle boundary (artifact-glob race)

**Revision examined:** `main` `6109c72ab9eedc2593d2cc6c50ebd01596c80072` (2026-10-12T06:36:48+01:00)
**Branch:** `gate10/beta-evidence-bundle-race-01`
**Status:** IMPLEMENTED (repository-source). No merge, no production claim.

## 1. Defect

`.github/workflows/n-atlas-external-beta.yml`, job `bundle` (`bundle-beta-evidence`):

```yaml
- uses: actions/download-artifact@v4
  with:
    path: evidence
    pattern: "*-evidence"        # also selects natlas-native-golden-evidence
    merge-multiple: true
- name: Verify bundle shape
  run: |
    python - <<'PY'
    import glob, json, sys
    files = glob.glob("evidence/*.json")
    statuses=[]
    for p in files:
        d=json.load(open(p))
        statuses.append(d.get("status"))
    if len(files) != 2 or any(s != "PASS" for s in statuses):
        sys.exit(1)
    PY
```

The `bundle` job is `needs: beta` with `if: always()`; the sibling `native-golden` job is
`needs.beta.result == 'success'` and uploads `natlas-native-golden-evidence`, whose artifact
**also ends in `-evidence`**. Both jobs become runnable at the same instant, so whether the
third artifact is in the directory when `bundle` lists it is a **race, not a shape**. The
verify step then asserts a *total* file count of 2.

The golden artifact's own file is named `native-golden.json`, so it is a foreign file with a
foreign status. It does not need to be `PASS` for the count assertion to fail.

## 2. Measured evidence

### 2.1 The red run (log, not inference)

Run `38233402572` (`pull_request`, head `a3c630a2`, branch `gate10/history-depth-ci-wiring-01`),
job `bundle-beta-evidence` = `114760741359`, started 2026-10-12T10:06:20Z, failed 10:06:27Z.
Verbatim log lines:

```
evidence files: ['evidence/native-golden.json', 'evidence/beta-01-english.json', 'evidence/beta-02-hausa.json']
statuses: ['PASS', 'PASS', 'FAILED']
##[error]Process completed with exit code 1.
```

The verify step failed on `len(files) != 2` — three files arrived. The golden artifact was
`FAILED`; the beta files were both `PASS`.

### 2.2 The race, not a shape (timing)

| run | bundle start→end | golden start→end | bundle result |
|---|---|---|---|
| `38088702840` | 21:43:43→21:43:49 | 21:43:43→21:44:24 | success (2 files) |
| `38232115080` | 09:47:26→09:47:30 | 09:47:26→09:48:12 | success (2 files) |
| `38233402572` | 10:06:20→10:06:27 | 10:03:48→10:04:30 | **failure (3 files)** |

The golden job started *before* the bundle job in the failing run (`10:03:48` vs `10:06:20`) —
the only run where the third artifact was already uploaded when the bundle listed the
directory. Same workflow, same SHA class, different interleaving. This is a timing-dependent
verdict, which is the definition of a race.

### 2.3 Artifact names (source)

| job | upload name | matches `*-evidence`? | matches `beta-*-evidence`? |
|---|---|---|---|
| `beta` (matrix) | `${{ matrix.id }}-evidence` → `beta-01-english-evidence`, `beta-02-hausa-evidence` | yes | yes |
| `native-golden` | `natlas-native-golden-evidence` | **yes** | no |
| `bundle` | `natlas-ps1-external-beta-evidence-bundle` | yes | no |

## 3. Repair

Two changes, both in the `bundle` job:

1. **Narrow the download** to `pattern: "beta-*-evidence"`, which selects the two beta
   artifacts and not the golden one.
2. **Assert the invariant the guard means** — the two named beta evidence files are present
   and each is `PASS` — instead of a total directory count:

```python
expected = {"beta-01-english.json", "beta-02-hausa.json"}
seen = {f.rsplit("/", 1)[-1] for f in files}
statuses = {f.rsplit("/", 1)[-1]: json.load(open(f)).get("status") for f in files}
if expected - seen or any(statuses.get(n) != "PASS" for n in expected):
    sys.exit(1)
```

A **subset** test (`expected - seen`), deliberately not an exact-set match: the narrowed
pattern already excludes the golden artifact, and the subset form stays correct even if the
download step's behaviour changes, because it can only fail on a *missing or non-PASS beta
file* — never on an extra foreign file.

## 4. Proof

### 4.1 Guard suite

`tests/test_natlas_beta_evidence_bundle_boundary.py` — **9 passed** (was 7).

New node added this pass: `test_count_detector_is_not_disarmed_by_an_incidental_expected`.

### 4.2 The repair against the exact red-run shape

Real `glob` + `json` body, run with the measured directory contents:

```
evidence files: ['evidence/beta-01-english.json', 'evidence/beta-02-hausa.json', 'evidence/native-golden.json']
statuses: {'beta-01-english.json': 'PASS', 'beta-02-hausa.json': 'PASS', 'native-golden.json': 'FAILED'}
exit=0
```

Exit 0 where the pre-repair form exited 1. The golden artifact is a foreign job's file and no
longer decides this job's verdict.

### 4.3 Scenario matrix

| scenario | contents | expected | observed |
|---|---|---|---|
| A | 2 beta files, both PASS | exit 0 | exit 0 |
| B | race: `native-golden.json` also present | exit 0 | exit 0 |
| C | a beta file missing | exit 1 | exit 1 |
| D | a beta file not PASS | exit 1 | exit 1 |
| E | empty evidence dir | exit 1 | exit 1 |

### 4.4 Live negative control

Reverting the **real** workflow file to the pre-repair shape (`pattern: "*-evidence"` and
`if len(files) != 2 ...`) and running the guard:

```
5 failed, 4 passed
FAILED ...::test_bundle_download_cannot_select_a_sibling_job_artifact
FAILED ...::test_bundle_verify_does_not_assert_a_total_file_count
FAILED ...::test_bundle_verify_asserts_both_beta_files_are_pass
FAILED ...::test_positive_control_repaired_shape_is_silent
FAILED ...::test_detector_bites_on_a_reintroduced_count
```

Restored byte-identically; SHA256 of the repaired workflow
`293954d498abf79812ec394bbc221831fd0f5d4eaf426c9a4c72b37744f534cc`; guard returns to 9 passed.
A synthetic fixture would not prove the detector reads the real file.

### 4.5 Detector-soundness control

`_asserts_bare_file_count` originally read `"len(files)" in script and "expected" not in script`,
so a rewrite re-adding `len(files) != 2` **beside** the repaired `expected` set would have
escaped detection. The detector now tests for the bare `len(files)` call, and
`test_count_detector_is_not_disarmed_by_an_incidental_expected` feeds it exactly that disarming
rewrite and requires it to be flagged.

## 5. Regression boundary

- `api/main.py` untouched. `python -m py_compile api/main.py` not required (no boot code).
- Architecture fitness: **11 passed** (`python -m pytest tests/architecture -q`).
- Full suite at `6109c72a`: **17 failed, 2872 passed, 20 skipped, 1 error** in 201.31s.
  Sorted FAILED/ERROR node set (18 nodes) sha256:
  `cdc1a04b7e7c006c6af0553804aa42157d00fc8f22d6ed40d44acff9cf2a7c89`.
  This branch adds one passing node and changes no failing node.
- CP10 mutation boundary: `PASS` for every path this change touches
  (`tests/test_natlas_beta_evidence_bundle_boundary.py`,
  `.github/workflows/n-atlas-external-beta.yml`, this evidence file).

## 6. Composition

No open PR touches `.github/workflows/n-atlas-external-beta.yml` or
`tests/test_natlas_beta_evidence_bundle_boundary.py`:

| PR | files |
|---|---|
| #455 | `docs/portfolio/BOUNDED_TECHNICAL_PORTFOLIO.md` |
| #479 | `AGENTS.md`, `lab/observatory/git.py`, `lab/service.py`, `tests/test_repository_remote_redaction.py`, evidence |
| #480 | `docs/portfolio/BOUNDED_TECHNICAL_PORTFOLIO.md` |
| #481 | `.github/workflows/knowledge-connection-lifecycle-guard.yml`, `tests/test_knowledge_shared_connection_lifecycle*.py`, `tests/test_sqlite_busy_timeout.py`, evidence |
| #482 | `.github/workflows/provider-routing.yml`, `AGENTS.md`, `tests/test_history_depth_ci_wiring.py`, evidence |
| #483 | `tests/test_ci_verdict_step_integrity.py`, evidence |

The workflow triggers on `pull_request: branches: [main]`, so CI exercises the repair on this
PR itself — the repaired bundle job runs in this PR's own run.

## 7. Remaining uncertainty

- The repair is verified as **repository source** and as a real-script execution against the
  measured directory contents. It is **not** a claim that the N-ATLAS external beta validation
  passes: that depends on the external EDNAi/HF Space, which is out of scope here.
- The race is *narrowed*, not eliminated in principle: a future job that uploads an artifact
  named `beta-*-evidence` would re-introduce it. `test_detector_bites_on_a_reintroduced_count`
  pins that case so it reddens the guard rather than passing silently.

## 8. Authority

`MERGE`, deployment, and production acceptance remain the human sovereign's. This record is
repository-source evidence only. PR #462 was closed by the sovereign and was **not** re-run,
re-opened, or modified by this pass.
