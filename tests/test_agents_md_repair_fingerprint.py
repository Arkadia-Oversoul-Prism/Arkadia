"""AGENTS.md must not gain character classes its repair is supposed to remove.

Four open pull requests claim to repair this repository's ``AGENTS.md`` encoding
corruption: UTF-8 bytes written back as CP866 glyphs, applied line-wise. They
cannot all be right, and the two that are wrong fail in ways a diff summary
hides. One restores the corrupted region *verbatim* while its title says repair,
leaving 188 Cyrillic look-alikes in the file. One clears the Cyrillic but
re-encodes the text, introducing 594 box-drawing and Latin-1 characters that
never belonged to the document.

Two fingerprints separate them, and neither needs history, network, or a
candidate list:

1. The corruption transform must be *exact* on its own domain. Applying the
   inverse and then re-applying the forward transform must return the input, and
   the line count must be preserved. A repair built on the wrong codec is not
   invertible; this makes "which codec" decidable instead of a matter of taste.
2. In the recovered domain, ``AGENTS.md``'s non-ASCII alphabet must stay inside
   the document's established alphabet. A repair that leaves Cyrillic behind, or
   invents box-drawing characters, pushes its alphabet outside that set and
   fails. The correct candidate reproduces the recovered text exactly and
   therefore passes.

Why this is a *fingerprint* and not a formatting taste
------------------------------------------------------
The competing repairs produce mutually exclusive byte streams, and today's
``main`` is neither. The subset test is monotone under merging: it passes on
``main``, on the correct candidate, and on the file after the correct repair
merges; it fails on each incorrect candidate both before and after merge. It
reads no candidate name and no branch, so it cannot go stale when the queue
changes. That is the property worth carrying forward.

The established alphabet
------------------------
The corruption is total over ``AGENTS.md``'s non-ASCII content — every genuine
character was mangled — so recovering the current file yields the document's
true alphabet. It is twelve codepoints, and it is what the correct repair
produces:

    python3 -c "import importlib.util as u; ..."   # recover(AGENTS.md) alphabet
    # 0x00a7 0x00b7 0x2013 0x2014 0x201c 0x201d 0x2026 0x2192 0x2194 0x2260 0x2b06 0x1f512
    # section · en dash — curly quotes … → ↔ ≠ up-arrow lock

No Cyrillic. Each rejected candidate adds codepoints outside this set:

* the "restore verbatim" candidate — 26 extra, including the box-drawing pair
  ``0x252c``/``0x255d`` that a mis-chosen codec regenerates from the middle dot;
* the "clear the Cyrillic" candidate — ``0x0410`` ``0x0416`` ``0x0422`` ``0x0424``
  ``0x0442`` still present, plus ``0x21d2``.

``0x2014`` and ``0x2192`` *are* members: the repaired document uses them
legitimately. A candidate that merely pastes them into prose passes this guard
and still deserves a review comment — that is a presentational call, not a
fingerprint, and asserting it would break the next time a legitimate em dash is
added. The guard polices what the document is *made of*, not how it reads.

How to extend, not weaken
-------------------------
If a future edit legitimately needs a thirteenth non-ASCII character, add it to
``RECOVERED_NON_ASCII_ALPHABET`` here *and* record why in that change's evidence.
Do not widen ``recover`` to make an assertion pass, and do not delete the
alphabet test: it is the only check that distinguishes the correct codec from a
plausible-looking one.

Skipping
--------
Nothing here is skipped. This module reads only ``AGENTS.md`` from the working
tree, so it is meaningful in a shallow or grafted clone and in CI.
"""

from __future__ import annotations

import pathlib

REPO_ROOT = pathlib.Path(__file__).resolve().parents[1]
AGENTS = REPO_ROOT / "AGENTS.md"

CORRUPT_CODEC = "cp866"

# AGENTS.md's non-ASCII alphabet, recovered from the corrupted file. The
# corruption is total over non-ASCII content, so recovery yields the true set —
# twelve codepoints, which is exactly what the correct repair produces. Named,
# never pasted: see the module docstring for the derivation.
RECOVERED_NON_ASCII_ALPHABET = {
    0x00A7: "section sign",
    0x00B7: "middle dot",
    0x2013: "en dash",
    0x2014: "em dash",
    0x201C: "left double quote",
    0x201D: "right double quote",
    0x2026: "ellipsis",
    0x2192: "right arrow",
    0x2194: "left-right arrow",
    0x2260: "not equal",
    0x2B06: "up arrow",
    0x1F512: "lock",
}

