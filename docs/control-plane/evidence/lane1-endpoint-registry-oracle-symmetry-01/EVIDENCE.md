# Lane 1 — endpoint-registry guard: served-path oracle repaired in both directions

**Branch:** `feat/prism-l1-endpoint-registry-oracle-symmetry-01`
**Base:** `main` @ `b5bc34cb178d0ec8a804ce6f5761e4bd5e0c7989`
**Head:** `cedced8da52bacdb7d322f81927a4e36ca8a2098`
**Owner:** Lane 1 (SHARED-CONTRACTS.md §1 — "shared shell/endpoint contract tests")
**Scope:** `tests/test_console_endpoint_registry_contract.py` — one file, no production code.

## Defect (measured at `b5bc34cb`)

The guard decided whether an advertised `contract="…"` string is served by the app:

```python
stripped = value[4:] if value.startswith("/api/") else value   # one-way strip
return re.sub(r"\{[^}]*\}", "{}", stripped) in normalized_served
```

The `/api` prefix was stripped from the **advertised** side only, so the comparison
was a one-way prefix removal. It was wrong in both directions:

| Direction | Case | Pre-repair | Truth |
|---|---|---|---|
| false positive | `/api/lab/engineering/sessions/{id}/execute` | unserved | **served** (`{session_id}`) |
| false negative | `/api/solspire/proposals` | **served** | unserved — no such route |

The false negative is the dangerous one: the guard exists to catch an invented
endpoint, and a genuinely invented `/api/...` path passed by collapsing onto its real
bare twin. `grep -rn '"/api/solspire' api/ solspire/` → no match, so nothing is mounted
at that prefix; `/solspire` is the mount.

A second, narrower blind spot sat in the extractor that fed the oracle: it keyed its
result by file (`found[name] = match.group(1)`), so a page with several `NotYetWired`
panels had **every advertised contract but the last one** silently unjudged.
`SolSpirePage.tsx` has four panels; three were never judged.

## Repair

- `_is_served(value, served)` — symmetric: parameter-normalized on both sides, `/api`
  significant on both. A page may still advertise the served shape with its own
  parameter name, which normalization keeps.
- `_advertised_contract_strings` — returns **every** literal per file.
- `RECORDED_ADVERTISED_DRIFT` — 6 entries → 1. Four were never drift; two
  (`/solspire/proposals`, `/solspire/workloads`) are no longer advertised by any page.
  The survivor (`{id}` vs served `{session_id}`) is real display copy in a feature page
  owned by another workstream — recorded, not edited, per §1.

## Evidence

| Check | Command | Result |
|---|---|---|
| Guard | `pytest tests/test_console_endpoint_registry_contract.py -q -rEf` | **20 passed** (was 18; +2 controls) |
| Negative control — oracle | pre-repair oracle restored in place, rerun | **1 failed** (`test_served_oracle_is_prefix_symmetric_in_both_directions`); file restored byte-identically (md5 `d3155158…`) |
| Negative control — extractor | pre-repair keyed-by-file extractor restored, rerun | **2 failed** (extractor + drift test); restored byte-identically |
| Console-contract gate (exact CI command) | `pytest -q $(python scripts/console_contract_domain.py)` | **944 passed** |
| Architecture fitness | `pytest tests/architecture -q` | **11 passed** |
| Related guards | routing / aeas05 / rebuild / shell-nav / ci-wiring | **106 passed** |
| CP10 admission | `printf '<path>' \| python scripts/cp10_mutation_boundary_policy.py --judge` | PASS (exit 0) |
| Full suite (once) | `pytest tests/ -q -rEf --continue-on-collection-errors` | 8 failed, 3674 passed, 20 skipped, 1 error |
| Failing/error node set | sha256 | `c280ddc616fe4f4e9110bf4e6b6e538783a83d3764148d8a6d7ac45f6e8bc46b` (9 nodes) |

**Zero endpoint-registry nodes** appear in the failing/error set (`grep -c endpoint_registry` → 0).

## Baseline attribution

The full-suite node set is 9 nodes. Eight are in the recorded
`tests/fixtures/baseline_node_set.txt` and are unowned pre-existing debt. The two
`tests/test_engineering_lab_api.py` nodes are the documented `api/lab_routes.py`
authority-surface drift (`require_auth` → `require_lab_auth`), sovereign-only to repair
— they read neither this guard nor `endpoints.ts` (`grep -c` → 0), so they are not
attributable to this change. `tests/test_autonomy.py` is the reserved CE-01
module-vs-package collision.

The gate's domain is **derived** (`scripts/console_contract_domain.py`), not a fixed
inventory, so a guard added or removed is executed without editing the workflow — the
composition hazard recorded at `17988afd` is closed for this gate.

## Not claimed

No production deployment, merge, or acceptance. `deployment build output observed`
remains outside this change; the canonical origin was not reachable from this sandbox
(`curl` → exit 28, connection timeout), so no runtime claim is made either way.

## Repair — stray runtime journal removed from the branch (2026-10-29)

`0bb4a18` carried a **357 KB** `data/economic_seams.db-journal` (a SQLite rollback
journal, `Bin 0 -> 357560 bytes`). It was not an intended artifact: the commit's message
concerns a `GH_TOKEN` recovery, and its parent did not contain the file, so a `git add -A`
swept it in from the worktree.

Provenance — `economic_seams/engine.py:9` resolves its store under the same
`SOLSPIRE_DATA_DIR` convention as the canonical SolSpire store:

    DB_PATH = os.environ.get("ECONOMIC_SEAMS_DB") or os.path.join(
        os.environ.get("SOLSPIRE_DATA_DIR", "data"), "economic_seams.db")

`.gitignore` had `data/solspire_projects.db*` but no rule for this store, and `*.db`
covers only the database file, never `-journal`/`-wal`/`-shm`. `git check-ignore
--no-index -q data/economic_seams.db-journal` → exit 1 (stageable). `main` tracks
neither `economic_seams.db` nor any sidecar, so nothing of value was removed.

Three bounded repairs, all inside Lane 1's "shared shell/endpoint contract tests"
ownership plus the repository-hygiene surface:

1. `git rm --cached data/economic_seams.db-journal` — untracked from the branch.
2. `.gitignore` — added `data/economic_seams.db*`.
3. `conftest.py::_sandbox_economic_seams_store` — the load-bearing fix. The engine
   snapshots `DB_PATH` (unprefixed, unlike the SolSpire modules' `_DB_PATH`) at import
   time, so it inherited `data/` rather than a sandbox. The fixture forces
   `ECONOMIC_SEAMS_DB` and rebinds every already-imported copy, mirroring
   `_sandbox_solspire_store`.
4. `tests/test_repo_hygiene_gitignore.py` — `ECONOMIC_SEAMS_FAMILY` (4 paths) pinned,
   plus a `data/`-scoped negative control.

### Verification

| Check | Result |
| --- | --- |
| `pytest tests/test_repo_hygiene_gitignore.py -q` | **16 passed** |
| Negative control: delete `data/economic_seams.db*` | **3 failed, 13 passed** — exactly the three sidecars; `*.db` still covers the base file |
| Restore byte-identically | **16 passed** |
| The 5 economic-seam modules that previously left the journal behind | **47 passed**, `data/` left **clean** |
| `git diff --numstat AGENTS.md` | **26 / 0** — insert-only append preserved |

The negative control is the load-bearing evidence: it shows the new guard detects the
artifact class rather than merely passing alongside it. It also discriminates correctly —
reddening on three of four paths, not on all four or none.
