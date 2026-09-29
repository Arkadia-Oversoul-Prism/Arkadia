# WORKSTREAM STATE — gate hygiene / baseline test debt

> Persisted so the next hourly heartbeat reconstructs from evidence, not memory.
> Reconstruct live state anyway (rule 14) — do not trust this file over the repository.

## Fingerprint (measured, not remembered)

```
main 67a660c : 54 failed / 964 passed / 10 skipped / 2 collection errors   (56 nodes)
architecture : 11/11
py_compile api/main.py : pass    (api/main.py = 2519 / 2600 lines)
vite build   : environment-blocked (no npm registry access)
```

Re-measure at the start of every pass; the automation contract's `main := 6038989` /
`804 passed / 12 skipped` / `architecture 9/10` figures are stale.

## Node inventory (reproducible)

```bash
PYTHONPATH=<repo>/archive/legacy_python python -m pytest tests/ -q \
  -p no:cacheprovider --continue-on-collection-errors \
  | grep -E '^(FAILED|ERROR) ' | sed 's/ - .*//' | sort
```

Compare the sorted node list against the baseline to attribute a delta by *name*, never
by count alone — counts move when tests are added.

## Classification ledger

`docs/control-plane/evidence/gate-hygiene-baseline-test-debt-classification-01/BASELINE_TEST_DEBT_CLASSIFICATION.md`
is the single source of truth for node→bucket assignment (51 nodes at `a26af408`).

Bucket counts at that pass: **STALE_ASSERTION 35**, **DRIFT 10**, **ENV/ARTIFACT 2**,
**REAL_DEFECT 1**, **COLLECTION_ERROR 2**.

## Repair queue (`SH-*` — proposed, sovereign authorizes)

| id | task | bucket | state |
|---|---|---|---|
| `SH-01` | `SOLSPIRE_PROJECTS_DB` env leak in `tests/test_echofeild_aggregator.py` | REAL_DEFECT | **already fixed on main** — do not re-do |
| `SH-02` | migrate the 35 stale string assertions, in bounded batches | STALE_ASSERTION | **6 / 35 repaired** (SCI/nexus family) |
| `SH-03` | `"DERIVED"` vs `"DERIVED_BOUNDED_SEMANTIC"` contract split | DRIFT | awaits product decision |
| `SH-04` | is `CapabilityRegistry` cycle detection reachable? | DRIFT | not started |
| `SH-05` | fate of `test_gate_serve_script` / `test_gate_status` | ENV | sovereign call |
| `SH-06` | should `steward_filter` stem-match `transcend*`? | STALE_ASSERTION | awaits product judgement |
| `SH-07` | shared-session key in `ArkanaCommune.tsx` (`test_m02_reasomate_truth`) | DRIFT (high) | awaits architectural gate |
| `F-01` | `test_no_firebase_persistence_in_gate` — `sessionStorage` proxy no longer measures its "no cloud persistence" intent (gate has 0 firebase refs; storage is ephemeral handoff) | DRIFT (proxy-invalidation) | **sovereign decision** — do not silently loosen |

## Next bounded task

Continue `SH-02`: the next batch of stale string assertions. Suggested dense groups
(all pre-classified `STALE_ASSERTION`, all test-only):

- `test_prism_pass_c_surface_ownership.py` (6 nodes)
- `test_solariun_experience_consolidation_01.py` (3 nodes)

Unchanged rule: re-point the assertion at the surface that now owns the behaviour, and
run a negative control proving the repaired assertion can still fail. Test-only edits;
never touch `api/main.py`, `LAYER_MAP.py`, ADRs, or governance files from this workstream.

### `test_prism_pass_c_surface_ownership.py` — needs a HELPER rewrite, not just string edits

Its 6 nodes all fail at the same place: `_block(view)` (`:20-24`) matches
`{view === '<v>' && (\(.*?\)\n\)}` against `App.tsx`, but `App.tsx` now resolves views via
a `requested`/`next` mapping with an explicit redirect, so no such JSX block exists for
`spiral-codex`, `personal-echofeild`, `knowledge-os`, `codex`, `loops`.
This is a **parser-helper rewrite** with a materially larger blast radius than the batch-1
string edits — treat it as its own bounded pass, and re-derive the assertion intent for each
view from `App.tsx`'s real routing table rather than re-fitting the old regex.

## ⚠ FINDING F-01 — `test_no_firebase_persistence_in_gate` is a PROXY-INVALIDATION, not a relocation

`tests/test_ais_w2_living_gate_grove_handoff.py::test_no_firebase_persistence_in_gate`
(`:74`) fires on the **negative** assertion `assert "sessionStorage" not in src` against
`web/public_prism/src/pages/LivingGate.tsx`.

**Verified against live source:**

- `LivingGate.tsx` contains **zero** `firebase` / `firestore` references (`grep -c` → 0).
  The test's *stated* intent — no cloud persistence, no silent identity creation in the
  Living Gate — is therefore still satisfied.
