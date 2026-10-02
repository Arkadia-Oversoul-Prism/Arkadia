# GATE-HYGIENE — Baseline fingerprint reproducibility

Pass: `gate-hygiene/baseline-fingerprint-reproducibility-01`
Date: 2026-10-02 (UTC)
Base main: `702b63ae633180034d1a36aa68b090541af6dae3`
Repository: `Arkadia-Oversoul-Prism/Arkadia`
Status: **IMPLEMENTED** (verified locally; sovereign review required)

## 1. Why this pass exists

The repository publishes a *baseline test-debt fingerprint* — a hash of the
failing/error node set — and uses it to attribute regressions. A fingerprint is only
usable if an independent operator can re-derive it. `.bootstrap/01_STATE.md` had
recorded **three** values that could not be reproduced from the derivation printed
beside them (`a7687fad…`, `d7ff35b2…687036`, and the current `a59453b8…`), and an
earlier pass had tested 62 derivations without a hit. The pass objective was narrow:
**resolve the mismatch by measurement and make the derivation reproducible.**

## 2. Root cause — RESOLVED (VERIFIED)

Two independent defects, both in the *derivation*, not in the node set.

1. **Wrong convention documented.** The published derivation read
   `sha256("\n".join(sorted(FAILED/ERROR node ids)) + "\n")` — the node-set
   convention — but `a59453b8…` is actually
   `sha256("\n".join(sorted("<OUTCOME> <nodeid>")) + "\n")`, i.e. with the
   `FAILED`/`ERROR` prefix retained.
2. **Terminal width baked into the hash.** The node ids had been read from `pytest -q`
   output *including* the assertion reason. `pytest -q` truncates that reason to the
   terminal width, so the same node set hashed differently in a 120-column CI job than
   in an 80-column shell. This is why the earlier sweeps could not find a hit: every
   candidate was built from already-truncated input.

Both conventions were then reproduced exactly:

| convention | `sha256("\n".join(sorted(…)) + "\n")` | reproduces `a59453b8…`? |
|---|---|---|
| outcomes `"<OUTCOME> <nodeid>"` | `a59453b8a1e5a02899f469cf6ea7db9b5eaae658050261e1405c394cb0f3cf6f` | **yes** |
| node set `"<nodeid>"` | `9a35c8122188e272ec5769d7a8f5cdba6160b4f2f1fba8a840019a487c1bcc22` | no |

Search exhausted before concluding: 210 derivations (separator × trailing byte ×
ordering × `FAILED/ERROR` prefix kept or stripped × reason stripped × `tests/` prefix
stripped × case-folded sort × drop-the-error-node). Exactly one hit.

## 3. Regression attribution — NO REGRESSION (VERIFIED)

The failing/error node set is **byte-identical at three revisions**, under both
conventions:

| revision | nodes | outcomes fingerprint | node-set fingerprint |
|---|---|---|---|
| `64cbe74` | 21 | `a59453b8…` | `9a35c812…` |
| `481afa1` | 21 | `a59453b8…` | `9a35c812…` |
| `702b63ae` (current main) | 21 | `a59453b8…` | `9a35c812…` |

The recorded `64cbe74 → 481afa1` "node set identical" claim is therefore **confirmed by
measurement**, not contradicted.

Note on the passed count: it reads 1240 on some runs and 1242 on others **of the same
tree**. That is the order-dependent
`tests/test_engineering_lab_agent_loop.py::test_agent_loop_does_not_mutate_repository`
already documented in `AGENTS.md` — a passed-count wobble, never a failure-node change.
Regression is attributed from the failing/error node set only.

## 4. Change

- `scripts/baseline_fingerprint.py` (new) — read-only, stdlib-only. Parses a pytest log
  and prints both fingerprints, plus failed/error counts. `--json` for machine output.
- `tests/test_baseline_fingerprint.py` (new) — 10 tests. Known-answer tests pin both
  derivations; the terminal-width and report-order properties are asserted directly; an
  independent `hashlib` re-implementation guards the extractor from drifting; the
  `FAILED`↔`ERROR` distinction is pinned so the two fingerprints cannot be conflated.
- `.bootstrap/01_STATE.md` — derivation corrected to the executable script, both values
  recorded, and the superseded non-reproducible values explained.

## 5. Evidence (commands actually run)

```
python scripts/baseline_fingerprint.py /tmp/nodes702.txt
  -> 21 nodes (20 failed, 1 error)
     outcomes a59453b8a1e5a02899f469cf6ea7db9b5eaae658050261e1405c394cb0f3cf6f
     ids      9a35c8122188e272ec5769d7a8f5cdba6160b4f2f1fba8a840019a487c1bcc22

python -m pytest tests/architecture -q                      -> 11 passed
python -m pytest tests/test_baseline_fingerprint.py -q      -> 10 passed
python -m py_compile api/main.py                            -> OK (2571 lines / 2600)

# full suite, branch vs main
branch:  20 failed, 1252 passed, 17 skipped, 1 error
main:    20 failed, 1242 passed, 17 skipped, 1 error
delta:   +10 passed (exactly the new test file); failing/error node set EMPTY

git diff --name-only main...HEAD | python scripts/cp10_mutation_boundary_policy.py --judge
  -> Mutation boundary PASS (exit 0)
```

## 6. Limits / not claimed

- `vite_build` remains environment-blocked (no npm registry access); not attempted.
- The 21 baseline failure nodes are **not** repaired here. They are classified debt and
  are separate bounded workstreams, per the standing rule that baseline debt is not fixed
  inside an unrelated pass.
- This pass makes the fingerprint *reproducible*; it does not make the baseline *green*.

## 7. Authorization

Sovereign merge authority. No merge performed by the agent. No push to `main`.
