# Baseline Test Debt Classification ‚Äî `main` @ `a26af408`

**Workstream:** test-hygiene (standalone; explicitly *not* folded into an architectural gate)
**Authority required:** none for classification. Repairs are separate bounded tasks (see ¬ß8).
**PR:** #106 ¬∑ branch `gate-hygiene/baseline-test-debt-classification-01`
**BASE_MAIN:** `a26af408c269729a57d0a53c6ad39fcf0ca22fdf`
**Status:** classification complete ‚Äî every one of the 51 failing/error nodes is assigned a
bucket with evidence. **No test, no source file, and no policy was modified.**

> **Pass linkage (heartbeat continuity).** Pass 1 authored the classification; pass 2 (¬ß7)
> independently re-derived it and corrected the inaccuracies. PR #106 carries both.
> PR #105 (`gate10/cp10-allowlist-root-docs`) is a **separate, non-overlapping workstream** ‚Äî
> verified: no file in #105's diff is touched here, and no file here is touched by #105.

This pass exists because `PARKING_LOT.md` recorded the debt as *unclassified* and stated the
explicit precondition: _"Classify by real defect vs stale assertion before repairing."_
This document is that classification.

## 1. Measured baseline (independently reproduced)

| | value |
|---|---|
| ref | `main` @ `a26af408c269729a57d0a53c6ad39fcf0ca22fdf` |
| passed / failed / skipped / errors | **903 / 49 / 12 / 2** (invocation: `PYTHONPATH=<repo>/archive/legacy_python python -m pytest tests/ -q`; see ¬ß5 for the environment this number depends on) |
| architecture fitness (`pytest tests/architecture -q`) | **11/11 passed** |
| `api/main.py` | 2519 lines (budget 2600 ‚Äî untouched) |
| failing/error node fingerprint | `sha256 = 256204af4082a70f062ed6004fd0c51c126a14262a072afdac9279ce158c3fca` |

The fingerprint in `PARKING_LOT.md` was reproduced byte-for-byte from the 51
`FAILED`/`ERROR` node ids joined by `\n` with a trailing newline. The same 51 ids were
reproduced again from a second independent full-suite run (`--tb=line`), so the baseline is
stable, not flaky. The suite is **order-independent at this level** ‚Äî see ¬ß5.

## 2. Method

Classification used source-vs-assertion semantics, not commit dates. This is deliberate:
the clone is **grafted** (shallow ancestry), so `git log -1 -- <path>` returns the same
boundary commit for unrelated files and `git blame` is not trustworthy here. Every bucket
below is backed by a command that can be re-run.

Buckets:

- **STALE_ASSERTION** ‚Äî the implementation moved and the test still asserts a literal string
  (or symbol) that no longer exists. No user-facing capability is absent.
- **REAL_DEFECT** ‚Äî implementation and assertion disagree and the implementation is the
  side that is wrong; a genuine product/test-isolation behaviour is broken.
- **DRIFT** ‚Äî a canonical contract identifier changed; both sides are internally consistent.
  Needs a product decision, not a mechanical edit.
- **ENV / ARTIFACT** ‚Äî the test depends on something outside the repository working tree.
- **COLLECTION_ERROR** ‚Äî the module cannot be imported at all.

## 3. Bucket summary

| bucket | nodes | share |
|---|---|---|
| STALE_ASSERTION | 35 | 69% |
| DRIFT (canonical contract) | 11 | 21% |
| ENV / ARTIFACT | 2 | 4% |
| REAL_DEFECT | 1 | 2% |
| COLLECTION_ERROR | 2 | 4% |
| **total** | **51** | |

The counts above are asserted against the baseline set in Appendix A (51/51 mapped, none
missing, none extra), not counted by hand.

