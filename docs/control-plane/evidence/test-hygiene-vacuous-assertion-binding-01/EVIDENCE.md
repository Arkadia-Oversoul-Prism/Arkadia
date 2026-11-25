# TEST-HYGIENE — bind seven always-true assertions to real invariants

**Contract:** ARK-OPS-CONTINUOUS-001 (rev. 2026-11-22) · **Cycle:** 16
**Base:** `main` `fd0a4fdc081064b2074aab9e17b4c7841736dd9f` (GOV-04 merge, #722)
**Authority:** implementation + tests + evidence only. **No merge, no deploy, no acceptance.**

## 1. Defect

Seven assertions in the tracked test corpus were **structurally always true**, so they passed
on every tree and protected nothing:

| File | Line | Form |
|------|------|------|
| `tests/test_corpus_sync_schema.py` | 65 | `assert any(...) or True` |
| `tests/test_solspire_p0_execution_01.py` | 57 | `assert True` |
| `tests/test_solspire_p1_experience_01.py` | 85 | `assert "universal object" not in src.lower() or True` |
| `tests/test_stellar_cartography.py` | 103 | `assert "api.main" not in sys.modules or True` |
| `tests/test_weaver_context.py` | 112 | `assert pkt[...]["bound_head_sha"] != head or True` |
| `tests/test_weaver_k14.py` | 55 | `assert a.authorization["current_pass_authorized"] is False or True` |
| `tests/test_weaver_k8.py` | 89 | `assert not hasattr(WeaverContinuation, "allowed_paths") or True` |

The enumeration is AST-based, not textual (so string fixtures that merely *contain*
`assert True` — `tests/test_engineering_lab_test_boundary.py`,
`tests/test_baseline_fingerprint.py` — are correctly excluded). AST scan over every
`tests/**/*.py` reported exactly the seven rows above.

This is the class already recorded in `AGENTS.md`: *a guard that is silent on both the defect
and its absence is not a guard.*

## 2. Repair (each site bound to the invariant it was written for)

| Site | Now asserts | Falsified by |
|------|-------------|--------------|
| `test_stellar_decoupled_from_api_main` | `kernel/stellar.py` imports none of `api`/`httpx`/`fastapi`/`starlette` (AST import scan, deterministic; replaces the order-dependent `sys.modules` check) | adding `import httpx` to `kernel/stellar.py` |
| `test_continuation_not_pass_spec` | `WeaverContinuation` has no `allowed_paths` attribute | adding the attribute |
| `test_patch_deterministic` | `authorization["current_pass_authorized"] is False` | returning `True` |
| `test_stale_detection` | the packet binds `bound_head_sha == head` **before** mutation; the post-mutation `is_stale(...) is True` already covered the stale branch | a packet that does not bind the head |
| `test_corpus_sync_state_index` | the `key` column is the primary key **and** carries an automatic `origin="pk"` index (`PRAGMA index_list`) | dropping the PK |
| `test_packet_scope_excludes_p2_claims` | the page disclaims P2's index: `"no universal object index"` (the literal appears only inside that disclaimer) | removing the disclaimer |
| `test_packet_forbids_p0_1_in_this_branch_not_required` | the P0 packet's evidence records `**Forbidden:** P0.1` | dropping P0.1 from the recorded scope |

The last two are the cases where the vacuous form was hiding a **wrong** assertion: the
archived `SolSpireExperience.tsx` *does* contain the string `universal object`, inside the
sentence `No universal object index · Semantic may be unavailable`. Removing `or True`
without reading the source would have produced a false failure; the invariant is the
disclaimer, not the absence of the phrase.

## 3. Structural guard (class cannot recur)

`tests/test_vacuous_assertion_guard.py` (3 nodes) AST-scans every `git ls-files` test file for
`assert True` and `assert <expr> or True` and fails on any offender. It carries:

- **negative control** — the detector reports both forms on a synthetic source;
- **positive control** — a falsifiable assertion is not reported;
- **live control** — re-introducing `or True` in `tests/test_weaver_k8.py:89` on the real tree
  reddens exactly `test_no_tracked_test_assertion_cannot_fail`
  (`Left contains one more item: 'tests/test_weaver_k8.py:89 assert ... or True'`); the file was
  then restored byte-identically (`git diff --stat` = the intended 1-line repair).

Live controls for the repaired assertions themselves:

```
# stellar detector
$ sed -i '19a import httpx' kernel/stellar.py
1 failed, 9 passed          # test_stellar_decoupled_from_api_main
$ restore -> clean

# P0.1 scope pin
$ sed -i 's/**Forbidden:** P0.1, P1, P2/**Forbidden:** P1, P2/' .../solspire-p0-execution-01/EVIDENCE.md
1 failed, 6 passed          # test_packet_forbids_p0_1_in_this_branch_not_required
$ restore -> clean
```

## 4. Measurements

| Scope | Result |
|-------|--------|
| The seven files + new guard | **60 passed** (57 before, +3 new nodes) |
| Generic gate-integrity + architecture (`m02a`, `ci_gate_trigger_coverage`, `gate_filter_selection`, `ci_suite_collection_continuation`, `workflow_injection_boundary`, `tests/architecture`) | **388 passed** |
| CP10 mutation-boundary judge over the diff | `Mutation boundary PASS`, exit 0 |
| Full suite, branch | `10 failed, 4266 passed, 22 skipped, 1 error` — **11 nodes**, sha256 `753e8931…` |
| Full suite, `main` `fd0a4fdc` (same sandbox, measured earlier) | `20 failed, 4253 passed, 22 skipped, 1 error` — **21 nodes**, sha256 `4118e2ff…` |
| Node-set delta | branch ⊆ main; **zero new nodes**. The 10-node reduction is `test_mission_lifecycle_adapter_contract.py` (10 passed in isolation), which needs `web/arkadia_console/node_modules/typescript` — present only after this cycle's console build. The file is **untouched** (`git diff origin/main -- <file>` empty), so the delta is environmental, not the change. |
| Passed-count arithmetic | `4253 + 10 (env-unblocked) + 3 (new nodes) = 4266` |

Remaining 11 nodes are all accounted for and unowned by this change: CE-01 (`test_autonomy`
collection error, sovereign-reserved), F-01 (`test_no_firebase_persistence_in_gate`), and the
rest repaired by open PRs (#700, #693, #691, #690, #698, #725).

## 5. Composition

No open PR among the **51** open heads touches any file this change edits
(`git diff --name-only origin/main...refs/remotes/pr/<n>` checked per head). No textual or
semantic conflict.

## 5.1 CI

All **10/10** check-runs `completed/success` on the code head `eeab2415` and again on the
docs-only follow-up `f03fc036` (final head at time of writing): `Full-history secret scan`,
`boot-syntax`, `console-contract` (3m15s), `test` (economic-seam engine), `posture-currency`,
`provider-forensics`, `beta-beta-01-english`, `beta-beta-02-hausa`, `bundle-beta-evidence`,
`native-arkadia-golden-workflow`. `mergeStateStatus` = `CLEAN`, PR remains a **draft**.
`lane-doc-currency` is path-filtered and did not run at either revision (absence is not a pass;
the lane suites were not modified).

## 6. Limitations (not claimed)

- The guard covers `tests/**/*.py` and the two structural forms only. Semantic tautologies
  (`assert x == x`, `assert isinstance("a", str)`) are **not** detected.
- The console build (`corepack pnpm install --frozen-lockfile && corepack pnpm build`) was run
  for environment fidelity and passed (`tsc --noEmit` clean, `dist/assets/index-CYGHeCpJ.js`);
  its output is untracked and not committed.
- No merge, no deployment, no production-parity or acceptance claim. Production was observed
  at `source_revision == fd0a4fdc…` (`revision_conflict false`) before this change; that is
  evidence about `main`, not about this branch.
