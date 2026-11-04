"""Lane 3 — Knowledge OS graph health: a count must be read, not enumerated.

``knowledge/graph_health.py`` is the single source of truth for graph health and
feeds ``GET /api/knowledge/status`` (``graph_health``), ``GET /api/knowledge/graph/health``
and the ``/relationships`` component count.

The defect this guard holds: ``_count()`` read its scalar with ``list(row)[0]``.
``knowledge.db.execute_one()`` returns a **dict keyed by column name**, so
iterating the row yields the *keys* and ``list(row)[0]`` returned the column name
(``"COUNT(*)"``) rather than the value. Every consumer that divided by or compared
that "count" then raised ``TypeError: unsupported operand type(s) for /: 'str' and 'str'``,
and ``evaluate_graph_health()``'s ``except`` collapsed the whole evaluation to::

    {"overall": "error", "error": "unsupported operand type(s) for /: 'str' and 'str'", "checks": {}}

Measured live on canonical ``main`` (deployed revision ``46d85e2d``): the public
``/api/knowledge/status`` served ``graph_health: "error"`` while the graph held
40 notes and 3 edges. It is **not** data-dependent — an empty database reproduces
it, because the empty path still divides (``orphan_count / total_nodes``) once
``total_nodes`` is truthy — so it was a total loss of the health surface.

The boundary is the *return shape of the canonical helper*. The guard therefore
binds the reading to the real ``execute_one`` rather than restating a count, and
carries a negative control that drives the pre-repair expression against the same
row so the detector cannot be disarmed by rewriting the module.

Scope note: the route-level assertion (``GET /api/knowledge/status`` serving a real
verdict) lives in ``tests/test_knowledge_status_read_boundary.py``, which already
covers that surface. It is deliberately **not** duplicated here: this file is
executed by ``knowledge-connection-lifecycle-guard.yml``, a stdlib+pytest-only gate
that installs no application dependency, and importing ``fastapi`` here would
require widening that job's install step.

See ``docs/control-plane/evidence/lane3-graph-health-count-read-01/EVIDENCE.md``.
"""
from __future__ import annotations

from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture()
def seeded_db(tmp_path, monkeypatch):
    """A private knowledge DB holding a small, known graph.

    ``knowledge.db`` snapshots ``ARKADIA_DB_PATH`` into ``_DB_PATH`` at import
    time, so the module constant is rebound too — otherwise the fixture would
    measure whatever DB the session already opened.
    """
    import knowledge
    from knowledge import db as kdb

    db_path = tmp_path / "arkadia.db"
    monkeypatch.setenv("ARKADIA_DB_PATH", str(db_path))
    monkeypatch.setattr(kdb, "_DB_PATH", db_path)
    monkeypatch.setattr(knowledge, "_DB_PATH", db_path, raising=False)
    if hasattr(kdb._local, "conn"):
        kdb._local.conn = None
    yield kdb
    if hasattr(kdb._local, "conn"):
        kdb._local.conn = None


def _add_note(kdb, uuid: str, embedding_status: str = "complete") -> int:
    kdb.execute(
        "INSERT INTO notes(uuid, title, content, vault_path, note_type, embedding_status) "
        "VALUES (?, ?, '', ?, 'note', ?)",
        (uuid, f"note {uuid}", f"vault/{uuid}.md", embedding_status),
    )
    row = kdb.execute_one("SELECT id FROM notes WHERE uuid = ?", (uuid,))
    return row["id"]


def _add_edge(kdb, source: int, target: int, relationship: str = "references") -> None:
    kdb.execute(
        "INSERT INTO graph_edges(source_note_id, target_note_id, relationship) VALUES (?, ?, ?)",
        (source, target, relationship),
    )


# ---------------------------------------------------------------------------
# The helper contract this module depends on
# ---------------------------------------------------------------------------


def test_execute_one_returns_a_dict_keyed_by_column_name(seeded_db):
    """The precondition of the defect: the row is a dict, so iteration yields keys."""
    _add_note(seeded_db, "a")
    row = seeded_db.execute_one("SELECT COUNT(*) FROM notes")
    assert isinstance(row, dict), "the canonical helper's shape is what the defect misread"
    assert list(row)[0] == "COUNT(*)", (
        "iterating the row yields the column *name*; this is the exact value the "
        "pre-repair `list(row)[0]` returned as a count"
    )
    assert list(row.values())[0] == 1


def test_count_reads_the_value_not_the_column_name(seeded_db):
    """The repaired reading: `_count` must return the number."""
    from knowledge.graph_health import _count

    _add_note(seeded_db, "a")
    _add_note(seeded_db, "b")
    measured = _count("SELECT COUNT(*) FROM notes")
    assert measured == 2, f"_count returned {measured!r}, not the row count"
    assert not isinstance(measured, str)


def test_count_is_zero_on_an_empty_result_set(seeded_db):
    """`execute_one` returns None for no rows; the reading must stay numeric."""
    from knowledge.graph_health import _count

    assert _count("SELECT COUNT(*) FROM notes WHERE id = 999999") == 0


# ---------------------------------------------------------------------------
# The public evaluation
# ---------------------------------------------------------------------------


