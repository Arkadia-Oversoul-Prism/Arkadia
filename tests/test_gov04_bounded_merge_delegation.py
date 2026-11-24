"""Regression pins for the human-authorized GOV-04 merge-delegation amendment."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
AUTH = ROOT / "docs/control-plane/evidence/gov-04-bounded-merge-delegation/AUTHORIZATION.md"
SHARED = ROOT / "docs/control-plane/parallel-ui/SHARED-CONTRACTS.md"
DIRECTIVE = ROOT / "docs/control-plane/overnight/PRISM-UI-RECONCILIATION.md"
AGENTS = ROOT / "AGENTS.md"
WORKER = ROOT / "docs/control-plane/WORKER_CONTRACT.md"
ADAPTER = ROOT / "weaver/execution_adapter.py"


def test_activation_requires_human_merge_of_this_governance_pr():
    auth = AUTH.read_text(encoding="utf-8").lower()
    assert "proposed" in auth
    assert "human-merged" in auth
    assert "this pr cannot self-authorize" in auth
    assert "governance pr" in auth and "human-reserved" in auth


def test_bounded_merge_is_exact_head_and_protected_fail_closed():
    auth = AUTH.read_text(encoding="utf-8").lower()
    for required in ("m1–m13", "expected head sha", "required checks", "required reviews",
                     "branch protections", "no auto-merge", "human_authority_required",
                     "post-merge", "dependency", "composition"):
        assert required in auth


def test_canonical_sources_reference_gov04_and_preserve_activation_gate():
    for path in (SHARED, DIRECTIVE, AGENTS, WORKER):
        content = path.read_text(encoding="utf-8").lower()
        assert "gov-04" in content
        assert "until" in content or "activation" in content
    assert "remains fail-closed" in WORKER.read_text(encoding="utf-8").lower()


def test_runtime_adapter_remains_fail_closed_until_separate_verification():
    adapter = ADAPTER.read_text(encoding="utf-8")
    assert 'raise RuntimeError("merge is human-only")' in adapter
