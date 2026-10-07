"""Provision a disposable Firebase identity for AEAS Gate 3 acceptance.

Uses the repository's existing harness (tests/production/firebase_harness.py),
which signs up through the public Identity Toolkit with the same web API key the
frontend uses. Credentials are written to a local file outside the repository and
are never printed. Cleanup deletes the account.

Usage:
  python tools/aeas-browser-runner/provision-identity.py provision <outfile>
  python tools/aeas-browser-runner/provision-identity.py cleanup  <outfile>
"""
from __future__ import annotations

import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from tests.production.firebase_harness import (  # noqa: E402
    DisposableUser,
    delete_user,
    provision_user,
    refresh_id_token,
)

RUN_ID = os.environ.get("AEAS_RUN_ID", "aeas-gate3")


def main() -> int:
    action, path = sys.argv[1], sys.argv[2]
    if action == "provision":
        user = provision_user(RUN_ID, "gate3")
        refresh_id_token(user)  # confirm the account is usable before we rely on it
        with open(path, "w") as handle:
            json.dump(
                {"email": user.email, "password": user._password, "uid": user.uid, "run_id": user.run_id},
                handle,
            )
        os.chmod(path, 0o600)
        domain = user.email.split("@")[-1]
        print(f"provisioned uid={user.uid[:8]}... domain={domain} file={path}")
        return 0

    if action == "cleanup":
        with open(path) as handle:
            saved = json.load(handle)
        user = DisposableUser(
            email=saved["email"],
            uid=saved["uid"],
            _password=saved["password"],
            _id_token="",
            run_id=saved["run_id"],
        )
        refresh_id_token(user)
        ok = delete_user(user)
        os.remove(path)
        print(f"cleanup deleted={ok}")
        return 0 if ok else 1

    print("usage: provision-identity.py {provision|cleanup} <file>", file=sys.stderr)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
