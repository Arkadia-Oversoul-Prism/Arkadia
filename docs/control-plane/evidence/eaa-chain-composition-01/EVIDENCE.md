# EAA / dispatch chain — composed candidate

**Baseline (verified base):** `main` at `7580bd8f0ca2925518d78775f9a323ff0df8bc66`
(the merge of PR #533, integration- and production-verified)
**Candidate branch:** `eaa/chain-composition-01`
**Authority:** candidate only. No merge, deployment, acceptance, or EAA/dispatch
advance is claimed.

## Source reconciliation

Every source PR was branched from `49809f45`, which is a **linear ancestor** of the
verified base (8 commits behind). Zero file overlap existed between those 8 main
commits and any source PR's changed-file set, and every source rebased with **no
conflict**.

| PR | head SHA | disposition | evidence |
|---|---|---|---|
| #502 | `ef82cb9e` | **included** (rebased `9dd776d4`) | `weaver/engineering_acceptance.py` + 14 focused tests pass; fail-closed evaluator does not originate authority |
| #503 | `37e89b4a` | **partially included** (rebased `9199495a`) | workflow included; an omitted filter entry repaired (below) |
| #508 | `071ecd8c` | **included** (rebased `a9037d13`) | stacked on #502; GET-only adapter, 9 tests pass, numeric reviewer allowlist, fail-closed protection read |
| #500 | `7640bbad` | **included** (rebased `98fa3bda`) | dispatch/inspection contract, 20 tests pass; no write-capable verb |
| #499 | `c1e7718b` | **included** (rebased `519bc8b8`) | `merged` removed from `TERMINAL_DONE`; gated statuses explicit; 44 tests pass |
| #496 | `967f30d9` | **included** (rebased `935cf651`) | docs reconciliation; see security note on `.gitleaks.toml` |

Dependency: **#508 is stacked on #502** (`base.ref = feat/engineering-acceptance-authority`,
`base.sha = ef82cb9e`). It was rebased with `--onto` the rebased #502, preserving that
ordering.

## Two candidate defects exposed by composition (repaired)

Both are real on their **own source branch**, not artifacts of composition.

1. **#503 — a gate not selected by a file it executes.** `eaa-base-baseline.yml`
   runs `tests/test_autonomy.py` but its `pull_request` filter named only itself, so
   a change to that file was never judged by the gate that runs it
   (`test_gate_filter_selection.py`, red on #503's own CI run `38310441067`).
   Repaired by adding the file to the filter — the repository's established repair
   for this class. **Negative control bites:** removing the entry reddens
   `test_no_workflow_omits_a_test_file_it_executes` (2 failed); restoring it returns
   50 passed.
2. **#499 — literal pins broken by a deliberate reclassification.** #499 moves
   `merged_acceptance_pending` from "unrecognized move status" to an explicit
   acceptance gate. Two pins in `tests/test_router_clean_stop_contract.py` still
   demanded the old literal (red on #499's own CI run `38297264096`). The protected
   **behavior is preserved** — measured directly: the unroutable frontier still
   yields `WEAVER_BLOCKED` / `HIGH` / `action_required=True` and is pushed to the
   sovereign. Only the pinned literal was updated.

No guard was weakened, no assertion removed, no policy relaxed.

## Verification

Full-suite figures and the node-set digest are recorded in `RECONCILIATION.json`
against the exact candidate SHA. The load-bearing regression claim is the
failing/error **node set**, which is identical to the verified base
(`sha256 c280ddc616fe4f4e9110bf4e6b6e538783a83d3764148d8a6d7ac45f6e8bc46b`, 9 nodes,
`comm -3` empty).

The `+65 passed` over the base is the six source PRs' new test files.

## Security note — #496 is not documentation-only

`#496` is described as a docs/portfolio reconciliation, but its diff also modifies
`.gitleaks.toml`, adding `^NovaNet/Solariun$` to the secret-scan allowlist. The
literal is prose in tracked docs already on `main` (5 files) and is not
credential-shaped, so the entry is defensible — but it is a **security-sensitive
surface** and should not ride in unremarked on a documentation change. Flagged for
the acceptance decision.

## Not claimed

- No merge, no push to `main`, no production change, no EAA/dispatch advance.
- The pre-existing failures and collection error on the base remain **unresolved**
  and are not repaired by this candidate.
