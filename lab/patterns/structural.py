from __future__ import annotations

from collections import defaultdict
from typing import Any
from ..model import Pattern, observed_now


def detect_patterns(files: list[dict[str,Any]], modules: list[dict[str,Any]], routes: list[dict[str,Any]], execution_paths: list[dict[str,Any]], trajectory: dict[str,Any], deployments: dict[str,Any]) -> list[dict[str,Any]]:
    now=observed_now(); out=[]
    def add(pid,typ,severity,evidence,affected,confidence=0.9):
        out.append(Pattern(id=pid,pattern_id=pid,type=typ,source="deterministic",confidence=confidence,observed_at=now,metadata={},severity=severity,evidence=sorted(set(evidence)),affected_entities=sorted(set(affected)),first_detected=now,last_detected=now).model_dump())
    by_base=defaultdict(list)
    for r in routes: by_base[r["path"]].append(r)
    dup_routes={k:v for k,v in by_base.items() if len(v)>1}
    if dup_routes: add("pattern:duplicate-frontend-api-surface","duplicate capability","medium",[f"{k}: {len(v)} route declarations" for k,v in dup_routes.items()],[r["module"] for v in dup_routes.values() for r in v],0.95)
    if len(execution_paths)>1: add("pattern:parallel-execution-paths","parallel execution paths","high",[p["id"] for p in execution_paths], [p["id"] for p in execution_paths],1.0)
    if len(deployments.get("files",[]))>1: add("pattern:deployment-configuration-multiplicity","duplicate configuration","medium",deployments["files"],deployments["files"],1.0)
    high=trajectory.get("high_churn",[])
    if high: add("pattern:high-churn-components","high-churn component","medium",[f'{x["path"]}: {x["changes"]} commits' for x in high], [x["path"] for x in high],1.0)
    module_paths={m["path"] for m in modules}; imported=set()
    for m in modules:
        imported.update(x for x in m.get("imports",[]) if x)
    disconnected=[m["path"] for m in modules if m["path"].startswith(("web/","api/","kernel/","weaver/","solspire/")) and m["path"].rsplit("/",1)[-1].split(".")[0] not in imported and m["path"] not in {"api/main.py"}]
    if disconnected: add("pattern:potentially-disconnected-modules","dead/disconnected surface","low",disconnected[:50],disconnected[:50],0.55)
    return sorted(out,key=lambda x:x["pattern_id"])
