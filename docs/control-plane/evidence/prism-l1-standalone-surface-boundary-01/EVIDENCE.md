# PRISM-L1 — standalone surface render-failure boundary (Slice C)

Lane 1 (shell / navigation / design system / integration seam).
Governing docs: `docs/control-plane/overnight/PRISM-UI-RECONCILIATION.md`,
`docs/control-plane/parallel-ui/SHARED-CONTRACTS.md` §1.

- Lane branch: `feat/prism-l1-standalone-surface-boundary-01` (new bounded PR).
- Base: `origin/main` = `4ff76c152f057795bf57c3abeb8de9b0e772f67b`.
- Scope: 4 implementation paths plus this evidence record — `web/arkadia_console/src/App.tsx`,
  `tests/test_console_surface_error_boundary.py`, `web/arkadia_console/src/lib/endpoints.ts`,
  and `tests/test_console_endpoint_registry_contract.py`.

## 1. The defect, as the repository recorded it

PRR-06 mounted a render-failure error boundary, but the mount lived *inside* the
`<Shell>` block while the declared standalone surface returns before the shell.
`App.tsx` carried the limitation verbatim:

```
if (def.standalone) return body;   // recorded: "a render failure in the
                                   // external tester is not caught by a boundary"
```

`web/arkadia_console/src/lib/surfaces.ts` declares exactly one standalone surface,
`n-atlas` (`path: "/n-atlas-lab"`, `standalone: true`), reconciled from the retired
operator bundle. A render exception there tore down the whole tree with no
recovery control — the same failure PRR-06 exists to prevent, on the one surface
the boundary could not reach.

Measured at `4ff76c15`:

```
grep -n "if (def.standalone) return body;" web/arkadia_console/src/App.tsx  -> 1 match
grep -c "standalone" tests/*.py                                             -> 0 guards
```

The limitation was recorded in a source comment only. No test, evidence record,
or open PR claimed it (`gh api .../pulls?state=all` filtered on
`standalone|boundary|error bound` returns closed #514/#550, both non-merged, and
neither touched this path).

## 2. The change

The boundary is hoisted into a single `surfaceBody` wrapper that both return
paths use. The shell is what varies per surface, not the boundary — so a
standalone surface skips the shell, not the boundary.

```diff
-  if (def.standalone) return body;
+  const surfaceBody = (
+    <ErrorBoundary key={route.surface} surface={SURFACE_BY_ID[route.surface].name} onHome={() => navigate("home")}>
+      {body}
+    </ErrorBoundary>
+  );
+
+  if (def.standalone) return surfaceBody;

   return (
     <Shell current={route.surface} onNavigate={handleNavigate}>
-      <ErrorBoundary key={route.surface} ...>{body}</ErrorBoundary>
+      {surfaceBody}
     </Shell>
   );
```

Still exactly one `<ErrorBoundary>` mount (`_mount_count` unchanged), still keyed
by surface, still bound to the shared router — the existing guards for those
properties were not relaxed.

## 3. The guard, and its negative control

`test_boundary_wraps_the_surface_body_for_every_surface` replaced the previous
`..._inside_the_shell` assertion. That assertion encoded the defect: it required
the boundary to sit *inside* the shell block, which a standalone surface never
reaches. The replacement uses `_guards_every_surface()`, which requires the
hoisted wrapper, the `return surfaceBody` standalone path, and `{surfaceBody}` in
the shell.

`test_negative_control_detects_the_standalone_surface_escaping_the_boundary`
feeds the detector the **actual** pre-repair shape and asserts it is rejected,
while the live file passes. A guard silent on both the defect and its absence
would not be a guard.

## 4. Verification

Live negative control on the **real** file — the pre-repair `App.tsx` restored in
place, then the repaired file restored byte-identically:

```
pre-repair : 2 failed, 9 passed   (exactly the two intended nodes)
repaired   : 11 passed
```

| Check | Result |
|---|---|
| `pytest tests/test_console_surface_error_boundary.py` | 11 passed (was 10) |
| `pytest $(python scripts/console_contract_domain.py)` | 1065 passed |
| adjacent lane-1 guards (shell nav, return-to, canonical routing) | 70 passed |
| `pytest tests/architecture -q` | 11 passed |
| `corepack pnpm build` (`tsc --noEmit` + vite) | built in 2.10s |
| `scripts/lane_state.py --check` | exit 0 |

