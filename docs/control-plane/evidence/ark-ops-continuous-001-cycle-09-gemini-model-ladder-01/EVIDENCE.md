# ARK-OPS-CONTINUOUS-001 — cycle 09: one Gemini model ladder

Contract: `ARK-OPS-CONTINUOUS-001` (rev 2026-11-22).
Cycle started 2026-11-24T10:06Z. No merge, no deployment, no acceptance claimed.

## 1. State reconstructed from live sources

| item | measured |
|---|---|
| canonical `main` | `bb19aabda34d59594615b0279a45e9cbd3d8204d` (2026-11-22T17:23:48Z) |
| local `HEAD` / `origin/main` | identical to the above |
| production `/api/version` | `source_revision` = `bb19aabd…`, `revision_conflict: false` |
| `/health` | `200` `{"status":"radiant"}` |
| `main` check-runs | `boot-syntax`, `console-contract`, `economic-seam-engine` (`test`), `posture-currency`, `Full-history secret scan`, `engineering-scheduler` x2 — all `success`; `weaver_evolution` x5 `skipped` |
| open PRs | **38**, every one a draft |

The first `/api/version` probe of this cycle timed out at the client (`status=000`, 0 bytes);
the next probe of the same URL returned `200` / 643 B. Recorded as a cold-start read, not a
defect: `/health` answered throughout.

## 2. The defect, measured

`ruff --select F821,F811` over `api/ kernel/` returns **1** redefinition after this change —
`api/main.py:1734` `github_webhook`, which open PR #711 owns. The same scan surfaced the class
this cycle repairs.

Four Gemini text call sites issued **one** request to **one** model identifier:

| site | model | fallback |
|---|---|---|
| `api/ceo_chat_routes.py:113` | `gemini-2.0-flash-exp` | none |
| `api/arkana_signal_routes.py:210` | `gemini-3.8-flash` | none |
| `api/arkana_signal_routes.py:294` | `gemini-3.8-flash` | none |
| `api/ims_products.py:86` | `gemini-1.5-flash` (literal inside the URL) | none |

Every sibling surface iterated a ladder and continued past an unavailable model
(`api/main.py`, `api/pulse.py`, `api/arkana_signal_commune.py`,
`api/arkana_stream_routes.py`, `kernel/planner.py`). So one unavailable model turned
`/api/ceo/chat` into a `500` carrying the raw exception string, both Arkana Signal Gate 01 routes
into a `502`, and IMS Oracle synthesis into a permanent `[Oracle synthesis error: ...]` — while the
rest of the product degraded to the next model.

The ladder itself was copied **five** times, and the copies had already drifted:

```console
$ grep -rn "GEMINI_MODELS = \[" api/ kernel/    # before
api/pulse.py:28          # 3 entries — missing gemini-flash-latest
api/main.py:777          # 4 entries
api/arkana_signal_commune.py:6
api/arkana_stream_routes.py:26
kernel/planner.py:55     # as PLANNER_MODELS
```

This cycle makes **no claim** that any of those four identifiers has been retired. That would
need a provider call, and the repository also carries `gemini-3.1-flash-image-preview`, so a 3.x
text identifier is not implausible here. The verified defect is the absence of a fallback and the
divergence between copies, both of which are provable from the tree alone.

## 3. What changed

| path | change |
|---|---|
| `kernel/gemini_models.py` | **new** — the single `GEMINI_MODELS` tuple. Pure data, no httpx/fastapi import, so `api` and `kernel` can both import it without a cycle. |
| `api/main.py` | 5-line literal to `from kernel.gemini_models import GEMINI_MODELS` (**2597 to 2592** lines; budget 2600) |
| `api/pulse.py` | literal to import (gains the entry it had drifted out of) |
| `api/arkana_signal_commune.py` | literal to import |
| `api/arkana_stream_routes.py` | literal to import |
| `kernel/planner.py` | `PLANNER_MODELS` tuple to import |
| `api/ceo_chat_routes.py` | walks the ladder; falls back on `403`/`404`/`5xx` and transport error; `429` still rotates the key and returns `429` unchanged; drops the function-local `import httpx, re, json as _json` (the shadowing import) and the second `get_current_user` call, which verified the token twice per request |
| `api/arkana_signal_routes.py` | both routes walk `_SIGNAL_MODELS = ("gemini-3.8-flash", *GEMINI_MODELS)`, so the gate's own model is still tried first and the canonical ladder is the degradation path |
| `api/ims_products.py` | the URL became a `{model}` template and `_gemini` walks the ladder; still returns the error string when every model fails |
| `tests/test_gemini_model_ladder.py` | **new** — 12 nodes, the guard and its controls |
| `tests/test_arkana_signal_schema_{conformance,guard}.py` | their `_FakeResponse` gains `status_code = 200`; a fake of an httpx response that omits `status_code` is incomplete, and every existing assertion is unchanged |

Behaviour is preserved everywhere except the intended one: a surface now retries the next model
instead of failing. `/api/ceo/chat` reports the model that answered in its `model` field, so the
change from the `-exp` alias to the shared ladder is visible in the response rather than silent.

## 4. The guard, and why it is not decoration

`tests/test_gemini_model_ladder.py` asserts two properties over a domain derived from
`git ls-files -- api kernel` at test time, not restated:

1. **One definition.** No module under `api/` or `kernel/` assigns `GEMINI_MODELS`; the only
   definer is `kernel/gemini_models.py`.
2. **No single-model text call site.** Every module that constructs a Gemini
   `:generateContent` / `:streamGenerateContent` URL imports the canonical ladder, and no such
   URL contains a hardcoded `models/gemini-...` segment.

