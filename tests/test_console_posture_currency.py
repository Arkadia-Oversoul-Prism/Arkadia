"""Boundary guard: the operator console's claims must be bound to the substrate.

The operator console (``web/console``) renders *claims* — deployment posture,
provenance edges, cited evidence, a revision stamp. Every one of those is a
statement about the repository or the runtime, and until this guard existed
nothing checked them. Measured on ``main`` @ ``9195334c``, that produced three
drifts in a console whose entire value is truthful posture:

1. **A frozen revision.** ``ae847dd`` was hardcoded in three files. It is an
   ancestor of ``main``, not the running revision, so the stamp misreported every
   later deployment.
2. **False deployment flags.** All four boundary instances carried
   ``deployed: false`` with "NOT DEPLOYED; the live host still runs the
   pre-hardening collapse" — while ``standing.ts`` in the *same bundle* said the
   boundaries were deployed and production-verified. The app contradicted itself,
   and the surfaces named by all four were served by the live runtime.
3. **A superseded premise and a dead citation.** ``executionNotWorkEvent``
   asserted "there is no durable execution -> WorkEvent identifier" and cited
   ``test_workevent_model_has_no_execution_or_job_reference_field``. That test
   does not exist in the corpus, at any revision; what exists is its opposite —
   ``test_workevent_model_has_explicit_execution_causal_reference`` — because
   PR #294 added the bridge (``weaver/execution_workevent_bridge.py``). A console
   derived from a map inherits the map's horizon, and nothing told it the map had
   moved.

Each invariant below is stated over the console's *own* declarations, so it keeps
holding as the data changes. Every detector carries a negative control proving it
reddens on the defect it claims to catch — a guard that is silent on both the
defect and its absence is not a guard.
"""

from __future__ import annotations

import re
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
CONSOLE_SRC = ROOT / "web" / "console" / "src"
DATA_DIR = CONSOLE_SRC / "data"
REVISION_MODULE = CONSOLE_SRC / "lib" / "revision.ts"

# The operator console's own source, not the primary console's. Referenced by
# path constant so the detectors can be driven against synthetic text too.
_CONSOLE_DIR = "web/console/src"


# ─────────────────────────────────────────────────────────────────────────────
# Detectors — each takes text, so a negative control can feed it a defect
# ─────────────────────────────────────────────────────────────────────────────

# A *declaration* is a whole quoted string of the form "METHOD /path". Requiring
# the closing quote keeps a path named inside a prose note (where the console
# explains where a boundary is served) from being read as a declaration — measured:
# the loose form matched `"...POST /api/x/approve, POST /api/y/run). Production..."`.
_SURFACE_RE = re.compile(r'"((?:GET|POST|PUT|PATCH|DELETE)\s+/[^"\s]+)"')
_CITED_TEST_RE = re.compile(r'"(test_[a-z0-9_]+)"')


def declared_surfaces(text: str) -> set[tuple[str, str]]:
    """Every ``"<METHOD> <path>"`` a console data file declares as proven."""
    out: set[tuple[str, str]] = set()
    for raw in _SURFACE_RE.findall(text):
        method, path = raw.split(None, 1)
        out.add((method.upper(), _normalise(path)))
    return out


def _normalise(path: str) -> str:
    """Collapse template params so ``{id}`` and ``{approval_id}`` compare equal."""
    path = path.split("?")[0].strip()
    if len(path) > 1:
        path = path.rstrip("/")
    return re.sub(r"\{[^}]+\}", "{}", path)


def cited_tests(text: str) -> set[str]:
    """Every test name a console data file cites as its evidence."""
    return set(_CITED_TEST_RE.findall(text))


def corpus_test_names(repo_root: Path | None = None) -> set[str]:
    """Every ``def test_...`` defined by a tracked test module."""
    root = repo_root or ROOT
    tracked = subprocess.run(
        ["git", "ls-files", "-z", "--", "tests/"],
        cwd=root, capture_output=True, text=True, check=True,
    ).stdout.split("\0")
    names: set[str] = set()
    for rel in tracked:
        if not rel.endswith(".py"):
            continue
        src = (root / rel).read_text(encoding="utf-8", errors="ignore")
        names.update(re.findall(r"^def (test_[a-z0-9_]+)\s*\(", src, re.M))
    return names


def served_routes() -> set[tuple[str, str]]:
    """Every ``(METHOD, path)`` the canonical application actually serves."""
    from api.main import app

    out: set[tuple[str, str]] = set()
    for path, ops in app.openapi()["paths"].items():
        for method in ops:
            out.add((method.upper(), _normalise(path)))
    return out


def unresolved_citations(text: str, corpus: set[str]) -> list[str]:
    """Cited evidence that no test module defines — a non-reproducible claim."""
    return sorted(cited_tests(text) - corpus)


def missing_surfaces(text: str, served: set[tuple[str, str]]) -> list[str]:
    """Declared surfaces the application does not serve."""
    return sorted(f"{m} {p}" for m, p in declared_surfaces(text) - served)


# ─────────────────────────────────────────────────────────────────────────────
# The console's data files, discovered from the corpus
# ─────────────────────────────────────────────────────────────────────────────

def data_files() -> list[Path]:
    return sorted(DATA_DIR.glob("*.ts"))


def test_there_are_boundary_instances_to_judge():
    """The domain must not silently empty out — an empty domain passes vacuously."""
    files = data_files()
    assert files, "no console data files found"
    total = sum(len(declared_surfaces(f.read_text(encoding="utf-8"))) for f in files)
    assert total > 0, "no declared surfaces found across the console data files"


