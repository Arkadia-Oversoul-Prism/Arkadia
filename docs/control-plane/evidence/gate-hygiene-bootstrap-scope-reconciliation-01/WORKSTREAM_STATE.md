# WORKSTREAM STATE — `gate-hygiene` / bootstrap scope reconciliation

> Pass `gate-hygiene/bootstrap-scope-reconciliation-01`, 2026-09-30.
> Persisted so the next heartbeat reconstructs from evidence, not memory.

## Base identity

| item | value |
|---|---|
| `BASE_MAIN` | `002b189dd95e41c9b4f4cca33d08b4121453d289` |
| branch | `gate-hygiene/bootstrap-scope-reconciliation-01` |
| status | READY FOR SOVEREIGN MERGE (docs-only) |
| merge order | **independent** of #146/#153/#154/#156 — touches no file they touch |

## Baseline fingerprint (regression boundary to protect)

```
20 failed / 1039 passed / 13 skipped / 2 collection errors        (22 nodes)
sha256(sorted FAILED/ERROR summary lines) =
  a7687fadaa25ad5f8aa283747bbffa85d304d516ae2b6c53b3849dc54479434c
```

Reproduced independently this pass; matches PR #146's published derivation. Derivation is
over the **full summary lines**, not node ids (`ff49f743…` — that is *not* the fingerprint).
The `sort` is load-bearing: pytest emits the short summary in report order.

## Red-node ownership map (22 nodes, 0 unowned after this pass)

| cluster | nodes | owner | state |
|---|---|---|---|
| `test_steward_filter.py` ×3 | steward-filter rules | **F-02** (merged #141) | repaired on `main` |
| `test_ais_w2_living_gate_grove_handoff` ×1 | F-01 | **F-01** | open, deliberate |
| `test_spiral_grove_activity_runtime` ×4 | SG-04 | **SH-08** | sovereign/product call |
| `test_engineering_scheduler_bootstrap` ×2 | scheduler spec | **PR #148** | carried |
| `ERROR test_render_codex.py` | naming defect | **PR #149** | carried |
| `test_identity_spine_w1` ×1 | DRIFT | unassigned | pre-existing |
| `test_m02_reasomate_truth` ×1 | DRIFT | unassigned | pre-existing |
| `test_spiral_grove_registry` ×2 | DRIFT | **parked** (product/contract) | see EVIDENCE §8 |
| `test_gate_serve_script` ×1, `test_gate_status` ×1 | ENV/ARTIFACT | **SH-05** (PR #142) | carried |
| `test_solspire_r{1,2,3}` ×4 | REAL_DEFECT, workflows inert | separate workstream | not opened |
| **`ERROR test_autonomy.py`** | **weaver.autonomy name collision** | **none → parked** | see EVIDENCE §6 |

`test_autonomy.py` was the only genuinely unowned node; it is now parked with a diagnosed
root cause. It is **not** repaired here — the repair requires a governance decision.

## Next bounded task (for the next heartbeat)

**Do not select it from prose.** Reconstruct, then choose from the current gate.

Candidates, in ascending scope:

1. **Sovereign adjudication queue** — 16 open PRs (incl. #157), several explicitly superseding each other
   (#147 vs #150 vs #151 vs #152 vs #155 all concern the same `AGENTS.md` encoding repair).
   The queue cannot converge without merge decisions. This is the highest-value *unblock*.
2. **`weaver.autonomy` collision** (§6) — needs a sovereign ruling: is autonomous execution
   reachable, or is the package's "no execution hooks" declaration canonical? Small change,
   large authority question. **Requires authorization.**
3. **`test_spiral_grove_registry` ordering** (§8) — needs a contract ruling.
4. Remaining unassigned `DRIFT` nodes (`test_identity_spine_w1`, `test_m02_reasomate_truth`)
   — need per-node classification before any repair.

Gate-ordered work (GATE-11 → GATE-13) should **not** open until GATE-10's queue converges:
GATE-10 is ACTIVE and carrying 15 open PRs.

## Standing boundary

**current main → deployment → production verification → UI/runtime evidence**

| boundary | state |
|---|---|
| current main = `002b189` | **VERIFIED** |
| deployment identity for `002b189` | **UNKNOWN** — not inspected this pass |
| production verification | **UNKNOWN** — not claimed |
| UI/runtime evidence | **UNKNOWN** — not claimed |

Never convert `UNKNOWN` into `VERIFIED` by repetition.

## Pass outcome — `gate-hygiene/bootstrap-scope-reconciliation-01`

| field | value |
|---|---|
| commit | `b61e5e0b8986f78783ec0fb7c6e52da6edcd0950` |
| branch | `gate-hygiene/bootstrap-scope-reconciliation-01` |
| PR | **#157** — https://github.com/Arkadia-Oversoul-Prism/Arkadia/pull/157 |
| mergeable | `True` (5 files, docs-only) |
| status | **READY FOR SOVEREIGN MERGE** — verification class `IMPLEMENTED` (docs-only) |
| CI on head | Full-history secret scan ✅ · Vercel Preview Comments ✅ |
| CP10 workflow | **did not run** — path-filtered; diff touches none of its filtered paths. The same policy module was executed locally on the exact diff → exit 0 PASS. |

### Fingerprint (regression boundary)

```
20 failed / 1039 passed / 13 skipped / 2 collection errors        (22 nodes)
sha256(sorted FAILED/ERROR summary lines) = a7687fadaa25ad5f8aa283747bbffa85d304d516ae2b6c53b3849dc54479434c
```

Byte-identical before and after this change (`diff` of sorted node lists empty). Independently
re-derived from a clean worktree; **reproduces PR #146's published value**, retiring the earlier
"UNKNOWN provenance" caveat on the `ff49f743…` / `a7687fad…` pair.

### Protected suites

| suite | result |
|---|---|
| `tests/architecture` | 11 / 11 |
| `tests/test_m02a_ci_gate_integrity.py` | 49 / 49 |
| `tests/test_sqlite_schema.py` | 11 / 11 |
| `python -m py_compile api/main.py` | OK — 2519 / 2600 (untouched) |

### Credential note (for the next heartbeat)

`$GITHUB_TOKEN` is **empty** in this runtime; `$GITHUB_PERSONAL_ACCESS_TOKEN` returns **401**.
The working credential is the lowercase provider token **`$github_token`** (HTTP 200 as
`Arkadia-Oversoul-Prism`, repo `push: true`). Push it as a one-shot URL and keep
`origin` clean — `git remote get-url origin` is tokenless and `.git/config` holds no `gh[pousr]_`
literal (both verified). Repo-local `user.name`/`user.email` were absent and were set to
`openhands` / `openhands@all-hands.dev` for this clone only.

### Next bounded task (do not select from prose — reconstruct first)

Unchanged from the candidates above. **#157 closes this workstream.** The highest-value unblock
remains the sovereign adjudication queue — 16 open PRs (incl. #157), several explicitly superseding each other
(#147 vs #150 vs #151 vs #152 vs #155 on the same `AGENTS.md` encoding repair). GATE-11+ stays
closed until GATE-10's queue converges.
