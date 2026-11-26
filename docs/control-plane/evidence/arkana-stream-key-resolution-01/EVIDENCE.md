# Arkana streaming surface — a misleading key fallback, and the guard for the class

**Observed:** 2026-11-24, cycle 09 of `ARK-OPS-CONTINUOUS-001`.
**Base:** `main` `bb19aabda34d59594615b0279a45e9cbd3d8204d` (local `HEAD` and
`GET /git/ref/heads/main` agree).
**Branch:** `gate-hygiene/arkana-stream-key-resolution-01`.
**Authority:** `MERGE_AUTHORITY := NONE`, `DEPLOY_AUTHORITY := NONE`. No merge, no push to
`main`, no deployment, no acceptance is claimed here.

## 1. The defect

`api/arkana_stream_routes.py` serves `POST /api/commune/resonance/stream`, the SSE path the
console's Arkana surface reads. Its comment states the intended chain:

```python
# Key resolution mirrors the non-streaming path (user → pool → env).
```

The code below it did not implement the `except` branch that comment implies:

```python
try:
    from api.main import _get_current_user, GOOGLE_API_KEY   # imported, never read
    ...
except Exception:
    GOOGLE_API_KEY = os.environ.get("GOOGLE_API_KEY", "")     # local, never read
```

`GOOGLE_API_KEY` is never read anywhere in that function, so the handler assigned a **dead
local** on the error path. Behaviour was unaffected (the real fallback is the `key_pool`
resolution two lines below), which is exactly why it survived: the code *looks* like an
environment-key fallback and is not one. A later edit that assumed the name was live — or a
reader reasoning about what happens when the `api.main` import fails — would be misled.

Measured with `pyflakes` over every tracked non-archive Python file:

```console
$ git ls-files '*.py' | grep -v '^tests/' | grep -v '^archive/' | xargs python -m pyflakes
api/arkana_stream_routes.py:135:9: local variable 'GOOGLE_API_KEY' is assigned to but never used
```

## 2. The repair

```diff
     try:
-        from api.main import _get_current_user, GOOGLE_API_KEY
+        from api.main import _get_current_user
 
         node_user = await _get_current_user(request)
@@
     except Exception:
-        GOOGLE_API_KEY = os.environ.get("GOOGLE_API_KEY", "")
+        logger.debug("[stream] per-user key resolution skipped", exc_info=True)
```

The fallback that actually runs is unchanged: `acquire_key()` from `api.key_pool`, then
`os.environ.get("GOOGLE_API_KEY", "")`. The error path now records *why* per-user resolution
was skipped instead of appearing to supply a key.

## 3. Why a guard, and what it binds

The module's pool reporting was correct and unpinned. `tests/test_arkana_stream_key_resolution.py`
(7 tests) binds three properties:

1. **the route is served** — `POST /api/commune/resonance/stream` is present in
   `api.main:app.openapi()["paths"]`, so the surface the console calls exists;
2. **no dead key fallback** — the module neither imports `GOOGLE_API_KEY` from `api.main`
   nor assigns it as a local;
3. **the pool contract holds** — `acquire_key`, `report_failure` and `report_success` are all
   imported from `api.key_pool`, and a behavioural test drives a provider `429` through
   `_stream_gemini` with only the HTTP boundary patched (`routes.httpx` replaced by a fake
   client; `api.key_pool` functions replaced by recorders) and asserts the charged key is
   cooled and **not** reported as a success.

Negative and polarity controls:

| control | input | expected |
|---|---|---|
| pre-repair shape | the measured `main` text, verbatim | detector reports **2** defects |
| missing outcome | `from api.key_pool import acquire_key, report_success` | reports `report_failure` |
| polarity | a correct pool import + env fallback | reports **nothing** |

Live negative control on the real file (repair reverted in place, then restored):

```console
$ python -m pytest tests/test_arkana_stream_key_resolution.py -q -rEf
FAILED tests/test_arkana_stream_key_resolution.py::test_no_dead_key_fallback_in_the_live_module
1 failed, 6 passed in 1.10s
$ cp /tmp/fixed.py api/arkana_stream_routes.py        # byte-identical restore
$ python -m pytest tests/test_arkana_stream_key_resolution.py -q
7 passed in 1.08s
```

## 4. Verification performed

| surface | command | result |
|---|---|---|
| boot syntax | `python -m py_compile api/arkana_stream_routes.py` | exit 0 |
| new guard | `pytest tests/test_arkana_stream_key_resolution.py` | **7 passed** |
| arkana + pool suites | `pytest tests/test_arkana_memory_ownership_containment.py tests/test_arkana_mode_workspace_contract.py tests/test_arkana_stream_key_resolution.py tests/test_key_pool.py tests/test_oracle_spine.py tests/test_prism_rec_arkana_provenance.py` | **51 passed** |
| gate integrity + architecture | `pytest tests/test_ci_gate_trigger_coverage.py tests/test_gate_filter_selection.py tests/test_boot_syntax_boundary.py tests/test_m02a_ci_gate_integrity.py tests/test_workflow_injection_boundary.py tests/architecture` | **292 passed** |
| mutation boundary | `printf '<paths>' \| python scripts/cp10_mutation_boundary_policy.py --judge` | PASS (exit 0) |
| console build | `corepack pnpm install --frozen-lockfile && corepack pnpm build` in `web/arkadia_console` | exit 0 (`tsc --noEmit` + vite, 170 modules) |

The full-suite baseline at `bb19aabd` was measured before the change:
**9 failed, 4260 passed, 22 skipped, 1 error** in 302.78 s — **10** failing/error nodes, every
one owned by an open PR or reserved (see the cycle-09 ledger, §3). This change adds no node to
that set: the only source file it edits is `api/arkana_stream_routes.py`, which no failing node
imports, and the new test file passes.

## 5. What this is not

Not a deployment observation, not production acceptance, and not a claim that the streaming
surface is healthy in production. It is a repository-source claim: the misleading fallback is
removed, the pool contract is pinned, and a behavioural control proves the guard can fail.
