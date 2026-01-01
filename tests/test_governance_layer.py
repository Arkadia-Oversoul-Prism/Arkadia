import json
from pathlib import Path

GOV_FILES = [
    Path('governance/roles.json'),
    Path('governance/permissions.json'),
    Path('governance/boundaries.json'),
    Path('governance/manifest.json'),
    Path('governance/vows.md')
]

BAD_KEYWORDS = ['import ', 'exec(', 'subprocess', '<script', 'os.system', 'curl ', 'wget ', 'fetch(', 'while True', 'rm -rf', 'eval(']


def test_governance_files_exist_and_valid_json():
    for f in GOV_FILES:
        assert f.exists(), f"Missing governance file: {f}"
    # roles.json, permissions.json, boundaries.json, manifest.json must parse
    for j in ['roles.json', 'permissions.json', 'boundaries.json', 'manifest.json']:
        p = Path('governance') / j
        data = json.loads(p.read_text())
        assert isinstance(data, dict)

    roles = json.loads((Path('governance') / 'roles.json').read_text())
    assert all(r in roles for r in ['Flamekeeper', 'Weaver', 'Witness', 'Guest'])

    perms = json.loads((Path('governance') / 'permissions.json').read_text())
    assert all(p in perms for p in ['Read', 'Propose', 'Execute', 'Govern'])

    bounds = json.loads((Path('governance') / 'boundaries.json').read_text())
    assert all(b in bounds for b in ['Gate', 'Sanctum', 'Engine'])


def test_governance_no_execution_or_recursion():
    # Ensure governance files don't enable code execution or recursion
    for p in Path('governance').glob('*'):
        txt = p.read_text() if p.is_file() else ''
        for kw in BAD_KEYWORDS:
            assert kw not in txt, f"Found suspicious keyword '{kw}' in {p}"
        assert 'recursive' not in txt.lower(), f"Found 'recursive' mention in {p} which may enable recursion"


def test_sanctum_status_governance_version_present_and_non_sensitive():
    sfile = Path('sanctum') / 'status.json'
    assert sfile.exists()
    st = json.loads(sfile.read_text())
    assert 'governance_version' in st
    gv = st['governance_version']
    assert isinstance(gv, str) and gv
    # No environment variables or stack trace substrings
    assert 'GEMINI_API_KEY' not in str(st)
    assert 'ENV' not in str(st)
