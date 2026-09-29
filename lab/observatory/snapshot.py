from __future__ import annotations

import ast
import re
from pathlib import Path
from typing import Any

from .git import python_imports
from .repository import discover_files, SECRET_PARTS, SECRET_NAMES


def _read(path: Path) -> str | None:
    try: return path.read_text(encoding="utf-8")
    except (OSError, UnicodeError): return None


def module_map(repo_root: str = ".") -> list[dict[str, Any]]:
    root = Path(repo_root).resolve(); out=[]
    for row in discover_files(repo_root):
        if row["extension"] not in {".py", ".ts", ".tsx", ".js", ".jsx"}: continue
        path=root/row["path"]; text=_read(path)
        if text is None: continue
        imports=python_imports(path) if path.suffix==".py" else sorted(set(re.findall(r"(?:import|from)\s+['\"]([^'\"]+)", text)))
        kind="react_component" if path.suffix in {".tsx",".jsx"} and ("React" in text or "return (" in text or "export default function" in text) else "module"
        if path.name.endswith("_router.py") or "APIRouter" in text: kind="router"
        elif any(x in path.parts for x in ("workers","worker")): kind="worker"
        elif any(x in path.parts for x in ("schemas","schema")): kind="schema"
        out.append({"path":row["path"],"kind":kind,"imports":imports})
    return sorted(out,key=lambda x:x["path"])


def route_map(repo_root: str = ".") -> list[dict[str, Any]]:
    root=Path(repo_root).resolve(); out=[]
    for row in discover_files(repo_root):
        if row["extension"]!=".py" or not row["path"].startswith("api/"): continue
        path=root/row["path"]; text=_read(path)
        if text is None: continue
        try: tree=ast.parse(text)
        except SyntaxError: continue
        for node in ast.walk(tree):
            if isinstance(node,(ast.FunctionDef,ast.AsyncFunctionDef)):
                for deco in node.decorator_list:
                    call=deco if isinstance(deco,ast.Call) else None
                    if not call or not isinstance(call.func,ast.Attribute): continue
                    if call.func.attr not in {"get","post","put","patch","delete","options","head"}: continue
                    if not call.args or not isinstance(call.args[0],ast.Constant): continue
                    path_value=call.args[0].value
                    if not isinstance(path_value,str): continue
                    out.append({"method":call.func.attr.upper(),"path":path_value,"module":row["path"],"handler":node.name,"auth_boundary":"deterministic: api.auth import/dependency" if ("require_auth" in text or "Depends(require_auth)" in text) else "unknown"})
    return sorted(out,key=lambda x:(x["path"],x["method"],x["module"]))


def deployment_map(repo_root: str = ".") -> dict[str, Any]:
    root=Path(repo_root).resolve(); names=[]
    for pattern in ("vercel.json","render.yaml","render.yml","Dockerfile","docker-compose.yml",".github/workflows/*.yml",".github/workflows/*.yaml"):
        names.extend(str(p.relative_to(root)).replace("\\","/") for p in root.glob(pattern) if p.is_file())
    env_refs=[]
    for row in discover_files(repo_root):
        if row["extension"] not in {".py",".ts",".tsx",".js",".jsx",".yml",".yaml",".json",".toml"}: continue
        p=root/row["path"]; text=_read(p) or ""
        if "os.environ" in text or "import.meta.env" in text: env_refs.append(row["path"])
    return {"files":sorted(set(names)),"environment_references":sorted(set(env_refs)),"platforms":{"vercel":any("vercel" in x.lower() for x in names),"render":any("render" in x.lower() for x in names),"github_actions":any(x.startswith(".github/workflows/") for x in names),"docker":any("dockerfile" in x.lower() or "docker-compose" in x.lower() for x in names)}}


def execution_paths(repo_root: str = ".") -> list[dict[str, Any]]:
    rows=discover_files(repo_root); paths=[]
    candidates=["kernel","weaver","solspire","engine","parsers","workers","jobs"]
    for name in candidates:
        hits=[r["path"] for r in rows if r["path"].startswith(name+"/") or r["path"]==name]
        if hits: paths.append({"id":f"execution:{name}","entrypoint":name,"orchestrator":name,"evidence":hits[:40],"status":"observed"})
    return paths


def security_observations(repo_root: str = ".") -> list[dict[str, Any]]:
    root=Path(repo_root).resolve(); out=[]
    patterns=("GEMINI_API_KEY","GOOGLE_API_KEY","SOVEREIGN_KEY","JWT_SECRET","PRIVATE_KEY","Authorization: Bearer","AIza")
    for row in discover_files(repo_root):
        p=root/row["path"]
        if row["extension"] not in {".py",".ts",".tsx",".js",".jsx",".json",".yml",".yaml",".env"}: continue
        text=_read(p) or ""
        hits=[pat for pat in patterns if pat in text]
        if hits: out.append({"path":row["path"],"signals":hits,"classification":"credential reference or potential secret; value redacted"})
    return out
