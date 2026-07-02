"""SolSpire Console — IntentRouter (Milestone 1).

Classifies raw user requests into one of the seven canonical IntentTypes.
Rule-based first (fast, deterministic), LLM fallback when confidence is low.

Contract:
    router = IntentRouter()
    intent_type = router.classify("Create a new project called Codex")
    # returns IntentType.Project
"""
from __future__ import annotations

import re
import logging
from enum import Enum
from typing import Any

logger = logging.getLogger("solspire.intent_router")


class IntentType(str, Enum):
    Question   = "Question"
    Coding     = "Coding"
    Research   = "Research"
    Automation = "Automation"
    Workflow   = "Workflow"
    Project    = "Project"
    Memory     = "Memory"


_RULES: list[tuple[IntentType, list[str]]] = [
    (IntentType.Project,    [r"\bproject\b", r"\bcreate\s+\w+\s+project\b", r"\barchive\s+project\b", r"\bload\s+project\b", r"\bnew\s+project\b"]),
    (IntentType.Coding,     [r"\bcode\b", r"\bwrite\s+(a\s+)?(function|class|script|module)\b", r"\bdebug\b", r"\brefactor\b", r"\bclone\s+(the\s+)?repo\b", r"\bgithub\b"]),
    (IntentType.Research,   [r"\bresearch\b", r"\bhistory\s+of\b", r"\bexplain\b", r"\bwhat\s+is\b", r"\bsummarise?\b", r"\banalyze?\b", r"\bstudy\b"]),
    (IntentType.Automation, [r"\bautomate?\b", r"\bschedule\b", r"\brun\s+every\b", r"\btrigger\b", r"\bpipeline\b", r"\bci\b", r"\bcd\b"]),
    (IntentType.Workflow,   [r"\bworkflow\b", r"\bmulti.?step\b", r"\bsequence\b", r"\bchain\b", r"\bstep\s+\d\b"]),
    (IntentType.Memory,     [r"\bremember\b", r"\bforget\b", r"\bstore\b", r"\bsave\s+to\b", r"\brecall\b", r"\bmemory\b"]),
    (IntentType.Question,   [r"\?$", r"^(what|who|when|where|how|why|is|are|does|do|can|will)\b"]),
]


class IntentRouter:
    def __init__(self) -> None:
        self._compiled: list[tuple[IntentType, list[re.Pattern[str]]]] = [
            (itype, [re.compile(p, re.IGNORECASE) for p in patterns])
            for itype, patterns in _RULES
        ]

    def classify(self, request: str) -> IntentType:
        if not isinstance(request, str) or not request.strip():
            return IntentType.Question

        scores: dict[IntentType, int] = {t: 0 for t in IntentType}
        for itype, patterns in self._compiled:
            for pat in patterns:
                if pat.search(request):
                    scores[itype] += 1

        best = max(scores, key=lambda t: scores[t])
        if scores[best] == 0:
            return self._llm_classify(request)

        logger.debug("IntentRouter: '%s' → %s (score=%d)", request[:60], best, scores[best])
        return best

    def _llm_classify(self, request: str) -> IntentType:
        try:
            from solspire.provider_manager import get_manager
            prompt = (
                "Classify this user request into exactly one of these intent types: "
                "Question, Coding, Research, Automation, Workflow, Project, Memory.\n"
                f"Request: {request}\n"
                "Respond with ONLY the intent type word, nothing else."
            )
            result = get_manager().invoke_model(prompt, {})
            word = result.strip().split()[0].capitalize() if result.strip() else ""
            return IntentType(word)
        except Exception as exc:
            logger.warning("IntentRouter LLM fallback failed: %s", exc)
            return IntentType.Question

    def describe(self, intent_type: IntentType) -> dict[str, Any]:
        return {"intent": intent_type.value, "description": _DESCRIPTIONS.get(intent_type, "")}


_DESCRIPTIONS = {
    IntentType.Question:   "A request for information or explanation",
    IntentType.Coding:     "Writing, debugging, or refactoring code",
    IntentType.Research:   "Deep investigation into a topic",
    IntentType.Automation: "Setting up automated pipelines or schedules",
    IntentType.Workflow:   "Multi-step coordinated task sequences",
    IntentType.Project:    "Creating, loading, or managing projects",
    IntentType.Memory:     "Storing, recalling, or modifying memory",
}

_GLOBAL_ROUTER = IntentRouter()


def get_router() -> IntentRouter:
    return _GLOBAL_ROUTER


__all__ = ["IntentType", "IntentRouter", "get_router"]
