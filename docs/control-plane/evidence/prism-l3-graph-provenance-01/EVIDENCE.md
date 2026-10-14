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

## 7. Measured baseline (2026-10-13, base `3ca8582a`)

Full suite, one pass: `python3 -m pytest tests/ -q -rEf --continue-on-collection-errors`
→ `8 failed, 2997 passed, 20 skipped, 2 warnings, 1 error in 210.11s`.

The failing/error **node set** (9 nodes, sorted) — all pre-existing, none in the
Knowledge/lane-3 area, none attributable to this change:

```
ERROR  tests/test_autonomy.py
FAILED tests/test_ais_w2_living_gate_grove_handoff.py::test_no_firebase_persistence_in_gate
FAILED tests/test_engineering_lab_api.py::test_lab_mutation_endpoints_are_exactly_the_lab_state_set
FAILED tests/test_engineering_lab_api.py::test_lab_router_is_read_only_and_authenticated
FAILED tests/test_identity_spine_w1.py::test_node_entry_is_ais_signup_not_a_separate_diagnostic_route
FAILED tests/test_m02_reasomate_truth.py::test_oracle_runtime_uses_the_shared_session_key
FAILED tests/test_solspire_r1_governance_convergence.py::test_r1_solspire_builders_delegate_to_weaver
FAILED tests/test_solspire_r1_governance_convergence.py::test_r1_weaver_governance_is_canonical
FAILED tests/test_solspire_r3_execution_runtime.py::test_runtime_is_explicitly_non_governed_and_blocks_mutation_tools
```

node-set sha256 `c280ddc616fe4f4e9110bf4e6b6e538783a83d3764148d8a6d7ac45f6e8bc46b`.
Compare by node identity, never by counts: no node in this set references
`knowledge/` or the console reader, and every one is a pre-existing main-debt
surface (autonomy package collision, Engineering Lab API pins, SolSpire R1/R3
governance pins). Do not repair any of them inside this lane.

Targeted proof on the committed tree:
`python3 -m pytest tests/test_knowledge_graph_provenance_boundary.py tests/test_solariun_lens_contract.py -q -rEf`
→ `24 passed`.

## 8. Next bounded task (non-overlapping)


Render the same provenance reading on the single-project detail reader
(`GET /api/knowledge/projects/{name_or_uuid}`) once its registry path builder is
available — a Workstream 1 request, not an edit.

---

## 9. Authorship reader pass — and two corrections to the above (2026-10-14)

**Head SHA:** `5f363f68` (branch `feat/prism-l3-graph-provenance-01`).
**Bounded objective:** the projection attaches a **second** dimension per node —
`authorship` (`authored_by`, `authored_by_kind`, `declared`) — beside `source`.
The reader added in §3 read only `source`, so the contract's declared-authorship
dimension was invisible. Add a separate authorship reading.

### 9.1 Correction — the graph node shape for UNKNOWN (supersedes §1)

§1 above states that `_attach_provenance` attaches the *full* UNKNOWN dict
(`note_id`, `state`, `unknown`, `source`, `authorship`) to every node. **That is
wrong, and it was measured this pass.** Read the source
(`knowledge/graph.py::_attach_provenance`, lines 16–31):

```python
node["provenance"] = (
    {"state": "UNKNOWN"} if provenance.get("state") == "UNKNOWN" else provenance
)
```

The projection **narrows** an UNKNOWN capture projection to the bare literal
`{"state": "UNKNOWN"}`. So on a graph node with no capture record there is **no**
`authorship` key and **no** `source` key at all — not a present-but-empty
sub-object. (`capture.provenance_for_note` does return the full dict; the graph
projection is where the narrowing happens.) The reader must therefore tolerate the
absent key. Pinned by
`test_unknown_projection_is_narrowed_to_the_state_literal`, which asserts the node
projection is exactly `{"state": "UNKNOWN"}`. §1's dict describes
`provenance_for_note`, not the node.

