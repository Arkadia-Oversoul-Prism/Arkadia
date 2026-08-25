"""
Arkadia Architecture — Layer Map
=================================
Canonical directory-to-layer assignments for the architecture fitness tests.
Update this file whenever a new subsystem or layer is added.

Referenced by: ADR-015, test_layer_boundaries.py

Layer stability order (higher number = more stable = fewer permitted dependencies):
  0 — Presentation  (least stable — depends on everything below)
  1 — API Surface
  2 — Runtime Core
  3 — Knowledge / Identity / Provider  (orthogonal stable leaves)
  4 — Storage Substrate
  5 — Constitution  (most stable — nothing depends on it)

Dependency rule: imports may only point FROM less stable layers TO more stable layers.
i.e., a file in layer N may import from layer N+1 or above (higher number = more stable),
never from layer N-1 or below (lower number = less stable).
Example: api (1) → kernel (2) is permitted. kernel (2) → api (1) is a violation.

Orthogonal layers (all at level 3) must not import from each other:
  knowledge <-> identity: forbidden
  knowledge <-> provider: forbidden
  identity  <-> provider: forbidden
"""

from pathlib import Path

# Root of the project (two levels up from this file's directory)
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent

# ── Layer assignments ────────────────────────────────────────────────────────
# Maps a path prefix (relative to PROJECT_ROOT) to its layer number.
# More specific prefixes take priority over less specific ones.

LAYER_MAP: dict[str, int] = {
    # Layer 5 — Constitution
    "docs":                 5,
    ".agents":              5,

    # Layer 4 — Storage Substrate
    "data":                 4,
    "vault":                4,

    # Layer 3 — Knowledge (orthogonal)
    "knowledge":            3,

    # Layer 3 — Identity (orthogonal)
    "api/auth.py":          3,
    "api/nodes.py":         3,
    "api/user_key_store.py": 3,
    "api/firebase_store.py": 3,

    # Layer 3 — Provider (orthogonal)
    "providers":            3,

    # Layer 3 — Key/credential substrate (stable leaves consumed by layer 1/2).
    # These are not presentation/API-surface handlers; they are the canonical
    # key-routing substrate (Pass 03 consolidation). api.key_pool is the single
    # source of truth for Gemini key selection (its own docstring; consumed by
    # api/main, solspire/provider_manager, solspire/llm). key_manager is the
    # legacy multi-key store read by the pool. provider_key_store is the
    # Settings multi-provider store read by the pool.
    "api/key_pool.py":           3,
    "api/key_manager.py":        3,
    "api/provider_key_store.py": 3,

    # Layer 2 — Runtime Core
    "kernel":               2,
    # SolSpire is the backend console kernel per the structural audit: api
    # routers mount it and api.echofeild aggregates its owner-scoped
    # primitives (Pass 01R/02R), so api(1) → solspire(2) is the correct
    # dependency direction.
    "solspire":             2,

    # Layer 1 — API Surface
    "api":                  1,   # catches all api/* not already assigned above

    # Layer 0 — Presentation
    "web":                  0,
    "bot":                  0,
    "arkadia-android":      0,
    "sonata-android":       0,
    "app":                  0,
    "static":               0,

    # Orthogonal sub-layer IDs for cross-dependency checks within level 3
    # (used by the test, not the numeric layer assignment above)
}

# Which directories belong to which orthogonal group at layer 3
ORTHOGONAL_GROUPS: dict[str, str] = {
    "knowledge":            "knowledge",
    "api/auth.py":          "identity",
    "api/nodes.py":         "identity",
    "api/user_key_store.py": "identity",
    "api/firebase_store.py": "identity",
    "providers":            "provider",
}

# ── Architectural Debt Registry ───────────────────────────────────────────────
#
# This registry records known architectural violations that exist in the
# codebase. It does NOT grant permission for them. Every entry represents
# a liability: understood, scheduled for removal, and assigned to a workstream.
#
# Freeze rule: this registry may only be edited in two cases:
#   1. New debt is intentionally introduced — rare; requires ADR justification.
#   2. Existing debt is removed — because the underlying violation has been fixed.
#
# Do not add entries to avoid a failing test. If a test fails due to a new
# violation, the correct response is to fix the import, not to register it here.
# If deferral is genuinely necessary, document the reason in an ADR first.
#
# Format: (importer_prefix, imported_prefix, "description — workstream — exit criterion")
# Remove an entry only after the violation is resolved and the fix is merged.