The guard is an existing tracked file, so it was already inside the derived
console-contract domain (`scripts/console_contract_domain.py`) — no workflow edit
was required. `api/main.py` is untouched; no boot-code change, so no
`py_compile` obligation arises.

## 5. Boundaries

Lane-1 owned paths only (`App.tsx` is the composition root; the guard is a
console-contract test). No route, alias, surface declaration, backend contract,
authority surface, or identity boundary changed. The standalone surface still
renders outside the shell, which is its declared contract.

Merge, production deployment, and acceptance remain human-only.

## 6. Engineering Lab PR-state route registration — shared integration seam

Lane 4's existing PR #624 surfaces the read-only `GET /api/lab/engineering/pr/{number}` handler. The handler is declared in `api/lab_routes.py::pr_state` under the `/api/lab` router, whose router-level dependency applies `require_lab_auth`. The response distinguishes `AVAILABLE` and `UNAVAILABLE`; no mutation route is involved.

This PR now supplies the Lane-1-owned registry half requested in #624:

- `web/arkadia_console/src/lib/endpoints.ts` declares `labEngineeringPr: "/api/lab/engineering/pr/{number}"` — the exact served route template, not an unserved prefix.
- `tests/test_console_endpoint_registry_contract.py::test_lab_pr_state_route_is_registered_from_the_served_handler` pins the registry key and confirms the exact template is present in `api.main:app.openapi()["paths"]`.
- The existing generic registry guard also checks that the new entry is served by the canonical app.
- Lane 4's #624 consumes the template and substitutes a validated, encoded PR number; a bare prefix or malformed template produces no request.

This reuses the existing endpoint registry and existing Lab handler. No backend route, identity, authorization, approval, persistence, WorkEvent, production configuration, or second API base was added. The route registration is committed on this Lane-1 branch so #624 can become wired after the shared entry is merged.

**Verification on source/test head `03aed5ef4b2dc0ea8794ece4e95473621e4afa00`:**

- Prism Console Contract [run 41997035224](https://github.com/Arkadia-Oversoul-Prism/Arkadia/actions/runs/41997035224): **1,066 passed in 50.49s**; CI-wiring guard **30 passed in 6.17s**.
- N-ATLAS Developer Lab [run 41997034890](https://github.com/Arkadia-Oversoul-Prism/Arkadia/actions/runs/41997034890): frontend typecheck/build, backend tests, canonical Render image, and N-ATLAS self-host image/smoke all succeeded.
- N-ATLAS external beta [run 41997034994](https://github.com/Arkadia-Oversoul-Prism/Arkadia/actions/runs/41997034994) succeeded; this supersedes the earlier source-head provider `error` event with null data.
- Canonical Render read-only runtime probe [run 41997034923](https://github.com/Arkadia-Oversoul-Prism/Arkadia/actions/runs/41997034923), security scan, boot syntax, economic seam, posture currency, and provider forensics checks succeeded.
- SG-02 [run 41997034929](https://github.com/Arkadia-Oversoul-Prism/Arkadia/actions/runs/41997034929) completed with outer workflow success. CP10-A passed **30**, SolSpire isolated integration passed **23**, CP10 API verification and unauthenticated browser route smoke succeeded (`consoleErrors=[]`, `pageErrors=[]`, `failedRequests=[]`).
- The authenticated Engineering Lab browser lens was **DEFERRED**, not PASS: Firebase web configuration was blank, no disposable identity was provisioned, and cleanup was skipped.
- CP10-B raw broader backend regression was **8 failed, 3,884 passed, 17 skipped, 3 warnings, 1 error**. The eight failing tests are the same set recorded in the canonical Engineering Lab evidence record under #624: two Lab API contracts, AIS persistence, identity-spine entry, ReasoMate shared session, two SolSpire R1 governance tests, and SolSpire R3 runtime; the collection error is `tests/test_autonomy.py`.
- The failing tests are outside this PR's changed paths. No base-main CP10-B run was available, so regression status is **UNKNOWN**; no full backend or authenticated browser acceptance is claimed.

The evidence-only follow-up that updates this record is separate from the verified source/test head. Merge and deployment remain human-only.
