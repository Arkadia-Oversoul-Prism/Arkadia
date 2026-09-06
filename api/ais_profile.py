"""A.I.S identity seed and longitudinal node spine."""
from __future__ import annotations
import hashlib, json, os, re
from datetime import datetime, timezone
from typing import Any
from fastapi import APIRouter, Depends, HTTPException, Request
from api.auth import _profiles_dir, load_user_profile_store, require_auth
router=APIRouter(); _KEY='ais_capability_portfolio'; _SPINE_KEY='identity_spine'; _ALLOWED_TYPES=('diagnostic_seed','portfolio')
_RELATIONAL_DIMENSIONS=('identity_coherence','context_continuity','personalization_fidelity','agency_preservation','trust_calibration','responsiveness','developmental_coherence','relational_alignment')
def _profile_path(uid:str)->str:return os.path.join(_profiles_dir(),f'{uid}.json')
def _write_store(uid:str,stored:dict[str,Any])->None:
 os.makedirs(_profiles_dir(),exist_ok=True)
 with open(_profile_path(uid),'w',encoding='utf-8') as handle: json.dump(stored,handle,indent=2,ensure_ascii=False)
def _save_projection(uid:str,payload:dict[str,Any])->dict[str,Any]:
 stored=load_user_profile_store(uid);stored[_KEY]=payload;_write_store(uid,stored);return payload
def _seed_from_ais(stored:dict[str,Any])->dict[str,Any]|None:
 projection=stored.get(_KEY)
 if not isinstance(projection,dict):return None
 profile=projection.get('profile');return profile if isinstance(profile,dict) else None
def _slug(value:str)->str:return re.sub(r'[^a-z0-9]+','-',value.lower()).strip('-')[:24]
def _seed_material(uid:str,seed:dict[str,Any]|None)->str:return json.dumps({'uid':uid,'seed':seed or {}},sort_keys=True,ensure_ascii=False)
def _sigil_for(uid:str,seed:dict[str,Any]|None)->str:
 sigils=('◈','✦','⬡','◇','✧','◉','⌬','⟐','✺','❖');digest=hashlib.sha256(_seed_material(uid,seed).encode('utf-8')).digest();return sigils[digest[0]%len(sigils)]
def _username_for(user:dict[str,Any],stored:dict[str,Any],uid:str)->str:
 existing=user.get('username') or stored.get('username')
 if isinstance(existing,str) and existing.strip():return _slug(existing) or f'node-{uid[:8]}'
 base=_slug((stored.get('display_name') or user.get('display_name') or 'node').strip()) or 'node';return f'{base}-{uid[:4].lower()}'
def _build_identity_spine(uid:str,user:dict[str,Any],stored:dict[str,Any])->dict[str,Any]:
 seed=_seed_from_ais(stored);existing=stored.get(_SPINE_KEY) if isinstance(stored.get(_SPINE_KEY),dict) else {};now=datetime.now(timezone.utc).isoformat();preferred=stored.get('display_name') or user.get('display_name') or '';username=_username_for(user,stored,uid);sigil=_sigil_for(uid,seed)
 identity={'uid':uid,'canonical_name':user.get('display_name') or preferred,'preferred_name':preferred or user.get('display_name') or 'Node','username':username,'role':user.get('role') or 'Authenticated Node','role_sigil':user.get('role_sigil') or sigil,'ims_id':user.get('ims_id')}
 baseline={'identity':seed.get('identity','') if seed else '','capabilities':seed.get('capabilities',[]) if seed else [],'builds':seed.get('builds','') if seed else '','evidence':seed.get('evidence','') if seed else '','projects':seed.get('projects','') if seed else '','offer':seed.get('offer','') if seed else '','credentials':seed.get('credentials','') if seed else '','growth':seed.get('growth',[]) if seed else [],'mind':seed.get('mind','') if seed else '','creating':seed.get('creating','') if seed else '','values':seed.get('values','') if seed else '','becoming':seed.get('becoming','') if seed else ''}
 old_cap=existing.get('capability') if isinstance(existing.get('capability'),dict) else {};capability={'baseline':baseline,'evidence_count':int(old_cap.get('evidence_count',0) or 0),'development_events':old_cap.get('development_events',[]),'last_assessed_at':old_cap.get('last_assessed_at')}
 old_rel=existing.get('relationship') if isinstance(existing.get('relationship'),dict) else {};relationship={'preferred_ai_role':old_rel.get('preferred_ai_role') or (seed.get('preferredAiRole') if seed else None),'communication_preference':old_rel.get('communication_preference') or None,'collaboration_preference':old_rel.get('collaboration_preference') or None}
 old_index=existing.get('relational_index') if isinstance(existing.get('relational_index'),dict) else {};old_dims=old_index.get('dimensions') if isinstance(old_index.get('dimensions'),dict) else {};relational={'version':1,'status':old_index.get('status') or ('seeded' if seed else 'awaiting_seed'),'score':old_index.get('score'),'confidence':old_index.get('confidence',0),'dimensions':{k:old_dims.get(k) for k in _RELATIONAL_DIMENSIONS},'observations':old_index.get('observations',[]),'last_evaluated_at':old_index.get('last_evaluated_at')}
 old_symbolic=existing.get('symbolic') if isinstance(existing.get('symbolic'),dict) else {};seed_phrase=old_symbolic.get('seed_phrase') or (seed.get('seedPhrase') if seed else None);symbolic={'seed_phrase':seed_phrase,'seed_symbols':old_symbolic.get('seed_symbols') or ([seed_phrase] if seed_phrase else []),'sigil_seed':old_symbolic.get('sigil_seed') or sigil,'resonance_signature':old_symbolic.get('resonance_signature') or None}
 return {'version':1,'identity':identity,'seed':{'created_at':seed.get('completedAt') if seed else None,'sigil':symbolic['sigil_seed'],'phrase':symbolic['seed_phrase'],'symbols':symbolic['seed_symbols'],'source':'A.I.S' if seed else None},'orientation':{'current_intent':seed.get('identity','') if seed else '','direction':seed.get('becoming') or (' · '.join(seed.get('growth',[])) if seed else ''),'interests':seed.get('capabilities',[]) if seed else [],'values':seed.get('values','') if seed else ''},'capability':capability,'relationship':relationship,'relational_index':relational,'symbolic':symbolic,'continuity':{'projections':['NovaNet','ReasoMate','Personal Codex','Personal EchoField','Spiral Grove','IMS','Encyclopedia Galactica'],'ims':user.get('ims_id'),'encyclopedia':'shared node continuity','codex':'canonical longitudinal context','echofield':'living identity visualization'},'provenance':{'ais_version':seed.get('version') if seed else None,'seed_created_at':seed.get('completedAt') if seed else None,'last_reconciled_at':now,'schema_version':2}}
