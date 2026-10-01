# CE-01 — the `weaver.autonomy` collision, measured disposition

**Workstream:** `gate-hygiene` (GATE-00 baseline hygiene, pre-gate engineering envelope)
**Bounded question:** the ledger adjudicates the `weaver/autonomy.py` (module) vs
`weaver/autonomy/` (package) collision as **"CONTRADICTED as autonomous work — needs a
sovereign decision"** (`docs/phase1/CONTINUATION_LEDGER.md:393,1331`), and PR #149 §"Corrections
to recorded state" repeats that CE-01 *"needs a sovereign decision"*. **No artifact in the
repository carries that decision.** What is the disposition, and is there any bounded action
this envelope may take?

**Classification:** `VERIFIED` (repository-layer). **Evidence-only — no test, source, workflow,
governance, constitutional, or boot file is modified.**
**Base:** `002b189dd95e41c9b4f4cca33d08b4121453d289` (`main` @ merge of #141).
**Branch:** `gate-hygiene/ce01-autonomy-collision-disposition-01`.

---

## 1. Answer

**The ledger is correct and this pass strengthens it. CE-01 is a defect, not hygiene debt, and
it is NOT repairable inside this envelope.** The bounded deliverable is the disposition itself —
which the queue had recorded as *needed* but had not yet written down.

Four independently-measured facts settle it:

1. **The collision is real and is the sole cause of the collection error.** `from
   weaver.autonomy import load_autonomy_config` raises `ImportError` because the package
   directory shadows the module.
2. **Un-shadowing would NOT repair the test.** Run against the un-shadowed module, the test's
   own assertion still fails — the collection error merely *masks* a substantive failure.
   Repairing the collision therefore does not reduce baseline debt; it converts one red node
   into two.
3. **Un-shadowing would re-open an autonomous commit surface.** `run_scheduled_once` drives
   `RecursiveEngine` → `weaver.agent.agent_run`, which constructs commit messages. It is
   currently dormant behind three stacked barriers — all of which are *config*, and all of
   which are invertible by a single JSON edit.
4. **The other side of the collision is load-bearing.** `weaver/session_kernel.py:11` imports
   `weaver.autonomy.guard` in **production**. Deleting the package — the move a "kill the
   dead module" instinct would reach for — breaks production.

Because (2) removes the hygiene justification and (3) invokes the authority model's
`AUTONOMOUS MUTATION PATH` reservation, the choice between the two canonical shapes is a
**sovereign decision**. Nothing here may be auto-repaired.

---

## 2. The collision — measured

```
$ python -c "from weaver.autonomy import load_autonomy_config"
ImportError: cannot import name 'load_autonomy_config' from 'weaver.autonomy'
  (/workspace/project/Arkadia/weaver/autonomy/__init__.py)

$ python -m pytest tests/test_autonomy.py tests/test_render_codex.py -q
E   ImportError: cannot import name 'load_autonomy_config' from 'weaver.autonomy' (...)
E   ModuleNotFoundError: No module named 'codex_brain'
2 errors in 0.12s
```

Both `weaver/autonomy.py` and `weaver/autonomy/__init__.py` exist as blobs at the Genesis root
commit `9ab26fc`; both are **blob-identical to Genesis** on current `main`. Neither side is the
product of a later drift, so no "one side superseded the other" history is available to break
the tie.

| side | shape | declared purpose |
|---|---|---|
| `weaver/autonomy.py` (91 lines) | module | `load_autonomy_config` / `validate_autonomy_config` / `run_scheduled_once` → `RecursiveEngine` |
| `weaver/autonomy/` | package | `__init__.py` states *"Conditional autonomy (disabled by default). Guards and proposal engine only. No execution hooks."* + `guard.py`, `proposal_engine.py` |

Python resolves the **package** first, so `weaver/run_autonomy.py:3` is import-broken and
`tests/test_autonomy.py` is a collection error.

---

## 3. Un-shadowing does not repair the test — the decisive measurement

The hygiene case for un-shadowing rests on the collection error being the defect. It is not.
Loading the legacy module **directly**, bypassing the shadow, and running the test's own
assertion sequence:

```
$ python -c "<load weaver/autonomy.py as a standalone module>"
res = {'ran': False, 'reason': 'disabled'}
assert res['ran'] is True -> *** FAILED ***
```

`tests/test_autonomy.py::test_autonomy_run_respects_limits` asserts `res['ran'] is True`. The
un-shadowed module returns `{'ran': False, 'reason': 'disabled'}` because it reads the
repository's live `governance/autonomy.json` (`enabled: false`) — `AUTONOMY_PATH` is built from
`os.getcwd()`, and the test's `monkeypatch.setenv('REPO_ROOT', ...)` **has no effect on it**.
The test's setup does not reach the module's configuration surface.

**Consequence.** Un-shadowing is a net *increase* in red: `test_autonomy_config_exists_and_valid`
would pass, `test_autonomy_run_respects_limits` would fail. The collection error is not a
separate defect to be cleared — it is the only reason this node is not already counted as a
substantive failure.

---

## 4. The autonomous commit surface, and its three barriers

`run_scheduled_once` constructs `RecursiveEngine(initial_task="autonomous scheduled run",
enabled=True)`, which calls `weaver.agent.agent_run` and builds commit messages
(`weaver/agent.py:136`, `weaver/recursive.py:96–102`). `weaver/git_ops.py` exposes
`commit_and_push`. So un-shadowing makes a commit-producing path importable.

Measured, the path is **dormant** — behind three stacked config barriers:

| # | barrier | measured value | where |
|---|---|---|---|
| 1 | `enabled` gate | `false` → returns `{'ran': False, 'reason': 'disabled'}` | `governance/autonomy.json` |
| 2 | `approved_by` role must exist in `roles.json` | `approved_by: "governance"` is **not** a role (`roles.json` holds `Flamekeeper`, `Weaver`, `Witness`, `Guest`) → returns `{'ran': False, 'reason': 'approval_missing'}` | `governance/autonomy.json` vs `governance/roles.json` |
| 3 | `require_env` match | returns `{'ran': False, 'reason': 'env_mismatch'}` unless the env var matches | `governance/autonomy.json` |

Measured, barrier 1 alone already yields `ran: False` on the real repository state.

**The barrier is config, not code.** All three are JSON/env values, inverted by an edit that
needs no code change and no review of `weaver/autonomy.py`. The governance record itself is
emphatic — `governance/autonomy.json` carries `"notes": "Cycle 8 reinitialization — no
autonomous execution permitted"`, `max_commits_per_run: 0`, and `mode: "proposal-only"`.

**Nothing invokes the path today.** No workflow, script, or Makefile references
`run_autonomy`; `.github/workflows/arkadia-engineering-scheduler.yml` is
`workflow_dispatch`-only and does not reference autonomy. The path is latent, not live.

This is why the ledger's `CONTRADICTED` stands: un-shadowing converts a *dormant but
config-gated* commit engine into a *live but config-gated* commit engine. The gate is one JSON
edit wide, and the edit is not reviewed by this envelope.

---

## 5. The package side is load-bearing production code

`weaver/session_kernel.py:11` — `from .autonomy.guard import AutonomyGuard` — is a **production**
import. `tests/test_autonomy_guard.py` and `tests/test_weaver_k0.py` import
`weaver.autonomy.guard` / `weaver.autonomy.proposal_engine` directly and **pass** on current
`main`.

Therefore the instinctive resolution — "delete the dead module" *or* "delete the shadowing
package" — is wrong in at least one direction: removing the package breaks `session_kernel.py`.
Neither side is disposable. This is a genuine either/or requiring a canonical choice.

---

## 6. Why this is not repairable in this envelope

Three independent disqualifiers, any one of which is sufficient:

1. **It is not hygiene.** §3 shows the repair does not green the node. GATE-00 hygiene's purpose
   is baseline classification and bounded repair; there is no repair here that reduces debt.
2. **It touches an autonomous mutation path.** §4. The authority model reserves
   `AUTONOMOUS MUTATION PATH` changes to the human sovereign. Un-shadowing makes a
   commit-producing surface importable; deleting the module destroys the other candidate.
3. **Every available action mutates a governance or mutation surface.** Un-shadowing rewrites
   the autonomy module boundary; deleting either side removes a governance-adjacent surface.
   The ledger's own remedy statement — *"Repair requires choosing a canonical autonomy module —
   that touches an autonomous mutation path, so it needs a sovereign decision"* — is confirmed
   rather than overturned.

**No code, test, or governance file is modified by this pass.** The deliverable is the
disposition.

---

## 7. Correction to the recorded baseline, and to the "two collection errors" pairing

Both collection errors have been carried together as *"the two documented, pre-existing
collection errors"* (`docs/control-plane/evidence/gate10-cp10-boundary-continuity-01/EVIDENCE.md:100`,
`PARKING_LOT.md:54`, and the automation contract). **They are not the same kind of thing**, and
this pass makes the second half of that correction precise:

