"""Source-level fitness for the native Arkadia Console boot path.

The Android client is compiled only in CI (`build-apk.yml`), so a source defect reaches
`main` as a red build rather than a failing test. Two failure modes have already shipped:

1. `MainActivity.button(...)` opens a `TextView.apply { }` receiver. Inside that lambda the
   simple name `text` resolves to the receiver's `CharSequence` property, so passing it to
   `setTextColor(Int)` fails to compile. The field must be qualified as
   `this@MainActivity.text`.
2. `ProcessTextActivity` passes `MainActivity.EXTRA_PROCESS_TEXT`, but the constant was
   never declared, so the reference is unresolved.

These tests pin both, plus the companion wiring that consumes the extra.
"""

from __future__ import annotations

import re
from pathlib import Path

ANDROID_SRC = (
    Path(__file__).resolve().parents[1]
    / "arkadia-android/app/src/main/kotlin/com/arkadia/os"
)
MAIN_ACTIVITY = ANDROID_SRC / "MainActivity.kt"
PROCESS_TEXT_ACTIVITY = ANDROID_SRC / "ProcessTextActivity.kt"
MANIFEST = ANDROID_SRC.parents[3] / "AndroidManifest.xml"


def test_extra_process_text_constant_is_declared() -> None:
    """The constant ProcessTextActivity references must exist on MainActivity."""
    source = MAIN_ACTIVITY.read_text(encoding="utf-8")
    assert re.search(
        r"const\s+val\s+EXTRA_PROCESS_TEXT\b", source
    ), "MainActivity must declare EXTRA_PROCESS_TEXT (ProcessTextActivity references it)"


def test_extra_process_text_is_consumed_by_main_activity() -> None:
    """Declaring the extra is not enough; MainActivity must act on the passed text."""
    source = MAIN_ACTIVITY.read_text(encoding="utf-8")
    assert re.search(r"getStringExtra\(\s*EXTRA_PROCESS_TEXT\s*\)", source), (
        "MainActivity must read the EXTRA_PROCESS_TEXT it is launched with"
    )
    assert "onNewIntent" in source, (
        "MainActivity launches with SINGLE_TOP; it needs onNewIntent to receive the text"
    )


def test_no_shadowed_text_is_passed_to_set_text_color() -> None:
    """Inside a `text`-bearing adapter lambda, `text` must be qualified.

    Negative control: a bare `setTextColor(text)` is exactly the pattern that failed to
    compile, so this test detects the defect it claims to detect.
    """
    offenders = []
    for path in sorted(ANDROID_SRC.glob("*.kt")):
        for lineno, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            if re.search(r"setTextColor\(\s*text\s*\)", line):
                offenders.append(f"{path.name}:{lineno}")
    assert not offenders, (
        "unqualified `setTextColor(text)` resolves to the receiver's CharSequence "
        f"property, not the color Int: {offenders}"
    )


def test_process_text_activity_is_routed_by_the_manifest() -> None:
    """An activity with no PROCESS_TEXT filter can never receive selected text."""
    manifest = MANIFEST.read_text(encoding="utf-8")
    assert "android.intent.action.PROCESS_TEXT" in manifest, (
        "ProcessTextActivity must be registered for android.intent.action.PROCESS_TEXT, "
        "or the OS will never route a selection to it"
    )
