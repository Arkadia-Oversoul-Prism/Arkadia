import os
import json
from weaver.recursive import RecursiveEngine


def test_report_export(tmp_path, monkeypatch):
    monkeypatch.setenv('REPO_ROOT', str(tmp_path))
    engine = RecursiveEngine(initial_task='test', enabled=True)
    engine.set_depth(1)
    engine.current_cycle = 1
    path = tmp_path / 'sanctum' / 'status.json'
    engine.report(export_path=str(path))
    assert path.exists()
    j = json.loads(path.read_text())
    assert 'cycle' in j and isinstance(j['cycle'], int)
    assert 'depth' in j and isinstance(j['depth'], int)
    assert 'ready' in j and isinstance(j['ready'], bool)
    assert 'commits' in j and isinstance(j['commits'], list)


def test_gate_files_and_fetch_handling():
    # Ensure gate files exist and gate.js contains fetch/catch logic for missing/invalid data
    from pathlib import Path
    base = Path('gate')
    assert (base / 'index.html').exists()
    assert (base / 'gate.js').exists()
    gjs = (base / 'gate.js').read_text()
    assert "fetch('/sanctum/status.json'" in gjs
    assert 'Gate Closed' in gjs
