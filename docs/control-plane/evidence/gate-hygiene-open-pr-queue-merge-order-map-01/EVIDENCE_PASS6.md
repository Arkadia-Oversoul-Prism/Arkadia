# EVIDENCE — gate-hygiene/open-pr-queue-merge-order-map-01 — Pass 6

**Pass:** hourly bounded execution, 2026-10-03
**BASE_MAIN:** `162f574b05dd839540d803aadda7608342618a84` (merge of PR #214)
**PR:** #219 — branch `gate-hygiene/open-pr-queue-merge-order-map-02`
**Live #219 tip at measurement:** `e60bc91340611272d824eeca75e4801fc90d6caf`
**Classification:** `VERIFIED` (composition proof) · next task `IMPLEMENTED` (evidence-only)
**Authority:** none required for this pass. No merge, no push to `main`, no force-push.

Pass 5 recorded its state at `210d6c0`; the branch then moved to `e60bc913`. This pass
re-derives every Pass-5 claim from live evidence at the moved tip rather than inheriting
them. All measurements below were run in isolated `git worktree`s; no source, test, or
governance file was modified.

---

## 1. Composition proof (live #219 tip)

Five-PR cluster composed onto `main @ 162f574` in queue order, then in a second, shuffled
order, using a fresh worktree each time.

| step | PR | result |
|---|---|---|
| 1 | #215 | merge clean, rc=0 |
| 2 | #216 | merge clean, rc=0 |
| 3 | #217 | merge clean, rc=0 |
| 4 | #218 | merge clean, rc=0 |
| 5 | #219 @ `e60bc913` | merge clean, rc=0 |

- Sequential composed tree: `2f7dc9c59c404a9c4cf02b7a44c6bcb0c9566e09`
- Shuffled order (216, 218, 215, 217, 219): **identical tree** `2f7dc9c5…`
- Zero conflict markers in either composition.

The cluster is **order-insensitive and conflict-free** on the live tip. The tree identity
is the strong form: no pair of the five PRs can interact, regardless of merge order.

## 2. Protected-surface checks

| check | command | result |
|---|---|---|
| boot code compiles | `python -m py_compile api/main.py` | OK |
| line budget (2600) | `wc -l api/main.py` | **2582** — within budget |
| architecture fitness | `pytest tests/architecture -q` | **11 passed** |
| CP10 boundary, composed diff | `cp10_mutation_boundary_policy.py --judge` | PASS (rc=0) |
| CP10 boundary, each PR alone | per-PR `--judge` | PASS (rc=0) ×5 |

CP10 was run against the **composed** diff and against each PR's own diff; the executed
decision matches the proven decision in every case.

## 3. Suite measurement — composed vs baseline

Invocation (both sides identical): `PYTHONPATH=<tree>/archive/legacy_python python -m pytest tests/ -q --continue-on-collection-errors -p no:cacheprovider`

| tree | passed | failed | skipped | errors | failing-node fingerprint (sha256) |
|---|---|---|---|---|---|
| `main @ 162f574` | 1307 | **20** | 16 | 1 | `4d84e7eb2524d4a5a952405f6df8017398ce21cca44aec6d04fbb523d577c6a7` (21 nodes) |
| composed (5 PRs) | 1310 | **18** | 16 | 1 | `c9ffdb6216c7031403b9e259a75f0d173bccc9103c8c66215b52aa04ffd05c01` (19 nodes) |

Node-set delta (compared by identity, never by count):

- **fixed (2):**
  - `tests/test_agents_md_encoding_adjudication.py::test_exit_code_does_not_call_a_divergent_clean_file_verified`
  - `tests/test_agents_md_encoding_adjudication.py::test_gate2_parent_agents_md_repair_is_byte_identical_to_the_pipeline`
- **newly failing: 0**
- **unchanged:** 19

The two fixed nodes are exactly the two named by the queue map and fixed by #217 / #218.
The `1310 = 1307 + 2 (fixed) + 1` arithmetic is consistent with a third pass that also
resolves on the composed tree. Composed counts and fingerprint reproduce Pass 5 exactly.

## 4. AGENTS.md encoding invariant

`python scripts/agents_md_encoding_audit.py` on the composed tree:

```
Cyrillic             0 -> 0
line count preserved True
round-trip holds     True
oracle 6c43218a48a4  insertions-only inserted=453 alterations=0 reproduced=True
exit 1
```

`alterations=0` and `reproduced=True` — the working tree relates to the oracle by
insertions only. Exit 1 is the clean-and-oracle-corroborated status, not a failure
(exit 2 is the divergent/undecided status; exit 0 is a mojibake recovery).

## 5. Gate-2 production observation

`python scripts/gate2_production_observation.py` at `main @ 162f574`:

| boundary | classification |
|---|---|
| current main resolved | VERIFIED |
| main → deployment identity | **STALE** (newest Production deploy `57e67c53` predates main) |
| deployment build output observed | **BLOCKED** (deployment-specific URL → HTTP 410, SSO) |
| alias reachable | VERIFIED (HTTP 200, 836748-byte bundle) |
| alias → deployment SHA binding | UNKNOWN |
| build ↔ source lineage | UNKNOWN |
| browser-rendered UI correctness | UNKNOWN |
| production acceptance | NOT CLAIMED (human authority) |

Unchanged from the standing Gate-2 record. `BLOCKED` on provider auth, not on repository
work; repetition cannot convert it to VERIFIED.

## 6. Live open-PR inventory (6 open)

| PR | draft | disposition |
|---|---|---|
| #215 | no | in the composable cluster |
| #216 | no | in the composable cluster |
| #217 | no | in the composable cluster |
| #218 | no | in the composable cluster |
| #219 | no | in the composable cluster (this branch) |
| #220 | **yes** | HOLD — `SH-05` sovereign disposition required |

PR #220 (`gate-hygiene: SH-05 retirement boundary — HOLD`) is **draft** and is **not** part
of the merge-ready cluster. Its own state doc classifies it `BLOCKED` pending a sovereign
`SH-05` product ruling (retire / relocate / restore the Gate UI). This pass did not touch it.

## 7. Next bounded task — classification of two unclaimed baseline failures

A grep of `docs/control-plane/evidence/` showed two of the twenty baseline failure nodes
are named by **no evidence document** — neither the baseline test-debt classification
(51-node table) nor any workstream doc. Both are now classified; neither is a source defect.

**7.1 `tests/test_solariun_thread_navigation_01.py::test_shell_wires_home_to_lens_selection`**

The test asserts three literals against `web/public_prism/src/components/solspire/SolSpireExperience.tsx`:

| assertion | live state |
|---|---|
| `"<SolariunHomeCockpit onNavigate={onThreadTarget}/>"` | **FALSE** — the mount does not exist |
| `"onThreadTarget={selectSection}"` | TRUE (still present) |
| `"onThreadTarget:(s:SolSpireLens)=>void"` | TRUE (still present) |

Mechanism: PR #189 (`6d5f722b`, sovereign-authored, *"Reconcile frontend into a simpler
interaction canvas"*) deliberately replaced the mount. Its commit log includes
*"chore: remove superseded Solariun home import"*; the diff shows
`-<SolariunHomeCockpit onNavigate={onThreadTarget}/>` →
`+<SolariunInteractionCanvas onNavigate={target=>{…}}/>` and the import swap. The sibling
cockpit tests still pass, so `SolariunHomeCockpit.tsx` remains in the tree as an unmounted
component.

Classification: **STALE_ASSERTION** — the assertion pins a mount that a deliberate,
documented sovereign refactor replaced. No capability is absent. A repair is a *test*
edit, and it has a design dimension: `SolariunInteractionCanvas`'s `onNavigate` is typed
`(target: string) => void` (`SolariunInteractionCanvas.tsx:5`), not the canonical
`SolSpireLens` union, so the test's *intent* (bounded destination union) is only satisfied
by the surviving `LensContent` signature — not by the live canvas. Resolving whether the
canvas should be bounded to `SolSpireLens` is a product call, which is why this is pinned
as a task rather than executed in this evidence-only pass.

**7.2 `tests/test_authority_api_enterprise_boundary.py::test_api_approval_does_not_create_enterprise_authorization_without_explicit_bridge`**

Failure mode: `async def functions are not natively supported. You need to install a
suitable plugin … (anyio / pytest-asyncio / …)`. The test is decorated
`@pytest.mark.asyncio`, but **no async pytest plugin is installed or declared** — `grep`
for `pytest-asyncio|pytest_asyncio|anyio` across `requirements*.txt`, `pyproject.toml`,
and `setup.cfg` is empty, and `import pytest_asyncio` raises `ModuleNotFoundError`.

Classification: **ENV / ARTIFACT** — the module is importable, but no assertion ever
executes. This is the same defect class recorded in the MIE lesson ("a job that *runs*
`testDebugUnitTest` is not evidence that any test *ran*"): the node is green-or-red
independent of the behaviour it claims to guard, so it provides no authority-boundary
coverage today. The repair — declare an async plugin and re-measure, or convert the
module to synchronous tests — is a bounded test-infrastructure change, not a source edit.

Neither classification touches `api/main.py`, the authority model, the identity boundary,
or governance code.

## 8. Next bounded task (pinned)

**Bounded objective:** classify-and-repair the two unclaimed baseline nodes above as a
standalone `test-hygiene` workstream (explicitly *not* folded into an architectural gate),
following the established pattern of `baseline-test-debt-classification-01`.

- **Scope:** `tests/test_solariun_thread_navigation_01.py`,
  `tests/test_authority_api_enterprise_boundary.py`, plus an async-plugin declaration
  (`requirements*.txt` or `pyproject.toml`) if the synchronous conversion is not chosen.
- **Completion condition:** both nodes either pass on `main` or are explicitly retired
  with a recorded rationale; the 21-node baseline fingerprint is re-derived and the delta
  is by node identity (2 removed / 0 new).
- **Regression boundary:** `tests/architecture` stays 11/11; `api/main.py` untouched and
  within budget; the AGENTS.md audit stays `alterations=0`.
- **Authority boundary:** no merge; a sovereign `SH-05` ruling is **not** a dependency of
  this task, but the `SH-05a` retirement (#220) and this repair both delete or rewrite
  Gate-adjacent tests — they must **not** be merged in one batch without the sovereign
  seeing the combined test-file inventory.

**Do not execute #220 (draft/HOLD)** until a sovereign `SH-05` disposition is recorded.

## 9. What this pass does NOT claim

- No production parity: Gate 2 remains `BLOCKED` (provider auth).
- No merge authorization: the five-PR cluster is `READY FOR SOVEREIGN MERGE`, not merged.
- No frontend build: `pnpm build` was not attempted this pass (untracked `dist/`); the
  source-level assertions are the repo's stated convention for frontend tests.
- No source/test/governance change was made; this pass is evidence-only.
