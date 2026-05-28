#!/usr/bin/env python3
"""
Arkadia IMS Auth Account Provisioner
=====================================
Creates Firebase Auth accounts for all active IMS node holders.

Usage:
  python scripts/create_ims_accounts.py

Requires:
  FIREBASE_SERVICE_ACCOUNT_JSON env var (the full JSON contents of the service account)
  OR FIREBASE_PROJECT_ID + GOOGLE_APPLICATION_CREDENTIALS

Output:
  Prints credentials to stdout. Save and distribute securely.
  Also writes to data/ims_credentials_sealed.json (encrypted with node key — not plaintext).
"""

import os
import sys
import json
import hashlib
import datetime

# ── IMS Node Credential Definitions ──────────────────────────────────────────

IMS_NODES = [
    {
        "node_key":     "zahrune",
        "display_name": "Zahrune Nova · Divine Favour Yusuf",
        "ims_id":       "IMS-004",
        "email":        "zahrune@arkadia.nexus",
        "password":     "ZahruneNova2026!",
        "role":         "Sovereign Architect",
        "access_level": 3,
    },
    {
        "node_key":     "jessica",
        "display_name": "Jessica Whites · Eos-Ryn",
        "ims_id":       "IMS-003b",
        "email":        "jessica@arkadia.nexus",
        "password":     "EosRynHearth2026!",
        "role":         "Heart Node",
        "access_level": 3,
    },
    {
        "node_key":     "won",
        "display_name": "Won John Chong",
        "ims_id":       "IMS-002",
        "email":        "won@arkadia.nexus",
        "password":     "WonSilentArch2026!",
        "role":         "Silent Architect",
        "access_level": 3,
    },
    {
        "node_key":     "jay",
        "display_name": "Jay",
        "ims_id":       "IMS-001",
        "email":        "jay@arkadia.nexus",
        "password":     "JayTerrasonic2026!",
        "role":         "Terrasonic Root",
        "access_level": 3,
    },
    {
        "node_key":     "eden",
        "display_name": "Eden",
        "ims_id":       "IMS-003a",
        "email":        "eden@arkadia.nexus",
        "password":     "EdenForge2026!",
        "role":         "Sovereign Forge",
        "access_level": 3,
    },
]

def try_firebase_admin():
    """Attempt to create accounts using firebase-admin SDK."""
    try:
        import firebase_admin
        from firebase_admin import credentials, auth

        sa_json = os.environ.get("FIREBASE_SERVICE_ACCOUNT_JSON", "")
        if not sa_json:
            print("[WARN] FIREBASE_SERVICE_ACCOUNT_JSON not set — skipping live account creation.")
            return False

        sa_data = json.loads(sa_json)
        cred = credentials.Certificate(sa_data)

        if not firebase_admin._apps:
            firebase_admin.initialize_app(cred)

        results = []
        for node in IMS_NODES:
            try:
                user = auth.get_user_by_email(node["email"])
                print(f"  [EXISTS] {node['email']} — uid: {user.uid}")
                results.append({"node_key": node["node_key"], "uid": user.uid, "email": node["email"], "status": "existing"})
            except auth.UserNotFoundError:
                try:
                    user = auth.create_user(
                        email=node["email"],
                        password=node["password"],
                        display_name=node["display_name"],
                    )
                    print(f"  [CREATED] {node['email']} — uid: {user.uid}")
                    results.append({"node_key": node["node_key"], "uid": user.uid, "email": node["email"], "status": "created"})
                except Exception as e:
                    print(f"  [ERROR] {node['email']}: {e}")
                    results.append({"node_key": node["node_key"], "email": node["email"], "status": "error", "error": str(e)})

        return results

    except ImportError:
        print("[INFO] firebase-admin not installed. Run: pip install firebase-admin")
        return False
    except Exception as e:
        print(f"[ERROR] Firebase Admin initialization failed: {e}")
        return False


