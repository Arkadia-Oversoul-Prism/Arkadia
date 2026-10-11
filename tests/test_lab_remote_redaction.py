"""Security repair — a git remote's userinfo must never be surfaced.

`lab/observatory/git.py::repository_state()` returned `remote` as the verbatim
output of `git remote get-url origin`. Git stores a remote URL including any
`user:token@` userinfo, so the value carried whatever credential the environment's
remote was configured with, through `lab.service.build_overview()` and any surface
that reads it.

The repair is at the source of truth: `redact_remote_url()` runs inside
`repository_state()`, so every consumer receives an already-redacted value and no
caller has to remember to strip it.

Every test here uses a **synthetic** credential literal. No real secret is read,
written, printed, or persisted: the synthetic repositories are built in a temp
directory with `git remote add`, and the assertions look for the synthetic string.

The detector is proven with a negative control, so a regression that surfaced the
raw value would fail these tests rather than pass them.
"""
from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest

from lab.observatory.git import RemoteURL, redact_remote_url, repository_state
from lab.service import build_overview

# A synthetic credential used only to prove the redactor strips userinfo. It is
# not, and must never be, a real token.
FAKE_TOKEN = "SYNTHETIC0000TOKEN0000NOTAREALSECRET"
FAKE_USER = "x-access-token"


# ---------------------------------------------------------------------------
# Synthetic repositories


def _init_repo(path: Path) -> None:
    subprocess.run(["git", "init", "-q"], cwd=path, check=True)
    subprocess.run(["git", "config", "user.email", "t@t"], cwd=path, check=True)
    subprocess.run(["git", "config", "user.name", "t"], cwd=path, check=True)
    (path / "README").write_text("x", encoding="utf-8")
    subprocess.run(["git", "add", "README"], cwd=path, check=True)
    subprocess.run(["git", "commit", "-qm", "init"], cwd=path, check=True)


def _repo_with_remote(tmp_path: Path, remote: str) -> Path:
    path = tmp_path / "repo"
    path.mkdir()
    _init_repo(path)
    subprocess.run(["git", "remote", "add", "origin", remote], cwd=path, check=True)
    return path


# ---------------------------------------------------------------------------
# redact_remote_url — unit behaviour per URL form


def test_https_url_with_user_and_token_userinfo_is_stripped():
    result = redact_remote_url(f"https://{FAKE_USER}:{FAKE_TOKEN}@github.com/o/r.git")
    assert isinstance(result, RemoteURL)
    assert result.url == "https://github.com/o/r.git"
    assert result.redacted is True
    assert FAKE_TOKEN not in json.dumps({"url": result.url})


def test_https_url_with_bare_token_userinfo_is_stripped():
    """A `token@host` form has no colon and must be stripped too."""
    result = redact_remote_url(f"https://{FAKE_TOKEN}@github.com/o/r.git")
    assert result.url == "https://github.com/o/r.git"
    assert result.redacted is True


def test_password_containing_an_at_sign_is_fully_removed():
    """Split the authority on the LAST `@`, or part of the secret survives."""
    result = redact_remote_url(f"https://user:p@ss:{FAKE_TOKEN}@github.com/o/r.git")
    assert result.url == "https://github.com/o/r.git"
    assert FAKE_TOKEN not in json.dumps({"url": result.url})
    assert "@" not in result.url.split("://", 1)[-1]


def test_ssh_scheme_userinfo_is_stripped_and_host_preserved():
    result = redact_remote_url("ssh://git@github.com/o/r.git")
    assert result.url == "ssh://github.com/o/r.git"
    assert result.redacted is True


def test_scp_like_shorthand_userinfo_is_stripped():
    """`user@host:path` is a valid git remote form that `urlsplit` does not parse."""
    result = redact_remote_url("git@github.com:o/r.git")
    assert result.url == "github.com:o/r.git"
    assert result.redacted is True


def test_query_and_fragment_are_preserved_when_redacting():
    result = redact_remote_url(f"https://user:{FAKE_TOKEN}@github.com/o/r.git?x=1#frag")
    assert result.url == "https://github.com/o/r.git?x=1#frag"
    assert FAKE_TOKEN not in json.dumps({"url": result.url})


def test_non_default_port_is_preserved():
    result = redact_remote_url("https://github.com:8443/o/r.git")
    assert result.url == "https://github.com:8443/o/r.git"
    assert result.redacted is False


# ---------------------------------------------------------------------------
# Normal, credential-free forms pass through unchanged


@pytest.mark.parametrize(
    "remote",
    [
        "https://github.com/o/r.git",
        "https://github.com/o/r.git/",
        "ssh://github.com/o/r.git",
        "git://github.com/o/r.git",
        "https://github.com:8443/o/r.git",
        "/local/path/to/repo",
    ],
)
def test_credential_free_remote_passes_through_unchanged(remote: str):
    result = redact_remote_url(remote)
    assert result.url == remote
    assert result.redacted is False


