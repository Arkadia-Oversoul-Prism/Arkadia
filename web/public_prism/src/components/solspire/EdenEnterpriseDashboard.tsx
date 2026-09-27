import { useCallback, useEffect, useMemo, useState } from 'react';
import { apiFetch } from '../../lib/apiClient';

type Cell = { label: string; value: unknown; epistemic_status?: string; source?: string | null };
type Dashboard = {
  product: { name: string; surface: string; tier: string; role: string; authority_effect: string };
  commercial: Cell[];
  money: Cell[];
  operations: {
    workstreams: Array<{ slug: string; name: string; budget: number; status: string }>;
    week1_tasks: Array<{ task_id: string; day: string; owner_role: string; title: string; status: string }>;
  };
  transaction: Cell[];
  critical_path: Cell[];
  evidence: Record<string, unknown>;
  truthfulness: { rule: string; unknown_policy: string };
};

const money = (n: number) => `₦${n.toLocaleString('en-NG')}`;

function Status({ status }: { status?: string }) {
  return <span style={{fontSize:10,letterSpacing:'.08em',padding:'4px 7px',borderRadius:999,border:'1px solid rgba(201,168,76,.24)',color:'rgba(233,231,223,.62)'}}>{status || 'UNKNOWN'}</span>;
}

function CellCard({ cell }: { cell: Cell }) {
  const unknown = cell.epistemic_status === 'UNKNOWN' || cell.value === 'UNKNOWN';
  return <article style={{padding:'14px 15px',borderRadius:14,border:'1px solid rgba(233,231,223,.09)',background:'rgba(255,255,255,.025)'}}>
    <div style={{fontSize:10,textTransform:'uppercase',letterSpacing:'.09em',color:'rgba(233,231,223,.42)'}}>{cell.label}</div>
    <div style={{fontSize:18,fontWeight:650,marginTop:7,color:unknown?'rgba(233,231,223,.38)':'#e9e7df'}}>{typeof cell.value === 'number' ? money(cell.value) : String(cell.value ?? 'UNKNOWN')}</div>
    <div style={{fontSize:10,marginTop:7,color:'rgba(233,231,223,.32)'}}>{unknown ? 'No governed source recorded' : (cell.source || cell.epistemic_status || 'RECORDED')}</div>
  </article>;
}

