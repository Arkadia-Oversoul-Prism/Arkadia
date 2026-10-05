"""Google Workspace Attention Bridge.

User-authorized OAuth for Tasks/Keep/Workspace Studio, Workspace Studio
subscription lifecycle, Keep feed delivery, FCM push delivery, and delivery
acknowledgements into the canonical evidence ledger.
"""
from __future__ import annotations
import hashlib, hmac, json, os, time, urllib.parse
from typing import Any
import httpx
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import RedirectResponse
from pydantic import BaseModel, Field
from api.auth import require_auth
from api.google_workspace_store import (
    delete_trigger, get_oauth, list_device_tokens, list_triggers,
    revoke_device_token, save_device_token, save_oauth, save_trigger,
)

router=APIRouter(prefix="/api/google-workspace",tags=["Google Workspace Attention"])

SCOPES=[
 "openid","email",
 "https://www.googleapis.com/auth/tasks",
 "https://www.googleapis.com/auth/keep",
 "https://www.googleapis.com/auth/workspace.studio.trigger",
]
AUTH_URL="https://accounts.google.com/o/oauth2/v2/auth"
TOKEN_URL="https://oauth2.googleapis.com/token"

def _cfg():
    cid=os.environ.get("GOOGLE_OAUTH_CLIENT_ID","").strip()
    secret=os.environ.get("GOOGLE_OAUTH_CLIENT_SECRET","").strip()
    redirect=os.environ.get("GOOGLE_OAUTH_REDIRECT_URI","").strip()
    if not cid or not secret or not redirect:
        raise HTTPException(status_code=503,detail="Google OAuth is not configured")
    return cid,secret,redirect

def _state(uid):
    nonce=os.urandom(18).hex(); raw=f"{uid}|{nonce}|{int(time.time())}"
    sig=hmac.new(os.environ.get("SOVEREIGN_KEY","").encode(),raw.encode(),hashlib.sha256).hexdigest()
    return urllib.parse.quote(raw+"|"+sig,safe="")

def _verify_state(value):
    try:
        raw=urllib.parse.unquote(value); uid,nonce,issued,sig=raw.rsplit("|",3)
        unsigned=f"{uid}|{nonce}|{issued}"
        if not hmac.compare_digest(sig,hmac.new(os.environ.get("SOVEREIGN_KEY","").encode(),unsigned.encode(),hashlib.sha256).hexdigest()): raise ValueError
        if time.time()-int(issued)>600: raise ValueError
        return uid
    except Exception as exc: raise HTTPException(status_code=400,detail="Invalid or expired Google OAuth state") from exc

@router.get("/oauth/start")
async def oauth_start(user=Depends(require_auth)):
    cid,_,redirect=_cfg()
    params={"client_id":cid,"redirect_uri":redirect,"response_type":"code","access_type":"offline",
            "prompt":"consent","include_granted_scopes":"true","scope":" ".join(SCOPES),"state":_state(user["uid"])}
    return {"authorization_url":AUTH_URL+"?"+urllib.parse.urlencode(params)}

@router.get("/oauth/callback")
async def oauth_callback(code:str,state:str):
    cid,secret,redirect=_cfg(); uid=_verify_state(state)
    async with httpx.AsyncClient(timeout=20) as client:
        res=await client.post(TOKEN_URL,data={"code":code,"client_id":cid,"client_secret":secret,"redirect_uri":redirect,"grant_type":"authorization_code"})
    if res.status_code>=400: raise HTTPException(status_code=502,detail="Google token exchange failed")
    token=res.json()
    token["scope"]=token.get("scope"," ".join(SCOPES))
    save_oauth(uid,token)
    return {"ok":True,"google_connected":True,"uid":uid,"scopes":token["scope"].split()}

@router.get("/status")
async def workspace_status(user=Depends(require_auth)):
    token=get_oauth(user["uid"])
    return {"connected":bool(token),"scopes":(token or {}).get("scope","").split(),
            "workspace_studio_triggers":list_triggers(user["uid"]),
            "push_devices":len(list_device_tokens(user["uid"]))}

