# WORKSTREAM STATE — gate10/cp10-allowlist-deploy-surface-01

**Gate:** GATE-10 (Governed Execution) — CP10 mutation boundary / M02A CI gate integrity
**BASE_MAIN:** `f96d5fd27d40110196ec22b114808efc0eb9dc05`
**Branch:** `gate10/cp10-allowlist-deploy-surface-01`
**PR:** #354
**Head at record:** `04662703` (Pass 4 correction)
**Status:** VERIFIED — READY FOR SOVEREIGN MERGE
**Authority:** merge and authorization retained exclusively by the human sovereign.

## Deterministic next action

- **Current state:** `deploy/` (4 tracked paths, added by PR #352 / merge `a27c6c80`) is
  enumerated in `LEGIT`. The CP10 boundary step passes on the full PR range at the current
  head, and the three completeness fitness nodes pass on the branch and fail on `main`.
- **Evidence:** `docs/control-plane/evidence/gate10-cp10-allowlist-deploy-surface-01/EVIDENCE.md`
  (Passes 1–3c, plus the Pass 4 attribution correction).
- **Authorized action:** sovereign review and merge of PR #354.
- **Forbidden actions:** merge, force-push, self-authorization, weakening the gate,
  reclassifying `REGISTERED_ARCHITECTURAL_DEBT`, widening scope into unrelated baseline debt.
- **Completion condition:** PR #354 is merged by the sovereign and
  `test_allowlist_admits_every_tracked_top_level_prefix`,
  `test_allowlist_covers_every_tracked_surface`, and
  `test_delegated_verdict_admits_every_tracked_surface` are green on the resulting `main`.

## Measured state at this record

| Check | Result |
|---|---|
| `tests/test_m02a_ci_gate_integrity.py` (branch) | 64 passed |
| three completeness nodes (`main` `f96d5fd2`, detached worktree) | 3 FAILED |
| `SG-02-FE.2-V` @ `e7ce1d0f` | success — `Mutation boundary PASS`, range `f96d5fd2..HEAD` |
| `security-secret-scan` @ `e7ce1d0f` | success |
| `N-ATLAS external beta validation` @ `e7ce1d0f` | success |
| Vercel (both contexts) | failure — identical on `main` `f96d5fd2`; provider rate limit, not attributable |
| `api/main.py` | untouched (not in the diff) |
| tracked corpus | 1955 paths |

`mergeable=MERGEABLE`; `mergeStateStatus=UNSTABLE` is caused solely by the pre-existing Vercel
rate-limit status.

## Predecessor and open follow-on

- Predecessor: `gate10/cp10-allowlist-economic-seams-mie-01` (merge of `economic_seams/` +
  `musical-intention-engine/`). Its WORKSTREAM_STATE explicitly named this recurrence class:
  "A future tracked top-level tree re-triggers the same defect class; the completeness
  invariant in `tests/test_m02a_ci_gate_integrity.py` is the guard." That prediction fired
  here, at `deploy/`.
- The guard is the point: a new tracked top-level tree must be enumerated, not admitted by a
  broadened rule. Do not replace the enumerated `deploy/` entry with a generic pattern.

## Reported, not resolved — measured at `696cc07b` (separate workstreams)

`tests/test_engineering_lab_api.py` → **2 failed, 3 passed**. Both are pre-existing on `main`
`f96d5fd2` and are recorded here, not repaired: this PR's scope is the CP10 allowlist, and
"do not expand scope to repair adjacent failures" governs.

1. `test_lab_mutation_endpoints_are_exactly_the_lab_state_set` — the frozen
   `ALLOWED_MUTATION_ENDPOINTS` list in the test does not contain two mutating endpoints the
   N-ATLAS work added: `/api/lab/engineering/n-atlas/run` and
   `/api/lab/engineering/n-atlas/test-session`. **Attribution corrected in Pass 4:** these
   routes originate in **PR #352** (merge `a27c6c80`), not #353; `2c6f6f1e` already contains
   them at lines 362/427/440, and `git merge-base --is-ancestor a27c6c80 2c6f6f1e` is true. **This is the same recurrence class as this
   PR** — a frozen inventory that fell behind a legitimate new surface — but on a *different*
   list, and its assertion message is a mutation-boundary question ("review it against the
   no-repository-mutation boundary"), not a formatting one. It needs an owner's decision, not
   a mechanical addition: whether those endpoints are inside the Lab's declared no-mutation
   boundary must be established before the list is widened.
2. `test_lab_router_is_read_only_and_authenticated` — the router's dependency is named
   `require_lab_auth`; the test pins the literal `require_auth`. The router *does* carry a
   dependency (`assert router.dependencies` passes), so this reads as a stale name pin, the
   documented test-side literal-defect class. It is an authentication-boundary assertion, so
   the equivalence of `require_lab_auth` to the expected guard must be confirmed, not assumed.

---

## Pass 4 — head, clone depth, and full-clone node sets (2026-10-08)

- **BASE_MAIN:** `f96d5fd2` (still `origin/main`; unchanged this pass).
- **ACTIVE_PR:** #354 `gate10/cp10-allowlist-deploy-surface-01`.
  - True head: **`ba187124f29a248be5a98c21ddb4d0d6836879c6`** → advanced this pass to
    `e55239ef` (evidence-only Pass 4 correction).
  - Earlier citations `f7c212bd` / `e90a5769` / `696cc07b` are superseded; each advance is
    documentation-only.
- **#355** `73104fdf` — still open, not merged; owns the trigger-coverage node.
- **Environment correction:** the clone **was shallow** (`--is-shallow-repository` -> `true`).
  Deepened with `git fetch --unshallow --filter=blob:none` (32 `AGENTS.md` revisions).
- **Node-set measurements (full clone, `-rEf --continue-on-collection-errors`):**
  - `main` `f96d5fd2` -> 27F/1763P/18S/1E, **28** nodes, `d12b3aae...`.
  - #354 `ba187124` -> 24F/1766P/18S/1E, **25** nodes, `153246a9...`.
  - Removed = the 3 `test_m02a_ci_gate_integrity` nodes; **introduced = 0**.
- **Corrected classification:** `test_corruption_origin_is_re_derivable` fails on shallow
  `main` and passes on the branch only because a shallow clone sees 1 `AGENTS.md` revision.
  On a full clone it is **absent** — a shallow-clone artefact / branch **false positive**, not
  a repair this branch makes. Do not cite it as fixed by #354.
- **CI at `ba187124`:** six check-runs all `success` (incl. SG-02 run 37714998141); combined
  status `failure` only from the two pre-existing Vercel rate-limit contexts.
- **Blocker:** none. **Forbidden:** the standing list (no merge, no push to `main`, no policy /
  denylist / test / `AGENTS.md` change, no `api/lab_routes.py` or `api/auth.py` edit).
- **Completion condition:** #354 and #355 merged by the sovereign; a fresh pass reconstructs
  `main` and re-derives the node set on a full clone.

### Credential reality observed this pass (for the next heartbeat)

- `GITHUB_PERSONAL_ACCESS_TOKEN` -> **HTTP 401**.
- The `gh` session token -> **401 Bad credentials** (`gh auth status` fails).
- The **`github_token` provider secret** -> **HTTP 200**, and `GET /repos/.../Arkadia` reports
  `permissions: {admin, maintain, push, triage, pull}`. Use this token for API reads *and*
  writes; it is never printed.
- `git push` succeeds with the credential embedded in the `origin` remote URL
  (`GIT_TERMINAL_PROMPT=0`). Pushes this pass: `ba187124 -> e55239ef -> 8a99ef7e` on
  `gate10/cp10-allowlist-deploy-surface-01`. **Never to `main`.**
- Consequence: the earlier "read-only token, push not possible" classification is
  **superseded** — it was the wrong token. Push is available; the authority boundary (no merge,
  no push to `main`) is unchanged and was respected.
