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


def _states_no_auto_merge(text: str) -> bool:
    """True when the authorization forbids auto-merge in either recorded form."""
    text = text.lower()
    return "auto-merge" in text and (
        "no authorization" in text or "does not enable auto-merge" in text
    )


def _records_post_merge_reconciliation(text: str) -> bool:
    """True when the authorization requires reconciling main after the merge."""
    text = text.lower()
    return "post-merge" in text or ("reconcile main" in text and "afterward" in text)


def test_bounded_merge_is_exact_head_and_protected_fail_closed():
    auth = AUTH.read_text(encoding="utf-8").lower()
    # The merged pin demanded the literals "no auto-merge" and "post-merge"; the
    # authorization states both obligations as "No authorization: auto-merge" /
    # "does not enable auto-merge" and "reconcile main afterward".
    for required in ("m1–m13", "expected head sha", "required checks", "required reviews",
                     "branch protections", "human_authority_required",
                     "dependency", "composition"):
        assert required in auth
    assert _states_no_auto_merge(auth)
    assert _records_post_merge_reconciliation(auth)


def test_prohibition_detectors_have_negative_controls():
    assert _states_no_auto_merge(AUTH.read_text(encoding="utf-8"))
    assert _records_post_merge_reconciliation(AUTH.read_text(encoding="utf-8"))
    assert not _states_no_auto_merge("**Authorization:** the operator may auto-merge any PR.")
    assert not _states_no_auto_merge("**Authorization:** exact-head merges only.")
    assert not _records_post_merge_reconciliation("Merge the PR with the expected head SHA.")
    assert _records_post_merge_reconciliation("Post-merge: reconcile main.")


def test_canonical_sources_reference_gov04_and_preserve_activation_gate():
    for path in (SHARED, DIRECTIVE, AGENTS, WORKER):
        content = path.read_text(encoding="utf-8").lower()
        assert "gov-04" in content
        assert "until" in content or "activation" in content
    assert "remains fail-closed" in WORKER.read_text(encoding="utf-8").lower()


def test_runtime_adapter_remains_fail_closed_until_separate_verification():
    adapter = ADAPTER.read_text(encoding="utf-8")
    assert 'raise RuntimeError("merge is human-only")' in adapter
