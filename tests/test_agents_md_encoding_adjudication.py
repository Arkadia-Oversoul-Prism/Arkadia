"""gate-hygiene — AGENTS.md encoding adjudication.

Proves the repair invariant on synthetic input and against the live repository,
so the verdict does not rest on a remembered codec table or on prose in an
evidence document. The oracle revision is real history, not a fixture: recovery
must reproduce the file's own last clean revision byte-for-byte.
"""
from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path

import pytest

from scripts.agents_md_encoding_audit import (
    CORRUPTION_COMMIT,
    ORACLE_REV,
    RECOVERED_TIP_REV,
    SHADOW_CODEC,
    audit,
    audit_shadow,
    corrupt,
    cyrillic_count,
    exit_code,
    heal_shadow,
    recover,
    try_recover_line,
)

ROOT = Path(__file__).resolve().parents[1]
AGENTS_MD = ROOT / "AGENTS.md"

# PR #143 head. Pinned to an immutable commit, not the branch name: a branch is
# deleted when its PR merges, and this reference must outlive the queue.
GATE2_PARENT_REV = "7d79f38bd520a99637785db80bbe786192900d6d"
# sha256 of that revision's AGENTS.md after the two-stage repair. Recomputed by
# the test, so the evidence document cannot claim a digest the bytes deny.
GATE2_PARENT_REPAIRED_SHA256 = (
    "af67aad45631d130d1c352efdea75a20e16cb829a3620d527c07e31f2772415f"
)

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


def test_recover_is_decidable_on_the_corrupted_live_file():
    """The adjudication, scoped to the revision it was made about.

    ``main``'s AGENTS.md carries the mojibake, so recovery is decidable and the
    recovered text relates to the clean oracle by insertions only. This test
    asserts what is true *while the repair is still unmerged*.

    It is deliberately not the whole story: once PR #150 merges, this same file
    is already clean and the correct verdict changes (see
    ``test_live_file_verdict_matches_its_state``). An adjudication that assumed
    its own repair would never land is the defect this pair exists to prevent.
    """
    text = AGENTS_MD.read_text(encoding="utf-8")
    if cyrillic_count(text) == 0:
        pytest.skip(
            "AGENTS.md on this revision is already repaired — the corrupted-main "
            "adjudication does not bind here (see test_live_file_verdict_matches_its_state)"
        )
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


def test_live_file_verdict_matches_its_state():
    """The verdict must follow the working tree, not a remembered verdict.

    Order-dependent either way:

    * corrupted ``main`` (PR #150 unmerged): recovery is decidable, exit 0;
    * repaired ``main`` (PR #150 merged): nothing to recover, exit 1.

    The two live-file tests are written as complementary branches so that both
    merge orders of #150 and #151 keep the suite green. Exactly one branch runs
    on any given revision; the other states its reason and skips.
    """
    text = AGENTS_MD.read_text(encoding="utf-8")
    repaired = cyrillic_count(text) == 0
    proc = _run_cli()
    if repaired:
        assert proc.returncode == 1, proc.stdout + proc.stderr
        assert "0 -> 0" in proc.stdout
    else:
        assert proc.returncode == 0, proc.stdout + proc.stderr
        assert "reproduced=True" in proc.stdout
    assert AGENTS_MD.read_text(encoding="utf-8") == text, "the audit must not mutate the tree"


def test_cli_does_not_claim_clean_without_an_oracle(tmp_path):
    """An unproven "already clean" is reported as unproven, never as a verdict.

    The oracle is looked up as ``<rev>:<path>``, so it exists only for a path the
    repository actually tracks. For a clean file the repository does not track —
    a scratch file, a deleted path, a ``fetch-depth: 1`` checkout that cannot
    resolve the revision — "clean" and "never verified" are indistinguishable
    from the bytes alone. Exit 2 keeps the distinction; only a resolvable oracle
    licenses exit 1.
    """
    porcelain = tmp_path / "AGENTS.md"
    porcelain.write_text("perfectly ordinary text\n", encoding="utf-8")
    proc = _run_cli("--path", str(porcelain))
    assert proc.returncode == 2, proc.stdout + proc.stderr
    assert "KeyError" not in proc.stderr, proc.stderr
    # the summary must not dress an unproven clean file up as a verified one
    assert "decidable            False" in proc.stdout