Two behaviour tests drive the real handlers with a stubbed HTTP boundary: a `404` for every model
except the last must still return a reply, and the models attempted must be the ladder in order.
Their **negative controls** reduce the ladder to one entry and assert the surface fails — that is
the pre-repair shape.

Detector controls feed the detectors the pre-repair source: a hardcoded `models/gemini-1.5-flash`
URL, a text call site with no ladder import, and a second `GEMINI_MODELS` assignment must each be
reported, and a correct module must be silent.

### Live negative controls (real files, not synthetic fixtures)

| control | measured |
|---|---|
| revert `api/ims_products.py` to `models/gemini-1.5-flash` **and** delete the import in `api/pulse.py` | `2 failed, 10 passed` — naming `{'api/ims_products.py': ['models/gemini-1.5-flash']}` and `api/pulse.py` |
| restore both byte-identically (`diff -q`) | `12 passed` |

## 5. Verification

```console
$ python -m py_compile api/main.py api/pulse.py api/arkana_signal_commune.py \
    api/arkana_stream_routes.py api/ceo_chat_routes.py api/arkana_signal_routes.py \
    api/ims_products.py kernel/planner.py kernel/gemini_models.py
ALL COMPILE

$ wc -l api/main.py
2592 api/main.py                     # budget 2600; was 2597

$ printf '<changed paths>\n' | python scripts/cp10_mutation_boundary_policy.py --judge
Mutation boundary PASS (M02A legitimate-surface + constitutional denylist)

$ python -m pytest tests/test_tool_execution_perimeter.py \
    tests/test_arkana_signal_schema_conformance.py tests/test_arkana_signal_schema_guard.py \
    tests/test_canonical_pulse.py tests/architecture -q -rEf
85 passed                            # includes architecture 11/11

$ PYTHONPATH=$PWD/archive/legacy_python python -m pytest tests/ -q -rEf \
    --continue-on-collection-errors
21 failed, 4260 passed, 22 skipped, 6 warnings, 1 error in 302.47s
```

Fingerprint of that run: **22** nodes, outcomes
`828d330f6d73ae7c1ed39bfbf4a3498eba040a1090ab4ce3f57ed720bb673b75`, ids
`75916d2c4765ae7391248fc9d25918002c174e3db7edcec04f1fc1230f72de1d`.

### Regression attribution by node identity

The same 11 failing files were re-run on a pristine `bb19aabd` worktree
(`git worktree add --detach`), with `--continue-on-collection-errors` so the CE-01 collection
error does not interrupt the session:

```console
$ cd /tmp/wt-main && python -m pytest <the 11 files> -q -rEf --continue-on-collection-errors
20 failed, 67 passed, 1 error
```

**21** nodes there, **22** here. `comm -3` yields exactly one branch-only node:

```
tests/test_static_ingestion_idempotency.py::test_open_loop_content_is_checksum_stable_through_a_vault_round_trip
```

It **passes in isolation on this branch** (`2 passed`) and its file is untouched by this change;
it is the order-dependent shared-runtime class already recorded for
`test_engineering_lab_agent_loop`, and open PR #698 owns it. Zero nodes are attributable to this
change. Every one of the 21 shared nodes sits in a file this change does not touch.

The `+12 passed` over the recorded `main` count is exactly this file's 12 nodes, measured with
`--collect-only` rather than inferred from the delta.

## 6. Limitations

- No provider call was made. The cycle does not claim any model identifier is retired or
  available; it claims only that these surfaces had no fallback and that the copies had drifted.
- `providers/gemini.py::models()` still advertises `gemini-1.5-pro` / `gemini-1.5-flash`, and
  `solspire/llm.py`, `solspire/provider_manager.py`, `weaver/llm.py` and `bot/**` still default to
  `gemini-1.5-flash`. Those are separate subsystems with their own model configuration and were
  **recorded, not repaired**: changing a default model is a product decision, and `models()` has
  no consumer in the tree (`grep -rn "\.models()"` returns one internal call in
  `providers/local.py`).
- `api/main.py` was edited, so the boot path was re-compiled; it was not started. A compile is not
  a boot.
- The full-suite absolute counts in this sandbox differ from CI's because
  `web/arkadia_console/node_modules` is absent here (10 environment-only nodes in
  `test_mission_lifecycle_adapter_contract.py`). Attribution is by node identity for that reason.

## 7. Next-action block

**Current state.** `main` = `bb19aabda34d59594615b0279a45e9cbd3d8204d`; production
`source_revision` identical, `revision_conflict: false`; architecture 11/11; the 22-node full-suite
set is 21 recorded nodes plus one order-dependent node that passes in isolation.

**Evidence.** This record; `tests/test_gemini_model_ladder.py`; the live negative controls in
section 4; the targeted `main` baseline in section 5.

**Blockers.** (a) Merge execution is human-only (GOV-03); the open queue is 38 drafts plus this
one. (b) CE-01 (`weaver.autonomy` module-vs-package collision) and FINDING F-01 are reserved to
the sovereign. (c) Whether `gemini-3.8-flash`, `gemini-2.0-flash-exp` and `gemini-1.5-flash` are
still served by the provider is **NOT TESTED** — no credential in this environment, so the ladder
ordering that preserves `gemini-3.8-flash` as Gate 01's first choice was kept rather than guessed
away.

**Authorized next action.** Human review. A later cycle may take up the recorded
`providers/gemini.py::models()` and `solspire`/`weaver` default-model drift, which needs a product
decision on which model each subsystem should prefer.

**Forbidden.** Merging; pushing to `main`; force-pushing; deploying; reordering the ladder to drop
a model identifier this cycle could not test; weakening the guard to make a surface green.

**Completion condition.** This cycle is complete when this record and the accompanying draft PR
are reviewable, with `main` unmodified and no merge, deployment or acceptance claimed.
