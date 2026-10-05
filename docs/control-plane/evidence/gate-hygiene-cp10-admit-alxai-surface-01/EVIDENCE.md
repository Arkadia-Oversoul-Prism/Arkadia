# gate-hygiene — admit the `alxai/` surface to the CP10 mutation boundary

Pass: `gate-hygiene/cp10-admit-alxai-surface-01`
BASE_MAIN at reconstruction: `dc6d1563cd53e15f1c3ceb80b434fd37b62f3f11`
("Merge pull request #304 … oversoul-prism-144-substrate")
Branch: `gate-hygiene/cp10-admit-alxai-surface-01`

## 1. Defect

`alxai/` is a legitimately tracked product surface (`__init__.py`, `protocol.py`,
`reconcile.py` — the AL-XAI-04 deterministic reconciliation engine, merged to `main`
via PR #298 and consumed by `tests/conformance/test_alxai04.py`), but it was not
enumerated in `scripts/cp10_mutation_boundary_policy.py::LEGIT`.

This is the exact "allowlist is an inventory, not a filter" class already documented
in `AGENTS.md`. Measured: **exactly 3** rejected tracked paths, all under `alxai/`
(judging every path in `git ls-files`). Three fitness tests are consequently red on
`main`, and the CP10 workflow (`sg-02-fe-2-v.yml`, path-filtered) will reject the next
ordinary commit that touches the tree.

Failing on `main` before this pass:

- `tests/test_m02a_ci_gate_integrity.py::test_allowlist_admits_every_tracked_top_level_prefix`
- `tests/test_m02a_ci_gate_integrity.py::test_allowlist_covers_every_tracked_surface`
- `tests/test_m02a_ci_gate_integrity.py::test_delegated_verdict_admits_every_tracked_surface`

## 2. Change (bounded)

A single regex alternation added to `LEGIT` plus an explanatory comment. No other
surface admitted; no other rule changed.

```diff
-r"\.github/|web/|api/|solspire/|kernel/|weaver/|lab/|tests/|docs/|scripts/"
+r"\.github/|web/|api/|solspire/|kernel/|weaver/|lab/|tests/|docs/|scripts/|alxai/"
```

## 3. Measurements

| check | before | after |
|---|---|---|
| rejected tracked paths (`git ls-files`) | **3** (`alxai/*`) | **0** |
| `test_m02a_ci_gate_integrity.py` | 3 failed / 57 passed | **60 passed** |
| CP10 judge, `alxai/protocol.py` | FAIL (exit 1) | **PASS (exit 0)** |
| negative control: `SolSpireExperienceV3.tsx` | FAIL | **FAIL (exit 1)** — denylist intact |
| negative control: unknown root | FAIL | **FAIL (exit 1)** — unknown-root rejection intact |

The two negative controls prove the change did not flatten the boundary: the
constitutional V3 dual-shell denylist and the unknown-root rejection still have teeth.

## 4. Why this is a separate pass

The `alxai/` omission is independent of the `api/main.py` 2600-line budget defect
(PR #308). Per the contract's step 11, non-consequential follow-on work is isolated on
its own branch rather than folded into an unrelated PR.

## 5. Remaining uncertainty

- `alxai/` is not registered in `tests/architecture/LAYER_MAP.py`. Nothing asserts
  LAYER_MAP completeness (11 architecture tests inspected), so this is not required for
  the gate; registering it with a correct layer is a separate, optional workstream.
- `tests/test_verification_review_boundary.py` (4 failures) asserts the *absence* of a
  Review record type, but `weaver/enterprise_orchestration.py` now defines
  `ew_reviews` / `ReviewRecord` / `review_id`. That is a **semantic design conflict**,
  not a mechanical or env-dependent failure — it requires an authority decision and is
  deliberately **not** touched here.

## 6. Authorization

Ready for sovereign review and merge. No merge performed by this agent.
