# EVIDENCE — gate01/option-a-completeness-adjudication-01

Trajectory: `ARK-$200K-READINESS-01` (GATE-01 — canonical authorship / portfolio substrate)
Move class: bounded defect repair on an open PR (no gate promotion, no authority change,
no merge, no new mutation path)
Branch: `gate01/portfolio-initiative-slice` (PR #351)
Base: `main` @ `ff3f6d4294728464669d78eaa356dc5021ab4477`
Head before this pass: `103b51217`
Head after this pass: `48226931`

## Observation

`tests/test_ark_200k_gate_01_portfolio_initiative.py::test_portfolio_to_initiative_is_canonical_and_traversable`
— the PR's own proof test — **failed** on its own head:

```
FAILED tests/test_ark_200k_gate_01_portfolio_initiative.py::test_portfolio_to_initiative_is_canonical_and_traversable
```

## Defect (test-side, measured not inferred)

The test asserted:

```python
assert reverse["complete"] is True
```

for the option A `PORTFOLIO -> INITIATIVE` chain. Two independent facts contradict it:

1. `weaver/enterprise_orchestration.py::reverse_walk` computes
   `complete = bool(roots)` where
   `root_kinds = {"CANONICAL_RECORD", "AUTHORITY_EVENT"}`.
2. `docs/architecture/GATE-01_CANONICAL_AUTHORSHIP_IMPLEMENTATION.md` §3.4 states the
   staging nodes "are records, not authority" and add no path into
   identity / authority / authorization / approval / execution.

A healthy option A chain therefore has **no** such root, and `complete is False` is the
correct value. The assertion transposed the plan's §4.3 assertion 5
(`reaches a root of kind CANONICAL_RECORD or AUTHORITY_EVENT, with complete == True`),
which is scoped to the **authority-rooted full chain (option C)**, into an option A test
where it does not apply.

Corroboration: `tests/test_enterprise_orchestration.py` pins `complete is True` only for
walks rooted in a human `AUTHORITY_EVENT` and asserts
`any(r["kind"] == "CANONICAL_RECORD" for r in walk["records"]) is False` for that same
walk — i.e. the substrate treats a human authority origin, not any top, as what makes a
chain complete.

## Repair

`48226931` — two changes, both inside the hunk this PR already introduces:

| File | Change |
|---|---|
| `tests/test_ark_200k_gate_01_portfolio_initiative.py` | assert `complete is False`, with a comment pinning the strict semantics |
| `weaver/enterprise_orchestration.py` | replace the dead no-op `_rows_where` loop in `forward_walk`'s `INITIATIVE` branch with an explicit "no forward edge yet" statement |

## Rejected alternative (recorded, not silently discarded)

Widening `complete` so that a verified `PORTFOLIO` counts as a chain top would make this
one assertion pass, but it changes the meaning of the substrate's grounding flag: a later
option B/C chain whose canonical/authority origin had been deleted would stop at the
portfolio and report `complete=True` — a claim appearing grounded while its origin is
missing. That is a boundary weakening, not a test repair, and it requires a sovereign
semantic decision. The test now pins `complete is False` so a silent widening fails here.

## Verification (measured on this tree)

| Check | Command | Result |
|---|---|---|
| Proof test + 6 traversal consumers | `pytest tests/test_ark_200k_gate_01_portfolio_initiative.py tests/test_enterprise_orchestration.py tests/test_gate_02_09_orchestration_deltas.py tests/test_evidence_verification_boundary.py tests/test_verification_review_boundary.py tests/test_eden_ops_01.py tests/test_upstream_causal_continuity_01.py -q` | **48 passed** |
| Architecture fitness | `pytest tests/architecture -q` | **11 passed** |
| Full suite (before) | `pytest tests/ -q --continue-on-collection-errors -rEf` | 21 failed / 1753 passed / 21 skipped / 1 error |
| Full suite (after) | same | **20 failed / 1754 passed / 21 skipped / 1 error** |
| Failing/error **node set** delta | sorted `FAILED`/`ERROR` node lists | **-1**, exactly this PR's own node; **no new node** |
| CP10 mutation boundary | `scripts/cp10_mutation_boundary_policy.py --judge` | **PASS** |
| Boot compile | `python -m py_compile api/main.py` | OK — `api/main.py` 2434/2600 lines, untouched |

Node-set hashes (the load-bearing invariant — counts move with how many tests are present):

```
before: dfb8a55053694dfe2f16bc6c6c094f7b31a79851b03c75fd458f4a87dd562bf3  (22 nodes)
after:  4ede2e044de2b27873e97ce3f1ac1dfe6fefbbd69fc1250d84bdde2e5e390f3e  (21 nodes)
```

## Red checks, attributed rather than hidden

- `provider-routing` → **Broader test suite** step fails on this PR's head. It **also fails
  on `main`** (`17e626cd2`, run `37539664677`), so it is pre-existing and not attributable
  to this PR. Classified pre-existing, not fixed here (baseline-debt rule).
- `Vercel – arkadia-prism` / `Vercel – console`: provider rate limit
  `api-deployments-free-per-day` (>100 deployments/day on the free tier), and a
  pre-existing failure on `main`. Not a code defect.

## Acceptance boundary

This evidence claims: the bounded option A slice is implemented, its proof test passes,
and no regression was introduced. It does **not** claim Gate 01 PASS or production parity.
Gate 01 closure remains with the sovereign.
