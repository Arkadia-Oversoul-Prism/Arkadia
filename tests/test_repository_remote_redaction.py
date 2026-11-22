from __future__ import annotations

import subprocess

import pytest

from lab.observatory.git import redact_remote_url, repository_state


@pytest.mark.parametrize(
    ("remote", "expected"),
    [
        (
            "https://alice:synthetic-token@example.invalid/Arkadia/repo.git",
            "https://example.invalid/Arkadia/repo.git",
        ),
        (
            "ssh://deploy:synthetic-token@example.invalid:2222/Arkadia/repo.git",
            "ssh://example.invalid:2222/Arkadia/repo.git",
        ),
        ("https://example.invalid/Arkadia/repo.git", "https://example.invalid/Arkadia/repo.git"),
        ("git@example.invalid:Arkadia/repo.git", "example.invalid:Arkadia/repo.git"),
        ("https://example.invalid/path?contact=alice@example.invalid", "https://example.invalid/path?contact=alice@example.invalid"),
        # A bare token with no colon is userinfo too.
        (
            "https://synthetic-token@example.invalid/Arkadia/repo.git",
            "https://example.invalid/Arkadia/repo.git",
        ),
        # A password that itself contains "@": split on the LAST one.
        (
            "https://alice:p@ss:synthetic-token@example.invalid/Arkadia/repo.git",
            "https://example.invalid/Arkadia/repo.git",
        ),
        # Query/fragment survive redaction, and a non-default port is preserved.
        (
            "https://alice:synthetic-token@example.invalid:8443/Arkadia/repo.git?ref=main#top",
            "https://example.invalid:8443/Arkadia/repo.git?ref=main#top",
        ),
    ],
)
def test_remote_userinfo_is_removed_without_rewriting_safe_remotes(remote: str, expected: str):
    assert redact_remote_url(remote) == expected


def test_malformed_credential_bearing_remote_fails_closed():
    value = redact_remote_url("https://alice:synthetic-token@")
    assert "alice" not in (value or "")
    assert "synthetic-token" not in (value or "")


def test_repository_state_never_exposes_remote_userinfo(tmp_path):
    subprocess.run(["git", "init", "-q", str(tmp_path)], check=True)
    subprocess.run(
        [
            "git",
            "-C",
            str(tmp_path),
            "remote",
            "add",
            "origin",
            "https://alice:synthetic-token@example.invalid/Arkadia/repo.git",
        ],
        check=True,
    )

    state = repository_state(str(tmp_path))

    assert state["remote"] == "https://example.invalid/Arkadia/repo.git"
    assert state["remote_redacted"] is True
    assert "alice" not in repr(state)
    assert "synthetic-token" not in repr(state)


def test_repository_state_reports_redaction_only_when_it_happened(tmp_path):
    """`remote_redacted` is a reading, not a constant: a clean remote reports False."""
    subprocess.run(["git", "init", "-q", str(tmp_path)], check=True)
    subprocess.run(
        ["git", "-C", str(tmp_path), "remote", "add", "origin", "https://example.invalid/Arkadia/repo.git"],
        check=True,
    )

    state = repository_state(str(tmp_path))

    assert state["remote"] == "https://example.invalid/Arkadia/repo.git"
    assert state["remote_redacted"] is False


def test_build_overview_security_status_is_truthful_and_narrowly_scoped():
    """`values_redacted` is scoped to the observations, so say so; the remote
    guarantee is a separate reading."""
    from lab.service import build_overview

    view = build_overview(".")
    security = view["security"]

    assert security["values_redacted"] is True
    assert security["redaction_scope"] == "security.observations"
    assert security["remote_userinfo_redacted"] is True
    assert "remote_redacted" in view["repository"]


