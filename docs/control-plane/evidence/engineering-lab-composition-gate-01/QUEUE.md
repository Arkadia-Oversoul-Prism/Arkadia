# Queue reconciliation — overlapping open drafts

Two pairs of open drafts overlap on the same file. Neither pair was combined this
pass; the analysis below is recorded so the next bounded unit starts from measurement
rather than a fresh inventory.

## #542 + #543 — `api/knowledge_routes.py`

| PR | Head | Files |
|---|---|---|
| #542 | `934037d9b8` | `api/knowledge_routes.py`, `knowledge/graph_health.py`, `tests/test_knowledge_graph_health_owner_scope.py`, evidence |
| #543 | `1a4b71aa37` | `api/knowledge_routes.py`, `knowledge/timeline.py`, `tests/test_knowledge_timeline_boundary.py` |

Both edit `api/knowledge_routes.py`, so they **must** be composed rather than merged
in sequence. #542 scopes graph analytics to the caller's accessible subgraph; #543
bounds the timeline read limit at both ends. They touch different handlers in the same
module, so a textual union is likely — but "likely" is not a measurement, and the
combined tree still needs its own exact-head validation.

## #538 + #544 — `solspire/buyer_recon.py`

| PR | Head | Files |
|---|---|---|
| #538 | `1a36f23536` | `solspire/buyer_recon.py`, `tests/test_prism_opportunity_entry_flow.py`, `AGENTS.md`, evidence |
| #544 | `73575cd781` | `solspire/buyer_recon.py`, `tests/test_prism_opportunity_entry_flow.py`, `AGENTS.md`, evidence |

#538 repairs `update_entry` status normalization (DEFECT 3); #544 repairs `update_entry`
silently dropping an evidence patch. Both touch the **same function** and the **same
test file** and the **same `AGENTS.md`**, so this pair has the higher conflict risk of
the two. It is the natural next bounded unit: one combined `update_entry` repair with
one evidence-backed candidate and one exact-head validation.

## Everything else

45 open PRs, all drafts, no eligibility labels. Each remaining PR is classified
integrate / combine / repair / hold / close only after its own exact-head measurement;
no PR in this set was touched by this pass.
