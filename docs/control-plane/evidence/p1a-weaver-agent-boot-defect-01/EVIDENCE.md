# P1-A class boot defect — `weaver/agent.py` — EVIDENCE

Bounded workstream: `gate-hygiene/p1a-weaver-agent-boot-defect-01`
Base main at pass start: `ae847ddfd4bd01bd61e3c26545f90f3fe217f5a5`
Observed: 2026-10-02 (UTC)

## 1. Defect (VERIFIED)

`weaver/agent.py` on `main` was not importable. Line 75 carried a **literal two-character
`\n` escape sequence** instead of real newlines:

```
pres = invoke_provider(\n            ProviderRequest(\n                provider=model,\n ...
```

This is a JSON-escape artifact — a multi-line call that was serialized with escaped
newlines and committed verbatim as source. Python reads `\n` outside a string as a line
continuation followed by `n`, producing:

```
SyntaxError: unexpected character after line continuation character
```

Introduced by `55ccc07` ("feat: task-aware multi-provider Weaver routing (#177)"), whose
diff replaced the single-line call with the escaped blob.

### Blast radius

`weaver.agent` is imported by `weaver/transaction.py` and `weaver/execution.py`, so the
SyntaxError propagated through the governed-execution import chain:

| module | before fix |
|---|---|
| `weaver.agent` | SyntaxError |
| `weaver.transaction` | SyntaxError (via `weaver.agent`) |
| `weaver.execution` | SyntaxError (via `weaver.agent`) |
| `weaver.session` | OK (does not import `weaver.agent`) |

Repo-wide scan: **`weaver/agent.py` was the only tracked `.py` file failing
`py_compile`** (`git ls-files '*.py'` → 1 SYNTAX-FAIL). No second copy of the artifact
exists in the tree.

## 2. Repair (mechanically determined)

The escaped blob is the *intended* #177 multi-line call; the correct form is recovered by
replacing the literal `\n` sequences with real newlines. The keyword arguments are valid —
`ProviderRequest` declares `task_type: str = "general"` and
`required_capabilities: tuple[str, ...] = ("chat",)` (`weaver/provider.py:32-42`), so the
repair restores the feature #177 intended rather than reverting it.

## 3. Companion defect in the same commit (VERIFIED)

`tests/test_weaver_k2.py` — added by the same commit `55ccc07` — uses `ProviderResult`
(line 272, inside `test_explicit_provider_is_not_silently_rerouted`) but never imports it:

```
NameError: name 'ProviderResult' is not defined
```

`ProviderResult` is a public class in `weaver.provider` (`weaver/provider.py:45`). The
missing import is added to the existing `from weaver.provider import (...)` block. Without
it the test masks whether #177's routing policy actually honours explicit providers.

## 4. Verification

| command | result |
|---|---|
| `python -m py_compile weaver/agent.py` | OK |
| `python -c "import weaver.transaction, weaver.execution"` | OK (was SyntaxError) |
| `pytest tests/test_weaver_k2.py -q` | **14 passed** (was 1 failed / collection error before) |
| `pytest tests/architecture -q` | **11 passed** — unchanged |
| `git ls-files '*.py' \| py_compile` | 0 syntax failures (was 1) |

### Fingerprint — honest baseline (deps installed, fix absent)

Measured on `main` `ae847dd` with `requests`/`httpx`/`google-generativeai` present so the
SyntaxError is the only variable:

```
52 failed / 1146 passed / 17 skipped / 8 errors   (60 FAILED+ERROR nodes)
sha256("\n".join(sorted(node ids)) + "\n") = b9f600c3317953610cd987617b3d30aa2ee666f8e8202083b6ad78aca70ad70a
```

### Fingerprint — after repair

```
23 failed / 1231 passed / 17 skipped / 1 error    (24 FAILED+ERROR nodes)
sha256("\n".join(sorted(node ids)) + "\n") = 3c3e5a15f4f25b07b0a2d8087da2b27eb1f2d77ad90f549c6c830edc290e6c5f
```

**Node-set delta: 36 resolved, 0 new.** Strictly a reduction; no failure was introduced.

### Note on the earlier 61-node measurement

A first baseline taken before `requests` was installed read **61 nodes** and differed from
the 60-node honest baseline by exactly one node
(`FAILED tests/test_weaver_mvp2_exec_binding.py::test_eb_valid_reaches_k15_seam`), which is
order/state sensitive in that module. The honest 60-node baseline is the one used above.
Both agree that the repair is strictly a reduction.

## 5. Pre-existing failures recorded, NOT fixed (out of scope)

The 24 remaining nodes are pre-existing `main` debt, unchanged by this pass. Two are worth
naming because they are allowlist/governance debt rather than product debt:

- `tests/test_m02a_ci_gate_integrity.py` (3 nodes) — the CP10 `LEGIT` allowlist omits the
  tracked path `reconciliation/UPSTREAM-CAUSAL-CONTINUITY-01.md`. Confirmed pre-existing on
  clean `main` (`git stash` → same 3 failures). This is the documented CP10
  allowlist-omission class: a path the repository genuinely tracks, so the next merge that
  touches it reddens the gate. **Separate bounded workstream** — not repaired here.
- `tests/test_spiral_grove_activity_runtime.py::test_runtime_dispatches_all_eight_kinds_to_deterministic_renderers`
  — the known SG-04 `ActivityRuntime` regression (see `AGENTS.md`, Gate GATE-01).

## 6. Authority

No merge, no push to `main`, no force-push. Human-only merge. This pass changes no
authority, identity, K15/K3 governance, or mutation path.
