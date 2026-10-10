"""Every root-absolute <script src> in index.html must resolve to a real asset.

index.html loads /firebase-config.js before the app bundle. The Vite dev server
(used by the CP10 browser gate) 404s any root-absolute path with no file under
public/. A dangling src therefore fails the browser gate even though Vite itself
starts cleanly — this guard makes that class of defect fail at test time instead.
"""
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PRISM = ROOT / "web" / "public_prism"
INDEX = PRISM / "index.html"

_SCRIPT_SRC = re.compile(r"""<script\b[^>]*\bsrc\s*=\s*["']([^"']+)["']""", re.IGNORECASE)


def _root_absolute_srcs(html: str) -> list[str]:
    """Root-absolute srcs the Vite dev server resolves to a static public asset.

    /src/... is the app module graph (main.tsx), served by Vite itself and absent
    from public/, so it is excluded.
    """
    return [src for src in _SCRIPT_SRC.findall(html) if src.startswith("/") and not src.startswith("/src/")]


def _unresolved_srcs(html: str, prism_root: Path) -> list[str]:
    return [src for src in _root_absolute_srcs(html) if not (prism_root / "public" / src.lstrip("/")).is_file()]


def test_index_script_srcs_resolve_to_committed_assets():
    unresolved = _unresolved_srcs(INDEX.read_text(encoding="utf-8"), PRISM)
    assert unresolved == [], f"index.html references assets absent from public/: {unresolved}"


def test_firebase_config_default_is_present_and_credential_free():
    config = PRISM / "public" / "firebase-config.js"
    assert config.is_file()
    text = config.read_text(encoding="utf-8")
    assert "__ARKADIA_FIREBASE_CONFIG__" in text
    assert "apiKey" not in text, "committed default must not carry credentials"


def test_detector_flags_a_dangling_script_src():
    """Negative control: the guard must detect the defect it claims to detect."""
    html = '<html><body><script src="/firebase-config.js"></script><script src="/ghost.js"></script></body></html>'
    unresolved = _unresolved_srcs(html, PRISM)
    assert "/ghost.js" in unresolved
    assert "/firebase-config.js" not in unresolved
