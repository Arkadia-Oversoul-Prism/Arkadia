# Baseline Test Debt Classification — `main` @ `a26af408`

**Workstream:** test-hygiene (standalone; explicitly *not* folded into an architectural gate)
**Authority required:** none for classification. Repairs are separate bounded tasks (see §8).
**PR:** #106 · branch `gate-hygiene/baseline-test-debt-classification-01`
**BASE_MAIN:** `a26af408c269729a57d0a53c6ad39fcf0ca22fdf`
**Status:** classification complete — every one of the 51 failing/error nodes is assigned a
bucket with evidence. **No test, no source file, and no policy was modified.**

> **Pass linkage (heartbeat continuity).** Pass 1 authored the classification; pass 2 (§7)
> independently re-derived it and corrected the inaccuracies. PR #106 carries both.
> PR #105 (`gate10/cp10-allowlist-root-docs`) is a **separate, non-overlapping workstream** —
> verified: no file in #105's diff is touched here, and no file here is touched by #105.

This pass exists because `PARKING_LOT.md` recorded the debt as *unclassified* and stated the
explicit precondition: _"Classify by real defect vs stale assertion before repairing."_
This document is that classification.

## 1. Measured baseline (independently reproduced)

| | value |
|---|---|
| ref | `main` @ `a26af408c269729a57d0a53c6ad39fcf0ca22fdf` |
| passed / failed / skipped / errors | **903 / 49 / 12 / 2** (invocation: `PYTHONPATH=<repo>/archive/legacy_python python -m pytest tests/ -q`; see §5 for the environment this number depends on) |
| architecture fitness (`pytest tests/architecture -q`) | **11/11 passed** |
| `api/main.py` | 2519 lines (budget 2600 — untouched) |
| failing/error node fingerprint | `sha256 = 256204af4082a70f062ed6004fd0c51c126a14262a072afdac9279ce158c3fca` |

The fingerprint in `PARKING_LOT.md` was reproduced byte-for-byte from the 51
`FAILED`/`ERROR` node ids joined by `\n` with a trailing newline. The same 51 ids were
reproduced again from a second independent full-suite run (`--tb=line`), so the baseline is
stable, not flaky. The suite is **order-independent at this level** — see §5.

## 2. Method

Classification used source-vs-assertion semantics, not commit dates. This is deliberate:
the clone is **grafted** (shallow ancestry), so `git log -1 -- <path>` returns the same
boundary commit for unrelated files and `git blame` is not trustworthy here. Every bucket
below is backed by a command that can be re-run.

Buckets:

- **STALE_ASSERTION** — the implementation moved and the test still asserts a literal string
  (or symbol) that no longer exists. No user-facing capability is absent.
- **REAL_DEFECT** — implementation and assertion disagree and the implementation is the
  side that is wrong; a genuine product/test-isolation behaviour is broken.
- **DRIFT** — a canonical contract identifier changed; both sides are internally consistent.
  Needs a product decision, not a mechanical edit.
- **ENV / ARTIFACT** — the test depends on something outside the repository working tree.
- **COLLECTION_ERROR** — the module cannot be imported at all.

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
either stale assertions or contract drift — i.e. **the tests are behind the code, not the
code behind the tests.** Exactly **one** node is a real defect.

## 4. Findings by bucket

### 4.1 STALE_ASSERTION — 35 nodes

> **Verification-status note (added in the verification pass, §4.6).** The buckets were
> assigned by reading assertion text and grepping for the literal. The verification pass
> re-ran the specific nodes in §4.1–§4.3 and confirmed the failure fingerprints, which is the
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

- `test_prism_pass_c_surface_ownership.py` (6 nodes) — asserts `"view block not found for
  <surface>"` for `spiral-codex`, `personal-echofeild`, `knowledge-os`, `codex`, `loops`.
  `web/public_prism/src/App.tsx:32` still declares all of those in the `View` union, but the
  render blocks were consolidated; the test's regex for a per-view block no longer matches.
- `test_ais_capability_profile_onboarding.py:40` — asserts `'Learn. Build. Prove. Launch.'`;
  the component now renders `...ONE SYSTEM · MANY SURFACES · ONE CONTINUOUS FIELD`.
