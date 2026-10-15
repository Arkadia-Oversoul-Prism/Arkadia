# PRR-L3-14 · Knowledge Graph analytics owner scope + `_count` silent-error repair (Lane 3)

Bounded Lane 3 (Solariun / Knowledge OS) slice. Branch
`fix/prism-l3-graph-analytics-owner-scope-01`, base `main` @
`7580bd8f0ca2925518d78775f9a323ff0df8bc66`.

Authority: no merge, no deployment, no production acceptance, no shared-file
(`App.tsx`, `router.ts`, `surfaces.ts`, `endpoints.ts`, `types.ts`,
`SurfaceLenses.tsx`, `knowledgeContracts.ts`) edit. Draft PR only.

## Defects repaired (both measured, not inferred)

### D1 — graph analytics evaluated every check over the whole store

`knowledge/graph_health.py::evaluate_graph_health()` and the route handlers that
consume it (`GET /api/knowledge/status`, `GET /api/knowledge/relationships`,
`GET /api/knowledge/graph/health`) computed their checks with **unscoped** SQL
(`SELECT COUNT(*) FROM notes`, `SELECT ... FROM graph_edges`). The Knowledge OS
visibility contract is owner-or-public — authenticated callers read
`user_id = ? OR user_id IS NULL`, anonymous callers read `user_id IS NULL` only.
Every analytics field was therefore a whole-store aggregate over material the
caller cannot read:

- `orphan_nodes.total_nodes`, `duplicate_nodes`, `embedding_completeness`,
  `graph_connectivity.components` counted and joined other owners' private rows;
- `relationships.summary.total_nodes` / `total_relationships` /
  `connected_components` / `average_degree` / `density` were whole-store;
- `relationships.top_connected_nodes` returned up to 10 **note titles** — a real
  disclosure surface, since a title is the private content of another owner's note.

Measured pre-repair on the fixture: unscoped `notes` = 7 vs scoped = 4 for
`USER_A`, and an `A3 — B3` cross-owner edge joined two owners' components into
one. The `graph_health` endpoint is mounted on the K3-B/K3-C graph surfaces.

### D2 — `_count` returned a column name instead of a count (silent wrong value)

```python
row = execute_one(sql, params)
return list(row)[0]          # pre-repair
```

`knowledge.db` returns each row as a **dict keyed by column name**, so
`list(row)[0]` is the string `'COUNT(*)'`, not an integer. Measured on base:
`evaluate_graph_health()` returned

```json
{"overall": "error",
 "error": "unsupported operand type(s) for /: 'str' and 'str'",
 "checks": {}}
```

The surface was entirely non-functional. This is a silent wrong-value defect: no
exception is raised at the `_count` call site, and the failure only surfaces
later when the string is used arithmetically (`density`, `average_degree`) or
compared to an int.

A note on provenance: the test's original docstring claimed the pre-repair form
raised `KeyError: 0`. That claim is **false** for the actual `knowledge.db` row
type — `list(dict)` yields the keys, so the observed failure is the `TypeError`
above. The docstring was corrected to the measured behaviour rather than left as
an unverified citation.

## Repair

- `_count` reads `next(iter(row.values()))`.
- New `_note_owner_clause(user_id, alias)` and `_accessible_edge_sql(user_id, select)`
  helpers in `knowledge/graph_health.py` express the owner-or-public predicate once
  and mirror `knowledge.search._notes_owner_sql` / `knowledge.graph.accessible_note_ids`.
- Every check except `_check_invalid_references` accepts `user_id` and evaluates over
  the accessible subgraph; `evaluate_graph_health(user_id)` threads it through.
- `_check_invalid_references` is **deliberately left unscoped** and documented as such:
  a dangling edge is referential corruption, and scoping the probe would hide
  corruption behind the caller's visibility. It reports a count only — no title,
  owner, or per-owner breakdown — so it discloses no private material. Recorded as a
  deliberate non-change, not an oversight.
- `api/knowledge_routes.py`: `/status`, `/relationships`, `/graph/health` take
  `request: Request`, resolve the caller via the module's existing
  `_optional_user_id(request)`, and pass it down. No new auth path, no new
  endpoint, no response-key change (backwards-compatible).

## Tests

`tests/test_knowledge_graph_health_owner_scope.py` (8 tests):

| Test | Property |
|---|---|
| `test_count_reads_a_value_not_a_column_name` | D2 directly |
| `test_graph_health_is_a_verdict_not_a_swallowed_error` | D2 at the public API: `overall` is a verdict, `error` is `None`, `checks` populated |
| `test_graph_health_endpoint_is_scoped_to_the_caller` | D1 on `/graph/health` |
| `test_relationships_route_counts_only_accessible_edges` | D1 on `/relationships` |
| `test_relationships_route_never_names_another_owners_note` | the title-disclosure surface |
| `test_anonymous_caller_sees_only_the_public_corpus` | anonymous = `IS NULL`, a real caller |
| `test_negative_control_unscoped_queries_disagree_with_the_scoped_answers` | the fixture discriminates |
| `test_source_keeps_the_scope_on_every_graph_read` | a later edit cannot silently drop the predicate |

Measured:

- **After repair: 8 passed.**
- **Negative control on base: 7 failed, 1 passed** — the guard fails on the defect
  it describes and passes on the repair, so it is not vacuous.
- Broader knowledge set (`pytest tests/ -k knowledge`): **149 passed, 1 skipped**,
  1 collection error (pre-existing CE-01 `weaver.autonomy` module-vs-package
  collision, reserved to the sovereign).
- `pytest tests/architecture -q` → **11 passed**.
- `pytest tests/test_prism_console_ci_wiring.py -q` → **30 passed**; this test does
  not name the console, so it does not enter the console-contract domain.
- `python -m py_compile api/main.py` → OK; `api/main.py` = 2505 lines (budget 2600).
  `api/main.py` is not touched by this change.

## Cross-PR contention

`knowledge/graph_health.py` and `api/knowledge_routes.py` are touched by **no**
other open PR (scanned all 42 open PRs by `pulls/{n}/files`). The contended Lane 3
file is `knowledgeContracts.ts` (PRs #498/#509/#527/#534), which this slice does
not touch. This slice therefore does not compose into the intra-lane
`knowledgeContracts.ts` contention.

## Remaining uncertainty

- No runtime/production observation: the canonical origin was not probed this pass,
  and production parity is **NOT CLAIMED**.
- `knowledge/graph_health.py` is a backend module, not a console source file, so the
  CP10 console-contract gate does not select it; CP10 boundary admission was verified
  per-path via `scripts/cp10_mutation_boundary_policy.py --judge` (all ADMITTED).
- The whole-store `invalid_references` probe is a deliberate, documented exception;
  if the sovereign prefers a scoped referential-integrity view, that is a separate
  bounded change.
