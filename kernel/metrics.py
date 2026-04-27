"""SolSpire Phase 8 — Lightweight observability ledger.

In-process counters for tool usage, success rate, and latency. This is
intentionally NOT a full metrics backend — for production you'd ship
this into Prometheus / OpenTelemetry. Here it gives the dashboard and
debug endpoints something concrete to render.

Thread-safe. Bounded memory (caps recent latency samples per tool).
"""
from __future__ import annotations

import threading
import time
from collections import deque
from typing import Any

_LOCK = threading.Lock()
_LATENCY_WINDOW = 200  # keep last N latencies per tool for p50/p95

_tool_metrics: dict[str, dict[str, Any]] = {}
_plan_metrics: dict[str, int] = {
    "plans_total":     0,
    "plans_success":   0,
    "plans_failed":    0,
    "plans_llm":       0,
    "plans_fallback":  0,
}
_goal_metrics: dict[str, int] = {
    "goal_runs_total":    0,
    "goal_runs_success":  0,
    "goal_runs_failed":   0,
    "goal_runs_skipped":  0,
}


def _ensure_tool(name: str) -> dict[str, Any]:
    m = _tool_metrics.get(name)
    if m is None:
        m = {
            "tool":      name,
            "calls":     0,
            "successes": 0,
            "failures":  0,
            "latencies": deque(maxlen=_LATENCY_WINDOW),
            "last_at":   None,
        }
        _tool_metrics[name] = m
    return m


def record_tool_call(name: str, *, success: bool, duration_ms: float) -> None:
    if not isinstance(name, str) or not name:
        return
    with _LOCK:
        m = _ensure_tool(name)
        m["calls"] += 1
        m["successes" if success else "failures"] += 1
        m["latencies"].append(float(duration_ms))
        m["last_at"] = time.time()


def record_plan(*, success: bool, source: str) -> None:
    """source ∈ {'llm', 'fallback', 'user', 'none'}"""
    with _LOCK:
        _plan_metrics["plans_total"] += 1
        _plan_metrics["plans_success" if success else "plans_failed"] += 1
        if source == "llm":
            _plan_metrics["plans_llm"] += 1
        elif source == "fallback":
            _plan_metrics["plans_fallback"] += 1


def record_goal_run(*, success: bool, skipped: bool = False) -> None:
    with _LOCK:
        _goal_metrics["goal_runs_total"] += 1
        if skipped:
            _goal_metrics["goal_runs_skipped"] += 1
        elif success:
            _goal_metrics["goal_runs_success"] += 1
        else:
            _goal_metrics["goal_runs_failed"] += 1


def _percentile(samples: list[float], pct: float) -> float | None:
    if not samples:
        return None
    s = sorted(samples)
    k = max(0, min(len(s) - 1, int(round((pct / 100.0) * (len(s) - 1)))))
    return round(s[k], 2)


def snapshot() -> dict[str, Any]:
    """Return a JSON-safe snapshot of all metrics."""
    with _LOCK:
        tools_out: list[dict[str, Any]] = []
        for name, m in sorted(_tool_metrics.items()):
            samples = list(m["latencies"])
            calls = m["calls"]
            tools_out.append({
                "tool":         name,
                "calls":        calls,
                "successes":    m["successes"],
                "failures":     m["failures"],
                "success_rate": round(m["successes"] / calls, 4) if calls else None,
                "p50_ms":       _percentile(samples, 50),
                "p95_ms":       _percentile(samples, 95),
                "last_at":      m["last_at"],
            })
        return {
            "tools": tools_out,
            "plans": dict(_plan_metrics),
            "goals": dict(_goal_metrics),
            "ts":    time.time(),
        }


def reset() -> None:
    """Test-only."""
    with _LOCK:
        _tool_metrics.clear()
        for k in _plan_metrics:
            _plan_metrics[k] = 0
        for k in _goal_metrics:
            _goal_metrics[k] = 0


__all__ = [
    "record_tool_call", "record_plan", "record_goal_run",
    "snapshot", "reset",
]