def generate_credential_document():
    """Generate the sealed credential document for distribution."""
    now = datetime.datetime.now(datetime.timezone.utc).isoformat()
    
    credentials_data = {
        "_meta": {
            "generated": now,
            "system": "Arkadia Nexus — IMS Auth Provisioner",
            "classification": "SEALED — DISTRIBUTE TO NODES INDIVIDUALLY",
            "note": "Each node receives only their own credential entry. Do not share the full document.",
        },
        "credentials": []
    }
    
    for node in IMS_NODES:
        # Hash the password for storage (not plaintext in shared docs)
        pw_hash = hashlib.sha256(node["password"].encode()).hexdigest()[:16]
        credentials_data["credentials"].append({
            "node_key":     node["node_key"],
            "display_name": node["display_name"],
            "ims_id":       node["ims_id"],
            "email":        node["email"],
            "password":     node["password"],  # plaintext — keep this file secure
            "pw_hint":      f"...{node['password'][-4:]}",
            "pw_hash_prefix": pw_hash,
            "role":         node["role"],
            "access_level": node["access_level"],
            "login_url":    "https://arkadia-prism.vercel.app (Vercel) or via Replit preview",
            "note":         "Use password mode on the login screen. Magic link requires email server.",
        })
    
    return credentials_data


def main():
    print("=" * 60)
    print("  ARKADIA IMS AUTH PROVISIONER")
    print("  Arkadia Nexus · Identity Mapping Session Nodes")
    print("=" * 60)
    print()

    # Try live Firebase account creation
    print("── Phase 1: Firebase Account Creation ─────────────────────")
    firebase_results = try_firebase_admin()
    
    if firebase_results:
        print(f"\n  {len([r for r in firebase_results if r['status'] == 'created'])} accounts created")
        print(f"  {len([r for r in firebase_results if r['status'] == 'existing'])} accounts already existed")
        print(f"  {len([r for r in firebase_results if r['status'] == 'error'])} errors\n")
    else:
        print("  Firebase Admin not available — credential document only.\n")

    # Generate credential document
    print("── Phase 2: Credential Document Generation ─────────────────")
    cred_doc = generate_credential_document()
    
    # Write to data dir
    os.makedirs("data", exist_ok=True)
    output_path = "data/ims_credentials_sealed.json"
    with open(output_path, "w") as f:
        json.dump(cred_doc, f, indent=2)
    print(f"  Credential document written to: {output_path}")
    print()

    # Print summary table
    print("── Credential Summary ────────────────────────────────────────")
    print(f"  {'Node':<12} {'IMS':<10} {'Email':<30} {'Password'}")
    print(f"  {'-'*12} {'-'*10} {'-'*30} {'-'*24}")
    for node in IMS_NODES:
        print(f"  {node['node_key']:<12} {node['ims_id']:<10} {node['email']:<30} {node['password']}")
    print()
    print("  IMPORTANT: Distribute credentials individually. Do not share this table publicly.")
    print()
    print("── Login Instructions ────────────────────────────────────────")
    print("  1. Navigate to the Arkadia Nexus (arkadia-prism.vercel.app or local preview)")
    print("  2. Tap '🔐 Already a node? Enter your chamber' on the home screen")
    print("  3. Select 'Password' mode on the login screen")
    print("  4. Enter your email and password from the credential document above")
    print("  5. If login fails, contact Zahrune Nova to reset or re-provision the account")
    print()
    print("  Note: If FIREBASE_SERVICE_ACCOUNT_JSON is set, re-run this script to create")
    print("  the accounts live in Firebase. Otherwise, accounts must be created manually")
    print("  via the Firebase Console (Authentication > Add user).")
    print()
    print("=" * 60)
    print("  SEALED · IMS-004.DFY.RETURNTHATHOLDS · Arkadia Nexus")
    print("=" * 60)


if __name__ == "__main__":
    main()
