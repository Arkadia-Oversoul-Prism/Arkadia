import ast
from pathlib import Path


ROUTER = Path("solspire/console_router.py")


def _functions(tree):
    return {node.name: node for node in tree.body if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))}


def test_r4_has_one_canonical_run_pipeline():
    tree = ast.parse(ROUTER.read_text(encoding="utf-8"))
    functions = _functions(tree)

    assert "_execute_run" in functions
    helper = functions["_execute_run"]
    names = [node.func.attr if isinstance(node.func, ast.Attribute) else node.func.id
             for node in ast.walk(helper)
             if isinstance(node, ast.Call) and isinstance(node.func, (ast.Attribute, ast.Name))]

    assert "classify" in names
    assert "create_plan" in names
    assert "validate_plan" in names
    assert "execute" in names


def test_r4_global_and_project_routes_delegate_to_same_pipeline():
    tree = ast.parse(ROUTER.read_text(encoding="utf-8"))
    functions = _functions(tree)

    global_run = functions["run_request"]
    project_run = functions["project_run"]

    def calls_helper(node):
        return any(
            isinstance(call.func, ast.Name) and call.func.id == "_execute_run"
            for call in ast.walk(node)
            if isinstance(call, ast.Call)
        )

    assert calls_helper(global_run)
    assert calls_helper(project_run)


def test_r4_project_route_contains_only_contextual_logging_after_pipeline():
    tree = ast.parse(ROUTER.read_text(encoding="utf-8"))
    project_run = _functions(tree)["project_run"]

    called_names = {
        call.func.attr if isinstance(call.func, ast.Attribute) else call.func.id
        for call in ast.walk(project_run)
        if isinstance(call, ast.Call) and isinstance(call.func, (ast.Attribute, ast.Name))
    }

    assert "_execute_run" in called_names
    assert "log_event" in called_names
    assert "classify" not in called_names
    assert "create_plan" not in called_names
    assert "validate_plan" not in called_names
    assert "execute" not in called_names
