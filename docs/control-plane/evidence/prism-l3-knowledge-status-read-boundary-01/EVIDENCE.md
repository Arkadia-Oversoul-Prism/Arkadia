# Lane 3 — Knowledge OS status read: a `200` can carry a failed read

**Workstream:** Prism UI reconciliation, Lane 3 (Solariun & Knowledge OS).
**Branch:** `feat/prism-l3-knowledge-status-read-boundary-01`
**Base:** `main` @ `2a1bca755bd6e93413ccbe78790e65d3aec1c2b1`
**Status:** IMPLEMENTED — tests + build measured; no runtime/production claim.

## 1. The defect

`GET /api/knowledge/status` → `api.knowledge_routes.knowledge_os_status` wraps its whole
body in `try: … except Exception as e: return {"status": "error", "detail": str(e)}`.

That `except` branch **returns**. FastAPI therefore serves it with **HTTP 200**, and the
envelope carries **no** `vault`, `graph` or `timeline` block. The transport cannot carry
the distinction between "the vault is healthy and empty" and "the vault read failed".

`KnowledgePage` read the body through an unvalidated typed request and dereferenced
`status.data.vault.notes` in the vault-status panel. On the handler's failure envelope that
is a **render crash** — and a dead vault was indistinguishable from an unread one.

Measured live (this pulse, `main` @ `2a1bca7`): forcing the vault read to raise yields
`200 {"status":"error","detail":"simulated vault failure"}`; the handler's real success body
carries `status: "operational"` plus all three blocks.

## 2. The change

| File | Change |
|---|---|
| `web/arkadia_console/src/pages/knowledge/knowledgeContracts.ts` | `isKnowledgeStatusReading()` (already present) plus a new pure reader `requireKnowledgeStatusReading(payload)`, which returns a validated reading or throws with the handler's own failure detail |
| `web/arkadia_console/src/pages/KnowledgePage.tsx` | `readStatus` is now a thin fetch wrapper over `requireKnowledgeStatusReading`, converting the refusal into an `ApiError` with `kind: "UNKNOWN"` |
| `tests/test_knowledge_status_read_boundary.py` | New guard (14 tests) |

The reader is **pure** — it takes the parsed body, not a path — so the contract is
executable in isolation rather than only string-matched in source.

## 3. Evidence

| Command | Result |
|---|---|
| `python -m pytest tests/test_knowledge_status_read_boundary.py -q -rEf` | **14 passed** |
| `python -m pytest tests/architecture -q` | **11 passed** |
| `python -m pytest -q $(python scripts/console_contract_domain.py)` | **458 passed** |
| `corepack pnpm build` (in `web/arkadia_console`) | **tsc clean, build OK** — `dist/assets/index-ByxKH3QV.js` 106.65 kB |

The guard is in the derived console-contract domain: `scripts/console_contract_domain.py`
returns **26** paths including `tests/test_knowledge_status_read_boundary.py`, and
`.github/workflows/prism-console-contract.yml` executes `pytest -q $(python scripts/console_contract_domain.py)`
— so the gate runs it with no workflow edit, and `tests/test_prism_console_ci_wiring.py`
(**30 passed**) judges that wiring.

## 4. The guard's oracle is falsifiable

The defect assertion (`test_the_200_error_envelope_does_not_validate_as_a_reading`) is a
`False` assertion, which a reader that rejected *everything* would satisfy vacuously. Three
controls close that:

1. `test_the_reader_returns_the_reading_on_a_healthy_body` — the reader yields the real
   `vault.notes` on the handler's own success body (read from the handler, not restated).
2. `test_negative_control_the_naive_reader_dereferences_the_error_envelope` — the Node probe
   reproduces the pre-fix read (`errorEnvelope.vault.notes`) and asserts it **throws
   `TypeError`**. If the defect's shape moves, this control stops throwing and the guard is
   shown stale rather than silently passing.
3. `test_negative_control_the_status_surface_routes_through_the_shared_reader` — the page
   seam is asserted over the `readStatus` body, so a cosmetic rewrite of the line cannot
   drop the guard (the first draft pinned an exact literal and a one-token edit dodged it).

## 5. Not claimed

- No production/runtime observation. Render at `https://arkadia-qzu4.onrender.com` is the
  sole canonical origin (ADR-016); this pulse performed no deployment and claims no
  acceptance.
- The handler's `except` branch still returns `200`. Changing the **transport** (a non-2xx
  status, or a `{ok: false}` envelope) is a backend contract change affecting every consumer
  and is **not** in this bounded slice. This slice makes the *reader* honest about the body it
  already receives.
- `api/main.py` is untouched (2600-line budget unaffected).

## 6. Boundary

Lane 3 owns Solariun/Knowledge OS page modules and their feature-local components/tests.
This slice touches only Lane-3 files plus a new Lane-3 test. No file owned by Lanes 1, 2 or 4
was edited. Human retains merge, deployment and acceptance authority.
