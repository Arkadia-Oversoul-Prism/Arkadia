# gate-hygiene — api/main.py line-budget restoration (Phase C CEO chat extraction)

Pass: `gate-hygiene/api-main-budget-ceo-chat-extraction-01`
BASE_MAIN at reconstruction: `44f5fe38d555e36cdd895114277013f691ba57ed`
("Merge pull request #303 … ci-gate-trigger-coverage-01-followup")
Branch: `gate-hygiene/api-main-budget-ceo-chat-extraction-01`

## 1. Defect

`api/main.py` on `main` `44f5fe3` is **2602 lines**, two lines over the hard
2600-line architecture budget pinned by
`tests/architecture/test_layer_boundaries.py::test_api_main_line_count_within_budget`.
That test is red on `main`; the architecture suite is therefore **10/11**, not 11/11.

This is environment-independent debt and is reproduced below.

## 2. Change (bounded)

A pure move of the Phase C CEO chat route out of `api/main.py` into a new
module `api/ceo_chat_routes.py`, mounted back with `include_router`.

| file | change |
|---|---|
| `api/ceo_chat_routes.py` | new module; `@router.post("/api/ceo/chat")` + `async def ceo_chat(request, user=Depends(_require_auth))` |
| `api/main.py` | route body removed; `from api.ceo_chat_routes import router as _ceo_chat_router` + `app.include_router(_ceo_chat_router)` added |
| `tests/test_tool_execution_perimeter.py` | the auth-dependency pin follows the route to its new owner module |

Route path, HTTP method, request/response shape, auth dependency and behaviour
are unchanged. This is not a rewrite.

### Shared-state fidelity (load-bearing)

The original route read approval queue state that `api/main.py` had *already*
imported from `api/approval_routes` (main.py:391–392). The new module imports the
same singletons from the same owner:

```python
from api.approval_routes import (
    APPROVAL_LOCK as _APPROVAL_LOCK,
    PENDING_APPROVALS as _PENDING_APPROVALS,
)
from api.auth import get_current_user as _get_current_user, require_auth as _require_auth
```

`api/approval_routes.py:35–36` is the sole definition site
(`PENDING_APPROVALS: dict = {}`, `APPROVAL_LOCK = threading.Lock()`), so the queue
written on `/api/ceo/chat` is the same object read by `/api/approvals` and the
tool-run boundary. Mirrors the sibling `api/plan_routes.py` convention
(`from api.auth import require_auth`, hard import).

## 3. Measurements

All commands run in this clone, `PYTHONPATH=<repo>/archive/legacy_python`.

| check | `main` @ `44f5fe3` | branch |
|---|---|---|
| `wc -l api/main.py` | 2602 | **2427** |
| budget test (2600) | FAIL | **PASS** |
| architecture suite | 10/11 (1F) | **11 passed** |
| full suite (`-rEf --continue-on-collection-errors`) | 20 failed / 1482 passed / 20 skipped / 1 error | **19 failed / 1483 passed / 20 skipped / 1 error** |
| failure node-set delta | — | **-1 (budget test only), 0 new** |
| `py_compile api/main.py api/ceo_chat_routes.py` | — | OK |

The `-1` delta is exactly the budget test flipping FIXED; every other failing/error
node is identical between the two trees. The single collection error
(`tests/test_autonomy.py`, CE-01 `weaver.autonomy` module-vs-package collision) is
pre-existing and unrelated.

CP10 mutation boundary judge over the changed path set → PASS (exit 0).

## 4. Remaining uncertainty

- Cited base debt `6038989 · 804p/54f · 9/10 architecture` in the automation contract
  does **not** reproduce. Measured current main is `20F/1482P`. Stated as a
  measurement, not reconciled to stale prose.
- The full-suite failing-node set includes env/order-dependent nodes
  (`test_steward_filter`, `test_verification_review_boundary`) already documented as
  baseline debt. This pass changes none of them.
- Two stale remote branches target the same defect but have **no open PR** and are
  based on older `main` (they also carry unrelated work):
  `architecture/main-line-budget-restoration-01` (2594), `gate07/main-py-line-budget-restore`
  (2512). This pass is the minimal current-`main` fix. Sovereign may prefer to delete them.

## 5. Authorization

Ready for sovereign review and merge. No merge performed by this agent.
