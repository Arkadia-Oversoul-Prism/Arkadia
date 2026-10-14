# Lane 4 — run → work-event → evidence → **artifact** trace · evidence

**Branch:** `feat/prism-l4-run-artifact-trace-01`
**Base:** `7580bd8f0ca2925518d78775f9a323ff0df8bc66` (`main`, merge of PR #533)
**Instruction:** `docs/control-plane/parallel-ui/AGENT-04-ARKANA-WEAVER-LAB.md`
**Contract:** `docs/control-plane/parallel-ui/SHARED-CONTRACTS.md`
**Authority:** implement, test, commit, report. **No merge, deployment, or acceptance.**

---

## 1. Verified contract (measured against the handler, not inferred)

The Lab session view already returns artifacts, but the console projection dropped them.
The trace joins exactly the reference fields the substrate records:

| Join | Field | Written by |
|---|---|---|
| run → artifacts | `artifact.run_id === run.run_id` | `runtime._finish` → `store.save_artifact` |
| run → declared artifacts | `run.artifact_refs` contains the artifact id | `RunRecord.artifact_refs` (`lab/engineering_lab/models.py:187`) |

Verified by reading the substrate, not by assuming a shape:

- `lab/engineering_lab/models.py:187` — `artifact_refs: tuple[str, ...] = ()`
- `lab/engineering_lab/runtime.py:432,450,464` — the run carries
  `artifact_refs=[a["artifact_id"] for a in artifacts]`
- `lab/engineering_lab/artifacts.py` — `ArtifactView` carries `artifact_id`, `session_id`,
  `run_id`, `kind`, `title`, `content`, `mime_type`, `evidence_refs`

## 2. What changed (bounded)

| File | Change |
|---|---|
| `web/arkadia_console/src/components/lab/labRunTrace.ts` | `LabArtifactRecord` type; `artifacts` source + per-run `artifacts`, `dangling_artifact_refs`, `unreferenced_artifact_ids`; ledger `unlinked_artifacts`, `unattributed_artifacts`, `duplicate_artifact_ids`; the join itself |
| `web/arkadia_console/src/components/lab/LabRunTrace.tsx` | render the joined artifacts under `data-testid` `lab-trace-artifacts-${run_id}`, marked "captured, not applied" |
| `web/arkadia_console/src/components/lab/LabSessionList.tsx` | type the view's `artifacts` as `LabArtifactRecord[]` so records flow typed into the projection |
| `tests/test_prism_w4_run_evidence_trace.py` | +5 artifact-trace tests incl. a negative control |
| `tests/test_lab_run_trace_contract.py` | +3 source-contract guards on the join |

**Not changed:** no shared file (`App.tsx`, `router.ts`, `surfaces.ts`, `endpoints.ts`,
`types.ts`, `SurfaceLenses.tsx`), no backend, no authority/route surface. `api/main.py`
untouched.

## 3. Evidence chain preserved (contract §3.7)

An artifact is a **captured proposal**. The projection does not fold artifacts into the
evidence list and does not read them in the verification derivation — the presence of an
artifact is never presented as a record, a verdict, or an applied change. This is asserted
by `test_artifact_is_not_presented_as_evidence_or_verification`, which greps the
`verificationFor` body for any artifact reference.

## 4. Proof

Command (targeted, the required proof):

```
python -m pytest tests/test_prism_w4_run_evidence_trace.py tests/test_lab_run_trace_contract.py -q
-> 51 passed in 4.39s
```

Node count attribution: `--collect-only` -> **51** nodes (these two files only).

Frontend build/typecheck:

```
cd web/arkadia_console && corepack pnpm build
-> tsc --noEmit && vite build, 92 modules transformed, built in 1.55s
```

Architecture fitness: `python -m pytest tests/architecture -q` -> **11 passed**.

### Negative control (live, on the real file)

Neutralised the join in `labRunTrace.ts` (artifacts bucketed to no run) and re-ran the two
files:

```
FAILED tests/test_prism_w4_run_evidence_trace.py::test_projection_joins_a_real_artifact
FAILED ...::test_artifact_is_a_captured_proposal_not_evidence_or_verification
FAILED ...::test_missing_artifact_link_is_reported_not_dropped
FAILED ...::test_partial_link_artifact_run_id_and_artifact_refs_disagree
FAILED ...::test_negative_control_artifact_link_detector_sees_a_clean_view_as_clean
5 failed, 46 passed in 4.61s
```

Restored byte-identically; re-ran -> **51 passed**. The detector bites on the real file, so
it cannot be disarmed by rewriting the source.

## 5. Baseline comparison

Baseline measured on `main` `7580bd8` (full suite, once):

```
12 failed, 3099 passed, 22 skipped, 1 error
```

Pre-existing failures recorded, **not** attributed to this slice and **not** repaired here:
`tests/test_autonomy.py` (collection ERROR), four
`tests/test_agents_md_encoding_adjudication.py` nodes (clone-depth/oracle-revision class),
`tests/test_ais_w2_living_gate_grove_handoff.py`,
`tests/test_solspire_r3_execution_runtime.py::test_runtime_is_explicitly_non_governed_and_blocks_mutation_tools`.

This slice adds **+8** test nodes (5 new artifact tests + 3 new contract guards) and changes
no source outside its own feature-local files, so no baseline node can change fingerprint.

## 6. Remaining uncertainty

- The two touched test files' node count is the attribution basis; a second full-suite run
  was deliberately not performed (time budget, and the change is source-additive within
  Lane-4-owned files only).
- Runtime/production observation of the rendered artifact row is **NOT CLAIMED** — the
  console is not deployed by this pass and no browser observation was made.
- `web/arkadia_console/dist/` is gitignored and was not staged.
