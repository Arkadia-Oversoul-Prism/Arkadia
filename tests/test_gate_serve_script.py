from pathlib import Path


def test_root_index_redirect_and_script_exists():
    root_index = Path('index.html')
    assert root_index.exists()
    content = root_index.read_text()
    assert 'Redirecting to the Arkadia Living Gate' in content
    assert 'meta http-equiv' in content.lower() or '/gate/' in content

    serve_script = Path('scripts/serve-gate.sh')
    assert serve_script.exists()
    s = serve_script.read_text()
    assert 'http.server' in s
    assert 'xdg-open' in s or 'open ' in s
