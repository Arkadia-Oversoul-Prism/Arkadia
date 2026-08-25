"""P1-A production two-user verification — disposable Firebase identities.

Proves against the live backend:
  • identity derives from auth uid (no canon/IMS silent match)
  • PATCH /api/me persists owner-only display name (B cannot change A)
  • POST /api/messages A->B and B->A with server-derived sender
  • thread/inbox recipient isolation; unauthenticated send rejected
Disposable users are deleted afterward. Run:
  python tests/production/p1a_verify.py
"""
import json
import os
import sys
import uuid

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from firebase_harness import (  # noqa: E402
    DisposableUser, ProductionClient, provision_user, delete_user, base_url,
)

RUN_ID = uuid.uuid4().hex[:8]
FAILS: list[str] = []
LOG: list[str] = []


def check(name: str, ok: bool, detail: str = ""):
    line = f"[{'PASS' if ok else 'FAIL'}] {name}" + (f" — {detail}" if detail else "")
    LOG.append(line)
    if not ok:
        FAILS.append(name)


def main() -> int:
    url = base_url()
    print(f"P1-A PRODUCTION VERIFY — target: {url} run: {RUN_ID}")

    a: DisposableUser = provision_user(RUN_ID, "p1a-a")
    b: DisposableUser = provision_user(RUN_ID, "p1a-b")
    anon = ProductionClient(url)
    A = ProductionClient(url, a)
    B = ProductionClient(url, b)

    try:
        # ── IDENTITY ────────────────────────────────────────────────────────
        sA, meA = A.request("GET", "/api/me")
        sB, meB = B.request("GET", "/api/me")
        check("A /api/me 200", sA == 200)
        check("B /api/me 200", sB == 200)
        uA, uB = meA.get("user", {}), meB.get("user", {})
        check("A uid == provisioned uid", uA.get("uid") == a.uid)
        check("A uid != B uid", uA.get("uid") != uB.get("uid"))
        check("A has no canon node_key", uA.get("node_key") in (None, ""))
        check("A role is Guest (no silent IMS)", uA.get("role") == "Guest")
        check("A access_level 0", uA.get("access_level", 99) == 0)

        # ── PROFILE PATCH (owner-only) ─────────────────────────────────────
        pA, _ = A.request("PATCH", "/api/me", {"display_name": f"P1A-A-{RUN_ID}"})
        check("A PATCH /api/me 200", pA == 200)
        gA, meA2 = A.request("GET", "/api/me")
        check("A GET reflects persisted name", meA2.get("user", {}).get("display_name") == f"P1A-A-{RUN_ID}")

        pB, _ = B.request("PATCH", "/api/me", {"display_name": f"P1A-B-{RUN_ID}"})
        check("B PATCH own name 200", pB == 200)
        gA2, meA3 = A.request("GET", "/api/me")
        check("A unaffected by B PATCH", meA3.get("user", {}).get("display_name") == f"P1A-A-{RUN_ID}")

        # B attempts to overwrite A via uid spoof in body (server must ignore)
        sSpoof, spB = B.request("PATCH", "/api/me", {"display_name": "HACKED", "uid": a.uid})
        check("B uid-spoof ignored (still B)", spB.get("user", {}).get("uid") == b.uid)
        gA3, meA4 = A.request("GET", "/api/me")
        check("A name intact after B spoof", meA4.get("user", {}).get("display_name") == f"P1A-A-{RUN_ID}")

        aUnauth, _ = anon.request("PATCH", "/api/me", {"display_name": "anon"})
        check("unauth PATCH /api/me == 401", aUnauth == 401)

        # ── MESSAGING A->B / B->A ──────────────────────────────────────────
        sAB, mAB = A.request("POST", "/api/messages", {"recipient_uid": b.uid, "content": f"A->B {RUN_ID}"})
        check("A->B send 200", sAB == 200)
        check("A->B sender == A uid", mAB.get("message", {}).get("sender_uid") == a.uid)
        check("A->B recipient == B uid", mAB.get("message", {}).get("recipient_uid") == b.uid)

        sBA, mBA = B.request("POST", "/api/messages", {"recipient_uid": a.uid, "content": f"B->A {RUN_ID}"})
        check("B->A send 200", sBA == 200)
        check("B->A sender == B uid", mBA.get("message", {}).get("sender_uid") == b.uid)

        # persistence + thread read by participants
        thA_s, thA = A.request("GET", f"/api/messages/thread/{b.uid}")
        msgsA = thA.get("messages", [])
        check("A reads thread with B", thA_s == 200 and len(msgsA) == 2)
        check("thread persisted (2 msgs incl both dirs)",
              {m.get("sender_uid") for m in msgsA} == {a.uid, b.uid})
        thB_s, thB = B.request("GET", f"/api/messages/thread/{a.uid}")
        check("B reads thread with A (2 msgs)", thB_s == 200 and len(thB.get("messages", [])) == 2)

        # inbox recipient view
        ib_s, ib = B.request("GET", "/api/messages/inbox")
        convs = ib.get("conversations", [])
        check("B inbox lists A", ib_s == 200 and any(c.get("peer_uid") == a.uid for c in convs))

        # sender spoof attempt
        sSp, mSp = A.request("POST", "/api/messages",
                             {"recipient_uid": b.uid, "content": "spoof", "sender_uid": "mallory"})
        check("sender spoof ignored (sender == A)", mSp.get("message", {}).get("sender_uid") == a.uid)

        # isolation: third party cannot read A-B thread
        c: DisposableUser = provision_user(RUN_ID, "p1a-c")
        C = ProductionClient(url, c)
        try:
            thC_s, thC = C.request("GET", f"/api/messages/thread/{a.uid}")
            check("C cannot read A-B thread (0 msgs)", len(thC.get("messages", [])) == 0)
            ibC_s, ibC = C.request("GET", "/api/messages/inbox")
            check("C inbox empty", len(ibC.get("conversations", [])) == 0)
        finally:
            delete_user(c)

        mUnauth, _ = anon.request("POST", "/api/messages", {"recipient_uid": b.uid, "content": "x"})
        check("unauth send == 401", mUnauth == 401)

        for line in LOG:
            print(line)
        ok = not FAILS
        print(f"RESULT: {'GREEN' if ok else 'RED'} ({len(FAILS)} fail)")
        return 0 if ok else 1
    finally:
        delete_user(a)
        delete_user(b)


if __name__ == "__main__":
    sys.exit(main())
