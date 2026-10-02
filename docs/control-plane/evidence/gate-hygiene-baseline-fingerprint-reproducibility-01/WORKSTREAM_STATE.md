# WORKSTREAM STATE — gate-hygiene / baseline-fingerprint-reproducibility-01

Pass: `gate-hygiene/baseline-fingerprint-reproducibility-01`
Date: 2026-10-02 (UTC)
Base main: `702b63ae633180034d1a36aa68b090541af6dae3`
Branch head: `e66bb231c1dd3c15fd4f92dfe8fe678f1b7a215a`
PR: #203 — **MERGED** (squash) into main as `6dbdde52bdd115293044845200f7a2220bc6d418`
Post-merge main: `6dbdde52bdd115293044845200f7a2220bc6d418`

## Active workstreams

| WS | Branch / PR | State |
| --- | --- | --- |
| baseline fingerprint reproducibility | `gate-hygiene/baseline-fingerprint-reproducibility-01`, PR #203 | **MERGED** as `6dbdde5`; post-merge verification 21 passed (10 new + 11 architecture) |
| baseline fingerprint state persistence | `gate-hygiene/baseline-fingerprint-state-02` (this branch) | IMPLEMENTED — this file; the pass-01 branch was squashed, so its post-squash state commit could not land |
| Gate-2 production parity | `gate-hygiene/gate2-production-parity-02`, PR #143 | BLOCKED on provider auth (unchanged) |

An intervening merge landed during this pass: PR #202 (`fix/solariun-blank-page-user-hook`)
merged as `937e162` at 09:36:53, one minute before PR #203. It is a normal squash-merge of a
PR, not a direct push to `main`, and touches only
`web/public_prism/src/components/solspire/SolSpireExperience.tsx` — no overlap with this pass.

## 1. Baseline fingerprint recorded at pass start

Measured on `702b63ae` in this environment.

| Suite | Result |
| --- | --- |
| `python -m pytest tests/architecture -q` | **11 passed / 0 failed** |
| `python -m pytest tests/ -q --continue-on-collection-errors` | **20 failed / 1242 passed / 17 skipped / 1 error** |
| `python -m py_compile api/main.py` | OK |
| `api/main.py` line count | 2571 (budget 2600) |

Failing/error node set: **21 nodes**.

| convention | sha256 |
| --- | --- |
| outcomes `"<OUTCOME> <nodeid>"` | `a59453b8a1e5a02899f469cf6ea7db9b5eaae658050261e1405c394cb0f3cf6f` |
| node set `"<nodeid>"` | `9a35c8122188e272ec5769d7a8f5cdba6160b4f2f1fba8a840019a487c1bcc22` |

Both are reproduced by `python scripts/baseline_fingerprint.py <pytest-log>`. The
node set is byte-identical at `64cbe74`, `481afa1` and `702b63ae`, so
`64cbe74 → 481afa1` is confirmed regression-free.

The passed count reads 1240 or 1242 on the same tree depending on ordering — the
documented order-dependent
`test_engineering_lab_agent_loop.py::test_agent_loop_does_not_mutate_repository`.
Attribute regressions from the failing/error node set only, never from the passed count.

## 2. Closed this pass

The recorded fingerprints `a7687fad…`, `d7ff35b2…687036` and `a59453b8…` were
non-reproducible. Resolved: the documented derivation named the node-set convention
while the value used the outcomes convention, and ids had been captured from `pytest -q`
output including the terminal-width-truncated assertion reason. 210 derivations were
tested; exactly one reproduces `a59453b8…`.

## 3. Next bounded task (classified, not started — separate pass)

`tests/test_autonomy.py` is the single collection **error** node in the baseline set.
Root cause, measured:

```
ImportError: cannot import name 'load_autonomy_config' from 'weaver.autonomy'
```

Both a module and a package exist and are tracked:

| path | contents |
| --- | --- |
| `weaver/autonomy.py` | defines `load_autonomy_config`, `validate_autonomy_config`, `run_scheduled_once` |
| `weaver/autonomy/__init__.py` | docstring + `__version__`/`__cycle__`/`__status__` only |

The package **shadows** the module (packages win over same-named modules in the same
directory), so the import can never resolve. The duplication is Genesis-era
(`9ab26fc`, `18cd657`), i.e. pre-existing baseline debt, not introduced by this pass.

Not repaired here, deliberately: `weaver/autonomy` is a governance-adjacent surface
(conditional autonomy, guards, proposal engine) and the choice between deleting the
stale module and folding its functions into the package is an architectural decision.
It needs its own bounded workstream with an explicit decision on which artifact is
canonical. Recorded so the next pass starts from a diagnosis rather than a bare name.

## 4. Authority boundary

Sovereign merge authority. No merge performed; no push to `main`.
