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

Files changed: `tests/test_solariun_experience_consolidation_01.py` **only** (+67/−11 lines,
`import re` added, one new node appended — see §3.4).

## 1a. Independent re-verification (this pass)

This pass did not assume the prior session's claims. It re-derived every load-bearing fact
from live source and re-ran the full suite in a **pristine `main` worktree** to attribute
the delta by node name:

```
$ git worktree add /tmp/mainwt main      # ee3fac1, untouched
removed : test_area_c_solspire_substrate_uses_existing_search_and_context_grammar
          test_preimplementation_map_is_present_and_bounded
          test_responsive_composition_and_inspector_exist
added   : (none)
```

Exactly the intended 3 nodes disappear and **nothing else moves**.

Two corrections to the prior session's record came out of this pass:

1. **NC1 as previously recorded did not actually fire.** The recorded control ("remove
   `searchKnowledge` from `SolSpireExperience.tsx`") only renamed the import alias while
   the call site still contained the literal, so the assertion still passed — the control
   was vacuous, not the assertion. A *real* swap of the shared client is caught (§3.3).
2. **`NC7 = 7 passed` understated the file** — it contains 8 nodes (see §3.4).

Not silently dropped: the two obsolete prose strings, and the vacuous control, are both
recorded below.

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
   This same staleness was independently flagged in
   `docs/architecture/AEAS_FRONTEND_SCALPEL_PLAN.md:264`, which classified the node
   "C / B" and required rewriting it to assert the architectural *invariant* rather than
   obsolete prose.

   **Two of the five old strings are deliberately dropped, not re-pointed.**
   `Knowledge OS search only` and `Existing repository components + existing APIs` were
   documentation prose; `grep -rn` finds neither anywhere under `web/public_prism/src` or
   `docs/architecture` except this classification table. Asserting them would be
   re-pinning the same prose drift in a new file. The bounded search/no-universal-index
   *intent* is retained by asserting the live mechanisms (`searchKnowledge`,
   `No universal object index`, `COVERAGE (honest)`). Likewise the literal
   `ACTIVITY ≠ PROVENANCE` is re-expressed as its live form — the `ACTIVITY (project_events)`
   layer token plus `provenance proof` as a distinct layer.

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
branch + §3.4 binding guard  : 45 failed / 972 passed / 12 skipped / 2 errors   (48 nodes)
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
| NC0 | baseline, no mutation | **pass** (8 passed) |
| NC1 | swap the shared client — `../../lib/knowledgeApi` → `../../lib/FOREIGN_SEARCH` | **caught** (2 failed) |
| NC2 | inject `searchKnowledge` into the frame wrapper | **caught** (1 failed) |
| NC3 | change the canonical `700px` breakpoint to `701px` | **caught** (1 failed) |
| NC4 | re-introduce `experience-inspector` testid in the frame | **caught** (1 failed) |
| NC5 | `human_only` → `human-only` in the map | **caught** (1 failed) |
| NC6 | remove the inspector testid from `ProjectDashboard.tsx` | **caught** (1 failed) |
| NC7 | restore all; re-run | **pass** (8 passed, no residue) |

This discharges the batch-1 rule: *re-point the assertion and prove it can still fail.*
NC2 is the load-bearing one — a relocation repair that merely moved the assertion to a new
file could leave the frame free to regrow the substrate; the control proves it cannot.

NC1 is recorded above in its **corrected** form. The previously recorded NC1 renamed only
the import alias (`searchKnowledge` → `KNOWLEDGE_SEARCH_REMOVED`) while the call site on
line 86 still contained the literal, so the Area C assertion — and the new binding node —
both still passed: the control was too weak to falsify anything. The mutation above is a
real substitution of the shared client and is caught by **two** nodes.

## 3.4 Closing the NC1 weakness — `test_log_binding_uses_shared_substrate`

NC1's weakness exposed a genuine fuzziness in the Area C assertion: `"searchKnowledge" in
solspire` is satisfied by the **import alias alone**, so a same-named local function, or an
alias pointed at a foreign module, would pass a module-level substring check. The repair:

```python
def test_log_binding_uses_shared_substrate():
    solspire_lines = SOLSPIRE.read_text().splitlines()
    assert any("lib/knowledgeApi" in line for line in solspire_lines)
    assert any("await searchKnowledge(" in line for line in solspire_lines)

    dashboard = DASHBOARD.read_text()
    assert "projects/${project.id}/events" in dashboard  # ACTIVITY layer
    assert "/solspire/workevents" in dashboard           # CONTINUITY layer
    assert "work_events" in dashboard
```

Rather than a new mechanism, this asserts the two **live call sites** that already carry the
binding — the `await searchKnowledge(` invocation in `SolSpireExperience.tsx` (bound to the
line that also names the shared module) and the two canonical project/work-event reads in
`ProjectDashboard.tsx`. No new assertion vocabulary, no source change: purely test-hygiene,
inside the authorized envelope.

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