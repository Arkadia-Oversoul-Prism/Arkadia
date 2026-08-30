# WEAVER-MVP2-05 — Bounded Semantic Graph

## Invariant

Semantic relationships are exposed only when explicitly recorded in project-store event data. The graph remains a derived, read-only projection.

## Rules

- `REFERENCES` edges require an explicit typed ID in event data.
- Missing targets are discarded.
- Malformed event data creates no edge.
- No text similarity, embedding inference, or LLM-generated relationship is promoted.
- Provenance remains `SOURCE-BACKED` with an evidence event ID.
- The graph cannot create PassSpec, PatchApproval, or execution authority.
- Existing `/projects/{project_id}/knowledge/graph` surface remains the read-only access point.

## Deferred

Semantic inference, vector retrieval, graph persistence, autonomous graph mutation, and any new authorization semantics remain out of scope.
