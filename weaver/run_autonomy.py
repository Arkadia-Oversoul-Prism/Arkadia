import os
import json
from weaver.autonomy import load_autonomy_config, run_scheduled_once, validate_autonomy_config
from weaver.logger import get_logger

LOGGER = get_logger()


def main():
    try:
        cfg = load_autonomy_config()
    except FileNotFoundError:
        LOGGER.warning('Autonomy manifest not found; skipping')
        return
    if not validate_autonomy_config(cfg):
        LOGGER.warning('Autonomy config invalid; skipping')
        return

    # Only run if env var ARKADIA_AUTONOMOUS matches the requirement (default true set in manifest for now)
    req = cfg.get('require_env', {})
    for k, v in req.items():
        if os.environ.get(k) != v:
            LOGGER.info('Autonomy env requirement not satisfied: %s expected %s, got %s', k, v, os.environ.get(k))
            return

    # Determine if we should use LLM or stub
    use_stub = True  # deterministic behavior requested by user

    # Run scheduled once (the scheduler would call this repeatedly in a full implementation)
    res = run_scheduled_once(config=cfg, use_stub=use_stub)
    LOGGER.info('Autonomy run result: %s', res)


if __name__ == '__main__':
    main()
