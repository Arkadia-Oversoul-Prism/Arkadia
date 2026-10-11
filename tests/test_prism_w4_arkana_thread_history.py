"""Arkana thread-history read-only slice — frontend source contract (Workstream 4).

The console's Arkana surface now shows first-class thread history read from the
verified `/api/commune/threads` contract. This guard binds the *slice* to the
things that make that claim real, at the source level (this repository's frontend
test convention — see `tests/test_prism_w4_lab_read_model.py`):

  * the **backend contract** the slice reads: both `GET` routes are declared by
    `api/commune_threads.py`, require an identity, and answer `200` empty (never
    an error) when the identity owns nothing — which is why an empty state must
    render distinctly from a failure;
  * the **read-only ceiling**: the slice issues no mutating request and does not
    reference the mutating thread routes at all (open / rename / append are human
    acts, deliberately not wired);
  * the **single declared base**: the parameterised sub-resource path is built
    from `endpoints.arkanaThreads`, never a restated literal.

Negative controls prove each detector fires on the defect it exists to catch.
"""
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONSOLE = ROOT / "web" / "arkadia_console" / "src"
PAGE = CONSOLE / "pages" / "ArkanaPage.tsx"
COMPONENT = CONSOLE / "components" / "arkana" / "ArkanaThreadHistory.tsx"
CONTRACT = CONSOLE / "components" / "arkana" / "arkanaThreadsContract.ts"
ENDPOINTS = CONSOLE / "lib" / "endpoints.ts"
HANDLER = ROOT / "api" / "commune_threads.py"

MUTATING_METHODS = ("POST", "PUT", "PATCH", "DELETE")

#: The mutating thread verbs the read-only slice must not reach for.
MUTATING_THREAD_MARKERS = ("method: \"POST\"", "method: 'POST'", "/threads\", {\n", "rename")


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


# ---------------------------------------------------------------------------
# Detectors (each has a negative control below)
# ---------------------------------------------------------------------------


def mutating_calls(text: str) -> list[str]:
    """Every mutating HTTP method a module explicitly asks for."""
    return [m.group(1) for m in re.finditer(r'method\s*:\s*"([A-Z]+)"', text) if m.group(1) in MUTATING_METHODS]


def hydration_path_arguments(text: str) -> list[str]:
    """The first argument of every ``useHydration<…>(`` call in a module."""
    return re.findall(r"useHydration<[^>]*>\(\s*([^,\n]+)", text)


def registry_anchored(paths: list[str]) -> bool:
    """Every hydration path derives from the declared registry object."""
    return all(p.strip().startswith("endpoints.") for p in paths)


# ---------------------------------------------------------------------------
# The slice is mounted on the Arkana page
# ---------------------------------------------------------------------------


def test_arkana_page_renders_the_thread_history_slice():
    page = _read(PAGE)
    assert 'import { ArkanaThreadHistory }' in page
    assert "<ArkanaThreadHistory />" in page


# ---------------------------------------------------------------------------
# Read-only ceiling
# ---------------------------------------------------------------------------


def test_slice_issues_no_mutating_request():
    assert mutating_calls(_read(COMPONENT)) == []


def test_slice_does_not_reference_the_mutating_thread_verbs():
    component = _read(COMPONENT)
    for marker in MUTATING_THREAD_MARKERS:
        assert marker not in component, f"read-only slice reaches for the mutating marker {marker!r}"


def test_negative_control_detector_flags_a_mutating_slice():
    """The detector must report the defect it exists to catch."""
    assert mutating_calls('apiRequest(p, { method: "POST", body: "{}" })') == ["POST"]
    assert mutating_calls('apiRequest(p, { method: "PATCH" })') == ["PATCH"]
    assert mutating_calls('apiRequest(p, { method: "GET" })') == []
    assert mutating_calls("apiRequest(p)") == []


# ---------------------------------------------------------------------------
# One declared base: the sub-resource is built from the registry
# ---------------------------------------------------------------------------


def test_declared_collection_is_the_registry_entry():
    assert 'arkanaThreads: "/api/commune/threads"' in _read(ENDPOINTS)


def test_every_hydration_path_is_registry_anchored():
    paths = hydration_path_arguments(_read(COMPONENT))
    assert paths, "the slice performs no hydration read -- the guard would be vacuous"
    assert registry_anchored(paths), f"non-registry hydration path(s): {paths}"


def test_messages_sub_resource_is_derived_from_the_collection():
    component = _read(COMPONENT)
    assert "endpoints.arkanaThreads" in component
    assert "/messages" in component
    # The base is never restated as a literal in the slice.
    assert '"/api/commune/threads' not in component


def test_negative_control_detector_flags_a_restated_literal():
    assert registry_anchored(['endpoints.arkanaThreads + "/x/messages"']) is True
    assert registry_anchored(['"/api/commune/threads/x/messages"']) is False
    assert registry_anchored(["p"]) is False


# ---------------------------------------------------------------------------
# Honest states
# ---------------------------------------------------------------------------


def test_slice_distinguishes_empty_from_failure():
    component = _read(COMPONENT)
    # Empty is rendered only on a ready read; a failure uses the shared state panel.
    assert 'threads.state === "ready"' in component
    assert "arkana-threads-empty" in component
    assert "arkana-thread-empty" in component
    assert "<ContractState" in component


def test_slice_reuses_the_shared_state_classifier():
    """Loading / auth-required / unavailable / read-failed are classified once, by
    the shared hook -- the slice must not invent its own error strings."""
    component = _read(COMPONENT)
    assert 'from "../../lib/useHydration"' in component
    assert "useHydration<" in component


def test_slice_does_not_assume_the_resonance_role_vocabulary():
    """The thread contract emits `user` / `arkana` -- not `assistant`."""
    assert 'role === "user" ? "you" : "arkana"' in _read(COMPONENT)
    contract = _read(CONTRACT)
    assert 'export type ArkanaThreadRole = "user" | "arkana";' in contract
    assert '"assistant"' not in contract


def test_contract_does_not_leak_the_owner_field():
    """`_public_thread` omits `user_id`; the client type must not declare it.

    Scoped to a property declaration so the module's prose (which *names* the
    omitted field to explain why it is omitted) is not itself the defect.
    """
    contract = _read(CONTRACT)
    assert re.search(r"^\s*user_id\??\s*:", contract, re.M) is None


# ---------------------------------------------------------------------------
# The backend contract the slice binds to
# ---------------------------------------------------------------------------


def test_backend_declares_get_list_and_messages_routes():
    handler = _read(HANDLER)
    assert '@router.get("")' in handler
    assert '@router.get("/{thread_uuid}/messages")' in handler
    assert 'prefix="/api/commune/threads"' in handler


def test_backend_reads_require_an_identity():
    handler = _read(HANDLER)
    assert 'raise HTTPException(status_code=401, detail="Authentication required")' in handler
    # `_user_id` is called by every read route.
    assert handler.count("await _user_id(request)") >= 3


def test_backend_empty_list_is_a_success_not_a_404():
    """`list_threads` returns `[]` for an identity that owns nothing; the handler
    wraps it in `{"threads": []}`. No 404 path exists for an empty collection."""
    handler = _read(HANDLER)
    assert 'return {"threads":' in handler
    vault = _read(ROOT / "knowledge" / "vault.py")
    assert "return []" in vault.split("def list_threads", 1)[1].split("def get_thread", 1)[0]
