# EVIDENCE — test-hygiene/authority-boundary-async-01

**Workstream:** `test-hygiene` (standalone, explicitly *not* an architectural gate)
**Pass:** hourly bounded execution, 2026-10-03
**BASE_MAIN:** `162f574b05dd839540d803aadda7608342618a84` (merge of PR #214)
**Pinned by:** PR #219 Pass 6 §8 (`gate-hygiene/open-pr-queue-merge-order-map-02`)
**Classification:** `IMPLEMENTED` (repair + measured delta); no merge authorization claimed.
**Authority:** none required. No merge, no push to `main`, no force-push.

This pass executes the bounded task that PR #219 Pass 6 §8 pinned. It repairs **one** of
the two unclaimed baseline nodes; the second (§5) is deferred because it carries a
product-design dimension, not a mechanism defect.

---

## 1. Baseline (re-measured at this pass, not inherited)

`PYTHONPATH=archive/legacy_python python -m pytest tests/ -q --continue-on-collection-errors -p no:cacheprovider`

| tree | passed | failed | skipped | errors | failing-node fingerprint (sha256, 21 nodes) |
|---|---|---|---|---|---|
| `main @ 162f574` | 1305 | **20** | 18 | 1 | `a59453b8a1e5a02899f469cf6ea7db9b5eaae658050261e1405c394cb0f3cf6f` |

The fingerprint was derived twice with identical results; the environment reproduces the
documented **20F / 1305P / 18S / 1E** exactly (this sandbox already had an async plugin
installed, which is why the proxy fingerprint matches the literal one here — see §3).

## 2. Defect — the async node could not fail

`tests/test_authority_api_enterprise_boundary.py::test_api_approval_does_not_create_enterprise_authorization_without_explicit_bridge`

The test is decorated `@pytest.mark.asyncio` but the module is `async def`. Two layered
defects, both preconditions that stop the body from ever executing:

1. **No async plugin declared.** `requirements.txt` lists `pytest` consumers but not
   `pytest-asyncio`; CI installs `pytest` alone. A collected `async def` test without a
   plugin is never awaited. This is the MIE lesson's class: *a job that runs the test is
   not evidence that any assertion ran.* The node therefore provided no authority-boundary
   coverage, independent of the behaviour it claims to guard.
2. **Body written against the pre-#180 API.** PR #179 (`4a84936`, 2026-10-02 04:31)
   merged the test; PR #180 (`ae847dd`, 2026-10-02 04:32) landed **immediately after** and
   rewrote `api/approval_routes.py` and `solspire/eden_ops.py`. `4a84936` is an ancestor
   of `ae847dd`. The reconciled signature is now `api_approve(approval_id, *, user)` with
   authority (`_require_govern_authority`) on the authenticated principal, and
   `decide_proposal(..., actor_identity=…)` requiring governance authority. The test called
   the old signature.

## 3. Repair

- `tests/test_authority_api_enterprise_boundary.py` — updated the node to the **#180
  authority model**: requester and approver are distinct principals (self-approval is
  refused by the reconciled boundary), the approver carries governance authority, and the
  EdenOps bridge passes `actor_identity`. The test's *claim* is unchanged: deciding an
  approval does **not** create an enterprise authorization record; only the explicit
  EdenOps bridge does.
- `requirements.txt` — declared `pytest-asyncio` with a rationale comment, so the async
  boundary is actually executed in CI and locally.

## 4. Measured delta (by node identity, never by count)

Composed tree = `main @ 162f574` + both files:

| tree | passed | failed | skipped | errors | fingerprint (sha256) |
|---|---|---|---|---|---|
| baseline | 1305 | **20** | 18 | 1 | `a59453b8…` (21 nodes) |
| repaired | 1306 | **19** | 18 | 1 | `e4d010eb…` (20 nodes) |

- **fixed (1):** `tests/test_authority_api_enterprise_boundary.py::test_api_approval_does_not_create_enterprise_authorization_without_explicit_bridge`
- **newly failing: 0**
- **unchanged: 20**

## 5. Second pinned node — DEFERRED

`tests/test_solariun_thread_navigation_01.py::test_shell_wires_home_to_lens_selection`

PR #219 Pass 6 §7.1 classified this `STALE_ASSERTION` with a **product-design dimension**:
sovereign PR #189 (`6d5f722b`) deliberately replaced the mount with
`<SolariunInteractionCanvas onNavigate={target=>{…}}/>`, whose handler is typed
`(target: string) => void` — not the canonical `SolSpireLens` union the test intent pins.
Repairing the assertion therefore means **deciding whether the live canvas should be
bounded to `SolSpireLens`**, which is a product call reserved to the sovereign. This pass
did **not** execute it: the bounded objective is the mechanism defect (§3), and widening
scope to a design decision would violate the no-self-expansion rule.

## 6. Protected surfaces

| check | result |
|---|---|
| `python -m py_compile api/main.py` | OK |
| `wc -l api/main.py` | **2582** — within the 2600 budget |
| `pytest tests/architecture -q` | **11 passed** |
| CP10 boundary judge on the diff | PASS (rc=0) |
| `api/main.py` touched | **no** |
| authority model / identity boundary / governance changed | **no** — only test + dependency declaration |

## 7. Deliberately excluded

- PR #220 (`SH-05` retirement, draft/HOLD) — untouched; requires a sovereign `SH-05`
  disposition. Per #219 Pass 6 §8, #220's Gate-adjacent test edits and this repair must
  **not** be merged in one batch without the sovereign seeing the combined test-file
  inventory.
- The five-PR composable cluster (#215–#219) — not modified by this branch; this is a
  separate bounded PR.

## 8. What this pass does NOT claim

- No merge authorization — `READY FOR SOVEREIGN MERGE`, not merged.
- No production parity — Gate 2 remains `BLOCKED` (provider auth).
- No async coverage claim beyond the one repaired node; `asyncio_mode` remains the default,
  so unrelated `async def` tests (if any) stay un-awaited and are out of scope here.
