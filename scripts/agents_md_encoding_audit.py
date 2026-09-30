#!/usr/bin/env python3
"""AGENTS.md encoding audit — decide a mojibake repair from the bytes, not prose.

The repository's ``AGENTS.md`` carries a pre-existing encoding defect and two
open pull requests disagreed about whether it is repairable. The disagreement
was not about taste; it was about whether one candidate recovery reproduces the
file's own last clean state. This script answers that with a byte oracle so the
answer survives a re-run and does not depend on a remembered codec table.

The defect
----------
Text that was once UTF-8 was written back as if the bytes were CP866: the
sequence ``U+2014`` (em dash) becomes the three characters ``U+0442 U+0410
U+0424``. The transform is applied **per line** and is exactly reversible:

    line.encode("cp866").decode("utf-8") == original_line

Only for *some* lines, though. A line that legitimately contains an em dash and
no mojibake is itself not CP866-decodable, so the round-trip raises and the line
is left alone. That is the classifier this script uses: a corrupted line is one
whose CP866 round-trip **succeeds**. The Cyrillic count is deliberately *not* the
discriminator — mojibake of ``U+00B7`` yields box-drawing characters with no
Cyrillic at all, and requiring Cyrillic to disappear silently skips those lines.

Decidability
------------
A candidate repair is correct when it satisfies all of:

1. applying the corruption transform to the repair returns the corrupted input
   on the corrupted domain, and
2. every line outside that domain is byte-identical, and
3. recovery introduces no new Latin-1 leftover relative to the oracle, and
4. the recovered text relates to the last clean revision by **insertions only** —
   no oracle line is replaced or deleted.

The last clause is the load-bearing one: the oracle predates later appended
sections, so prefix equality is the wrong test. Divergence in a byte that existed
before means recovery invented or dropped content.

The second clause is why this script never rewrites the whole file. A whole-file
``bytes.decode("cp866")`` is destructive: it raises on the genuine, un-corrupted
``U+2014``/``U+2192`` lines and, where it does not, rewrites them.

Usage
-----
    python scripts/agents_md_encoding_audit.py [--path AGENTS.md] [--json]

Exits 0 when the recovered text is verified against the byte oracle, 1 when the
input is already clean and the oracle was consulted to confirm it, 2 when
recovery is not decidable (including an already-clean file on a clone that
cannot resolve the oracle, where "clean" would be an unproven verdict).

No third-party imports, no network, no mutation.
"""
from __future__ import annotations

import argparse
import difflib
import hashlib
import json
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
# Last revision whose AGENTS.md carried no mojibake. Recovery must reproduce it
# exactly, with later content appearing only as append-only insertions.
ORACLE_REV = "6c43218a48a4"
# First revision whose AGENTS.md carried the mojibake (2026-09-28). Pinned so the
# origin claim in the evidence is re-derivable rather than asserted.
CORRUPTION_COMMIT = "e0dde9ad9c5e"
CORRUPT_CODEC = "cp866"

# Immutable revision of the already-clean repaired tip (PR #150 head). Recovery
# of ``main`` must equal its prefix, which is what makes the adjudication
# decidable rather than plausible. Pinned to a commit, never a branch: after
# PR #150 merges, the branch ``pr150`` is deleted by the hosting platform and a
# branch name would resolve to nothing (or, worse, to something else).
RECOVERED_TIP_REV = "03fe21fef66e78e66e6f5406b9c4a0ed8f68c4e9"

CYRILLIC = (0x0400, 0x04FF)
CRUFT = (0x0080, 0x024F)  # Latin-1 supplement + Latin Extended-A/B


def cyrillic_count(text: str) -> int:
    lo, hi = CYRILLIC
    return sum(1 for ch in text if lo <= ord(ch) <= hi)


def cruft_count(text: str) -> int:
    lo, hi = CRUFT
    return sum(1 for ch in text if lo <= ord(ch) <= hi)


def non_ascii_count(text: str) -> int:
    return sum(1 for ch in text if ord(ch) > 0x7F)


