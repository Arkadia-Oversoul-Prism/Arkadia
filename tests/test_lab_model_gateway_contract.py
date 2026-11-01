"""Workstream 4 — model gateway surface contract (read-only ceiling + wiring).

Source-level guards for `components/lab/LabModelGateway.tsx` and its projection
`labGateway.ts`. They pin the properties a behavioural test cannot see from the
handler alone: that the surface is wired to the *declared* registry entry, that
it issues no request of its own beyond that entry, that it asks for no mutating
method, and that its projection stays pure.

The state-vocabulary guard reads the handler's own declarations rather than
restating them, so a class or status added to the gateway cannot be silently
mislabelled by the console.
"""
from __future__ import annotations

import re
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
LAB_SRC = REPO_ROOT / "web" / "arkadia_console" / "src" / "components" / "lab"
PAGE = REPO_ROOT / "web" / "arkadia_console" / "src" / "pages" / "EngineeringLabPage.tsx"
GATEWAY_TS = LAB_SRC / "labGateway.ts"
GATEWAY_TSX = LAB_SRC / "LabModelGateway.tsx"
ENDPOINTS_TS = REPO_ROOT / "web" / "arkadia_console" / "src" / "lib" / "endpoints.ts"
GATEWAY_HANDLER = REPO_ROOT / "lab" / "engineering_lab" / "gateway.py"


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


# ---------------------------------------------------------------------------
# Read-only ceiling


def test_surface_is_wired_to_the_declared_registry_entry():
    """The surface must read the registry, not inline the path.

    `labGateway` is already a registry member (Workstream 1 owns the file), so no
    registry edit is needed for this slice — which is the whole reason this
    surface was chosen next.
    """
    source = _read(GATEWAY_TSX)
    assert "endpoints.labGateway" in source
    assert "/api/lab/engineering/gateway" not in source
    assert 'labGateway: "/api/lab/engineering/gateway"' in _read(ENDPOINTS_TS)


def test_surface_fetches_nothing_beyond_its_declared_entry():
    """One GET to one declared entry; no second reader of the contract."""
    source = _read(GATEWAY_TSX)
    assert source.count("useHydration<") == 1
    assert source.count("apiRequest<") == 1
    assert "fetch(" not in source


def test_surface_requests_no_mutating_method():
    """No execution, selection, authorization, or deployment control."""
    source = _read(GATEWAY_TSX) + _read(GATEWAY_TS)
    for forbidden in ('method: "POST"', 'method: "PUT"', 'method: "DELETE"', "method: 'POST'"):
        assert forbidden not in source
    for path in ("/engineering/n-atlas/run", "/engineering/voice/resolve", "/execute", "/authorize"):
        assert path not in source


def test_projection_is_pure():
    """The projection imports nothing — so it cannot reach a client or a store."""
    source = _read(GATEWAY_TS)
    assert not re.search(r"^\s*import\b", source, re.MULTILINE), "projection must import nothing"
    for token in ("fetch(", "apiRequest", "useHydration", "localStorage", "window."):
        assert token not in source


def test_no_control_that_could_select_or_run_a_model():
    """The surface renders readings, not actions.

    A `<button>` here would imply the console can select or invoke a provider,
    which is a mutating act it holds no authority for.
    """
    source = _read(GATEWAY_TSX)
    assert "<button" not in source
    assert "onClick" not in source
    assert "onSubmit" not in source


def test_mounted_on_the_engineering_lab_page():
    page = _read(PAGE)
    assert "LabModelGateway" in page
    assert "<LabModelGateway />" in page


# ---------------------------------------------------------------------------
# State vocabulary conformance (read from the handler, not restated)


def _gateway_dict(source: str, name: str) -> dict[str, str]:
    match = re.search(rf"{name}:\s*dict\[str,\s*str\]\s*=\s*\{{(.*?)\}}", source, re.DOTALL)
    assert match, f"gateway.py declares no {name} mapping"
    return dict(re.findall(r'"([a-z_0-9]+)":\s*"([A-Z_]+)"', match.group(1)))


