from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

STATUSES = frozenset({"SUCCESS", "PARTIAL", "REGRESSION", "FAILURE"})


@dataclass(frozen=True)
class CalibrationResult:
    status: str
    mismatches: tuple[str, ...]


def _flatten(value: Any, prefix: str = "") -> dict[str, Any]:
    if isinstance(value, Mapping):
        out: dict[str, Any] = {}
        for key, item in value.items():
            path = f"{prefix}.{key}" if prefix else str(key)
            out.update(_flatten(item, path))
        return out
    return {prefix: value}


def classify(expected_state: Mapping[str, Any], actual_state: Mapping[str, Any]) -> CalibrationResult:
    """Classify actual state against expected state without side effects."""
    expected = _flatten(expected_state)
    actual = _flatten(actual_state)
    mismatches = tuple(
        key for key in sorted(set(expected) | set(actual))
        if expected.get(key) != actual.get(key)
    )
    if not mismatches:
        return CalibrationResult("SUCCESS", ())

    # A regression is an unexpected loss or newly observed failure signal.
    regression_keys = {
        key for key in mismatches
        if (key not in actual) or (isinstance(actual.get(key), (int, float)) and isinstance(expected.get(key), (int, float)) and actual[key] < expected[key])
        or "regression" in key.lower() or "failure" in key.lower() or "error" in key.lower()
    }
    status = "REGRESSION" if regression_keys else "PARTIAL"
    return CalibrationResult(status, mismatches)