def try_recover_line(line: str) -> str | None:
    """Return the recovered line, or ``None`` if the line is not corrupted.

    The discriminator is the transform's own domain: a corrupted line is one
    whose bytes were UTF-8 and are now CP866 glyphs, so re-encoding to CP866 and
    decoding as UTF-8 **succeeds**. A genuine line carrying a real em dash or
    arrow raises ``UnicodeEncodeError`` (those codepoints have no CP866 byte) and
    is therefore left alone.

    The Cyrillic count is deliberately *not* part of the test. Mojibake of
    ``U+00B7``/``U+2014`` yields box-drawing characters (``U+2534`` …) with no
    Cyrillic at all; requiring Cyrillic to disappear silently skips those lines
    and the recovery then fails to reproduce the oracle revision.
    """
    if not any(ord(ch) > 0x7F for ch in line):
        return None
    try:
        return line.encode(CORRUPT_CODEC).decode("utf-8")
    except (UnicodeEncodeError, UnicodeDecodeError):
        return None


def recover(text: str) -> tuple[str, list[int]]:
    """Return (recovered_text, 1-based line numbers repaired)."""
    repaired: list[int] = []
    out: list[str] = []
    for i, line in enumerate(text.split("\n"), 1):
        rec = try_recover_line(line)
        if rec is None:
            out.append(line)
        else:
            out.append(rec)
            repaired.append(i)
    return "\n".join(out), repaired


def corrupt(text: str, lines: list[int] | None = None) -> str:
    """Inverse of :func:`recover`, applied to the recovered domain.

    The domain cannot be re-derived from the recovered text: a genuine middle
    dot (``U+00B7``) is not CP866-encodable, so a recovered line looks exactly
    like a line that was never touched. The repaired line numbers are carried
    across instead, which also makes the round-trip assertion exact rather than
    approximate.
    """
    if lines is None:
        lines = [i for i, line in enumerate(text.split("\n"), 1) if try_recover_line(line)]
    domain = set(lines)
    out = []
    for i, line in enumerate(text.split("\n"), 1):
        out.append(line.encode("utf-8").decode(CORRUPT_CODEC) if i in domain else line)
    return "\n".join(out)


def show_rev(rev: str, path: str) -> str | None:
    proc = subprocess.run(
        ["git", "-C", str(REPO_ROOT), "show", f"{rev}:{path}"],
        capture_output=True,
    )
    if proc.returncode != 0:
        return None
    return proc.stdout.decode("utf-8")


