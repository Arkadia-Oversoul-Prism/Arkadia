"""Gate-2 canonical-alias <-> application binding — fitness tests.

Source-level and pure-function; no network, no credential, no browser. These
prove the binding classifier has teeth (negative controls), is fail-closed on an
undetermined output directory, and does not silently widen the Prism marker
scope to a deployment of a different application.
"""

import json
from pathlib import Path

from scripts.gate2_alias_app_binding import (
    KNOWN_ROOT_OUTPUTS,
    MARKER_APP,
    app_of_output,
    binding,
    classify,
    root_output_directory,
)

_ROOT = Path(__file__).resolve().parents[1]


def _write_cfg(tmp_path: Path, cfg: dict) -> str:
    (tmp_path / "vercel.json").write_text(json.dumps(cfg), encoding="utf-8")
    return str(tmp_path)


# ---------------------------------------------------------------------------
# App mapping
# ---------------------------------------------------------------------------


def test_public_prism_output_is_the_marker_app():
    assert app_of_output("web/public_prism") == MARKER_APP


def test_nested_output_resolves_to_parent_app_longest_prefix():
    assert app_of_output("web/public_prism/dist") == MARKER_APP
    assert app_of_output("web/console/dist") == "console"


def test_unknown_output_is_undetermined_not_assumed():
    # A repoint to a frontend nobody enumerated must not silently read as
    # "still Prism" -- it yields no app, which is fail-closed.
    assert app_of_output("web/unknown-app") is None
    assert app_of_output("") is None
    assert app_of_output(None) is None


# ---------------------------------------------------------------------------
# Root vercel.json reading
# ---------------------------------------------------------------------------


def test_missing_config_is_undetermined(tmp_path):
    assert root_output_directory(str(tmp_path)) is None


def test_unparseable_config_is_undetermined(tmp_path):
    (tmp_path / "vercel.json").write_text("{not json", encoding="utf-8")
    assert root_output_directory(str(tmp_path)) is None


# ---------------------------------------------------------------------------
# Binding classification
# ---------------------------------------------------------------------------


def test_public_prism_root_is_applicable_positive_control(tmp_path):
    root = _write_cfg(tmp_path, {"outputDirectory": "web/public_prism"})
    b = binding(root)
    assert b["root_app"] == MARKER_APP
    assert b["marker_comparison_applicable"] is True
    assert "APPLICABLE" in classify(b)


def test_console_root_is_not_applicable(tmp_path):
    root = _write_cfg(tmp_path, {"outputDirectory": "web/console"})
    b = binding(root)
    assert b["root_app"] == "console"
    assert b["marker_comparison_applicable"] is False
    msg = classify(b)
    assert "NOT APPLICABLE" in msg
    assert "console" in msg and MARKER_APP in msg
    # Must describe a *different application*, never a disagreement/divergence.
    assert "different application" in msg
    assert "disagreement" in msg


def test_undetermined_root_is_not_applicable(tmp_path):
    b = binding(str(tmp_path))
    assert b["root_output_directory"] is None
    assert b["root_app"] is None
    assert b["marker_comparison_applicable"] is False
    assert "fail-closed" in classify(b)


# ---------------------------------------------------------------------------
# Negative control: the would-be false positive is prevented
# ---------------------------------------------------------------------------


def test_zero_markers_on_a_different_app_is_not_reported_as_agreement(tmp_path):
    """The defect this guards: scoring Prism literals against a Console artifact
    yields an all-zero marker set. That is "different application", and the
    binding must withhold the comparison rather than let the observer report
    divergence or agreement.
    """
    root = _write_cfg(tmp_path, {"outputDirectory": "web/console"})
    b = binding(root)
    # If the observer had assumed applicability, an all-zero set would be a
    # divergence claim. The binding must be the thing that stops it.
    assert b["marker_comparison_applicable"] is False
    msg = classify(b).lower()
    assert "not applicable" in msg
    assert "marker set matches" not in msg
    assert "different application" in msg


# ---------------------------------------------------------------------------
# Live repository state (the binding must be re-derived, not remembered)
# ---------------------------------------------------------------------------


def test_live_root_config_names_a_known_frontend():
    """If the repository root still carries a ``vercel.json``, it must name a
    frontend this module can classify -- a repoint to an unlisted frontend
    reddens this test rather than shipping an unclassified binding.

    The file was retired (removed at 5a292e11) when the canonical runtime moved
    to Render, so its absence is the expected live state, not an unclassified
    binding. Guarding that transition explicitly keeps the repoint guard intact
    while allowing the retirement: the earlier unconditional ``output is not
    None`` pinned the pre-retirement tree and went red the moment the file was
    removed.
    """
    cfg = _ROOT / "vercel.json"
    output = root_output_directory(str(_ROOT))
    if not cfg.exists():
        assert output is None
        return
    assert output is not None
    assert app_of_output(output) in set(KNOWN_ROOT_OUTPUTS.values())


def test_live_binding_is_derived_from_the_working_tree():
    b = binding(str(_ROOT))
    assert b["marker_app"] == MARKER_APP
    assert b["root_output_directory"] == root_output_directory(str(_ROOT))
    # Keep the classification honest: it is a function of the live file.
    assert b["marker_comparison_applicable"] == (b["root_app"] == MARKER_APP)


# ---------------------------------------------------------------------------
# Read-only guarantee
# ---------------------------------------------------------------------------


def test_module_holds_no_credential_or_network_surface():
    src = (_ROOT / "scripts" / "gate2_alias_app_binding.py").read_text(encoding="utf-8")
    assert "urllib" not in src
    assert "requests" not in src
    assert "subprocess" not in src
    assert "TOKEN" not in src and "token" not in src