@pytest.mark.parametrize("path", data_files(), ids=lambda p: p.name)
def test_every_cited_evidence_test_exists(path: Path):
    """A console that cites its evidence must cite evidence that exists.

    The pre-repair tree failed this on ``executionNotWorkEvent.ts``, which cited
    a test asserting the WorkEvent model has NO execution reference — a test that
    exists nowhere in the corpus, at any revision.
    """
    unresolved = unresolved_citations(path.read_text(encoding="utf-8"), corpus_test_names())
    assert not unresolved, (
        f"{path.name} cites evidence that does not exist: {unresolved}. "
        "Cite a test that is in the corpus, or drop the claim."
    )


@pytest.mark.parametrize("path", data_files(), ids=lambda p: p.name)
def test_every_declared_surface_is_served(path: Path):
    """A console that names its surfaces must name routes the app serves.

    The pre-repair tree was correct here, which is exactly why it went unnoticed:
    the surfaces were live while the posture flags said NOT DEPLOYED. This binds
    the two together.
    """
    missing = missing_surfaces(path.read_text(encoding="utf-8"), served_routes())
    assert not missing, (
        f"{path.name} declares surfaces the canonical app does not serve: {missing}"
    )


@pytest.mark.parametrize("path", data_files(), ids=lambda p: p.name)
def test_no_boundary_instance_claims_an_undeployed_posture(path: Path):
    """Every boundary instance's declared surfaces are served, so none is undeployed.

    ``deployed: false`` is only truthful if the surfaces are genuinely absent.
    The check above proves they are served, so a ``deployed: false`` here is a
    claim the substrate contradicts.
    """
    text = path.read_text(encoding="utf-8")
    if not declared_surfaces(text):
        pytest.skip(f"{path.name} declares no surfaces")
    assert "deployed: false" not in text, (
        f"{path.name} declares deployed: false while its surfaces are served. "
        "Measure the posture from the substrate, not from the map."
    )


# ─────────────────────────────────────────────────────────────────────────────
# The revision stamp must be read, not remembered
# ─────────────────────────────────────────────────────────────────────────────

def _hardcoded_revision_hits() -> dict[str, list[str]]:
    """Console source files carrying a bare commit-SHA literal."""
    hits: dict[str, list[str]] = {}
    for src in sorted(CONSOLE_SRC.rglob("*.ts*")):
        rel = src.relative_to(ROOT).as_posix()
        if rel == REVISION_MODULE.relative_to(ROOT).as_posix():
            continue  # the one module allowed to hold the derivation point
        text = src.read_text(encoding="utf-8", errors="ignore")
        found = re.findall(r"\b[0-9a-f]{7,40}\b", text)
        if found:
            hits[rel] = sorted(set(found))
    return hits


def test_the_revision_is_not_hardcoded_outside_one_module():
    """One source for the revision claim, so it cannot drift per-file again."""
    hits = _hardcoded_revision_hits()
    assert not hits, (
        "commit-SHA literals outside web/console/src/lib/revision.ts: "
        f"{hits}. Import MAP_DERIVED_FROM instead."
    )


def test_the_map_derivation_point_is_a_real_commit():
    """The provenance constant must resolve, or the console cites a phantom."""
    text = REVISION_MODULE.read_text(encoding="utf-8")
    match = re.search(r'MAP_DERIVED_FROM\s*=\s*"([0-9a-f]{7,40})"', text)
    assert match, "MAP_DERIVED_FROM not found in the revision module"
    rev = match.group(1)
    result = subprocess.run(
        ["git", "cat-file", "-e", f"{rev}^{{commit}}"],
        cwd=ROOT, capture_output=True, text=True,
    )
    assert result.returncode == 0, f"MAP_DERIVED_FROM={rev} is not a commit in this repository"


def test_the_running_revision_is_read_from_the_runtime():
    """The stamp must come from the read-only probe, not a constant."""
    text = REVISION_MODULE.read_text(encoding="utf-8")
    assert "/api/version" in text, (
        "the revision module must read GET /api/version rather than a constant"
    )
    assert "source_revision" in text, "the revision module must read source_revision"
    assert "unavailable" in text, (
        "an unreadable revision must be stated as unavailable, never guessed"
    )


# ─────────────────────────────────────────────────────────────────────────────
# Negative controls — prove each detector reddens on the defect it claims
# ─────────────────────────────────────────────────────────────────────────────

def test_negative_control_detector_flags_a_missing_citation():
    """Feed the citation detector the measured pre-repair defect."""
    corpus = {"test_workevent_model_has_explicit_execution_causal_reference"}
    defect = 'evidence: ["test_workevent_model_has_no_execution_or_job_reference_field"],'
    assert unresolved_citations(defect, corpus) == [
        "test_workevent_model_has_no_execution_or_job_reference_field"
    ]


def test_negative_control_detector_flags_an_absent_surface():
    """Feed the surface detector a route the application does not serve."""
    served = {("POST", "/api/approvals/request")}
    defect = 'surfaces: ["POST /api/approvals/request", "POST /api/approvals/nowhere"],'
    assert missing_surfaces(defect, served) == ["POST /api/approvals/nowhere"]


def test_negative_control_detector_flags_a_hardcoded_revision():
    """Feed the revision detector a stamp of the pre-repair shape."""
    defect = '<span className="topbar-meta tiny mono">ae847dd · reconciled</span>'
    assert re.findall(r"\b[0-9a-f]{7,40}\b", defect) == ["ae847dd"]


def test_positive_control_normalisation_joins_template_params():
    """``{id}`` in the console and ``{approval_id}`` in OpenAPI are one route."""
    assert _normalise("/api/approvals/{id}/approve") == _normalise(
        "/api/approvals/{approval_id}/approve"
    )
