"""An Android JVM unit test may only touch a framework class it can actually run.

``org.json`` and ``android.*`` are Android *framework* classes. On the JVM
unit-test classpath they resolve to the stub ``android.jar``, whose every method
throws ``RuntimeException("Method ... not mocked")``. A test that reaches one of
them therefore cannot pass, and because ``sonata-android``'s gate runs
``testDebugUnitTest`` **before** ``assembleDebug``, the failure also suppresses
the debug APK.

That is not hypothetical. Measured on ``main`` ``bb19aabd`` (run
``45365917578``, and on the ``main`` push run ``37261583101`` of 2026-10-05)::

    com.arkadia.sonata.MieMusicalObjectTest > cloneProvenanceAndNameSurviveJson FAILED
        java.lang.RuntimeException at MieMusicalObjectTest.kt:45
    8 tests completed, 1 failed
    Execution failed for task ':app:testDebugUnitTest'.

Line 45 is ``val json = result.toJson()``; ``toJson()`` builds an
``org.json.JSONObject``. Gate 05 had deliberately kept the unit test independent
of the Android JSON runtime (``3de223c6``); Gate 06 (``33c59362``) re-introduced
the dependency in a new test and nothing recorded the invariant, so the
regression shipped and the Android gate stayed red.

The detector reads *references*, not imports: the failing line calls
``org.json.JSONObject`` fully qualified and carries no ``import org.json`` at all,
so an import-only scan would be silent on the exact defect this guard exists for.

The domain is derived from the tracked corpus, and the satisfier is resolved from
the module's own Gradle files (a literal coordinate, or a version-catalog
accessor resolved through ``gradle/libs.versions.toml``), so the guard states
"the classpath satisfies the reference" rather than restating a dependency list.
"""

from __future__ import annotations

import re
import subprocess
import tomllib
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]

#: Framework packages that are stubbed on the JVM unit-test classpath, mapped to
#: the Maven coordinate that provides a real implementation for tests. A package
#: with no entry here has no JVM substitute: a unit test may not reference it.
JVM_SATISFIERS: dict[str, tuple[str, str]] = {
    "org.json": ("org.json", "json"),
}

#: `android.` but not `androidx.` — the latter ships real jars, not stubs.
_FRAMEWORK_REFERENCE = re.compile(r"\b(org\.json|android)\.[A-Za-z]")
_TEST_IMPLEMENTATION = re.compile(r"testImplementation\s*\(\s*([^)\s]+)\s*\)")
_LITERAL_COORDINATE = re.compile(r'^"([^:"]+):([^:"]+)(?::[^"]*)?"$')


def unit_test_sources(root: Path = ROOT) -> list[Path]:
    """Every tracked Kotlin file under a ``src/test`` tree, at any depth."""
    result = subprocess.run(
        ["git", "ls-files", "-z", "--", "*.kt"],
        cwd=root,
        capture_output=True,
        text=True,
        check=True,
    )
    return [
        root / p
        for p in result.stdout.split("\0")
        if p and "/src/test/" in p
    ]


def framework_references(source: str) -> set[str]:
    """Framework packages the source *references*, however it names them."""
    return {match.group(1) for match in _FRAMEWORK_REFERENCE.finditer(source)}


def _gradle_module_dir(source: Path, root: Path) -> Path | None:
    """The Gradle project that owns ``source`` — the nearest ancestor with a build file."""
    for candidate in source.parents:
        if (candidate / "build.gradle.kts").is_file() or (
            candidate / "build.gradle"
        ).is_file():
            return candidate
        if candidate == root:
            break
    return None


def _catalog_for(module_dir: Path, root: Path) -> dict[str, tuple[str, str]]:
    """The version catalog visible to ``module_dir``, keyed by library alias."""
    for candidate in module_dir.parents:
        catalog = candidate / "gradle" / "libs.versions.toml"
        if catalog.is_file():
            data = tomllib.loads(catalog.read_text(encoding="utf-8"))
            libraries: dict[str, tuple[str, str]] = {}
            for alias, entry in data.get("libraries", {}).items():
                if isinstance(entry, dict) and "group" in entry and "name" in entry:
                    libraries[alias] = (entry["group"], entry["name"])
            return libraries
        if candidate == root:
            break
    return {}


def _build_text(module_dir: Path) -> str:
    for name in ("build.gradle.kts", "build.gradle"):
        path = module_dir / name
        if path.is_file():
            return path.read_text(encoding="utf-8")
    return ""


