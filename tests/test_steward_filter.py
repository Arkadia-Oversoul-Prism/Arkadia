"""
Tests for Steward Filter

Ensures identity blocking, action enforcement, sustainability checks.
"""

from weaver.filters.steward import steward_filter, check_sustainability, compress_to_choices


def test_blocks_identity_claims():
    """Block divine/chosen/ascended claims."""
    assert steward_filter("You are divine") is None
    assert steward_filter("You are chosen") is None
    assert steward_filter("You have transcended") is None


def test_allows_action():
    """Allow action-oriented text."""
    assert steward_filter("Take one step forward") is not None
    assert steward_filter("Choose what to maintain") is not None
    assert steward_filter("I will quit this") is not None


def test_blocks_pure_symbolism():
    """Block symbolism without action."""
    result = steward_filter("The grid resonates with the flame" * 5)
    assert result is None


def test_allows_mythic_with_action():
    """Allow mythic language if action-grounded."""
    result = steward_filter("The field resonates. I will do this.")
    assert result is not None


def test_sustainability_check_valid():
    """Valid sustainable language."""
    assert check_sustainability("I will maintain this daily")
    assert check_sustainability("I choose to quit when needed")


def test_sustainability_check_invalid():
    """Block unsustainable compulsion patterns."""
    assert not check_sustainability("I must always do this")
    assert not check_sustainability("I can never stop")
    assert not check_sustainability("This is urgent immediately forever")


def test_compress_to_choices():
    """Compress to actionable points."""
    text = "Many words here. Do this. More noise. Quit that. Final thought."
    compressed = compress_to_choices(text)
    assert "Do this" in compressed
    assert "Quit that" in compressed
    assert "More noise" not in compressed


def test_empty_input():
    """Handle empty input."""
    assert steward_filter("") is None
    assert steward_filter(None) is None
