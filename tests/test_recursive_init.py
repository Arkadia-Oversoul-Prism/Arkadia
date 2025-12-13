import os

from weaver.recursive import RecursiveEngine


def test_recursive_engine_validate_and_ready():
    # Ensure the engine validates modules and respects enabled flag
    engine = RecursiveEngine(initial_task="test task", enabled=False)
    status = engine.validate()
    assert isinstance(status, dict)
    # Engine should not be ready if enabled is False
    assert engine.ready() is False

    # Toggle on and check ready only if modules are importable
    engine.enabled = True
    # If agent found and all modules importable the ready() should be a bool
    assert isinstance(engine.ready(), bool)


def test_recursive_engine_start_and_report():
    engine = RecursiveEngine(initial_task="testing", enabled=True)
    # Running start() without GEMINI_API_KEY should result in no updates but a completed short cycle
    engine.start()
    rep = engine.report()
    assert "cycle" in rep
    assert isinstance(rep["cycle"], int)
    assert isinstance(rep["updates"], list)
    assert isinstance(rep["commits"], list)
    assert isinstance(rep["errors"], list)


def test_set_depth_modifies_engine():
    engine = RecursiveEngine(initial_task="testing", enabled=True)
    engine.set_depth(4)
    assert engine.depth == 4
