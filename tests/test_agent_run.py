"""Bounded agent-run proof.

Re-pinned for SH-02 row 1 (``STALE_ASSERTION``). The pre-K0.1
``task -> LLM -> write -> commit/push`` flow asserted here was superseded by the
WEAVER-K0.1 kernel, so the node now pins the *current* flow on the same seams:

* the default entry point refuses without a ``PassSpec`` (K0.1 — no anonymous
  execution path);
* the authorized flow goes through ``run_authorized`` and returns a
  ``SessionResult``;
* the commit stays **terminal** and routed through the K0.1 kernel — the agent
  module must not re-expose ``weaver.git_ops.commit_and_push`` directly
  (``tests/test_weaver_k2.py::test_provider_has_no_write_commit_push`` guards the
  provider side of the same boundary).

The removed ``test_agent_run_writes_and_commits`` additionally asserted that
``engine_cycle`` reached the commit as ``meta['engine_cycle']``. That provenance is
**not** carried by the current commit path (``finalize_session`` passes
``meta={"pass_id": ...}`` only and never receives ``engine_cycle``), so the row is
re-pinned to the retained properties. The provenance gap is recorded as an open
delta rather than fixed here: closing it changes what the kernel commits for
governance, which is not test hygiene.
"""
from pathlib import Path

from weaver import agent
from weaver.pass_spec import PassSpec
from weaver.provider import ProviderOutcome, ProviderResult
from weaver.session_kernel import SessionResult

SENTINEL_SHA = "a" * 40


def test_agent_run_refuses_without_pass_spec():
    """K0.1: the default entry point is fail-closed — no authorization, no run."""
    changed, message = agent.run("test task", engine_cycle=5)
    assert changed == []
    assert message is None


def test_agent_run_authorized_reaches_terminal_publication_on_the_kernel_seam(
    tmp_path, monkeypatch
):
    monkeypatch.setenv("REPO_ROOT", str(tmp_path))
    monkeypatch.chdir(tmp_path)

    # No-op the read/diff/test/checkpoint side-effects; the commit itself is
    # the seam under test and is still exercised.
    monkeypatch.setattr("weaver.agent.read_repo", lambda *a, **k: {})
    monkeypatch.setattr("weaver.agent.build_prompt", lambda *a, **k: "fake prompt")
    monkeypatch.setattr(
        "weaver.agent.invoke_provider",
        lambda req: ProviderResult(
            outcome=ProviderOutcome.SUCCESS,
            text="--- FILE: weaver/note.txt ---\nre-pin\n",
            provider="gemini",
        ),
    )
    # Lineage + SHA resolution read the ambient repo. Both the agent entry point and
    # finalize_session re-run preflight, so pin the kernel's own binding too, and give
    # the SHAs deterministic values so the publication result can be asserted exactly.
    monkeypatch.setattr("weaver.agent.preflight", lambda *a, **k: SENTINEL_SHA)
    monkeypatch.setattr("weaver.session_kernel.preflight", lambda *a, **k: SENTINEL_SHA)
    monkeypatch.setattr("weaver.session_kernel.current_head", lambda *a, **k: SENTINEL_SHA)
    monkeypatch.setattr(
        "weaver.session_kernel.current_origin_main", lambda *a, **k: SENTINEL_SHA
    )
    monkeypatch.setattr("weaver.session_kernel.verify_diff_scope", lambda *a, **k: [])
    monkeypatch.setattr(
        "weaver.session_kernel.run_required_tests",
        lambda *a, **k: {"passed": True, "items": []},
    )

    # Pin the decisive bit with a sentinel: only the kernel's commit path may set it.
    commits = {}

    def fake_commit(msg, paths=None, meta=None, **kwargs):
        commits["msg"] = msg
        commits["meta"] = meta
        return True

    monkeypatch.setattr("weaver.session_kernel.commit_and_push", fake_commit)

    spec = PassSpec(
        pass_id="WEAVER-K0-SH02E",
        objective="bounded agent-run re-pin",
        base_sha=SENTINEL_SHA,
        allowed_paths=["weaver/", "data/weaver/checkpoints/"],
        forbidden_paths=[".git/"],
        required_tests=[],
        required_builds=[],
        commit_required=True,
        checkpoint_required=False,
        push_allowed=False,
        publication_required=False,
        provider="gemini",
    )

    result = agent.run_authorized("test task", spec, engine_cycle=5, repo_root=str(tmp_path))

    assert isinstance(result, SessionResult)
    assert result.ok is True, result.message
    assert result.status == "PASS"
    assert result.result_sha == SENTINEL_SHA
    assert "weaver/note.txt" in result.changed_paths
    # The turn also materializes its durable checkpoint into the changed set.
    assert any(p.startswith("data/weaver/checkpoints/") for p in result.changed_paths)
    assert (tmp_path / "weaver" / "note.txt").read_text().strip() == "re-pin"
    assert commits, "terminal commit did not run through the session kernel"
    # The iteration still reaches the commit message...
    assert "(cycle 5)" in commits["msg"]
    # ...but the epoch is not carried in commit metadata. `finalize_session` is the only
    # commit path and never receives `engine_cycle`, so this is a structural gap in
    # provenance, not an assertion the kernel is meant to satisfy. Pin the invariant
    # rather than the absence: today the key is missing, and if it is ever threaded
    # through it must carry the real epoch — never a fabricated one. A strict
    # `not in` would turn a legitimate future fix into a red test.
    assert commits["meta"].get("engine_cycle", 5) == 5
    assert commits["meta"]["pass_id"] == "WEAVER-K0-SH02E"
    # A durable checkpoint is still materialized for the turn.
    assert Path(result.checkpoint_path).exists()
    # No unnamed / permissionless write path was reintroduced on the agent module.
    assert not hasattr(agent, "commit_and_push")

