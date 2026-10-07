"""Gate 01 Option A: canonical Portfolio -> Initiative substrate proof.

Synthetic data only. This test exercises the existing Weaver relational store,
not a parallel persistence layer.
"""
from __future__ import annotations

import re
import sqlite3

import pytest

import weaver.enterprise_orchestration as eo


def test_portfolio_to_initiative_is_canonical_and_traversable(tmp_path, monkeypatch):
    db_path = tmp_path / "solspire_projects.db"
    monkeypatch.setattr(eo, "_DB_PATH", str(db_path))
    store = eo.EnterpriseOrchestrationStore()
    subject = "gate01-test-subject"
    correlation_id = "gate01-correlation"

    portfolio = store.portfolio(
        subject=subject,
        name="Synthetic Portfolio",
        mandate="Gate 01 proof fixture",
        correlation_id=correlation_id,
    )
    initiative = store.initiative(
        subject=subject,
        portfolio_id=portfolio.id,
        name="Synthetic Initiative",
        objective="Prove the canonical Portfolio -> Initiative edge",
    )

    assert re.fullmatch(r"portfolio-[0-9a-f]{32}", portfolio.id)
    assert re.fullmatch(r"initiative-[0-9a-f]{32}", initiative.id)
    assert store.get_portfolio(subject=subject, portfolio_id=portfolio.id).id == portfolio.id
    assert store.get_initiative(subject=subject, initiative_id=initiative.id).portfolio_id == portfolio.id

    forward = store.forward_walk(subject=subject, kind="PORTFOLIO", record_id=portfolio.id)
    assert {(r["kind"], r["id"]) for r in forward["records"]} == {
        ("PORTFOLIO", portfolio.id),
        ("INITIATIVE", initiative.id),
    }

    reverse = store.reverse_walk(subject=subject, kind="INITIATIVE", record_id=initiative.id)
    assert {(r["kind"], r["id"]) for r in reverse["records"]} == {
        ("INITIATIVE", initiative.id),
        ("PORTFOLIO", portfolio.id),
    }
    assert reverse["complete"] is True

    with sqlite3.connect(db_path) as conn:
        tables = {
            row[0]
            for row in conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name LIKE 'ew_%'"
            )
        }
        assert {"ew_portfolios", "ew_initiatives"} <= tables
    assert list(tmp_path.glob("*.db")) == [db_path]


def test_initiative_cannot_cross_subject_boundary(tmp_path, monkeypatch):
    db_path = tmp_path / "solspire_projects.db"
    monkeypatch.setattr(eo, "_DB_PATH", str(db_path))
    store = eo.EnterpriseOrchestrationStore()
    portfolio = store.portfolio(
        subject="subject-a", name="A", mandate="A", correlation_id="corr-a"
    )

    with pytest.raises(ValueError, match="subject"):
        store.initiative(
            subject="subject-b",
            portfolio_id=portfolio.id,
            name="Cross-boundary initiative",
            objective="must be rejected",
        )


def test_missing_parent_never_traverses_or_invents_an_edge(tmp_path, monkeypatch):
    db_path = tmp_path / "solspire_projects.db"
    monkeypatch.setattr(eo, "_DB_PATH", str(db_path))
    store = eo.EnterpriseOrchestrationStore()
    portfolio = store.portfolio(
        subject="subject-a", name="A", mandate="A", correlation_id="corr-a"
    )
    initiative = store.initiative(
        subject="subject-a", portfolio_id=portfolio.id, name="I", objective="I"
    )

    with sqlite3.connect(db_path) as conn:
        conn.execute("PRAGMA foreign_keys=OFF")
        conn.execute("DELETE FROM ew_portfolios WHERE id=?", (portfolio.id,))
        conn.commit()

    forward = store.forward_walk(subject="subject-a", kind="PORTFOLIO", record_id=portfolio.id)
    reverse = store.reverse_walk(subject="subject-a", kind="INITIATIVE", record_id=initiative.id)
    assert forward["records"] == []
    assert reverse["complete"] is False


def test_foreign_keys_prevent_silent_parent_deletion(tmp_path, monkeypatch):
    db_path = tmp_path / "solspire_projects.db"
    monkeypatch.setattr(eo, "_DB_PATH", str(db_path))
    store = eo.EnterpriseOrchestrationStore()
    portfolio = store.portfolio(
        subject="subject-a", name="A", mandate="A", correlation_id="corr-a"
    )
    store.initiative(
        subject="subject-a", portfolio_id=portfolio.id, name="I", objective="I"
    )

    with pytest.raises(sqlite3.IntegrityError):
        with sqlite3.connect(db_path) as conn:
            conn.execute("PRAGMA foreign_keys=ON")
            conn.execute("DELETE FROM ew_portfolios WHERE id=?", (portfolio.id,))
            conn.commit()
