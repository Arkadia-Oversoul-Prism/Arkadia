"""WEAVER-SCI-DISCOVERY-01 - canonical SCI capability discovery layer.

Registry is descriptive only. Discovery != authorization.
"""
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
SCI_REG = ROOT / "web/public_prism/src/lib/sciCommandRegistry.ts"
SCI_PAGE = ROOT / "web/public_prism/src/pages/SpiralCommandInterface.tsx"
APP = ROOT / "web/public_prism/src/App.tsx"


def _r(p: Path) -> str:
    return p.read_text(encoding="utf-8")


def _command_blocks(reg: str):
    start = reg.find("export const SCI_COMMANDS")
    assert start != -1
    body = reg[start:]
    ids = re.findall(r"id:\s*'([^']+)'", body)
    return ids


def test_registry_descriptive_only():
    reg = _r(SCI_REG)
    assert "SCI_REGISTRY_IS_DESCRIPTIVE_NOT_AUTHORIZING = true" in reg
    assert "DISCOVERABLE != AVAILABLE != AUTHORIZED" in reg or "DISCOVERABLE" in reg


def test_every_capability_has_owner_availability_authority_mutation_class():
    reg = _r(SCI_REG)
    ids = _command_blocks(reg)
    assert len(ids) >= 9
    assert reg.count("owner:") >= len(ids)
    assert reg.count("availability:") >= len(ids)
    assert reg.count("authority:") >= len(ids)
    assert reg.count("mutationClass:") >= len(ids)
    assert reg.count("mutation:") >= len(ids)


def test_navigation_targets_are_known_or_null():
    reg = _r(SCI_REG)
    assert "KNOWN_ROUTE_VIEWS" in reg
    routes = re.findall(r"routeView:\s*'([^']+)'", reg)
    known = {"solspire", "knowledge-os", "novanet", "sci"}
    for r in routes:
        assert r in known, f"invented routeView {r}"


def test_unbound_targets_reported():
    reg = _r(SCI_REG)
    sci = _r(SCI_PAGE)
    assert "No operator surface currently bound" in reg
    assert "navigationLabel" in reg
    assert "No operator surface currently bound" in sci or "sci-unbound-" in sci


def test_sci_no_passspec_patchapproval_k15_k3_git():
    sci = _r(SCI_PAGE)
    reg = _r(SCI_REG)
    for banned in (
        "createPassSpec(",
        "createPatchApproval(",
        "execute_patch(",
        "run_transaction(",
        "git commit",
        "git push",
    ):
        assert banned not in sci
        assert banned not in reg


def test_autonomy_disabled_or_proposal_only():
    reg = _r(SCI_REG)
    assert "sci.autonomy" in reg
    assert "DISABLED" in reg
    assert "PROPOSAL_ONLY" in reg


def test_embeddings_not_available():
    reg = _r(SCI_REG)
    assert "sci.knowledge.embeddings" in reg
    assert "NOT_AVAILABLE" in reg
    idx = reg.find("sci.knowledge.embeddings")
    chunk = reg[idx : idx + 400]
    assert "NOT_AVAILABLE" in chunk


def test_knowledge_is_context_not_authorization():
    reg = _r(SCI_REG)
    assert "Knowledge != Authorization" in reg or "mustNot: ['authorization'" in reg
    idx = reg.find("id: 'sci.knowledge'")
    chunk = reg[idx : idx + 500]
    assert "CONTEXT" in chunk or "knowledge" in chunk.lower()


def test_discovery_helpers_exported():
    reg = _r(SCI_REG)
    for name in (
        "commandsForDomain",
        "commandsForOwner",
        "hasBoundRoute",
        "navigationLabel",
        "discoveryByDomain",
    ):
        assert f"export function {name}" in reg or f"function {name}" in reg


def test_sci_ui_shows_owner_and_mutation_class():
    sci = _r(SCI_PAGE)
    assert "owner:" in sci or "cmd.owner" in sci
    assert "mutationClass" in sci
    assert "hasBoundRoute" in sci


def test_app_still_mounts_sci():
    app = _r(APP)
    assert "view === 'sci'" in app
    assert "SpiralCommandInterface" in app
