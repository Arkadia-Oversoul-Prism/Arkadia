"""SolSpire Console — Planner (Milestone 1).

Translates a user request + intent type into an ordered Plan of steps.
Uses Gemini when available; falls back to deterministic templates.

Contract:
    planner = Planner()
    plan = planner.create_plan("Create project Codex and clone the repo", IntentType.Project)
    is_valid = planner.validate_plan(plan)
"""
from __future__ import annotations

import json
import logging
import re
import time
import uuid
from typing import Any

from solspire.execution_runtime import Plan
from solspire.intent_router import IntentType

logger = logging.getLogger("solspire.planner")

MAX_STEPS = 5

_TEMPLATES: dict[IntentType, list[dict[str, Any]]] = {
    IntentType.Project: [
        {"tool": "project_create", "description": "Create the project in the project manager",
         "payload": {"name": "{project_name}"}},
        {"tool": "llm", "description": "Generate an initial plan and summary for the project",
         "payload": {"prompt": "Create a brief project plan for: {request}"}},
    ],
    IntentType.Coding: [
        {"tool": "llm", "description": "Write the requested code",
         "payload": {"prompt": "Write code for: {request}"}},
        {"tool": "fs_write", "description": "Save the code to a file",
         "payload": {"path": "output/generated_code.py", "content": "{result}"}},
    ],
    IntentType.Research: [
        {"tool": "llm", "description": "Research the topic comprehensively",
         "payload": {"prompt": "Research and explain in detail: {request}"}},
    ],
    IntentType.Question: [
        {"tool": "llm", "description": "Answer the question",
         "payload": {"prompt": "{request}"}},
    ],
    IntentType.Automation: [
        {"tool": "llm", "description": "Design the automation pipeline",
         "payload": {"prompt": "Design an automation pipeline for: {request}"}},
    ],
    IntentType.Workflow: [
        {"tool": "llm", "description": "Orchestrate the multi-step workflow",
         "payload": {"prompt": "Create a detailed workflow plan for: {request}"}},
    ],
    IntentType.Memory: [
        {"tool": "llm", "description": "Process the memory operation",
         "payload": {"prompt": "Process this memory request: {request}"}},
    ],
}


def _extract_project_name(request: str) -> str:
    m = re.search(r"(?:called?|named?|project)\s+['\"]?([A-Za-z0-9 _\-]+)['\"]?", request, re.I)
    return m.group(1).strip() if m else "Unnamed Project"


class Planner:
    def create_plan(self, request: str, intent: IntentType) -> Plan:
        steps = self._llm_plan(request, intent) or self._template_plan(request, intent)
        steps = steps[:MAX_STEPS]

        plan = Plan(
            id=str(uuid.uuid4()),
            request=request,
            intent=intent.value,
            steps=steps,
            created_at=time.time(),
        )
        logger.info("Planner: plan %s (%s, %d steps)", plan.id, intent.value, len(steps))
        return plan

    def validate_plan(self, plan: Plan) -> bool:
        if not isinstance(plan.steps, list) or not plan.steps:
            return False
        if len(plan.steps) > MAX_STEPS:
            return False
        for step in plan.steps:
            if not isinstance(step, dict):
                return False
            if "tool" not in step:
                return False
        return True

    def _template_plan(self, request: str, intent: IntentType) -> list[dict[str, Any]]:
        templates = _TEMPLATES.get(intent, _TEMPLATES[IntentType.Question])
        project_name = _extract_project_name(request)
        steps = []
        for tmpl in templates:
            step = dict(tmpl)
            payload = {}
            for k, v in (tmpl.get("payload") or {}).items():
                if isinstance(v, str):
                    v = v.replace("{request}", request).replace("{project_name}", project_name)
                payload[k] = v
            step["payload"] = payload
            steps.append(step)
        return steps

    def _llm_plan(self, request: str, intent: IntentType) -> list[dict[str, Any]] | None:
        try:
            from solspire.provider_manager import get_manager
            tools_hint = (
                "Available tools: llm (LLM reasoning), fs_read, fs_write, fs_list, "
                "github_repos, github_tree, github_read, project_create"
            )
            prompt = (
                f"You are a planner. Create a JSON plan for this {intent.value} request.\n"
                f"{tools_hint}\n"
                f"Request: {request}\n\n"
                f"Respond ONLY with valid JSON: "
                f'{{ "steps": [ {{ "tool": "tool_name", "description": "what this step does", "payload": {{}} }} ] }}\n'
                f"Max {MAX_STEPS} steps. Use the simplest possible plan."
            )
            raw = get_manager().invoke_model(prompt, {})
            m = re.search(r'\{.*\}', raw, re.DOTALL)
            if not m:
                return None
            data = json.loads(m.group(0))
            steps = data.get("steps", [])
            if not isinstance(steps, list):
                return None
            valid = [s for s in steps if isinstance(s, dict) and "tool" in s]
            return valid if valid else None
        except Exception as exc:
            logger.warning("Planner LLM failed: %s", exc)
            return None


_GLOBAL_PLANNER = Planner()


def get_planner() -> Planner:
    return _GLOBAL_PLANNER


__all__ = ["Planner", "get_planner"]
