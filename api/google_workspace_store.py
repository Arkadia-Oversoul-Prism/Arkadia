"""Encrypted per-user Google Workspace connection state."""
from __future__ import annotations
import base64, hashlib, json, os, threading, time, uuid
from pathlib import Path
from cryptography.fernet import Fernet, InvalidToken

_LOCK=threading.Lock()
_PATH=Path(os.environ.get("SOLSPIRE_DATA_DIR","data"))/"google_workspace_connections.json"

def _fernet():
    secret=os.environ.get("SOVEREIGN_KEY","").strip()
    if not secret: raise RuntimeError("SOVEREIGN_KEY is required")
    return Fernet(base64.urlsafe_b64encode(hashlib.sha256(secret.encode()).digest()))

def _load():
    if not _PATH.exists(): return {}
    try: return json.loads(_PATH.read_text(encoding="utf-8"))
    except Exception: return {}

def _save(v):
    _PATH.parent.mkdir(parents=True,exist_ok=True)
    tmp=_PATH.with_suffix(".tmp"); tmp.write_text(json.dumps(v,indent=2),encoding="utf-8")
    os.replace(tmp,_PATH)
    try: os.chmod(_PATH,0o600)
    except OSError: pass

def _enc(v): return _fernet().encrypt(json.dumps(v).encode()).decode()

def _dec(v):
    try: return json.loads(_fernet().decrypt(v.encode()).decode())
    except InvalidToken as exc: raise RuntimeError("Google Workspace credential cannot be decrypted") from exc

def save_oauth(uid, token):
    with _LOCK:
        db=_load(); u=db.setdefault(uid,{})
        prev=_dec(u["oauth"]) if u.get("oauth") else {}
        merged={**prev,**token,"updated_at":time.time()}
        u["oauth"]=_enc(merged); _save(db)

def get_oauth(uid):
    with _LOCK:
        u=_load().get(uid,{})
        return _dec(u["oauth"]) if u.get("oauth") else None

def save_trigger(uid, trigger_id, notify_uri, inputs=None):
    with _LOCK:
        db=_load(); u=db.setdefault(uid,{})
        triggers=u.setdefault("triggers",{})
        triggers[trigger_id]={"notify_uri":notify_uri,"inputs":inputs or {},"active":True,"updated_at":time.time()}
        _save(db)

def delete_trigger(uid, trigger_id):
    with _LOCK:
        db=_load(); u=db.setdefault(uid,{})
        t=u.setdefault("triggers",{}).get(trigger_id)
        if t: t["active"]=False; t["updated_at"]=time.time()
        _save(db)

def list_triggers(uid):
    with _LOCK:
        return list(_load().get(uid,{}).get("triggers",{}).values())

def save_device_token(uid, token, platform="android"):
    with _LOCK:
        db=_load(); u=db.setdefault(uid,{})
        devices=u.setdefault("devices",{})
        devices[token]={"platform":platform,"active":True,"updated_at":time.time()}
        _save(db)

def list_device_tokens(uid):
    with _LOCK:
        return [k for k,v in _load().get(uid,{}).get("devices",{}).items() if v.get("active")]

def revoke_device_token(uid, token):
    with _LOCK:
        db=_load(); u=db.setdefault(uid,{})
        if token in u.setdefault("devices",{}): u["devices"][token]["active"]=False
        _save(db)
