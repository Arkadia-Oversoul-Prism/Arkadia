#!/usr/bin/env python3
"""
Arkadia IMS Auth Account Provisioner
=====================================
Creates or rotates Firebase Auth accounts for active IMS node holders.

Security boundary:
  - No password is stored in source control.
  - No credential document is written to disk.
  - Passwords are supplied through the environment or generated in-memory.
  - Generated passwords are printed once to stdout and must be captured by
    the operator through an approved secret-handling channel.

Requires:
  FIREBASE_SERVICE_ACCOUNT_JSON env var (full JSON contents)
  OR GOOGLE_APPLICATION_CREDENTIALS / Firebase Admin credentials.

Optional:
  ROTATE_EXISTING=1  Reset passwords for existing IMS accounts as well as
                     creating missing accounts.
  IMS_PASSWORD_<NODE_KEY>  Explicit password for a node when provisioning.
                           Example: IMS_PASSWORD_ZAHRUNE.

No credential artifact is persisted by this script.
"""

import os
import json
import secrets
import string

IMS_NODES = [
    {
        "node_key": "zahrune",
        "display_name": "Zahrune Nova · Divine Favour Yusuf",
        "ims_id": "IMS-004",
        "email": "zahrune@arkadia.nexus",
        "role": "Sovereign Architect",
        "access_level": 3,
    },
    {
        "node_key": "jessica",
        "display_name": "Jessica Whites · Eos-Ryn",
        "ims_id": "IMS-003b",
        "email": "jessica@arkadia.nexus",
        "role": "Heart Node",
        "access_level": 3,
    },
    {
        "node_key": "won",
        "display_name": "Won John Chong",
        "ims_id": "IMS-002",
        "email": "won@arkadia.nexus",
        "role": "Silent Architect",
        "access_level": 3,
    },
    {
        "node_key": "jay",
        "display_name": "Jay",
        "ims_id": "IMS-001",
        "email": "jay@arkadia.nexus",
        "role": "Terrasonic Root",
        "access_level": 3,
    },
    {
        "node_key": "eden",
        "display_name": "Eden",
        "ims_id": "IMS-003a",
        "email": "eden@arkadia.nexus",
        "role": "Sovereign Forge",
        "access_level": 3,
    },
]


def generated_password(length: int = 24) -> str:
    alphabet = string.ascii_letters + string.digits + "!@#$%^&*_-"
    return "".join(secrets.choice(alphabet) for _ in range(length))


def password_for(node: dict) -> str:
    """Resolve a password without ever persisting it."""
    env_name = f"IMS_PASSWORD_{node['node_key'].upper()}"
    supplied = os.environ.get(env_name, "").strip()
    return supplied or generated_password()


def try_firebase_admin():
    """Create or rotate Firebase accounts using Firebase Admin SDK."""
    try:
        import firebase_admin
        from firebase_admin import credentials, auth

        sa_json = os.environ.get("FIREBASE_SERVICE_ACCOUNT_JSON", "")
        if sa_json:
            cred = credentials.Certificate(json.loads(sa_json))
            if not firebase_admin._apps:
                firebase_admin.initialize_app(cred)
        elif not firebase_admin._apps:
            firebase_admin.initialize_app()

        rotate_existing = os.environ.get("ROTATE_EXISTING", "").strip().lower() in {
            "1", "true", "yes", "on"
        }
        results = []

        for node in IMS_NODES:
            password = password_for(node)
            try:
                user = auth.get_user_by_email(node["email"])
                if rotate_existing:
                    auth.update_user(user.uid, password=password)
                    print(f"[ROTATED] {node['email']} — uid: {user.uid} — one-time password: {password}")
                    status = "rotated"
                else:
                    print(f"[EXISTS] {node['email']} — uid: {user.uid} — unchanged")
                    status = "existing"
                results.append({"node_key": node["node_key"], "uid": user.uid, "email": node["email"], "status": status})
            except auth.UserNotFoundError:
                try:
                    user = auth.create_user(
                        email=node["email"],
                        password=password,
                        display_name=node["display_name"],
                    )
                    print(f"[CREATED] {node['email']} — uid: {user.uid} — one-time password: {password}")
                    results.append({"node_key": node["node_key"], "uid": user.uid, "email": node["email"], "status": "created"})
                except Exception as exc:
                    print(f"[ERROR] {node['email']}: {exc}")
                    results.append({"node_key": node["node_key"], "email": node["email"], "status": "error", "error": str(exc)})

        return results

    except ImportError:
        print("[ERROR] firebase-admin is not installed. Install it before provisioning.")
        return False
    except Exception as exc:
        print(f"[ERROR] Firebase Admin initialization failed: {exc}")
        return False


def main():
    print("=" * 60)
    print("  ARKADIA IMS AUTH PROVISIONER")
    print("  Credential boundary: external/in-memory only")
    print("=" * 60)
    print()

    if not os.environ.get("FIREBASE_SERVICE_ACCOUNT_JSON") and not os.environ.get("GOOGLE_APPLICATION_CREDENTIALS"):
        print("[ERROR] Firebase Admin credentials are required; no account changes performed.")
        raise SystemExit(1)

    results = try_firebase_admin()
    if results is False:
        raise SystemExit(1)

    created = sum(r["status"] == "created" for r in results)
    rotated = sum(r["status"] == "rotated" for r in results)
    existing = sum(r["status"] == "existing" for r in results)
    errors = sum(r["status"] == "error" for r in results)

    print()
    print("── Result ───────────────────────────────────────────────────")
    print(f"  Created: {created}")
    print(f"  Rotated: {rotated}")
    print(f"  Existing/unchanged: {existing}")
    print(f"  Errors: {errors}")
    print()
    print("No credential file was written to disk.")
    print("One-time passwords, when generated or rotated, were emitted only to stdout.")
    print("=" * 60)

    if errors:
        raise SystemExit(2)


if __name__ == "__main__":
    main()
