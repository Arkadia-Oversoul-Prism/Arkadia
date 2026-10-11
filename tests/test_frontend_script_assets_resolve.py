"""Every root-absolute <script src> in index.html must resolve to a real asset.

index.html loads /firebase-config.js before the app bundle. The Vite dev server
(used by the CP10 browser gate) 404s any root-absolute path with no file under
public/. A dangling src therefore fails the browser gate even though Vite itself
starts cleanly — this guard makes that class of defect fail at test time instead.

Domain: the Arkadia Console (``web/arkadia_console``), the primary application.
The retired Prism UI is archived under ``archive/frontend/arkadia-prism`` and is
not built or served.
"""
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONSOLE = ROOT / "web" / "arkadia_console"
INDEX = CONSOLE / "index.html"

_SCRIPT_SRC = re.compile(r"""<script\b[^>]*\bsrc\s*=\s*["']([^"']+)["']""", re.IGNORECASE)


def _root_absolute_srcs(html: str) -> list[str]:
    """Root-absolute srcs the Vite dev server resolves to a static public asset.

    /src/... is the app module graph (main.tsx), served by Vite itself and absent
    from public/, so it is excluded.
    """
    return [src for src in _SCRIPT_SRC.findall(html) if src.startswith("/") and not src.startswith("/src/")]


def _unresolved_srcs(html: str, console_root: Path) -> list[str]:
    return [src for src in _root_absolute_srcs(html) if not (console_root / "public" / src.lstrip("/")).is_file()]


def test_index_script_srcs_resolve_to_committed_assets():
    unresolved = _unresolved_srcs(INDEX.read_text(encoding="utf-8"), CONSOLE)
    assert unresolved == [], f"index.html references assets absent from public/: {unresolved}"


def test_firebase_config_default_is_present_and_credential_free():
    config = CONSOLE / "public" / "firebase-config.js"
    assert config.is_file()
    text = config.read_text(encoding="utf-8")
    assert "__ARKADIA_FIREBASE_CONFIG__" in text
    assert "apiKey" not in text, "committed default must not carry credentials"


def test_detector_flags_a_dangling_script_src():
    """Negative control: the guard must detect the defect it claims to detect."""
    html = '<html><body><script src="/firebase-config.js"></script><script src="/ghost.js"></script></body></html>'
    unresolved = _unresolved_srcs(html, CONSOLE)
    assert "/ghost.js" in unresolved
    assert "/firebase-config.js" not in unresolved
