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


def test_bare_mythic_mention_is_not_identity_escalation():
    """Naming a mythic concept is not claiming it as identity."""
    assert steward_filter("The oversoul is a theme in this text") is not None
    assert steward_filter("We discuss the eternal in class") is not None


def test_identity_claim_is_blocked_in_surrounding_context():
    """A claim with intervening words still trips rule 1."""
    assert steward_filter("You are the chosen one") is None
    assert steward_filter("We are eternal") is None
    assert steward_filter("I am god") is None


def test_action_requires_a_word_boundary():
    """"words" contains "do" but is not an action."""
    assert steward_filter("Many words here." + " noise" * 40) is None
    assert steward_filter("Many words here. Do this." + " noise" * 40) is not None


def test_symbolic_density_is_what_blocks_not_recurrence():
    """One symbolic mention passes; dominant symbolic density does not."""
    assert steward_filter("The grid holds the plan. We do the work.") is not None
    assert steward_filter("Grid flame resonance field.") is None
