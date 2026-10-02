"""Deployment auth posture — the production guard must fail closed.

``api/auth.py`` carries a production guard: with ``ENVIRONMENT=production`` and
no (or invalid) ``FIREBASE_SERVICE_ACCOUNT_JSON`` the process must refuse to
start rather than serve unsigned tokens. These tests pin that contract so it
cannot regress.

They assert the *contract*, not the deployment: the deployment is configured by
its environment and is verified operationally, not here.

Each case runs in a subprocess so the module-level ``_init_firebase()`` call
re-executes against a controlled environment, isolated from the test process.
"""
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

#: Env vars that decide the auth posture. Stripped from the inherited env so the
#: subprocess is exercised against a known configuration, never the developer's.
_AUTH_ENV_VARS = (
    "ENVIRONMENT",
    "FIREBASE_SERVICE_ACCOUNT_JSON",
)


def _run_import(extra_env: dict[str, str], expression: str = "import api.auth"):
    env = {k: v for k, v in os.environ.items() if k not in _AUTH_ENV_VARS}
    env["PYTHONPATH"] = str(ROOT)
    env.update(extra_env)
    return subprocess.run(
        [sys.executable, "-c", expression],
        cwd=ROOT,
        env=env,
        capture_output=True,
        text=True,
        timeout=60,
    )


def test_production_without_credentials_refuses_to_start():
    r = _run_import({"ENVIRONMENT": "production"})
    assert r.returncode != 0, "production must not start without credentials"
    assert "FIREBASE_SERVICE_ACCOUNT_JSON is required in production" in r.stderr


def test_production_with_invalid_credentials_refuses_to_start():
    bogus = '{"type":"service_account","project_id":"x"}'
    r = _run_import(
        {"ENVIRONMENT": "production", "FIREBASE_SERVICE_ACCOUNT_JSON": bogus}
    )
    assert r.returncode != 0, "a misconfigured credential must be fatal, not a downgrade"
    assert "initialisation failed" in r.stderr


def test_non_production_without_credentials_falls_back_to_dev_mode():
    """Documents the fallback: outside production, absent credentials yield
    dev-mode (unsigned tokens)."""
    r = _run_import({}, "import api.auth; print('DEV_MODE', api.auth._dev_mode)")
    assert r.returncode == 0
    assert "DEV_MODE True" in r.stdout