def test_evaluation_reports_a_healthy_graph_rather_than_a_crash(seeded_db):
    """Two connected, fully embedded notes: the evaluation must be `ok`, not `error`."""
    from knowledge.graph_health import evaluate_graph_health

    a, b = _add_note(seeded_db, "a"), _add_note(seeded_db, "b")
    _add_edge(seeded_db, a, b)

    health = evaluate_graph_health()
    assert health["overall"] == "ok", (
        f"a clean graph evaluated to {health['overall']!r}: {health.get('error')!r}"
    )
    assert "error" not in health, "the crash envelope must not be reachable for a clean graph"
    assert set(health["checks"]) == {
        "orphan_nodes",
        "duplicate_nodes",
        "invalid_references",
        "ontology_violations",
        "embedding_completeness",
        "graph_connectivity",
    }


def test_evaluation_ratios_are_numeric(seeded_db):
    """The two divisions in the module — the exact site of the TypeError."""
    from knowledge.graph_health import evaluate_graph_health

    a, b = _add_note(seeded_db, "a"), _add_note(seeded_db, "b")
    _add_edge(seeded_db, a, b)

    checks = evaluate_graph_health()["checks"]
    assert isinstance(checks["orphan_nodes"]["orphan_ratio"], float)
    assert isinstance(checks["embedding_completeness"]["completion_ratio"], float)
    assert checks["orphan_nodes"]["total_nodes"] == 2
    assert checks["embedding_completeness"]["complete"] == 2


def test_an_empty_database_is_ok_not_error(seeded_db):
    """The defect reproduced with no data at all; an empty graph is legitimately `ok`."""
    from knowledge.graph_health import evaluate_graph_health

    health = evaluate_graph_health()
    assert health["overall"] == "ok", f"empty graph evaluated to {health.get('error')!r}"
    assert health["checks"]["orphan_nodes"]["total_nodes"] == 0


def test_pending_embeddings_surface_as_warn_with_real_counts(seeded_db):
    """A real finding must be reported with its measured numbers, not a crash."""
    from knowledge.graph_health import evaluate_graph_health

    a, b = _add_note(seeded_db, "a", "pending"), _add_note(seeded_db, "b", "pending")
    _add_edge(seeded_db, a, b)

    health = evaluate_graph_health()
    assert health["overall"] == "warn"
    completeness = health["checks"]["embedding_completeness"]
    assert completeness["total"] == 2
    assert completeness["pending"] == 2
    assert completeness["complete"] == 0


def test_a_dangling_edge_is_still_reported_as_error(seeded_db):
    """The repair must not blunt the checks: a real violation stays an error."""
    from knowledge.graph_health import evaluate_graph_health

    a, b = _add_note(seeded_db, "a"), _add_note(seeded_db, "b")
    _add_edge(seeded_db, a, b)
    # Drop the target directly so the edge outlives its note (FKs are per-connection).
    seeded_db.execute("PRAGMA foreign_keys=OFF")
    seeded_db.execute("DELETE FROM notes WHERE id = ?", (b,))

    health = evaluate_graph_health()
    assert health["checks"]["invalid_references"]["dangling_edges"] == 1
    assert health["overall"] == "error"


# ---------------------------------------------------------------------------
# The served contract
# ---------------------------------------------------------------------------


# ---------------------------------------------------------------------------
# Negative control — the pre-repair expression against the same row
# ---------------------------------------------------------------------------


def test_negative_control_the_pre_repair_expression_yields_the_column_name(seeded_db):
    """Prove the detector bites on the defect it exists to catch.

    This reproduces the pre-repair reading directly against a real row. If
    ``execute_one`` ever changed shape such that ``list(row)[0]`` *did* return the
    value, the guard above would become vacuous — this control fails first, so the
    guard cannot be silently disarmed.
    """
    _add_note(seeded_db, "a")
    row = seeded_db.execute_one("SELECT COUNT(*) FROM notes")

    pre_repair = list(row)[0]
    assert pre_repair == "COUNT(*)", (
        "the pre-repair expression no longer yields the column name; re-derive this "
        "guard against the helper's current return shape"
    )
    assert pre_repair != 1


def test_negative_control_the_pre_repair_ratio_raises(seeded_db):
    """The exact failure mode: dividing by the misread count raises TypeError."""
    _add_note(seeded_db, "a")
    row = seeded_db.execute_one("SELECT COUNT(*) FROM notes")

    pre_repair = list(row)[0]
    with pytest.raises(TypeError):
        pre_repair / pre_repair


def test_no_other_module_reads_a_row_positionally():
    """The defect class, not just the instance.

    Every reader of ``knowledge.db``'s dict rows must read them by column name; a
    positional read is the same mistake waiting to recur. Scanned over the
    ``knowledge`` package, which is the bounded domain this guard declares to the
    workflow that executes it -- an ``api/`` sweep would silently widen that
    domain past the gate's ``paths`` filter (see the ci-wiring guard).
    """
    offenders: list[str] = []
    for base in (REPO_ROOT / "knowledge",):
        for path in sorted(base.rglob("*.py")):
            for lineno, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
                stripped = line.strip()
                if stripped.startswith("#"):
                    continue
                if "list(row)[0]" in stripped or "list(rows[0])[0]" in stripped:
                    offenders.append(f"{path.relative_to(REPO_ROOT)}:{lineno}")
    assert offenders == [], f"positional read of a dict row: {offenders}"
