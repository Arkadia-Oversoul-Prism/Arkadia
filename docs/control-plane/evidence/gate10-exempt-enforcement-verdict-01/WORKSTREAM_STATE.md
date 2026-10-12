# WORKSTREAM STATE — gate10/exempt-enforcement-verdict-01

Persisted so the next heartbeat reconstructs from evidence, not memory.

## Current state

| Field | Value |
|---|---|
| Workstream | `gate10/cp10-broad-suite-execution-coverage` (decoration class) |
| Branch | `gate10/exempt-enforcement-verdict-01` |
| Base main | `6109c72ab9eedc2593d2cc6c50ebd01596c80072`; **`main` moved to `26521e24` mid-pass** and both sides were re-measured there |
| Head | `1af68c2880364f7ac3815b199adf665de784d455` |
| PR | #483 (open, MERGEABLE, CLEAN, 10/10 checks success at head `1af68c28`) |
| Result | **IMPLEMENTED** — Detectors 3 and 4 + controls green; corpus clean, so no repair |
| Baseline debt | full suite 155 failing/error nodes at `6109c72` **and** at `26521e24` — pre-existing, unchanged |

## Evidence

- Guard: **30 passed** (21 after pass 1, 13 on `main`). Focused guards + architecture:
  **265 passed**, architecture **11 passed**.
- Regression by node identity: failing/error set sha256
  `d0541c6c1303f03b242b69d206beeb68b3a9becb5f25477d14fb16ba19823f26` (155 nodes) on `main`
  `6109c72`, on the branch, and **re-measured unchanged** on `main` `26521e24` and on the
  composed tree (`comm -3` empty in every pairing). `+17 passed` == the guard's collect delta
  (13 → 30), measured with `--collect-only`.
- CI at head `1af68c28`: **10/10 checks success**, including the dedicated gate
  `verdict-step-integrity` (run `38240697907`, `event=pull_request`, `head_sha` == head).
- Live negative controls on the real `sg-02-fe-2-v.yml`, in memory only, restored byte-identically
  (sha256 `f1423a5087cc14dc00e7e63182daaa1a0a40b30b1ec9d15811dd1d88d06cbcd0`):
  `continue-on-error: true` → 2F (pass 1); `shell: bash {0}` → 2F; `shell: bash --noprofile {0}`
  → 2F (the precision control).
- `python -m py_compile api/main.py` OK; `api/main.py` = 2505 lines (budget 2600). CP10 judge
  on the changed paths and on the composed diff: PASS, exit 0.

## Blockers

None. No 403/401 encountered — `gh` credential helper configured
(`git config credential.helper '!gh auth git-credential'`, `GIT_TERMINAL_PROMPT=0`).

## Authorized action (this pass, completed)

Extend the pure-source verdict-step-integrity guard with Detector 4 (abortless shell) plus its
controls and inventory — the follow-on pass 1 recorded as *proposed, not authorized*. Composed
into the same branch and PR #483 because it touches the same single guard file; a separate PR
would conflict on that file. **No merge.**

## Forbidden actions

Merge; push to `main`; force-push; mutate `.github/workflows/**` in this PR; repair pre-existing
full-suite debt; edit `api/main.py`; edit `AGENTS.md` (PR #482 owns it); add a second authority
or mutation path.

## Next bounded task (proposed — NOT authorized)

No further defect in this class is known to be open. Two adjacent, separately-bounded items are
recorded in `docs/control-plane/evidence/gate10-ci-coverage-reconnaissance-01/RECONNAISSANCE.md`
and remain **proposed, not executed**:

- **Defect A** — `sg-02-fe-2-v.yml`'s CP10-B step executes zero tests (the session aborts at the
  collection error); the one-token repair is `--continue-on-collection-errors`. It mutates
  `.github/workflows/**`, so it needs explicit sovereign authorization.
- The 155-node pre-existing full-suite debt, which is its own workstream.

## Exact completion condition

PR #483 merged by the sovereign, and the next heartbeat re-derives `main`, the node set, and the
gate state from live evidence rather than from this file.

## Authority boundary

No merge, deployment, or acceptance claimed. Human merge authority is final.
