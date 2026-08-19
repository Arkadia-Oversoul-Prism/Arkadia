# PHASE 0C — PRODUCTION ISOLATION REPORT

**Verdict:** GREEN
**Run ID:** `ef07d6b7`
**Host:** `https://arkadia-kw64.onrender.com`
**Started:** 2026-08-19T22:48:32.302273+00:00
**Finished:** 2026-08-19T22:48:54.461720+00:00
**User A UID:** `BLc7JcytC9PdaKU3XQXypaXgYQ83`
**User B UID:** `QgJlxsGk1KfRdnwkdlbwaWq5D3h2`
**Cleanup:** OK

## Matrix

| Test | OK | Status | Detail |
|------|----|--------|--------|
| anon_status | ✅ | 200 | status=200 |
| anon_public_search | ✅ | 200 | hits=3 |
| a_create_canary | ✅ | 200 | uuid=c40a7f9e-7dd0-4417-befc-4319457cc517 id=33 |
| b_create_canary | ✅ | 200 | uuid=b1aaba6d-4c25-4c5b-85e2-06659fc4dd90 id=34 |
| a_get_note | ✅ | 200 | status=200 |
| a_get_node | ✅ | 200 | status=200 |
| a_traverse | ✅ | 200 | status=200 nodes=1 |
| a_full_graph | ✅ | 200 | status=200 |
| a_search | ✅ | 200 | status=200 |
| b_get_a_note | ✅ | 404 | status=404 leaked=False |
| b_get_a_node | ✅ | 404 | status=404 leaked=False |
| b_traverse_a | ✅ | 200 | status=200 nodes=0 |
| b_graph_no_a | ✅ | 200 | status=200 leaked=False |
| b_search_a_marker | ✅ | 200 | status=200 leaked=False |
| b_timeline_no_a | ✅ | 200 | status=200 leaked=False |
| a_get_b_note | ✅ | 404 | status=404 leaked=False |
| a_search_b_marker | ✅ | 200 | status=200 leaked=False |
| anon_get_a_note | ✅ | 404 | status=404 leaked=False |
| anon_search_a | ✅ | 200 | status=200 leaked=False |
| anon_get_b_note | ✅ | 404 | status=404 leaked=False |
| anon_search_b | ✅ | 200 | status=200 leaked=False |
| anon_graph_no_private | ✅ | 200 | leaked_a=False leaked_b=False |
| anon_timeline_no_private | ✅ | 200 | status=200 |
| a_oracle_seed | ✅ | 200 | status=200 memory=True |
| a_oracle_retrieve | ✅ | 200 | status=200 marker_in_response=True |
| b_oracle_no_a_marker | ✅ | 200 | status=200 leaked=False |
| anon_oracle_no_a_marker | ✅ | 200 | status=200 leaked=False |
| public_corpus_regression | ✅ | 200 | hits=5 |

## Errors

- none

## Notes

Tokens and passwords are never written to this report.
Canary markers are synthetic isolation probes only.
