# Workstream 4 — run → work-event → evidence trace · evidence

**Branch:** `feat/prism-next2-04-run-evidence-trace`
**PR:** [#432](https://github.com/Arkadia-Oversoul-Prism/Arkadia/pull/432) (draft)
**Base:** `f390526ab14e122fef358ef9b9e1cd438509463c` (`main`)
**Instruction:** `docs/control-plane/parallel-ui/AGENT-04-ARKANA-WEAVER-LAB.md`
**Contract:** `docs/control-plane/parallel-ui/SHARED-CONTRACTS.md`
**Authority:** implement, test, commit, report. **No merge, deployment, or acceptance.**

---

## 1. Verified contract (measured against the handler, not inferred)

The trace reads exactly one endpoint, already declared in the shared registry:

| Method | Path | Auth | Success |
|---|---|---|---|
| `GET` | `/api/lab/engineering/sessions/{session_id}` | `401` without identity (`require_lab_auth`) | `EngineeringLabRuntime.session_view(...)` |

`session_view` returns
`{session, agent, runs, events, evidence, artifacts, loop, reached_review_boundary, human_decision_required}`
(`lab/engineering_lab/runtime.py`).

### The reference fields the trace joins on (measured, not assumed)

| Join | Field | Written by |
|---|---|---|
| run → work events | `event.run_id == run.run_id` | `runtime._emit(..., run_id=…)` → `store.append_event` |
| run → evidence | `evidence.run_ref == run.run_id` | `EvidenceRecord(run_ref=run_id)` → `store.save_evidence` |
| run → declared evidence | `run.evidence_refs` contains the evidence id | `runtime._finish(evidence_refs=…)` → `store.update_run` |

Measured by driving the **real** runtime over an isolated SQLite DB and event log
(`tests/test_prism_w4_run_evidence_trace.py`):

* a session opens with `SESSION_CREATED` carrying **no** `run_id` (recorded work,
  not a run's work);
* `SESSION_TRANSITION` events are likewise session-scoped (no `run_id`);
* a run's own events all carry `run_id == run.run_id`;
* the run's single evidence record carries `run_ref == run.run_id` and its
  `evidence_id` appears in `run.evidence_refs`.

No field is joined that the substrate does not write. A fabricated join field
would report a healthy session as empty rather than raising, so this is pinned
by both a live measurement and a source guard
(`test_projection_does_not_invent_a_reference_field`).

---

## 2. The governance boundary the trace preserves

The substrate's own `contracts.NON_COLLAPSES` says `IMPLEMENTED != VERIFIED`. The
runtime honours it: a **successful bounded run** is finished as
`state="VERIFYING"` while its evidence `state` stays **`IMPLEMENTED`**.
"Verification was entered" and "verification concluded successfully" are
therefore genuinely different readings, and the projection separates them:

| Reading | Derived only from | Measured after a successful bounded run |
|---|---|---|
| `verification.stage_entered` | `run.state ∈ {VERIFYING, READY_FOR_REVIEW, REVISION_REQUIRED}` | `true` |
| `verification.asserted` | an evidence record with `state == "VERIFIED"` (a `RESULT_STATES` member) | **`false`** |
| `review.at_boundary` | `run.state`/`session.state == READY_FOR_REVIEW`, else the backend's `reached_review_boundary` | `true` |
| `acceptance.state` | `session.state == "COMPLETED"` — the sole member of `contracts.HUMAN_TERMINAL_STATES` | **`NOT_RECORDED`** |

The negative control that matters: a view where the session sits at
`READY_FOR_REVIEW` **and** its evidence reads `VERIFIED` still reports
`acceptance.state == "NOT_RECORDED"` with an empty basis. Evidence marked VERIFIED
moves `verification.asserted` and `evidence_with_verification`; it never moves
acceptance. Conversely `evidence_without_verification` names the run whose
evidence no recorded value verifies.

`human_decision_required` is carried as its own field: it means the decision is
**outstanding**, so it can never be read as the decision having been made.

---

## 3. Missing / partial / duplicate links

Each condition is reported, never dropped and never guessed:

| Condition | Reading |
|---|---|
| `evidence_refs` entry with no matching record | `trace.dangling_evidence_refs` + an `unresolved` line |
| evidence linked by `run_ref` but absent from `evidence_refs` | `trace.unreferenced_evidence_ids` (partial link) |
| event whose `run_id` names no run in the view | `ledger.unlinked_events` |
| evidence whose `run_ref` names no run in the view | `ledger.unlinked_evidence` |
| evidence with no `run_ref` at all | `ledger.unattributed_evidence` |
| the same `evidence_id` twice | `ledger.duplicate_evidence_ids`; the record is counted once |
| every reference resolves | `unresolved == ["Every recorded reference in this view resolves."]` |
| no references at all | `unresolved == []`, rendered as "none are unresolved" — distinct from both |

A clean view and a defective view are distinguished in **both** directions: the
negative control asserts a fully-resolving view is reported as clean, so the
detector is not trivially true.

`session_view` filters evidence to the session's runs before returning, so
orphan evidence cannot normally appear. It is classified anyway, so a future
change to that filter surfaces as an unresolved link rather than a silent
omission.

**Measured, not restated.** `test_the_handler_filters_orphan_evidence_before_the_projection_sees_it`
writes an `EvidenceRecord` whose `run_ref` names no run straight to the store and
asserts three things against the **real** handler: the record is in
`list_evidence(OWNER)`; `session_view` does not return it; and the projection,
given that real view, reports nothing unresolved. So the projection's
`unlinked_evidence` / `unattributed_evidence` classifications are a **forward
guard** reachable only from a view the handler did not produce — stated as a
measurement rather than implied. Removing the filter line from
`runtime.py:610` reddens this test (verified as a live negative control, then the
file restored byte-identically).

---

## 4. Owner isolation

Owner scoping is enforced by the runtime, not by the projection: the projection
only ever receives what the handler returned. Measured — another subject calling
`session_view` for this session raises `KeyError` (the handler maps that to
`404`). The trace therefore cannot display another subject's runs, events, or
evidence: it has no path to them.

---

## 5. Slice (feature-local, read-only)

| Path | Role |
|---|---|
| `web/arkadia_console/src/components/lab/labRunTrace.ts` | pure projection (no imports, no network, no React) |
| `web/arkadia_console/src/components/lab/LabRunTrace.tsx` | read-only renderer |
| `web/arkadia_console/src/components/lab/LabSessionList.tsx` | mounts the trace inside the session detail; `LabSessionView`'s `runs`/`events`/`evidence` are now typed to the projection's interfaces |
| `tests/test_prism_w4_run_evidence_trace.py` | backend + projection oracle (18 tests) |
| `tests/test_lab_run_trace_contract.py` | read-only-ceiling + render guard (19 tests) |

* **Read-only by construction.** The trace issues **no request of its own** — it
  is a projection of the session view its parent already holds, so the ceiling is
  structural rather than a promise. Pinned by
  `test_trace_fetches_nothing_of_its_own` (detector matches `fetch|apiRequest|useHydration`).
* **No mutating verb.** `mutating_calls(...) == []` and none of
  `/authorize`, `/execute`, `/transition`, `/run-agent` appears in either file.
* **The projection is executed, not read.** `labRunTrace.ts` is dependency-free,
  so the oracle test runs it under Node (`node --input-type=module -e`, absolute
  `file://` URL — no driver file is written into the source tree) against the
  **real** session view. Every governance reading above is an observed output,
  not a source-level string match. If Node is unavailable the projection tests
  **skip with a stated reason** rather than passing silently.
* **No shared file edited.** `lib/endpoints.ts`, `App.tsx`, `lib/router.ts`,
  `lib/surfaces.ts`, and `lib/types.ts` are untouched; no registry entry added.
  The trace reuses the existing declared `endpoints.labSessions` read, asserted by
  `test_trace_does_not_edit_the_shared_registry`.

### Shared-file boundary

`LabSessionList.tsx` is Workstream 4's own feature-local component (slices 02–05).
No file owned by Workstream 1 or by Workstreams 2/3 was modified.

---

## 6. Verification

```
python -m pytest tests/test_prism_w4_run_evidence_trace.py tests/test_lab_run_trace_contract.py \
  tests/test_prism_w4_lab_read_model.py tests/test_console_endpoint_registry_contract.py \
  tests/test_weaver_run_evidence_contract.py tests/test_lab_artifact_canvas_contract.py \
  tests/test_lab_agent_registry_contract.py tests/test_prism_w4_arkana_thread_history.py \
  tests/test_arkana_thread_history_contract.py -q -rEf
  -> 131 passed
```

```
corepack pnpm install --frozen-lockfile && corepack pnpm build   (web/arkadia_console)
  -> tsc --noEmit clean; vite build succeeded (76 modules,
     dist/assets/index-CHe0g7FZ.js 70.28 kB)
```

`node v24.21.0` / `pnpm 10.26.1` measured in this environment.

### Independent reproduction in CI

The `frontend` job ("Console typecheck and build", `tsc -b && vite build`) and the
`Build canonical Render image` job (which builds `web/arkadia_console` per the
root `Dockerfile`) both passed on head `1c0edeae`. The Render image job emitted

```
dist/assets/index-CHe0g7FZ.js   70.28 kB
```

— the **same asset hash and byte size** as the local build recorded above, so the
bundle CI produced is the bundle measured here. `frontend` and `boot-syntax`
passed, as did the full-history secret scan.

---

## 7. Measured suite delta

Command (both trees, same environment):

```
PYTHONPATH=<repo>/archive/legacy_python python -m pytest tests/ -q -rEf --continue-on-collection-errors
```

| Tree | Summary | Failing/error node set (sha256) | Nodes |
|---|---|---|---|
| `main` `f390526a` (detached worktree) | 27F / 2342P / 17S / 1E | `521c63e1b75d3369aa6ca40e96c12268bd9c9b633e7584d514dd421e54ecdebe` | 28 |
| branch (this slice) | 27F / 2379P / 17S / 1E | `521c63e1b75d3369aa6ca40e96c12268bd9c9b633e7584d514dd421e54ecdebe` | 28 |

`diff` on the two sorted node sets is **empty** — no node was fixed or broken by
this slice. The `+37 passed` is exactly the two new test files: `--collect-only`
on them reports **37** nodes (18 + 19), matching the count delta. Both trees were
measured in the same environment, back to back, with the branch re-measured after
the final test edit.

### Independently re-measured (second environment, after the orphan-filter test)

A later pass added
`test_the_handler_filters_orphan_evidence_before_the_projection_sees_it` (38 nodes
in `test_prism_w4_run_evidence_trace.py` + 19 in `test_lab_run_trace_contract.py` =
57 for the slice) and re-derived the fingerprint in a **different environment**
where the dependency set differs from the one above:

| Tree | Failing/error node set (sha256) | Nodes |
|---|---|---|
| `main` `f390526a` | `a24c695f24998816ee4537096cad075718f21ef47840c6380431fb639cb3ab36` | 19 |
| branch | `a24c695f24998816ee4537096cad075718f21ef47840c6380431fb639cb3ab36` | 19 |

`comm -3` on the two sorted node sets is **empty** again. The absolute fingerprint
differs from the 28-node figure above because this environment's dependency set
resolves a different set of pre-existing failures — the load-bearing invariant is
the **node set**, not the count, and it is unchanged in both environments. The
28-node figure is retained as the first measurement, not superseded.

Architecture suite: **11 passed** (the contract's older "9/10" does not reproduce
here; recorded as measured).

`api/main.py` is untouched by this slice (`py_compile` clean; 2499 lines, within
the 2600 budget). All new paths were judged against the CP10 mutation boundary:

```
python scripts/cp10_mutation_boundary_policy.py --judge   ->  PASS (exit 0)
```

---

## 8. Known gaps / next bounded move

* **Not wired (deliberately):** every mutating Lab act (`/authorize`,
  `/execute`, `/transition`, `/run-agent`) and the declared canvas actions. The
  trace is an observation of recorded state, not a control surface.
* **Not attempted:** live run progress, streaming events, and PR projection
  (`GET /api/lab/engineering/pr/{number}` is a real `GET`). The ledger is a
  snapshot, not a live feed; the UI does not imply liveness.
* **Blocked (recorded, not worked around):** the automations read surface still
  needs a Workstream 1 registry entry (`labAutomations`). `lib/endpoints.ts`
  remains Workstream 1's file and is not edited here.
* **Next bounded move:** continue with the next verified Arkana/Weaver read
  surface that needs no shared-registry change, and integrate the automation read
  surface only once Workstream 1's `labAutomations` contract lands.
* No merge, production deployment, or acceptance is claimed.
