from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class NodeVerdict:
    node: str  # constitutional | structural | integrative
    pass_: bool
    reasons: tuple[str, ...] = ()


@dataclass(frozen=True)
class CouncilResult:
    proposal_id: str
    verdicts: tuple[NodeVerdict, ...]
    consensus: str  # PASS | FAIL | DISAGREE
    disagreement: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return {
            "proposal_id": self.proposal_id,
            "consensus": self.consensus,
            "disagreement": list(self.disagreement),
            "verdicts": [
                {"node": v.node, "pass": v.pass_, "reasons": list(v.reasons)}
                for v in self.verdicts
            ],
        }


def _constitutional(p: dict[str, Any]) -> NodeVerdict:
    reasons: list[str] = []
    ok = True
    if p.get("authority_ceiling", 99) > 2:
        ok = False
        reasons.append("authority_ceiling exceeds Level 2 without explicit grant")
    if p.get("mutation") is True and not p.get("human_authorization"):
        ok = False
        reasons.append("mutation true without human_authorization")
    if p.get("bypasses_auth") is True:
        ok = False
        reasons.append("bypasses_auth is forbidden")
    if not p.get("goal"):
        ok = False
        reasons.append("missing goal")
    return NodeVerdict("constitutional", ok, tuple(reasons))


def _structural(p: dict[str, Any]) -> NodeVerdict:
    reasons: list[str] = []
    ok = True
    required = ("id", "goal", "kind")
    for k in required:
        if k not in p or p[k] in (None, ""):
            ok = False
            reasons.append(f"missing required field: {k}")
    kind = p.get("kind")
    if kind is not None and kind not in ("observe", "analyse", "suggest", "execute"):
        ok = False
        reasons.append(f"invalid kind: {kind}")
    return NodeVerdict("structural", ok, tuple(reasons))


def _integrative(p: dict[str, Any]) -> NodeVerdict:
    reasons: list[str] = []
    ok = True
    kind = p.get("kind")
    if kind == "execute" and p.get("authority_ceiling", 0) < 3:
        # Advisory: execute claims need higher ceiling in Track 2+; at Level 2 this fails integrative
        ok = False
        reasons.append("kind=execute inconsistent with authority_ceiling < 3")
    if p.get("mutation") is True and kind in ("observe", "analyse"):
        ok = False
        reasons.append("mutation true inconsistent with non-executing kind")
    goal = (p.get("goal") or "").lower()
    if "bypass" in goal or "weaken require_auth" in goal:
        ok = False
        reasons.append("goal language conflicts with integrative safety")
    return NodeVerdict("integrative", ok, tuple(reasons))


def evaluate_proposal(proposal: dict[str, Any]) -> CouncilResult:
    """Run all three nodes; record consensus or explicit disagreement."""
    pid = str(proposal.get("id") or "unknown")
    verdicts = (_constitutional(proposal), _structural(proposal), _integrative(proposal))
    passes = [v.pass_ for v in verdicts]
    if all(passes):
        consensus = "PASS"
        disagreement: tuple[str, ...] = ()
    elif not any(passes):
        consensus = "FAIL"
        disagreement = ()
    else:
        consensus = "DISAGREE"
        disagreement = tuple(
            f"{v.node}:{'PASS' if v.pass_ else 'FAIL'}" + (f" ({'; '.join(v.reasons)})" if v.reasons else "")
            for v in verdicts
        )
    return CouncilResult(proposal_id=pid, verdicts=verdicts, consensus=consensus, disagreement=disagreement)
