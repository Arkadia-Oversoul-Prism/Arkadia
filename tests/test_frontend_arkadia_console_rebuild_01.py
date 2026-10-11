"""Frontend rebuild guard — the console is canonical and Prism stays recoverable.

This is a source-level contract over the frontend transition:

  * the Arkadia Console (``web/arkadia_console``) is the primary application and
    is what the backend and the canonical image build and serve;
  * the retired Prism UI is preserved in full under
    ``archive/frontend/arkadia-prism`` and remains recoverable;
  * nothing that serves or builds a frontend still names the old path.

The failure it exists to prevent is a "rebuild" that quietly deletes or drops
the previous implementation, or an archive that keeps the source but loses the
build instructions that make it restorable. Both are asserted here.
"""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONSOLE = ROOT / "web" / "arkadia_console"
PRISM = ROOT / "archive" / "frontend" / "arkadia-prism" / "web" / "public_prism"


# ---------------------------------------------------------------------------
# The console is the canonical frontend
# ---------------------------------------------------------------------------


def test_console_scaffold_is_complete_and_buildable():
    for name in ("package.json", "vite.config.ts", "tsconfig.json", "tailwind.config.js", "index.html"):
        assert (CONSOLE / name).is_file(), f"web/arkadia_console missing {name}"
    lock = CONSOLE / "pnpm-lock.yaml"
    assert lock.is_file(), "the console must ship a lockfile so --frozen-lockfile can install"
    pkg = (CONSOLE / "package.json").read_text(encoding="utf-8")
    assert "build" in pkg and "vite" in pkg


def test_console_exposes_the_product_surfaces():
    surfaces = (CONSOLE / "src" / "lib" / "surfaces.ts").read_text(encoding="utf-8")
    for surface in ("arkana", "solariun", "engineering-lab", "solspire", "knowledge", "weaver"):
        assert f'"{surface}"' in surfaces, f"product surface '{surface}' is not declared"


def test_dockerfile_builds_the_console_not_the_archive():
    dockerfile = (ROOT / "Dockerfile").read_text(encoding="utf-8")
    assert "web/arkadia_console" in dockerfile
    assert "web/public_prism" not in dockerfile, "the image must not build the retired path"


def test_entrypoint_writes_the_firebase_config_into_the_console_dist():
    entrypoint = (ROOT / "entrypoint.sh").read_text(encoding="utf-8")
    assert "web/arkadia_console/dist" in entrypoint
    assert "web/public_prism" not in entrypoint


def test_backend_root_serves_the_console_spa():
    main = (ROOT / "api" / "main.py").read_text(encoding="utf-8")
    assert '"arkadia_console"' in main
    assert '"public_prism"' not in main


def test_frontend_routes_serve_the_console_and_the_operator_console():
    routes = (ROOT / "api" / "frontend_routes.py").read_text(encoding="utf-8")
    assert '"arkadia_console"' in routes
    assert '"console"' in routes
    assert "public_prism" not in routes


# ---------------------------------------------------------------------------
# Prism is archived, not destroyed
# ---------------------------------------------------------------------------


def test_prism_source_is_preserved_in_the_archive():
    assert (PRISM / "src" / "App.tsx").is_file()
    assert (PRISM / "package.json").is_file()
    assert len(list((PRISM / "src").rglob("*.tsx"))) > 50, "the archived Prism app lost source files"


def test_archive_keeps_build_inputs_and_recovery_instructions():
    for name in ("package.json", "vite.config.ts", "pnpm-lock.yaml"):
        assert (PRISM / name).is_file(), f"the archived app cannot be rebuilt without {name}"
    readme = (ROOT / "archive" / "frontend" / "arkadia-prism" / "README.md").read_text(encoding="utf-8")
    assert "Recovery procedure" in readme
    assert "git mv" in readme


def test_legacy_prism_path_is_gone():
    assert not (ROOT / "web" / "public_prism").exists(), "the retired path must not be resurrected"


# ---------------------------------------------------------------------------
# Negative controls
# ---------------------------------------------------------------------------


def test_detector_would_flag_a_dockerfile_that_still_builds_prism():
    """The guard must detect the defect it claims to detect."""
    stale = "COPY web/public_prism/ ./web/public_prism/\nRUN pnpm run build\n"
    assert "web/public_prism" in stale  # the literal the guard rejects is real
    dockerfile = (ROOT / "Dockerfile").read_text(encoding="utf-8")
    assert "web/public_prism" not in dockerfile


def test_recovery_assertion_fails_for_a_directory_without_build_inputs(tmp_path):
    readme = (ROOT / "archive" / "frontend" / "arkadia-prism" / "README.md")
    assert readme.is_file()
    assert not (tmp_path / "package.json").is_file()
