# Lane 3 — Knowledge OS graph health: a count was read as its column name

**Pass:** lane3-graph-health-count-read-01
**Lane:** 3 (Solariun + Knowledge OS)
**Base main:** `46d85e2d74df4f5016f54a4ee9c3d994a5bb0c03` (verified live `origin/main`, unchanged
before and after this change)
**Deployed revision under examination:** `46d85e2d74df4f5016f54a4ee9c3d994a5bb0c03`
(`GET /api/version` -> `source_revision`, `revision_conflict: false`)
**Canonical origin:** `https://arkadia-qzu4.onrender.com` (ADR-016)

## 1. The defect

`knowledge/graph_health.py::_count()` read its scalar with `list(row)[0]`, under the
comment "execute_one returns a sqlite3.Row; first value is the count". That assumption is
false: `knowledge/db.py::execute_one()` returns a **dict keyed by column name**
(`row_factory = sqlite3.Row` is the *connection* factory, but the helper converts to
`dict`). Iterating a dict yields its **keys**, so `list(row)[0]` returned the column name.

```
_count("SELECT COUNT(*) FROM notes")  ->  'COUNT(*)'
```

The misread propagates. Every consumer divides it, and `evaluate_graph_health()`'s
`except` collapses the entire evaluation:

```
{"overall": "error",
 "error": "unsupported operand type(s) for /: 'str' and 'str'",
 "checks": {}}
```

This is **not data-dependent**. The empty path still divides
(`orphan_count / total_nodes`) once `total_nodes` is truthy, so an empty database
reproduces it. The whole Knowledge OS health surface is lost regardless of graph content.

Sibling occurrences of the same row-shape assumption were checked and are **correct**
because they set the factory themselves and never read positionally:
`knowledge/db.py:30`, `solspire/eden_ops.py:52`, `solspire/voice_store.py:57`.

## 2. Production measurement (read-only)

Measured 2026-11-03 against the canonical origin at deployed revision `46d85e2d`:

```
$ curl -s https://arkadia-qzu4.onrender.com/api/knowledge/graph/health
{"overall":"error","error":"unsupported operand type(s) for /: 'str' and 'str'","checks":{}}

$ curl -s https://arkadia-qzu4.onrender.com/api/knowledge/status
graph_health = error
status       = operational          <-- the transport reports success while the reading is lost
graph        = {"edges": 3}
vault        = {"notes": 40, "projects": 0, "chunks": 119,
                "embeddings": 0, "pending_embeddings": 40}
```

Note the contrast that makes this a real loss rather than a cosmetic one: the same body
carries `vault.notes: 40` and `graph.edges: 3` — the data is present and countable — while
`graph_health` reports `error`. The reading is unavailable, not the data.

## 3. Repair

One function, two lines (`knowledge/graph_health.py::_count`):

```python
row = execute_one(sql, params)
if row is None:
    return 0
return int(next(iter(row.values())))
```

`None` (no rows) yields `0`; otherwise the **first value** is taken, matching the dict
shape the helper actually returns. The misleading comment is corrected to name the real
shape and the failure it caused.

## 4. Guard

`tests/test_knowledge_graph_health_read_boundary.py` — **12 nodes**, all passing.

The guard binds the reading to the **real** `execute_one` rather than restating a count, so
it measures the helper contract rather than a copy of it:

| node | what it holds |
|---|---|
| `test_execute_one_returns_a_dict_keyed_by_column_name` | the precondition: the row is a dict, `list(row)[0] == "COUNT(*)"` |
| `test_count_reads_the_value_not_the_column_name` | `_count` returns the number |
| `test_count_is_zero_on_an_empty_result_set` | the `None` path stays numeric |
| `test_evaluation_reports_a_healthy_graph_rather_than_a_crash` | clean graph -> `ok`, all six checks present |
| `test_evaluation_ratios_are_numeric` | both divisions — the exact `TypeError` site |
| `test_an_empty_database_is_ok_not_error` | the empty case reproduces the defect, so it is pinned |
| `test_pending_embeddings_surface_as_warn_with_real_counts` | a real finding reports measured numbers |
| `test_a_dangling_edge_is_still_reported_as_error` | the repair does not blunt the checks |
| `test_status_route_serves_the_evaluation` | `graph_health` on the public body is a real verdict |
| `test_negative_control_the_pre_repair_expression_yields_the_column_name` | detector bites |
| `test_negative_control_the_pre_repair_ratio_raises` | the exact failure mode |
| `test_no_other_module_reads_a_row_positionally` | the defect *class*, across `knowledge/` and `api/` |