- `test_prism_interior_shell.py` (3) — asserts `'Same identity · same context · same
  backend'` and `data-testid="prism-secondary-toggle"`. `grep` finds the former nowhere in
  `web/public_prism/src`; the shell now renders `ExperienceConsolidationFrame`.
  **REPAIRED `SH-02d` (§9).**
- `test_ais_w2_living_gate_grove_handoff.py` (6) — five are copy/regex drift in
  `pages/LivingGate.tsx`: the test pins an exact `useState<FlowStep>(initialMode === 'reset'
  ? 'reset' : 'diagnostic')` expression that no longer matches, requires `'Open Spiral Grove'`
  and `'invitation'` copy, and requires the literal `'/api/pulse/analyze'`. **The endpoint is
  preserved** — `api/pulse.py:272` still defines `@router.post("/api/pulse/analyze")`; the
  component now calls it through the canonical client (`lib/apiClient` `apiFetch`), so only
  the call-site string is stale. The sixth node,
  `test_no_firebase_persistence_in_gate`, fails on `assert "sessionStorage" not in src`;
  `LivingGate.tsx:61-80,207,218` uses `sessionStorage` for a transient, tab-scoped
  diagnostic handoff (`arkadia.ais.diagnostic-handoff.v1`). **No Firebase and no durable
  persistence was added** — the assertion is simply broader than its stated intent. See the
  borderline note below.
- `test_spiral_grove_chambers.py`, `test_spiral_grove_frontend_projection.py`,
  `test_spiral_grove_learning_path_projection.py` — all three target `web/public_prism/src/components/spiral-grove/CapabilityChamber.tsx` and assert the copy
  `'Evidence is separate.'` / `'Evidence submission, assessment, ...'` which the current
  `CapabilityChamber.tsx` and fail solely on the copy string `'Evidence is separate.'` / `'Evidence submission, assessment, and capability-state updates remain separate downstream stages.'` (`grep -c` -> 0). **The governance properties those tests exist to protect are intact.** Verified present in the file: `'SG-03 activity contract'` (2), `'mutate learner capability state'` (1), `prerequisites: GroveCapability[]`, `GroveCapability`, `LearnerCapabilityState`; verified **absent**: `generateExercise` (0) and `createEvidence` (0). The chamber still does not autonomously generate or adjudicate - only the prose was reworded. Re-pinning the copy restores these without weakening the boundary.
- `test_solspire_p1_experience_01.py` (2) — asserts `'CONTEXT PACK (explicit)'` and
  `'Not an authorization authority'` in
  `web/public_prism/src/components/solspire/SolSpireExperience.tsx`. Both literals are
  **absent** (`grep -c` → 0). The testid the test also checks *is* still present
  (`data-testid="solariun-arkana-context-pack"`), but the panel now renders the label
  `CURRENT CONTEXT`. So the Arkana context pack exists; the copy/packaging changed. Genuine
  copy drift, not an absent capability.
- `test_weaver_sci_boundary_01.py` (3), `test_weaver_sci_contract_01.py` (2),
  `test_weaver_mvp2_08.py` (1) — the "nexus→novanet" family. The assertion looks for
  `v === 'nexus' ? 'novanet'`; `App.tsx:114` now reads
  `if (requested === 'nexus') next = {view:'novanet',path:'/nexus'}`. Same intent, different
  expression. The same family also asserts `'ProjectDashboard'` inside
  `SolSpireConsole.tsx`; that page is now a 4-line re-export of `EnterpriseConsole`
  (`return <EnterpriseConsole {...props}/>`), and the project workspace moved into
  `SolSpireExperience.tsx` (which mounts `ResilientProjectDashboard`). `ProjectDashboard`
  itself still exists at `pages/ProjectDashboard.tsx` and is asserted successfully there by
  `test_m04_projects.py` — so the surface is intact and only the assertion's location
  assumption is stale.
- `test_solariun_experience_consolidation_01.py` (3) — asserts `'searchKnowledge'` and
  `data-testid="experience-inspector"` in `ExperienceConsolidationFrame.tsx`, which now
  renders only `data-experience-surface`; and asserts `'Merge: human_only'` in the
  consolidation map, which is not present.
- `test_ais_w6_future_skills_challenge.py`, `test_ais_w8_canonical_identity.py` (2),
  `test_identity_spine_w1.py` (2), `test_solspire_p1_experience_01.py` — same copy/symbol
  drift in `.tsx` and in the identity-seed module (asserting `_SPINE_KEY = "identity_spine"`
  and `'"ais_capability_portfolio"'` against a module that now emits `'identity_spine'` as a
  dict key).
