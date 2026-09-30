"""gate-hygiene — AGENTS.md encoding adjudication.

Proves the repair invariant on synthetic input and against the live repository,
so the verdict does not rest on a remembered codec table or on prose in an
evidence document. The oracle revision is real history, not a fixture: recovery
must reproduce the file's own last clean revision byte-for-byte.
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

from scripts.agents_md_encoding_audit import (
    CORRUPTION_COMMIT,
    ORACLE_REV,
    RECOVERED_TIP_REV,
    audit,
    corrupt,
    cyrillic_count,
    recover,
    try_recover_line,
)

ROOT = Path(__file__).resolve().parents[1]
AGENTS_MD = ROOT / "AGENTS.md"

# Build every corrupt literal from a codepoint, never by pasting the bytes: a
# pasted literal is itself mojibake and an editor/round-trip can rewrite it.
EM_DASH = chr(0x2014)
RIGHT_ARROW = chr(0x2192)
MISMATCH = chr(0x2260)


def mojibake(text: str) -> str:
    """UTF-8 bytes reinterpreted as CP866 — the transform under audit."""
    return text.encode("utf-8").decode("cp866")


def test_transform_is_the_documented_one():
    assert mojibake(EM_DASH) == chr(0x0442) + chr(0x0410) + chr(0x0424)
    assert mojibake(RIGHT_ARROW) == chr(0x0442) + chr(0x0416) + chr(0x0422)


def test_recover_line_round_trips():
    corrupt_line = mojibake(f"a {EM_DASH} b {RIGHT_ARROW} c")
    assert try_recover_line(corrupt_line) == f"a {EM_DASH} b {RIGHT_ARROW} c"


def test_ascii_and_genuine_lines_are_left_alone():
    for line in ["plain ascii", f"genuine {EM_DASH} dash", f"genuine {RIGHT_ARROW} arrow"]:
        assert try_recover_line(line) is None, line
    assert try_recover_line(f"genuine {chr(0x00B7)} middot") is None


def test_classifier_does_not_require_cyrillic_to_disappear():
    """A corrupt line whose mojibake has no Cyrillic must still be recovered.

    ``U+00B7`` corrupts to ``U+2534`` + ``U+00B7`` — box drawing plus Latin-1,
    zero Cyrillic. A classifier keyed on the Cyrillic count skips it, and the
    recovery then fails to reproduce the oracle revision.
    """
    corrupt_line = mojibake(chr(0x00B7))
    assert cyrillic_count(corrupt_line) == 0
    assert try_recover_line(corrupt_line) == chr(0x00B7)


def test_recover_preserves_everything_outside_the_corrupted_domain():
    lines = [
        "plain ascii",
        mojibake(f"corrupted {EM_DASH} here"),
        f"genuine {RIGHT_ARROW} arrow",
        mojibake(f"also corrupted {RIGHT_ARROW}"),
        "",
    ]
    text = "\n".join(lines)
    recovered, repaired = recover(text)
    assert repaired == [2, 4]
    assert recovered.split("\n") == [
        "plain ascii",
        f"corrupted {EM_DASH} here",
        f"genuine {RIGHT_ARROW} arrow",
        f"also corrupted {RIGHT_ARROW}",
        "",
    ]


def test_round_trip_is_scoped_to_the_corrupted_domain():
    text = "\n".join(["ascii", mojibake(f"x {EM_DASH} y"), f"genuine {RIGHT_ARROW}"])
    recovered, repaired = recover(text)
    assert corrupt(recovered, repaired) == text
    assert repaired == [2]


def test_round_trip_needs_the_repaired_domain():
    """A recovered middle dot is indistinguishable from a genuine one.

    ``U+00B7`` is not CP866-encodable, so after recovery the line no longer
    looks corrupt and the domain cannot be re-derived. This is why the repaired
    line numbers must be carried into the inverse transform.
    """
    text = "\n".join([mojibake(chr(0x00B7)), chr(0x00B7)])
    recovered, repaired = recover(text)
    assert recovered.split("\n") == [chr(0x00B7), chr(0x00B7)]
    assert repaired == [1]
    assert corrupt(recovered, repaired) == text
    # re-deriving the domain from the recovered text would miss line 1 entirely
    assert corrupt(recovered) != text


def test_whole_file_decode_is_destructive():
    """Negative control for the rejected approach."""
    text = "\n".join([mojibake(f"x {EM_DASH} y"), f"genuine {RIGHT_ARROW}"])
    with pytest.raises(UnicodeEncodeError):
        text.encode("cp866")


def test_recover_is_decidable_on_the_live_file():
    text = AGENTS_MD.read_text(encoding="utf-8")
    oracle = subprocess.run(
        ["git", "-C", str(ROOT), "show", f"{ORACLE_REV}:AGENTS.md"],
        capture_output=True,
    )
    if oracle.returncode != 0:
        pytest.skip(f"oracle revision {ORACLE_REV} unavailable in this clone")
    result = audit(text, oracle.stdout.decode("utf-8"))
    assert result["decidable"] is True, result
    assert result["cyrillic_after"] == 0
    assert result["line_count_preserved"] is True
    assert result["only_corrupted_lines_changed"] is True
    assert result["round_trip_holds"] is True
    # insertions only: the recovered text must not alter any oracle line
    assert result["oracle_alterations"] == []
    assert result["oracle_inserted_lines"] == 164
    assert result["oracle_cyrillic"] == 0


def test_recovered_text_equals_the_repaired_tip():
    """Recovery must reproduce the already-clean tip written to pr150.

    This is what makes the adjudication decidable rather than merely plausible:
    the transform applied to ``main`` lands exactly on the version of the file
    that a human already reviewed as clean.
    """
    text = AGENTS_MD.read_text(encoding="utf-8")
    recovered, _ = recover(text)
    tip = subprocess.run(
        ["git", "-C", str(ROOT), "show", f"{RECOVERED_TIP_REV}:AGENTS.md"],
        capture_output=True,
    )
    if tip.returncode != 0:
        pytest.skip(f"repaired tip {RECOVERED_TIP_REV} unavailable in this clone")
    tip_text = tip.stdout.decode("utf-8")
    assert recovered == "\n".join(tip_text.split("\n")[: result_shape(recovered)])
    assert cyrillic_count(tip_text) == 0


def result_shape(recovered: str) -> int:
    return len(recovered.split("\n"))


def test_corruption_origin_is_re_derivable():
    """The claimed origin commit is checked, not asserted."""
    proc = subprocess.run(
        ["git", "-C", str(ROOT), "log", "--format=%H", "--", "AGENTS.md"],
        capture_output=True,
    )
    if proc.returncode != 0 or not proc.stdout.strip():
        pytest.skip("AGENTS.md history unavailable in this clone")
    revisions = proc.stdout.decode().split()
    first_corrupt = None
    for rev in reversed(revisions):
        blob = subprocess.run(
            ["git", "-C", str(ROOT), "show", f"{rev}:AGENTS.md"], capture_output=True
        )
        if blob.returncode != 0:
            continue
        if cyrillic_count(blob.stdout.decode("utf-8")):
            first_corrupt = rev
            break
    assert first_corrupt is not None, "no corrupt revision found in history"
    assert first_corrupt.startswith(CORRUPTION_COMMIT)


def test_audit_reports_the_corruption_class_not_a_codec_table():
    text = "\n".join([mojibake(f"x {EM_DASH} y"), f"genuine {RIGHT_ARROW} arrow"])
    result = audit(text, oracle=None)
    assert result["corrupted_lines"] == 1
    assert result["cyrillic_before"] == cyrillic_count(mojibake(f"x {EM_DASH} y"))
    assert result["cyrillic_after"] == 0
    assert result["cruft_after"] == 0
    assert result["non_ascii_after"] == result["non_ascii_before"] - 2


def test_audit_flags_already_clean_input():
    result = audit("nothing wrong here\n", oracle=None)
    assert result["corrupted_lines"] == 0
    assert result["cyrillic_before"] == 0


def test_no_literal_mojibake_in_the_audit_surfaces():
    """The instrument and its evidence must not reintroduce the corruption.

    A lesson that pastes a corrupt sequence re-introduces the very bytes it
    documents, and the verification it prescribes then fails on itself.
    """
    for path in [
        ROOT / "scripts" / "agents_md_encoding_audit.py",
        Path(__file__),
    ]:
        cyr = cyrillic_count(path.read_text(encoding="utf-8"))
        assert cyr == 0, f"{path.name} contains {cyr} Cyrillic mojibake chars"


def _run_cli(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "agents_md_encoding_audit.py"), *args],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )


def test_cli_summarises_the_oracle_without_crashing():
    """The human-facing summary must not outrun the result dict.

    The keys printed here were once renamed out from under the report, so the
    CLI raised ``KeyError`` after already claiming the repair decidable. Only an
    end-to-end invocation catches that — the audit function returns fine.
    """
    proc = _run_cli()
    assert proc.returncode == 0, proc.stderr
    assert "insertions-only" in proc.stdout
    assert "reproduced=True" in proc.stdout
    assert "KeyError" not in proc.stderr


def test_cli_exits_one_on_an_already_clean_file(tmp_path):
    clean = tmp_path / "AGENTS.md"
    clean.write_text("perfectly ordinary text\n", encoding="utf-8")
    proc = _run_cli("--path", str(clean))
    assert proc.returncode == 1, proc.stdout + proc.stderr
