# WORKSTREAM_STATE — `gate-hygiene` / SOLARIUN-THREAD-NAV supersede

Persisted so the next hourly heartbeat reconstructs from evidence, not memory.
**Reconstruct live state anyway (contract §14) — do not trust this file over the repository.**

## Pass record — 2026-10-03 (heartbeat, ~12:2xZ) — SH-02 batch continuation

Executed the task pinned by PR #224 §"Next bounded task".
New PR **#225**, branch `gate-hygiene/solariun-thread-nav-supersede-01`, base
`main 162f574b05dd839540d803aadda7608342618a84`, head `54d59500669822cb81530c9a562a6b42d86c288e`.

- **Fixed node** `tests/test_solariun_thread_navigation_01.py::test_shell_wires_home_to_lens_selection`.
  Classification: **stale-assertion supersede**, not regression. Sovereign merge `6d5f722`
  (PR #189) retired the `SolariunHomeCockpit` Home mount in favour of
  `SolariunInteractionCanvas`; the component is dead code (sole reference is its own export).
  Re-pointed the mount assertion to the live canvas; kept the `SolSpireLens` typing assertion.
  Source-side repair rejected — would re-introduce the retired mount.
- **Fingerprint measured live at `162f574`** (not inherited): 20 failed / 1306 passed /
  17 skipped / 1 error; node-set 21, fp `a59453b8…`. Branch head: 19 / 1307 / 17 / 1;
  node-set 20, fp `66a69c50…`. **Delta −1 / +0.**
- `tests/architecture` **11/11**; `api/main.py` **2582 / 2600**, `py_compile` clean;
  CP10 judge PASS.

## Queue (reconstruct live — do not trust this list)

Open queue at branch point was **#215–#224** (10 PRs, all `gate-hygiene`, base `main`).
#225 joins it. Composition: #225 touches only `tests/test_solariun_thread_navigation_01.py`,
which no other open PR modifies — order-independent.

## Next bounded task (proposed, not executed)

`SH-02` still carries remaining `STALE_ASSERTION` nodes. Re-derive the live failing-node set,
classify the remaining test-side literal pins against their source literals, and take the next
smallest one as a separate bounded batch. **Discovery does not authorize execution** — confirm
the task is inside the active envelope before mutating.

Merge is the sovereign's. This pass requests none.
