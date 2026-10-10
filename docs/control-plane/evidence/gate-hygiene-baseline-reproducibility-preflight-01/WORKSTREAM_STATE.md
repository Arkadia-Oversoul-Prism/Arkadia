# WORKSTREAM STATE — gate-hygiene/baseline-reproducibility-preflight-01

**Gate:** GATE-10 / gate-hygiene
**Branch:** `gate-hygiene/baseline-reproducibility-preflight-01`
**PR:** #387 (OPEN, MERGEABLE, CLEAN)
**Base main at this pass:** `f9ced6b6b974a6e19a8a19b4d1360b59b037a2c8`
**Head at this pass:** `c39477cce3dcac4b7d931a5eb18f312e76aa7e8f`
**Authority:** human merge required. Nothing here merged, nothing pushed to `main`.

---

## Objective (bounded)

Name the environment preconditions that silently change a full-suite failing/error node
set, so a baseline fingerprint is never derived in an environment that cannot describe the
canonical debt — and make the preflight that checks them actually execute in CI.

## State: IMPLEMENTED → VERIFIED (repository + CI evidence; not merged)

### Delivered

| artifact | role |
|---|---|
| `scripts/baseline_preflight.py` | read-only, stdlib-only probes; fails closed; never prints a token; `--json` |
| `tests/test_baseline_preflight.py` | 16 network-free tests incl. a shallow-clone negative control |
| `.github/workflows/baseline-preflight.yml` | executes the guard: `pull_request` (path-filtered), `push` to `main`, `workflow_dispatch`, `fetch-depth: 0` |
| `tests/test_baseline_preflight_ci_wiring.py` | wiring invariant over every workflow that runs the guard; inputs derived by AST |
| `EVIDENCE.md` (§1–6) | measurements, negative controls, regression boundary, authority boundary |

### Regression boundary (the load-bearing claim)

`main` `f9ced6b6` (clean detached worktree) vs branch, same command, same environment:

- failing/error node **set** byte-identical — sha256 `facc29a91e12fa3437362c6c4d40ac837393da7f4856c1bf018795d1032f87ed`, **16 nodes (15F/1E)** both sides
- outcomes `bfcfe592…` / ids `ed5e4714…` — identical both sides
- passed: `main` 1854 → branch 1870 (**+16** = the new guard suite's own nodes)
- architecture fitness **11 passed** both sides; `py_compile api/main.py` OK
- CP10 mutation-boundary judge PASS (RC 0) on every changed path
- `api/main.py` untouched

Counts alone are not the claim. The node **set** is.

### CI wiring is runtime-proven, not asserted

As introduced, `grep -rn baseline_preflight .github/workflows/` → **0**: the preflight held
only when a human invoked it (the "a guard no workflow executes is decoration" class).

At head `d4f07881`: run **`38001869735`**, `event=pull_request`, `conclusion=success`,
`headSha=d4f07881…`. At head `c39477cc` all **7** check-runs are `completed/success`
(`baseline-preflight`, `Full-history secret scan`, `native-arkadia-golden-workflow`,
`bundle-beta-evidence`, `beta-beta-01-english`, `beta-beta-02-hausa`,
`Vercel Preview Comments`).

Two negative controls keep the wiring test honest: removing the workflow fails
`test_a_workflow_executes_the_preflight_guard`; dropping `requirements.txt` from the filter
fails `test_guard_workflow_is_selected_by_every_input[baseline-preflight.yml]`. Both
restored → pass.

## Not done here (deliberately)

- **Fixture reconciliation (§8)** — not touched. 6 live nodes are owned by open PRs (#354
  plus unowned drift); re-pinning now would be immediately stale.
- **The 3 `test_m02a_ci_gate_integrity.py` failures** are the pre-existing CP10 `deploy/`
  allowlist omission, reproduced on `main` itself — classified, not fixed.
- **Gate 2 production parity** remains `BLOCKED` on Vercel Deployment Protection.
- `.bootstrap/01_STATE.md` is **not** edited by this pass: it is a `FINGERPRINT_DOCS` member
  asserted against the canonical fingerprint, and this workstream changes no fingerprint.

## Next bounded task

Unchanged: the four candidate workstreams in
`phase1-runtime-stabilization-01/EVIDENCE.md` §6 stand as separate bounded branches. The
nearest to this pass is baseline node-set reconciliation, which is blocked on PR #354.

## Authority boundary

Read-only preflight, its guard tests, and its CI wiring. No merge, no push to `main`, no
authority/mutation/identity path, no scope expansion. Human merge required.
