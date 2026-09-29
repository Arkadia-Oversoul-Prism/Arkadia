# EVIDENCE — Gate hygiene: stale-assertion repair (Solariun experience consolidation)

- **Gate / workstream:** GATE-10 context — test-suite hygiene
- **Bounded task:** `SH-02`, batch 2 — the 3-node `test_solariun_experience_consolidation_01.py` family
  named as the next bounded task by the batch-1 ledger
- **BASE_MAIN:** `ee3fac1baffe512f1d9462984f1d507d38cdfa7a`
- **Branch:** `gate-hygiene/baseline-stale-assertion-repair-solariun-consolidation-01`
- **Authority:** test-hygiene only. No source, policy, governance, or architecture mutation.
- **Status:** IMPLEMENTED (targeted tests pass, protected regressions pass, negative controls fire;
  full-suite delta verified by name; sovereign merge pending)

---

## 1. Scope

Repoints three string-level assertions whose targets were **relocated** by earlier
architecture passes. The governance intent of each assertion is preserved; only the
file-location assumption changed. Per `BASELINE_TEST_DEBT_CLASSIFICATION.md` these were
already classified `STALE_ASSERTION`; this pass independently re-verified that
classification against live source before editing.

| node | prior target (now stale) | new target |
|---|---|---|
| `test_area_c_solspire_substrate_uses_existing_search_and_context_grammar` | `ExperienceConsolidationFrame.tsx` prose | the components that own the substrate |
| `test_responsive_composition_and_inspector_exist` | frame-local CSS + frame testids | canonical SolSpire chrome + `ProjectDashboard` |
| `test_preimplementation_map_is_present_and_bounded` | map emphasis formatting | the map decision token |

Files changed: `tests/test_solariun_experience_consolidation_01.py` **only** (+6/−3 lines,
`import re` added).

## 2. Root causes (verified against live source, not assumed)

1. **Substrate grammar moved out of the wrapper.** `searchKnowledge`,
   `No universal object index` and `COVERAGE (honest)` no longer live in
   `ExperienceConsolidationFrame.tsx`; they live in
   `components/solspire/SolSpireExperience.tsx` (imports `search` as `searchKnowledge`
   from `lib/knowledgeApi`, calls it with the four Knowledge OS groups, and renders the
   honest-coverage copy). `ACTIVITY (project_events)` and `provenance proof` live in
   `pages/ProjectDashboard.tsx`.
   → re-point Area C at the real owners and keep a **negative guard** that the frame
   wrapper does not regrow them (verified necessary: `5402553` "remove duplicate Solariun
   outer shell" deleted 147 lines from the frame — exactly this duplication).

2. **Frame is now a thin wrapper.** `experience-inspector` / `experience-context-bar`
   testids moved to the canonical surfaces
   (`ProjectDashboard` owns `data-testid="solariun-epistemic-inspector"`,
   `SolSpireExperience` owns `solspire-context-bar`). Responsive chrome moved to
   `components/solspire/solspire-canonical.css` (`@media (max-width: 700px)`,
   `.solspire-context-bar`, `.solspire-mobile-bottom`).
   → assert the chrome where it is owned **and** assert the frame did not re-implement
   shell placeholders (both testids absent from the frame — confirmed live).

3. **Markdown emphasis is presentation, not the decision.** The map's `Merge:` / `Deploy:`
   lines carry the decision `human_only`; the assertion previously pinned formatting.
   → assert the token on the located line.

## 3. Verification

### 3.1 Characteristics and delta (measured)

```
main ee3fac1 (test reverted) : 48 failed / 968 passed / 12 skipped / 2 errors   (50 nodes)
branch       (repair applied): 45 failed / 971 passed / 12 skipped / 2 errors   (47 nodes)
```

Node-set diff (by name, not by count):

```
removed : test_area_c_solspire_substrate_uses_existing_search_and_context_grammar
          test_preimplementation_map_is_present_and_bounded
          test_responsive_composition_and_inspector_exist
added   : (none)
```

**3 nodes removed, 0 added, 0 altered.** The unaffected node set is byte-identical
between the two runs, so no other test's fingerprint moved.

### 3.2 Protected regressions (unchanged)

```
tests/architecture                                  : 11 passed
tests/test_m02a_ci_gate_integrity.py tests/architecture : 60 passed
python -m py_compile api/main.py                    : pass   (api/main.py = 2519 / 2600)
```

### 3.3 Negative controls — every repaired assertion can still fail

Each control mutates live source in a targeted way, runs the repaired file, and requires
the mutation to be caught; source is restored afterwards.

| NC | mutation | result |
|---|---|---|
| NC1 | remove `searchKnowledge` from `SolSpireExperience.tsx` | **caught** (Area C fails) |
| NC2 | inject `searchKnowledge` into the frame wrapper | **caught** (Area C negative guard fires) |
| NC3 | change the canonical `700px` breakpoint to `701px` | **caught** (responsive node fails) |
| NC4 | re-introduce `experience-inspector` testid in the frame | **caught** (responsive node fails) |
| NC5 | `human_only` → `human-only` in the map | **caught** (map node fails) |
| NC6 | remove the inspector testid from `ProjectDashboard.tsx` | **caught** (responsive node fails) |
| NC7 | restore all; re-run | **7 passed** (no residue) |

This discharges the batch-1 rule: *re-point the assertion and prove it can still fail.*
NC2 is the load-bearing one — a relocation repair that merely moved the assertion to a new
file could leave the frame free to regrow the substrate; the control proves it cannot.

## 4. Remaining uncertainty / not claimed

- **Not fixed here:** `tests/test_prism_pass_c_surface_ownership.py` (6 nodes) still needs a
  *helper* rewrite, not string edits — it fails at `_block(view)` because `App.tsx` now
  resolves views through a `requested`/`next` mapping (`App.tsx:111-120`) with explicit
  redirects, so views like `personal-echofeild` keep a real JSX block while
  `knowledge-os` / `codex` are routed to `solariun` with a section. Recorded as its own
  bounded task; deliberately not bundled here.
- Remaining `SH-02` budget: **9 / 35 repaired** after this batch (6 from batch 1 + 3 here).
- No runtime/browser evidence: `vite build` remains environment-blocked (no npm registry
  access). Changes are inspection- and test-verified only. Not claimed as runtime-verified.
- Baseline debt is recorded, not fixed: the residual failures are pre-existing and their
  fingerprints are unchanged by this pass.

## 5. Authority

No merge, no authorization/identity/authority-model change, no governance or architecture
change, no new mutation path, no new authorization path. Test-only edit.
**HUMAN-MERGE-ONLY.**