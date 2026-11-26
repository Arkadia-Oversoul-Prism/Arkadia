"""Ark Date parity guard: `kernel/stellar.py` must equal `api/main.py::_ark_date`.

`kernel/stellar.py` states the invariant in its own docstring:

    Mirrors api.main._ark_date exactly; duplicated here to avoid a circular
    import through api.main's heavy dependency tree.

The duplication is deliberate — `api/main.py` imports httpx/fastapi, and the stellar
engine must load standalone (`tests/test_stellar_cartography.py::
test_stellar_decoupled_from_api_main`). But a stated equivalence that nothing checks
is not a contract. Measured on `main` @ `cb284195`: the only test naming the pair
asserts the *shape* of the stellar copy, so editing one implementation's epoch,
duration, rounding, or coordinate format would leave the two copies disagreeing while
every test stayed green — and the disagreement is user-visible, because the stellar
readout is the star-date header while the same coordinate is served elsewhere.

The guard compares the two implementations field by field at several pinned instants
(the epoch day, day 2, a mid-Ark day, and a minute before a day boundary), with the
clock frozen so a minute rollover cannot make the comparison flaky. The clock is the
only thing replaced; both implementations run their real code.

Every detector here is paired with a control that runs against the real modules: a
comparison that cannot report a difference would pass on two identical constants and
prove nothing.
"""

from __future__ import annotations

from datetime import datetime, timezone

import pytest

from kernel import stellar as stellar_engine

# Instants chosen to exercise the boundary arithmetic: the epoch itself (day 1),
# the first rollover, a mid-Ark day, and one minute before a day boundary.
PINNED_INSTANTS = (
    datetime(2026, 3, 31, 0, 0, 0, tzinfo=timezone.utc),
    datetime(2026, 4, 1, 0, 0, 0, tzinfo=timezone.utc),
    datetime(2027, 8, 14, 13, 37, 0, tzinfo=timezone.utc),
    datetime(2029, 3, 30, 23, 59, 0, tzinfo=timezone.utc),
)


class _FrozenClock:
    """Stand-in for the `datetime` module attribute the two implementations call."""

    def __init__(self, instant: datetime) -> None:
        self._instant = instant

    def now(self, tz=None) -> datetime:  # noqa: ARG002 - signature mirrors datetime.now
        return self._instant


def _api_main():
    """The canonical implementation. Imported lazily: it pulls the FastAPI app."""
    import api.main as api_main

    return api_main


def ark_date_mismatches(monkeypatch, instant: datetime) -> list[str]:
    """Fields on which the stellar copy and the canonical Ark Date disagree.

    Both implementations are driven at the same frozen instant so the comparison
    cannot be split by a clock rollover between the two calls.
    """
    api_main = _api_main()
    monkeypatch.setattr(stellar_engine, "datetime", _FrozenClock(instant))
    monkeypatch.setattr(api_main, "datetime", _FrozenClock(instant))
    stellar = stellar_engine._ark_date()
    canonical = api_main._ark_date()

    mismatches = []
    for key in sorted(set(stellar) | set(canonical)):
        if key not in stellar:
            mismatches.append(f"{key}: missing from kernel.stellar")
        elif key not in canonical:
            mismatches.append(f"{key}: missing from api.main")
        elif stellar[key] != canonical[key]:
            mismatches.append(f"{key}: stellar={stellar[key]!r} api.main={canonical[key]!r}")
    return mismatches


def test_the_two_ark_date_constants_agree():
    api_main = _api_main()
    assert stellar_engine.ARK_EPOCH == api_main.ARK_EPOCH, (
        "the stellar engine and api.main disagree about the Ark epoch; every Ark Day "
        "computed by one is wrong by the difference shown by the other"
    )
    assert stellar_engine.ARK_DURATION_YEARS == api_main.ARK_DURATION_YEARS


@pytest.mark.parametrize("instant", PINNED_INSTANTS, ids=lambda i: i.isoformat())
def test_stellar_ark_date_mirrors_the_canonical_implementation(monkeypatch, instant):
    assert ark_date_mismatches(monkeypatch, instant) == []


def test_negative_control_a_shifted_epoch_is_reported(monkeypatch):
    """A perturbation of one implementation must be visible to the comparison.

    The instant must be a mid-Ark day: both implementations clamp
    ``max(1, delta.days + 1)``, so at (or before) the epoch a one-day epoch shift is
    absorbed by the clamp and the control would be vacuous for a reason unrelated to
    the comparison.
    """
    api_main = _api_main()
    monkeypatch.setattr(api_main, "ARK_EPOCH", datetime(2025, 1, 1, tzinfo=timezone.utc))

    mismatches = ark_date_mismatches(monkeypatch, PINNED_INSTANTS[2])

    assert mismatches, "a one-day epoch shift produced no mismatch: the guard is vacuous"
    assert any(field.startswith("total_ark_day") for field in mismatches)


def test_negative_control_a_changed_coordinate_format_is_reported(monkeypatch):
    """The comparison covers the rendered strings, not only the integers."""
    api_main = _api_main()
    original = api_main._ark_date

    def reformatted():
        value = original()
        value["coordinate"] = value["coordinate"].replace("Ark Year", "Ark Cycle")
        return value

    monkeypatch.setattr(api_main, "_ark_date", reformatted)

    mismatches = ark_date_mismatches(monkeypatch, PINNED_INSTANTS[1])

    assert any(field.startswith("coordinate") for field in mismatches)