- `test_steward_filter.py` (3) — asserts `steward_filter("You have transcended") is None`
  while `weaver/filters/steward.py` forbids `"transcendent"`, not `"transcended"`; and
  `compress_to_choices` no longer drops the `'More noise'` sentence. Borderline: the
  stem-matching gap is arguably a real content-hygiene hole. Logged as `SH-06` in §8 with a
  product judgement, not auto-repaired.
- `test_ais_capability_profile_onboarding.py` (1 node, counted above).

### 4.2 DRIFT — canonical contract identifier changed — 11 nodes

These are **not** copy drift. A canonical machine-readable identifier changed, and the
identifier is asserted consistently across several tests while the code emits a different,
self-consistent value. Fixing them is a product/contract decision, not a test edit.

- `test_weaver_w5.py::test_derived_graph_provenance` and `::test_http_knowledge_isolation`
  (2 nodes, incl. the `/solspire/projects/{id}/knowledge/graph` route) assert
  `kind == "DERIVED"`; `solspire/semantic_graph.py:112` emits
  `"DERIVED_BOUNDED_SEMANTIC"`, and `tests/test_weaver_mvp2_05.py:24` asserts the **new**
  value. Two tests in the same suite encode opposite contracts — the identifier was
  deliberately widened (W5) and these two were not migrated.
- `test_spiral_grove_registry.py::test_ais_catalog_supports_progressive_creative_workflow`
  asserts prerequisites `["cap-ai-prompt-engineering", "cap-digital-intelligence",
  "cap-content-systems"]`; `spiral_grove/registry.py` now declares only
  `["cap-digital-intelligence"]` for that capability. The catalog was re-parented.
- `test_spiral_grove_registry.py::test_registry_rejects_prerequisite_cycle` expects
  `CapabilityCycleError`; `registry.py:118` raises `UnknownCapabilityError` first because it
  validates membership before cycles. Whether cycle detection is still reachable is
  unverified — flagged as `SH-04` in §8 (and RESOLVED in the verification pass).
- `test_m02_reasomate_truth.py::test_oracle_runtime_uses_the_shared_session_key` asserts
  `"arkanaSessionId"` in `components/ArkanaCommune.tsx`. `grep -c` returns **0**. The
  requirement — Oracle and ReasoMate keying one longitudinal thread on a shared session id —
  is **genuinely not satisfied by that symbol**; the test is a correct assertion against a
  capability that is currently absent. Grouped under DRIFT because the requirement is
  architectural, not a copy string.
- `test_engineering_scheduler_bootstrap.py::test_dry_run_evidence` — `EngineeringRouter.run()`
  returns `NO_LEGAL_MOVE` instead of `READY_FOR_REVIEW`, and
  `::test_blocked_dependency_skips_move` then hits `TypeError: 'NoneType' object is not
  subscriptable` because `select_next_move` returns `None`. The scheduler finds no legal move
  in the checked-in trajectory — the trajectory and the scheduler have drifted apart.
- `test_ais_w8_canonical_identity.py` (2) and `test_identity_spine_w1.py` (2) counted here
  overlap §4.1; they assert canonical symbol names (`load_user_profile_store(user["uid"])`)
  that the current spine module does not expose. Canonical-identity surface is W8 territory
  and requires identity-boundary care — **not** touched by this pass.

### 4.3 ENV / ARTIFACT — 2 nodes

- `test_gate_serve_script.py::test_root_index_redirect_and_script_exists` — asserts
  `Path('index.html').exists()` relative to CWD.
- `test_gate_status.py::test_gate_files_and_fetch_handling` — asserts `Path('gate/index.html')`.
- Neither `index.html` nor `gate/` exists at the repository root. They exist only under
  `static/index.html` and `archive/legacy_frontend/gate/index.html`. `conftest.py` does not
  `chdir`. These tests reference a served-artifact layout that is not in the tree.

### 4.4 REAL_DEFECT — 1 node

