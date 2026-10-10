# PHASE 1 · Runtime Stabilization — PASS 2B · the baseline is dependency-sensitive

**Status:** OBSERVED — measurement record (repairs no product code, test, workflow)
**Date:** 2026-10-09
**Measured at:** `main` @ `f9ced6b6b974a6e19a8a19b4d1360b59b037a2c8`
**Gate:** Phase 1 (runtime stabilization) · feeds GATE-10 baseline honesty
**Continues:** `docs/control-plane/evidence/phase1-runtime-stabilization-02/EVIDENCE.md` (PR #385)
**Related:** `docs/control-plane/evidence/phase1-runtime-stabilization-03-baseline-honesty/EVIDENCE.md` (PR #386)
**Constraint:** evidence-only · human merge required · no push to `main`, no merge, no force-push

## 1. Objective

PASS 2 (PR #385) recorded the live `main` baseline as **16 failing/error nodes**
(`bfcfe592…` / `ed5e4714…`). PASS 3 (PR #386) ownership-classified all 16 nodes.
Neither pass asked whether the **node set is a property of `main` or a property of
the measuring environment**. This pass establishes that it is the latter in a
measurable, bounded way, and states the consequence for anyone replicating the
baseline.

This artifact repairs no product code, no test assertion, no workflow, no authority
path, and no mutation path.

## 2. The declared contract

`requirements.txt` treats the async plugin as a contract, not a coincidence:

```
# pytest-asyncio drives the async test modules (e.g. the API→enterprise
# authorization boundary in tests/test_authority_api_enterprise_boundary.py).
# CI installs pytest but not this plugin, so an async test collected without it
# is never awaited and asserts nothing -- a test that cannot fail is not
# coverage. Declared explicitly so the async boundary is actually exercised.
pytest-asyncio
```

(also `jsonschema`, declared for the ARK-01 signal-schema conformance tests.)

## 3. Measurement — one uninstalled declaration moves the node set

Reproduced with the PASS 2 command
(`PYTHONPATH=<repo>/archive/legacy_python python -m pytest tests/ -q -rEf --continue-on-collection-errors`),
isolating the plugin with `-p no:asyncio`:

| condition | summary | failing/error nodes | outcomes fingerprint |
|---|---|---|---|
| `pytest-asyncio` installed (canonical) | `15 failed, 1854 passed, 20 skipped, 1 error` | **16** | `bfcfe592…` |
| `-p no:asyncio` (plugin disabled) | `22 failed, 1848 passed, 19 skipped, 1 error` | **23** | `f3a01107…` |

**The delta is exactly 7 nodes, all from one missing plugin:**

```
tests/test_arkana_signal_schema_conformance.py::test_route_emits_a_schema_conforming_signal
tests/test_arkana_signal_schema_conformance.py::test_route_normalizes_ordinary_model_output
tests/test_arkana_signal_schema_conformance.py::test_route_rejects_an_invalid_audio_payload
tests/test_arkana_signal_schema_guard.py::test_route_emits_a_conforming_signal
tests/test_arkana_signal_schema_guard.py::test_route_normalizes_ordinary_model_output
tests/test_authority_api_enterprise_boundary.py::test_api_approval_does_not_create_enterprise_authorization_without_explicit_bridge
tests/test_natlas_developer_lab.py::test_native_natlas_route_live_external_gradio
```

Each is an `async def` carrying `@pytest.mark.asyncio`. Without the plugin they fail
with pytest's explicit diagnostic, not a product assertion:

```
async def functions are not natively supported.
You need to install a suitable plugin for your async framework, for example:
  - anyio  - pytest-asyncio  - pytest-tornasync  - pytest-trio  - pytest-twisted
```

### 3.1 Negative control — the plugin dependency is real, not incidental

Feeding the detector the *pre-plugin* condition reproduces the defect deterministically:

```
python -m pytest tests/test_arkana_signal_schema_conformance.py \
    tests/test_arkana_signal_schema_guard.py \
    tests/test_authority_api_enterprise_boundary.py \
    tests/test_natlas_developer_lab.py -q -p no:asyncio
# -> 7 failed, 40 passed
```

With the plugin present the same files are `44 passed, 20 skipped` (via the schema
suites) and the async boundary test passes. The 7-node delta is entirely attributable
to dependency availability, so a fingerprint measured without the plugin is not a
statement about `main`.

## 4. The same gap sits in the executable guard

`.github/workflows/baseline-fingerprint.yml:60` installs
`pip install pytest pyyaml` — omitting the declared `pytest-asyncio` and `jsonschema`
that `requirements.txt` explicitly introduced. The workflow's own step runs only
`tests/test_baseline_fingerprint.py` and `tests/test_baseline_fingerprint_ci_wiring.py`,
which do not import async modules, so CI stays green while the environment the
repository declares is not the environment CI builds. (The broader CI suite workflows
that carry the async boundary — e.g. `arkana-signal-conformance.yml` — *do* install
the plugin, so the gap is per-workflow, not repository-wide.) This mirrors the
recorded `pdfminer.six` / `cryptography` lesson: an undeclared dependency let an
observation "compare a route set missing four operations against production and could
not distinguish an environment gap from a source divergence."

## 5. Consequence and recommendation

Any baseline fingerprint is only meaningful together with the requirement set it was
measured under. Two operators on the same `main` SHA can legitimately report 16 or 23
nodes depending on whether they installed `requirements.txt`. Reproduce the canonical
16-node pair (`bfcfe592…` / `ed5e4714…`) with the **full** declared requirements,
not `pip install pytest`.

Proposed (not executed here — separate bounded workstream):

1. `gate-hygiene/ci-requirements-parity-01` — install `-r requirements.txt` in
   `baseline-fingerprint.yml` (and the other pytest workflows still on bare
   `pip install pytest`), or pin `pytest-asyncio`/`jsonschema` explicitly, so the
   declared contract and the CI contract agree.
2. `gate-hygiene/baseline-env-provenance-01` — have the fingerprint tooling record the
   installed `pytest-asyncio`/`jsonschema` versions alongside the hash, so a fingerprint
   is never quoted without its environment.

## 6. Regression boundary

- No product code, test, workflow, mutation path, or authority path changed.
- Changed paths are this directory only.
- The canonical `main` fingerprint (`bfcfe592…` / `ed5e4714…`, 16 nodes) is **unchanged**
  and reproduced by the canonical script at `f9ced6b6`.

## 7. Authority boundary

Read-only measurement and in-repo evidence persistence on a dedicated branch. **No
merge, no push to `main`, no force-push.** Human authority is required to merge. This
pass does not claim production parity and does not promote its own result to acceptance.