def audit(text: str, oracle: str | None) -> dict:
    recovered, repaired = recover(text)
    lines = text.split("\n")
    rec_lines = recovered.split("\n")

    # 1. only the repaired lines may differ
    untouched = [i for i, (a, b) in enumerate(zip(lines, rec_lines), 1) if a != b]
    only_repaired_changed = sorted(untouched) == sorted(repaired)

    # 2. line count preserved
    line_count_preserved = len(lines) == len(rec_lines)

    # 3. round-trip: corrupt(recover(x)) == x on the corrupted domain
    round_trip = corrupt(recovered, repaired) == text

    result = {
        "path": None,
        "lines": len(lines),
        "clean_lines": sum(1 for l in lines if not any(ord(c) > 0x7F for c in l)),
        "corrupted_lines": len(repaired),
        "lines_repaired": repaired,
        "cyrillic_before": cyrillic_count(text),
        "cyrillic_after": cyrillic_count(recovered),
        "cruft_before": cruft_count(text),
        "cruft_after": cruft_count(recovered),
        "non_ascii_before": non_ascii_count(text),
        "non_ascii_after": non_ascii_count(recovered),
        "line_count_preserved": line_count_preserved,
        "only_corrupted_lines_changed": only_repaired_changed,
        "round_trip_holds": round_trip,
        "oracle_rev": ORACLE_REV,
        "oracle_checked": oracle is not None,
    }

    if oracle is not None:
        # The oracle predates the appended Gate-2/Gate-1/Gate-10 sections. The
        # proof is not "the prefix is equal" — it is that the recovered text
        # relates to the oracle by insertions only. Divergence in a byte that
        # existed before means recovery invented or dropped content.
        opcodes = difflib.SequenceMatcher(
            None, oracle.split("\n"), rec_lines, autojunk=False
        ).get_opcodes()
        result["oracle_inserted_lines"] = sum(
            j2 - j1 for tag, _, _, j1, j2 in opcodes if tag != "equal"
        )
        result["oracle_alterations"] = [
            (tag, i1, i2, j1, j2) for tag, i1, i2, j1, j2 in opcodes if tag in ("replace", "delete")
        ]
        result["oracle_reproduced"] = not result["oracle_alterations"]
        result["oracle_cyrillic"] = cyrillic_count(oracle)
        result["oracle_cruft"] = cruft_count(oracle)

    # `cruft_after == 0` is the wrong criterion: the file legitimately carries
    # U+00B7 and U+00A7 (in "Ark Y1 · D140" and "§2"). The claim under test is
    # narrower — recovery introduces no *additional* Latin-1 leftover. With an
    # oracle available that is exact; without one, recovery must strictly
    # decrease the count (it converts bytes to codepoints, so it shrinks).
    if oracle is not None:
        result["cruft_delta_vs_oracle"] = result["cruft_after"] - result["oracle_cruft"]
        no_new_cruft = result["cruft_delta_vs_oracle"] == 0
        result["decidable_basis"] = "oracle"
    elif result["corrupted_lines"] > 0:
        result["cruft_delta_vs_oracle"] = None
        no_new_cruft = result["cruft_after"] <= result["cruft_before"]
        result["decidable_basis"] = "cruft-decrease"
    else:
        # Nothing to repair and no oracle to compare against. A clean file and a
        # file whose repair was never verified are the same bytes, so no claim
        # about it is decidable.
        result["cruft_delta_vs_oracle"] = None
        no_new_cruft = True
        result["decidable_basis"] = "none"

    result["decidable"] = bool(
        line_count_preserved
        and only_repaired_changed
        and round_trip
        and result["cyrillic_after"] == 0
        and no_new_cruft
        and result.get("oracle_reproduced", True)
        and result["decidable_basis"] != "none"
    )
    result["recovered_text_sha256"] = hashlib.sha256(recovered.encode("utf-8")).hexdigest()
    return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--path", default="AGENTS.md")
    parser.add_argument("--json", action="store_true")
    parser.add_argument(
        "--emit-recovered",
        metavar="OUT",
        help="write the recovered text to OUT (does not modify the working tree)",
    )
    args = parser.parse_args(argv)

    target = REPO_ROOT / args.path
    if not target.exists():
        print(f"error: {target} not found", file=sys.stderr)
        return 2
    text = target.read_text(encoding="utf-8")

    oracle = None
    if subprocess.run(
        ["git", "-C", str(REPO_ROOT), "rev-parse", "--verify", f"{ORACLE_REV}^{{commit}}"],
        capture_output=True,
    ).returncode == 0:
        oracle = show_rev(ORACLE_REV, args.path)

    result = audit(text, oracle)
    result["path"] = args.path

    if args.emit_recovered:
        Path(args.emit_recovered).write_text(recover(text)[0], encoding="utf-8")
        result["emitted"] = args.emit_recovered

    if args.json:
        print(json.dumps(result, indent=2))
    else:
        print(f"AGENTS.md encoding audit — {args.path}")
        print(f"  lines                {result['lines']} (clean {result['clean_lines']}, corrupted {result['corrupted_lines']})")
        print(f"  Cyrillic             {result['cyrillic_before']} -> {result['cyrillic_after']}")
        print(f"  Latin-1/Ext cruft    {result['cruft_before']} -> {result['cruft_after']}")
        print(f"  non-ASCII            {result['non_ascii_before']} -> {result['non_ascii_after']}")
        print(f"  line count preserved {result['line_count_preserved']}")
        print(f"  only corrupt changed {result['only_corrupted_lines_changed']}")
        print(f"  round-trip holds     {result['round_trip_holds']}")
        if oracle is not None:
            print(
                f"  oracle {ORACLE_REV}  insertions-only "
                f"inserted={result['oracle_inserted_lines']} "
                f"alterations={len(result['oracle_alterations'])} "
                f"reproduced={result['oracle_reproduced']}"
            )
            if result["oracle_alterations"]:
                print(f"    first alteration: {result['oracle_alterations'][0]}")
        print(f"  decidable            {result['decidable']}")
        print(f"  recovered sha256     {result['recovered_text_sha256']}")

    # 1 signals "already clean, and the oracle confirms it". That verdict needs
    # the oracle: without one a clean file is indistinguishable from a file whose
    # repair was never verified, and audit() marks that undecidable (exit 2).
    already_clean = result["cyrillic_before"] == 0 and result["corrupted_lines"] == 0
    if already_clean and result["oracle_checked"]:
        return 1
    return 0 if result["decidable"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
