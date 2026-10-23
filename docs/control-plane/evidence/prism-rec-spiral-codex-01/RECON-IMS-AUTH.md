# Recon finding — IMS authorization asymmetry (proposed, NOT repaired)

Found during BUILD N recon for PRISM-REC-SPIRAL-CODEX-01. **Out of that slice's scope and
sovereign-gated: recorded, not repaired.** `api/ims_products.py` is an authorization surface;
repairing it is an authority-boundary change, not a UI reconciliation.

Measured at `main` `68403b9e`, canonical origin `https://arkadia-qzu4.onrender.com`.

## Observation

`api/ims_products.py` defines two POST endpoints with **no authentication dependency**, while
their sibling GET in the same product family requires a sovereign key:

| Route | Method | Auth in source | Observed |
|---|---|---|---|
| `/api/ims/inquiries` | GET | `x-sovereign-key` check → 403 | **403** |
| `/api/ims/diagnostic` | POST | none | **500** (handler executed) |
| `/api/ims/archetypal-analyze` | POST | none | not probed |

- `api/ims_products.py:27` — `router = APIRouter()` with **no** router-level dependency.
- `api/main.py:315` — `app.include_router(_ims_products_router)` with **no** `dependencies=`.
- `api/ims_products.py:256` — `async def run_ims_diagnostic(request: Request)` — the only
  parameter is the request; no `Depends(...)`.
- Contrast `api/main.py:2093` — `get_ims_inquiries` reads `x-sovereign-key` and raises 403.

## Evidence that the handler ran unauthenticated

An **anonymous** POST with a malformed body returns **500**, not 401/403:

```
POST /api/ims/diagnostic  body='{'   -> HTTP 500  "Internal Server Error"
GET  /api/ims/inquiries               -> HTTP 403   (gated control)
GET  /solspire/projects               -> HTTP 401   (gated control)
```

A 500 (not 401/403) is the tell that authorization did not reject the request and the handler
body executed. The malformed body fails at `await request.json()`, **before** `_gemini()` and
before any persistence, so this probe is **non-mutating by construction**.

## What was NOT tested

**The write effect is NOT TESTED.** The handler reaches `_save(IMS_DIAG_FILE, diagnostics)`
and `_fb_save("ims_diagnostics", ...)` **after** the model call
(`api/ims_products.py:329-334`). No well-formed request was sent, so no record was created
and no durable state was observed to change. The claim is exactly:

> an anonymous caller can reach the handler body of a mutating endpoint

and **not** "anonymous callers can write records" — that would require executing a real
diagnostic, which is a consequential action outside this authorization.

## Why it matters

`/api/ims/diagnostic` performs an LLM call and **writes** to `data/ims_diagnostics.json` plus
Firebase, keyed by a caller-supplied `mbti_type` and four free-form layers. If reachable
anonymously, that is an unauthenticated compute-and-persist surface in a product family whose
sibling is sovereign-gated. The asymmetry itself is the finding; the severity is unassessed.

## Proposed bounded repair (sovereign-gated)

Add the same gate the sibling uses (`x-sovereign-key` → 403), or a `Depends` on the router,
then re-probe: the anonymous malformed POST must move from **500 → 401/403**. A regression
test should carry a negative control proving the probe still returns 500 when the gate is
removed, so the test cannot pass vacuously.

**Do not repair this inside a UI reconciliation slice.** Recorded for the sovereign to
authorize; discovery does not authorize execution.
