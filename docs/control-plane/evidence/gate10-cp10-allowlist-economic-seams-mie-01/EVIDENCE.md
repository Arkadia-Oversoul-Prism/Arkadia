# GATE-10 / CP10 — Allowlist reconciliation: `economic_seams/` + `musical-intention-engine/` — Evidence

**Gate:** GATE-10 (Governed Execution) — CP10 mutation boundary / M02A CI gate integrity
**Authority:** Human sovereign (merge and authorization retained exclusively by the sovereign)
**BASE_MAIN:** `886759f2de6a1edd062c878ebdf448d0ed4e0330`
**Branch:** `gate10/cp10-allowlist-economic-seams-mie-01`
**Status:** VERIFIED (fitness tests + CLI runtime evidence); merge is human-only.

## 1. Objective (bounded)

`scripts/cp10_mutation_boundary_policy.py` (`LEGIT`) is the single source of the CP10
mutation-boundary decision; the workflow pipes `git diff --name-only` into its `--judge`
mode and fails on a non-zero exit. Its stated invariant is that **every path in
`git ls-files` is admitted** — an allowlist that omits a surface the repository genuinely
tracks does not tighten the boundary, it reddens the canonical branch on the next real
commit.

Two tracked trees were omitted, and the invariant is currently red on `main` for them:

| Omitted surface | Paths | Provenance |
|---|---|---|
| `economic_seams/` | 5 (`__init__`, `correlation`, `engine`, `market_data`, `nocopo`) | provider-neutral economic seam engine; `39cd05e` "fix: repair correlation source registry syntax" touches only `economic_seams/correlation.py` |
| `musical-intention-engine/` | 14 (constitution, field recon, interaction canvas, musical-object spec, prototype loop, decisions, experiments, research, build state, gates, README) | MIE control-plane corpus that issue #209's MVP build reads from |

`39cd05e` is judged **FAIL** by the policy CLI the gate executes: an ordinary bug-fix
commit on `main` is reported as "Unexpected path outside legitimate surfaces". The three
completeness fitness tests are correspondingly red on `main`:
`test_allowlist_admits_every_tracked_top_level_prefix`,
`test_allowlist_covers_every_tracked_surface`,
`test_delegated_verdict_admits_every_tracked_surface`.

This pass reconciles the allowlist to the tracked corpus, following the `reconciliation/`
precedent (`dde3a7f`, PR #182). No boundary was weakened.

## 2. Change set

| File | Change |
|---|---|
| `scripts/cp10_mutation_boundary_policy.py` | Two alternations added to `LEGIT`: `economic_seams/` and `musical-intention-engine/`, each with a provenance comment. The header's stale inventory count is corrected to the measured `83 entries, 1645 paths at 886759f`. |
| `tests/test_m02a_ci_gate_integrity.py` | Four regression tests pinning each surface and the exact shipped change sets; two lookalike paths added to `test_allowlist_rejects_unknown_lookalike_roots`. |

The `forbid` stage (`SolSpireExperienceV3.tsx` / `SolSpireExperienceV2.tsx`) and the
unknown-root rejection are untouched, so the gate's teeth are unchanged.

## 3. Verification

```
python scripts/cp10_mutation_boundary_policy.py --judge   (economic_seams/correlation.py)  -> PASS, exit 0
python scripts/cp10_mutation_boundary_policy.py --judge   (musical-intention-engine/*.md)  -> PASS, exit 0
python scripts/cp10_mutation_boundary_policy.py --judge   (this change set)                -> PASS, exit 0
lookalikes economic_seams_evil/x.py, musical-intention-engine_evil/x.md, musical_intention_engine/x.md -> rejected
vault/Ideas/2026-01-01.md (generated note)                                                 -> rejected
web/public_prism/src/components/solspire/SolSpireExperienceV3.tsx                          -> rejected (forbid)
omitted tracked paths, whole corpus (git ls-files, 1645 paths)                             -> 0
pytest tests/test_m02a_ci_gate_integrity.py   -> 55 passed
pytest tests/architecture                     -> 11 passed
pytest tests/test_baseline_fingerprint.py     -> 17 passed
python -m py_compile api/main.py              -> OK, 2582 lines (budget 2600, api/main.py untouched)
```

## 4. Baseline comparison (no regression)

Full suite, same environment, before and after this change:

- Baseline (main @ `886759f`, measured this pass): **23 failed / 1301 passed / 15 skipped / 1 error**
- After this change: **20 failed / 1308 passed / 15 skipped / 1 error**

The delta is exactly the three CP10 completeness nodes this change repairs — no new failure
node is introduced. The depth-stable failing-node set is **identical** to
`tests/fixtures/baseline_node_set.txt` (20 nodes):

```
sha256("\n".join(sorted("FAILED/ERROR <nodeid>")) + "\n")
  = a578a766c09c949c620c9d324248659812d215d3d1e875a0c25b42adb8912aa1   (depth-stable, unchanged)
```

The clone here carries the pinned PR-head revision `7d79f38`, so
`test_gate2_parent_agents_md_repair_is_byte_identical_to_the_pipeline` is *reported* as an
extra failure (live set 21 outcomes) while `ERROR tests/test_autonomy.py` is reported in
the summary but omitted from the `-rf` short list. That node is clone-depth-dependent and
is deliberately excluded from the recorded set by `a5fa8a0`; it is **not** part of this
workstream and is unchanged by it.

## 5. Remaining uncertainty / out of scope

- The two excluded/known-baseline nodes above are pre-existing main debt and are not
  touched here (rule: do not fix baseline debt while executing an unrelated gate).
- `api/main.py` is untouched and within budget (2582 / 2600).
- No new mutation path, authorization path, or authority surface is introduced: the change
  widens the *inventory of legitimate repository surfaces*, not the boundary's teeth.
