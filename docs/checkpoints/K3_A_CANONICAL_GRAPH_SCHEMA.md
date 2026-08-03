# Checkpoint K3-A — Canonical Knowledge Graph Ontology

**Date:** ARK Y1 · D136 (2026-08-03)
**Role:** Implementation Steward
**Session type:** Workstream K — Checkpoint K3-A (ontology foundation only)

---

## Objective

Freeze the canonical Knowledge Graph ontology — the constitutional layer that every subsystem shares.

No features. No UI. No ingestion. No dashboard. Only the ontology.

---

## Deliverables

### Created

| File | Purpose |
|---|---|
| `knowledge/relationship_types.py` | Canonical registry for all graph relationship definitions |

### Modified

| File | Change |
|---|---|
| `knowledge/node_types.py` | Removed local `RELATIONSHIP_TYPES` definition; now imports from `relationship_types.py` |
| `knowledge/graph.py` | Removed local `RELATIONSHIP_TYPES` definition; now imports from `relationship_types.py` |
| `knowledge/vault.py` | Removed local `RELATIONSHIP_TYPES` definition; now re-exports from `relationship_types.py` |
| `knowledge/pipeline.py` | Changed `RELATIONSHIP_TYPES` import source from `vault` to `relationship_types` |

---

## What Was Found

### Pre-existing state (from previous session)

`knowledge/node_types.py` was partially created in a prior session. It contained:
- `NODE_TYPES` (canonical node list) ✅
- `TYPE_TO_DIR` mapping ✅
- `RELATIONSHIP_TYPES` (duplicate — should have been in `relationship_types.py`) ✗

`knowledge/relationship_types.py` did not exist.

`knowledge/graph.py` still had its local `RELATIONSHIP_TYPES` (9 types, narrow).

`knowledge/vault.py` still had its local `RELATIONSHIP_TYPES` (identical to graph.py — the exact duplication this checkpoint was written to resolve).

`knowledge/pipeline.py` imported `RELATIONSHIP_TYPES` from `knowledge.vault`.

### Resolution

1. Created `knowledge/relationship_types.py` as the single canonical source.
   - Defines `RelationshipDef` dataclass (identifier, display_name, direction, description)
   - Defines `RELATIONSHIP_REGISTRY` — 28 relationship types with rich metadata
   - Exports `RELATIONSHIP_TYPES` (list) and `RELATIONSHIP_TYPES_SET` (frozenset) for backward compatibility
   - Exports `validate_relationship()` helper

2. Updated `knowledge/node_types.py` to import `RELATIONSHIP_TYPES`, `RELATIONSHIP_TYPES_SET`, `validate_relationship`, and `RELATIONSHIP_REGISTRY` from `relationship_types.py` rather than defining them locally.

3. Updated `knowledge/graph.py` — removed 7-line local definition, added single import line from `relationship_types`.

4. Updated `knowledge/vault.py` — removed 4-line local definition, replaced with re-export import from `relationship_types`.

5. Updated `knowledge/pipeline.py` — changed import source from `knowledge.vault` to `knowledge.relationship_types`.

---

## Canonical Relationship Types (28 total)

| Identifier | Direction | Category |
|---|---|---|
| `created` | directed | Authorship |
| `authored_by` | directed | Authorship |
| `generated` | directed | Authorship |
| `generated_by` | directed | Authorship |
| `reviewed_by` | directed | Authorship |
| `references` | directed | Semantic |
| `derived_from` | directed | Semantic |
| `contradicts` | undirected | Semantic |
| `supported_by` | directed | Semantic |
| `inspired` | directed | Semantic |
| `inspired_by` | directed | Semantic |
| `mentions` | directed | Semantic |
| `relates_to` | undirected | Semantic |
| `connected_to` | undirected | Semantic |
| `belongs_to` | directed | Structural |
| `member_of` | directed | Structural |
| `part_of` | directed | Structural |
| `child_of` | directed | Structural |
| `parent_of` | directed | Structural |
| `follows` | directed | Structural |
| `precedes` | directed | Structural |
| `uses` | directed | Usage |
| `owns` | directed | Usage |
| `depends_on` | directed | Usage |
| `replies_to` | directed | Discourse |
| `extends` | directed | Transformation |
| `summarizes` | directed | Transformation |
| `implements` | directed | Transformation |

---

## Canonical Node Types (19 total, including legacy)

Defined in `knowledge/node_types.py`:
`document`, `conversation`, `person`, `project`, `organization`, `community`, `concept`, `scroll`, `chapter`, `place`, `timeline_event`, `media`, `task`, `note` (active) + `research`, `book`, `idea`, `decision`, `daily` (legacy — backward compatibility only).

---

## Verification

```
pytest tests/architecture -q          → 10/10 PASSED
python3 -c "from knowledge.node_types import NODE_TYPES; print('node types ok')"  → OK
python3 -c "from knowledge.relationship_types import RELATIONSHIP_TYPES; print('relationship types ok')"  → OK
grep -rn "RELATIONSHIP_TYPES\s*=" --include="*.py"  → 1 definition (relationship_types.py only)
Pre-push checklist (TODO/FIXME/XXX/HACK in source)  → CLEAN
```

---

## Architecture Tests

10/10 passing. No regressions.

---

## What K3-B Must NOT Do

- Do not modify these files unless there is a genuine ontology extension need
- Do not add a duplicate RELATIONSHIP_TYPES anywhere
- Do not define NODE_TYPES outside `knowledge/node_types.py`
- The ontology is frozen at this checkpoint; extend only via approved checkpoint

---

## Stop Condition Met

- ✅ One canonical node registry (`knowledge/node_types.py`)
- ✅ One canonical relationship registry (`knowledge/relationship_types.py`)
- ✅ Zero duplicate relationship definitions
- ✅ All repository imports unified
- ✅ 10/10 architecture tests
- ✅ Documentation updated
- ✅ Pre-push checklist clean
