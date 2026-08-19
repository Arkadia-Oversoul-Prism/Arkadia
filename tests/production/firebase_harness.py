"""
Phase 0C — disposable Firebase identity provisioning via Identity Toolkit.

Uses the public Firebase Web API key (same as the frontend) to:
  signUp → idToken → Arkadia API → accounts:delete

No Admin SDK required. No manual token handling.
Never logs passwords or ID tokens.
"""
from __future__ import annotations

import json
import os
import secrets
import string
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Any, Optional

# Public Firebase web config (embedded in frontend; not a secret)
DEFAULT_FIREBASE_API_KEY = "AIzaSyDfu2qD5aONhw4KxOjHyE2a7VEf8cVrk9A"
DEFAULT_FIREBASE_PROJECT_ID = "arkadia-2d4a7"
DEFAULT_BASE_URL = "https://arkadia-kw64.onrender.com"

IDENTITY_TOOLKIT = "https://identitytoolkit.googleapis.com/v1"


def _api_key() -> str:
    return (
        os.environ.get("FIREBASE_WEB_API_KEY")
        or os.environ.get("VITE_FIREBASE_API_KEY")
        or DEFAULT_FIREBASE_API_KEY
    )


def _redact(s: str) -> str:
    if not s:
        return s
    # scrub JWT-shaped strings
    import re
    return re.sub(r"eyJ[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+", "[REDACTED_JWT]", s)


@dataclass
class DisposableUser:
    email: str
    uid: str
    _password: str
    _id_token: str
    run_id: str

    @property
    def authorization(self) -> str:
        return f"Bearer {self._id_token}"

    def scrubbed(self) -> dict:
        return {"email": self.email, "uid": self.uid, "run_id": self.run_id}


def _http_json(method: str, url: str, body: Optional[dict] = None, headers: Optional[dict] = None, timeout: int = 60) -> tuple[int, Any]:
    hdrs = {"Content-Type": "application/json", **(headers or {})}
    data = None if body is None else json.dumps(body).encode()
    req = urllib.request.Request(url, data=data, headers=hdrs, method=method)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            raw = resp.read().decode() or "null"
            try:
                return resp.status, json.loads(raw)
            except json.JSONDecodeError:
                return resp.status, {"_raw": raw[:500]}
    except urllib.error.HTTPError as e:
        raw = e.read().decode()
        try:
            payload = json.loads(raw)
        except Exception:
            payload = {"_raw": _redact(raw[:500])}
        return e.code, payload
    except Exception as e:
        return 0, {"error": str(e)}


def provision_user(run_id: str, label: str) -> DisposableUser:
    """Create a disposable Firebase Auth user and return with fresh ID token."""
    api_key = _api_key()
    suffix = secrets.token_hex(6)
    # use a domain that Identity Toolkit accepts (gmail-like not required for test)
    email = f"arkadia.isolation.{label}.{suffix}@gmail.com"
    password = "Ark0!" + secrets.token_urlsafe(20)
    status, data = _http_json(
        "POST",
        f"{IDENTITY_TOOLKIT}/accounts:signUp?key={api_key}",
        {"email": email, "password": password, "returnSecureToken": True},
    )
    if status != 200 or not data.get("idToken"):
        raise RuntimeError(f"signUp failed for {label}: status={status} body={_redact(str(data))[:200]}")
    return DisposableUser(
        email=email,
        uid=data["localId"],
        _password=password,
        _id_token=data["idToken"],
        run_id=run_id,
    )


def delete_user(user: DisposableUser) -> bool:
    """Delete disposable user via Identity Toolkit (requires their idToken)."""
    api_key = _api_key()
    status, data = _http_json(
        "POST",
        f"{IDENTITY_TOOLKIT}/accounts:delete?key={api_key}",
        {"idToken": user._id_token},
    )
    return status == 200


def refresh_id_token(user: DisposableUser) -> None:
    """Re-sign-in to refresh ID token if needed."""
    api_key = _api_key()
    status, data = _http_json(
        "POST",
        f"{IDENTITY_TOOLKIT}/accounts:signInWithPassword?key={api_key}",
        {"email": user.email, "password": user._password, "returnSecureToken": True},
    )
    if status != 200 or not data.get("idToken"):
        raise RuntimeError(f"signIn failed: status={status}")
    user._id_token = data["idToken"]


class ProductionClient:
    def __init__(self, base_url: str, user: Optional[DisposableUser] = None):
        self.base_url = base_url.rstrip("/")
        self.user = user

    def request(self, method: str, path: str, body: Optional[dict] = None, timeout: int = 90) -> tuple[int, Any]:
        headers = {}
        if self.user:
            headers["Authorization"] = self.user.authorization
        return _http_json(method, self.base_url + path, body=body, headers=headers, timeout=timeout)

    def get(self, path: str, **kw) -> tuple[int, Any]:
        return self.request("GET", path, **kw)

    def post(self, path: str, body: Optional[dict] = None, **kw) -> tuple[int, Any]:
        return self.request("POST", path, body=body, **kw)


def marker_present(payload: Any, marker: str) -> bool:
    try:
        blob = json.dumps(payload, default=str)
    except Exception:
        blob = str(payload)
    return marker in blob


def production_gate_enabled() -> bool:
    return os.environ.get("ARKADIA_RUN_PRODUCTION_ISOLATION", "").strip() == "1"


def base_url() -> str:
    return os.environ.get("ARKADIA_PRODUCTION_BASE_URL", DEFAULT_BASE_URL).rstrip("/")
