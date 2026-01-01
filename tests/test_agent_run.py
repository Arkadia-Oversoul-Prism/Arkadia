import os
from pathlib import Path
from weaver import agent


def test_agent_run_writes_and_commits(tmp_path, monkeypatch):
    # Configure repo root to tmp_path
    monkeypatch.setenv('REPO_ROOT', str(tmp_path))

    # Create a fake file to be in read_repo
    repo_file = tmp_path / 'existing.txt'
    repo_file.write_text('existing')

    # Monkeypatch build_prompt to avoid reading actual repo files
    monkeypatch.setattr('weaver.prompts.build_prompt', lambda task, files: 'fake prompt')

    # Prepare LLM response that updates a file within tmp_path
    new_file = tmp_path / 'new.txt'
    llm_response = f"--- FILE: {new_file} ---\nHello New Content\n"
    # Monkeypatch the agent's imported call_llm
    monkeypatch.setattr('weaver.agent.call_llm', lambda provider, prompt: llm_response)

    # Capture commit message without actually calling git
    called = {}

    def fake_commit(msg, paths=None, meta=None, **kwargs):
        called['msg'] = msg
        called['paths'] = paths
        called['meta'] = meta
        return True

    # Monkeypatch the commit function the agent imported
    monkeypatch.setattr('weaver.agent.commit_and_push', fake_commit)

    updated_files, commit_msg = agent.run('test task', engine_cycle=5)
    assert isinstance(updated_files, list)
    assert len(updated_files) == 1
    # The commit msg should match expected pattern
    assert commit_msg is not None
    assert 'weaver: auto update' in commit_msg
    # The new file should exist and contain content
    assert new_file.exists()
    assert new_file.read_text().strip() == 'Hello New Content'
    # The fake commit was called with the expected paths
    assert called['paths'] == updated_files
    # meta should include engine_cycle
    assert 'meta' in called
    assert called['meta']['engine_cycle'] == 5
