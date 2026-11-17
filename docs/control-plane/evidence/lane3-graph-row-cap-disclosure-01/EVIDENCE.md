# Lane 3 — the knowledge-graph row cap discloses its own bound

**Lane:** 3 (Solariun + Knowledge OS).
**Base:** freshly fetched `main` `f9bd8da913fa194d7cff2e53b9c417ddb2a9f43a`.
**Branch:** `lane3/graph-row-cap-disclosure-01`.
**Authority:** opened under `11 — LANE NEW-PR AUTHORIZATION` (N1–N8 below). Merge,
deployment, and acceptance remain human-only (GOV-03).

## 1. The defect, measured

`web/arkadia_console/src/pages/knowledge/KnowledgeGraphPanel.tsx` renders the
per-node provenance rows with a bare `slice`:

```tsx
const PROVENANCE_ROWS = 8;
...
{graph.nodes.slice(0, PROVENANCE_ROWS).map((node) => ( ... ))}
```

The `Facts` block directly above it prints the **exact** node count
(`{ label: "nodes", value: String(summary.nodes) }`). So a reader of a 40-node
scope sees "nodes 40" and eight rows, with nothing saying the list was cut. The
prefix reads as the complete record — the same silent-cap class the Lab names in
`web/arkadia_console/src/components/lab/renderClip.ts` ("a bare `slice` breaks
that convention silently").

Measured at the base revision: `grep -nE "showing|Showing|hidden|truncat|of \$"
KnowledgeGraphPanel.tsx` → **0** matches. There was no disclosure.

## 2. The repair (feature-local, no shared file)

| File | Change |
|---|---|
| `.../pages/knowledge/knowledgeContracts.ts` | adds `boundedRowNotice(shown, total)` — the one place the disclosure copy is composed; returns `null` when nothing was withheld |
| `.../pages/knowledge/KnowledgeGraphPanel.tsx` | binds the notice to the same constant the `slice` uses and renders it at `data-testid="knowledge-graph-rows-bounded"` |

Both files are Lane 3's exclusive ownership (SHARED-CONTRACTS §1: "Solariun/Knowledge
OS page modules and feature-local components"). No shared shell, registry, router,
or endpoint file is touched. No backend file is touched.

## 3. Proof

Targeted suite — `tests/test_knowledge_graph_provenance_boundary.py` (the existing
Lane 3 provenance guard, already in the derived console-contract domain):

```
$ python -m pytest tests/test_knowledge_graph_provenance_boundary.py -q -rEf
29 passed          # was 24; +5 = exactly the new nodes
```

The derived console-contract domain still passes in full, so the guard is executed
by the same gate that judged it before:

```
$ python -m pytest -q $(python scripts/console_contract_domain.py) -rEf
1173 passed
```

Frontend build:

```
$ cd web/arkadia_console && corepack pnpm install --frozen-lockfile && corepack pnpm build
✓ built in 2.29s
```

Architecture fitness:

```
$ python -m pytest tests/architecture -q
11 passed
```

### Negative controls (live, on the real files)

Both polarities bite; the files were restored byte-identically afterwards
(`KnowledgeGraphPanel.tsx` md5 `33e52ac652bb3f9b2f41ef5db5f4ea96`,
`knowledgeContracts.ts` md5 `ee50ed25f4f8bfccd5fc308b9bed5fd3`).

1. **A notice that never fires** — bind it to `(PROVENANCE_ROWS, PROVENANCE_ROWS)`
   so `total <= shown` is always true:
   `1 failed, 28 passed` (`test_panel_discloses_the_row_cap`).
2. **A notice that always fires** — replace the guard with `if (false) return null;`:
   `1 failed, 28 passed` (`test_bounded_notice_is_silent_when_nothing_is_withheld`).

A detector that reports unconditionally, or one that never reports, cannot pass
both. The control in the test file feeds the pre-repair shape (a bare `slice` with
no notice) and asserts the property is false for it.

## 4. N1–N8 justification

- **N1 — reconciliation exhausted.** Measured live at `main` `f9bd8da9`: 5 open PRs,
  all drafts with green checks (#663 lane-currency, #664 lane 4, #665 lane 1,
  #666 lane 2, #657 unassigned governance). No eligible merge is available to an
  agent — GOV-03 makes every merge human-only (§5 below). No actionable dependency
  or safe bounded repair on another lane's PR remains.
- **N2 — lane holds no open PR.** Lanes 1, 2, and 4 each hold one; **lane 3 holds
  none** (verified against the live PR list, not the snapshot).
- **N3 — ownership.** Both paths are Lane 3's exclusive ownership.
- **N4 — base.** Branched from freshly fetched `main` `f9bd8da9`.
- **N5 — bounded scope.** One objective: a bounded row list discloses its bound.
- **N6 — continuation, not duplication.** No open or merged PR repairs this defect
  (`git log --oneline origin/main -- .../KnowledgeGraphPanel.tsx` shows no such
  change; #664 repaired the same class in *lane 4's* files only).
- **N7 — evidence plan.** Targeted suite + domain suite + build + two live negative
  controls, bound to this commit.
- **N8 — boundaries preserved.** No protected authority, identity, K15/K3,
  approval-enforcement, constitutional architecture, or deployment config touched.

## 5. Authority contradiction recorded (hard stop on merge)

This pulse's prompt grants Weaver bounded merge authority with
`REVISION_DATE := 2026-10-28`. The repository's **current** canonical rule is
GOV-03, merged as `e0f85052` (2026-11-16) and present on `main` at
`AGENTS.md` and `SHARED-CONTRACTS.md §9`:

> all GitHub pull-request merge execution is human-only. No agent, Weaver worker,
> scheduler, OpenHands process, provider adapter, or automation may execute a merge.

The runtime refusal boundary is live: `weaver/execution_adapter.py::ForbiddenMergeAdapter.merge()`
raises `RuntimeError("merge is human-only")`. The repository also carries a prior
incident record for an agent-executed merge:
`docs/control-plane/evidence/unauthorized-merge-3a1088c5-01/INCIDENT.md`.

Per the contract's own rule — "If canonical topology, provenance, authorization
records, or required evidence is contradictory, HARD STOP the affected operation and
report the contradiction" — **no merge is executed by this pulse.** The open PRs are
recorded as eligibility-assessed only. This PR stays a **draft**.

## 6. Remaining known red on `main` (recorded, not repaired)

- `lane-doc-currency` is **red on `main` `f9bd8da9`** (`scripts/lane_state.py --check`
  exit 1: the snapshot's `base_main` `19697a6a` predates `51a19ae6`/`0f174e90`, which
  edited guarded lane docs). PR #663 is the existing repair and is green; it is
  eligible for human consideration.
- `console-contract` is **red on `main` `f9bd8da9`** in the `exercise_mission_workspace.py`
  step (`authorization record did not report human origin`). It is a Lab authority
  surface (`api/lab_routes.py`, `lab/`) — sovereign-only; recorded, not repaired here.

Neither is touched by this PR, and neither is a Lane 3 surface.
