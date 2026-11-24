# ARK-OPS-CONTINUOUS-001 — cycle 08: orientation documents named an archived frontend

**Measured:** 2026-11-24, canonical `main` = `bb19aabda34d59594615b0279a45e9cbd3d8204d`.
**Authority:** none claimed. No merge, no deployment, no acceptance. Merge execution is
human-only under GOV-03. `api/main.py` untouched.

## 1. State reconstructed before acting

| item | measured |
|---|---|
| canonical `main` | `bb19aabd…` (local clone `is-shallow-repository` = `false`) |
| production `/api/version` | `source_revision` = `bb19aabd…`, `revision_conflict: false` — revision parity **VERIFIED** |
| open PRs | **38**, every one a draft, every one `base: main`, `MERGEABLE`, **0** obsolete |
| prior ledger | PR #705 carries cycles 01–07; cycle 05's next action was "human review of the queue" |

Production parity here is revision identity only. It is **not** product acceptance, and it
does not claim that a revision has been functionally verified.

## 2. The defect

`web/public_prism/` was archived into `archive/frontend/arkadia-prism/` by `c081d200`
(2026-10-11). `ls web/` returns exactly `arkadia_console` and `console`. The executable
source agrees on the active shell: `Dockerfile:22` copies `web/arkadia_console/`,
`api/frontend_routes.py:50` serves `web/arkadia_console/dist`, and its own header says
"There is ONE application shell: the Arkadia Console in ``web/arkadia_console``".

Three tracked documents still told a reader otherwise:

| document | line | claim | why it is a currency claim |
|---|---|---|---|
| `REPOSITORY_SNAPSHOT.md` | Layer 5 block | `web/public_prism/    React/Vite SPA` | the file says "The agent reads this instead of crawling the repository tree" |
| `REPOSITORY_SNAPSHOT.md` | Runtime Dependencies | `Node.js: web/public_prism/package.json` | same |
| `replit.md` | service table | `cd web/public_prism && npm run dev` | a **run instruction** for a directory that does not exist |
| `architecture/ATLAS.md` | MAP 01 row | `web/public_prism/` … 🟢 **LIVE** | asserts liveness of an absent tree |

## 3. Why no gate reported it