REGISTERED_ARCHITECTURAL_DEBT: list[tuple[str, str, str]] = [
    # ── Previously documented (Phase 1 analysis) ────────────────────────────
    # Owner: Principal Engineer | Workstream: A | Deadline: Phase 1 Gate E

    # Exit criterion: grep -n "from api" kernel/agents.py returns empty
    ("kernel/agents.py",     "api", "kernel→api: generate_verse — Workstream A, Phase 1 Gate E"),

    # Exit criterion: grep -n "from api" kernel/planner.py returns empty
    ("kernel/planner.py",    "api", "kernel→api: key_manager — Workstream A, Phase 1 Gate E"),

    # Exit criterion: grep -n "from api" kernel/tools_real.py returns empty
    ("kernel/tools_real.py", "api", "kernel→api: key_manager — Workstream A, Phase 1 Gate E"),

    # Exit criterion: grep -n "from api" kernel/jobs.py returns empty
    ("kernel/jobs.py",       "api", "kernel→api: firebase_store — Workstream A, Phase 1 Gate E"),

    # Exit criterion: grep -n "from api" kernel/goals.py returns empty
    ("kernel/goals.py",      "api", "kernel→api: firebase_store — Workstream A, Phase 1 Gate E"),

    # ── Resolved in Consolidation Pass 03 (2026-08-25) ──────────────────────
    # solspire/provider_manager.py → api.key_pool and solspire/llm.py →
    # api.key_manager were resolved by consolidating both consumers onto the
    # canonical distributed key pool (api.key_pool.acquire_key), which already
    # unions provider_key_store + key_manager + env. The upward imports are
    # gone; the registry entries are removed.
    #
    # Remaining (intentional, protected boundary): solspire/console_router.py
    # imports api.auth.require_auth (Pass 01R) — api.auth is layer 3 identity,
    # so solspire(2) → api.auth(3) is a *permitted* direction (downward toward
    # more stable), not debt.

    # ── Discovered during B0.5 calibration (2026-07-24) ─────────────────────

    # RESOLVED (Consolidation Pass 04, 2026-08-25): kernel/tts.py →
    # api.tts_key_manager. Fixed by dependency injection (ADR-014 Decision 4
    # pattern): api/main.py (composition root) injects the store accessors
    # into kernel.tts via kernel.tts.configure_key_store(); the kernel no
    # longer imports the api layer. Exit criterion met:
    # grep -n "from api" kernel/tts.py returns empty. This removes the last
    # detector-visible Layer-2→Layer-1 import in the codebase.

    # RESOLVED (Consolidation Pass 06, 2026-08-25): api/nodes.py → kernel.tools.
    # The only kernel use was len(list_tools()) for the tools_count field of
    # the public /api/codex/personal response — non-identity data, already
    # guarded by try/except with a default of 4. Removed by capability
    # injection: the composition root (api/knowledge_routes.wire_downstream_seams)
    # injects a () -> int counter via api.nodes.configure_tools_counter().
    # Without injection the fallback remains 4, identical to the previous
    # import-failure path. Identity semantics unchanged: no identity,
    # ownership, or request context ever crossed this boundary. Exit
    # criterion met: grep -n "from kernel" api/nodes.py returns empty. The
    # identity layer is now a true leaf.

    # api/main.py imports solspire.console_router (Layer 1 API → Layer 0 Presentation).
    # API surface must not depend on any presentation layer module.
    # Owner: Principal Engineer | Workstream: A | Deadline: Phase 1 Gate E
    # Exit criterion: grep -n "solspire" api/main.py returns empty
    ("api/main.py",          "solspire", "api→presentation: solspire.console_router — Workstream A, Phase 1 Gate E"),

    # providers/* import api.provider_key_store / api.key_manager (Layer 3 → Layer 1).
    # Providers are leaf adapters — they must receive keys via injection, not import them.
    # The fix is a KeyProvider interface injected at startup (see ADR-014 Decision 4).
    # Owner: Principal Engineer | Workstream: A | Deadline: Phase 1 Gate E
    # Exit criterion: grep -rn "from api" providers/ returns empty
    ("providers/",           "api", "provider→api: key_manager/provider_key_store — Workstream A, Phase 1 Gate E"),

    # RESOLVED (Consolidation Pass 05, 2026-08-25): providers/router.py →
    # knowledge.db. The only knowledge use was a single persona system-prompt
    # lookup in _resolve_persona_prompt. Removed by dependency injection: the
    # composition root (api/knowledge_routes.wire_downstream_seams, called
    # from api/main.py) injects api.knowledge_routes.resolve_persona_system_prompt
    # into providers.router.configure_persona_resolver(). Without injection the
    # router falls back to no persona prompt — identical to the old behavior
    # when the query raised or returned no row. Exit criterion met: no
    # knowledge.db import remains in providers/router.py.
]

# ── Circular Import Debt Registry ─────────────────────────────────────────────
#
# Same freeze rule as REGISTERED_ARCHITECTURAL_DEBT above.
# Format: (cycle_as_tuple, "description — workstream — exit criterion")
# A cycle is expressed as the sequence of module names the detector reports,
# starting and ending at the same node.
# Remove an entry only after the cycle is broken and the fix is merged.

REGISTERED_CIRCULAR_DEBT: list[tuple[tuple[str, ...], str]] = [
    # All previously registered kernel circular import cycles have been resolved
    # in source (Checkpoint A, conversational-spine prep) by relocating shared
    # helpers into the lowest appropriate kernel leaf module:
    #   • _summarize moved kernel.execution → kernel.tools
    #   • classify_input (+ private helpers) moved kernel.execution → kernel.intent_types
    # The former execution↔tools, execution↔planner, and execution→planner→tools
    # cycles no longer exist in the import graph. Keep this list empty until a
    # new cycle is genuinely introduced and registered with owner + exit criterion.
]
