"""
P1-1 Two-User Beta Verification — deterministic plain-_python_ runner.

Runs the exact mission-defined two-account scenario against a target Arkadia
backend (local dev or production) using disposable Firebase identities:

  ACCOUNT A: signup → identity → save note → own field → edit → delete →
             public post → owner delete → public post (kept)
  ACCOUNT B: signup → identity → A's private memory absent → own note →
             own field → B post → cannot delete A's post
  THEN:      A sees B's post; B sees A's post; B gets 403 deleting A's post;
             unauthenticated DELETE == 401.

Exit code 0 iff every check passes. Disposable users are always scrubbed after.
"""
import json
import sys
import os
import uuid

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from firebase_harness import (  # noqa: E402
    DisposableUser,
    ProductionClient,
    provision_user,
    delete_user,
    refresh_id_token,
    base_url,
)

RUN_ID = uuid.uuid4().hex[:8]
FAILS: list[str] = []
LOG: list[str] = []


def check(name: str, ok: bool, detail: str = ""):
    line = f"[{'PASS' if ok else 'FAIL'}] {name}" + (f" — {detail}" if detail else "")
    LOG.append(line)
    if not ok:
        FAILS.append(name)


def req(client: ProductionClient, method: str, path: str, body: dict | None):
    status, data = client.request(method, path, body=body)
    return status, data


def main() -> int:
    url = base_url()
    print(f"P1-1 TWO-USER CHECK — target: {url} run: {RUN_ID}")

    a_user: DisposableUser = provision_user(RUN_ID, "user-a")
    b_user: DisposableUser = provision_user(RUN_ID, "user-b")
    anon = ProductionClient(url)

    try:
        A = ProductionClient(url, a_user)
        B = ProductionClient(url, b_user)

        # ── IDENTITY ────────────────────────────────────────────────────────
        sA, meA = req(A, "GET", "/api/me", None)
        sB, meB = req(B, "GET", "/api/me", None)
        check("A /api/me 200", sA == 200)
        check("B /api/me 200", sB == 200)
        check("A uid != B uid", meA.get("user", {}).get("uid") != meB.get("user", {}).get("uid"))
        check("identity not sovereign fixture",
              meA.get("user", {}).get("display_name", "").lower() not in ("zahrune", "sovereign"))

        nA_owner = meA.get("user", {}).get("uid")
        nB_owner = meB.get("user", {}).get("uid")

        # ── A PRIVATE MEMORY (Save to memory ⇒ Knowledge OS) ───────────────
        markerA = f"P1-MARKER-A-{RUN_ID}"
        s1, ing1 = req(A, "POST", "/api/personal/ingest-note",
                       {"title": markerA, "content": markerA, "tags": ["p1-test"]})
        check("A save memory", s1 in (200, 201))
        uuid_a = (ing1.get("ingest") or {}).get("note_uuid") or ing1.get("note_uuid")

        s2a, notesA = req(A, "GET", "/api/knowledge/notes", None)
        check("A field contains A marker", s2a == 200 and markerA in json.dumps(notesA, default=str))

        # ── B CANNOT SEE A'S PRIVATE MEMORY ────────────────────────────────
        s2b, notesB = req(B, "GET", "/api/knowledge/notes", None)
        noA = json.dumps(notesB, default=str)
        check("B field has NO A marker", markerA not in noA)

        markerB = f"P1-MARKER-B-{RUN_ID}"
        s1b, ing1b = req(B, "POST", "/api/personal/ingest-note",
                         {"title": markerB, "content": markerB, "tags": ["p1-test"]})
        check("B save memory", s1b in (200, 201))
        uuid_b = (ing1b.get("ingest") or {}).get("note_uuid") or ing1b.get("note_uuid")

        sBb, notesBB = req(B, "GET", "/api/knowledge/notes", None)
        check("B field contains B marker", markerB in json.dumps(notesBB, default=str))

        # ── A GOVERNANCE: PATCH + DELETE OWN NOTE ──────────────────────────
        if uuid_a:
            pA, _ = req(A, "PATCH", f"/api/knowledge/notes/{uuid_a}", {"title": "A-EDITED"})
            check("A PATCH own note", pA == 200)
            dA, _ = req(A, "DELETE", f"/api/knowledge/notes/{uuid_a}", None)
            check("A DELETE own note", dA == 200)
        # B governance cleanup for B note done at end

        # ── NOVANET PUBLIC POSTS ────────────────────────────────────────────
        tA, postA = req(A, "POST", "/api/transmissions",
                        {"content": f"Public post A {RUN_ID}",
                         "author": {"name": "User A", "avatar": "◆", "role": "Node"}})
        idA = postA.get("transmission", {}).get("id")
        check("A create post", tA == 200 and idA)
        check("A post owner bound to A uid", postA["transmission"]["owner_uid"] == nA_owner)

        tB, postB = req(B, "POST", "/api/transmissions",
                        {"content": f"Public post B {RUN_ID}",
                         "author": {"name": "User B", "avatar": "☽", "role": "Node"}})
        idB = postB.get("transmission", {}).get("id")
        check("B create post", tB == 200 and idB)
        check("B post owner bound to B uid", postB["transmission"]["owner_uid"] == nB_owner)

        # visibility: B sees A post; A sees B post (public layering)
        lsB, feedB = req(B, "GET", "/api/transmissions", None)
        lsA, feedA = req(A, "GET", "/api/transmissions", None)
        check("B sees A's public post", any(p["id"] == idA for p in feedB.get("transmissions", [])))
        check("A sees B's public post", any(p["id"] == idB for p in feedA.get("transmissions", [])))

        # comment binding
        cB, comment = req(B, "POST", f"/api/transmissions/{idA}/comment",
                          {"content": "B comment", "author": {"name": "User B"}})
        check("B comment on A post", cB == 200)
        check("comment author bound to uid", cB == 200 and comment.get("comment", {}).get("owner_uid") == nB_owner)

        # deletion semantics
        d_anon, _ = req(anon, "DELETE", f"/api/transmissions/{idA}", None)
        check("unauth delete =401", d_anon == 401)
        d_bad, _ = req(B, "DELETE", f"/api/transmissions/{idA}", None)
        check("B cannot delete A's post", d_bad == 403)

        d_own, _ = req(A, "DELETE", f"/api/transmissions/{idA}", None)
        check("A can delete own post", d_own == 200)
        # cleanup B artifacts
        clB, _ = req(B, "DELETE", f"/api/transmissions/{idB}", None)
        check("B can delete own post", clB == 200)
        if uuid_b:
            dB_note, _ = req(B, "DELETE", f"/api/knowledge/notes/{uuid_b}", None)
            check("B DELETE own note", dB_note == 200)

        # final report
        for line in LOG:
            print(line)

        ok = not FAILS
        print(f"RESULT: {'GREEN' if ok else 'RED'} ({len(FAILS)} fail)")
        return 0 if ok else 1

    finally:
        delete_user(a_user)
        delete_user(b_user)


if __name__ == "__main__":
    sys.exit(main())