| node | cause | disposition |
|---|---|---|
| `tests/test_autonomy.py` (CE-01) | module/package collision; masks a substantive `ran is True` failure | **sovereign decision** — §1–§6 |
| `tests/test_render_codex.py` (CE-02) | `ModuleNotFoundError: No module named 'codex_brain'` — the module exists only at `archive/legacy_python/codex_brain.py`; this is a naming/placement defect | **unclaimed by this pass** — PR **#149** owns CE-02 |

CE-02 is named here only to keep the pairing accurate. It is **not** re-litigated: PR #149
(`gate-hygiene/render-codex-collection-error-provenance-01`) is open and owns it. Deliberately
no finding about CE-02's remedy is asserted, because another open PR holds that workstream.

---

## 8. Live fingerprint at `002b189` (this pass)

| item | value |
|---|---|
| `main` / `origin/main` | `002b189` — agree |
| full suite | `20 failed / 1039 passed / 13 skipped / 2 collection errors` |
| `tests/architecture` | **11/11** |
| `api/main.py` | **2519 / 2600** lines |
| `vite build` | environment-blocked (no npm registry) — unchanged |
| open PRs | 22 |

The automation contract's recorded baseline (`main := 6038989`, `804 passed / 54 failed`,
`arch := 9/10`) is **stale**. `6038989` is real history — *"Merge PR #90: GATE-00 closure —
recover EDEN-OPS-02 onto canonical main"* — but it is **behind** current `main`; the contract
is anchored to the GATE-00 *closure* commit, not to head. The failure **fingerprint**, not the
raw count, remains the attribution unit. This corroborates PR #149's independent correction.

---

## 9. Authority boundary

No merge, no authorization, no identity change, no new mutation path, no new authorization path,
no governance/constitutional change, no boot-file change. `api/main.py` is untouched (2519/2600).
No source or test file is modified. Docs-only, under `docs/control-plane/evidence/`.

## 10. Handoff to the sovereign

One decision, stated so it can be answered without re-deriving any of the above:

> **Which autonomy shape is canonical — the `weaver/autonomy.py` engine module, or the
> `weaver/autonomy/` governance package — and is the `run_scheduled_once` commit path to be
> retired, retained-dormant, or re-enabled?**

Until that is answered, CE-01 stays a collection error. That is the **correct** resting state:
a red node that faithfully represents an unresolved governance question is more honest than a
green node produced by silently choosing a side of an autonomous mutation path.