def test_recovered_text_equals_the_pinned_repaired_tip():
    """Recovery must reproduce the reviewed-and-clean PR #150 head.

    This is what makes the adjudication decidable rather than merely plausible:
    the transform applied to ``main`` lands exactly on the version of the file
    that a human already reviewed as clean. The tip is pinned to an immutable
    commit, so the reference survives the PR being merged and its branch
    deleted.
    """
    text = AGENTS_MD.read_text(encoding="utf-8")
    if cyrillic_count(text) == 0:
        pytest.skip("AGENTS.md on this revision is already repaired — nothing to recover")
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
    end-to-end invocation catches that — the audit function returns fine. The
    printed numbers are cross-checked against ``--json`` so the summary cannot
    drift from the machine-readable result in either working-tree state.
    """
    proc = _run_cli()
    assert "KeyError" not in proc.stderr, proc.stderr
    assert proc.returncode in (0, 1), proc.stdout + proc.stderr

    machine = _run_cli("--json")
    assert machine.returncode == proc.returncode, machine.stdout + machine.stderr
    result = json.loads(machine.stdout)
    assert f"Cyrillic             {result['cyrillic_before']} -> {result['cyrillic_after']}" in proc.stdout
    assert f"  lines                {result['lines']}" in proc.stdout
    if result["oracle_checked"]:
        assert "insertions-only" in proc.stdout
        assert f"reproduced={result['oracle_reproduced']}" in proc.stdout


# --- the second corruption class (outer codec pass) -------------------------


def shadow(text: str) -> str:
    """UTF-8 bytes reinterpreted through ``SHADOW_CODEC`` — the outer pass."""
    return text.encode("utf-8").decode(SHADOW_CODEC)


def test_shadow_heal_inverts_the_outer_pass_on_clean_text():
    """The outer pass is reachable from clean text and exactly reversible.

    Its domain is the codec's own repertoire, not "lines that look wrong": a line
    is shadow-corrupted when re-reading it *through the codec* yields valid UTF-8.
    An em dash is outside CP775's repertoire, so a line carrying one cannot be
    shadow-corrupted and is left alone — which is why this pass is invisible to
    the Cyrillic test and needed its own instrument.
    """
    for original in [f"a {chr(0x00F6)} b", f"{chr(0x00B7)} middot", "plain ascii", ""]:
        shadowed = shadow(original)
        healed, _ = heal_shadow(shadowed)
        assert healed == original, original
    # a line the codec cannot represent is left byte-identical, never mangled
    for outside in [f"a {EM_DASH} b", f"genuine {chr(0x0100)} line"]:
        healed, changed = heal_shadow(outside)
        assert healed == outside
        assert changed == 0


def test_shadow_adjudication_is_proved_by_the_oracle_not_the_codec():
    """A wrong codec cannot reproduce the oracle, so the oracle names the codec.

    This is the property that lets ``--shadow`` exist without trusting a codec
    table: the heal is accepted only when the text it produces then satisfies the
    byte-oracle test. Every other candidate codec is rejected *by the oracle*,
    not by a hardcoded preference.
    """
    text = _rev("AGENTS.md", GATE2_PARENT_REV)
    oracle = _rev("AGENTS.md", ORACLE_REV)
    result, healed = audit_shadow(text, oracle)
    assert result["shadow_adjudicated"] is True
    assert result["shadow_lines_healed"] > 0
    assert result["oracle_reproduced"] is True
    # the outer pass is not the class audit() decides on its own
    assert audit(text, oracle)["decidable"] is False

    reproducing = []
    for codec in ["cp775", "cp437", "cp850", "cp866", "latin-1"]:
        candidate, _ = heal_shadow(text, codec=codec)
        if audit(candidate, oracle)["oracle_reproduced"]:
            reproducing.append(codec)
    assert reproducing == [SHADOW_CODEC], reproducing


def test_gate2_parent_agents_md_repair_is_byte_identical_to_the_pipeline():
    """#143's ``AGENTS.md`` is adjudicated: one shadow heal then the CP866 repair.

    The digested value is recomputed from the pinned revision, so the claim in
    the evidence document is re-derivable rather than asserted.
    """
    text = _rev("AGENTS.md", GATE2_PARENT_REV)
    if text is None:
        pytest.skip(f"gate-2 parent {GATE2_PARENT_REV} unavailable in this clone")
    oracle = _rev("AGENTS.md", ORACLE_REV)
    # Read the corruption off the pinned revision that carried it, not off the
    # moving branch `origin/main`: `main` is now repaired, so "origin/main is
    # corrupt" is a premise that expires with the very repair this instrument
    # guards. `healed` is a superset of the corrupt text the file grew from, so
    # it must still start with that revision's bytes.
    corrupted_main = _rev("AGENTS.md", CORRUPTION_COMMIT)
    if corrupted_main is None or cyrillic_count(corrupted_main) == 0:
        pytest.skip(f"pinned corrupt revision {CORRUPTION_COMMIT} unavailable in this clone")
    healed, changed = heal_shadow(text)
    assert changed > 0
    assert healed.startswith(corrupted_main), "the cp775 undo restores the pinned corrupt bytes"
    assert cyrillic_count(healed) == cyrillic_count(corrupted_main), (
        "the outer heal must not touch the inner CP866 class — that is recover()'s job"
    )
    repaired, _ = recover(healed)
    assert hashlib.sha256(repaired.encode("utf-8")).hexdigest() == GATE2_PARENT_REPAIRED_SHA256
    result = audit(repaired, oracle)
    assert result["oracle_reproduced"] is True
    assert result["oracle_alterations"] == []


def test_exit_code_does_not_call_a_divergent_clean_file_verified():
    """A mojibake-free file that alters oracle lines is not "clean and verified".

    Exit 1 is the adjudication's positive claim. A file can lose its Cyrillic and
    still replace oracle content; collapsing that into exit 1 would report the
    defect class this whole instrument exists to catch. Only a corroborating
    oracle licenses exit 1 — anything else is exit 2.
    """
    oracle = _rev("AGENTS.md", ORACLE_REV)
    assert oracle is not None

    assert exit_code(audit("nothing wrong here\n", oracle=None)) == 2, "no oracle → unproven"

    # clean, oracle present, but it replaces an oracle line
    divergent = oracle.replace("Arkadia", "Arcadia", 1)
    assert divergent != oracle, "the fixture must actually diverge"
    result = audit(divergent, oracle)
    assert result["cyrillic_before"] == 0 and result["corrupted_lines"] == 0
    assert result["oracle_reproduced"] is False
    assert result["oracle_alterations"], "a replaced oracle line must be reported"
    assert exit_code(result) == 2

    # a file whose recovery is actually performed earns exit 0
    live = AGENTS_MD.read_text(encoding="utf-8")
    corrupted = live if cyrillic_count(live) else _rev("AGENTS.md", "origin/main")
    assert exit_code(audit(corrupted, oracle)) == 0

    # ...and the recovered text, now clean and oracle-corroborated, earns exit 1.
    # Exit 1 is "clean and verified", not "a repair was needed" — the two are
    # different claims and must not be collapsed into one code.
    recovered, _ = recover(corrupted)
    assert exit_code(audit(recovered, oracle)) == 1


def _rev(path: str, rev: str) -> str | None:
    proc = subprocess.run(
        ["git", "-C", str(ROOT), "show", f"{rev}:{path}"], capture_output=True
    )
    if proc.returncode != 0:
        return None
    return proc.stdout.decode("utf-8")


def test_cli_shadow_emits_the_end_state_not_the_intermediate_heal(tmp_path):
    """``--shadow --emit-recovered`` must write the finished file.

    The intermediate shadow heal still carries the CP866 defect, so writing it
    would hand a branch a file that looks repaired by the flag it was produced
    with and is not. The emitted bytes are therefore checked against the same
    two-stage pipeline the adjudication defines, and against the Cyrillic test.

    The oracle is resolved as ``<rev>:--path``, so a scratch path has none and
    the run is necessarily undecided (exit 2). That is the documented behaviour,
    not a defect: the emitted bytes are still the end state, which is the
    property under test here.
    """
    source = _rev("AGENTS.md", GATE2_PARENT_REV)
    if source is None:
        pytest.skip(f"gate-2 parent {GATE2_PARENT_REV} unavailable in this clone")
    scratch = tmp_path / "AGENTS.md"
    scratch.write_text(source, encoding="utf-8")
    out = tmp_path / "healed.md"

    proc = _run_cli("--path", str(scratch), "--shadow", "--emit-recovered", str(out))
    assert "KeyError" not in proc.stderr, proc.stderr
    assert proc.returncode == 2, "a scratch path cannot resolve an oracle"
    assert out.exists(), proc.stdout + proc.stderr
    emitted = out.read_text(encoding="utf-8")
    assert cyrillic_count(emitted) == 0, "the emitted file must be fully repaired"
    assert hashlib.sha256(emitted.encode("utf-8")).hexdigest() == GATE2_PARENT_REPAIRED_SHA256
    assert "shadow cp775" in proc.stdout, proc.stdout


def test_shadow_heal_is_a_no_op_when_there_is_no_outer_pass():
    """Without an outer pass there is nothing for ``--shadow`` to do.

    An already-repaired file must not be "healed" into something else by a flag
    that is exercised unconditionally: the transform is skipped per line when the
    inverse does not hold, so the heal returns the input unchanged and the
    adjudication declines to claim it (``shadow_adjudicated`` False).
    """
    oracle = _rev("AGENTS.md", ORACLE_REV)
    if oracle is None:
        pytest.skip(f"oracle {ORACLE_REV} unavailable in this clone")
    result, healed = audit_shadow(oracle, oracle)
    assert healed == oracle, "the heal must not alter text with no outer pass"
    assert result["shadow_lines_healed"] == 0
    assert result["shadow_adjudicated"] is False

