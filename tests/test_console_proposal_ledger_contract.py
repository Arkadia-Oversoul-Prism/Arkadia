"""Console proposal-ledger contract.

The SolSpire `proposals` lens used to advertise `/solspire/proposals` on a
``NotYetWired`` panel — "contract not yet wired" — while the canonical app serves
``GET /solspire/proposals`` (authenticated, owner-scoped through the subject's
workspace). The panel was therefore a *false* statement about the backend, and the
lens showed an operator nothing that the contract could answer.

This guard binds the repaired surface to the contract it claims to read:

* the registry entry is the served path, and the serving router requires auth;
* the component reads through the registry, not an inline literal;
* the component offers no mutating act (decision / authorization are human acts);
* the page mounts the ledger and no longer advertises the served contract as
  unwired.

Each detector has a negative control that feeds it the pre-repair shape, so the
guard cannot be satisfied by deleting the assertions or by a detector that never
reports anything.
"""
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "web" / "arkadia_console" / "src"
ENDPOINTS_PATH = SRC / "lib" / "endpoints.ts"
LEDGER_PATH = SRC / "components" / "solspire" / "ProposalLedger.tsx"
PAGE_PATH = SRC / "pages" / "SolSpirePage.tsx"

PROPOSAL_COLLECTION = "/solspire/proposals"


# ---------------------------------------------------------------------------
# Detectors (module level so the controls exercise the same code as the live
# assertions).
# ---------------------------------------------------------------------------


def _strip_comments(source: str) -> str:
    """The rendered code: block and line comments removed.

    The component's docstring legitimately *names* the mutating endpoints it does
    not offer, so a scan over the raw text would read documentation as behaviour.
    """
    without_blocks = re.sub(r"/\*.*?\*/", "", source, flags=re.DOTALL)
    return re.sub(r"^\s*//.*$", "", without_blocks, flags=re.MULTILINE)


def _declared_endpoint(text: str, name: str) -> str | None:
    body = re.search(r"export const endpoints\s*=\s*\{(.*?)\}\s*as const;", text, re.DOTALL)
    if not body:
        return None
    match = re.search(rf'{name}:\s*"([^"]+)"', body.group(1))
    return match.group(1) if match else None


def _hydration_literal_paths(source: str) -> list[str]:
    """Quoted literal paths passed to a read hook — the registry bypass."""
    return re.findall(r'useHydration<[^>]*>\(\s*"([^"]+)"', _strip_comments(source))


def _mutating_references(source: str) -> list[str]:
    """Mutating-act references in the rendered code (a mutating route or an explicit POST).

    Scoped to *routes and verbs*, not to words: the ledger legitimately renders the
    data field ``requested_decision``, which is a recorded value rather than an act.
    """
    rendered = _strip_comments(source)
    found = []
    if re.search(r"/(?:decision|authorize|execute|transition)\b", rendered):
        found.append("mutating route")
    if re.search(r"method:\s*['\"]POST['\"]", rendered):
        found.append("POST request")
    return found


def _advertises_unwired_proposals(page_source: str) -> bool:
    """Whether the page still advertises the served proposal collection as unwired."""
    rendered = _strip_comments(page_source)
    return re.search(rf'contract="{re.escape(PROPOSAL_COLLECTION)}"', rendered) is not None


def _served_operations() -> dict[str, set[str]]:
    """Method names per served path, from the canonical app's OpenAPI document.

    Imported lazily so the negative controls do not pay the application import.
    """
    from api.main import app

    return {path: set(operations) for path, operations in app.openapi()["paths"].items()}


# ---------------------------------------------------------------------------
# The live assertions
# ---------------------------------------------------------------------------


def test_registry_declares_the_served_proposal_collection():
    declared = _declared_endpoint(ENDPOINTS_PATH.read_text(encoding="utf-8"), "solspireProposals")
    assert declared == PROPOSAL_COLLECTION, f"registry entry is {declared!r}, not {PROPOSAL_COLLECTION!r}"
    served = _served_operations()
    assert PROPOSAL_COLLECTION in served, "the canonical app does not serve the proposal collection"
    assert "get" in served[PROPOSAL_COLLECTION], "the proposal collection is not served as a GET"


def test_serving_router_requires_authentication():
    """A ledger read must not be an anonymous surface, whatever the UI renders."""
    from solspire.proposal_router import router

    dependency_names = {getattr(dep.dependency, "__name__", "") for dep in router.dependencies}
    assert "require_auth" in dependency_names, (
        "the proposal router does not declare require_auth; the console ledger would read an "
        f"unauthenticated surface (dependencies: {sorted(dependency_names)})"
    )


def test_ledger_reads_through_the_registry():
    source = LEDGER_PATH.read_text(encoding="utf-8")
    assert "useHydration<unknown>(endpoints.solspireProposals" in source, (
        "the ledger must read through the shared endpoint registry"
    )
    assert _hydration_literal_paths(source) == [], (
        "the ledger passes an inline path literal to a read hook: "
        f"{_hydration_literal_paths(source)}"
    )


def test_ledger_offers_no_mutating_act():
    """Decision and authorization are human acts; the read surface must not imply them."""
    source = LEDGER_PATH.read_text(encoding="utf-8")
    assert _mutating_references(source) == [], (
        f"the ledger's rendered code references a mutating act: {_mutating_references(source)}"
    )


def test_page_mounts_the_ledger_and_stops_advertising_the_served_contract():
    page = PAGE_PATH.read_text(encoding="utf-8")
    assert "<ProposalLedger />" in page, "the SolSpire proposals lens does not mount the ledger"
    assert not _advertises_unwired_proposals(page), (
        "the page still advertises the served proposal collection on a NotYetWired panel"
    )


# ---------------------------------------------------------------------------
# Negative controls — each detector must report the shape it exists to catch
# ---------------------------------------------------------------------------


def test_control_inline_path_is_reported():
    defective = 'const ledger = useHydration<unknown>("/solspire/proposals", read<unknown>);'
    assert _hydration_literal_paths(defective) == [PROPOSAL_COLLECTION]


def test_control_mutating_act_is_reported():
    defective = 'const decide = () => apiRequest(`/solspire/proposals/${id}/decision`, { method: "POST" });'
    assert _mutating_references(defective) != []


def test_control_readvertised_contract_is_reported():
    defective = '<NotYetWired contract="/solspire/proposals" note="…" />'
    assert _advertises_unwired_proposals(defective) is True


def test_control_docstring_mention_is_not_a_mutating_act():
    """The component documents the acts it refuses; documentation is not behaviour."""
    documented = (
        "/**\n"
        " * A decision (`POST /solspire/proposals/{id}/decision`) is a human act.\n"
        " */\n"
        "export function ProposalLedger() { return null; }\n"
    )
    assert _mutating_references(documented) == []