**The headline result:** the parked hypothesis ("several look like stale assertions rather
than defects") is **confirmed but understated**. 69% are stale assertions, and **90%** are
either stale assertions or contract drift ‚Äî i.e. **the tests are behind the code, not the
code behind the tests.** Exactly **one** node is a real defect.

## 4. Findings by bucket

### 4.1 STALE_ASSERTION ‚Äî 35 nodes

> **Verification-status note (added in the verification pass, ¬ß4.6).** The buckets were
> assigned by reading assertion text and grepping for the literal. The verification pass
> re-ran the specific nodes in ¬ß4.1‚Äì¬ß4.3 and confirmed the failure fingerprints, which is the
> strongest evidence available without a frontend build. For `test_prism_pass_c_surface_ownership.py`
> specifically, the mechanism recorded below is **not confirmed**: the module contains no
> helper and no call site containing the string `view block not found`; that string only
> exists as an f-string error message, so it cannot be grepped from a passing file. Treat the
> per-node mechanism as *inferred, unverified* and the bucket verdict as *verified* (the nodes
> fail, and they fail on moved prose/symbols).


The dominant pattern is `assert "<literal prose>" in <component source>`. The component was
rebuilt (often into a denser or routed form) and the literal was dropped. These are
**source-level string assertions**, the repo's own documented convention for `.tsx` tests,
which makes them brittle by construction: they assert copy and formatting rather than
behaviour.

Representative evidence:

- `test_prism_pass_c_surface_ownership.py` (6 nodes) ‚Äî asserts `"view block not found for
  <surface>"` for `spiral-codex`, `personal-echofeild`, `knowledge-os`, `codex`, `loops`.
  `web/public_prism/src/App.tsx:32` still declares all of those in the `View` union, but the
  render blocks were consolidated; the test's regex for a per-view block no longer matches.
- `test_ais_capability_profile_onboarding.py:40` ‚Äî asserts `'Learn. Build. Prove. Launch.'`;
  the component now renders `...ONE SYSTEM ¬∑ MANY SURFACES ¬∑ ONE CONTINUOUS FIELD`.
- `test_prism_interior_shell.py` (3) ‚Äî asserts `'Same identity ¬∑ same context ¬∑ same
  backend'` and `data-testid="prism-secondary-toggle"`. `grep` finds the former nowhere in
  `web/public_prism/src`; the shell now renders `ExperienceConsolidationFrame`.
- `test_ais_w2_living_gate_grove_handoff.py` (6) ‚Äî five are copy/regex drift in
  `pages/LivingGate.tsx`: the test pins an exact `useState<FlowStep>(initialMode === 'reset'
  ? 'reset' : 'diagnostic')` expression that no longer matches, requires `'Open Spiral Grove'`
  and `'invitation'` copy, and requires the literal `'/api/pulse/analyze'`. **The endpoint is
  preserved** ‚Äî `api/pulse.py:272` still defines `@router.post("/api/pulse/analyze")`; the
  component now calls it through the canonical client (`lib/apiClient` `apiFetch`), so only
  the call-site string is stale. The sixth node,
  `test_no_firebase_persistence_in_gate`, fails on `assert "sessionStorage" not in src`;
  `LivingGate.tsx:61-80,207,218` uses `sessionStorage` for a transient, tab-scoped
  diagnostic handoff (`arkadia.ais.diagnostic-handoff.v1`). **No Firebase and no durable
  persistence was added** ‚Äî the assertion is simply broader than its stated intent. See the
  borderline note below.
- `test_spiral_grove_chambers.py`, `test_spiral_grove_frontend_projection.py`,
  `test_spiral_grove_learning_path_projection.py` ‚Äî all three target `web/public_prism/src/components/spiral-grove/CapabilityChamber.tsx` and assert the copy
  `'Evidence is separate.'` / `'Evidence submission, assessment, ...'` which the current
  `CapabilityChamber.tsx` and fail solely on the copy string `'Evidence is separate.'` / `'Evidence submission, assessment, and capability-state updates remain separate downstream stages.'` (`grep -c` -> 0). **The governance properties those tests exist to protect are intact.** Verified present in the file: `'SG-03 activity contract'` (2), `'mutate learner capability state'` (1), `prerequisites: GroveCapability[]`, `GroveCapability`, `LearnerCapabilityState`; verified **absent**: `generateExercise` (0) and `createEvidence` (0). The chamber still does not autonomously generate or adjudicate - only the prose was reworded. Re-pinning the copy restores these without weakening the boundary.

  > **CORRECTED — see §11.** This classification is **wrong in causal direction**. The SG-04
  > expectations were never satisfied by this surface at any revision, and the merge
  > `1363c65` (PR #1, `sg-04-learning-activity-runtime`) resolved the conflict in favour of
  > the **older** content. The nodes are therefore a merge **CONTRADICTION**, not
  > stale-assertion drift, and the *mount* expectations need a product decision before any
  > repair. Do not re-pin the copy in isolation.
- `test_solspire_p1_experience_01.py` (2) ‚Äî asserts `'CONTEXT PACK (explicit)'` and
  `'Not an authorization authority'` in
  `web/public_prism/src/components/solspire/SolSpireExperience.tsx`. Both literals are
  **absent** (`grep -c` ‚Üí 0). The testid the test also checks *is* still present
  (`data-testid="solariun-arkana-context-pack"`), but the panel now renders the label
  `CURRENT CONTEXT`. So the Arkana context pack exists; the copy/packaging changed. Genuine
  copy drift, not an absent capability.
- `test_weaver_sci_boundary_01.py` (3), `test_weaver_sci_contract_01.py` (2),
  `test_weaver_mvp2_08.py` (1) ‚Äî the "nexus‚Üínovanet" family. The assertion looks for
  `v === 'nexus' ? 'novanet'`; `App.tsx:114` now reads
  `if (requested === 'nexus') next = {view:'novanet',path:'/nexus'}`. Same intent, different
  expression. The same family also asserts `'ProjectDashboard'` inside
  `SolSpireConsole.tsx`; that page is now a 4-line re-export of `EnterpriseConsole`
  (`return <EnterpriseConsole {...props}/>`), and the project workspace moved into
  `SolSpireExperience.tsx` (which mounts `ResilientProjectDashboard`). `ProjectDashboard`
  itself still exists at `pages/ProjectDashboard.tsx` and is asserted successfully there by
  `test_m04_projects.py` ‚Äî so the surface is intact and only the assertion's location
  assumption is stale.
- `test_solariun_experience_consolidation_01.py` (3) ‚Äî asserts `'searchKnowledge'` and
  `data-testid="experience-inspector"` in `ExperienceConsolidationFrame.tsx`, which now
  renders only `data-experience-surface`; and asserts `'Merge: human_only'` in the
  consolidation map, which is not present.
- `test_ais_w6_future_skills_challenge.py`, `test_ais_w8_canonical_identity.py` (2),
  `test_identity_spine_w1.py` (2), `test_solspire_p1_experience_01.py` ‚Äî same copy/symbol
  drift in `.tsx` and in the identity-seed module (asserting `_SPINE_KEY = "identity_spine"`
  and `'"ais_capability_portfolio"'` against a module that now emits `'identity_spine'` as a
  dict key).
- `test_steward_filter.py` (3) ‚Äî asserts `steward_filter("You have transcended") is None`
  while `weaver/filters/steward.py` forbids `"transcendent"`, not `"transcended"`; and
  `compress_to_choices` no longer drops the `'More noise'` sentence. Borderline: the
  stem-matching gap is arguably a real content-hygiene hole. Logged as `SH-06` in ¬ß8 with a
  product judgement, not auto-repaired.
- `test_ais_capability_profile_onboarding.py` (1 node, counted above).

### 4.2 DRIFT ‚Äî canonical contract identifier changed ‚Äî 11 nodes

These are **not** copy drift. A canonical machine-readable identifier changed, and the
identifier is asserted consistently across several tests while the code emits a different,
self-consistent value. Fixing them is a product/contract decision, not a test edit.

- `test_weaver_w5.py::test_derived_graph_provenance` and `::test_http_knowledge_isolation`
  (2 nodes, incl. the `/solspire/projects/{id}/knowledge/graph` route) assert
  `kind == "DERIVED"`; `solspire/semantic_graph.py:112` emits
  `"DERIVED_BOUNDED_SEMANTIC"`, and `tests/test_weaver_mvp2_05.py:24` asserts the **new**
  value. Two tests in the same suite encode opposite contracts ‚Äî the identifier was
  deliberately widened (W5) and these two were not migrated.
- `test_spiral_grove_registry.py::test_ais_catalog_supports_progressive_creative_workflow`
  asserts prerequisites `["cap-ai-prompt-engineering", "cap-digital-intelligence",
  "cap-content-systems"]`; `spiral_grove/registry.py` now declares only
  `["cap-digital-intelligence"]` for that capability. The catalog was re-parented.
- `test_spiral_grove_registry.py::test_registry_rejects_prerequisite_cycle` expects
  `CapabilityCycleError`; `registry.py:118` raises `UnknownCapabilityError` first because it
  validates membership before cycles. Whether cycle detection is still reachable is
  unverified ‚Äî flagged as `SH-04` in ¬ß8 (and RESOLVED in the verification pass).
- `test_m02_reasomate_truth.py::test_oracle_runtime_uses_the_shared_session_key` asserts
  `"arkanaSessionId"` in `components/ArkanaCommune.tsx`. `grep -c` returns **0**. The
  requirement ‚Äî Oracle and ReasoMate keying one longitudinal thread on a shared session id ‚Äî
  is **genuinely not satisfied by that symbol**; the test is a correct assertion against a
  capability that is currently absent. Grouped under DRIFT because the requirement is
  architectural, not a copy string.
- `test_engineering_scheduler_bootstrap.py::test_dry_run_evidence` ‚Äî `EngineeringRouter.run()`
  returns `NO_LEGAL_MOVE` instead of `READY_FOR_REVIEW`, and
  `::test_blocked_dependency_skips_move` then hits `TypeError: 'NoneType' object is not
  subscriptable` because `select_next_move` returns `None`. The scheduler finds no legal move
  in the checked-in trajectory ‚Äî the trajectory and the scheduler have drifted apart.
- `test_ais_w8_canonical_identity.py` (2) and `test_identity_spine_w1.py` (2) counted here
  overlap ¬ß4.1; they assert canonical symbol names (`load_user_profile_store(user["uid"])`)
  that the current spine module does not expose. Canonical-identity surface is W8 territory
  and requires identity-boundary care ‚Äî **not** touched by this pass.

### 4.3 ENV / ARTIFACT ‚Äî 2 nodes

- `test_gate_serve_script.py::test_root_index_redirect_and_script_exists` ‚Äî asserts
  `Path('index.html').exists()` relative to CWD.
- `test_gate_status.py::test_gate_files_and_fetch_handling` ‚Äî asserts `Path('gate/index.html')`.
- Neither `index.html` nor `gate/` exists at the repository root. They exist only under
  `static/index.html` and `archive/legacy_frontend/gate/index.html`. `conftest.py` does not
  `chdir`. These tests reference a served-artifact layout that is not in the tree.

### 4.4 REAL_DEFECT ‚Äî 1 node

- `test_m01_persistence.py::test_db_path_honours_data_dir_env` ‚Äî **test-isolation defect,
  reproduced and root-caused.**

  It passes in isolation (**13/13**) and fails in the full suite:

  ```
  E  - /tmp/arkadia_m01_vy0q181d/solspire_projects.db
  E  + /tmp/arkadia_echofeild_u4j95395/solspire_projects.db
  ```

  `tests/test_echofeild_aggregator.py:27` sets `os.environ["SOLSPIRE_PROJECTS_DB"]` at module
  import time and never restores it. `solspire/project_store.py:19` gives
  `SOLSPIRE_PROJECTS_DB` **precedence** over `SOLSPIRE_DATA_DIR`, so the later
  `importlib.reload` in the M01 test picks up the leaked value and `SOLSPIRE_DATA_DIR` is
  ignored. Minimal reproduction:

  ```
  pytest tests/test_echofeild_aggregator.py \
         tests/test_m01_persistence.py::test_db_path_honours_data_dir_env -q
  ‚Üí 1 failed, 15 passed
  ```

  This is a real defect in the **test substrate**, not in product code. It is the only node
  in the baseline whose pass/fail depends on test execution order, which means the recorded
  fingerprint is only valid for the full-suite invocation ‚Äî a second reason to repair it.

### 4.5 COLLECTION_ERROR ‚Äî 2 nodes

Both are the documented, pre-existing collection errors and are unchanged by this pass:

- `tests/test_autonomy.py` ‚Äî `load_autonomy_config` is not importable.
- `tests/test_render_codex.py` ‚Äî imports `archive/legacy_python/codex_brain.py`, which imports
  `arkadia_drive_sync` (absent). `AGENTS.md` records this as expected when
  `PYTHONPATH=<repo>/archive/legacy_python` is set.

### 4.6 Governance-invariant verification (added this pass)

The initial classification read the assertion text and grepped for the literal. A follow-up
pass opened the target files and checked the *properties each test exists to protect* - so a
"stale copy" verdict is not covering a real hole. Results:

| Node(s) | Stale claim | Verified intact | Verified absent |
|---|---|---|---|
| grove chambers / frontend_projection / learning_path_projection | `'Evidence is separate.'` copy | `SG-03 activity contract`, `mutate learner capability state`, `prerequisites: GroveCapability[]`, `LearnerCapabilityState` | `generateExercise`, `createEvidence` |
| w2 living_gate (pulse node) | literal `'/api/pulse/analyze'` in the component | endpoint `@router.post("/api/pulse/analyze")` at `api/pulse.py:272`, called via `lib/apiClient` | - |
| w2 living_gate (`sessionStorage` node) | `assert "sessionStorage" not in src` | no Firebase added; handoff is tab-scoped and cleared (`LivingGate.tsx:207,218`) | durable/local persistence |
| solariun consolidation (`Merge: human_only`) | literal `Merge: human_only` in the frame component | **corrected target:** `docs/architecture/SOLARIUN_EXPERIENCE_CONSOLIDATION_01_MAP.md` carries `**Merge:** human_only`, `**Deploy:** human_only`, `Human authority remains above all display/navigation surfaces`, `Discovery ‚âÝ authorization` (U+2260) | no `human_only` literal in any `.tsx` |
| solariun consolidation (frame) | `searchKnowledge` et al. in the frame | `SearchOverlay`, `ContextBar`, `ArkanaOverlay`, `searchKnowledge` in canonical owner `SolSpireExperience.tsx` | - |

**Conclusion:** no governance invariant was found broken. Every one of these is copy,
location, or expression drift, and STALE_ASSERTION is not concealing a capability or
boundary regression.

**Correction to the initial pass.** Two claims in the first draft were wrong and are now
fixed in place: (a) the SolSpire P1 literals live in
`components/solspire/SolSpireExperience.tsx`, not `SolSpireConsole.tsx`; (b) the W2
assertions target `pages/LivingGate.tsx` via regex, not `NodeEntry.tsx`. Both were
path-attribution errors, not classification errors - the bucket verdicts are unchanged.

**New finding (not previously recorded).** `web/public_prism/src/components/experience-consolidation.css`
still styles `.experience-inspector` (7 rules), and `.experience-inspector` is referenced
nowhere in any `.tsx` file. The consolidation test asserts
`data-testid="experience-inspector"` in the frame, so this is a deliberately removed
surface whose stylesheet was left behind - dead CSS plus a stale assertion. Purely cosmetic;
no behavioural effect. Strengthens the STALE_ASSERTION verdict for that node and adds a
small bounded cleanup candidate (see section 8).

## 5. Regression boundary

- Fingerprint `256204af‚Ä¶83fca` is reproduced and **must remain unchanged** by any future
  hygiene pass except where that pass explicitly claims the node.
- **Environment-dependent baseline (verification pass).** The fingerprint `256204af‚Ä¶83fca` is
  the fingerprint of *this invocation environment* only. The suite's outcome depends on which
  optional deps are importable: `tests/test_m08_trajectory_schema.py:38` and
  `tests/test_m09_worker_contract.py:55` gate on `pytest.importorskip("jsonschema")`. Confirmed
  by direct run with `jsonschema` absent (`9 passed, 2 skipped`), and `jsonschema` **is** absent
  from this environment, so 2 of the 12 skips are dependency-gated. Install `jsonschema` and the
  pass/skip split changes, so the recorded counts and fingerprint are not portable unless the
  invocation is pinned (as amended in ¬ß1).
- **`test_prism_pass_c_surface_ownership.py` must not be attributed to a helper.** The module
  has no call site referencing `view block not found`; the string exists only as the f-string
  text of an `assert m, ...`. The 6 "nodes" are the `@pytest.mark.parametrize` case ids
  Python generates from the f-string, not greppable source lines.
- Architecture fitness is **11/11** and no `REGISTERED_ARCHITECTURAL_DEBT` was touched.
- Working tree after two full-suite runs: **0 untracked files, 0 files under `vault/`** ‚Äî
  the GATE-VAULT guardrail (`vault/**` gitignored, `conftest.py` sandbox) is holding.
- `api/main.py` was not touched; no boot-code `py_compile` gate was required.

## 6. Remaining uncertainty

> **Resolved in the verification pass:** the two items below that were open questions in the
> first draft are now answered; the answers are stated inline and the item is resolved.

- `test_registry_rejects_prerequisite_cycle` ‚Äî **RESOLVED: no defect, and the name is
  misleading.** Cycle detection *is* reachable: `CapabilityRegistry([cap-a‚Üícap-a])` (a
  self-prerequisite) raises `CapabilityCycleError`. The test's two-node a‚Üîb case raises
  `UnknownCapabilityError('cap-b')` only because `ReferenceValidator._validate_references`
  runs the membership loop to completion before the first `graph_validate_cycle` call, and
  registration is incremental ‚Äî `cap-b` is not yet a member when `cap-a` is registered. The
  test asserts `pytest.raises(CapabilityCycleError)`, which is *not* a superclass of
  `UnknownCapabilityError`, so the test is genuinely wrong about ordering, not about cycles.
  No dead code; the library already exposes the correct exception.
- **New, cleaner STALE_ASSERTION case discovered:** the same test module expects the
  *transitive* prerequisite closure of `cap-ai-creative-workflows` to be exactly
  `[cap-ai-prompt-engineering, cap-digital-intelligence, cap-content-systems]`. The registry
  correctly returns `[cap-digital-intelligence, cap-ai-prompt-engineering, cap-content-systems]`
  ‚Äî a set-correct answer in a different order, asserting list equality. This is an ordering
  brittleness, not a capability regression.
- `test_steward_filter.py` ‚Äî the `"transcended"` vs `"transcendent"` gap is a plausible real
  content-hygiene hole rather than pure copy drift. Requires a product judgement. **Still open.**
- The `.tsx` stale assertions were classified from the assertion text plus a targeted `grep`
  for the literal, not by rendering the components. No frontend build was run
  (`pnpm build` is environment-blocked), so "the capability is absent" is asserted only for
  the literal, which is the correct standard for a source-level string assertion. A follow-up pass (section 4.6) did open the target files and verify the *governance properties* behind the copy assertions (endpoint existence, `generateExercise`/`createEvidence` absence, human-only merge authority, `sessionStorage` scope). That raises confidence from "the literal moved" to "the invariant is intact" for those nodes, but it still does not constitute a rendered-UI verification.

## 7. Verification pass (independent re-check of this document)

A second pass re-derived this document's factual claims from the repository rather than
trusting the prose. Confirmed accurate: the measured baseline `903/49/12/2`, architecture
`11/11`, `api/main.py` = 2519 lines, the `SOLSPIRE_PROJECTS_DB` precedence at
`solspire/project_store.py:19`, the missing root `index.html` / `gate/index.html` versus
`archive/legacy_frontend/gate/index.html`, `conftest.py` having no `chdir`, and the
REAL_DEFECT root cause.

Corrections and additions made in this pass (all in place above):

| # | Claim as first written | Verified reality | Where corrected |
|---|---|---|---|
| C1 | fingerprint treated as a portable contract | environment-dependent ‚Äî `jsonschema` gated skips | ¬ß1, ¬ß5 |
| C2 | `test_prism_pass_c_surface_ownership.py` asserts a `"view block not found"` helper per surface | no such call site exists; string is only an f-string message; the 6 nodes are parametrize case ids | ¬ß4.1, ¬ß5 |
| C3 | `test_registry_rejects_prerequisite_cycle` ‚Äî cycle detection may be dead code | not dead; reachable via self-prerequisite; the test's a‚Üîb case fails on validation *ordering* | ¬ß6 |
| C4 | `Merge: human_only` asserted in the frame `.tsx` | no `human_only` literal in any `.tsx`; the assertion target is `SOLARIUN_EXPERIENCE_CONSOLIDATION_01_MAP.md`, and the map uses `Discovery ‚âÝ authorization` (U+2260) not `!=` | ¬ß4.6 table |
| C5 | (new) registry transitive-closure ordering brittleness | `cap-ai-creative-workflows` closure is set-correct but order-differs | ¬ß6 |
| C6 | (refinement) dead CSS `experience-inspector` = "7 rules" | 8 rule blocks total ‚Äî 7 base selectors (`.css:72‚Äì86`) plus 1 responsive override (`.css:121`); "7" counts the base block only, which is defensible | ¬ß4.6 prose |

Nothing in this pass changes a bucket verdict. No test, source, or policy file was modified;
the only file touched is this evidence document.

## 8. Proposed next bounded tasks (NOT executed here)

Per `NO SELF-EXPANSION`, these are **proposed**, classified, dependency-linked and bounded.
None is authorised by this pass.

| id | task | bucket | risk | depends on |
|---|---|---|---|---|
| `SH-01` | **Repair the `SOLSPIRE_PROJECTS_DB` env leak** in `tests/test_echofeild_aggregator.py` (use `monkeypatch.setenv`) so the baseline is order-independent. | REAL_DEFECT | low | none |
| `SH-02` | Migrate the 35 stale string assertions to behaviour-level assertions (or refresh literals), file by file, in bounded batches. | STALE_ASSERTION | low | none |
| `SH-03` | Resolve the `"DERIVED"` vs `"DERIVED_BOUNDED_SEMANTIC"` contract split across `test_weaver_w5` / `test_weaver_mvp2_05`. | DRIFT | medium | product decision |
| `SH-04` | Verify whether `CapabilityRegistry` cycle detection is reachable. | DRIFT | medium | none |
| `SH-05` | Decide the fate of `test_gate_serve_script` / `test_gate_status` (repair the path, or retire the tests as archival). | ENV | low | sovereign call |
| `SH-06` | Decide whether `steward_filter` should stem-match `transcend*`. | STALE_ASSERTION | medium | product judgement |
| `SH-07` | Migrate `test_m02_reasomate_truth::test_oracle_runtime_uses_the_shared_session_key` ‚Äî the shared-session requirement is genuinely unmet in `ArkanaCommune.tsx`. | DRIFT | **high** | architectural gate |

**Recommended first:** `SH-01`. It is a one-line test-hygiene fix, it removes the only
order-dependent node, and it makes the baseline fingerprint reproducible under any
invocation order ‚Äî which every later hygiene task depends on.

## 9. Deliberate non-edit: `PARKING_LOT.md` is left untouched

`PARKING_LOT.md` is the natural home for the status change on the parked item
("unclassified" ‚Üí classified). It is **intentionally not modified here.**

Open PR **#105** rewrites the same `## Open Items` anchor ‚Äî it replaces `_None._` with the
CP10 and baseline-debt entries. Editing that anchor on this branch would guarantee a textual
conflict in a file the sovereign must merge by hand, for zero engineering benefit.

Deferred: once #105 lands, a one-line follow-up updates the parked item to point at this
document. Until then this evidence file is the single source of truth for the classification.

## 10. Authorization

Classification only. No merge, no authorization, no identity-boundary change. The sovereign
decides which of `SH-01`‚Ä¶`SH-07` become canonical work.

## Appendix A ‚Äî complete node-to-bucket map

All **51** baseline nodes, assigned programmatically from the run output and
asserted to cover the baseline set exactly (no hand transcription).

```bash
PYTHONPATH=<repo>/archive/legacy_python python -m pytest tests/ -q \
  -p no:cacheprovider --continue-on-collection-errors \
  | grep -E '^(FAILED|ERROR) ' | sed 's/ - .*//' | sort
```

| # | node | kind | bucket |
|---|---|---|---|
| 1 | `tests/test_agent_run.py::test_agent_run_writes_and_commits` | FAILED | STALE_ASSERTION |
| 2 | `tests/test_ais_capability_profile_onboarding.py::test_home_is_offer_led_and_keeps_arkadia_entry_points` | FAILED | STALE_ASSERTION |
| 3 | `tests/test_ais_w2_living_gate_grove_handoff.py::test_app_wires_grove_navigation` | FAILED | STALE_ASSERTION |
| 4 | `tests/test_ais_w2_living_gate_grove_handoff.py::test_ims_lineage_preserved` | FAILED | STALE_ASSERTION |
| 5 | `tests/test_ais_w2_living_gate_grove_handoff.py::test_living_gate_defaults_to_diagnostic_not_reset` | FAILED | STALE_ASSERTION |
| 6 | `tests/test_ais_w2_living_gate_grove_handoff.py::test_no_firebase_persistence_in_gate` | FAILED | STALE_ASSERTION |
| 7 | `tests/test_ais_w2_living_gate_grove_handoff.py::test_pulse_analyze_endpoint_preserved` | FAILED | STALE_ASSERTION |
| 8 | `tests/test_ais_w2_living_gate_grove_handoff.py::test_spiral_grove_handoff_prop_and_cta` | FAILED | STALE_ASSERTION |
| 9 | `tests/test_ais_w6_future_skills_challenge.py::test_w6_is_self_guided_and_timed` | FAILED | STALE_ASSERTION |
| 10 | `tests/test_prism_interior_shell.py::test_authenticated_interior_uses_one_prism_shell` | FAILED | STALE_ASSERTION |
| 11 | `tests/test_prism_interior_shell.py::test_shell_exposes_canonical_primary_surfaces` | FAILED | STALE_ASSERTION |
| 12 | `tests/test_prism_interior_shell.py::test_shell_exposes_secondary_nexus_lenses` | FAILED | STALE_ASSERTION |
| 13 | `tests/test_prism_pass_c_surface_ownership.py::test_codex_resolves_to_solspire_codex` | FAILED | STALE_ASSERTION |
| 14 | `tests/test_prism_pass_c_surface_ownership.py::test_echo_field_aliases_resolve_to_solspire_field` | FAILED | STALE_ASSERTION |
| 15 | `tests/test_prism_pass_c_surface_ownership.py::test_knowledge_os_resolves_to_solspire_knowledge` | FAILED | STALE_ASSERTION |
| 16 | `tests/test_prism_pass_c_surface_ownership.py::test_loops_resolves_to_solspire_loops` | FAILED | STALE_ASSERTION |
| 17 | `tests/test_prism_pass_c_surface_ownership.py::test_spiral_codex_not_solspire_field` | FAILED | STALE_ASSERTION |
| 18 | `tests/test_prism_pass_c_surface_ownership.py::test_spiral_codex_uses_feed_component` | FAILED | STALE_ASSERTION |
| 19 | `tests/test_solariun_experience_consolidation_01.py::test_area_c_solspire_substrate_uses_existing_search_and_context_grammar` | FAILED | STALE_ASSERTION |
| 20 | `tests/test_solariun_experience_consolidation_01.py::test_preimplementation_map_is_present_and_bounded` | FAILED | STALE_ASSERTION |
| 21 | `tests/test_solariun_experience_consolidation_01.py::test_responsive_composition_and_inspector_exist` | FAILED | STALE_ASSERTION |
| 22 | `tests/test_solspire_p1_experience_01.py::test_p1_1_arkana_context_pack` | FAILED | STALE_ASSERTION |
| 23 | `tests/test_solspire_p1_experience_01.py::test_p1_1_not_authorization` | FAILED | STALE_ASSERTION |
| 24 | `tests/test_spiral_grove_chambers.py::test_chamber_does_not_invoke_autonomous_generation_or_adjudication` | FAILED | STALE_ASSERTION |
| 25 | `tests/test_spiral_grove_frontend_projection.py::test_activity_draft_persistence_is_local_and_not_evidence` | FAILED | STALE_ASSERTION |
| 26 | `tests/test_spiral_grove_learning_path_projection.py::test_evidence_assessment_state_are_downstream` | FAILED | STALE_ASSERTION |
| 27 | `tests/test_steward_filter.py::test_allows_mythic_with_action` | FAILED | STALE_ASSERTION |
| 28 | `tests/test_steward_filter.py::test_blocks_identity_claims` | FAILED | STALE_ASSERTION |
| 29 | `tests/test_steward_filter.py::test_compress_to_choices` | FAILED | STALE_ASSERTION |
| 30 | `tests/test_weaver_mvp2_08.py::test_nexus_novanet_canonical_routing_intact` | FAILED | STALE_ASSERTION |
| 31 | `tests/test_weaver_sci_boundary_01.py::test_nexus_novanet_alias_intact` | FAILED | STALE_ASSERTION |
| 32 | `tests/test_weaver_sci_boundary_01.py::test_product_nav_is_not_operator_authority` | FAILED | STALE_ASSERTION |
| 33 | `tests/test_weaver_sci_boundary_01.py::test_solspire_owns_project_workspace_not_global_command` | FAILED | STALE_ASSERTION |
| 34 | `tests/test_weaver_sci_contract_01.py::test_nexus_novanet_alias_intact` | FAILED | STALE_ASSERTION |
| 35 | `tests/test_weaver_sci_contract_01.py::test_solspire_is_workspace_not_second_sci` | FAILED | STALE_ASSERTION |
| 36 | `tests/test_ais_w8_canonical_identity.py::test_w8_ais_projection_reuses_authenticated_uid` | FAILED | DRIFT |
| 37 | `tests/test_ais_w8_canonical_identity.py::test_w8_no_second_authentication_or_identity_store_is_created` | FAILED | DRIFT |
| 38 | `tests/test_engineering_scheduler_bootstrap.py::test_blocked_dependency_skips_move` | FAILED | DRIFT |
| 39 | `tests/test_engineering_scheduler_bootstrap.py::test_dry_run_evidence` | FAILED | DRIFT |
| 40 | `tests/test_identity_spine_w1.py::test_ais_profile_exposes_canonical_identity_spine` | FAILED | DRIFT |
| 41 | `tests/test_identity_spine_w1.py::test_node_entry_is_ais_signup_not_a_separate_diagnostic_route` | FAILED | DRIFT |
| 42 | `tests/test_m02_reasomate_truth.py::test_oracle_runtime_uses_the_shared_session_key` | FAILED | DRIFT |
| 43 | `tests/test_spiral_grove_registry.py::test_ais_catalog_supports_progressive_creative_workflow` | FAILED | DRIFT |
| 44 | `tests/test_spiral_grove_registry.py::test_registry_rejects_prerequisite_cycle` | FAILED | DRIFT |
| 45 | `tests/test_weaver_w5.py::test_derived_graph_provenance` | FAILED | DRIFT |
| 46 | `tests/test_weaver_w5.py::test_http_knowledge_isolation` | FAILED | DRIFT |
| 47 | `tests/test_gate_serve_script.py::test_root_index_redirect_and_script_exists` | FAILED | ENV / ARTIFACT |
| 48 | `tests/test_gate_status.py::test_gate_files_and_fetch_handling` | FAILED | ENV / ARTIFACT |
| 49 | `tests/test_m01_persistence.py::test_db_path_honours_data_dir_env` | FAILED | REAL_DEFECT |
| 50 | `tests/test_autonomy.py` | ERROR | COLLECTION_ERROR |
| 51 | `tests/test_render_codex.py` | ERROR | COLLECTION_ERROR |


---

## 11. Correction pass — SG-04 merge CONTRADICTION and live-vs-ledger drift

**Pass type:** documentation/evidence correction only. No test, source, policy, workflow, or
governance file is modified by this section.
**Reconstructed at:** `main` @ `4164573586860b9c7e04e1815bca4957559046a2` (PR #128).
**Supersedes for SG-04:** §4.1's SG-04 paragraph above (left in place, annotated in-line).

### 11.1 Why §4.1's SG-04 classification is wrong

§4.1 read the SG-04 nodes as ordinary stale-assertion drift ("the implementation moved and
the test still asserts a literal string that no longer exists"). Two independent checks
contradict that reading.

**(a) The tests' "inline work surface" expectations were never implemented — not by the
current file, and not by any revision of it:**

`test_spiral_grove_chambers.py:55` and `test_spiral_grove_frontend_projection.py:94` both
assert `data-testid="learning-activity-work-surface"` in
`web/public_prism/src/components/spiral-grove/CapabilityChamber.tsx`. Scanning every
historical revision of that file:

```bash
C=web/public_prism/src/components/spiral-grove/CapabilityChamber.tsx
git log --format=%h -- $C | while read c; do
  n=$(git show $c:$C 2>/dev/null | grep -c 'learning-activity-work-surface')
  [ "$n" != "0" ] && echo "$c -> $n"
done
```

returns `ff80b8c`, `44e1c99`, `70568eb`, `b8aca42`, `b9aafc1`, `cfb73b6`, `012ef5e` — all
**SG-03 / AIS** revisions that predate SG-04 — and **never** the SG-04 revisions `74f5494`,
`1b63994`, `06ad5f2`, nor current `main`. The SG-04 commits did the opposite: they *removed*
the inline card in favour of a mounted `<ActivityRuntime/>`:

```bash
for c in 74f5494 1b63994 06ad5f2 origin/main; do
  printf "%s mount=%s\n" "$c" "$(git show $c:$C | grep -c '<ActivityRuntime')"
done
# 74f5494 mount=1   1b63994 mount=1   06ad5f2 mount=1   main mount=0
```

So the "inline surface" assertions (§4.1's `STALE_ASSERTION`) and the "runtime is mounted"
assertions (`tests/test_spiral_grove_activity_runtime.py`, also failing) **cannot both pass
against any single revision in this repository's history.** This is not drift; it is two
mutually exclusive expectations.

**(b) The SG-04 branch tip `06ad5f2` was itself red — the merge did not regress a green
branch.** Measured in a worktree at the branch tip (`git worktree add /tmp/sg04wt 06ad5f2`):
`7 failed, 25 passed` on the SG-04 test set. The mechanism is a conflict resolution that
kept the wrong side:

| revision | `CapabilityChamber.tsx` blob |
|---|---|
| `077f30a` — main before the SG-04 merge | `5c78fcbc…` |
| `4c50fb4` — SG-04 branch, merge of main | `cef5a593…` (mount present, 36 insertions) |
| `ff80b8c` — merge of `4c50fb4` + main | `0cde2f78…` |
| `origin/main` @ `4164573` | `0cde2f78…` — **identical to `ff80b8c`** |

`ff80b8c` is a commit **on main's own history**, and its content is what shipped. Its
`CapabilityChamber.tsx` carries the legacy `<ActivityCard/>` + inline draft capture
(the `ACTIVITY_DRAFT_PREFIX` declaration is present, with **zero** uses) and **drops** the
`<ActivityRuntime/>` mount — i.e. the merge took main's side and discarded the branch's
integration for this file. `ActivityRuntime.tsx` survived, but nothing renders it.

**Also under-implemented on the SG-04 side, independent of any merge:**
`tests/test_spiral_grove_activity_runtime.py:41` asserts
`data-testid="activity-surface-research"`, and that string appears in **no revision** of
`ActivityRuntime.tsx` (only `74f5494`, `1b63994`, `06ad5f2` exist). The suite as written
never had a passing state.

**Verdict.** The seven currently-failing SG-04 nodes are a **merge CONTRADICTION**:
the merged artefact does not satisfy its own suite, the suite is internally
mutually-exclusive, and part of it was never implemented. Repairing it requires choosing
between two activity surfaces — and the TDD-native reading (green the assertions as written)
points at a **frontend capability change** in `web/public_prism/**`, which is outside this
workstream's test-only boundary and is CP10 path-filtered (`sg-02-fe-2-v.yml`). It is
therefore **escalated, not auto-repaired**. Bucket reclassification proposed below.

### 11.2 Proposed bucket reclassification (nodes present today)

| node | §4.1 bucket | proposed | reason |
|---|---|---|---|
| `test_spiral_grove_activity_runtime.py::test_runtime_is_mounted_by_the_capability_chamber` | — (file absent at `a26af408`) | CONTRADICTION | merge dropped the mount |
| `…::test_chamber_preserves_sg03_downstream_boundary` | — | CONTRADICTION | same merge, same file |
| `…::test_runtime_dispatches_all_eight_kinds_to_deterministic_renderers` | — | REAL_DEFECT | `activity-surface-*` never implemented |
| `…::test_spiral_grove_uses_the_nexus_canonical_header` | — | STALE_ASSERTION | copy/header relocation — safe standalone repair |
| `test_spiral_grove_chambers.py::test_chamber_does_not_invoke_autonomous_generation_or_adjudication` | STALE_ASSERTION | CONTRADICTION | inline `'Evidence is separate.'` vs mounted runtime |
| `test_spiral_grove_frontend_projection.py::test_activity_draft_persistence_is_local_and_not_evidence` | STALE_ASSERTION | CONTRADICTION | inline surface expected, runtime mounted |
| `test_spiral_grove_learning_path_projection.py::test_evidence_assessment_state_are_downstream` | — | CONTRADICTION | inline surface expected, runtime mounted |

Governance invariant unchanged: the chamber still does not autonomously generate or
adjudicate (`generateExercise` / `createEvidence` both absent), and the SG-03 downstream
boundary is still enforced by `test_ais_w5_evidence_capture.py` (`activity-draft.v1`,
`activity.evidence_required`) — which **passes** on the pre-SG-04 shape that main actually
carries.

### 11.2.1 Correction (SH-02e, measured on `main` @ `df7a99a`)

The §11.2 table is a **proposal from the `4164573` measurement**, not a live inventory.
Re-measured at `df7a99a`, all three `STALE_ASSERTION → CONTRADICTION` reclassifications are
**already resolved and green**:

| node | §11.2 proposed | measured at `df7a99a` |
|---|---|---|
| `test_spiral_grove_chambers.py::test_chamber_does_not_invoke_autonomous_generation_or_adjudication` | CONTRADICTION | **PASSES** |
| `test_spiral_grove_learning_path_projection.py::test_evidence_assessment_state_are_downstream` | CONTRADICTION | **PASSES** |
| `test_spiral_grove_frontend_projection.py::test_activity_draft_persistence_is_local_and_not_evidence` | CONTRADICTION | **PASSES** |

This matters because the proposed remedy for those three rows was "align the test with the
mounted runtime" — i.e. relax a boundary assertion. On the current shape the boundary
assertions hold **as written**, so acting on the §11.2 remedy would replace passing
boundary guards with weaker ones for no gain. That is a silent regression of the
autonomous-generation / downstream-evidence boundary, not test hygiene.

**Rule for the SG-04 escalation:** the ungreen SG-04 set is now exactly the four nodes in
`tests/test_spiral_grove_activity_runtime.py`
(`…is_mounted_by_the_capability_chamber`, `…chamber_preserves_sg03_downstream_boundary`,
`…dispatches_all_eight_kinds_to_deterministic_renderers`,
`…uses_the_nexus_canonical_header`). Repairing those requires choosing between two activity
surfaces in `web/public_prism/**` — still a **frontend capability change**, outside the
test-only boundary and CP10 path-filtered. The escalation stands; the §11.2 bucket list must
be re-measured before it is acted on, and the three now-green nodes must **not** be touched.

### 11.3 Live-vs-ledger node drift (measured, `main` @ `4164573`)

Measured fingerprint: **39 failed / 1018 passed / 13 skipped / 2 errors (41 nodes)**;
`tests/architecture` **11/11**; `api/main.py` 2519 / 2600 lines.

Diffing the live node list against §Appendix A's 51 rows (`comm`, by node **name**):

**18 ledger nodes now pass** — repaired by PRs #104→#128, plus `test_weaver_w5.py` ×2,
`test_prism_pass_c_surface_ownership.py` ×6 (SH-02b), and
`test_solariun_experience_consolidation_01.py` ×3.

**4 live nodes absent from the ledger** (their suites post-date `a26af408`) — all fail
against `main`:

| node | observed failure | classification |
|---|---|---|
| `test_solspire_r1_governance_convergence.py::test_r1_solspire_builders_delegate_to_weaver` | `AssertionError: 'mvp1-50c0ee9b89' == 'mvp1-r1-patch'` — `pass_id` not delegated | **REAL_DEFECT** |
| `…::test_r1_weaver_governance_is_canonical` | `'execute_patch'` absent from `weaver/governance.py` | **REAL_DEFECT** |
| `test_solspire_r2_github_mutation.py::test_legacy_commit_file_fails_closed_without_network_write` | `KeyError: 'code'` — `gh.commit_file` returns no `code` key | **REAL_DEFECT** (fail-closed **works**; error contract drifted) |
| `test_solspire_r3_execution_runtime.py::test_runtime_is_explicitly_non_governed_and_blocks_mutation_tools` | `PermissionError` raised synchronously; test expects a result dict with `code == "MUTATION_DISABLED"` | **REAL_DEFECT** (boundary holds; contract of *how* it refuses drifted) |

These are three `recon/solspire-r0` forked-recon **file copies** whose workflows trigger only
on `push` to `recon/solspire-r0` (`solspire-r{1,2,3}-validation.yml`), so they are **inert
for `main` CI**; they still execute in the local suite. They are recorded here for
continuity, **not** repaired in this pass (per the rule against fixing unrelated debt inside
bounded work).

### 11.4 CI observation (derived, not assumed)

`actions/runs?head_sha=4164573586860b9c7e04e1815bca4957559046a2` → **5 runs**:
`SG-02-FE.2-V` (push) **success**, `security-secret-scan` (push) **success**,
`_diagnose_blank_frontend` (push) **success**, Arkadia Genesis Agent ×2 (issue_comment,
skipped). So the merge *was* gated: both the CP10 mutation boundary and the full-history secret
scan ran on it and passed.

> **Correction of an earlier claim in this section.** A first query used the **short** SHA
> `4164573` and reported **0 runs**. That was wrong, and the error was silent: the GitHub
> Actions API returns `total_count: 0` for an unresolved short SHA instead of failing. Query
> with a **full 40-char SHA** (or `?branch=`), and read `0` as *unproven*, never as *absence*.
> `solspire-r1/r2/r3` are the genuinely inert ones — they trigger only on `push` to
> `recon/solspire-r0`, a branch `main` never receives.
`solspire-r1/r2/r3` last ran on `recon/solspire-r0` (`aed112b`, `611f69e`, 2026-09-29) and are
red; `weaver-mvp2-validation` last ran on a `pull_request` and passed.

### 11.5 Reproduction commands

```bash
# fingerprint
PYTHONPATH=<repo>/archive/legacy_python python -m pytest tests/ -q \
  -p no:cacheprovider --continue-on-collection-errors
# architecture
PYTHONPATH=<repo>/archive/legacy_python python -m pytest tests/architecture -q
# SG-04 as-shipped vs branch tip
for c in 74f5494 1b63994 06ad5f2 origin/main; do
  printf "%s mount=%s\n" "$c" \
    "$(git show $c:web/public_prism/src/components/spiral-grove/CapabilityChamber.tsx \
       | grep -c '<ActivityRuntime')"
done
git worktree add /tmp/sg04wt 06ad5f2   # then run the SG-04 tests there
```

### 11.6 SH-02e measured fingerprint and repair record (rows 1-2)

Re-measured on `main` @ `df7a99a067382401c00de5e7bbaaac0125ba2088` (deepened history, 820
commits):

```
30 failed, 1028 passed, 13 skipped, 2 errors  (108.28s)
PYTHONPATH=<repo>/archive/legacy_python python -m pytest tests/ -q \
  -p no:cacheprovider --continue-on-collection-errors
```

`tests/architecture` **11/11**; `api/main.py` **2519 / 2600** lines; `py_compile` clean.

**Attribution of the delta against §Appendix A's 51-row set** (`comm`, by node name):

- **30 live failures, all 30 present in Appendix A** — no unexplained regression.
- **21 Appendix A rows now pass**, including the two repaired here plus the
  #128/#130/#131/#132 repair series and the §11.2.1 rows.
- **8 live failures are absent from Appendix A**: the 4 `test_solspire_r{1,2,3}_*.py` nodes
  already recorded in §11.3, and the 4 `test_spiral_grove_activity_runtime.py` nodes recorded
  in §11.2/§11.2.1.
- **Proven pre-existing, not regressions.** All 8 were executed against a `4164573` worktree
  and fail there identically (`8 failed, 15 passed in 0.65s`). Appendix A's "cover the
  baseline set exactly" claim is therefore **incomplete** — it under-counts the baseline set
  by these 8 nodes. Recorded here rather than edited into Appendix A, which is a frozen
  `a26af408`-era artefact whose additions §11.2/§11.3 already carry.

**Rows repaired in this batch (both `STALE_ASSERTION`):**

| # | node | repair | verification |
|---|---|---|---|
| 1 | `tests/test_agent_run.py` (was `::test_agent_run_writes_and_commits`) | Re-pinned from the superseded pre-K0.1 `task -> LLM -> write -> commit/push` flow onto the current kernel seams: fail-closed default entry point, `run_authorized` -> `SessionResult`, terminal commit through `weaver.session_kernel`, and no re-exposed `agent.commit_and_push` | FAILS on pristine `main` (`AttributeError`); PASSES after |
| 2 | `tests/test_ais_capability_profile_onboarding.py::test_home_is_offer_led_and_keeps_arkadia_entry_points` | Replaced the removed `'Learn. Build. Prove. Launch.'` tagline with the live headline `'One intelligence. Four ways to work with it.'` (`ArkadiaLandingPage.tsx:64`); replaced the duplicate dead `button-home-ais-diagnostic` assertion with the live mount testid `arkadia-home-landing` (`:35`) | FAILS on pristine `main`; PASSES after |

Both replaced symbols were confirmed **dead**, not merely relocated: `button-home-ais-diagnostic`
and the old tagline appear nowhere in `web/` or `tests/` on current `main`, so the re-pin
removes no live coverage. Node 1 was **renamed**, so its Appendix A name no longer resolves —
the rename *is* the repair, since a node cannot keep asserting a symbol that no longer exists.

**Open delta recorded, not fixed (authority boundary).** The pre-K0.1 node additionally
asserted `engine_cycle` reached the commit as `meta['engine_cycle']`. The epoch is
**structurally dropped at the kernel seam**: `weaver.session_kernel.finalize_session` is the
only commit path, never receives `engine_cycle`, and passes `meta={"pass_id": ...}` only.
Threading it through changes what the kernel records for governance, so it is **not** test
hygiene. The re-pinned row pins the invariant (`meta.get("engine_cycle", 5) == 5`) rather than
the absence, so a legitimate future fix greens it instead of reddening it.

**Status:** IMPLEMENTED (corrected classification + measured live drift; no runtime claim
made). **Authority:** documentation/evidence only — no merge, no authorization, no identity
or authority-model change, no new mutation or authorization path. Human-merge-only.