@router.post("/push/device")
async def register_push(body:dict, user=Depends(require_auth)):
    token=str(body.get("token") or "").strip()
    if not token: raise HTTPException(status_code=400,detail="token required")
    save_device_token(user["uid"],token,str(body.get("platform") or "android"))
    return {"ok":True,"registered":True}

@router.delete("/push/device")
async def unregister_push(body:dict,user=Depends(require_auth)):
    token=str(body.get("token") or "").strip()
    if token: revoke_device_token(user["uid"],token)
    return {"ok":True}

@router.post("/studio/manage")
async def studio_manage(request:Request):
    event=await request.json(); workflow=event.get("workflow") or {}
    creation=workflow.get("triggerCreation"); deletion=workflow.get("triggerDeletion")
    # The add-on lifecycle callback is the source of trigger identity. The
    # callback itself does not grant Arkadia authority.
    if creation:
        trigger_id=creation.get("triggerId")
        notify=creation.get("notifyUri") or f"https://workspacestudio.googleapis.com/v1/triggers/{trigger_id}:fire"
        inputs=creation.get("inputs") or {}
        # Workspace Studio custom starter lifecycle does not carry Firebase UID
        # by contract, so the configured flow must include an Arkadia user_id
        # input or a pre-authorized owner mapping.
        uid=(inputs.get("arkadiaUserId") or {}).get("stringValues",[None])[0]
        if not uid: return {"ok":False,"error":"arkadiaUserId input required"}
        save_trigger(uid,trigger_id,notify,inputs)
        return {"ok":True,"triggerId":trigger_id}
    if deletion:
        trigger_id=deletion.get("triggerId")
        # deletion payload may omit owner; mark through supplied owner input if present
        uid=(deletion.get("inputs") or {}).get("arkadiaUserId",{}).get("stringValues",[None])[0]
        if uid and trigger_id: delete_trigger(uid,trigger_id)
        return {"ok":True,"deleted":trigger_id}
    return {"ok":True,"ignored":True}

class DeliveryRequest(BaseModel):
    event_id:str
    event_type:str
    subject:str
    claim:str=""
    severity:str="INFO"
    human_authority_required:bool=False
    task_delivery:bool=False
    keep_delivery:bool=True
    push_delivery:bool=True
    workspace_studio_delivery:bool=True

async def _access_token(uid):
    token=get_oauth(uid)
    if not token:
        raise RuntimeError("Google Workspace not connected")
    if token.get("refresh_token"):
        cid,secret,_=_cfg()
        async with httpx.AsyncClient(timeout=20) as client:
            r=await client.post(
                TOKEN_URL,
                data={
                    "client_id":cid,
                    "client_secret":secret,
                    "refresh_token":token["refresh_token"],
                    "grant_type":"refresh_token",
                },
            )
        if r.status_code>=400:
            raise RuntimeError("Google access-token refresh failed")
        fresh=r.json()
        fresh["refresh_token"]=token["refresh_token"]
        fresh["scope"]=token.get("scope"," ".join(SCOPES))
        save_oauth(uid,fresh)
        return fresh["access_token"]
    return token["access_token"]

async def _keep(uid,event):
    access=await _access_token(uid)
    if hasattr(access,"__await__"): access=await access
    body={"title":f"ARKANA // {event['event_type']} · {event['subject']}",
          "body":{"text":{"text":event.get("claim") or json.dumps(event,ensure_ascii=False)}}}
    async with httpx.AsyncClient(timeout=20) as client:
        r=await client.post("https://keep.googleapis.com/v1/notes",headers={"Authorization":f"Bearer {access}"},json=body)
    return {"status":"DELIVERED" if r.is_success else "FAILED","http_status":r.status_code,"remote_id":(r.json().get("name") if r.is_success else None)}

async def _tasks(uid,event):
    access=await _access_token(uid)
    body={"title":f"{'AUTH' if event.get('human_authority_required') else event['event_type']}: {event['subject']}",
          "notes":json.dumps(event,ensure_ascii=False)}
    async with httpx.AsyncClient(timeout=20) as client:
        r=await client.post("https://tasks.googleapis.com/tasks/v1/lists/@default/tasks",headers={"Authorization":f"Bearer {access}"},json=body)
    return {"status":"DELIVERED" if r.is_success else "FAILED","http_status":r.status_code,"remote_id":(r.json().get("id") if r.is_success else None)}

