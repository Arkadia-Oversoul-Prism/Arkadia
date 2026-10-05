import React, { useEffect, useMemo, useState } from 'react';
import { apiFetch } from '../../lib/apiClient';
import type { Project } from '../../pages/ProjectDashboard';

type Entry = {
  id:string; prospect:string; location:string; buyer_type:string; contact_route:string;
  commodity:string; estimated_demand:string; procurement_frequency:string; decision_maker:string;
  current_price:string; quantity:string; specification:string; delivery_point:string;
  delivery_window:string; payment_terms:string; supplier:string; source_price:string;
  available_quantity:string; logistics_quote:string; packaging_qc_cost:string; landed_cost:string;
  buyer_price:string; expected_gross_margin:string; capital_required:string;
  evidence_status:string; why_this_prospect:string; status:string; notes:string;
};

const columns = ['UNCONTACTED','CONTACTED','CONVERSATION','REQUIREMENT_CAPTURED','PRICE_CONFIRMED','BUYER_COMMITMENT','SUPPLIER_CONFIRMED','ECONOMICS_CLOSED','READY_TO_EXECUTE','EXECUTED','SETTLED'];

const input:React.CSSProperties={flex:'1 1 160px',padding:'9px 11px',background:'rgba(0,0,0,.3)',border:'1px solid rgba(0,212,170,.18)',borderRadius:7,color:'#D4DFE8',fontSize:12};
const button:React.CSSProperties={padding:'8px 12px',background:'rgba(0,212,170,.08)',border:'1px solid rgba(0,212,170,.28)',borderRadius:7,color:'#00D4AA',cursor:'pointer',fontSize:10,letterSpacing:'.1em'};