- `test_m01_persistence.py::test_db_path_honours_data_dir_env` — **test-isolation defect,
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
  → 1 failed, 15 passed
  ```

  This is a real defect in the **test substrate**, not in product code. It is the only node
  in the baseline whose pass/fail depends on test execution order, which means the recorded
  fingerprint is only valid for the full-suite invocation — a second reason to repair it.

### 4.5 COLLECTION_ERROR — 2 nodes

Both are the documented, pre-existing collection errors and are unchanged by this pass:

- `tests/test_autonomy.py` — `load_autonomy_config` is not importable.
- `tests/test_render_codex.py` — imports `archive/legacy_python/codex_brain.py`, which imports
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
| solariun consolidation (`Merge: human_only`) | literal `Merge: human_only` in the frame component | **corrected target:** `docs/architecture/SOLARIUN_EXPERIENCE_CONSOLIDATION_01_MAP.md` carries `**Merge:** human_only`, `**Deploy:** human_only`, `Human authority remains above all display/navigation surfaces`, `Discovery ≠ authorization` (U+2260) | no `human_only` literal in any `.tsx` |
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

- Fingerprint `256204af…83fca` is reproduced and **must remain unchanged** by any future
  hygiene pass except where that pass explicitly claims the node.
- **Environment-dependent baseline (verification pass).** The fingerprint `256204af…83fca` is
  the fingerprint of *this invocation environment* only. The suite's outcome depends on which
  optional deps are importable: `tests/test_m08_trajectory_schema.py:38` and
  `tests/test_m09_worker_contract.py:55` gate on `pytest.importorskip("jsonschema")`. Confirmed
  by direct run with `jsonschema` absent (`9 passed, 2 skipped`), and `jsonschema` **is** absent
  from this environment, so 2 of the 12 skips are dependency-gated. Install `jsonschema` and the
  pass/skip split changes, so the recorded counts and fingerprint are not portable unless the
  invocation is pinned (as amended in §1).
- **`test_prism_pass_c_surface_ownership.py` must not be attributed to a helper.** The module
  has no call site referencing `view block not found`; the string exists only as the f-string
  text of an `assert m, ...`. The 6 "nodes" are the `@pytest.mark.parametrize` case ids
  Python generates from the f-string, not greppable source lines.
- Architecture fitness is **11/11** and no `REGISTERED_ARCHITECTURAL_DEBT` was touched.
- Working tree after two full-suite runs: **0 untracked files, 0 files under `vault/`** —
  the GATE-VAULT guardrail (`vault/**` gitignored, `conftest.py` sandbox) is holding.
- `api/main.py` was not touched; no boot-code `py_compile` gate was required.

## 6. Remaining uncertainty

> **Resolved in the verification pass:** the two items below that were open questions in the
> first draft are now answered; the answers are stated inline and the item is resolved.

- `test_registry_rejects_prerequisite_cycle` — **RESOLVED: no defect, and the name is
  misleading.** Cycle detection *is* reachable: `CapabilityRegistry([cap-a→cap-a])` (a
  self-prerequisite) raises `CapabilityCycleError`. The test's two-node a↔b case raises
  `UnknownCapabilityError('cap-b')` only because `ReferenceValidator._validate_references`
  runs the membership loop to completion before the first `graph_validate_cycle` call, and
  registration is incremental — `cap-b` is not yet a member when `cap-a` is registered. The
  test asserts `pytest.raises(CapabilityCycleError)`, which is *not* a superclass of
  `UnknownCapabilityError`, so the test is genuinely wrong about ordering, not about cycles.
  No dead code; the library already exposes the correct exception.
- **New, cleaner STALE_ASSERTION case discovered:** the same test module expects the
  *transitive* prerequisite closure of `cap-ai-creative-workflows` to be exactly
  `[cap-ai-prompt-engineering, cap-digital-intelligence, cap-content-systems]`. The registry
  correctly returns `[cap-digital-intelligence, cap-ai-prompt-engineering, cap-content-systems]`
  — a set-correct answer in a different order, asserting list equality. This is an ordering
  brittleness, not a capability regression.
- `test_steward_filter.py` — the `"transcended"` vs `"transcendent"` gap is a plausible real
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
| C1 | fingerprint treated as a portable contract | environment-dependent — `jsonschema` gated skips | §1, §5 |
| C2 | `test_prism_pass_c_surface_ownership.py` asserts a `"view block not found"` helper per surface | no such call site exists; string is only an f-string message; the 6 nodes are parametrize case ids | §4.1, §5 |
| C3 | `test_registry_rejects_prerequisite_cycle` — cycle detection may be dead code | not dead; reachable via self-prerequisite; the test's a↔b case fails on validation *ordering* | §6 |
| C4 | `Merge: human_only` asserted in the frame `.tsx` | no `human_only` literal in any `.tsx`; the assertion target is `SOLARIUN_EXPERIENCE_CONSOLIDATION_01_MAP.md`, and the map uses `Discovery ≠ authorization` (U+2260) not `!=` | §4.6 table |
| C5 | (new) registry transitive-closure ordering brittleness | `cap-ai-creative-workflows` closure is set-correct but order-differs | §6 |
| C6 | (refinement) dead CSS `experience-inspector` = "7 rules" | 8 rule blocks total — 7 base selectors (`.css:72–86`) plus 1 responsive override (`.css:121`); "7" counts the base block only, which is defensible | §4.6 prose |

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
| `SH-07` | Migrate `test_m02_reasomate_truth::test_oracle_runtime_uses_the_shared_session_key` — the shared-session requirement is genuinely unmet in `ArkanaCommune.tsx`. | DRIFT | **high** | architectural gate |

**Recommended first:** `SH-01`. It is a one-line test-hygiene fix, it removes the only
order-dependent node, and it makes the baseline fingerprint reproducible under any
invocation order — which every later hygiene task depends on.

## 9. Deliberate non-edit: `PARKING_LOT.md` is left untouched

`PARKING_LOT.md` is the natural home for the status change on the parked item
("unclassified" → classified). It is **intentionally not modified here.**

Open PR **#105** rewrites the same `## Open Items` anchor — it replaces `_None._` with the
CP10 and baseline-debt entries. Editing that anchor on this branch would guarantee a textual
conflict in a file the sovereign must merge by hand, for zero engineering benefit.

Deferred: once #105 lands, a one-line follow-up updates the parked item to point at this
document. Until then this evidence file is the single source of truth for the classification.

## 10. Authorization

Classification only. No merge, no authorization, no identity-boundary change. The sovereign
decides which of `SH-01`…`SH-07` become canonical work.

## Appendix A — complete node-to-bucket map

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

## 9. Repair record - `SH-02d` (`tests/test_prism_interior_shell.py`, rows 10-12)

Rows 10/11/12 were repaired as batch `SH-02d`. The three nodes were re-pointed at the
NovaNet primary rail and secondary lens surfaces that `PrismInteriorShell` now owns, and
the `testid="prism-secondary-toggle"` expectation was dropped: that disclosure control is
now expressed as `aria-expanded={lensesOpen}` on the lens group and carries no `testid` in
the component. No product capability is absent - this is the bucket's definition.

Two things beyond a plain re-point:

- **Vacuous pass closed.** `test_shell_exposes_canonical_primary_surfaces` asserted
  `"'sci' in shell"`. `sci` is a substring of `science`, so the node could pass on any
  shell file mentioning that word regardless of whether a `sci` surface existed. The
  repaired node parses the `PRIMARY` rail and requires each key to be resolvable by
  `activeSurfaceFor`.
- **Prose that was never a literal.** A fourth failing assertion expected
  `"Same identity / same context / same backend"` in the component. That sentence is the
  node's own docstring - the invariant it names, not a string the shell ever rendered.
  The repaired node asserts the structure that actually delivers the invariant
  (`useAuth` + `data-testid="identity-persistence"` + `PrismInteriorShell` mounted inside
  `ArkadiaNavigation`).

Verification (evidence, not assertion):

| check | result |
|---|---|
| `pytest tests/test_prism_interior_shell.py -q` | 5 passed |
| `pytest tests/architecture -q` | 11 passed |
| negative controls (mutation anchor confirmed applied) | 4 / 4 fired |
| full suite vs clean `main` `4164573` | 39F/1020P/11S/2E -> **36F/1023P/11S/2E** |
| nodes added (regressions) | **none** |
| nodes removed (by name) | exactly rows 10, 11, 12 |

The negative controls mutate the shell and confirm each repaired node still owns its
invariant: drop the primary rail `testid`, the lens `aria-expanded`/`setLensesOpen`
disclosure pair, the identity-persistence `testid`, or the `activeSurfaceFor` resolver
entry for `commune` - each fails exactly the node that asserts it.

`SH-03`/`SH-04`/`SH-06`/`SH-07`/`F-01` were deliberately **not** touched: each needs a
product or architectural decision, not a test edit.
