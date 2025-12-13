import os
from .recursive import RecursiveEngine
from .llm import available_providers


def report() -> dict:
    engine = RecursiveEngine(enabled=os.environ.get("ARKADIA_RECURSIVE_ENABLED", "false").lower() in ("1", "true", "yes"))
    status = {
        "enabled": engine.enabled,
        "depth": engine.depth,
        "interval": engine.interval,
        "module_status": engine.validate(),
        "ready": engine.ready(),
        "llm_providers": available_providers(),
    }
    return status


if __name__ == "__main__":
    import json
    print(json.dumps(report(), indent=2))