The fixture rebinds `ARKADIA_DB_PATH`, `knowledge.db._DB_PATH` and the package-level
`_DB_PATH`, and clears the thread-local connection, because `knowledge.db` snapshots the
path at import time — without that the fixture would measure a session DB rather than its
own.

### Negative control — live, not synthetic

The pre-repair expression was restored in the **real** `knowledge/graph_health.py`
(`return list(row)[0]`) and the guard re-run:

```
9 failed, 3 passed
```

The 3 that still pass are exactly the precondition and the two controls — the nodes that
assert the *defect's* shape rather than the repair. The file was then restored
byte-identically and the guard re-run: `12 passed`.

### Coverage before this change

Measured: `grep -rln "graph_health" tests/` matched **nothing** before this file was added,
so the module that produces the public `graph_health` verdict had **zero** test coverage.
That is why the defect survived to production: nothing executed `_count()`.

## 5. Verification executed

| command | result |
|---|---|
| `python -m pytest tests/test_knowledge_graph_health_read_boundary.py -q -rEf` | **12 passed** |
| same, with the pre-repair expression restored | **9 failed, 3 passed** (control bites) |
| `python -m pytest tests/architecture -q` | **11 passed** |
| `python -m pytest tests/test_m02a_ci_gate_integrity.py -q -rEf` | **72 passed** |
| `python -m pytest tests/test_knowledge_status_read_boundary.py tests/test_knowledge_os_boundary.py tests/test_m06_knowledge.py tests/test_knowledge_shared_connection_lifecycle.py tests/test_solariun_knowledge_slice_01.py -q -rEf` | **43 passed** |
| `python -m py_compile api/main.py` | compiles; `api/main.py` = **2586** lines (budget 2600) |
| `python scripts/cp10_mutation_boundary_policy.py --judge` (new paths) | **PASS** |

Behavioural end-to-end check against real databases:

```
empty DB   -> overall = ok
2 notes + 1 edge, embeddings complete -> overall = ok
2 notes + 1 edge, embeddings pending  -> overall = warn   (measured counts, no crash)
2 notes + 1 edge, target deleted      -> overall = error  (dangling_edges = 1)
```

## 6. Gate-domain check

`tests/test_knowledge_graph_health_read_boundary.py` was checked against the
content-derived gate domains before committing. It contains **zero** occurrences of the
needles those domains key on (`economic_seams`, `arkadia_console`, `frontend_routes`), so
it joins no derived domain and requires no workflow edit. The guard is executed by the
existing knowledge-test surface (`tests/**` selection).

## 7. Boundaries

- **Not merged.** OpenHands holds no Weaver merge authorization; this is a draft PR.
- **No deployment, no acceptance claim.** This is a repository-source repair plus a
  read-only production observation of the defect. Production parity is not claimed: the
  fix reaches production only after a deploy containing it.
- **Scope:** `knowledge/graph_health.py` + its new test + this record. No shared routing,
  navigation, tokens, NovaNet, or Arkana/Weaver/Lab files were touched.
- **`docs/control-plane/parallel-ui/AGENT-03-SOLARIUN-KNOWLEDGE.md` was deliberately not
  edited.** That path is a *guarded lane doc*: `scripts/lane_state.py::_freshness_findings`
  anchors the staleness window on `lane-state.json` and reddens `main` when a guarded doc
  moves after the snapshot was recorded. A doc edit here would have required refreshing
  `lane-state.json` (a re-derivation this pass did not perform), so the lane status is
  recorded in this evidence file instead of on the guarded surface.

## 8. Next bounded task

`GET /api/knowledge/graph/health` now has a guard for the count read. The remaining
unpinned surface in this module is the **ontology-violation** check
(`unknown_relationship_types`): no test drives a real unknown relationship type through
it. That is the next bounded Lane 3 slice.
