# EVIDENCE — `gate-hygiene` / bootstrap scope reconciliation, pass 2026-09-30

> **Docs-only.** No test, source, workflow, governance, constitutional, kernel, api, or
> `web/` file is modified. `api/main.py` untouched (2519 / 2600 lines, `py_compile` clean).
> Two `.bootstrap/` session files are rewritten; nothing outside `.bootstrap/` and this
> evidence directory is touched.

## 1. Objective and scope

`.bootstrap/03_SCOPE.md` and `.bootstrap/04_SUCCESS.md` were asserting an **active Build
session for a checkpoint that closed long ago**. Both files describe session
`B1.1 — SQLite Schema` as the work to do now ("Implement the SQLite schema for the runtime
database. Nothing else."). B1.1 is complete on `main`; the brief was never rewritten.

A stale session brief is not cosmetic: `00_BOOT.md` instructs a stateless agent to
"implement exactly one checkpoint from `01_STATE.md`" and to treat `03_SCOPE.md` as the
authoritative file list. An agent obeying these two files would attempt to re-create
`kernel/storage/schema.py` and `tests/test_sqlite_schema.py` — both of which already exist —
or, if it noticed, would be left with no authorized next action at all.

**Bounded question answered by this pass.** Are the B1.1 brief in `03_SCOPE.md` and the
B1.1 checklist in `04_SUCCESS.md` satisfied on `main`, and if so, what should those two
files say instead?

**Completion condition.** Every B1.1 success criterion is resolved against measured evidence
at a stated SHA, both files are rewritten to stop asserting a dead session, and the
remainder is explicitly deferred with an owner.

**Regression boundary.** Documentation only — the full-suite fingerprint must be identical
before and after. See §5.

**Authority boundary.** No merge, no push to `main`, no force-push, no product decision, no
governance or authority-model change.

## 2. Base identity

| item | value |
|---|---|
| `BASE_MAIN` | `002b189dd95e41c9b4f4cca33d08b4121453d289` |
| provenance | merge of PR #141, `2026-09-30 02:22:31 +0100` |
| local `main` / `origin/main` / `origin/HEAD` | all at `002b189` |
| working tree at branch point | clean |
| branch | `gate-hygiene/bootstrap-scope-reconciliation-01` |
| clone | **grafted** — `git log --oneline -3 -- weaver/autonomy.py` returns a single grafted commit; ancestry claims beyond one commit are **not** verifiable in this clone |

## 3. B1.1 is complete on `main` — every criterion measured

`04_SUCCESS.md` listed 14 binary criteria. All were re-measured at `002b189`:

| # | criterion | measured result | state |
|---|---|---|---|
| 1 | `kernel/storage/__init__.py` exists | present | **VERIFIED** |
| 2 | `kernel/storage/schema.py` contains `create_tables(db_path)` | present | **VERIFIED** |
| 3 | `create_tables()` idempotent | called twice → `idempotent OK` | **VERIFIED** |
| 4 | schema matches `docs/phase1/SQLITE_JOB_QUEUE_DESIGN.md` | `jobs` + `goals` match exactly; `corpus_sync_state` / `corpus_file_state` are later C1.1 additions | **VERIFIED** |
| 5 | WAL mode enabled in `create_tables()` | `PRAGMA journal_mode = WAL` at `kernel/storage/schema.py:31` | **VERIFIED** |
| 6 | `tests/test_sqlite_schema.py` exists and passes | **11 passed** | **VERIFIED** |
| 7 | `pytest tests/architecture/ -v` → 11/11 | **11 passed** | **VERIFIED** |
| 8 | no new layer violations | architecture suite green | **VERIFIED** |
| 9 | `data/runtime.db` NOT committed | not in `git ls-files` | **VERIFIED** |
| 10–14 | `01_STATE.md` / `03_SCOPE.md` / `04_SUCCESS.md` / `NEXT_AGENT.md` / ledger updated for B1.2 | `docs/phase1/CONTINUATION_LEDGER.md:710` records `B1.1 CLOSED — commit 1a38633`; `docs/checkpoints/B1.1.md` exists | **VERIFIED** |

Commands:

```bash
python -m pytest tests/test_sqlite_schema.py -q          # 11 passed
python -m pytest tests/architecture -q                   # 11 passed
python -c "from kernel.storage.schema import create_tables; \
  create_tables('data/test_runtime.db'); create_tables('data/test_runtime.db'); print('idempotent OK')"
git ls-files | grep -i runtime.db                        # (no output)
```

B1.2 is also already implemented — `kernel/storage/sqlite_job_store.py` and
`kernel/storage/sqlite_goal_store.py` both exist, and `CONTINUATION_LEDGER.md:711` marks
B1.2 as done. **The B1.1 brief is stale, not the code.** This is the same failure shape
already documented for `01_STATE.md`'s K5 marker (see §7).

## 4. What was changed

| file | change |
|---|---|
| `.bootstrap/03_SCOPE.md` | B1.1 session brief replaced with an explicit **"no checkpoint authorized"** state + the measured B1.1 evidence table + a rule that the next checkpoint is derived from the repository, not from this scratchpad |
| `.bootstrap/04_SUCCESS.md` | B1.1 checklist retained as a **closed historical record** with every box measured; "no session is active" stated up front |
| `PARKING_LOT.md` | two items appended (§6, §8) |
| this file | new |

**Both rewritten files stop asserting a live session.** They do not select a replacement
checkpoint, because selecting one is `01_STATE.md`'s job and that file is already being
reconciled by an open PR (§7).

## 5. Baseline comparison — no regression

Full suite at `002b189` before any write:

```
20 failed / 1039 passed / 13 skipped / 2 collection errors
```

**Fingerprint, independently reproduced.** PR #146 published a derivation for the recorded
`a7687fad…` value. This pass re-ran it from a clean worktree and obtained the **same hash**,
which retires the "UNKNOWN provenance" caveat carried in earlier evidence:

```bash
grep -E '^(FAILED|ERROR) ' <run>.txt | sed 's/ - .*//' | sort > /tmp/nodes.txt   # 22 nodes
```

| derivation | value |
|---|---|
| over full `FAILED`/`ERROR` summary lines, sorted | `a7687fadaa25ad5f8aa283747bbffa85d304d516ae2b6c53b3849dc54479434c` ✅ matches PR #146 |
| over node ids alone, sorted | `ff49f74304ca3c4790a0d11ebfdf55a7c4d90bf522057ee3e5addad42998b35e` — **not** the fingerprint |

20 `FAILED` + 2 `ERROR` = 22 nodes. The change set is documentation-only, so the fingerprint
is expected to be byte-identical after; it is re-checked in §9.

## 6. Discovery — the `test_autonomy.py` collection error is unclaimed (parked, not fixed)

While mapping the red nodes to their owners, one node turned out to have **no carrier**:

| node | owner found |
|---|---|
| `ERROR tests/test_autonomy.py` | **none** — no open PR, no ledger row, no workstream |

PR #149 (`gate-hygiene/render-codex-collection-error-provenance-01`) claims only
`test_render_codex.py`; its changed files are `tests/render_codex_probe.py` + evidence. The
`test_autonomy.py` error is unowned.

**Root cause, measured (not inferred).** Two distinct objects occupy the same dotted name:

```
weaver/autonomy.py    — module;  def load_autonomy_config() (line 15),
                                 def validate_autonomy_config() (line 22),
                                 def run_scheduled_once() (line 43)
weaver/autonomy/      — package; __init__.py declares
                                 __status__ = "disabled",
                                 "Guards and proposal engine only. No execution hooks."
```

Python resolves `weaver.autonomy` to the **package**, so the module is shadowed and
unreachable by its dotted name. Two live consumers import the shadowed names and both fail:

- `tests/test_autonomy.py:2` → `ImportError: cannot import name 'load_autonomy_config' from 'weaver.autonomy'`
- `weaver/run_autonomy.py:3` → same import path, same failure

This is a **CONTRADICTION, not stale prose**: the package's own docstring declares
"no execution hooks", while the module it shadows *is* an execution hook
(`run_scheduled_once` drives `RecursiveEngine` and commits via `git_ops`). Choosing which
object is canonical therefore decides whether autonomous execution is reachable at all —
that is an authority/governance question reserved to the sovereign.

**Disposition: parked in `PARKING_LOT.md`, not repaired.** Fixing it inside a docs-only
scope-reconciliation pass would both widen scope and pre-empt a governance decision.

## 7. Continuity — why this pass did not reconcile `01_STATE.md`

`.bootstrap/01_STATE.md` is **also** stale (it marks `K5 — Static Ingestion` as
`READY TO BEGIN` and lists K2 as the next checkpoint while `01_STATE.md`'s own "Completed"
section marks K2 done). That is the **same class of defect**, but it is already claimed:

- **PR #146** `gate-k/k5-status-reconciliation` — "reconcile stale bootstrap state; correct
  two false claims (docs-only)", changing `.bootstrap/01_STATE.md`, `MISSION.md`,
  `NEXT_AGENT.md`, `docs/checkpoints/K5_static_ingestion.md`.
- **PR #153** `gate-k/k4-response-provenance-01` — implements the K4 checkpoint that #146
  names as next.

Per the contract's `PRESERVE CONTINUITY` rule ("IF an existing bounded PR is active:
CONTINUE THAT PR. Do NOT create duplicate work"), `01_STATE.md` was **left untouched**. This
pass covers only the two files #146 does not touch, so the two PRs are complementary and
non-overlapping.

## 8. Discovery — `spiral_grove` prerequisite order is a contract contradiction (parked)

`tests/test_spiral_grove_registry.py::test_ais_catalog_supports_progressive_creative_workflow`
is classified `DRIFT` in the ledger. Measured behaviour at `002b189`:

```
registry declares:  cap-ai-creative-workflows -> [cap-ai-prompt-engineering,
                                                  cap-digital-intelligence,
                                                  cap-content-systems]   # declaration order
graph returns:                                    [cap-digital-intelligence,
                                                   cap-ai-prompt-engineering,
                                                   cap-content-systems]   # topological order
```

`test_registry_rejects_prerequisite_cycle` is red **on `main`** too, while the same test
passes in the module's own non-catalog fixture (`test_registry_reports_ready_prerequisites`,
green). So the catalog contains a prerequisite cycle or a self-edge that the guard only
detects on the catalog path.

