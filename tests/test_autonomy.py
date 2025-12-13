import os
from weaver.autonomy import load_autonomy_config, validate_autonomy_config, run_scheduled_once


def test_autonomy_config_exists_and_valid():
    cfg = load_autonomy_config()
    assert isinstance(cfg, dict)
    assert validate_autonomy_config(cfg)


def test_autonomy_run_respects_limits(monkeypatch, tmp_path):
    # Prepare a temporary repo root and override AUTONOMY_PATH
    monkeypatch.setenv('REPO_ROOT', str(tmp_path))
    # Make sure roles.json includes Flamekeeper
    roles_dir = tmp_path / 'governance'
    roles_dir.mkdir(parents=True, exist_ok=True)
    (roles_dir / 'roles.json').write_text('{"Flamekeeper": {}}')

    # Create a copy of autonomy.json with a low commit limit
    from pathlib import Path
    aconf = load_autonomy_config()
    aconf['max_commits_per_run'] = 1
    # Run scheduled once with use_stub True and patched environment
    monkeypatch.setenv('ARKADIA_AUTONOMOUS', 'true')
    res = run_scheduled_once(config=aconf, use_stub=True)
    assert res['ran'] is True
    assert res['commit_count'] <= 1
