from pathlib import Path

def read_repo(root="."):
    files = {}
    for p in Path(root).rglob("*"):
        if p.is_file() and ".git" not in str(p):
            try:
                files[str(p)] = p.read_text()
            except:
                pass
    return files

def write_file(path, content):
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content)

