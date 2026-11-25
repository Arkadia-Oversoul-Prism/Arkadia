# Gate hygiene — served-asset identity (01)

- **Contract:** `ARK-OPS-CONTINUOUS-001` rev `2026-11-22`.
- **Authority:** `MERGE_AUTHORITY := NONE`, `DEPLOY_AUTHORITY := NONE`. No merge, no push to
  `main`, no deployment, no acceptance claimed. GOV-03 remains the execution rule.
- **Branch:** `gate-hygiene/served-asset-identity-01`
- **Observed:** 2026-11-25T14:06Z onward.

---

## 1. Reconstructed state (live, before any change)

| fact | measured value | how |
|---|---|---|
| canonical `main` | `fd0a4fdc081064b2074aab9e17b4c7841736dd9f` | `GET /commits/main`; local `HEAD` agrees |
| production `/api/version` | `source_revision` = `fd0a4fdc…`, `revision_source` = `RENDER_GIT_COMMIT`, `revision_conflict` = `false` | one command |
| production `/health` | `200` | one command |
| open PRs | **57**, 56 draft, 1 non-draft (#724), all `base: main`, **0** obsolete | `GET /pulls`; heads fetched with `+refs/pull/*/head` and tested with `git merge-base --is-ancestor` and `git diff --stat origin/main...<head>` |
| `api/main.py` | 2597 lines (budget 2600) | `wc -l` |
| check-runs on `fd0a4fdc` | 7 `success`, 2 `skipped`, **0** `failure` | `commits/<sha>/check-runs` |
| branch protection / rulesets | none / 0 | REST (recorded for M5/M6 completeness; confers no authority) |

An obsolete-PR audit over all 57 heads returned **0**: no open head is an ancestor of `main` and
every head carries a non-empty diff. The queue is real work awaiting human review, not stale
state to retire.

## 2. The gap this cycle closes

Revision identity and served-artifact identity are different claims. `/api/version` binds a
deployment to a source commit; it says nothing about the bytes the origin hands a browser. The
repository records the first and had **no reproducible record of the second**, so the strongest
available production claim could only be made by hand, once, in a conversation — the class this
contract exists to eliminate ("an agent must be able to resume without relying on conversational
memory").

`scripts/production_runtime_probe.py` already captured the root document's status and a 160-byte
preview, which is enough to see that a route resolves and not enough to identify the artifact.

## 3. The change

Four files, additive; no authorization, routing, product behaviour or `api/main.py` touched.

| file | change |
|---|---|
| `scripts/served_asset_manifest.py` | new, stdlib-only. `declared_assets(html)` extracts the `/assets/` build output a document declares (de-duplicated, document order, external/runtime/icon references excluded); `observe(origin)` fetches `/` as a browser navigation and records `status`, `bytes`, `sha256`, `content_type` for the document and every declared asset. Records facts only. |
| `scripts/production_runtime_probe.py` | imports it, adds a `served_assets` block to the artifact, and treats a capture failure as a recorded limitation rather than a silent empty block. |
| `.github/workflows/canonical-render-runtime-probe.yml` | both `paths` filters name the new module and its test; the job runs the detector before the probe. |
| `tests/test_served_asset_manifest.py` | 17 tests over the real extraction path. |

The manifest deliberately makes **no** parity judgement, and the code says so in a recorded
`note`: build output is environment-dependent, so a hash difference is not by itself divergence
and a match is not acceptance. The tool answers "which bytes did the origin serve", not "is this
correct".

## 4. Verification

### 4.1 Served-artifact identity at `fd0a4fdc` — measured, and now reproducible

Local build of the tracked tree at `fd0a4fdc`:

```console
$ cd web/arkadia_console
$ corepack pnpm install --frozen-lockfile     # exit 0
$ corepack pnpm build                         # exit 0
  tsc --noEmit && vite build — 170 modules transformed
  dist/assets/index-BJojPKi_.css            91.92 kB
  dist/assets/vendor-react-nf7bT_Uh.js     140.87 kB
  dist/assets/vendor-firebase-DNJjg0gV.js  167.59 kB
  dist/assets/index-CYGHeCpJ.js            425.15 kB
```

Every asset the origin serves is **sha256-identical** to that build:

| asset | bytes | sha256 (local = served) |
|---|---|---|
| `/assets/index-CYGHeCpJ.js` | 426232 | `63a28f23bbb433f995632eecb3fc0995cceebb205bf0531de89cf572aba5a4e5` |
| `/assets/vendor-react-nf7bT_Uh.js` | 140868 | `4c505e7d37efcf10d26942ffdcfce1e58e40408a5738b04ba7889e37fe173e5d` |
| `/assets/vendor-firebase-DNJjg0gV.js` | 167589 | `c554f70d81052613dfd2a45de119fa2b0a1f588a023afa69c0a164487d3f9a6d` |
| `/assets/index-BJojPKi_.css` | 91922 | `4948b2fa145b04cc10591e61f8a486e097523fab9dd28015081f9f54053f1e37` |

The served document (1256 B, `sha256 444785c2fbb5b8b85c60eafeacf76b9e85acb0b37ef67bc5d30159570f250985`)
declares exactly those four assets. So for this revision, source ↔ deployment ↔ **served artifact**
are all consistent. That is an artifact observation, not an acceptance: no route behaviour, no
authorization boundary and no product correctness is claimed by it.

### 4.2 The console is buildable and its own suite is green at this revision

```console
$ corepack pnpm exec vitest run
Test Files  8 passed (8)
     Tests  61 passed (61)
```

### 4.3 The new guard, and its control

```console
$ pytest tests/test_served_asset_manifest.py -q
17 passed
```

Live negative control — the behaviour disabled **at its definition** (`declared_assets` returns
`[]`), then restored byte-identically:

```console
$ pytest tests/test_served_asset_manifest.py -q
4 failed, 13 passed        # the four content assertions redden
$ # restore
17 passed
```

The "a document with no build output declares nothing" control keeps passing under the disabled
extractor, which is correct: it asserts absence. A control that reddened on both, or on neither,
would be measuring the wrong thing.

### 4.4 The probe emits the block, from the live origin

```console
$ python scripts/production_runtime_probe.py     # exit 0, read-only GETs only
artifacts/…/production-route-inventory.json -> served_assets
  document  200 1256 B  sha256 444785c2…
  assets    4 entered, 4 × 200, hashes equal to §4.1
```

### 4.5 No regression, by node identity

Full suite at `fd0a4fdc`, this sandbox, **without** `web/arkadia_console/node_modules`:

```console
$ PYTHONPATH=$PWD/archive/legacy_python python -m pytest tests/ -q -rEf \
    --continue-on-collection-errors
22 failed, 4251 passed, 22 skipped, 1 error in 287.93s
```

**23** failing/error nodes, each already classified and owned: 1 sovereign-reserved (CE-01
`weaver.autonomy`), 1 sovereign-reserved (FINDING F-01 persistence boundary), 10 environment-only
(`test_mission_lifecycle_adapter_contract.py`, needs `web/arkadia_console/node_modules/typescript`),
and 11 repaired by open PRs #700 (2), #690 (2), #693 (2), #691 (1), #698 (1), #683 (2), #725 (1).
**No unowned, non-reserved defect is in the failing set.**

The environment split is verified, not inferred: after `corepack pnpm install` created
`web/arkadia_console/node_modules/typescript`, `pytest tests/test_mission_lifecycle_adapter_contract.py -q`
reports **10 passed**. The residual is therefore **13** nodes, all owned or reserved.

Gate wiring and architecture, on this branch:

```console
$ pytest tests/test_ci_gate_trigger_coverage.py tests/test_gate_filter_selection.py \
    tests/test_m02a_ci_gate_integrity.py tests/test_ci_suite_collection_continuation.py \
    tests/test_workflow_injection_boundary.py tests/architecture -q
391 passed

$ git diff --name-only origin/main | python scripts/cp10_mutation_boundary_policy.py --judge
Mutation boundary PASS   (exit 0)
```

## 5. One production observation, owned elsewhere

`/api/codex/github-tree` returns **502** on the canonical origin:

```json
{"error":"Client error '401 Unauthorized' for url 'https://api.github.com/repos/…/git/trees/main?recursive=1'"}
```

Pinned rather than inferred: an **anonymous** request to that same GitHub URL returns `200`, so the
tree is publicly readable and the deployment's configured `GITHUB_PERSONAL_ACCESS_TOKEN` is what is
being refused. Two open PRs already own the two halves of the repair — #701 makes the corpus read
fall back to an anonymous request when the credential is refused and reports `authenticated` from
acceptance rather than from presence; #729 stops the handler echoing the upstream exception text.
Rotating the credential is provider configuration, reserved to the operator.

The remaining anonymous probe results over 101 parameterless `GET` routes are 37 × `200`,
56 × `401`, 3 × `403`, 4 × `422` (each a correct missing-query-parameter validation), and that one
`502`. No other failing route was observed.

## 6. Limitations and non-claims

- **Read-only.** The probe issues `GET` only; no mutation verb was invoked against the origin, and
  the anonymous `GET`s are the same reads the probe already performed.
- **The manifest is not a monitoring verdict.** It is a capture. Nothing in this change makes a
  build-hash mismatch or a 5xx route fail a gate, because both would be manufactured-red signals
  before the owner PRs land — and because a hash difference is legitimately possible.
- **Only `/` is captured.** Chunk names are discovered from the document the origin serves, so a
  lazy-loaded chunk that the entry document does not declare is not in the manifest.
- `web/arkadia_console/dist/` and `artifacts/canonical-render-runtime/` are generated and untracked;
  neither is staged here.
- Production parity in §4.1 is a served-artifact observation. It is **not** deployment acceptance,
  and it says nothing about route correctness.

## 7. Next-action block

**Current state.** `main` = `fd0a4fdc…`; production revision identical and its served artifact
sha256-identical to a local build of the same revision; CI on `main` green (7 success, 2 skipped);
console builds and 61 vitest tests pass; full-suite residual 13 nodes, all owned or reserved; 57
open PRs, 0 obsolete. This branch adds one stdlib-only module, 12 lines in the probe, its workflow
wiring, 17 tests and this record.

**Blockers.** (a) Merge execution is human-only (GOV-03); 57 PRs await human review. (b) The
anonymous GitHub push webhook, the CE-01 `weaver.autonomy` collision and FINDING F-01 are reserved
to the sovereign. (c) The deployed GitHub credential is refused; rotating it is operator
configuration.

**Authorized next action.** A human reviews this branch together with the queue. A later cycle may
re-capture the manifest after a deployment and compare it against a build of the revision the
deployment reports.

**Forbidden.** Merging; pushing to `main`; force-pushing; deploying; adding an authorization guard
to `/api/webhook/github`; turning the manifest into a pass/fail gate; weakening a guard to
manufacture green.

**Completion condition.** This cycle is complete when the manifest helper, its probe wiring, its
guard and this evidence are reviewable on the branch, with `main` unmodified and no merge,
deployment or acceptance claimed.
