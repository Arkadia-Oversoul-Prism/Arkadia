# WORKSTREAM STATE — gate-hygiene open-PR queue map (Pass 5)

Workstream: `gate-hygiene/open-pr-queue-merge-order-map-01`
Active PR: **#219** (`gate-hygiene/open-pr-queue-merge-order-map-02`)
Base main: `162f574b05dd839540d803aadda7608342618a84`
Pass 5 head: this branch. Authority: no merge / no push to `main` / no force-push.

## Current state

- Live queue: **5 open PRs, #215–#219**, all on `main 162f574`, all open / non-draft.
  Heads re-read from the API this pass; **#219 moved** from `a83c538` (Pass 4) to
  `210d6c0a24d2d0ca4b6fe24fd2322e15ed469042`.
- Composability **re-proven from `main` on the live #219 tip**: `#215→#216→#217→#218→#219`
  is git-clean at every step; composed HEAD `b06399bc005527a8f58cf4ee88ed40299673ccf6`;
  tree `db958f62e8fd91aa45b5656b805a1848eebdb9f1`; alternate order → identical tree.
- Node-set delta (this clone): baseline 21 → composed 19; **fixed 2, newly-failing 0**.
  Baseline `4d84e7eb…`, composed `c9ffdb62…`. CP10 judge PASS on composed + every PR.
- `api/main.py` untouched; budget 2582 / 2600; `py_compile` OK.

## Correction recorded this pass

Pass 4 §1's clone-regime claims do **not** reproduce: `7d79f38` **is** resolvable
(`commit`); `requests` **2.34.2 is installed** and the run has **0** `ModuleNotFoundError`
and **1** error (`test_autonomy.py`); the clone has **7** `refs/remotes/pr/*`, not 5. Pass 4
also marked the composed set `c9ffdb6216c70314` "not reproduced" — it **is** this clone's
composed fingerprint, stable across the #219 head move. The 45-error regime is consistent
with a *bare / single-branch* clone (pinned revision + `origin/main` absent); that shape was
not observed here and is recorded, not resolved.

## Next bounded task (pinned)

**`gate-hygiene/stale-gate-fixture-retirement-01`** — retire the two residual `main`
failures that assert an archived surface:

- `tests/test_gate_status.py::test_gate_files_and_fetch_handling`
- `tests/test_gate_serve_script.py::test_root_index_redirect_and_script_exists`

Both assert a root `gate/` dir (`gate/index.html`, `gate/gate.js`, `gate/gate.css`) and a
root `index.html` redirect. `f6718b9` archived those files to
`archive/legacy_frontend/gate/`; neither path is tracked at root. Scope: those two test
files only. Test-only; **separate PR** — do not fold into this one.

## Resume condition

Next heartbeat reconstructs from `main`, the open PRs, and this file. Do not merge; a human
merges. Do not fold the pinned task into the queue-map PR.