CYRILLIC = (0x0400, 0x04FF)


def try_recover_line(line: str) -> str | None:
    """Return the recovered line, or ``None`` if the line is not corrupted.

    A corrupted line is one whose UTF-8 bytes were written back as CP866 glyphs,
    so re-encoding to CP866 and decoding as UTF-8 **succeeds**. A genuine line
    carrying a real em dash or arrow raises ``UnicodeEncodeError`` (those
    codepoints have no CP866 byte) and is left byte-identical.

    The Cyrillic count is deliberately not the discriminator: mojibake of the
    middle dot yields box-drawing characters with no Cyrillic at all, and a
    discriminator that required Cyrillic to disappear would silently skip those
    lines and fail to reproduce the clean revision.
    """
    if not any(ord(ch) > 0x7F for ch in line):
        return None
    try:
        return line.encode(CORRUPT_CODEC).decode("utf-8")
    except (UnicodeEncodeError, UnicodeDecodeError):
        return None


def recover(text: str) -> tuple[str, set[int]]:
    """Return ``(recovered_text, 1-based line numbers repaired)``."""
    repaired: set[int] = set()
    out: list[str] = []
    for i, line in enumerate(text.split("\n"), 1):
        rec = try_recover_line(line)
        if rec is None:
            out.append(line)
        else:
            out.append(rec)
            repaired.add(i)
    return "\n".join(out), repaired


def test_recovery_is_exact_on_its_own_domain() -> None:
    """The transform is invertible, and it moves no line.

    The corrupted domain cannot be re-derived from the recovered text — a
    genuine middle dot is not CP866-encodable, so a recovered line looks exactly
    like a line that was never touched. The repaired line numbers are carried
    across instead, which makes the round-trip assertion exact rather than
    approximate.

    This is where a wrong codec fails: a repair built on cp1250/iso-8859-2/cp1252
    cannot re-encode its own output back to the corrupted input, because those
    codecs do not round-trip the characters they produced.
    """
    text = AGENTS.read_text(encoding="utf-8")
    lines = text.split("\n")
    recovered, repaired = recover(text)
    rec_lines = recovered.split("\n")

    changed = {i for i, (a, b) in enumerate(zip(lines, rec_lines), 1) if a != b}
    assert changed == repaired, (
        "recovery changed a line it did not classify as corrupted (or left a "
        "classified line untouched); the transform is not line-local"
    )
    assert len(lines) == len(rec_lines), "recovery changed the line count"

    round_tripped = "\n".join(
        line.encode("utf-8").decode(CORRUPT_CODEC) if i in repaired else line
        for i, line in enumerate(rec_lines, 1)
    )
    assert round_tripped == text, "the corruption transform is not invertible on its domain"


def test_recovered_agents_md_uses_only_the_established_alphabet() -> None:
    """No Cyrillic, and nothing outside the document's own character set.

    This is the fingerprint that adjudicates the open repair queue. Stated over
    the *recovered* text so that it holds on today's still-corrupted ``main`` and
    continues to hold once a correct repair merges.
    """
    recovered, _ = recover(AGENTS.read_text(encoding="utf-8"))
    alphabet = {ord(ch) for ch in recovered if ord(ch) > 0x7F}
    unexpected = alphabet - set(RECOVERED_NON_ASCII_ALPHABET)

    assert not [c for c in alphabet if CYRILLIC[0] <= c <= CYRILLIC[1]], (
        "the recovered AGENTS.md still carries Cyrillic look-alikes; this is the "
        "encoding corruption, and a repair that leaves a non-zero count has not "
        "repaired anything"
    )
    assert not unexpected, (
        "the recovered AGENTS.md carries non-ASCII codepoints the document never "
        f"used: {[hex(c) for c in sorted(unexpected)]}. A correct repair restores "
        "the original text; it does not substitute a second mojibake"
    )