Cycles 06 (#714) and 07 (#715) closed this class for `README.md` and `PROJECT_INDEX.md`.
Two distinct escape routes remained, and one of them was **inside** #715's own domain:

1. **A table row is not a fenced block.** #715's extractor read fenced code blocks only.
   `replit.md` carries no generation marker, so it **was** enrolled in the guard's derived
   domain — `--collect-only` on the base guard yields
   `…test_a_live_root_map_declares_only_present_web_surfaces[replit.md]` — and the node
   **passed** while the document told a reader to `cd` into an absent directory. This is a
   measured blind spot in an executing guard, not merely an unjudged document.
2. **A generation marker exempted an instruction.** `REPOSITORY_SNAPSHOT.md` carries
   `Last generated:`, so #715 excluded it as a point-in-time record. But the same header
   tells an agent to rely on it *instead of* reading the tree, which makes it an
   instruction rather than a record.
3. `architecture/*.md` was outside the derived domain entirely, so `ATLAS.md` was never read.

## 4. The change

Docs (three files, no behavioural code):

* `REPOSITORY_SNAPSHOT.md` — Layer 5 now names `web/arkadia_console/` (the one application
  shell) and `web/console/` (retired operator console, capabilities migrated); the Node
  runtime line points at `web/arkadia_console/package.json`. A dated correction line
  records what was corrected and at which revision, so the 2026-07-25 generation date is
  not silently overwritten.
* `replit.md` — the service table names the console and its real dev command
  (`cd web/arkadia_console && pnpm dev`, port 5100 from `vite.config.ts:24`).
* `architecture/ATLAS.md` — MAP 01's Presentation row names the console and marks
  `web/console/` 🟣 LEGACY; a dated correction block states that the rest of the map is
  still the 2026-09-12 reading and has **not** been re-derived.

Guard (`tests/test_root_doc_module_map_currency.py`, extending #715 rather than adding a
parallel detector):

* the domain is now root `*.md` **plus** `architecture/*.md`;
* a generation marker no longer exempts a document that tells an agent to rely on it;
* a markdown **table row** is a claim, alongside a fenced block line;
* `.github/workflows/root-doc-module-map.yml` selects `architecture/**` in both the
  `pull_request` and `push` filters, because the guard now reads that tree.

## 5. Verification

```console
$ python -m pytest -q tests/test_root_doc_module_map_currency.py
46 passed in 0.13s
$ python -m pytest -q --collect-only tests/test_root_doc_module_map_currency.py
46 tests collected
$ python -m pytest -q tests/architecture/
11 passed
$ python -m pytest -q tests/test_ci_gate_trigger_coverage.py \
    tests/test_workflow_injection_boundary.py tests/test_m02a_ci_gate_integrity.py
229 passed
$ git status --porcelain | awk '{print $2}' | python scripts/cp10_mutation_boundary_policy.py --judge
Mutation boundary PASS
```

**Attribution of `+7`.** Base guard collects **39**, branch collects **46**. The delta is
5 new test functions plus 2 new parametrized documents (`REPOSITORY_SNAPSHOT.md`, now
enrolled by the reliance rule; `architecture/ATLAS.md`, now in the domain). `replit.md`
adds **no** node — it was already enrolled and passing, which is the blind spot in §3.1.

**Live negative controls.** Each repair was reverted alone, the guard was run, and the file
was restored:

| reverted | result |
|---|---|
| `REPOSITORY_SNAPSHOT.md` | `FAILED …[REPOSITORY_SNAPSHOT.md]` |
| `replit.md` | `FAILED …[replit.md]` |
| `architecture/ATLAS.md` | `FAILED …[ATLAS.md]` |

All three restored byte-identically (sha256 compared before and after). Each repair is
individually load-bearing; none of the three nodes is carried by another repair.

**Full-suite node-set comparison.** Two full passes in this environment (`pyyaml` present,
`PYTHONPATH=archive/legacy_python`, `--continue-on-collection-errors`):

| tree | result |
|---|---|
| `main` @ `bb19aabd` | `19 failed, 4250 passed, 22 skipped, 1 error` |
| this branch | `19 failed, 4303 passed, 22 skipped, 1 error` |

Failing/error node **set** is identical on both sides — 20 nodes, sha256
`31653a5cc1e70e0cbac26c98b2bde3b7cec6fc27b93fcbadfb7c422da10b5505` on **both**, `comm -3`
empty, zero nodes only-on-branch. The `+53 passed` is the 46 guard nodes in this file
(absent from `main`) plus 7 the generic workflow-scanning suites gain by construction from
the one workflow this branch edits.

Every one of the 20 nodes is owned or sovereign-reserved, matching the decomposition
cycle 05 recorded: 1 CE-01 (`ERROR tests/test_autonomy.py`, sovereign-reserved), 1 FINDING
F-01 (`test_no_firebase_persistence_in_gate`, sovereign-reserved), 10 environment-only
(`test_mission_lifecycle_adapter_contract.py`, which needs
`web/arkadia_console/node_modules/typescript`; `pnpm install` was not run for this pass),
2 owned by #700, 2 by #690, 2 by #693, 1 by #691, 1 by #698. **No unowned, non-reserved
defect is in the set.**

## 6. Recorded, not repaired

* `architecture/ATLAS.md` MAP 02 labels the interface layer "Prism / Android / Bots". That
  is a conceptual diagram, not a path claim, so it is outside this guard's invariant. The
  correction block above it bounds the claim; the diagram is **not** re-derived.
* `CURRENT_STATE.md`, `NEXT_AGENT.md`, `MISSION.md`, `.bootstrap/01_STATE.md` and
  `RECONCILED-CONSOLE-ARCHITECTURE-01.md` mention `web/public_prism` in **prose** and in
  work-log narrative. Prose is not a claim under this guard, and rewriting a work log to
  look current would be a different change. Left as records.
* `.bootstrap/01_STATE.md:55` also names `arkadia-kw64.onrender.com`, which is not the
  canonical origin (`arkadia-qzu4`). Out of scope here; recorded for a separate pass.

## 7. Next-action block

**Current state.** `main` = `bb19aabd…`; production revision identical (revision parity
only). The three orientation documents named above now point at the active console, and the
class is judged for table rows, the architecture tree, and agent-reliance documents.

**Evidence.** This record; §5's commands and their measured output.

**Blockers.** (a) Merge execution is human-only (GOV-03) — 38 drafts, including this one,
await human review. (b) The queue is large enough that composition, not authoring, is the
binding constraint.

**Authorized next action.** Human review of the queue. A later cycle may take up the
prose/narrative surfaces recorded in §6, or the `arkadia-kw64` origin claim in
`.bootstrap/01_STATE.md`.

**Forbidden.** Merging; pushing to `main`; force-pushing; deploying; rewriting the work-log
documents in §6 under this authorization; widening the guard's domain to documents whose
claims are not path claims.

**Completion condition.** This cycle is complete when this record and the change are
reviewable, `main` is unmodified, and no merge, deployment or acceptance is claimed.