`SH-02`'s disposition pass already ruled this node **out of `SH-02` scope** — "`SH-02` is
scoped to *assertions drifted from intact behaviour*, and in all four of these the behaviour
itself is in question" — and assigned the registry nodes to `DRIFT`. A topological order is
a defensible contract for a *learning path* and a contradiction for a *declaration-order*
contract; deciding which the Spiral Grove registry means is a product/contract decision, and
it sits on a CP10-fenced path. **Parked, not repaired.**

## 9. Verification states

| item | state | basis |
|---|---|---|
| `BASE_MAIN` = `002b189` | **VERIFIED** | live `git log`; three refs agree |
| B1.1 complete (all 14 criteria) | **VERIFIED** | §3 commands, run this pass |
| `.bootstrap/03_SCOPE.md` asserted a dead session | **VERIFIED** | file content at `002b189` vs `CONTINUATION_LEDGER.md:710` |
| `test_autonomy.py` error unclaimed | **VERIFIED** | open-PR file lists (#149 covers `test_render_codex.py` only) |
| `weaver.autonomy` name collision is the cause | **VERIFIED** | verbatim `ImportError` + both paths on disk |
| autonomy repair requires a governance decision | **VERIFIED** | package docstring "No execution hooks" vs module's `run_scheduled_once` |
| fingerprint `a7687fad…` reproduces | **VERIFIED** | re-derived this pass (§5) |
| registry ordering is a contradiction, not drift | **VERIFIED** | declaration order vs returned order + cycle test red on `main` |
| **production parity for `002b189`** | **UNKNOWN** | no deployment identity inspected this pass — not claimed |
| `vite build` | **BLOCKED** | no npm registry access in this environment |

## 10. Preconditions verified before any write

| precondition | result |
|---|---|
| canonical clone on `main`, remote consistent | **pass** |
| `BASE_MAIN` is a real commit | **pass** — `002b189`, PR #141 merge |
| working tree clean at branch point | **pass** |
| protected architecture suite | **11 / 11 pass** |
| boot code compiles, within budget | **pass** — `py_compile api/main.py` OK; 2519 / 2600 |
| CP10 admits every written path | **pass** — `--judge` exit 0 for all four paths |
| no repository evidence contradicts assumed state | **pass** — one prior claim (B1.1 "next") contradicted and reconciled |

## 11. What this pass did not do

- Did not touch `01_STATE.md`, `MISSION.md`, `NEXT_AGENT.md` — owned by open PR #146.
- Did not repair the `weaver.autonomy` collision — governance decision (§6).
- Did not repair the registry ordering — product/contract decision (§8).
- Did not touch `tests/`, `kernel/`, `api/`, `web/`, `weaver/`, any workflow, or any ADR.
- Did not reclassify any ledger row, and did not touch `LAYER_MAP.py`.
- Did not merge, push to `main`, force-push, or self-authorize anything.
- Did not claim production parity — `UNKNOWN` (§9).
