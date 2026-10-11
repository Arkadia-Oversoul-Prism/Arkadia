# Workstream 4 — Engineering Lab read-only session read model

**Workstream:** 4 (Arkana/Oracle, Weaver, Engineering Lab)
**Branch:** `feat/prism-parallel-04-arkana-weaver-lab`
**PR:** #422 (draft)
**Evidence bound to branch SHA:** `b5125f090d31abe1766b130cf1594f16c1c14e2c` (the commit this
slice is layered on). The slice commit SHA is recorded in the PR comment; this file binds to
the tree it describes.
**PR base (`main` at read time):** `d2670ce8b41c500df5cf475f7c6526016c7bd3aa`
**Observed `origin/main`:** `8dcb782d` — re-fetch before acting; neither SHA is a permanent pin.

**Authority:** read-only slice. No merge, deployment, or acceptance is claimed or performed.
Render is canonical under ADR-016.

---

## 1. Discovery — exact feature paths (source evidence)

| Surface | Console path (feature-local) | Backend module | SHA |
|---|---|---|---|
| Arkana/Oracle | `web/arkadia_console/src/pages/ArkanaPage.tsx` (+ `src/lib/arkana.ts`) | `api/main.py::commune_resonance`; `api/commune_threads.py` | `b5125f09` |
| Weaver | `web/arkadia_console/src/pages/WeaverPage.tsx` | `api/approval_routes.py` | `b5125f09` |
| Engineering Lab | `web/arkadia_console/src/pages/EngineeringLabPage.tsx` | `api/lab_routes.py`; `lab/engineering_lab/*` | `b5125f09` |

The retired Prism UI is preserved at `archive/frontend/arkadia-prism/web/public_prism/`
(`ArkanaCommune.tsx`, `OracleVoicePlayer.tsx`, `ReasoMatePage.tsx`, `SolSpireConsole.tsx`, …).
Archive is source evidence, not code to restore blindly. The console
(`web/arkadia_console`) is canonical and is what the backend and image build/serve
(`tests/test_frontend_arkadia_console_rebuild_01.py`).

### Verified backend contracts (method / path / auth)

Read from the live FastAPI route table (`app.openapi()`), not from archive usage:

| Method | Path | Auth |
|---|---|---|
| POST | `/api/commune/resonance` | **anonymous by design** — the handler takes `request: Request` only (`api/main.py:1154`); rate-limited (20/60s) |
| GET | `/api/commune/threads` | bearer (401 without a verified uid) |
| GET | `/api/approvals` | bearer (401); ordinary callers see only their own; `Govern` authority sees all |
| GET | `/api/lab/engineering/sessions` | bearer — `require_lab_auth` |
| GET | `/api/lab/engineering/sessions/{session_id}` | bearer — `require_lab_auth` |
| POST | `/api/lab/engineering/sessions/{id}/authorize` · `/execute` · `/transition` · `/run-agent` | bearer — mutating Lab state, human decision |

`api/lab_routes.py` mounts `dependencies=[Depends(require_lab_auth)]` on the whole router; the
only public exceptions are two N-ATLAS tester paths (`catalog`, `test-session`).

### State / event / evidence contract (read, not inferred)

`lab/engineering_lab/contracts.py::LEGAL_TRANSITIONS` is the authoritative session state
vocabulary (13 states). `runtime.session_view()` returns
`{session, agent, runs, events, evidence, artifacts, loop, reached_review_boundary,
human_decision_required}`. `COMPLETED` is a **human-accepted terminal**
(`HUMAN_TERMINAL_STATES`) the substrate never self-sets.

---

## 2. The slice — one isolated, feature-local, read-only capability

`web/arkadia_console/src/components/lab/LabSessionList.tsx` (new, feature-local) reads
`GET /api/lab/engineering/sessions` and lazily `GET /api/lab/engineering/sessions/{id}` on
selection, rendering the governed state ladder with each stage named and annotated.

Wired into `web/arkadia_console/src/pages/EngineeringLabPage.tsx`, replacing the scaffold
placeholder for the sessions collection. The mutating acts (authorize/execute/transition) remain
an explicit `NotYetWired` blocked state — the read-only ceiling is a product boundary, not a
missing feature.

### Governance distinction preserved

- The rendered state vocabulary is asserted **identical** to `LEGAL_TRANSITIONS`; a UI state the
  substrate cannot enter would let the surface imply a stage the backend never granted.