### 9.2 Correction — the node delta of the authorship commit

The commit message for `5f363f68` says "was 22 before this change" and describes a
`+9` node delta. **Measured, it is +12** and the file went **12 → 24**:

```
git show 5f363f68~1:tests/test_knowledge_graph_provenance_boundary.py | grep -c '^def test_'   -> 12
grep -c '^def test_' tests/test_knowledge_graph_provenance_boundary.py                          -> 24
```

The 12 added nodes, by group: **3** handler-side projection controls
(`test_capture_with_a_declared_author_reports_it`,
`test_declared_author_with_unknown_kind_keeps_the_name`,
`test_unknown_projection_is_narrowed_to_the_state_literal`), **7** console-side
source readings, **2** negative controls. The commit message's `22` was the
12-node file plus a stale recollection; the file never held 22. Force-push is
forbidden, so the commit message stands as written and this section supersedes it.

### 9.3 Changed paths (this pass)

| Path | Change |
|---|---|
| `knowledgeContracts.ts` | adds `authorDeclared`, `summarizeAuthorship`, `authorshipReading`, `authorshipNotice`; documents the narrowed UNKNOWN node shape on `GraphNode`. |
| `KnowledgeGraphPanel.tsx` | binds the authorship reading into `GraphReading` (declared/undeclared totals + copy) and into each node row beside the origin reading. |
| `tests/test_knowledge_graph_provenance_boundary.py` | 12 new nodes (see §9.2). |

No shared file is touched (`App.tsx`, `router.ts`, `surfaces.ts`, `endpoints.ts`,
`types.ts`, `SurfaceLenses.tsx`). No backend file is modified.

### 9.4 Verification (measured on the committed tree)

| Command | Result |
|---|---|
| `python -m pytest tests/test_knowledge_graph_provenance_boundary.py -q -rEf` | **24 passed** |
| `python -m pytest tests/test_knowledge*.py -q -rEf` (10 files) | **122 passed** |
| `python -m pytest tests/architecture -q -rEf` | **11 passed** |
| `cd web/arkadia_console && corepack pnpm build` | **exit 0** — `tsc --noEmit` clean, `vite build` → `dist/assets/index-D6wL-ywD.js` (103.07 kB) |

No full-suite re-run this pulse (one-pass budget). No node in the knowledge or
architecture suites changed state, so the §7 baseline node set is unchanged by
this pass.

### 9.5 Negative control (proved on the real files, not a fixture)

1. Remove `· {authorshipReading(node)}` from the real
   `KnowledgeGraphPanel.tsx` → `1 failed, 22 passed`
   (`test_panel_row_reads_authorship_for_every_node`).
2. Collapse `summary[authorDeclared(node) ? "declared" : "undeclared"]` to a
   constant in the real `knowledgeContracts.ts` → `1 failed, 23 passed`
   (`test_authorship_summary_keys_off_the_same_predicate_as_the_reading` — a guard
   added **because** the first mutation alone did not redden the suite, so the
   original control had a blind spot).

Both files were restored byte-identically and the suite returned **24 passed**.

### 9.6 Boundary semantics proven

- Only `declared: true` **with a name present** renders as a name; the absent case
  reads `author not declared`. The reader never substitutes a placeholder, a user
  id, or the literal `unknown` for an author the boundary withheld.
- A declared actor whose `authored_by_kind` is `unknown` keeps its name and reports
  the kind as unknown — the reader does not upgrade it to `human`.
- Authorship stays distinct from origin: a note can carry a declared source and no
  declared author, and the two readings do not collapse into one enum.

### 9.7 Known limits

- **No browser observation.** Source-contract suite plus production build only; a
  source-side claim, not a rendered-UI or production-parity claim.
- `tests/test_prism_console_ci_wiring.py` derives the console-contract domain at
  test time; the new nodes are inside an already-tracked file, so the domain is
  unchanged and no wiring edit was needed.
