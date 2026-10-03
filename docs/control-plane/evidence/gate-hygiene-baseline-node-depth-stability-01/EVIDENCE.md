# EVIDENCE — gate-hygiene / baseline-node-depth-stability-01

**PR:** #215
**Branch:** `gate-hygiene/baseline-node-depth-stability-01`
**Base main:** `162f574b05dd839540d803aadda7608342618a84` (Merge PR #214)
**Head:** `ae6e0e04ef4b30af59180170b20d331194a364f2`
**State:** IMPLEMENTED — `READY FOR SOVEREIGN MERGE` (no merge performed)

## Defect

The recorded baseline node set (`tests/fixtures/baseline_node_set.txt`, canonical
fingerprints `a578a766…` / `8036fc06…`) is never compared to a live run: the guard in
`tests/test_baseline_fingerprint.py` re-hashes the fixture file only. A live CI-shaped run
therefore diverges from the published set silently.

Two nodes in `tests/test_agents_md_encoding_adjudication.py` read `AGENTS.md` at
`GATE2_PARENT_REV` (`7d79f38bd520a99637785db80bbe786192900d6d`), which is reachable only
through PR #147's ref — absent from a normal clone and from the CI checkout:

| Node | Guarded? | Behaviour when `7d79f38` absent |
|---|---|---|
| `test_gate2_parent_agents_md_repair_is_byte_identical_to_the_pipeline` | yes (`pytest.skip`) | SKIP |
| `test_shadow_adjudication_is_proved_by_the_oracle_not_the_codec` | **no** | **AttributeError** |

PR #212 excluded `test_gate2_parent_…` from the recorded set as "the clone-depth-dependent
node", but which of the two carries the failure depends on clone depth — so the published set
does not describe CI's live debt. Same defect class, one node over.

## Measurement

Reproduce a CI-shaped clone (no `7d79f38`):

```
git clone --no-local file://$PWD /tmp/ciclone2
cd /tmp/ciclone2
PYTHONPATH=archive/legacy_python python -m pytest tests/ --continue-on-collection-errors -q
```

| Clone | before (base) | after (this branch) |
|---|---|---|
| CI-shaped (no `7d79f38`) | 20 failed, 1 error; `test_shadow_…` extra vs recorded set | 19 failed, 1 error; **FAILED set matches the recorded 19 exactly** |
| Deep (with `7d79f38`) | 2 failed in file (`test_shadow_…`, `test_exit_code_…`) | 2 failed in file (`test_gate2_parent_…`, `test_exit_code_…`) |

`test_shadow_…` now SKIPs when the revision is absent and PASSes when present — its outcome no
longer varies with clone depth. The canonical fingerprint value and the recorded node set are
**unchanged**.

## Gates (this branch)

| Gate | Command | Result |
|---|---|---|
| Architecture fitness | `pytest tests/architecture -q` | 11 passed |
| CP10 fitness | `pytest tests/test_m02a_ci_gate_integrity.py -q` | 55 passed |
| Fingerprint guard | `pytest tests/test_baseline_fingerprint.py -q` | 17 passed |
| Mutation boundary | `git diff --name-only main...HEAD \| python scripts/cp10_mutation_boundary_policy.py --judge` | exit 0 |
| Boot compile | `python -m py_compile api/main.py` | OK (2582 lines) |
| CI check-runs at head | `commits/<sha>/check-runs` | Vercel Preview Comments success; Full-history secret scan success |

The CP10 workflow (`sg-02-fe-2-v.yml`) is path-filtered and does not cover this test file, so it
does not run on this PR — no gate is red.

## Regression boundary

Only `test_shadow_…` changes outcome, and only in clones lacking `7d79f38` (crash → skip).
No other node moves.

## Recorded, not fixed — separate bounded candidates (new scope needs authorization)

1. `test_gate2_parent_agents_md_repair_is_byte_identical_to_the_pipeline` — byte mismatch,
   visible only where `7d79f38` is present.
2. `test_exit_code_does_not_call_a_divergent_clean_file_verified` — asserts main's `AGENTS.md`
   is still corrupted; it is repaired, so the premise is false and the test fails in every clone.

The fixture also carries a hand-recorded `ERROR tests/test_autonomy.py` line that pytest does
not emit in a `-q` summary (the collection error is present but unnamed), which is why the
`test_autonomy.py` `ImportError` stays recorded rather than live-derived.

## Provenance

- Base main: `162f574b05` · branch head: `ae6e0e04`
- Changed: `tests/test_agents_md_encoding_adjudication.py` (2 lines)
- Prior work: PR #212 (`gate-hygiene/baseline-fingerprint-reconciliation-01`), PR #203
