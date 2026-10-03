# WORKSTREAM STATE — `gate-hygiene/pr-217-221-lineage-equivalence-01`

Pass: `gate-hygiene/pr-217-221-lineage-equivalence-01`
Date: 2026-10-03 (UTC)
Base main: `162f574b05dd839540d803aadda7608342618a84`
Status: **IMPLEMENTED** (evidence complete; no code/test change; sovereign review only)
Branch: `gate-hygiene/pr-217-221-lineage-equivalence-01`

## What this pass did

Bounded evidence pass. Adds **two** files (both under
`docs/control-plane/evidence/gate-hygiene-pr-217-221-lineage-equivalence-01/`). Decides the
open merge-preparation question: **is `#221` additive to the `#215–#219` cluster, or an
alternative revision of `#217`?** Answer: **lineage-equivalent — alternative, not additive.**
No source, test, `AGENTS.md`, or governance byte changed.

## Current state (derived from live evidence, not prose)

| item | value |
|---|---|
| `main` | `162f574b05dd839540d803aadda7608342618a84` (merge of #214) |
| open PRs | **#215–#222** (see §Live queue) |
| architecture suite | 11/11 (per repo ledger; not re-run this pass) |
| CP10 mutation boundary | `docs/` root is enumerated in `LEGIT` — `--judge` clean for added paths |
| clone | non-shallow, 1604 commits; `CORRUPTION_COMMIT`/`ORACLE_REV` present; `7d79f38` **absent** |
| full suite (plain `main`) | **20F / 1E = 21 nodes** (recorded fixture says 20 — see §Side finding) |

## Live queue (reconstructed 2026-10-03, `gh pr list --state open`)

`#215 #216 #217 #218 #219` (non-draft, MERGEABLE) = composable cluster.
`#220` draft **HOLD** (SH-05 sovereign ruling). `#221` draft (offshoot). `#222` non-draft
`test-hygiene` offshoot.

## Findings

1. **`#217` and `#221` are lineage-equivalent.** Both substitute `_rev("AGENTS.md",
   "origin/main")` → `_rev("AGENTS.md", CORRUPTION_COMMIT)` in the same function
   (`test_exit_code_does_not_call_a_divergent_clean_file_verified`). `#221` also contains
   `#218`; `#217` does not. Merged over `main`, the trees `[215,216,217,218,219]` and
   `[215,216,218,221]` produce **identical** fingerprints `c9ffdb62…/2c92cb38…` (19 nodes).
2. **The cluster is order-insensitive by hunk disjointness.** `#215`/`#216`/`#217`/`#218`
   auto-merge in `tests/test_agents_md_encoding_adjudication.py`; `#219` auto-merges
   `AGENTS.md`. Measured clean at every step.
3. **`#221`'s characterization of itself is slightly off.** It is not "closing a #218 gap";
   it is `#218 ∪ #217` on the adjudication file. Corrected by measurement in §3 of the
   evidence.
4. **Zero new failures** in every composed tree; cluster moves `main` 21 → 19 nodes, `#222`
   moves the composed tree 19 → 18.
5. **Side finding (recorded, not fixed):** the recorded baseline fixture
   (`tests/fixtures/baseline_node_set.txt`, 20 nodes) does not reproduce on plain `main` in a
   clone lacking `7d79f38` — the shadow-oracle node fails rather than skips, giving 21. This
   is **#215's** subject; not repaired here.

## Disposition (recommendation; sovereign call)

Merge **`#217`** with the cluster and **close `#221`** as a superseded alternative — or, under
a separate authorized cluster, merge `[215,216,218,221]` (which subsumes `#217`). Never merge
`#217` **and** `#221`: they conflict at one hunk and are mutually redundant. `#221` is a draft
offshoot off `#219`'s ancestor, so the recomposed-cluster member is `#217`.

## Baseline fingerprint

- plain `main` `162f574`: 21 nodes, `a59453b8…` / `9a35c812…` (canonical
  `scripts/baseline_fingerprint.py`).
- recorded fixture `tests/fixtures/baseline_node_set.txt`: 20 nodes, `a578a766…` /
  `8036fc06…` (does not reproduce here; see finding 5).
- composed cluster: 19 nodes, `c9ffdb62…` / `2c92cb38…`.
- composed cluster + `#222`: 18 nodes, `4e189cac…` / `eae79aac…`.

## Next bounded task

After the cluster merges: re-derive the `main` baseline fingerprint (the recorded fixture will
need `#215`'s depth-stability change to reproduce) and confirm `#222`'s merge-readiness. If
`#221` is chosen over `#217`, re-run the composition map against the new `main` — do not assume
the equivalence survives a rebase.
