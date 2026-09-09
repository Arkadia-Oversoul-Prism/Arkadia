from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Any

from .model import ANALYSIS_VERSION, COLLECTOR_VERSION, SCHEMA_VERSION, observed_now
from .observatory.repository import repository_observation
from .observatory.git import repository_state, commit_history
from .observatory.snapshot import module_map, route_map, deployment_map, execution_paths, security_observations
from .trajectory.model import trajectory_model
from .canon.loader import load_canon
from .graph.entities import entity
from .graph.relationships import relates
from .patterns.structural import detect_patterns


def _architecture(files, modules, routes, executions):
    components=[r for r in files if r["directory"] in {"api","kernel","weaver","solspire","engine","parsers"}]
    services=[r for r in modules if r["kind"] in {"router","worker"}]
    return {"components":len(components),"modules":len(modules),"services":len(services),"routes":len(routes),"execution_paths":len(executions),"status":"observed"}


def _graph(files, modules, routes, commits, canon, patterns):
    entities=[]; relationships=[]
    entities.append(entity("System","system:arkadia","repository",1.0, name="Arkadia").model_dump())
    entities.append(entity("Repository","repo:Arkadia-Oversoul-Prism/Arkadia","repository",1.0,name="Arkadia-Oversoul-Prism/Arkadia").model_dump())
    for r in files[:5000]:
        cid=f"module:{r['path']}"; et="Component" if r["directory"] in {"api","kernel","weaver","solspire"} else "Module"
        entities.append(entity(et,cid,"filesystem",1.0,path=r["path"]).model_dump())
    for r in routes:
        rid=f"route:{r['method']}:{r['path']}"; entities.append(entity("Route",rid,"ast",1.0,**r).model_dump())
    for c in commits[:250]:
        cid=f"commit:{c['sha']}"; entities.append(entity("Commit",cid,"git",1.0,**{k:v for k,v in c.items() if k not in {"sha"}}).model_dump())
        for p in c["files_changed"][:100]: relationships.append(relates(cid,"modifies",f"module:{p}",source="git",confidence=1.0,evidence=[c["sha"],p],provenance={"git_commit":c["sha"]},method="commit file list").model_dump())
    for p in patterns:
        entities.append(entity("Pattern",p["pattern_id"],"deterministic",p["confidence"],severity=p["severity"]).model_dump())
    return {"entities":entities,"relationships":relationships,"status":"observed"}


def build_overview(repo_root: str = ".") -> dict[str, Any]:
    root=str(Path(repo_root).resolve()); now=observed_now(); state=repository_state(root)
    files=[]; modules=[]; routes=[]; executions=[]; deployments={}; security=[]; git_status={}; commits=[]
    errors=[]
    try: files=__import__("lab.observatory.repository",fromlist=["discover_files"]).discover_files(root)
    except Exception as e: errors.append({"component":"files","status":"failed","reason":str(e)})
    try: modules=module_map(root); routes=route_map(root); deployments=deployment_map(root); executions=execution_paths(root); security=security_observations(root)
    except Exception as e: errors.append({"component":"snapshot","status":"failed","reason":str(e)})
    try: commits,git_status=commit_history(root)
    except Exception as e: errors.append({"component":"trajectory","status":"failed","reason":str(e)})
    try: traj=trajectory_model(commits)
    except Exception as e: traj={"counts":{},"high_churn":[],"transitions":[]}; errors.append({"component":"trajectory-analysis","status":"failed","reason":str(e)})
    try: canon=load_canon(root)
    except Exception as e: canon={"loaded":False,"sources":[],"status":"failed","reason":str(e)}; errors.append({"component":"canon","status":"failed","reason":str(e)})
    arch=_architecture(files,modules,routes,executions)
    patterns=detect_patterns(files,modules,routes,executions,traj,deployments)
    graph=_graph(files,modules,routes,commits,canon,patterns)
    return {"schema_version":SCHEMA_VERSION,"collector_version":COLLECTOR_VERSION,"analysis_version":ANALYSIS_VERSION,"observed_at":now,"repository_head":state.get("head"),"system":"Arkadia","repository":{"branch":state.get("branch") or "main","head":state.get("head"),"clean":state.get("clean"),"remote":state.get("remote"),"status":state.get("status"),"reason":state.get("reason")},"architecture":arch,"trajectory":{"commits_analysed":len(commits),"major_transitions":len(traj.get("transitions",[])),"high_churn_components":len(traj.get("high_churn",[])),"classifications":traj.get("counts",{})},"canon":{"loaded":canon.get("loaded",False),"sources":canon.get("sources",[]),"drift":[],"version":canon.get("canon_version")},"patterns":patterns,"graph":{"entities":len(graph["entities"]),"relationships":len(graph["relationships"]),"status":graph["status"]},"deployments":deployments,"security":{"observations":security,"values_redacted":True},"governance":{"maximum_authority":2,"autonomous_mutation":False,"production_mutation":False,"approval_required":True},"errors":errors,"status":"partial" if errors else "observed"}
