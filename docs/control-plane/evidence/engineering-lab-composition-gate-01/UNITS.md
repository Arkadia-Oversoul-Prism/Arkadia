# Bounded repairs — per-unit detail

Each unit was rebuilt against current `main` (`341867ebe4ea80ead557ca632707833b7620430a`),
not revived as-is. A stale branch whose base has moved is not a candidate: two of the
units below had to be rebased over merges that landed *their* predecessors (#497, #511).

## Unit A — `gate10/history-depth-repair-02` @ `b63f74e8dd5c`

Source: **#482** (`0cc7c9e766d8`), base `ee684fff`.

`provider-routing.yml` is byte-identical between #482's base and current `main`, so the
one-line workflow repair (`fetch-depth: 0`) applies unchanged, and the `AGENTS.md`
append lands cleanly as an insertion-only addition:

- `scripts/agents_md_encoding_audit.py` → `alterations=0`, `reproduced=True`,
  Cyrillic `0 -> 0`.

The repair's effect, measured in CI on both trees:

| Tree | CI failing/error nodes |
|---|---|
| `main` `341867eb` | **14** |
| candidate `b63f74e8` | **9** |

Removed (all five are shallow-checkout artifacts; the log says
`merge commit 972c3423 is not in this clone (shallow checkout?)`):

```
tests/test_agents_md_encoding_adjudication.py::test_cli_summarises_the_oracle_without_crashing
tests/test_agents_md_encoding_adjudication.py::test_corruption_origin_is_re_derivable
tests/test_agents_md_encoding_adjudication.py::test_exit_code_does_not_call_a_divergent_clean_file_verified
tests/test_agents_md_encoding_adjudication.py::test_live_file_verdict_matches_its_state
tests/test_lane_instruction_doc_currency.py::test_detector_flags_a_merged_pr_left_recorded_as_open
```

Introduced: **none**. Locally, the full-suite node set is `9de837ea…` on both trees
(214 nodes, `comm -3` empty); `+17 passed` is the new guard file.

## Unit B — `ui/alias-families-union-02` @ `e350316d2322`

Source: **#505** (`8cb030c03886`), base `49809f4527`.

**#497 is already merged** (`f44011e2`), so #505's branch is stale. Rebuilt on `main`:

- `router.ts` applied cleanly; the alias table is a **union** — #497's
  `/nexus` (with its namespace sub-path handling) is preserved and the four #505
  families are added: `/home`, `/knowledge-os`, `/gate`, `/living-gate`.
- The test file conflicted; resolved as a **union of both probe sets** rather than
  choosing a side.

Focused: `tests/test_console_shell_nav_contract.py` → **38 passed**.
Build: **success**, `index-4-WtClOi.js` (144,301 B); markers `/knowledge-os`,
`/living-gate`, `/nexus`, `/gate`, `/home` all present.
CI: `prism-console-contract.yml` @ `e350316d` → **success**.

## Unit C — `ui/return-to-error-boundary-02` @ `35951e6eddf0`

Source: **#514** (`e48cbf2620ad`), base `dfbd2304db`.

**#511 is already merged** (`d674e0e4`), so #514's `App.tsx` hunk conflicted. #514 was
authored against `onNavigate={(id) => navigate(id)}`; `main` now binds
`onNavigate={handleNavigate}` (the return-to wrapper). Rebuilt by hand:

- the `handleNavigate` binding is **preserved** (merged #511 behaviour is not regressed);
- `ErrorBoundary` is added around the surface body, keyed by `route.surface`, with
  `onHome={() => navigate("home")}` bound to the shared router.

Focused: `test_console_surface_error_boundary.py` + `test_console_return_to_contract.py`
+ `test_console_shell_nav_contract.py` → **59 passed** (both features coexist).
Build: **success**, `index-CraRQ7Av.js` (145,491 B). Markers `surface-error-boundary`,
`surface-error-reload`, `arkadia.returnTo` present; the `main` negative control build
reports **0** for the two boundary markers, proving they discriminate the change.
CI: `prism-console-contract.yml` @ `35951e6e` → **success**.

## Unit D — `eaa/chain-composition-02` @ `a68fefbdfff0`

Source: **#535** (`8b6eadd77aa1`), base `7580bd8f`.

#535 is an open draft; it applies cleanly to current `main` (31 files, no conflicts).

Focused: `test_engineering_acceptance_authority.py`,
`test_gate_l4_dispatch_security.py`, `test_gate_l4_run_inspection.py`,
`test_github_readonly_evidence_adapter.py` → **43 passed**.
Full suite: node set `9de837ea…` **identical** to baseline (214 nodes).
CI @ `a68fefbd`: `lab-security-contract` success, `gitleaks-config-guard` success,
`weaver-mvp2-validation` success.

`.gitleaks.toml`: #535 adds one allowlist entry, `^NovaNet/Solariun$`. Verified the
literal is **not a credential** — it is two product names separated by a slash,
appearing only in prose (6 doc occurrences), with no key material. This is a
legitimate policy addition under the recorded rule (only allowlist a value you have
read and verified is not a secret), and `gitleaks-config-guard` passes at this head.

## Not built

- **#525** — decided HELD in the prior pass (Arrangement D keeps `ExecutionLoop` at
  exactly one render site). Not integrated; capability stays on hold.
- **#542/#543**, **#538/#544** — see `QUEUE.md`; not attempted this pass.