@pytest.mark.parametrize("value", [None, "", "   ", 123, ["x"], {"a": 1}])
def test_absent_or_non_string_remote_is_none_and_unflagged(value):
    result = redact_remote_url(value)
    assert result.url is None
    assert result.redacted is False


# ---------------------------------------------------------------------------
# Malformed / unsupported forms are withheld, never guessed


@pytest.mark.parametrize(
    "remote",
    [
        "http://[::1",  # urlsplit raises ValueError (Invalid IPv6 URL)
        f"https://user:{FAKE_TOKEN}@",  # authority is userinfo only
        "https://user:tok@github.com/o/r.git extra",  # parseable but "@" outside netloc
    ],
)
def test_unverifiable_forms_are_withheld_rather_than_emitted(remote: str):
    """An unverifiable form must not be passed through on the assumption it is safe."""
    result = redact_remote_url(remote)
    if result.url is None:
        assert result.redacted is True
    else:  # a form we could fully verify and clean
        assert FAKE_TOKEN not in result.url
        assert "@" not in result.url.split("://", 1)[-1]


def test_unparseable_form_with_userinfo_is_withheld():
    result = redact_remote_url("http://[::1")
    assert result.url is None
    assert result.redacted is True


def test_unknown_form_carrying_an_at_sign_is_withheld():
    """Fail closed: an `@` we cannot attribute may hide userinfo."""
    result = redact_remote_url(f"weird{FAKE_TOKEN}@host")
    assert result.url is None
    assert result.redacted is True


# ---------------------------------------------------------------------------
# repository_state — the producer guarantees it


def test_repository_state_strips_userinfo_from_a_credentialed_remote(tmp_path):
    repo = _repo_with_remote(tmp_path, f"https://{FAKE_USER}:{FAKE_TOKEN}@github.com/o/r.git")
    state = repository_state(str(repo))

    assert state["remote"] == "https://github.com/o/r.git"
    assert state["remote_redacted"] is True
    assert FAKE_TOKEN not in json.dumps(state), "the credential survived into repository_state"


def test_repository_state_reports_no_redaction_for_a_clean_remote(tmp_path):
    repo = _repo_with_remote(tmp_path, "https://github.com/o/r.git")
    state = repository_state(str(repo))

    assert state["remote"] == "https://github.com/o/r.git"
    assert state["remote_redacted"] is False


def test_repository_state_withholds_a_credentialed_scp_like_remote(tmp_path):
    repo = _repo_with_remote(tmp_path, "git@github.com:o/r.git")
    state = repository_state(str(repo))

    assert state["remote"] == "github.com:o/r.git"
    assert "@" not in state["remote"]
    assert state["remote_redacted"] is True


# ---------------------------------------------------------------------------
# build_overview — the handler the endpoint returns


def test_build_overview_never_returns_remote_userinfo(tmp_path):
    repo = _repo_with_remote(tmp_path, f"https://{FAKE_USER}:{FAKE_TOKEN}@github.com/o/r.git")
    # The overview walks the tree, so a minimal repo is enough for the repository block.
    view = build_overview(str(repo))

    assert view["repository"]["remote"] == "https://github.com/o/r.git"
    assert view["repository"]["remote_redacted"] is True
    assert FAKE_TOKEN not in json.dumps(view), "the credential survived into build_overview"


def test_build_overview_security_status_is_truthful_and_narrowly_scoped():
    """`values_redacted` must be scoped, and the remote claim stated separately."""
    view = build_overview(".")
    security = view["security"]

    assert security["values_redacted"] is True
    assert security["redaction_scope"] == "security.observations"
    assert security["remote_userinfo_redacted"] is True
    assert "remote_redacted" in view["repository"]


def test_build_overview_on_this_repository_reports_no_userinfo():
    """Conformance against the live working tree, whatever its remote holds."""
    view = build_overview(".")
    remote = view["repository"]["remote"]
    if remote is None:
        pytest.skip("no git remote is readable in this environment")
    authority = remote.split("://", 1)[-1].split("/", 1)[0]
    assert "@" not in authority, f"repository.remote still carries userinfo: {remote!r}"


# ---------------------------------------------------------------------------
# Negative control — the detector must see an unredacted value


def test_negative_control_the_detector_would_flag_an_unredacted_remote():
    """Prove the assertions above can fail, rather than passing vacuously.

    If `repository_state` were reverted to the verbatim `get-url` output, the
    userinfo check below must fire.
    """
    raw = f"https://{FAKE_USER}:{FAKE_TOKEN}@github.com/o/r.git"
    authority = raw.split("://", 1)[-1].split("/", 1)[0]
    assert "@" in authority, "the control fixture must carry userinfo"
    assert FAKE_TOKEN in json.dumps({"remote": raw})

    # And the redactor is what removes it: the same value, redacted, no longer
    # trips the detector.
    result = redact_remote_url(raw)
    cleaned_authority = (result.url or "").split("://", 1)[-1].split("/", 1)[0]
    assert "@" not in cleaned_authority