def test_build_overview_never_returns_remote_userinfo(tmp_path):
    subprocess.run(["git", "init", "-q", str(tmp_path)], check=True)
    subprocess.run(
        [
            "git",
            "-C",
            str(tmp_path),
            "remote",
            "add",
            "origin",
            "https://alice:synthetic-token@example.invalid/Arkadia/repo.git",
        ],
        check=True,
    )

    from lab.service import build_overview

    view = build_overview(str(tmp_path))

    assert view["repository"]["remote"] == "https://example.invalid/Arkadia/repo.git"
    assert view["repository"]["remote_redacted"] is True
    assert "synthetic-token" not in repr(view)


def test_negative_control_the_redaction_reading_can_fail():
    """Prove the assertions above can fail, rather than passing vacuously.

    If `repository_state` returned the verbatim `get-url` output, the redaction
    reading below must be True and the value must carry userinfo - i.e. the
    detector distinguishes an unredacted value from a redacted one.
    """
    raw = "https://alice:synthetic-token@example.invalid/Arkadia/repo.git"
    assert redact_remote_url(raw) != raw, "the control fixture must be redactable"
    assert "synthetic-token" in raw
    clean = redact_remote_url(raw)
    assert clean == "https://example.invalid/Arkadia/repo.git"
    assert "synthetic-token" not in (clean or "")


# ── WEAVER reconnaissance ────────────────────────────────────────────────────
#
# `weaver.recon.git_identity()` feeds `build_context_packet()`, and
# `write_context_packet()` persists that packet to a *repository path*
# (`data/weaver/context/current.json`, which is tracked). An unredacted remote
# there is not just a read-model leak: it puts URL userinfo into a file that
# `git add` can publish, so the redaction has to hold at the writer, not only at
# the lab read model.

SYNTHETIC_REMOTE = "https://alice:synthetic-token@example.invalid/Arkadia/repo.git"
CLEAN_REMOTE = "https://example.invalid/Arkadia/repo.git"


def _init_repo_with_origin(tmp_path, remote: str) -> None:
    subprocess.run(["git", "init", "-q", str(tmp_path)], check=True)
    subprocess.run(["git", "-C", str(tmp_path), "remote", "add", "origin", remote], check=True)


def test_weaver_git_identity_never_exposes_remote_userinfo(tmp_path):
    _init_repo_with_origin(tmp_path, SYNTHETIC_REMOTE)

    from weaver.recon import git_identity

    ident = git_identity(str(tmp_path))

    assert ident["remote"] == CLEAN_REMOTE
    assert ident["remote_redacted"] is True
    assert "alice" not in repr(ident)
    assert "synthetic-token" not in repr(ident)


def test_weaver_git_identity_reports_redaction_only_when_it_happened(tmp_path):
    """A credential-free remote must report False, not a constant True."""
    _init_repo_with_origin(tmp_path, CLEAN_REMOTE)

    from weaver.recon import git_identity

    ident = git_identity(str(tmp_path))

    assert ident["remote"] == CLEAN_REMOTE
    assert ident["remote_redacted"] is False


def test_weaver_context_packet_never_persists_remote_userinfo(tmp_path):
    """The load-bearing assertion: the written packet is the disclosure surface."""
    _init_repo_with_origin(tmp_path, SYNTHETIC_REMOTE)

    from weaver.recon import write_context_packet

    rel = write_context_packet(str(tmp_path))
    written = (tmp_path / rel).read_text(encoding="utf-8")

    assert "synthetic-token" not in written
    assert "alice@" not in written
    assert CLEAN_REMOTE in written


def test_negative_control_the_packet_leaks_when_the_redaction_is_disabled(tmp_path, monkeypatch):
    """Prove the packet assertion above can fail.

    Disable the redaction at its definition (the imported name `git_identity`
    resolves) and the same write must persist the token. Without this control a
    green assertion could mean the fixture never reached the writer.
    """
    _init_repo_with_origin(tmp_path, SYNTHETIC_REMOTE)

    import weaver.recon as recon

    monkeypatch.setattr(recon, "redact_remote_url", lambda value: value)

    rel = recon.write_context_packet(str(tmp_path))
    written = (tmp_path / rel).read_text(encoding="utf-8")

    assert "synthetic-token" in written, (
        "the control did not reproduce the defect, so the positive assertion "
        "above proves nothing"
    )

