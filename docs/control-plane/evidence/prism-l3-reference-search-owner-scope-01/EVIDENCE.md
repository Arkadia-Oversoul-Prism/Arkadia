# Lane 3 — reference search leaked private citations across owners · evidence

**Branch:** `fix/prism-l3-reference-search-owner-scope-01`
**Base `main`:** `7580bd8f` (merge of PR #533)
**Authority:** implement, test, commit, open a draft PR, report. **No merge, deployment,
or acceptance.** The repair edits a Lane-3 feature-owned backend file
(`knowledge/search.py`), which `AGENT-03-SOLARIUN-KNOWLEDGE.md` authorizes for a
"concrete security/privacy issue" and requires escalating.

---

## 1. The defect

`POST /api/knowledge/search` (`api/knowledge_routes.py::search` ->
`knowledge.search.unified_search`) is documented and tested as an owner-scoped
boundary: a caller sees their own material plus the public (NULL-owner) corpus,
and never another owner's private rows. That held for `fulltext`, `semantic`,
`tag`, `timeline`, `graph`, `project`, and `people`.

It did **not** hold for `reference` — the eighth mode. `reference_search` took no
`user_id`, and `unified_search` dispatched it without one:

```python
def reference_search(query: str, limit: int = 20) -> list[dict]:
    return execute(
        "SELECT * FROM \"references\" WHERE target_ref LIKE ? OR label LIKE ? ...",
        (f"%{query}%", f"%{query}%", limit),
    )
...
results["reference"] = reference_search(query, limit=10)   # no user_id
```

`references` rows carry no owner column; visibility is inherited from
`source_note_id`. With no owner predicate at all, **every** caller — including an
anonymous one — received every owner's citations. This is the same defect class
commit `106640bb` ("anonymous search must not return private notes") repaired for
the other modes; `reference` was missed, and the existing static detector could
not see it either (see §4).

## 2. Measured, not inferred

Two independent probes, both run against a fresh temp `ARKADIA_DB_PATH`.

Function level (`knowledge.search.reference_search`, note owned by `USER_A`):

```
anonymous reference_search('PRIVATE_A_REF'): ['PRIVATE_A_REF']
anonymous reference_search('secret'): ['PRIVATE_A_REF']
```

HTTP level (`POST /api/knowledge/search` through the real router, auth layer in
dev-mode so the unsigned-token identity path is exercised):

```
anonymous HTTP: 200 ['ARKADIA_PRIVATE_REF_CANARY']
non-owner HTTP: 200 ['ARKADIA_PRIVATE_REF_CANARY']
default modes reference: ['ARKADIA_PRIVATE_REF_CANARY']
```

The third line matters: the leak is reachable through the **default** mode set,
not only an explicit `modes=["reference"]` call, so no caller had to opt in.

## 3. The repair

Owner predicate applied to the joined note, reusing the existing
`_notes_owner_sql` helper (own-or-public when authenticated, public-only
otherwise):

```python
def reference_search(query: str, limit: int = 20, user_id: Optional[str] = None) -> list[dict]:
    owner_sql, owner_params = _notes_owner_sql(user_id, table_alias="notes")
    return execute(
        "SELECT \"references\".* FROM \"references\" "
        "JOIN notes ON notes.id = \"references\".source_note_id "
        "WHERE (\"references\".target_ref LIKE ? OR \"references\".label LIKE ?) "
        f"AND {owner_sql} "
        "ORDER BY \"references\".created_at DESC LIMIT ?",
        (f"%{query}%", f"%{query}%", *owner_params, limit),
    )
...
results["reference"] = reference_search(query, limit=10, user_id=user_id)
```

Post-repair, the same HTTP probe:

```
anonymous HTTP: 200 []
non-owner HTTP: 200 []
default modes reference: []
```

## 4. The guard could not see the mode that leaked

`tests/test_knowledge_search_boundary.py::_unscoped_search_calls` scans
`unified_search`'s dispatch for calls omitting `user_id`. Its pattern listed
`project_search|timeline_search|people_search|graph_search` — **`reference_search`
was absent**, so the pre-repair dispatch was not reported. A guard that cannot
name the defective call is not a guard for it. The pattern now includes
`reference_search`, with a dedicated negative control
(`test_detector_flags_an_unscoped_reference_dispatch`) proving the pre-repair
shape is reported and the repaired shape is not.

## 5. Negative control on the real file

Reverting `knowledge/search.py` to the pre-repair blob (fix extracted to a patch,
file checked out, tests run, patch re-applied) yields exactly:

```
FAILED tests/test_knowledge_search_boundary.py::test_reference_mode_does_not_leak_private_citations
FAILED tests/test_knowledge_search_boundary.py::test_reference_mode_does_not_leak_through_the_default_mode_set
FAILED tests/test_knowledge_search_boundary.py::test_reference_search_owns_the_predicate_not_the_caller
FAILED tests/test_knowledge_search_boundary.py::test_unified_search_forwards_user_id_to_every_scoped_mode
4 failed, 21 passed in 0.64s
```

All four pass after the repair. The pins bite on the real file, not a synthetic
fixture.

## 6. Verification

| Command | Result |
|---|---|
| `pytest tests/test_knowledge_search_boundary.py -q -rEf` | **25 passed** (21 before -> +4 new nodes) |
| `pytest -q $(python scripts/console_contract_domain.py)` | **550 passed** |
| `pytest tests/architecture -q` | **11 passed** |
| `pytest tests/test_knowledge_{search,os,projects,timeline}_boundary.py tests/test_prism_console_ci_wiring.py -q -rEf` | **103 passed** |

Node delta attributed by `--collect-only`: the target file goes 21 -> 25, i.e. the
four added nodes and nothing else. `knowledge/search.py` is not in the
`api/main.py` boot path, so `py_compile api/main.py` is unaffected.

## 7. Uncertainty and next bounded task

- This is a repository-source claim. No deployment or runtime acceptance is
  claimed, and the live canonical runtime has not been re-probed.
- The `references` table has no owner column by design; the join is the only
  correct scoping point. If a future change gives references a direct owner, the
  predicate should move there rather than be duplicated.
- Not repaired here (separate, non-overlapping): `graph_search` provenance
  display and the open Lane-3 PRs #498 / #509 / #526 own their own slices.

**Next bounded task:** none taken in this pass; the next pulse advances the
oldest unadvanced Lane-3 PR per the rotation rule.