def _save_spine(uid:str,spine:dict[str,Any])->dict[str,Any]:
 stored=load_user_profile_store(uid);stored[_SPINE_KEY]=spine;_write_store(uid,stored);return spine
@router.get('/api/me/ais-profile')
async def get_ais_profile(user:dict=Depends(require_auth)):
 stored=load_user_profile_store(user['uid']);return {'profile':stored.get(_KEY)}
@router.patch('/api/me/ais-profile')
async def patch_ais_profile(request:Request,user:dict=Depends(require_auth)):
 try:body=await request.json()
 except Exception as exc:raise HTTPException(status_code=400,detail='Invalid JSON body') from exc
 if not isinstance(body,dict):raise HTTPException(status_code=400,detail='Invalid body')
 kind=body.get('kind');profile=body.get('profile')
 if kind not in _ALLOWED_TYPES or not isinstance(profile,dict):raise HTTPException(status_code=400,detail='Expected kind and profile')
 if profile.get('version')!=1:raise HTTPException(status_code=400,detail='Unsupported A.I.S profile version')
 payload={'kind':kind,'profile':profile};_save_projection(user['uid'],payload);spine=_build_identity_spine(user['uid'],user,load_user_profile_store(user['uid']));_save_spine(user['uid'],spine);return {'profile':payload,'identity_spine':spine}
@router.get('/api/me/identity-spine')
async def get_identity_spine(user:dict=Depends(require_auth)):
 uid=user['uid'];stored=load_user_profile_store(uid);spine=_build_identity_spine(uid,user,stored);_save_spine(uid,spine);return {'identity_spine':spine}
@router.post('/api/me/identity-spine/development')
async def add_development_event(request:Request,user:dict=Depends(require_auth)):
 try:body=await request.json()
 except Exception as exc:raise HTTPException(status_code=400,detail='Invalid JSON body') from exc
 if not isinstance(body,dict) or not str(body.get('type','')).strip():raise HTTPException(status_code=400,detail='Expected development event type')
 stored=load_user_profile_store(user['uid']);spine=_build_identity_spine(user['uid'],user,stored);event={'type':str(body['type'])[:80],'summary':str(body.get('summary',''))[:500],'source':str(body.get('source','arkadia'))[:80],'recorded_at':datetime.now(timezone.utc).isoformat()};events=spine['capability'].setdefault('development_events',[])
 if len(events)>=500:events.pop(0)
 events.append(event);spine['capability']['evidence_count']=int(spine['capability'].get('evidence_count',0))+1;spine['capability']['last_assessed_at']=event['recorded_at'];_save_spine(user['uid'],spine);return {'identity_spine':spine,'event':event}
@router.post('/api/me/identity-spine/relational-observation')
async def add_relational_observation(request:Request,user:dict=Depends(require_auth)):
 try:body=await request.json()
 except Exception as exc:raise HTTPException(status_code=400,detail='Invalid JSON body') from exc
 if not isinstance(body,dict):raise HTTPException(status_code=400,detail='Invalid body')
 stored=load_user_profile_store(user['uid']);spine=_build_identity_spine(user['uid'],user,stored);ri=spine['relational_index'];dimensions=body.get('dimensions') if isinstance(body.get('dimensions'),dict) else {}
 for key in _RELATIONAL_DIMENSIONS:
  if key in dimensions:
   try:value=max(0,min(100,int(dimensions[key])))
   except (TypeError,ValueError):continue
   ri['dimensions'][key]=value
 observation=str(body.get('observation','')).strip()[:500]
 if observation:
  observations=ri.setdefault('observations',[])
  if len(observations)>=200:observations.pop(0)
  observations.append(observation)
 ri['status']='observed' if any(v is not None for v in ri['dimensions'].values()) else 'seeded';known=[v for v in ri['dimensions'].values() if isinstance(v,int)];ri['score']=round(sum(known)/len(known)) if known else None;ri['confidence']=round((len(known)/len(_RELATIONAL_DIMENSIONS))*100);ri['last_evaluated_at']=datetime.now(timezone.utc).isoformat() if known else ri.get('last_evaluated_at');_save_spine(user['uid'],spine);return {'identity_spine':spine}
