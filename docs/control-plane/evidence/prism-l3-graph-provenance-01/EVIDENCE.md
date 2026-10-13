# PRR-L3-13 · Knowledge Graph provenance boundary recovery — evidence

**Work item:** `prism-recursive-recovery-01` ledger, Lane 3 (Solariun + Knowledge OS).
**Bounded objective:** surface the canonical GATE-01 capture provenance
(`knowledge/capture.py::provenance_for_note` → `knowledge/graph.py::_attach_provenance`)
in the console Knowledge Graph reader as a *declared* reading — a node whose
capture boundary did not declare an author must read as `undeclared`, and a node
with no capture record must read as `unknown` — instead of the panel silently
showing a node with no provenance line at all.
**Authority:** implement, test, commit, report. **No merge, deployment, or acceptance.**
**Base SHA:** `3ca8582ab3cbcd5950fe8a2eab1de2500c1255c3` (`origin/main` after
`git fetch --all --prune`; local `main` == `origin/main`, clean tree at start).

---

## 1. What the backend already provides (measured, not assumed)

The provenance projection is a **merged canonical contract**, not new work:

- `knowledge/capture.py::provenance_for_note(note_id)` (line 261) returns the
  canonical origin + authorship. A note with **no** `capture_records` row returns
  `{"state": "UNKNOWN", "unknown": True, "source": None,
  "authorship": {"authored_by": None, "authored_by_kind": "unknown", "declared": False}}`.
- `knowledge/graph.py::_attach_provenance(nodes)` (line 16) attaches that dict to
  every graph node, reading **through** `capture.provenance_for_note` so the graph
  projection cannot drift from the capture boundary's shape. Both graph entry
  points (`graph()` line 139 and the traverse projection line 193) pass their node
  lists through it.
- Merged by PR #175 (`gate01/relational-lineage-canonical-provenance`) and
  PR #170 (`arkadia-relational-lineage-02`).

So the defect this slice repairs is **reader-side only**: the console never
rendered the projection that the backend already serves.

## 2. Measured source state before this change

- `web/arkadia_console/src/pages/knowledge/knowledgeContracts.ts` declared no
  provenance vocabulary at all.
- `web/arkadia_console/src/pages/knowledge/KnowledgeGraphPanel.tsx` rendered a
  node's label/type/id and nothing about origin — a node with no capture record
  and a node with a declared source were visually identical.

## 3. Changed paths

| Path | Change |
|---|---|
| `web/arkadia_console/src/pages/knowledge/knowledgeContracts.ts` | adds the `ProvenanceState` vocabulary (`"captured" \| "undeclared" \| "unknown"`) and the graph-node provenance type. |
| `web/arkadia_console/src/pages/knowledge/KnowledgeGraphPanel.tsx` | imports and renders `summarizeProvenance` / `provenanceReading` / `provenanceNotice`, so each node carries a truthful provenance reading and the panel totals reconcile with the node count. |
| `tests/test_knowledge_graph_provenance_boundary.py` (new) | boundary tests over the real backend projection + source-level contract detectors for the reader. |

No shared file is touched: `App.tsx`, `router.ts`, `surfaces.ts`, `endpoints.ts`,
`types.ts`, `SurfaceLenses.tsx` are untouched. No backend file is modified —
`knowledge/capture.py` and `knowledge/graph.py` are read, never written.

## 4. Verification

| Command | Result |
|---|---|
| `python -m pytest tests/test_knowledge_graph_provenance_boundary.py -q` | **12 passed** |
| `python -m pytest tests/test_prism_console_ci_wiring.py -q` | **30 passed** |
| `python -m pytest tests/architecture -q` | **11 passed** |
| `cd web/arkadia_console && corepack pnpm install --frozen-lockfile && corepack pnpm build` | **exit 0** — `tsc --noEmit` clean, `vite build` → `dist/assets/index-EDBkFxDO.js` (102.08 kB) |
| `python -m pytest tests/ -q -rEf --continue-on-collection-errors` | full-suite node set recorded below |

### 4.1 The negative control that drove the contract

The reader test `test_reader_declares_the_three_provenance_states` failed first
with `assert 'export type ProvenanceState = "captured" | "undeclared" | "unknown";'
in source` because the vocabulary did not exist yet. It was written as a
**negative control** — it must redden while the contract is absent and pass once
the contract lands, which is exactly what was observed. The paired control
`test_negative_control_panel_does_not_hardcode_an_origin` asserts the panel
derives its reading from the projection rather than hardcoding a source string.

## 5. Boundary semantics proven by the tests

- A note that came through the capture boundary with a declared source reads
  `captured` with that source, not a guessed one.
- A capture that declared no author reports `declared: False` — absence is
  reported as absence, never as an invented origin.
- A note with no capture record reads `unknown`, distinct from `undeclared`.
- Private-note provenance is not exposed to an anonymous caller.

## 6. Known limits / remaining uncertainty

- **No browser observation.** The sandbox has no browser; the executable evidence
  is the source-contract suite plus the production build. This is a source-side
  claim, not a rendered-UI or production-parity claim.
- `tests/test_prism_console_ci_wiring.py` derives the console-contract domain from
  `git ls-files` **at test time**, so the new guard is invisible to the domain
  until it is tracked. Parity must be measured **after** the commit that tracks
  it — measured in §4 above on the committed tree.

## 7. Next bounded task (non-overlapping)

Render the same provenance reading on the single-project detail reader
(`GET /api/knowledge/projects/{name_or_uuid}`) once its registry path builder is
available — a Workstream 1 request, not an edit.