export default function ProjectOpportunityRadar({project}:{project:Project}) {
  const [entries,setEntries]=useState<Entry[]>([]);
  const [loading,setLoading]=useState(true);
  const [error,setError]=useState('');
  const [prospect,setProspect]=useState('');
  const [location,setLocation]=useState('');
  const [commodity,setCommodity]=useState('');
  const [buyerType,setBuyerType]=useState('');
  const [contact,setContact]=useState('');

  const base = `/solspire/buyer-recon/projects/${project.id}`;

  async function load(){
    setLoading(true); setError('');
    try {
      const r=await apiFetch(base);
      const data=await r.json();
      if(!r.ok) throw new Error(data?.detail||r.statusText);
      setEntries(data.entries||[]);
    } catch(e:any){ setError(String(e.message||e)); }
    finally{ setLoading(false); }
  }
  useEffect(()=>{void load();},[project.id]);

  async function add(){
    if(!prospect.trim()) return;
    const r=await apiFetch(`${base}/entries`,{
      method:'POST',headers:{'Content-Type':'application/json'},
      body:JSON.stringify({prospect,location,commodity,buyer_type:buyerType,contact_route:contact,status:'UNCONTACTED',evidence_status:'NONE'})
    });
    const data=await r.json();
    if(!r.ok){setError(data?.detail||r.statusText);return;}
    setEntries(prev=>[data.entry,...prev]);
    setProspect('');setLocation('');setCommodity('');setBuyerType('');setContact('');
  }

  async function advance(entry:Entry){
    const i=columns.indexOf(entry.status);
    if(i<0||i>=columns.length-1)return;
    const r=await apiFetch(`${base}/entries/${entry.id}`,{
      method:'PATCH',headers:{'Content-Type':'application/json'},
      body:JSON.stringify({status:columns[i+1]})
    });
    const data=await r.json();
    if(!r.ok){setError(data?.detail||r.statusText);return;}
    setEntries(prev=>prev.map(x=>x.id===entry.id?data.entry:x));
  }

  const counts=useMemo(()=>columns.reduce((a,c)=>(a[c]=entries.filter(e=>e.status===c).length,a),{} as Record<string,number>),[entries]);
  const actionable=entries.filter(e=>['BUYER_COMMITMENT','SUPPLIER_CONFIRMED','ECONOMICS_CLOSED','READY_TO_EXECUTE'].includes(e.status)).length;

  return <div style={{display:'grid',gap:16}} data-testid="project-opportunity-radar">
    <section className="solspire-object" style={{cursor:'default'}}>
      <div className="solspire-kicker">PROJECT FIELD · OPPORTUNITY RADAR</div>
      <h2 className="solspire-title">{project.name}</h2>
      <p className="solspire-object-summary">A project-scoped demand → supply → transaction surface. Reconnaissance is persistent, evidence-bound and does not authorize spending or execution.</p>
      <div style={{display:'grid',gridTemplateColumns:'repeat(auto-fit,minmax(100px,1fr))',gap:8,marginTop:14}}>
        <Metric label="Prospects" value={entries.length}/>
        <Metric label="Conversations" value={counts.CONVERSATION||0}/>
        <Metric label="Requirements" value={counts.REQUIREMENT_CAPTURED||0}/>
        <Metric label="Actionable" value={actionable}/>
      </div>
    </section>

    <section className="solspire-object" style={{cursor:'default'}}>
      <div className="solspire-kicker">CAPTURE DEMAND</div>
      <div style={{display:'flex',gap:8,flexWrap:'wrap',marginTop:10}}>
        <input value={prospect} onChange={e=>setProspect(e.target.value)} placeholder="Buyer / prospect" style={input}/>
        <input value={buyerType} onChange={e=>setBuyerType(e.target.value)} placeholder="Buyer type" style={input}/>
        <input value={contact} onChange={e=>setContact(e.target.value)} placeholder="Contact route" style={input}/>
        <input value={location} onChange={e=>setLocation(e.target.value)} placeholder="Location" style={input}/>
        <input value={commodity} onChange={e=>setCommodity(e.target.value)} placeholder="Commodity" style={input}/>
        <button onClick={add} disabled={!prospect.trim()} style={{...button,opacity:prospect.trim()?1:.45}}>ADD PROSPECT</button>
      </div>
      {error&&<div style={{marginTop:10,color:'#C84848',fontSize:11}}>{error}</div>}
    </section>

    <section style={{display:'grid',gridTemplateColumns:'repeat(auto-fit,minmax(180px,1fr))',gap:8}}>
      {columns.map(c=><div key={c} style={{padding:'8px 10px',border:'1px solid rgba(255,255,255,.06)',borderRadius:8,background:'rgba(10,11,20,.42)'}}>
        <div style={{fontSize:8,letterSpacing:'.12em',color:'rgba(212,223,232,.38)'}}>{c.replaceAll('_',' ')}</div>
        <strong style={{fontSize:16,color:c==='READY_TO_EXECUTE'?'#C9A84C':'#00D4AA'}}>{counts[c]||0}</strong>
      </div>)}
    </section>

    {loading ? <div className="solspire-object-summary">Loading project opportunity field…</div> :
      entries.length===0 ? <section className="solspire-object" style={{cursor:'default'}}><div className="solspire-kicker">EMPTY BY DESIGN</div><h3 className="solspire-title">No buyer evidence captured yet.</h3><p className="solspire-object-summary">Add a prospect or import one from the Economic Seam Engine. Nothing becomes executable without evidence and human authorization.</p></section> :
      <section style={{display:'grid',gap:10}}>{entries.map(e=><article key={e.id} className="solspire-object" style={{cursor:'default'}}>
        <div style={{display:'flex',justifyContent:'space-between',gap:12,alignItems:'start'}}>
          <div><div className="solspire-kicker">{e.status} · {e.evidence_status}</div><h3 className="solspire-title">{e.prospect}</h3></div>
          <button onClick={()=>advance(e)} disabled={e.status==='SETTLED'} style={button}>{e.status==='SETTLED'?'CLOSED':'ADVANCE'}</button>
        </div>
        <div style={{display:'grid',gridTemplateColumns:'repeat(auto-fit,minmax(145px,1fr))',gap:8,fontSize:11,color:'rgba(232,232,232,.58)',marginTop:8}}>
          <div><b>Type:</b> {e.buyer_type||'UNKNOWN'}</div><div><b>Contact:</b> {e.contact_route||'UNKNOWN'}</div>
          <div><b>Location:</b> {e.location||'UNKNOWN'}</div><div><b>Commodity:</b> {e.commodity||'UNKNOWN'}</div>
          <div><b>Quantity:</b> {e.quantity||'UNKNOWN'}</div><div><b>Buyer price:</b> {e.buyer_price||'UNKNOWN'}</div>
          <div><b>Delivery:</b> {e.delivery_point||'UNKNOWN'}</div><div><b>Window:</b> {e.delivery_window||'UNKNOWN'}</div>
          <div><b>Supplier:</b> {e.supplier||'UNKNOWN'}</div><div><b>Landed:</b> {e.landed_cost||'UNKNOWN'}</div>
          <div><b>Capital:</b> {e.capital_required||'UNKNOWN'}</div><div><b>Payment:</b> {e.payment_terms||'UNKNOWN'}</div>
        </div>
        {e.why_this_prospect&&<p className="solspire-object-summary" style={{marginTop:10}}>{e.why_this_prospect}</p>}
      </article>)}</section>}
  </div>;
}

function Metric({label,value}:{label:string;value:number}) {
  return <div style={{padding:'10px 12px',border:'1px solid rgba(0,212,170,.12)',borderRadius:8}}>
    <div style={{fontSize:8,letterSpacing:'.16em',color:'rgba(212,223,232,.38)'}}>{label.toUpperCase()}</div>
    <strong style={{fontSize:18,color:'#D4DFE8'}}>{value}</strong>
  </div>;
}
