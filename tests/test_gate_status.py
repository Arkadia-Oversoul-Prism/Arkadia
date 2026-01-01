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
    # Gate Intelligence fields
    assert 'system_phase' in j and isinstance(j['system_phase'], str)
    assert 'governance_mode' in j and isinstance(j['governance_mode'], str)
    assert 'autonomy_enabled' in j and isinstance(j['autonomy_enabled'], bool)
    assert 'last_cycle_summary' in j and isinstance(j['last_cycle_summary'], str)
    # last_cycle_summary should be single-line and reasonably short
    assert '\n' not in j['last_cycle_summary']
    assert len(j['last_cycle_summary']) < 256
    assert 'uptime_cycles' in j and isinstance(j['uptime_cycles'], int)
    assert 'governance_version' in j and isinstance(j['governance_version'], str)


def test_gate_files_and_fetch_handling():
    # Ensure gate files exist and gate.js contains fetch/catch logic for missing/invalid data
    from pathlib import Path
    base = Path('gate')
    assert (base / 'index.html').exists()
    assert (base / 'gate.js').exists()
    gjs = (base / 'gate.js').read_text()
    assert "fetch('/sanctum/status.json'" in gjs
    assert 'Gate Closed' in gjs
    # Gate JS must reference intelligence fields in its render path
    for f in ['system_phase', 'governance_mode', 'autonomy_enabled', 'uptime_cycles', 'last_cycle_summary', 'governance_version']:
        assert f in gjs, f"gate.js must reference {f}"
    # index.html must contain matching ids for the UI fields
    idx = (base / 'index.html').read_text()
    for idname in ['system_phase', 'governance_mode', 'autonomy_enabled', 'uptime_cycles', 'last_cycle_summary', 'governance_version']:
        assert f'id="{idname}"' in idx, f"index.html must contain id {idname}"
    # banner element and CSS/JS references
    assert 'id="gate-banner"' in idx
    css = (base / 'gate.css').read_text()
    assert '.banner' in css
    assert '.banner.stable' in css
    assert '.banner.evolving' in css
    assert '.banner.paused' in css
    assert '.banner.autonomous' in css
    assert '.banner.scheduled' in css
    # gate.js references the banner element
    assert 'gate-banner' in gjs
    assert "Arkadia is Paused" in gjs or "Arkadia is Autonomous" in gjs
