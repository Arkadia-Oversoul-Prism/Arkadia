# Lane 3 — disclose the knowledge-graph title cap

Lane 3 (Solariun + Knowledge OS) bounded slice, opened under `11 — LANE NEW-PR AUTHORIZATION`.
**Draft — merge is human-only (GOV-03).** This document records implementation evidence, not an
eligibility or acceptance decision.

## What changed and why

`KnowledgeGraphPanel.tsx` renders two bounded lists over the same node set:

- provenance rows — `graph.nodes.slice(0, PROVENANCE_ROWS)`, repaired by PR #667 (`97dbe012`),
  which added `boundedRowNotice(...)` and `data-testid="knowledge-graph-rows-bounded"`;
- title chips — `summary.titles`, capped by `TITLE_LIMIT = 8` inside `summarizeGraph`.

The second list shipped as a bare `<ul>` with **no disclosure**. `Facts` directly above it prints
the exact node count, so a 40-node scope rendered `nodes 40`, eight provenance rows *with* a
"Showing 8 of 40 readable rows" notice, and then eight title chips with nothing saying they were a
prefix. The repaired defect class and the unrepaired one were one block apart, which is why the
unrepaired one survived: the row notice made the block look already-honest.

Same class, same convention, so the same composed helper now covers it.

## Files

| Path | Change |
|---|---|
| `web/arkadia_console/src/pages/knowledge/knowledgeContracts.ts` | `TITLE_LIMIT` exported (the slice bound is now reachable by the disclosure); `boundedRowNotice` gains an optional `noun` so the copy names the list it describes — the panel bounds two lists, and a "rows" notice under chips would be a different false statement |
| `web/arkadia_console/src/pages/knowledge/KnowledgeGraphPanel.tsx` | composes `titleNotice` from the *same* `TITLE_LIMIT` the slice uses; renders it under the chips with `data-testid="knowledge-graph-titles-bounded"`; the chips list gains `data-testid="knowledge-graph-titles"` |
| `tests/test_knowledge_graph_provenance_boundary.py` | `_title_cap_defects` detector + live assertion + negative control |

Both bounded lists now derive their bound from one constant each and hand that same constant to
the disclosure, so a future edit to a cap cannot silently desynchronise the notice from the slice.

## Tests

| Command | Result |
|---|---|
| `python -m pytest tests/test_knowledge_graph_provenance_boundary.py -q -rEf` | **31 passed** (29 nodes before this change: `--collect-only` 29 → 31, +2 = the new assertion and its control) |
| `python -m pytest tests/architecture -q` | **11 passed** |
| `cd web/arkadia_console && corepack pnpm install --frozen-lockfile && corepack pnpm build` | **success** — `✓ 170 modules transformed`, `dist/assets/index-Sk7BSXOa.js 425.37 kB` (build output is untracked) |

### Negative control (live, on the real file)

The control is not a synthetic fixture. The shipped panel was reverted to its pre-repair bytes and
the suite re-run:

```
$ git checkout -- web/arkadia_console/src/pages/knowledge/KnowledgeGraphPanel.tsx
$ python -m pytest tests/test_knowledge_graph_provenance_boundary.py -q -rEf
FAILED tests/test_knowledge_graph_provenance_boundary.py::test_panel_discloses_the_title_cap
FAILED tests/test_knowledge_graph_provenance_boundary.py::test_negative_control_bare_title_chips_are_not_the_convention
2 failed, 29 passed

$ # restored the repair byte-identically
$ python -m pytest tests/test_knowledge_graph_provenance_boundary.py -q
31 passed
```

Both nodes redden together: the live assertion fails because the disclosure is gone, and the
control fails because its final clause requires the shipped sources to be clean under the same
detector. A detector that flagged everything, or nothing, could not produce this pair.

## Not claimed

- No production/runtime observation: this is a source-level console change. The Render origin at
  `https://arkadia-qzu4.onrender.com` is the sole canonical deployment (ADR-016) and was **not**
  exercised by this slice.
- No full-suite pass was run in this pulse: the pulse budget allows at most one, and it was spent
  on reconciliation reconnaissance. The change is confined to one console page module plus its
  guard test; the targeted suite and the architecture fitness suite are the proof.
- Baseline debt on `main` was not repaired and is not attributed to this branch.

## Next bounded task (Lane 3)

`GraphSummary.titles` is a *display* projection; `KnowledgeTimelinePanel` and
`KnowledgeSearchPanel` were not examined for the same undisclosed-prefix shape in this pass.
The next Lane-3 slice should scan those two panels for bounded lists whose bound is not named, and
either disclose it or record that the list is complete.