def test_projection_config_classes_equal_the_handler_s_classes():
    """Equality, not subset: a class the console adds would be an invented grouping."""
    handler_classes = set(_gateway_dict(_read(GATEWAY_HANDLER), "CONFIG_CLASSES").values())
    assert handler_classes, "control premise: CONFIG_CLASSES must be non-empty"

    match = re.search(r"CONFIG_CLASSES:\s*readonly string\[\]\s*=\s*\[(.*?)\]", _read(GATEWAY_TS), re.DOTALL)
    assert match, "the projection declares no CONFIG_CLASSES list"
    projected = set(re.findall(r'"([A-Z_]+)"', match.group(1)))
    assert projected == handler_classes, f"class vocabulary drift: {projected ^ handler_classes}"


def test_projection_groups_are_the_handler_s_groups():
    """The three group keys the projection reads must be `ModelGateway.to_dict()`'s."""
    handler = _read(GATEWAY_HANDLER)
    for group in ("local_providers", "remote_providers", "agent_providers"):
        assert f'"{group}"' in handler, f"gateway.py no longer emits {group}"

    match = re.search(r"PROVIDER_GROUPS\s*=\s*\[(.*?)\]", _read(GATEWAY_TS), re.DOTALL)
    assert match, "the projection declares no PROVIDER_GROUPS"
    projected = set(re.findall(r'"([a-z_]+)"', match.group(1)))
    assert projected == {"local_providers", "remote_providers", "agent_providers"}


def test_projection_available_status_is_the_handler_s_status():
    """`AVAILABLE` must be the status string the handler actually emits."""
    handler = _read(GATEWAY_HANDLER)
    assert 'status="AVAILABLE"' in handler
    assert 'AVAILABLE_STATUS = "AVAILABLE"' in _read(GATEWAY_TS)


def test_projection_does_not_hardcode_a_provider_name():
    """A provider list in the projection would drift from the handler's registry.

    Provider names are runtime data; the projection must group by `config_class`.
    """
    source = _read(GATEWAY_TS)
    for provider in ("gemini", "ollama", "n_atlas", "anthropic_compatible", "llama_cpp"):
        assert f'"{provider}"' not in source, f"the projection hardcodes provider {provider}"


def test_negative_control_class_detector_sees_a_divergent_value():
    handler_classes = set(_gateway_dict(_read(GATEWAY_HANDLER), "CONFIG_CLASSES").values())
    assert "HYBRID" not in handler_classes
    assert {"HYBRID"} - handler_classes == {"HYBRID"}


def test_negative_control_purity_detector_sees_an_import():
    """The purity detector must fire on an import if one were added."""
    polluted = 'import { apiRequest } from "../../lib/apiClient";\nexport const x = 1;\n'
    assert re.search(r"^\s*import\b", polluted, re.MULTILINE)


def test_negative_control_wiring_detector_sees_an_inlined_path():
    """The wiring detector must fire on an inlined path if one were added."""
    inlined = 'const p = "/api/lab/engineering/gateway";'
    assert "endpoints.labGateway" not in inlined


# ---------------------------------------------------------------------------
# The handler contract this surface depends on


def test_handler_route_and_auth_are_what_the_slice_claims():
    """`GET /engineering/gateway` under the Lab router, authenticated by default.

    The router carries a default `require_lab_auth` dependency and this path is
    not one of the two public tester paths, so the surface is owner-scoped by the
    same boundary as the rest of the Lab.
    """
    source = _read(REPO_ROOT / "api" / "lab_routes.py")
    assert '@router.get("/engineering/gateway")' in source
    assert 'router = APIRouter(prefix="/api/lab"' in source
    assert "dependencies=[Depends(require_lab_auth)]" in source

    public = re.search(r"_PUBLIC_NATLAS_PATHS\s*=\s*\{(.*?)\}", source, re.DOTALL)
    assert public, "lab_routes.py declares no _PUBLIC_NATLAS_PATHS"
    assert "/api/lab/engineering/gateway" not in public.group(1)


