from __future__ import annotations

from typing import Any


def classify_commit(message: str, files: list[str]) -> tuple[str, float]:
    m=message.lower(); joined=" ".join(files).lower()
    rules=[("security",("security","auth","credential","jwt")),("deployment",("deploy","render","vercel","workflow","docker")),("dependency",("depend","pnpm","npm","requirements")),("documentation",("docs","readme","adr","document")),("ui",("ui","tsx","css","frontend","navigation")),("architecture",("architecture","consolidat","layer","router","kernel")),("refactor",("refactor","reorganiz","cleanup")),("fix",("fix","bug","repair")),("feature",("feat","add","implement","introduc"))]
    for kind,terms in rules:
        if any(t in m or t in joined for t in terms): return kind,0.85
    return "unknown",0.4


def trajectory_model(commits: list[dict[str, Any]]) -> dict[str, Any]:
    counts: dict[str,int]={}; churn: dict[str,int]={}; transitions=[]
    for c in commits:
        kind,confidence=classify_commit(c["message"],c["files_changed"]); c["classification"]=kind; c["classification_confidence"]=confidence; counts[kind]=counts.get(kind,0)+1
        for path in c["files_changed"]: churn[path]=churn.get(path,0)+1
    for prev,nxt in zip(commits[1:],commits):
        if prev.get("classification")!=nxt.get("classification"):
            transitions.append({"from":prev.get("classification"),"to":nxt.get("classification"),"at":nxt.get("sha"),"evidence":[prev.get("sha"),nxt.get("sha")]})
    return {"counts":counts,"high_churn":sorted(({"path":p,"changes":n} for p,n in churn.items() if n>=3),key=lambda x:(-x["changes"],x["path"]))[:50],"transitions":transitions[:50]}
