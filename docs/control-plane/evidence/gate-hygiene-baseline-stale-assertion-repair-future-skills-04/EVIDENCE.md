# EVIDENCE — gate hygiene / SH-02 batch 4 (future-skills copy)

**Gate/workstream:** `SH-02` (baseline STALE_ASSERTION migration), batch 4
**Branch:** `gate-hygiene/baseline-stale-assertion-repair-future-skills-04`
**Base:** `main` @ `4164573586860b9c7e04e1815bca4957559046a2`
**Authority:** test-only edit; no merge, no `main` push, human-sovereign merge only.

## Objective

Repair the next bounded batch of stale source-level string assertions classified
`STALE_ASSERTION` in the baseline classification ledger, without widening scope into
`DRIFT` / product-decision nodes.

## Scope decision (why this batch is small)

The classification ledger
(`docs/control-plane/evidence/gate-hygiene-baseline-test-debt-classification-01/BASELINE_TEST_DEBT_CLASSIFICATION.md`)
assigns every failing node to a bucket. The `STALE_ASSERTION` bucket (35 nodes) is the
only bucket `SH-02` may migrate. Of those 35:

- nodes **13-18** (`test_prism_pass_c_surface_ownership.py`) are owned by merged PR #127;
- node **2** (`test_ais_capability_profile_onboarding.py::test_home_is_offer_led...`) is the
  visible face of `SH-08` (`/api/pulse/analyze` contradiction) - a governance decision;
- nodes **3-8** (`test_ais_w2_living_gate_grove_handoff.py`) are the `SH-08` cluster;
- nodes **10-12** (`test_prism_interior_shell.py`) assert a dropped canonical contract token
  (`prism-primary-rail` -> `novanet-primary-rail`; `sci` / `knowledge-os` removed from the
  rail) - a surface-ownership question, not a quote-style repair;
- the remaining clusters are owned by open PR #130 or await product decisions.

Node **9** was the one cleanly-stale, uncovered node. Batch is deliberately one node rather
than padding the diff with a product decision (see *Scope reverted* below).

## Change

`tests/test_ais_w6_future_skills_challenge.py::test_w6_is_self_guided_and_timed`

```diff
-    assert "60-minute challenge" in src
+    assert "self-guided practical challenge" in src
     assert "LIMIT_MS = 60 * 60 * 1000" in src
```

`LIMIT_MS = 60 * 60 * 1000` (the behavioural constraint the test exists to protect) is
unchanged and still asserted. `FutureSkillsChallenge.tsx` renders the self-guided framing -
"A self-guided practical challenge. Think, research, build, prove, and explain a useful
solution. No lecture. No certificate." - at `:178`. The advertised time limit was reworded
away, but the enforced timer is intact.

## Verification

### Negative control (repaired node can still fail)

```
old literal '60-minute challenge'             present in src : False  -> pre-repair assertion fails
new literal 'self-guided practical challenge' present in src : True
```

The repaired assertion is a real string assertion against real rendered copy; if the
self-guided framing is removed it fails again. Verified directly against the source file.

### Task-specific

```
tests/test_ais_w6_future_skills_challenge.py   7 passed
```

### Cancellation control (was the node failing at base?)

`git stash` back to `main` @ `4164573`, re-run the module:

```
FAILED tests/test_ais_w6_future_skills_challenge.py::test_w6_is_self_guided_and_timed
2 failed, 5 passed
```

Confirms the node was a genuine base failure, not a pre-existing pass.

### Regression fingerprint (by node name, not count)

```
main 4164573                     : 39 failed / 1020 passed / 11 skipped
main 4164573 + this repair       : 38 failed / 1021 passed / 11 skipped
architecture                     : 11/11
py_compile api/main.py           : pass   (api/main.py = 2519 / 2600 lines)
vite build                       : environment-blocked (no npm registry access)
```

Node delta is exactly the repaired node: `test_w6_is_self_guided_and_timed` is absent from
the post-repair failure list and no other node name changed.

Reproduction:

```bash
PYTHONPATH=<repo>/archive/legacy_python python -m pytest tests/ -q -p no:cacheprovider \
  --ignore=tests/test_autonomy.py --ignore=tests/test_render_codex.py \
  | grep -E '^(FAILED|ERROR) ' | sed 's/ - .*//' | sort
```

## Scope reverted (recorded, not silently dropped)

An initial attempt also repaired
`test_identity_spine_w1.py::test_node_entry_is_ais_signup_not_a_separate_diagnostic_route`
(`"Let's form your node."` -> rendered `"Let's see what feels like you."`). That node is
classified **DRIFT** (ledger row 41) and is registered as **`SH-09`** - *"product
presentation decision"*, explicitly *"not `SH-02`"*. The edit was reverted before commit.
The remaining failed assertions in that node (`Form my node`, `AIS_CAPABILITIES`,
`GROVE_DOMAINS`) reflect real copy/behaviour movement in `NodeEntry.tsx`; resolving them
requires a product call, not a test re-point. **No part of `SH-09` is included here.**

## Remaining uncertainty

- `SH-08` (pulse-analyze contradiction, LivingGate family) and `SH-09` (NodeEntry copy) stay
  open product/governance decisions; nodes 2, 3-8 and 41 remain red by design.
- `SH-02b` (`test_prism_pass_c_surface_ownership.py`) is already closed by merged PR #127.
- `test_prism_interior_shell.py` (nodes 10-12) needs a surface-ownership determination before
  any edit - it is not a quote-style repair.
- `test_solspire_p1_experience_01.py` (nodes 22-23): the panel survives
  (`data-testid="solariun-arkana-context-pack"`) but **both governance literals are now absent
  repo-wide** (`"CONTEXT PACK (explicit)"`, `"Not an authorization authority"`). Re-pinning the
  copy would restate a boundary the current UI no longer states, so this awaits a product
  decision on how the context-pack boundary is surfaced. Not repaired here.
- `vite build` is environment-blocked; no frontend build claim is made or implied.

## Authorization required

Sovereign review and human merge. This branch takes no authority over merge, authorization,
identity, authority-model, or constitutional architecture; creates no second mutation or
authorization path; touches no source, `api/main.py`, `LAYER_MAP.py`, ADR, or governance file.
