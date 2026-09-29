# EVIDENCE — Gate hygiene: stale-assertion repair (identity spine / `ais_profile`)

- **Gate / workstream:** GATE-10 context — test-suite hygiene
- **Bounded task:** `SH-02`, batch 3 — the `api/ais_profile.py` identity-spine family
  (`tests/test_ais_w8_canonical_identity.py`, `tests/test_identity_spine_w1.py`)
- **BASE_MAIN:** `4164573586860b9c7e04e1815bca4957559046a2`
  (merge of PR #128 `gate-l1.1-boundary-hardening`)
- **Branch:** `gate-hygiene/baseline-stale-assertion-repair-identity-spine-03`
- **Authority:** test-hygiene only. No source, policy, governance, architecture, or product mutation.
- **Status:** IMPLEMENTED (targeted tests pass, protected regressions pass, controls fire,
  full-suite delta verified by name; sovereign merge pending)

---

## 1. Scope

Repair the stale string assertions that fail against `api/ais_profile.py` because the module
is written in a compact **single-quote** house style while the assertions pin **double-quote**
literals. The contracts are intact; only the assertion's copy of the literal drifted.

Changed test nodes (3):

| file | node |
|---|---|
| `tests/test_ais_w8_canonical_identity.py` | `test_w8_ais_projection_reuses_authenticated_uid` |
| `tests/test_ais_w8_canonical_identity.py` | `test_w8_no_second_authentication_or_identity_store_is_created` |
| `tests/test_identity_spine_w1.py` | `test_ais_profile_exposes_canonical_identity_spine` |

Five assertions (4 failing, 1 added as a compensating negative control) were migrated from
exact-literal substring checks to quote-agnostic regexes.

## 2. Precondition — the invariant is intact in live source

Measured against the live `api/ais_profile.py` at `BASE_MAIN`:

| literal | occurrences | verdict |
|---|---|---|
| `load_user_profile_store(user['uid'])` | 4 | present (single-quoted) |
| `load_user_profile_store(user["uid"])` | 0 | absent — assertion was stale |
| `_SPINE_KEY` | 4 | present |
| `'identity_spine'` | 1 | present (single-quoted) |
| `@router.get('/api/me/identity-spine')` | 1 | present (single-quoted) |
| `'ais_capability_portfolio'` | 1 | present (single-quoted) |
| `"ais_capability_portfolio"` | 0 | absent — assertion was stale |
| `Depends(require_auth)` | 5 | present |
| `/api/me/ais-profile` | 2 | present |

Composition precondition verified: `api/nodes.py:51` does contain
`router.include_router(_ais_profile_router)`, so
`test_w8_ais_projection_reuses_authenticated_uid`'s `nodes` leg was already green and is
untouched.

No capability, endpoint, authority boundary, or storage surface was removed by this repair —
the assertions were asserting the wrong *copy*, not a missing *property*.

## 3. Change (test-only)

`assert 'X' in src` → `assert re.search(r"...", src)` where the pattern accepts **either**
quote form while still requiring the exact symbol/path and the exact quoting relationship.

- `_SPINE_KEY\s*=\s*['"]identity_spine['"]`
- `@router\.get\(\s*['"]/api/me/identity-spine['"]\s*\)`
- `load_user_profile_store\(\s*user\[['"]uid['"]\]\s*\)` (used in both files so the two files
  cannot drift apart again)
- `['"]ais_capability_portfolio['"]`, plus a compensating
  `assert '"ais_capability_portfolio"' not in ais` so the original negative-control intent is
  preserved rather than silently dropped.

`import re` was added to both modules. No other edit.

## 4. Proof

- **Targeted:** `tests/test_ais_w8_canonical_identity.py tests/test_identity_spine_w1.py`
  → `8 passed, 1 failed`. The single remaining failure is
  `test_node_entry_is_ais_signup_not_a_separate_diagnostic_route` (NodeEntry copy drift,
  node 41) — **explicitly out of this batch's scope**, see §5.
- **Controls:** 9 negative + 8 positive. All 9 negatives (uid param renamed, spine key
  renamed, route moved/deleted, portfolio key renamed, etc.) fail to match; all 8 positives
  (single- **and** double-quoted forms) match. The assertions retain teeth — they are not
  vacuous. `ALL CONTROLS PASS`.
- **Full suite** (both runs with `PYTHONPATH=<repo>/archive/legacy_python` and
  `--ignore` of the two pre-existing collection errors, which abort an unfiltered run):

| | failed | passed | skipped | collection errors |
|---|---|---|---|---|
| baseline `4164573` | 39 | 1018 | 13 | 2 |
| after | 36 | 1021 | 13 | 2 |

  Node-name delta is exactly the 3 repaired nodes. **No new failure, no new error, no
  fingerprint change other than the intended −3.**
- **Architecture fitness:** `tests/architecture` → **11 passed** (unchanged).
- **Protected budget:** `api/main.py` = 2519 lines (budget 2600, untouched);
  `python -m py_compile api/main.py` → OK. No boot code touched.
- **Diff:** 2 files, +8/−5, test-only. Zero product-code mutation.

## 5. Deliberate non-edits (accountability, not oversight)

- **Node 41 — `test_node_entry_is_ais_signup_not_a_separate_diagnostic_route`.**
  The `"Let's form your node."` copy is genuinely absent from `NodeEntry.tsx`, which now
  renders `See my shape →`. Repairing it means either restoring product copy or rewriting a
  product-flow assertion — a **product presentation decision**, not test hygiene. Deferred
  with a named reason rather than forced.
- **`/api/pulse/analyze` contradiction (nodes 1, 2).** `test_ais_w2_living_gate_grove_handoff.py`
  asserts presence; `test_ais_capability_profile_onboarding.py` asserts absence. Mutually
  unsatisfiable without a product/governance decision. Not touched.
- **`test_spiral_grove_registry.py` capability legs.** Classified `DRIFT`, not
  `STALE_ASSERTION`; the cycle-exception leg is arguably a genuine library ordering issue.
  Out of the SH-02 envelope.

## 6. Fingerprint handover

- Failing nodes now: **36** (was 39). The three repaired nodes are removed; nothing else moved.
- `SH-02` progress: 35 stale-assertion nodes at classification → batches 1 (sci-nexus),
  2 (solariun-consolidation) and 3 (identity-spine, this pass) complete.
- **Next bounded task:** continue `SH-02` on the remaining cleanly-provable stale-assertion
  families (`test_ais_w6_future_skills_challenge.py`, and the `test_steward_filter.py`
  `"transcended"` leg only if the classification's `SH-06` product judgement is resolved
  first). Do **not** fold in the `/api/pulse/analyze` contradiction or the `NodeEntry` copy.

## 7. Authority

Human-sovereign merge only. This branch does not touch `main`, does not widen the open
PR #129 (`gate-hygiene/baseline-ledger-correction-sg04-01`), and creates no second mutation
or authorization path.
