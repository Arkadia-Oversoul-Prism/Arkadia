import React,{useEffect,useMemo,useState} from 'react';
import {apiFetch} from '../../lib/apiClient';
import {useAuth} from '../../contexts/AuthContext';

type Candidate=Record<string,any>;
const LANES=['UNCONTACTED','CONTACTED','CONVERSATION','REQUIREMENT_CAPTURED','PRICE_CONFIRMED','BUYER_COMMITMENT','SUPPLIER_CONFIRMED','ECONOMICS_CLOSED','READY_TO_EXECUTE','EXECUTED','SETTLED'];

const fieldStyle:React.CSSProperties={width:'100%',padding:'10px 11px',borderRadius:10,border:'1px solid rgba(233,231,223,.10)',background:'rgba(255,255,255,.03)',color:'#E9E7DF',font:'12px Inter,system-ui,sans-serif'};
const card:React.CSSProperties={border:'1px solid rgba(233,231,223,.09)',background:'rgba(255,255,255,.025)',borderRadius:16,padding:14};

export default function SovereignFieldPage(){
 const {isSovereign}=useAuth();
 const [field,setField]=useState<any>(null);
 const [rows,setRows]=useState<Candidate[]>([]);
 const [busy,setBusy]=useState(true);
 const [error,setError]=useState('');
 const [prospect,setProspect]=useState('');
 const [location,setLocation]=useState('');
 const [commodity,setCommodity]=useState('');
 const [buyerType,setBuyerType]=useState('');
 const [status,setStatus]=useState('UNCONTACTED');

 const load=async()=>{
  setBusy(true);setError('');
  try{
   const r=await apiFetch('/solspire/enterprise/sovereign-field');
   const d=await r.json();
   if(!r.ok)throw new Error(d?.detail||'Sovereign field unavailable');
   setField(d.field);setRows(d.buyer_recon||[]);
  }catch(e:any){setError(e?.message||'Sovereign field unavailable')}finally{setBusy(false)}
 };
 useEffect(()=>{if(isSovereign)void load();else setBusy(false)},[isSovereign]);

 const grouped=useMemo(()=>LANES.map(lane=>({lane,items:rows.filter(r=>String(r.status||'UNCONTACTED')===lane)})).filter(g=>g.items.length),[rows]);

 const add=async()=>{
  if(!prospect.trim())return;
  setBusy(true);setError('');
  try{
   const r=await apiFetch('/solspire/enterprise/sovereign-field/buyer-recon',{method:'POST',body:JSON.stringify({
    prospect,location:location||'UNKNOWN',commodity:commodity||'UNKNOWN',buyer_type:buyerType||'UNKNOWN',status,
   })});
   const d=await r.json();if(!r.ok)throw new Error(d?.detail||'Candidate could not be created');
   setRows(v=>[d.candidate,...v]);setProspect('');setLocation('');setCommodity('');setBuyerType('');setStatus('UNCONTACTED');
  }catch(e:any){setError(e?.message||'Candidate could not be created')}finally{setBusy(false)}
 };

 const move=async(id:string,next:string)=>{
  try{
   const r=await apiFetch('/solspire/enterprise/sovereign-field/buyer-recon/'+encodeURIComponent(id),{method:'PATCH',body:JSON.stringify({status:next})});
   const d=await r.json();if(!r.ok)throw new Error(d?.detail||'Status update failed');
   setRows(v=>v.map(x=>x.candidate_id===id?d.candidate:x));
  }catch(e:any){setError(e?.message||'Status update failed')}
 };

 if(!isSovereign)return <section style={{...card,maxWidth:760,margin:'6vh auto'}}><div style={{color:'#C9A84C',fontSize:10,letterSpacing:'.18em'}}>SOVEREIGN FIELD</div><h2 style={{fontWeight:400}}>This field is not available to this identity.</h2><p style={{color:'rgba(233,231,223,.52)',lineHeight:1.6}}>Access follows the existing sovereign identity boundary. No client-side flag grants entry.</p></section>;

 return <main data-testid="sovereign-field" style={{display:'grid',gap:16,paddingBottom:100}}>
  <header style={{...card,padding:18}}>
   <div style={{color:'#B08DE8',fontSize:9,letterSpacing:'.22em'}}>SOVEREIGN ACCESS / PERSISTENT FIELD</div>
   <h1 style={{margin:'8px 0 6px',font:'500 clamp(28px,6vw,48px)/1.05 Georgia,serif'}}>The hidden operating field.</h1>
   <p style={{margin:0,color:'rgba(233,231,223,.54)',maxWidth:760,lineHeight:1.6}}>A durable session-independent surface bound to the sovereign identity. It instantiates from the same canonical subject on every session. The dashboard is a projection, not an authority.</p>
   <div style={{marginTop:12,font:'9px ui-monospace,monospace',color:'rgba(233,231,223,.38)'}}>FIELD {field?.field_id||'—'} · WORKSPACE {field?.workspace_ref||'—'} · SCHEMA {field?.schema_version||'—'}</div>
  </header>

  <section style={{...card,display:'grid',gap:10}}>
   <div style={{fontSize:9,letterSpacing:'.18em',color:'#00D4AA'}}>BUYER RECON</div>
   <div style={{color:'rgba(233,231,223,.56)',fontSize:11,lineHeight:1.55}}>This is the demand-discovery layer upstream of Commercial Confirmation. It records evidence progressively. Unknown remains unknown until observed.</div>
   <div style={{display:'grid',gridTemplateColumns:'repeat(auto-fit,minmax(150px,1fr))',gap:8}}>
    <input style={fieldStyle} value={prospect} onChange={e=>setProspect(e.target.value)} placeholder="Buyer / prospect"/>
    <input style={fieldStyle} value={location} onChange={e=>setLocation(e.target.value)} placeholder="Location"/>
    <input style={fieldStyle} value={commodity} onChange={e=>setCommodity(e.target.value)} placeholder="Commodity"/>
    <input style={fieldStyle} value={buyerType} onChange={e=>setBuyerType(e.target.value)} placeholder="Buyer type"/>
    <select style={fieldStyle} value={status} onChange={e=>setStatus(e.target.value)}>{LANES.map(x=><option key={x}>{x}</option>)}</select>
    <button onClick={()=>void add()} disabled={busy||!prospect.trim()} style={{...fieldStyle,cursor:'pointer',borderColor:'rgba(201,168,76,.35)',background:'rgba(201,168,76,.08)'}}>＋ Add prospect</button>
   </div>
  </section>

  {error&&<div role="alert" style={{...card,color:'#E9E7DF',borderColor:'rgba(255,100,100,.25)'}}>{error}</div>}
  {busy&&!rows.length?<div style={{color:'rgba(233,231,223,.48)',fontSize:12}}>Resolving the persistent field…</div>:null}
  {!busy&&!rows.length?<div style={{...card,color:'rgba(233,231,223,.48)',lineHeight:1.6}}>No buyer claims are recorded yet. The field itself is live and persistent; the first row becomes evidence only when a real prospect is entered.</div>:null}

  <section style={{display:'grid',gap:10}}>
   {grouped.map(group=><div key={group.lane} style={{...card}}>
    <div style={{display:'flex',justifyContent:'space-between',gap:10,marginBottom:10}}><strong style={{fontSize:10,letterSpacing:'.12em'}}>{group.lane}</strong><span style={{fontSize:10,color:'rgba(233,231,223,.38)'}}>{group.items.length}</span></div>
    <div style={{display:'grid',gap:8}}>
     {group.items.map(item=><article key={item.candidate_id} style={{border:'1px solid rgba(233,231,223,.07)',borderRadius:12,padding:11}}>
      <div style={{fontSize:14}}>{item.prospect}</div>
      <div style={{marginTop:4,color:'rgba(233,231,223,.45)',fontSize:10}}>{item.location} · {item.commodity} · {item.buyer_type}</div>
      <div style={{display:'flex',gap:6,marginTop:9,flexWrap:'wrap'}}>
       <span style={{padding:'4px 7px',borderRadius:8,background:'rgba(255,255,255,.04)',fontSize:9}}>DEMAND · {item.estimated_demand||'UNKNOWN'}</span>
       <span style={{padding:'4px 7px',borderRadius:8,background:'rgba(255,255,255,.04)',fontSize:9}}>PRICE · {item.buyer_price||'UNKNOWN'}</span>
       <span style={{padding:'4px 7px',borderRadius:8,background:'rgba(255,255,255,.04)',fontSize:9}}>EVIDENCE · {item.evidence_status||'UNKNOWN'}</span>
      </div>
      <select aria-label={'Move '+item.prospect} style={{...fieldStyle,marginTop:9}} value={item.status} onChange={e=>void move(item.candidate_id,e.target.value)}>{LANES.map(x=><option key={x}>{x}</option>)}</select>
     </article>)}
    </div>
   </div>)}
  </section>
 </main>;
}
