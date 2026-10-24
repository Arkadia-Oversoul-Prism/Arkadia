# LANE 3 — Knowledge OS · `traverse` edge-list dedupe (bounded defect repair)

Workstream: Prism UI reconciliation, LANE 3 (Solariun + Knowledge OS).
Branch: `fix/knowledge-traverse-edge-dedup-01`. Base `main`: `3ca8582ab3cbcd5950fe8a2eab1de2500c1255c3`
(measured this pulse; the ledger's `f390526…` baseline is superseded).

## Objective

`knowledge.graph.traverse` returned a duplicated edge row whenever a later BFS hop
re-reached an edge already seen. Repair the projection so the returned edge list is
a set of readable edges, and pin that property with a guard, since the existing
suites assert only node membership and were blind to the duplication.

## Evidence-backed defect

`traverse(start_id, max_depth=2)` on a `1->2, 1->3, 3->4` fixture starting at node 3
returned edges `[(3,1,3),(1,1,2),(3,1,3)]` — the `1->3` row twice, because node 1 is
adjacent to both the start (3) and node 2, so the second hop rediscovered it.
`max_depth=3` duplicated further. The reachable **node** set was correct; only the
edge list carried duplicates, which is why `tests/test_isolation.py` (node-set pins)
passed throughout.

## Change

- `knowledge/graph.py` — emit an edge once, when its first endpoint joins the
  frontier (`seen_edges` keyed on `graph_edges.id`). The row id is the edge identity
  (`UNIQUE(source_note_id, target_note_id, relationship)`).
- `tests/test_knowledge_graph_traverse_boundary.py` (new, 9 nodes) — pins the set
  property over the returned edge list at depths 1–3, that dedupe does not drop
  reachable nodes, that the relationship filter and the ownership boundary still
  hold, and carries two controls:
  - a **negative control** reconstructing the pre-repair accumulation inline and
    asserting it *does* duplicate on this fixture (so the fixture cannot stop
    exercising the class and let the guard pass vacuously);
  - a **detector control** asserting the duplicate detector reports a repeated row.

## Verification (measured)

| command | result |
| --- | --- |
| `python -m pytest tests/test_knowledge_graph_traverse_boundary.py -q` | **9 passed** |
| same, with the fix reverted to the pre-repair accumulation | **4 failed, 5 passed** |
| `tests/test_knowledge_graph_traverse_boundary.py tests/test_isolation.py tests/test_relational_lineage.py -q` | **24 passed** |
| `python -m pytest tests/architecture -q` | **11 passed** |
| `python -m py_compile knowledge/graph.py` | OK |

The revert/restore was performed in the working tree and the file restored
byte-identically (`knowledge/graph.py` compiled after restore).

## Regression boundary

Node set of the touched suites unchanged; the `+9` is the new file's own nodes
(`--collect-only` → 9). No shared file is touched: `knowledge/graph.py` is
backend-local, the new guard is `tests/…` (admitted by the existing CI rules), and
no workflow edit is required — the console-contract gate derives its domain and
filters `tests/**`.

## Scope boundary and ownership note

This pulse advanced **one bounded slice**. The working tree also carried
uncommitted LANE-3 console changes (`KnowledgeGraphPanel.tsx`,
`knowledgeContracts.ts` — the node-inspection surface) from a prior pass; they were
**left uncommitted and out of this commit**, because they overlap the file owned by
open PRs **#509** (`feat/prism-lane3-project-detail-reader-01`) and **#498**
(`feat/prism-next9-03-knowledge-timeline-paging`), both of which modify
`pages/knowledge/knowledgeContracts.ts`. Committing a second, un-reconciled variant
of that file would manufacture a conflict for the sovereign. They remain on the
branch's working tree only.

## Remaining uncertainty

- This is a repository-source claim. No runtime/deployment observation was made and
  none is claimed.
- The lane-3 console panels (#498, #509) are not reconciled by this commit.

## Authorization

Inspection/measurement only. No merge, deployment, or acceptance. PR opened **draft**;
the sovereign merges.
