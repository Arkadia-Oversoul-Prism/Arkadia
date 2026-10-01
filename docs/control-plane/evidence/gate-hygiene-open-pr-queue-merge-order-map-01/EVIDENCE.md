# gate-hygiene — open-PR queue: file-overlap map, merge order, and two stale ledger nodes

Pass: `gate-hygiene/open-pr-queue-merge-order-map-01`
Date: 2026-10-01 (UTC)
Base main: `002b189dd95e41c9b4f4cca33d08b4121453d289` (merge of PR #141)
Authority: no merge, no push to `main`, no force-push. Human-only merge.

**Type:** bounded evidence pass. **No source, test, or governance change.** Mirrors the
established evidence-only pattern of
`docs/control-plane/evidence/open-pr-composability-99-100-101/EVIDENCE.md` and PR #155.

---

## 1. Why this pass exists

Sixteen PRs are open against `main` at `002b189`. A human sovereign merging them one at a
time has no single artifact that answers the three questions that must be answered *before* a
merge, not discovered during one:

1. **Which open PRs touch the same files?** (overlap — candidates for conflict)
2. **Do those overlaps actually conflict when merged?** (composability — a real merge, not a
   guess)
3. **In what order should the queue drain?** (merge order)

Separately, this pass reconciles the workstream ledger
(`docs/control-plane/evidence/gate-hygiene-baseline-stale-assertion-repair-identity-spine-03/WORKSTREAM_STATE.md`)
against live repository evidence and finds its *"next bounded task"* pointer stale.

## 2. Method — and a trap that invalidated the first attempt

**M0 — unshallow first.** The automation clone is **shallow** (`git rev-parse
--is-shallow-repository` → `true`, `git rev-list --count origin/main` → `1`). In a shallow
clone the merge-base of a PR head and `origin/main` is the graft boundary, **not** the true
fork point, so `git diff origin/main...prNN` (three-dot) and `git merge-base` return
**silently wrong** results — including *empty* file lists for PRs that do change files.

> Measured: before unshallowing, PR **#142** reported **zero** changed files and
> `merge-base main pr142` returned **empty**. After `git fetch --unshallow origin`
> (1414 commits on `main`), #142 reports its real 3 files and
> `merge-base(origin/main, pr142) = df7a99a0`.

Every overlap number and every merge result below was **re-derived after unshallowing**. A
future pass that skips M0 will produce a confidently wrong map. **Unshallow is a precondition
of this measurement, not an optimization.**

- **M1 — overlap map.** `git diff --name-only origin/main...prNN` for all 16 open PR heads,
  inverted into a file → PRs relation (post-unshallow).
- **M2 — real composability.** `git merge --no-ff --no-commit` each PR head onto a branch cut
  from `origin/main`, in order, aborting only on conflict. A true three-way merge against the
  accumulated result, not a dry run.
- **M3 — staleness probe.** For a ledger task naming a target test file, check whether the
  task's own commits are ancestors of `main` (`git merge-base --is-ancestor`), not whether a
  branch name still exists.

Reproduction:

```bash
cd <repo>
git fetch --unshallow origin            # M0 — mandatory
for p in $(seq 142 157); do git fetch origin pull/$p/head:pr$p -f -q; done
for p in $(seq 142 157); do echo "== $p =="; git diff --name-only origin/main...pr$p; done
```

## 3. Overlap map — the queue is almost entirely disjoint

Only **two** clusters of files are touched by more than one open PR:

| file | open PRs | note |
|---|---|---|
| `AGENTS.md` | **#143, #147, #150** | the only semantic conflict — see §5 |
| `api/main.py` | #153, #154 | overlap, **non-conflicting** — see §4 |

Eight further files are shared **only between #143 and #147**, and they are not an independent
overlap: **#147 is stacked on #143's branch** (`base =
gate-hygiene/gate2-production-parity-02`), so those files are inherited from #143, not
authored twice. #147's *effective* delta over its own base (`pr143...pr147`) is just two
files:

```
AGENTS.md
docs/control-plane/evidence/gate-hygiene-gate2-production-parity-02/AGENTS_ENCODING_REPAIR.md
```

All other 14 PRs are single-writer. The queue can therefore drain in any order except for the
`AGENTS.md` cluster.

## 4. Composability — measured, not assumed

Real `--no-ff` merges from `origin/main`, post-unshallow:

| sequence | result |
|---|---|
| **all 13 non-`AGENTS.md` PRs, then #150** — `157,156,155,150,151,152,153,154,142,144,145,146,148,149` | **clean at every step** |
| `150 → 151 → 152` | clean |
| `143 → 150` | **CONFLICT: `AGENTS.md`** |
| `150 → 143` | **CONFLICT: `AGENTS.md`** |

### Why `api/main.py` overlaps but does not conflict

`#153` and `#154` both edit `api/main.py` in disjoint regions ~450 lines apart:

- `#153` — `+2/-0` at `@@ -1250,0 +1251 @@` and `@@ -1256,0 +1258 @@` (`commune_resonance`)
- `#154` — `+10/-0` at `@@ -799,0 +800,10 @@` (`heartbeat`)

Git merges them in either order. **File-level overlap is not conflict; only hunk-level overlap
is.** `#153`/`#154` ordering is a free choice.

### Why `AGENTS.md` conflicts

`#143` and `#150` both rewrite the *same* corrupted region, so whichever merges second
conflicts — confirmed symmetrically in both orders above. This is the single genuine conflict
in the queue.

## 5. `AGENTS.md` is the only real conflict — and it is already adjudicated

**This pass does not re-adjudicate that question.** The verdict already exists, independently
derived, at
`docs/control-plane/evidence/gate-hygiene-agents-md-queue-adjudication-02/EVIDENCE.md`
(PR #155), corroborating PR #151's byte-oracle:

| candidate | verdict (per #155) |
|---|---|
| **#150** | **CORRECT** — faithful CP866 round-trip; recovers `main` to the established 12-codepoint alphabet |
| #143 | WRONG — double-encoded (28-codepoint alphabet, 26 outside the established set) |
| #147 | SUPERSEDED / **CONTRADICTED** — re-introduces the corruption its title claims to remove |
| #151 | adjudication evidence |
| #152 | history-free guard — **sound and merge-safe**, passes before *and* after #150 |

Independently re-checked here: `git diff origin/main...pr147 -- AGENTS.md` is `+116/-0` — it
**adds** 116 lines and removes **no** corrupted byte, consistent with #155's `CONTRADICTED`
classification. `#150` is `+79/-50` — it removes the corrupted region. #147 is also the
**only stacked PR** in the queue, so it cannot merge before #143's branch reaches `main`, and
#143 must not merge with its current `AGENTS.md`.

## 6. The ledger's "next bounded task" is stale — `SH-02b` is already on `main`

The ledger names `SH-02b` (`tests/test_prism_pass_c_surface_ownership.py`) as *"the next
bounded task"*. Measured:

```
python -m pytest tests/test_prism_pass_c_surface_ownership.py -q   ->  9 passed
git merge-base --is-ancestor 82ce2a83 origin/main                  ->  ANCESTOR (merged)
git merge-base --is-ancestor 157da8d1 origin/main                  ->  ANCESTOR (merged)
```

The `SH-02b` repair commits are already in `main`'s history:

```
157da8d1 gate-hygiene/SH-02b: correct two false claims in the surface-ownership repair
82ce2a83 SH-02b: repair stale surface-ownership assertions in test_prism_pass_c (6 nodes)
```

There is **no live `SH-02b` branch** — the repair merged and the branch was deleted. The
target test passes 9/9 on `main`. **`SH-02b` is done; the ledger's pointer to it is stale and
must not be executed.** (Method note: an earlier probe looked for a branch *name* and reported
"branch not an ancestor of main", which is the wrong test — the correct test is whether the
*commits* are ancestors. Branch deletion is not evidence of unmerged work.)

## 7. Two escalated nodes — classified, fingerprinted, **not edited**

The task framing for this pass pointed at `SH-07`/`SH-09` as candidate repairs. The ledger's
own closing rule forbids exactly that:

> Do **not** fold `SH-08` or `SH-09` into it — both are product decisions dressed as test
> repairs, which is exactly the scope creep `SH-02` is bounded against.

This pass **reproduces both classifications** and adds the exact fingerprint, but takes **no
edit**. They are escalated as product/architecture decisions.

### `SH-07` — `ArkanaCommune` shared-session key: real architectural gap

`arkanaSessionId` is **defined and never called** anywhere in the tree — its only occurrence
is its own definition:

```
web/public_prism/src/lib/arkanaSession.ts:42:export function arkanaSessionId(...)
```

(`grep -rn arkanaSessionId web/` → 1 hit, the declaration.) The shared-session intent is
genuinely unwired, not a stale string.

It is enforced by a **failing test that states the architectural requirement verbatim**:

```
tests/test_m02_reasomate_truth.py::test_oracle_runtime_uses_the_shared_session_key
E  AssertionError: the Arkana runtime must key its thread on the shared session id so
   ReasoMate and Oracle describe one longitudinal conversation
E  assert 'arkanaSessionId' in "import { apiFetch } from '../lib/apiClient'; ..."
```

The oracle is `assert "arkanaSessionId" in <ArkanaCommune source>` — i.e. the *component*
must consume the shared key. Satisfying it means wiring the Oracle runtime through
`arkanaSessionId`, which is an **architectural change**, not a test repair. **Escalated, not
edited.**

### `SH-09` — `NodeEntry.tsx` copy drift: product presentation call

Asserted symbols vs. measured counts in `web/public_prism/src/pages/NodeEntry.tsx`:

| assertion | count | reading |
|---|---|---|
| `"WELCOME TO ARKADIA"` | 1 | present |
| `"Let's form your node."` | 0 | **absent — copy drift** |
| `"Form my node"` | 0 | **absent — copy drift** |
| `"/api/me/ais-profile"` | 1 | present (route intent survives) |
| `"AIS_CAPABILITIES"` | 0 | **absent** |
| `"GROVE_DOMAINS"` | 0 | **absent** |

The route and behaviour intent survives; only presentation copy and the Spiral Grove
catalogue coupling drifted. Repointing the strings is a product decision — which is why the
ledger marks it `DRIFT`, not `SH-02`. The enforcing test states the intent:

```
tests/test_identity_spine_w1.py::test_node_entry_is_ais_signup_not_a_separate_diagnostic_route
E  assert "Let's form your node." in "import { apiFetch } from '../lib/apiClient'; ..."
```

Note `"WELCOME TO ARKADIA"` and `"/api/me/ais-profile"` **do** survive — the route intent is
intact; only the copy drifted. **Escalated, not edited.**

## 8. Merge-order recommendation (advisory — merge remains HUMAN)

Ordered so every step is clean and no PR is merged with wrong content.

**Wave 1 — independent, no shared writer (any order; measured clean as one sequence):**

| PR | note |
|---|---|
| #157 | bootstrap scope/success reconciliation (docs) |
| #156 | documented route contract + served-app pin |
| #155 | `AGENTS.md` queue adjudication (evidence) |
| #151 | byte-oracle adjudication (evidence) |
| #152 | history-free fingerprint guard — merge-safe before/after #150 |
| #153 | Oracle provenance — `api/main.py` ~1250 |
| #154 | `/health` projection — `api/main.py` ~799 (no conflict with #153) |
| #142 | gate/ artifact rows 47–48 |
| #144 | stop full suite creating canonical SolSpire store |
| #145 | attribute full-suite intermittency |
| #146 | bootstrap state reconciliation |
| #148 | scheduler bootstrap test-spec |
| #149 | `test_render_codex.py` collection error |

**Wave 2 — the `AGENTS.md` repair, single writer:**

| PR | note |
|---|---|
| **#150** | the correct repair. **After this, #143 conflicts at `AGENTS.md` by construction.** |

**Wave 3 — disposition (sovereign):**

| PR | recommended disposition |
|---|---|
| #147 | **do not merge as-is** — `CONTRADICTED`; re-introduces the corruption. Close or rewrite. |
| #143 | **do not merge `AGENTS.md`** — double-encoded. Its non-`AGENTS.md` Gate-2 parity content is a separate question. |

Wave 1 plus #150 was verified end-to-end as a single 14-step sequence (§4). Wave 3 is a
content decision, not an ordering one.

## 9. Scope and regression boundary

Evidence-only. This pass adds **two docs files**. It changes no code, no test, no `AGENTS.md` byte,
no governance file, and touches neither `api/main.py` nor `LAYER_MAP.py`. It therefore cannot
alter any suite's outcome.

- `python -m py_compile api/main.py` — **OK** (boot code untouched); `api/main.py` remains
  **2519 / 2600** lines.
- Architecture fitness — **11 passed** (the contract's `9/10` and the ledger's `10/10` are
  both stale; re-measured live).
- Full suite — **21 failed / 1038 passed / 13 skipped / 2 collection errors**. Both the
  contract's `804 passed / 54 failed / 12 skipped` and the ledger's `1008 / 20 / 13` are
  **stale**; this is the live fingerprint. Collection requires
  `PYTHONPATH=archive/legacy_python` and `--continue-on-collection-errors` (without the flag
  pytest aborts at the 2 known errors and reports nothing).
- The 2 collection errors are the documented pre-existing debt (`tests/test_autonomy.py`
  → `load_autonomy_config`; `tests/test_render_codex.py` → `arkana_drive_sync`).
- **Baseline failures are not attributed to this pass** — it adds two docs files and cannot
  move any count by construction.
- **Failing set (21)** — the failures cluster on the escalated nodes and on recent
  gate-hygiene work, i.e. this is *live, in-flight* work rather than silent rot:
  `test_steward_filter.py` (3), `test_spiral_grove_activity_runtime.py` (4),
  `test_spiral_grove_registry.py` (2), `test_solspire_r1_governance_convergence.py` (2),
  `test_engineering_scheduler_bootstrap.py` (2), and one each in
  `test_m02_reasomate_truth.py` (**`SH-07`**),
  `test_identity_spine_w1.py` (**`SH-09`**),
  `test_solspire_r2_github_mutation.py`, `test_solspire_r3_execution_runtime.py`,
  `test_gate_status.py`, `test_gate_serve_script.py`,
  `test_engineering_lab_agent_loop.py`, `test_ais_w2_living_gate_grove_handoff.py`.
  **Recording only — not fixing** (unrelated to this pass's bounded scope).
- CP10 mutation boundary — `docs/` is admitted by
  `scripts/cp10_mutation_boundary_policy.py`; `--judge` exits 0.

## 10. Remaining uncertainty

- The composability probes are **git-object** merges, not a build or a deployment. They make
  **no** production-parity claim and do not assert the merged tree is *green* — only
  *conflict-free*.
- `mergeable=True` was read from the GitHub API for all 16 PRs; `mergeStateStatus` was `null`
  at read time, so mergeability is reported from `mergeable` alone.
- Wave-1 ordering is presented as *safe*, not *required* — with disjoint writers the order is
  free.
- **Method dependency:** every number here assumes the clone was unshallowed first (§2). The
  results are reproducible only from a full-history clone.
