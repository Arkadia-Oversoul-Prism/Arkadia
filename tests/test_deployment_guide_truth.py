"""Boundary guard: the deployment guide may only name things that exist.

``DEPLOYMENT_GUIDE.md`` is the repository's top-level deployment instruction. Before
this guard it described a different application: six of the seven components it listed
as "Core Components Built" -- ``arkana_app.py``, ``codex_brain.py``,
``arkadia_drive_sync.py``, ``arkadia_console.py``, ``models.py``, ``db.py`` -- existed at
no path in the tree, its required-environment block named two Google Drive variables that
no module reads, its deploy instructions pointed at the placeholder host
``your-app.onrender.com`` rather than the canonical origin, and its closing line asserted
the system was "ready for immediate deployment".

A reader following that guide could not deploy Arkadia. An agent reading it would
describe a runtime that does not exist. Both are documentation-truth defects of the class
this repository already guards elsewhere (a claim must be re-derivable, not asserted).

The guide's central claim is which application is deployed, so this guard names the
active console (``web/arkadia_console``) and the serving path that fronts it. That places
it in the derived console-contract domain (``scripts/console_contract_domain.py``), which
is executed by a *blocking* step in ``prism-console-contract.yml`` — a guard reached only
by a non-judging broad-suite step would be decoration.

Two properties are pinned here:

1. every repository path the guide names in an inline code span resolves on disk, and
2. the guide names the canonical production origin and the read-only revision probe, and
   presents no second deployment as production.

Controls
--------
``test_detector_reports_the_pre_repair_component_list`` feeds the detector the exact
component line the guide carried before the repair and asserts it reports the missing
names. A detector that passes the broken text proves nothing about the repaired one.

``test_detector_ignores_routes_and_urls`` is the polarity control: routes (``/health``),
URLs (``https://...``) and build outputs (``dist/``) are not repository paths and must not
be reported missing, or the guard would be trivially false.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
GUIDE = REPO_ROOT / "DEPLOYMENT_GUIDE.md"

# ADR-016: one canonical, reconciled deployment. The origin is also the default in
# scripts/production_runtime_probe.py.
CANONICAL_ORIGIN = "https://arkadia-qzu4.onrender.com"
REVISION_PROBE = "/api/version"

_SPAN = re.compile(r"`([^`\n]+)`")
_SEGMENT = re.compile(r"^[A-Za-z0-9_.-]+$")
_EXTENSIONS = (
    ".py", ".sh", ".json", ".md", ".txt", ".yml", ".yaml",
    ".ts", ".tsx", ".js", ".toml", ".cfg", ".ini",
)
_EXTENSIONLESS_FILES = {"Dockerfile", "Makefile", "Procfile", "CODEOWNERS"}


def is_repository_path(span: str) -> bool:
    """True when an inline span denotes a repository path rather than a route or URL."""
    span = span.strip()
    if not span or " " in span:
        return False
    if span.startswith("/") or "://" in span or "{" in span or "$" in span:
        return False
    if ":" in span:
        return False
    if span.endswith("/"):
        # A trailing slash denotes build output (`dist/`) or a directory named in prose.
        return False
    segments = span.split("/")
    if not all(_SEGMENT.match(segment) for segment in segments):
        return False
    if len(segments) > 1:
        return True
    return span.lower().endswith(_EXTENSIONS) or span in _EXTENSIONLESS_FILES


def named_repository_paths(text: str) -> list[str]:
    return sorted({span.strip() for span in _SPAN.findall(text) if is_repository_path(span)})


def missing_repository_paths(text: str, root: Path = REPO_ROOT) -> list[str]:
    return [path for path in named_repository_paths(text) if not (root / path).exists()]


def _guide_text() -> str:
    return GUIDE.read_text(encoding="utf-8")


def test_guide_exists() -> None:
    assert GUIDE.is_file(), f"the deployment guide is missing at {GUIDE}"


def test_every_repository_path_named_by_the_guide_exists() -> None:
    named = named_repository_paths(_guide_text())
    # A guard with an empty domain is not a guard: the guide names the app, the API,
    # the entrypoint and the ADR, so the extractor must find more than a couple.
    assert len(named) >= 8, f"the extractor found too few repository paths: {named}"
    assert missing_repository_paths(_guide_text()) == []


def test_guide_names_the_canonical_origin_and_the_revision_probe() -> None:
    text = _guide_text()
    assert CANONICAL_ORIGIN in text
    assert REVISION_PROBE in text


def test_guide_presents_no_second_deployment_as_production() -> None:
    text = _guide_text()
    assert "vercel.app" not in text
    # The pre-repair placeholder host: a reader cannot deploy against it.
    assert "your-app.onrender.com" not in text


def test_guide_does_not_claim_production_acceptance() -> None:
    text = _guide_text()
    assert "ready for immediate deployment" not in text
    assert "human decision" in text


# --- controls -------------------------------------------------------------------

PRE_REPAIR_COMPONENT_LINE = """### **Core Components Built:**
- **FastAPI Backend** (`arkana_app.py`) - All endpoints working
- **AI Brain System** (`codex_brain.py`) - Gemini integration with fallbacks
- **Google Drive Sync** (`arkadia_drive_sync.py`) - Corpus management
- **Interactive Console** (`arkadia_console.py`) - CLI interface
- **Database Models** (`models.py`, `db.py`) - SQLAlchemy setup
"""


def test_detector_reports_the_pre_repair_component_list() -> None:
    missing = missing_repository_paths(PRE_REPAIR_COMPONENT_LINE)
    assert missing == [
        "arkadia_console.py",
        "arkadia_drive_sync.py",
        "arkana_app.py",
        "codex_brain.py",
        "db.py",
        "models.py",
    ]


def test_detector_ignores_routes_and_urls() -> None:
    prose = (
        "Probe `GET /api/version` and `/health`, then load "
        "`https://arkadia-qzu4.onrender.com/api/version`. The build writes `dist/` "
        "and reads `PORT` from the platform. Call `api.main:app` via `railway.json`."
    )
    assert named_repository_paths(prose) == ["railway.json"]
    assert missing_repository_paths(prose) == []


@pytest.mark.parametrize(
    "span, expected",
    [
        ("web/arkadia_console", True),
        ("api/main.py", True),
        ("Dockerfile", True),
        ("dist/", False),
        ("/health", False),
        ("/api/commune/threads/{thread_uuid}", False),
        ("https://arkadia-qzu4.onrender.com/api/version", False),
        ("GET /api/version", False),
        ("api.main:app", False),
        ("RENDER_GIT_COMMIT", False),
        ("openclaw/", False),
    ],
)
def test_span_classifier(span: str, expected: bool) -> None:
    assert is_repository_path(span) is expected
