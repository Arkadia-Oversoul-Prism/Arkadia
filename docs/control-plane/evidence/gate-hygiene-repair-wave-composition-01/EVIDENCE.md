# Repair-wave composition and baseline-fixture reconciliation

_This record was produced by an AI agent (OpenHands) under contract `ARK-OPS-CONTINUOUS-001`. It performs **no** merge, **no** deployment, and claims **no** acceptance. Merge execution is human-only (GOV-03/GOV-04). Everything below is measurement, not intent._

**Measured:** 2026-11-25
**Canonical `main`:** `fd0a4fdc081064b2074aab9e17b4c7841736dd9f` (GOV-04, PR #722)
**Production `/api/version`:** `source_revision` = `fd0a4fdc081064b2074aab9e17b4c7841736dd9f`, `revision_conflict: false` — source↔runtime consistent at measurement time.
**Open PRs:** 48 (all drafts except #724).

## 1. Scope

This cycle found **no unowned defect**. Every failing/error node on `main` is either sovereign-reserved, environment-only, or already repaired by an open PR. Rather than open a competing PR on any of those defects (which would create the composition hazard recorded repeatedly in `AGENTS.md`), this cycle measures the thing only a composition can reveal: **do the open repair PRs hold together, and what does the baseline fixture look like once they land?**

The result is a merge-readiness assessment and one concrete, actionable finding: the recorded baseline node set goes **stale** after the repair wave.

## 2. Live failing/error set on `main` — full attribution

Full suite at `fd0a4fdc`:

```
PYTHONPATH=$PWD/archive/legacy_python python -m pytest tests/ -q -rEf --continue-on-collection-errors
20 failed, 4253 passed, 22 skipped, 6 warnings, 1 error in 282.90s
```

21 failing/error nodes, **all attributed**:

| # | node | class | owner |
|---|---|---|---|
| 1 | `ERROR tests/test_autonomy.py` | sovereign-reserved | CE-01 `weaver.autonomy` module-vs-package collision |
| 2 | `test_ais_w2_living_gate_grove_handoff.py::test_no_firebase_persistence_in_gate` | sovereign-reserved | F-01 persistence boundary |
| 3 | `test_gov04_bounded_merge_delegation.py::test_bounded_merge_is_exact_head_and_protected_fail_closed` | branch-introduced (#722) | **#725** |
| 4 | `test_identity_spine_w1.py::test_node_entry_is_ais_signup_not_a_separate_diagnostic_route` | repaired | **#700** |
| 5 | `test_m02_reasomate_truth.py::test_oracle_runtime_uses_the_shared_session_key` | repaired | **#700** |
| 6 | `test_m01_persistence.py::test_deletion_propagates_to_durable_corpus` | repaired | **#690** |
| 7 | `test_m05_files.py::test_update_file_supports_rename` | repaired | **#690** |
| 8 | `test_solspire_r1_governance_convergence.py::test_r1_solspire_builders_delegate_to_weaver` | repaired | **#693** |
| 9 | `test_solspire_r1_governance_convergence.py::test_r1_weaver_governance_is_canonical` | repaired | **#693** |
| 10 | `test_solspire_r3_execution_runtime.py::test_runtime_is_explicitly_non_governed_and_blocks_mutation_tools` | repaired | **#691** |
| 11 | `test_static_ingestion_idempotency.py::test_open_loop_content_is_checksum_stable_through_a_vault_round_trip` | repaired | **#698** |
| 12–20 | `test_mission_lifecycle_adapter_contract.py` (9 nodes) | environment-only | hard `assert TSC.exists()`; `web/arkadia_console/node_modules/typescript` absent |

Notes on the two environment-sensitive classes:

- **The 9 mission-lifecycle nodes are not a CI defect.** `provider-routing.yml` judges the candidate suite against a **merge-base baseline** by node difference (`scripts/provider_routing_gate.py`). These 9 nodes fail identically on baseline and candidate, so they cancel; they cannot turn that gate red.
- **The one node that can flip `provider-routing` is #11**, because it is order-dependent: it appeared in one of the two runs of the same tree (20 vs 21 failed) in run `45449878172`. #698 gives it its own oracle store.

Node #3 is the only node #722 added to `main`; removing it reproduces the canonical 20-node baseline `8d70e46e…`, which is why #725 is a one-node repair, not a re-baselining.

## 3. Composition of the six repair PRs

Composed in an isolated worktree from `main` `fd0a4fdc`:

```
git worktree add --detach /tmp/compose fd0a4fdc
git merge --no-edit origin/<branch>   # 690, 691, 693, 698, 700, 725
```

- **Zero conflicted files** across all six merges. No two repair PRs touch the same file.
- Composed tree test results:

| suite | result |
|---|---|
| the seven repaired files + `test_gov04_bounded_merge_delegation.py` + `test_baseline_fingerprint.py` | **81 passed** |
| `tests/architecture` | **11 passed** |
| gate-integrity bundle (`test_m02a_ci_gate_integrity`, `test_ci_gate_trigger_coverage`, `test_lane_instruction_doc_currency`, `test_lane_currency_ci_wiring`) | **253 passed** |

Composition is **safe**: the six repairs are textually and semantically compatible and their targets pass together.

## 4. Finding — the baseline fixture goes stale (before and after the wave)

`tests/fixtures/baseline_node_set.txt` is meant to describe the failing/error nodes of the revision it is committed to. It does not track the repair wave, because repair PRs do not update it.

**On current `main` (10-node fixture):** three entries are already stale — `tests/test_steward_filter.py` is `12 passed` live, yet its three nodes remain recorded. (#693 removes them.)

**After the six-PR wave (5-node fixture per #693):** three *different* entries go stale, because #691 and #700 repair nodes that #693 keeps:

| fixture entry (post-#693) | live after wave | status |
|---|---|---|
| `ERROR tests/test_autonomy.py` | fails (CE-01) | correct |
| `test_ais_w2_...::test_no_firebase_persistence_in_gate` | fails (F-01) | correct |
| `test_identity_spine_w1::test_node_entry_is_ais_signup...` | **passes** | **stale** (#700) |
| `test_m02_reasomate_truth::test_oracle_runtime_uses_the_shared_session_key` | **passes** | **stale** (#700) |
| `test_solspire_r3_execution_runtime::test_runtime_is_explicitly_non_governed...` | **passes** | **stale** (#691) |

Verified per-node on the composed tree (`1 passed` / `4 passed` for the first three; `1 failed` for `ais_w2`).

**This does not redden `test_baseline_fingerprint.py`.** That guard pins the fixture and the four `FINGERPRINT_DOCS` to hardcoded constants; it does **not** measure live. A stale fixture is internally consistent, so the guard stays green while describing debt that no longer exists. That is the whole reason the staleness survives.

## 5. Post-wave reconciliation (actionable)

After the wave merges, the correct recorded set is **2 nodes**:

```
ERROR tests/test_autonomy.py
FAILED tests/test_ais_w2_living_gate_grove_handoff.py::test_no_firebase_persistence_in_gate
```

Canonical fingerprints for that set (`scripts/baseline_fingerprint.py`):

```
outcomes_fingerprint = f607dffd1abda8bc667897a4366c6afe1498ae6e5b02635ff682cbc6daeb2ad1
ids_fingerprint      = 48e2b758b3194bd267e7babf13609b3467ff46985a879c72a55ad5201f44b3a9
```

This reconciliation must land **after** the wave (it under-reports while the repaired nodes still fail). It is not committed here because it is only correct once #691 and #700 are on `main`, and committing it earlier would describe a state that does not exist.

## 6. Recommended merge order (human-only)

All six are drafts; none is marked ready by this record. If the sovereign chooses to merge them:

1. **#690, #698** — independent, no fixture interaction.
2. **#725** — removes the one node #722 added.
3. **#691, #700** — repair nodes still listed by the post-#693 fixture.
4. **#693** — then re-derive: drop the three now-passing nodes and set the two fingerprints above in the same commit, so the fixture and its constants agree at every revision.

Alternatively merge #693 first (its 5-node fixture is correct at that revision) and apply §5 as a follow-up once #691/#700 land. Either way, **§5 must accompany or follow #693**; #693 alone cannot anticipate #691/#700.

## 7. Durable-fix proposal (not executed)

The recurring class — a fixture that lists repaired nodes and a guard that cannot see it — is not closed by any single reconciliation. A durable fix is to make the fixture **live-measuring**: assert that every node in `baseline_node_set.txt` is actually failing on the current tree. That changes `tests/test_baseline_fingerprint.py`, which #693 is already rewriting, so it is a **separate bounded workstream** for after the wave. Recorded, not performed — doing it now would conflict with #693.

## 8. Verification actually run

```
# main
python -m pytest tests/ -q -rEf --continue-on-collection-errors      -> 20F 4253P 22S 1E (21 nodes)
python -m pytest tests/test_gov04_bounded_merge_delegation.py -q     -> 1 failed, 3 passed (the #722 node)
python -m pytest tests/test_steward_filter.py -q                     -> 12 passed (fixture entries stale on main)

# composed tree (/tmp/compose, six merges, 0 conflicts)
python -m pytest <7 repaired files + gov04 + baseline_fingerprint>   -> 81 passed
python -m pytest tests/architecture -q                               -> 11 passed
python -m pytest <gate-integrity bundle> -q                          -> 253 passed
python scripts/baseline_fingerprint.py <2-node set> --json           -> f607dffd… / 48e2b758…
```

## 9. Next-action block

- **Current state:** `main` = `fd0a4fdc`; production matches it; 21 failing/error nodes, all attributed; 48 open PRs (all drafts).
- **Evidence:** this file; composition measured, not assumed.
- **Blocker:** merge execution is human-only (GOV-03/GOV-04); 30 PRs are fully green and awaiting human review; no agent may mark a draft ready or merge.
- **Authorized next action:** a human reviews and merges the repair wave in §6, then applies the §5 reconciliation with #693 (or immediately after it).
- **Forbidden:** marking drafts ready, merging, deploying, re-baselining the fixture before the wave, editing #693's files in a competing PR.
- **Completion condition:** the fixture names exactly the nodes that fail on `main`, and `test_baseline_fingerprint.py` either measures that live or is replaced by a live-measuring guard.