export default function EdenEnterpriseDashboard() {
  const [dashboard,setDashboard]=useState<Dashboard|null>(null);
  const [loading,setLoading]=useState(true);
  const [bootstrapping,setBootstrapping]=useState(false);
  const [error,setError]=useState<string|null>(null);

  const load = useCallback(async () => {
    setLoading(true); setError(null);
    try {
      const r = await apiFetch('/solspire/enterprise/eden/dashboard', { headers: {} });
      const d = await r.json();
      if (!r.ok) {
        if (r.status === 404) { setDashboard(null); return; }
        throw new Error(d?.detail || `Enterprise dashboard unavailable (${r.status})`);
      }
      setDashboard(d);
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Unable to load Eden enterprise workspace');
    } finally { setLoading(false); }
  }, []);

  useEffect(() => { void load(); }, [load]);

  const bootstrap = async () => {
    setBootstrapping(true); setError(null);
    try {
      const r = await apiFetch('/solspire/enterprise/eden/bootstrap', { method:'POST', headers:{'Content-Type':'application/json'}, body:'{}' });
      const d = await r.json();
      if (!r.ok) throw new Error(d?.detail || `Enterprise bootstrap failed (${r.status})`);
      await load();
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Unable to initialize Eden enterprise workspace');
    } finally { setBootstrapping(false); }
  };

  const total = useMemo(() => dashboard?.operations.workstreams.reduce((sum,w)=>sum+w.budget,0) || 0,[dashboard]);

  if (loading) return <section style={{padding:20,color:'rgba(233,231,223,.55)'}}>Loading Eden enterprise workspace…</section>;

  if (!dashboard) return <section style={{padding:24,borderRadius:18,border:'1px solid rgba(201,168,76,.18)',background:'rgba(201,168,76,.035)'}}>
    <div style={{fontSize:10,letterSpacing:'.12em',textTransform:'uppercase',color:'#C9A84C'}}>ENTERPRISE WORKSPACE</div>
    <h2 style={{margin:'8px 0 6px'}}>Eden Food Systems</h2>
    <p style={{maxWidth:680,color:'rgba(233,231,223,.58)',lineHeight:1.55}}>Initialize the governed Eden tenant on the existing SolSpire workspace. This provisions the enterprise structure and Week 1 operating seed. It does not authorize procurement, spending, execution, or any protected mutation.</p>
    {error && <p role="alert" style={{color:'#f0a8a8'}}>{error}</p>}
    <button type="button" onClick={bootstrap} disabled={bootstrapping} style={{marginTop:8,padding:'10px 14px',borderRadius:10,border:'1px solid rgba(201,168,76,.35)',background:'rgba(201,168,76,.10)',color:'#e9e7df',cursor:'pointer'}}>{bootstrapping?'Initializing…':'Initialize Eden Enterprise Workspace'}</button>
  </section>;

  return <div data-testid="eden-enterprise-dashboard" style={{display:'grid',gap:18}}>
    <header style={{display:'flex',justifyContent:'space-between',gap:16,alignItems:'flex-end',flexWrap:'wrap'}}>
      <div>
        <div style={{fontSize:10,letterSpacing:'.12em',textTransform:'uppercase',color:'#C9A84C'}}>SOLSPIRE ENTERPRISE · EDEN</div>
        <h2 style={{margin:'7px 0 4px'}}>{dashboard.product.name}</h2>
        <div style={{fontSize:11,color:'rgba(233,231,223,.43)'}}>{dashboard.product.surface} · {dashboard.product.tier} · {dashboard.product.role}</div>
      </div>
      <div style={{textAlign:'right'}}>
        <div style={{fontSize:10,color:'rgba(233,231,223,.42)'}}>WEEK 1 CONTROL BUDGET</div>
        <strong style={{fontSize:24}}>{money(total)}</strong>
      </div>
    </header>

    <section style={{display:'grid',gridTemplateColumns:'repeat(auto-fit,minmax(180px,1fr))',gap:10}}>
      {dashboard.money.map(c=><CellCard key={c.label} cell={c}/>)}
    </section>

    <section>
      <div style={{fontSize:10,letterSpacing:'.1em',textTransform:'uppercase',color:'rgba(233,231,223,.42)',marginBottom:9}}>Commercial confirmation</div>
      <div style={{display:'grid',gridTemplateColumns:'repeat(auto-fit,minmax(150px,1fr))',gap:10}}>{dashboard.commercial.map(c=><CellCard key={c.label} cell={c}/>)}</div>
    </section>

    <section>
      <div style={{fontSize:10,letterSpacing:'.1em',textTransform:'uppercase',color:'rgba(233,231,223,.42)',marginBottom:9}}>Eight operating desks</div>
      <div style={{display:'grid',gridTemplateColumns:'repeat(auto-fit,minmax(220px,1fr))',gap:10}}>
        {dashboard.operations.workstreams.map(w=><article key={w.slug} style={{padding:14,borderRadius:14,border:'1px solid rgba(233,231,223,.09)',background:'rgba(255,255,255,.025)'}}>
          <div style={{display:'flex',justifyContent:'space-between',gap:8}}><strong>{w.name}</strong><Status status={w.status}/></div>
          <div style={{marginTop:12,fontSize:17}}>{money(w.budget)}</div>
        </article>)}
      </div>
    </section>

    <section>
      <div style={{fontSize:10,letterSpacing:'.1em',textTransform:'uppercase',color:'rgba(233,231,223,.42)',marginBottom:9}}>Week 1 operating seed</div>
      <div style={{display:'grid',gap:7}}>
        {dashboard.operations.week1_tasks.map(t=><article key={t.task_id} style={{display:'grid',gridTemplateColumns:'72px minmax(160px,220px) 1fr auto',gap:10,alignItems:'center',padding:'10px 12px',borderRadius:10,border:'1px solid rgba(233,231,223,.07)',background:'rgba(255,255,255,.018)'}}>
          <span style={{fontSize:10,textTransform:'uppercase',color:'#C9A84C'}}>{t.day}</span>
          <span style={{fontSize:11,color:'rgba(233,231,223,.48)'}}>{t.owner_role}</span>
          <span style={{fontSize:12}}>{t.title}</span>
          <Status status={t.status}/>
        </article>)}
      </div>
    </section>

    <section style={{display:'grid',gridTemplateColumns:'repeat(auto-fit,minmax(220px,1fr))',gap:10}}>
      {dashboard.transaction.map(c=><CellCard key={c.label} cell={c}/>)}
    </section>

    <section style={{padding:14,borderRadius:14,border:'1px solid rgba(0,212,170,.14)',background:'rgba(0,212,170,.035)'}}>
      <div style={{fontSize:10,letterSpacing:'.1em',textTransform:'uppercase',color:'#00D4AA'}}>Truthfulness boundary</div>
      <p style={{fontSize:12,lineHeight:1.55,color:'rgba(233,231,223,.62)',marginBottom:5}}>{dashboard.truthfulness.rule}</p>
      <p style={{fontSize:11,color:'rgba(233,231,223,.42)',margin:0}}>{dashboard.truthfulness.unknown_policy}</p>
      {error && <p role="alert" style={{color:'#f0a8a8'}}>{error}</p>}
    </section>
  </div>;
}