- The `sessionStorage` usage is deliberate, local and **ephemeral** (per-tab, cleared on
  close): the session-scoped `HANDOFF_KEY` / `PORTFOLIO_KEY` namespace constants (`:61-62`,
  values `arkadia.ais.diagnostic-handoff.v1` / `arkadia.ais.capability-portfolio.v1`),
  introduced by the AIS feature commits `b822b95` → `c1073a4` → `f68cbf7`.

**Why this was NOT repaired in this pass.** The assertion's *mechanism* (`sessionStorage`
absent) no longer measures its *intent* (no cloud persistence). Repair requires rewriting a
**negative guard** — i.e. choosing what the gate is still forbidden to do. That is a
governance call about a persistence/identity boundary, not test hygiene. Silently loosening
it is exactly the "weaken the gate to make it green" failure mode this repo has been burned
by. Classify **DRIFT (needs product decision)**, hand to the sovereign, do not edit.

**Proposed shape for the sovereign to approve** (not applied): replace the crude proxy with
the actual intent — assert no `firebase`/`firestore` import and no durable cloud write in
`LivingGate.tsx`, while explicitly permitting ephemeral same-tab handoff keys. Note the
sibling assertion `"localStorage.setItem" not in src` currently **passes** and must not be
disturbed.

**Same family, same caution.** Among that file's other nodes, `test_ims_lineage_preserved`
(`:88`) already passes; the remaining failures mix relocation (`'/api/pulse/analyze'`,
`'Open Spiral Grove'`, `onEnterSpiralGrove={...}` in `App.tsx`) with a second negative guard
(`test_no_firebase_persistence_in_gate`). Split the file: relocation nodes are safe `SH-02`
work; negative guards go to the sovereign. Do **not** batch them.

## Open PRs (at the end of this pass)

- **#124** — this pass (`gate-hygiene/baseline-stale-assertion-repair-sci-nexus-01`),
  READY_FOR_SOVEREIGN_MERGE.
- **#123** — `aeas/frontend-seam-map`, **separate** diagnosis-only workstream. Not a duplicate
  of this work. Note: it declares a files-changed surface including
  `.github/workflows/`; if a PR ever modifies the CP10 workflow, **re-run the boundary judge
  and `test_m02a_ci_gate_integrity.py`** — a new rejection path would trip the hard stop.

This workstream took no new authority from either.

## Boundaries

Test-hygiene workstream holds **no** authority over merge, authorization, identity,
authority-model, or constitutional architecture. It must not create a second mutation or
authorization path (`examples: CP10 boundary judge`, `APS`/`ASI` status surfaces).

## Pass N+1 — secret-scan remediation (false-positive de-risk)

**Trigger.** `Full-history secret scan` (`.github/workflows/security-secret-scan.yml`,
`gitleaks-action@v3`) failed on run `36526464261` at commit `a81d9ff`. Reporting identity:
RuleID `generic-api-key`, entropy `3.801378`, secret redacted.

**Finding.** The finding pointed at **this file**, line 84 — the F-01 evidence quote, not at
any source file. It was a **false positive**: the flagged text was the prose fragment
reproducing the `HANDOFF_KEY` assignment from the canonical source — a namespace identifier,
carrying no credential material.

**Root cause of the miss.** The scan is **range-scoped**, not whole-history:
`gitleaks detect --log-opts="--no-merges --first-parent <merge-base>^..<head>"`. The same
namespace literal already lives on `main` in
`web/public_prism/src/pages/LivingGate.tsx` and `FutureSkillsChallenge.tsx`, and has done so
since the AIS commits (`b822b95`, 2026-08-30); it never trips the gate because those ranges
were scanned before the literal existed in a diff gitleaks re-inspected. The new evidence doc
therefore re-introduced a *known-benign* literal into a freshly-scanned range. The gate is
not wrong — this doc was the first pass to feed it an assignment-shaped literal in a new
commit.

**Remediation (reversible, evidence-preserving).** Rewrote the sentence to name the
constants and their provenance without reproducing the assignment form. The F-01 finding,
the quoted intent, and the sovereign handoff are unchanged — only the literal's formatting.
The literal itself remains canonical in the cited source files; it is deliberately **not**
being edited, allowlisted, or suppressed (that would be weakening the gate).

**Verification.**

- `gitleaks dir` over the changed evidence directory -> clean (exit 0), same detector and
  rule set as the failing job.
- Architectural + CP10 fitness: `tests/architecture` + `test_m02a_ci_gate_integrity.py`
  -> **60 passed**, unchanged from the batch-1 baseline (no regression, no newly-omitted
  CP10 surface; no new tracked path introduced).
- `python -m py_compile api/main.py` -> OK (boot code untouched; P1-A guard observed).
- CI re-run on the pushed revision is the binding evidence.

**Uncertainty.** The full-range job result can only be confirmed by the CI run on the new
revision; local `gitleaks dir` is a strong but not identical reproduction (it scans the
working tree, the job scans the commit range). No further literals of this shape were found
in this pass's evidence directory.
