# gate-hygiene — superseded-fingerprint-origin-01

**Gate:** gate-hygiene (baseline fingerprint reproducibility)
**Status:** IMPLEMENTED — sovereign review required
**Base main:** `162f574b05dd839540d803aadda7608342618a84`
**Branch:** `gate-hygiene/superseded-fingerprint-origin-01`
**Supersedes:** the "unreproducible by any convention" wording in
`docs/control-plane/evidence/gate-hygiene-baseline-fingerprint-reconciliation-01/`

## Objective

Explain — and guard — the origin of the baseline fingerprint pair
`a59453b8…` / `9a35c812…`, which the previous reconciliation pass recorded as UNKNOWN
("not reproducible by any convention"). The bounded question was: *is that UNKNOWN correct,
or is there a convention that reproduces it?*

## Finding — the pair IS reproducible (the earlier UNKNOWN was a measurement gap)

`a59453b8…` / `9a35c812…` are the fingerprints of the recorded 20-node baseline set **plus**
its depth-dependent *sibling* node:

```
tests/test_agents_md_encoding_adjudication.py::test_shadow_adjudication_is_proved_by_the_oracle_not_the_codec
```

That node dereferences the `GATE2_PARENT_REV` read **unconditionally**, so in a clone without
the PR-head revision `7d79f38…` it crashes (`AttributeError`) instead of skipping. A bare
clone's live run therefore reports it — 21 nodes, not the 20 of the recorded set — and that
21-node run hashes to exactly `a59453b8…` / `9a35c812…`.

Independent corroboration already in the repository: `AGENTS.md:429` records
`a59453b8…` as a **21-node** full-suite fingerprint. The 21st node is this sibling.

### Measured evidence (`162f574b05`, bare clone)

```
$ PYTHONPATH=<repo>/archive/legacy_python python -m pytest tests/ -q --continue-on-collection-errors
20 failed, 1308 passed, 15 skipped, 1 error
```

- Live failing/error nodes: **21** — one more than the recorded set.
- The extra node is exactly `...::test_shadow_adjudication_is_proved_by_the_oracle_not_the_codec`
  (ERROR — `AttributeError`, not a skip).
- Hashing the live 21 nodes reproduces `a59453b8…` (outcomes) / `9a35c812…` (ids).
- Hashing the recorded 20 nodes reproduces the canonical `a578a766…` / `8036fc06…`.

## Why the pair stays superseded

The pair is *reproducible*, but it is still clone-depth dependent — the sibling's outcome
flips between a plain clone and one carrying `7d79f38…`, exactly like the
`test_gate2_parent_…` node the recorded set already excludes. Republishing it would
reintroduce the defect the reconciliation removed. So: origin **explained**, value still
**superseded**.

## Change set

- `tests/test_baseline_fingerprint.py`
  - new `CLONE_DEPENDENT_SIBLING_NODE` constant.
  - new test `test_superseded_values_are_the_recorded_set_plus_its_sibling` — proves the
    origin from the recorded set, so the explanation cannot silently regress.
  - corrected the "unreproducible by any convention" wording in the module history comment,
    the `SUPERSEDED_*` comment, and the negative-control docstring/messages.
- `.bootstrap/01_STATE.md`, `MISSION.md`, `NEXT_AGENT.md`,
  `docs/phase1/CONTINUATION_LEDGER.md` — the "not reproducible" claims replaced with the
  corrected, explained origin.
- `docs/control-plane/evidence/gate-hygiene-baseline-fingerprint-reconciliation-01/WORKSTREAM_STATE.md`
  — the two rows reclassified from "unreproducible by any convention" to
  "recorded set + depth-dependent sibling (origin explained)".

## Verification

- `python -m pytest tests/test_baseline_fingerprint.py -q` → **18 passed**
  (was 17; the new origin test is the +1).
- `python -m pytest tests/architecture -q` → **11 passed** (unchanged).
- Recorded-set fingerprint unchanged: `a578a766…` / `8036fc06…` still reproduce.
- No production code touched; no boot code touched (`api/main.py` untouched).

## Regression boundary

Doc claims that asserted "unreproducible by any convention" are corrected. The canonical
fingerprint and the recorded node set are unchanged. The `SUPERSEDED_*` sets are unchanged,
so `test_published_docs_carry_the_canonical_fingerprint` still passes.

## Authorization required

Sovereign merge only. This pass does not merge, and does not select further work.

## Next bounded task

The two excluded nodes' own assertion defects — both pin the PR-head revision `7d79f38…`
and mis-handle its absence (one skips, one crashes) — remain a separate proposed workstream,
not executed here. No task ID assigned.
