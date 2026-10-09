import React, { useEffect, useState } from 'react';
import { apiFetch } from '../lib/apiClient';
import { useAuth } from '../contexts/AuthContext';

type Entry = {
  id:string; prospect:string; location:string; commodity:string; quantity:string; buyer_price:string;
  delivery_point:string; delivery_window:string; supplier:string; landed_cost:string;
  evidence_status:string; why_this_prospect:string; status:string;
};

const columns = ['UNCONTACTED','CONTACTED','CONVERSATION','REQUIREMENT_CAPTURED','PRICE_CONFIRMED','BUYER_COMMITMENT','SUPPLIER_CONFIRMED','ECONOMICS_CLOSED','READY_TO_EXECUTE','EXECUTED','SETTLED'];

export default function OpportunityRadarPage(){
  const [entries,setEntries]=useState<Entry[]>([]);
  const [loading,setLoading]=useState(true);
  const [error,setError]=useState('');
  const [prospect,setProspect]=useState('');
  const [location,setLocation]=useState('');
  const [commodity,setCommodity]=useState('');
  const { isSovereign } = useAuth();
  const [scanBusy,setScanBusy]=useState(false);
  const [scanMessage,setScanMessage]=useState('');
  const [scanResult,setScanResult]=useState<any>(null);
  const [sourceRuns,setSourceRuns]=useState<Array<{source_id:string;last_run?:string;status?:string;item_count?:number;error?:string|null}>>([]);

  async function loadScanStatus(){
    try {
      const r=await apiFetch('/api/economic-seams/status');
      const data=await r.json();
      if(!r.ok) throw new Error(data?.detail||r.statusText);
      setSourceRuns(Array.isArray(data?.runs)?data.runs:[]);
    } catch(e:any) { setScanMessage(String(e.message||e)); }
  }

  async function runEconomicScan(){
    if(!isSovereign || scanBusy) return;
    setScanBusy(true); setScanMessage('Scan requested. Waiting for provider results…'); setScanResult(null);
    try {
      const r=await apiFetch('/api/economic-seams/scan',{method:'POST'});
      const data=await r.json();
      if(!r.ok) throw new Error(data?.detail||r.statusText);
      setScanResult(data);
      setScanMessage('Scan request completed. Source results below are reported by the backend; persisted records still require verification.');
      await loadScanStatus();
    } catch(e:any) { setScanMessage(String(e.message||e)); }
    finally { setScanBusy(false); }
  }

  async function load(){
    setLoading(true);
    try {
      const r=await apiFetch('/solspire/buyer-recon');
      const data=await r.json();
      if(!r.ok) throw new Error(data?.detail||r.statusText);
      setEntries(data.entries||[]);
    } catch(e:any){ setError(String(e.message||e)); }
    finally{ setLoading(false); }
  }
  useEffect(()=>{ load(); void loadScanStatus(); },[]);

  async function add(){
    if(!prospect.trim()) return;
    const r=await apiFetch('/solspire/buyer-recon/entries',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({prospect,location,commodity,status:'UNCONTACTED',evidence_status:'NONE'})});
    const data=await r.json();
    if(!r.ok){setError(data?.detail||r.statusText);return;}
    setEntries(prev=>[data.entry,...prev]); setProspect(''); setLocation(''); setCommodity('');
  }

  async function advance(entry:Entry){
    const i=columns.indexOf(entry.status);
    if(i<0 || i>=columns.length-1) return;
    const r=await apiFetch('/solspire/buyer-recon/entries/'+entry.id,{method:'PATCH',headers:{'Content-Type':'application/json'},body:JSON.stringify({status:columns[i+1]})});
    const data=await r.json();
    if(!r.ok){setError(data?.detail||r.statusText);return;}
    setEntries(prev=>prev.map(x=>x.id===entry.id?data.entry:x));
  }

  return <div style={{display:'grid',gap:16}} data-testid="eden-buyer-recon-board">
    <section className="solspire-object" style={{cursor:'default'}}>
      <div className="solspire-kicker">PRIVATE FIELD · EDEN DEMAND ACQUISITION</div>
      <h2 className="solspire-title">Buyer Recon Board</h2>
      <p className="solspire-object-summary">Persistent in the authenticated SolSpire workspace. Every session resolves the same board from sovereign identity. Reconnaissance does not authorize execution.</p>
      <div style={{display:'flex',gap:8,flexWrap:'wrap',marginTop:12}}>
        <input value={prospect} onChange={e=>setProspect(e.target.value)} placeholder="Buyer / prospect" style={input}/>
        <input value={location} onChange={e=>setLocation(e.target.value)} placeholder="Location" style={input}/>
        <input value={commodity} onChange={e=>setCommodity(e.target.value)} placeholder="Commodity" style={input}/>
        <button onClick={add} style={button}>ADD PROSPECT</button>
      </div>
      {error&&<div style={{marginTop:10,color:'#C84848',fontSize:11}}>{error}</div>}
    </section>
    {loading ? <div className="solspire-object-summary">Loading persistent field…</div> :
      entries.length===0 ? <section className="solspire-object" style={{cursor:'default'}}><div className="solspire-kicker">EMPTY BY DESIGN</div><h3 className="solspire-title">No buyer evidence captured yet.</h3><p className="solspire-object-summary">The board is live and persistent. Nothing is promoted into the transaction system until evidence exists.</p></section> :
      <section style={{display:'grid',gap:10}}>{entries.map(e=><article key={e.id} className="solspire-object" style={{cursor:'default'}}>
        <div style={{display:'flex',justifyContent:'space-between',gap:12,alignItems:'start'}}>
          <div><div className="solspire-kicker">{e.status} · {e.evidence_status}</div><h3 className="solspire-title">{e.prospect}</h3></div>
          <button onClick={()=>advance(e)} disabled={e.status==='SETTLED'} style={button}>{e.status==='SETTLED'?'CLOSED':'ADVANCE'}</button>
        </div>
        <div style={{display:'grid',gridTemplateColumns:'repeat(auto-fit,minmax(140px,1fr))',gap:8,fontSize:11,color:'rgba(232,232,232,.58)',marginTop:8}}>
          <div><b>Location:</b> {e.location||'UNKNOWN'}</div><div><b>Commodity:</b> {e.commodity||'UNKNOWN'}</div>
          <div><b>Quantity:</b> {e.quantity}</div><div><b>Buyer price:</b> {e.buyer_price}</div>
          <div><b>Delivery:</b> {e.delivery_point}</div><div><b>Window:</b> {e.delivery_window}</div>
          <div><b>Supplier:</b> {e.supplier}</div><div><b>Landed:</b> {e.landed_cost}</div>
        </div>
        {e.why_this_prospect&&<p className="solspire-object-summary" style={{marginTop:10}}>{e.why_this_prospect}</p>}
      </article>)}</section>}
  </div>
}
const input:React.CSSProperties={flex:'1 1 160px',padding:'9px 11px',background:'rgba(0,0,0,.3)',border:'1px solid rgba(0,212,170,.18)',borderRadius:7,color:'#D4DFE8',fontSize:12};
const button:React.CSSProperties={padding:'8px 12px',background:'rgba(0,212,170,.08)',border:'1px solid rgba(0,212,170,.28)',borderRadius:7,color:'#00D4AA',cursor:'pointer',fontSize:10,letterSpacing:'.1em'};