async def _studio(uid,event):
    access=await _access_token(uid)
    results=[]
    for trig in list_triggers(uid):
        if not trig.get("active"): continue
        uri=trig["notify_uri"]
        payload={"name":uri.rsplit("/",1)[-1].replace(":fire","") and uri.split("/triggers/")[-1].replace(":fire","") and uri.split("/triggers/")[-1].replace(":fire",""),
                 "requestId":event["event_id"],
                 "outputs":{"eventId":{"stringValues":[event["event_id"]]},"eventType":{"stringValues":[event["event_type"]]},"subject":{"stringValues":[event["subject"]]},"claim":{"stringValues":[event.get("claim","")]}, "severity":{"stringValues":[event.get("severity","INFO")]}}}
        async with httpx.AsyncClient(timeout=20) as client:
            r=await client.post(uri,headers={"Authorization":f"Bearer {access}"},json=payload)
        results.append({"trigger_id":trig.get("notify_uri"),"status":"DELIVERED" if r.is_success else "FAILED","http_status":r.status_code})
    return {"status":"DELIVERED" if results and all(x["status"]=="DELIVERED" for x in results) else ("SKIPPED" if not results else "FAILED"),"results":results}

async def _push(uid,event):
    try:
        from firebase_admin import messaging
        tokens=list_device_tokens(uid)
        if not tokens: return {"status":"SKIPPED","reason":"no registered device"}
        msg=messaging.MulticastMessage(
            tokens=tokens,
            notification=messaging.Notification(title="Arkana",body=(event.get("claim") or event["event_type"])[:180]),
            data={"event_id":event["event_id"],"event_type":event["event_type"],"subject":event["subject"],"severity":event.get("severity","INFO")},
        )
        resp=messaging.send_each_for_multicast(msg)
        return {"status":"DELIVERED" if resp.success_count else "FAILED","success_count":resp.success_count,"failure_count":resp.failure_count}
    except Exception as exc:
        return {"status":"FAILED","error":str(exc)[:500]}

async def deliver_event(uid,event):
    from weaver.enterprise_orchestration import EnterpriseOrchestrationStore
    store=EnterpriseOrchestrationStore()
    results={}
    if event.get("task_delivery"): results["tasks"]=await _tasks(uid,event)
    if event.get("keep_delivery"): results["keep"]=await _keep(uid,event)
    if event.get("workspace_studio_delivery"): results["workspace_studio"]=await _studio(uid,event)
    if event.get("push_delivery"): results["push"]=await _push(uid,event)
    for channel,result in results.items():
        existing=store.attention_delivery_ack(
            subject=uid,event_id=event["event_id"],channel=channel
        )
        if existing:
            result["status"]="ALREADY_ACKNOWLEDGED"
            result["evidence_id"]=existing.id
            continue
        ack=store.evidence(
            subject=uid,
            evidence_type="ATTENTION_DELIVERY_ACK",
            content_or_ref={
                "event_id":event["event_id"],
                "channel":channel,
                "delivery":result,
            },
            source_ref=f"attention:{event['event_id']}:{channel}",
        )
        result["evidence_id"]=ack.id
    return results

@router.post("/internal/deliver")
async def internal_deliver(request:Request):
    expected=os.environ.get("SOVEREIGN_KEY","").strip()
    supplied=request.headers.get("X-Arkadia-Sovereign-Key","")
    if not expected or not hmac.compare_digest(supplied,expected):
        raise HTTPException(status_code=403,detail="Sovereign delivery credential required")
    body=await request.json()
    uid=str(body.pop("user_id") or os.environ.get("ARKADIA_ATTENTION_OWNER_UID") or "").strip()
    if not uid: raise HTTPException(status_code=400,detail="user_id required")
    return {"ok":True,"event_id":body.get("event_id"),"deliveries":await deliver_event(uid,body)}

@router.post("/deliver")
async def deliver(body:DeliveryRequest,user=Depends(require_auth)):
    event=body.model_dump()
    return {"ok":True,"event_id":body.event_id,"deliveries":await deliver_event(user["uid"],event)}
