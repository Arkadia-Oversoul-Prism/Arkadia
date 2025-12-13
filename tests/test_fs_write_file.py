import os
from pathlib import Path
from weaver.fs import write_file


def test_write_file_creates_backup(tmp_path, monkeypatch):
    monkeypatch.setenv('REPO_ROOT', str(tmp_path))
    p = tmp_path / "sample.txt"
    p.write_text("original")
    # write new content and expect backup created
    changed = write_file(str(p), "updated")
    assert changed is True
    bak = p.with_suffix(p.suffix + ".bak") if p.suffix else Path(str(p) + ".bak")
    assert bak.exists()
    assert bak.read_text() == "original"

    # writing same content returns False and does not alter backup
    changed2 = write_file(str(p), "updated")
    assert changed2 is False
    assert bak.exists()



def test_write_file_outside_repo_refused(tmp_path):
    # Attempt to write outside REPO_ROOT should be refused
    import os
    os.environ['REPO_ROOT'] = str(tmp_path)
    # target outside repo
    target = tmp_path.parent / "evil.txt"
    try:
        from weaver.fs import write_file
        try:
            write_file(str(target), "data")
            assert False, "Should have refused to write outside repo root"
        except ValueError:
            pass
    finally:
        os.environ.pop('REPO_ROOT', None)

