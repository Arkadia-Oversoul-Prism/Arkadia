"""Guard the root `.gitleaks.toml` so a malformed config cannot reach CI unjudged.

The Full-history secret scan runs `gitleaks detect`, which reads the root
`.gitleaks.toml` as its config. A config that fails to parse makes the scan abort:
gitleaks exits non-zero *without scanning*, so the job reports a red "secret scan"
that is really a configuration fault. A config that parses but carries an
unanchored `allowlist.regexes` entry silently over-suppresses findings by matching
the pattern as a substring of any secret value.

Nothing validated that file before this guard (see PR #312 §13.2/13.6, and the
malformed multi-line entries PR #311 carried). This test closes that surface with
stdlib-only validation and negative controls that feed the exact malformed bytes.

The guard never embeds a credential-shaped literal: the placeholder used to exercise
the shape checks is a plain non-secret token.
"""

from __future__ import annotations

import re
import tomllib
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
GITLEAKS_CONFIG = REPO_ROOT / ".gitleaks.toml"

# A plain, non-credential-shaped token used only to exercise the shape checks.
PLACEHOLDER = "placeholder-non-secret-identifier"


class GitleaksConfigError(ValueError):
    """Raised when the root `.gitleaks.toml` cannot be trusted as a scan config."""


def _validate_config_text(text: str, *, source: str = "<config>") -> dict:
    """Parse and validate a `.gitleaks.toml` payload.

    Raises `GitleaksConfigError` (never `AssertionError`) so the same validator can
    be exercised by a negative control on synthetic malformed input.
    """
    try:
        data = tomllib.loads(text)
    except tomllib.TOMLDecodeError as exc:
        raise GitleaksConfigError(f"{source}: not valid TOML: {exc}") from exc

    extend = data.get("extend")
    if not isinstance(extend, dict) or extend.get("useDefault") is not True:
        raise GitleaksConfigError(
            f"{source}: [extend] must set useDefault = true so the default rule "
            "set still runs; a config that disables it suppresses every default rule."
        )

    allowlist = data.get("allowlist")
    if not isinstance(allowlist, dict):
        raise GitleaksConfigError(
            f"{source}: missing [allowlist] table; the config must name exactly "
            "which non-secret literals are exempted."
        )

    # `regexTarget = "secret"` scopes a regex to the matched value only. Any other
    # target (notably "line") widens the exemption to surrounding prose, which is
    # how an allowlist entry can over-suppress unrelated findings.
    if allowlist.get("regexTarget") != "secret":
        raise GitleaksConfigError(
            f'{source}: [allowlist].regexTarget must be "secret", found '
            f'{allowlist.get("regexTarget")!r}.'
        )

    regexes = allowlist.get("regexes")
    if not isinstance(regexes, list) or not regexes:
        raise GitleaksConfigError(
            f"{source}: [allowlist].regexes must be a non-empty list."
        )

    for entry in regexes:
        if not isinstance(entry, str) or not entry.strip():
            raise GitleaksConfigError(
                f"{source}: every allowlist regex must be a non-empty string."
            )
        # A newline means the literal was written across lines: that is the exact
        # defect shape that breaks the TOML document (and, historically, the scan).
        if "\n" in entry or "\r" in entry:
            raise GitleaksConfigError(
                f"{source}: allowlist regex {entry!r} spans multiple lines; each "
                "entry must be a single-line pattern."
            )
        # Anchored on both ends: an unanchored pattern matches a *substring* of any
        # secret value, so it can suppress a real credential that merely contains it.
        if not (entry.startswith("^") and entry.endswith("$")):
            raise GitleaksConfigError(
                f"{source}: allowlist regex {entry!r} must be anchored with ^ and $ "
                "so it matches a whole secret value, never a substring."
            )
        try:
            re.compile(entry)
        except re.error as exc:
            raise GitleaksConfigError(
                f"{source}: allowlist regex {entry!r} does not compile: {exc}"
            ) from exc

    return data


def test_live_gitleaks_config_is_valid() -> None:
    """The root `.gitleaks.toml` must parse and satisfy every scan-safety rule."""
    assert GITLEAKS_CONFIG.is_file(), f"missing {GITLEAKS_CONFIG}"
    _validate_config_text(GITLEAKS_CONFIG.read_text(encoding="utf-8"),
                          source=".gitleaks.toml")


def test_negative_control_multi_line_entry_breaks_the_document() -> None:
    """A `'''`-opened entry that never closes on its line must be rejected.

    This reproduces the malformed shape PR #311 carried (a multi-line-start
    delimiter with no closing delimiter on the same line). It must raise before any
    regex inspection, because the document itself does not parse.
    """
    malformed = (
        "[extend]\nuseDefault = true\n\n[allowlist]\n"
        'regexTarget = "secret"\nregexes = [\n'
        f"  '''^{PLACEHOLDER}$,\n"
        "]\n"
    )
    with pytest.raises(GitleaksConfigError):
        _validate_config_text(malformed, source="<malformed>")


def test_negative_control_unanchored_entry_is_rejected() -> None:
    """An unanchored entry parses but over-suppresses; it must be rejected."""
    unanchored = (
        "[extend]\nuseDefault = true\n\n[allowlist]\n"
        'regexTarget = "secret"\nregexes = [\n'
        f"  '''{PLACEHOLDER}''',\n"
        "]\n"
    )
    with pytest.raises(GitleaksConfigError):
        _validate_config_text(unanchored, source="<unanchored>")


def test_negative_control_line_regex_target_is_rejected() -> None:
    """`regexTarget = "line"` widens the exemption beyond the secret value."""
    line_target = (
        "[extend]\nuseDefault = true\n\n[allowlist]\n"
        'regexTarget = "line"\nregexes = [\n'
        f"  '''^{PLACEHOLDER}$''',\n"
        "]\n"
    )
    with pytest.raises(GitleaksConfigError):
        _validate_config_text(line_target, source="<line-target>")


def test_negative_control_disabling_default_rules_is_rejected() -> None:
    """`useDefault = false` would suppress every default rule, not just literals."""
    no_default = (
        "[extend]\nuseDefault = false\n\n[allowlist]\n"
        'regexTarget = "secret"\nregexes = [\n'
        f"  '''^{PLACEHOLDER}$''',\n"
        "]\n"
    )
    with pytest.raises(GitleaksConfigError):
        _validate_config_text(no_default, source="<no-default>")


def test_positive_control_well_formed_config_is_accepted() -> None:
    """A well-formed config must pass, so the guard cannot be disarmed by making
    every input fail."""
    well_formed = (
        "[extend]\nuseDefault = true\n\n[allowlist]\n"
        'description = "test"\nregexTarget = "secret"\nregexes = [\n'
        f"  '''^{PLACEHOLDER}$''',\n"
        "]\n"
    )
    data = _validate_config_text(well_formed, source="<well-formed>")
    assert data["allowlist"]["regexes"] == [f"^{PLACEHOLDER}$"]