def test_handler_returns_a_description_not_an_authority():
    """`describe_gateway` must remain a description.

    If the handler ever gained a mutating side effect, this surface's read-only
    claim would be wrong even though its own code is unchanged. The body is read
    with `ast` rather than a regex, so the guard follows the function wherever it
    moves and cannot be satisfied by a matching comment.
    """
    import ast

    tree = ast.parse(_read(GATEWAY_HANDLER))
    fn = next(
        (node for node in ast.walk(tree) if isinstance(node, ast.FunctionDef) and node.name == "describe_gateway"),
        None,
    )
    assert fn is not None, "gateway.py declares no describe_gateway"

    body = ast.unparse(fn)
    for side_effect in ("register_adapter", "generate(", "select("):
        assert side_effect not in body, f"describe_gateway now performs {side_effect}"
    # It must return the gateway description, and nothing else.
    returns = [node for node in ast.walk(fn) if isinstance(node, ast.Return)]
    assert len(returns) == 1, "describe_gateway must have exactly one return"
    assert "to_dict()" in ast.unparse(returns[0].value)


def test_negative_control_the_side_effect_detector_sees_one():
    """The detector must fire on a function that does mutate."""
    import ast

    polluted = ast.parse("def describe_gateway():\n    get_gateway().register_adapter('ollama', None)\n    return {}\n")
    fn = next(n for n in ast.walk(polluted) if isinstance(n, ast.FunctionDef))
    assert "register_adapter" in ast.unparse(fn)


# ---------------------------------------------------------------------------
# Availability is not dispatchability (handler P0.5)


def test_panel_shows_dispatchability_as_a_separate_fact():
    """The surface must render `dispatchable`, not only `status`.

    `status` answers "is this configured and reachable?"; `dispatchable` answers
    "could a run actually call it right now?", which additionally needs a bound
    adapter. A row that showed only the former would present a reachable provider
    as a functioning worker.
    """
    src = _read(GATEWAY_TSX)
    assert "dispatchable" in src, "the panel must show dispatchability"
    assert re.search(r'label:\s*"dispatchable"', src), "dispatchability must be a labelled fact"
    assert re.search(r'label:\s*"configured"', src), "configured must remain a separate fact"


def test_panel_surfaces_available_but_not_dispatchable():
    """Reachable-without-an-adapter must be reported, not folded into availability."""
    src = _read(GATEWAY_TSX)
    assert "available_but_not_dispatchable" in src
    assert "lab-gateway-available-not-dispatchable" in src


def test_projection_reads_dispatchability_from_the_handler_field():
    """`dispatchable` must be read from the handler, never inferred from `status`.

    Inferring it would erase the state the handler can emit — `status: AVAILABLE`
    with `dispatchable: false` — which is exactly the provider that would fail a
    dispatch.
    """
    src = _read(GATEWAY_TS)
    assert re.search(r"entry\.dispatchable === true", src), "dispatchability must be read from the field"
    assert "dispatchable_provider_present" in src
    assert re.search(r"usable_provider_present:\s*available\.length > 0", src), (
        "availability must keep its own meaning"
    )


# ---------------------------------------------------------------------------
# Optional gateway facts remain truthful


def test_provider_boolean_facts_preserve_unknown():
    """Missing optional gateway booleans must not be rendered as an observed 'no'."""
    source = _read(GATEWAY_TSX)
    for field in ("configured", "adapter_bound", "dispatchable"):
        assert f"gatewayBooleanFact(entry.{field})" in source, f"{field} must preserve unknown"
    assert re.search(r'label:\\s*"adapter bound"', source), "the bound-adapter fact must be visible"
