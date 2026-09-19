from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_first_class_thread_api_exists():
    src = (ROOT / "api/commune_threads.py").read_text()
    assert '/api/commune/threads' in src
    assert 'create_thread' in src
    assert 'project_id' in src
    assert 'Authentication required' in src


def test_knowledge_os_thread_substrate_remains_canonical():
    src = (ROOT / "knowledge/schema.sql").read_text()
    assert 'CREATE TABLE IF NOT EXISTS threads' in src
    assert 'project_id' in src
    assert 'user_id' in src