- `READY_FOR_REVIEW` renders "at the human review boundary — this is not acceptance"; only
  `COMPLETED` maps to `ACCEPTANCE`. Reaching review is not rendered as acceptance.
- An unrecognised state renders as `UNKNOWN`, never coerced into a known stage.
- The component issues **GET only** and references **none** of the mutating Lab paths.

---

## 3. Verification (commands + measured results)

```
python -m pytest tests/test_prism_w4_lab_read_model.py -q -rEf   -> 13 passed
python -m pytest <targeted frontend + lab regression set>       -> 79 passed, 2 failed (pre-existing)
corepack pnpm install --frozen-lockfile                         -> Done
corepack pnpm build   (tsc --noEmit && vite build)              -> built, 63 modules, no TS errors
printf <4 paths> | python scripts/cp10_mutation_boundary_policy.py --judge -> PASS (exit 0)
```

### Baseline comparison — failing-node identity, not counts

The two targeted-set failures are `tests/test_engineering_lab_api.py::`
`test_lab_router_is_read_only_and_authenticated` and
`test_lab_mutation_endpoints_are_exactly_the_lab_state_set`. Both were **re-measured on
`origin/main` `8dcb782d`** in this environment: `2 failed, 3 passed`. They are the documented
unowned N-ATLAS drift (`/api/lab/engineering/n-atlas/run` and `/test-session` added without
updating `ALLOWED_MUTATION_ENDPOINTS`). **Not caused by this slice**; repairing them edits
`api/lab_routes.py`, an authority surface carrying the Lab mutation boundary — sovereign-only,
proposed not executed.

### Negative controls (detectors proven against the real file)

The guard's four detectors were each exercised by mutating `LabSessionList.tsx` in place, then
restoring it byte-identically (`grep -c injected` -> 0, guard back to 13 passed):

| Injected defect | Guard node that reddened |
|---|---|
| `apiRequest(path, { method: "POST" })` | `test_read_model_issues_no_mutating_request` |
| a reference to `/authorize` | `test_read_model_does_not_reference_the_mutating_lab_endpoints` |
| an invented state key in `STATE_STAGE` | `test_rendered_state_vocabulary_is_the_backend_vocabulary` |
| `COMPLETED` re-mapped away from `ACCEPTANCE` | `test_review_boundary_is_not_rendered_as_acceptance` |

Two further controls are in-file: `test_negative_control_detector_flags_a_mutating_read_model`
and `test_negative_control_state_vocabulary_detector`.

---

## 4. Boundaries preserved

- No edit to `App.tsx`, `lib/router.ts`, `lib/surfaces.ts`, `lib/endpoints.ts`, global
  navigation/tokens, shared shell tests, NovaNet/Solariun files, runtime/authority model, or
  deployment configuration.
- No invented endpoint: the read model consumes the declared collection endpoint and the
  backend's own session sub-resource.
- No fabricated data, no hidden execution, no authorization bypass.

## 5. Known gaps and the next bounded move

- **Interface request to Workstream 1:** add `labSession: (id) => /api/lab/engineering/sessions/${id}`
  to `src/lib/endpoints.ts` so the view path stops being composed feature-locally. This slice
  deliberately does not write that file (single-owner rule).
- **Arkana history (deferred):** `GET /api/commune/threads` and
  `GET /api/commune/threads/{uuid}/messages` are verified bearer contracts. A thread-history
  surface is the next natural bounded slice on this branch.
- **Weaver:** `WeaverPage` already reads `/api/approvals` and renders approval != execution. The
  approvals contract was verified here (bearer; `Govern` authority for decisions; self-approval
  prohibited). A read-only view of the separate `weaver/enterprise_orchestration` proposal ->
  evidence -> verification -> acceptance chain is a candidate next slice; it is not a UI-only
  change.
- **Unverified, therefore not built:** Arkana streaming, memory/citation controls, and
  model-provider readiness are not inferred from the archive. `POST /api/commune/resonance` is
  anonymous by design, which is why the existing `ArkanaPage` sends without a token.

**Next bounded move:** open the `endpoints.ts` interface request to Workstream 1, and — subject to
authorization — build the Arkana thread-history read slice against the verified
`/api/commune/threads` contract.

**No merge, no deploy, no acceptance.**
