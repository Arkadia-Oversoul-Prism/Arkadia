# PHASE 0C — PRODUCTION ISOLATION REPORT

**Verdict:** RED
**Run ID:** `86456a31`
**Host:** `https://arkadia-kw64.onrender.com`
**Started:** 2026-08-19T22:23:01.648117+00:00
**Finished:** 2026-08-19T22:23:05.184478+00:00
**User A UID:** `gYNhNFAgU5NnZSi9nCKXKdxoY5G2`
**User B UID:** `lAWaz7vozIQeFYyKPqATMR05mrF3`
**Cleanup:** OK

## Matrix

| Test | OK | Status | Detail |
|------|----|--------|--------|
| anon_status | ✅ | 200 | status=200 |
| anon_public_search | ✅ | 200 | hits=3 |
| a_create_canary | ✅ | 200 | uuid=926e9b06-2c17-4913-bad4-e798cb337b7d id=32 |
| b_create_canary | ✅ | 200 | uuid=None id=None |
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
| anon_search_a | ❌ | 200 | status=200 leaked=True |
| public_corpus_regression | ✅ | 200 | hits=5 |

## Errors

- anon_search_a: status=200 leaked=True

## Notes

Tokens and passwords are never written to this report.
Canary markers are synthetic isolation probes only.