def declared_test_dependencies(
    build_text: str, catalog: dict[str, tuple[str, str]]
) -> set[tuple[str, str]]:
    """``(group, artifact)`` for every ``testImplementation`` the build declares.

    Both declaration forms are read: a literal coordinate, and a version-catalog
    accessor resolved through the catalog. An accessor the catalog does not
    define (a bundle, a platform, a provider) is skipped rather than guessed.
    """
    coordinates: set[tuple[str, str]] = set()
    for raw in _TEST_IMPLEMENTATION.findall(build_text):
        literal = _LITERAL_COORDINATE.match(raw)
        if literal:
            coordinates.add((literal.group(1), literal.group(2)))
            continue
        accessor = re.match(r"^libs\.([A-Za-z0-9_.]+)$", raw)
        if accessor:
            alias = accessor.group(1).replace(".", "-")
            if alias in catalog:
                coordinates.add(catalog[alias])
    return coordinates


def findings(root: Path = ROOT) -> list[str]:
    """One entry per unit test that references a framework class it cannot run."""
    problems: list[str] = []
    for source in unit_test_sources(root):
        references = framework_references(source.read_text(encoding="utf-8"))
        if not references:
            continue
        module_dir = _gradle_module_dir(source, root)
        label = source.relative_to(root)
        if module_dir is None:
            problems.append(f"{label}: references {sorted(references)} with no Gradle module")
            continue
        declared = declared_test_dependencies(
            _build_text(module_dir), _catalog_for(module_dir, root)
        )
        for package in sorted(references):
            satisfier = JVM_SATISFIERS.get(package)
            if satisfier is None:
                problems.append(
                    f"{label}: references {package}, which has no JVM test substitute"
                )
            elif satisfier not in declared:
                problems.append(
                    f"{label}: references {package} but "
                    f"{module_dir.relative_to(root)} declares no "
                    f"{satisfier[0]}:{satisfier[1]} testImplementation"
                )
    return problems


# ---------------------------------------------------------------------------
# Live assertions
# ---------------------------------------------------------------------------


def test_the_domain_is_derived_from_the_tracked_corpus():
    sources = {p.relative_to(ROOT).as_posix() for p in unit_test_sources()}
    assert sources, "no tracked Android unit-test sources were found"
    assert "sonata-android/app/src/test/java/com/arkadia/sonata/MieMusicalObjectTest.kt" in sources
    assert "arkadia-webview-poc/app/src/test/java/com/arkadia/webviewpoc/OriginPolicyTest.kt" in sources


def test_no_unit_test_references_a_framework_class_it_cannot_run():
    assert findings() == []


def test_the_json_assertion_is_backed_by_a_real_implementation():
    """The Gate 06 node, named, so a regression is attributable rather than generic."""
    source = ROOT / "sonata-android/app/src/test/java/com/arkadia/sonata/MieMusicalObjectTest.kt"
    assert "org.json" in framework_references(source.read_text(encoding="utf-8"))
    module_dir = _gradle_module_dir(source, ROOT)
    assert module_dir is not None
    declared = declared_test_dependencies(
        _build_text(module_dir), _catalog_for(module_dir, ROOT)
    )
    assert ("org.json", "json") in declared


# ---------------------------------------------------------------------------
# Controls — the detector is exercised against the defect and against a literal
# coordinate, so a rewrite cannot leave it silently true.
# ---------------------------------------------------------------------------

_REPAIRED_BUILD = """dependencies {
    testImplementation(libs.junit)
    testImplementation(libs.org.json)
}
"""

_PRE_REPAIR_BUILD = """dependencies {
    testImplementation(libs.junit)
}
"""

_CATALOG = {"junit": ("junit", "junit"), "org-json": ("org.json", "json")}


def test_detector_is_silent_on_the_repaired_build_file():
    assert declared_test_dependencies(_REPAIRED_BUILD, _CATALOG) == {
        ("junit", "junit"),
        ("org.json", "json"),
    }


def test_detector_flags_the_pre_repair_build_file():
    """Negative control: the exact shape that shipped the regression."""
    declared = declared_test_dependencies(_PRE_REPAIR_BUILD, _CATALOG)
    assert ("org.json", "json") not in declared
    assert framework_references("val json = result.toJson()\norg.json.JSONObject(json)") == {
        "org.json"
    }


def test_detector_reads_a_literal_coordinate_dependency():
    """`arkadia-webview-poc` declares JUnit literally; that form must resolve too."""
    declared = declared_test_dependencies(
        'dependencies { testImplementation("junit:junit:4.13.2") }', {}
    )
    assert ("junit", "junit") in declared


def test_a_framework_package_without_a_jvm_substitute_is_reported():
    """Negative control for the `android.*` branch: no artifact can satisfy it."""
    assert JVM_SATISFIERS.get("android") is None
    assert framework_references("import android.util.Log") == {"android"}
    assert framework_references("import androidx.core.ktx") == set()
