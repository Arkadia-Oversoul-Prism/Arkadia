import React,{useEffect,useMemo,useRef,useState} from 'react';
import {useAuth} from '../contexts/AuthContext';
import {apiFetch,setApiAuthToken} from '../lib/apiClient';

type Option={value:string;label:string;hint?:string};
type Attachment={attachment_id:string;original_name:string;content_type:string;size_bytes:number;extraction_status:string;extracted_text?:string};
type Step={n:number;label:string;title:string;intro:string};

const STEPS:Step[]=[
 {n:1,label:'Identity',title:'Tell SolSpire what you are building',intro:'A few structured choices establish the enterprise context. You can add documents when the Oracle needs deeper context.'},
 {n:2,label:'Pilot',title:'Choose the first workload',intro:'Start with one consequential workload. SolSpire can expand the operating model later.'},
 {n:3,label:'Workstreams',title:'Shape the operating structure',intro:'Select the workstreams that actually exist. Nothing is created merely because a template suggests it.'},
 {n:4,label:'People',title:'Map people and ownership',intro:'Define the relationships that matter. Ownership is recorded as context, not execution authority.'},
 {n:5,label:'Operating context',title:'Set the operating frame',intro:'Give the pilot a financial and operating frame without pretending that unknowns are known.'},
 {n:6,label:'Week 1',title:'Choose the first operating rhythm',intro:'Select what the first week should make visible and actionable.'},
 {n:7,label:'Dashboard',title:'Choose what the enterprise should see',intro:'The master dashboard is a projection of governed context, not an authorization surface.'},
];

const OPTIONS:Record<string,Option[]>={
 organization_type:[['company','Company'],['nonprofit','Nonprofit / NGO'],['collective','Collective / cooperative'],['institution','Institution'],['public_body','Public body'],['other','Other']].map(([value,label])=>({value,label})),
 stage:[['idea','Idea / formation'],['early','Early operations'],['operating','Operating organization'],['scaling','Scaling / expansion'],['restructuring','Restructuring']].map(([value,label])=>({value,label})),
 industry:[['agriculture','Agriculture / food'],['technology','Technology'],['education','Education'],['health','Health'],['creative','Creative / media'],['professional','Professional services'],['commerce','Commerce / trade'],['other','Other']].map(([value,label])=>({value,label})),
 workload_type:[['growth','Growth / expansion'],['delivery','Client or service delivery'],['operations','Internal operations'],['project','Strategic project'],['market','Market intelligence'],['product','Product / system build'],['other','Other']].map(([value,label])=>({value,label})),
 horizon:[['7d','7 days'],['30d','30 days'],['90d','90 days'],['quarter','Quarter'],['unknown','Not decided yet']].map(([value,label])=>({value,label})),
 workstreams:[['operations','Operations'],['finance','Finance'],['commercial','Commercial'],['people','People'],['delivery','Delivery'],['knowledge','Knowledge'],['technology','Technology'],['marketing','Marketing'],['compliance','Compliance'],['other','Other']].map(([value,label])=>({value,label})),
 member_role:[['owner','Owner / principal'],['operator','Operator / lead'],['manager','Manager'],['specialist','Specialist'],['advisor','Advisor'],['contributor','Contributor']].map(([value,label])=>({value,label})),
 cadence:[['daily','Daily'],['weekly','Weekly'],['biweekly','Every 2 weeks'],['monthly','Monthly'],['adaptive','Adaptive']].map(([value,label])=>({value,label})),
 budget_band:[['unknown','Not decided'],['micro','Under 100k'],['small','100k–500k'],['medium','500k–2m'],['large','2m+']].map(([value,label])=>({value,label})),
 dashboard_focus:[['execution','Execution / workload'],['finance','Financial visibility'],['people','People / ownership'],['growth','Growth / commercial'],['evidence','Evidence / review'],['all','Balanced view']].map(([value,label])=>({value,label})),
};

const card:React.CSSProperties={border:'1px solid rgba(233,231,223,.10)',background:'linear-gradient(145deg,rgba(255,255,255,.045),rgba(255,255,255,.018))',borderRadius:20};
const gold='#C9A84C';
const ink='#E9E7DF';
const muted='rgba(233,231,223,.50)';

function formatBytes(n:number){if(n<1024)return n+' B';if(n<1024*1024)return Math.round(n/1024)+' KB';return (n/(1024*1024)).toFixed(1)+' MB'}
function selected(data:any,key:string){return Array.isArray(data[key])?data[key]:[]}
function toggle(data:any,setData:(v:any)=>void,key:string,value:string){const next=selected(data,key);setData({...data,[key]:next.includes(value)?next.filter((v:string)=>v!==value):[...next,value]})}

export default function EnterpriseConsole({onNavigate}:{onNavigate?:(v:any)=>void}){
 const {isAuthenticated,user}=useAuth();
 const [list,setList]=useState<any[]>([]); const [enterprise,setEnterprise]=useState<any>(); const [step,setStep]=useState(1);
 const [data,setData]=useState<any>({}); const [analysis,setAnalysis]=useState(''); const [error,setError]=useState('');
 const [busy,setBusy]=useState(false); const [attachments,setAttachments]=useState<Attachment[]>([]); const [dashboard,setDashboard]=useState<any>();
 const fileRef=useRef<HTMLInputElement>(null);

 useEffect(()=>setApiAuthToken(user?.idToken??null),[user?.idToken]);
 const load=async()=>{try{const r=await apiFetch('/solspire/enterprise/workspaces');const d=await r.json();if(!r.ok)throw new Error(d?.detail||'Unable to load enterprises');setList(d.enterprises||[])}catch(e){setError(e instanceof Error?e.message:'Unable to load enterprises')}};
 useEffect(()=>{if(isAuthenticated)void load()},[isAuthenticated]);

 const loadAttachments=async(id:string)=>{try{const r=await apiFetch(`/solspire/enterprise/workspaces/${id}/attachments`);const d=await r.json();if(r.ok)setAttachments(d.attachments||[])}catch(e){setError(e instanceof Error?e.message:'Unable to load attachments')}};
 const create=async()=>{setBusy(true);setError('');try{const r=await apiFetch('/solspire/enterprise/workspaces',{method:'POST',body:JSON.stringify({})});const d=await r.json();if(!r.ok)throw new Error(d?.detail||'Unable to create enterprise');setEnterprise(d.enterprise);setStep(1);setData({});setAttachments([]);await load()}catch(e){setError(e instanceof Error?e.message:'Unable to create enterprise')}finally{setBusy(false)}};
 const open=(e:any)=>{setEnterprise(e);setStep(Math.min(e.onboarding_step||1,7));setData(e.context||{});void loadAttachments(e.enterprise_id)};
 const save=async(next=true)=>{if(!enterprise)return;setBusy(true);setError('');try{const r=await apiFetch(`/solspire/enterprise/workspaces/${enterprise.enterprise_id}/steps/${step}`,{method:'PUT',body:JSON.stringify({data})});const d=await r.json();if(!r.ok)throw new Error(d?.detail||'Unable to save step');setEnterprise(d.enterprise);if(next&&step<7){const n=step+1;setStep(n);setData(d.enterprise[sectionForStep(n)]||{})}}catch(e){setError(e instanceof Error?e.message:'Unable to save step')}finally{setBusy(false)}};
 const attach=async(file:File)=>{if(!enterprise)return;setBusy(true);setError('');try{const form=new FormData();form.append('file',file);const r=await apiFetch(`/solspire/enterprise/workspaces/${enterprise.enterprise_id}/attachments`,{method:'POST',body:form});const d=await r.json();if(!r.ok)throw new Error(d?.detail||'Unable to attach file');setAttachments(a=>[d.attachment,...a]);setAnalysis('');}catch(e){setError(e instanceof Error?e.message:'Unable to attach file')}finally{setBusy(false)}};
 const ask=async()=>{if(!enterprise)return;setBusy(true);setError('');try{const evidence=attachments.map(a=>({name:a.original_name,type:a.content_type,status:a.extraction_status,text:a.extracted_text||''}));const message=`Act as an advisory enterprise architect. Analyze onboarding step ${step}. Identify missing information, structural risks, dependencies, useful questions and possible next structure. Do not invent facts, authorize actions, or execute work. Preserve UNKNOWN. Current structured answers: ${JSON.stringify(data)}. Attached evidence: ${JSON.stringify(evidence)}`;const r=await apiFetch('/api/commune/resonance',{method:'POST',body:JSON.stringify({message,history:[],session_id:`enterprise-${enterprise.enterprise_id}`})});const d=await r.json();if(!r.ok)throw new Error(d?.error||'Oracle unavailable');setAnalysis(d.reply||'No advisory response returned');await apiFetch(`/solspire/enterprise/workspaces/${enterprise.enterprise_id}/analysis`,{method:'POST',body:JSON.stringify({step:`0${step}`,context:{input:data,attachments:evidence,advisory:d.reply||''}})})}catch(e){setError(e instanceof Error?e.message:'Oracle unavailable')}finally{setBusy(false)}};
 const showDashboard=async()=>{if(!enterprise)return;setBusy(true);try{const r=await apiFetch(`/solspire/enterprise/workspaces/${enterprise.enterprise_id}/dashboard`);const d=await r.json();if(!r.ok)throw new Error(d?.detail||'Unable to open dashboard');setDashboard(d)}catch(e){setError(e instanceof Error?e.message:'Unable to open dashboard')}finally{setBusy(false)}};

 if(!isAuthenticated)return <div style={{...card,maxWidth:680,margin:'8vh auto',padding:24}}><Eyebrow>SOLSPIRE · ENTERPRISE</Eyebrow><h2 style={{fontSize:'clamp(26px,7vw,42px)',fontWeight:400,margin:'10px 0'}}>Enter the enterprise layer.</h2><p style={{color:muted,lineHeight:1.7}}>Sign in to create or continue an organizational workspace. Solariun remains your personal intelligence canvas.</p><button style={primary} onClick={()=>onNavigate?.('gate')}>Sign in</button></div>;
 if(dashboard)return <Dashboard d={dashboard} onBack={()=>setDashboard(undefined)}/>;

 return <main className="enterprise-console" style={{maxWidth:1180,margin:'0 auto',paddingBottom:120}}>
  <style>{`
    .enterprise-console *{box-sizing:border-box}
    .enterprise-console button{font:inherit}
    .enterprise-shell{display:grid;gap:14px}
    .enterprise-grid{display:grid;gap:14px}
    .step-nav{display:flex;gap:7px;overflow-x:auto;padding:2px 1px 8px;scrollbar-width:none}
    .step-nav::-webkit-scrollbar{display:none}
    .step-pill{min-width:92px;border:1px solid rgba(233,231,223,.08);background:rgba(255,255,255,.025);color:rgba(233,231,223,.42);border-radius:14px;padding:9px 10px;text-align:left}
    .step-pill.active{border-color:rgba(201,168,76,.42);background:rgba(201,168,76,.08);color:#E9E7DF}
    .choice-grid{display:grid;grid-template-columns:1fr 1fr;gap:9px}
    .choice{min-height:62px;border:1px solid rgba(233,231,223,.10);background:rgba(255,255,255,.025);color:rgba(233,231,223,.70);border-radius:14px;padding:11px;text-align:left;cursor:pointer}
    .choice.selected{border-color:rgba(201,168,76,.58);background:rgba(201,168,76,.11);color:#E9E7DF;box-shadow:inset 0 0 0 1px rgba(201,168,76,.08)}
    .choice small{display:block;color:rgba(233,231,223,.34);margin-top:4px}
    .mobile-actions{position:fixed;z-index:30;left:0;right:0;bottom:0;padding:10px max(12px,env(safe-area-inset-right)) max(10px,env(safe-area-inset-bottom));background:rgba(8,10,18,.92);backdrop-filter:blur(18px);border-top:1px solid rgba(233,231,223,.08)}
    .mobile-actions-inner{max-width:1180px;margin:0 auto;display:flex;gap:8px}
    @media(min-width:760px){.choice-grid{grid-template-columns:repeat(3,1fr)}.enterprise-grid{grid-template-columns:230px minmax(0,1fr)}.step-nav{display:grid;overflow:visible}.mobile-actions{position:static;background:none;border:0;padding:0;backdrop-filter:none}.mobile-actions-inner{justify-content:flex-end}.mobile-actions .secondary{margin-right:auto}}
  `}</style>

  <div className="enterprise-shell">
   <header style={{...card,padding:'20px 18px'}}>
    <div style={{display:'flex',justifyContent:'space-between',gap:12,alignItems:'start'}}><div><Eyebrow>ARKADIA / SOLSPIRE</Eyebrow><h1 style={{fontSize:'clamp(28px,8vw,46px)',fontWeight:400,lineHeight:1.05,margin:'8px 0 7px'}}>Build the enterprise, one decision at a time.</h1><p style={{margin:0,color:muted,lineHeight:1.65,maxWidth:720}}>A guided operating setup with fewer forms, more choices, and an Oracle that can read the evidence you bring.</p></div><button onClick={()=>setEnterprise(undefined)} style={iconButton}>×</button></div>
   </header>

   {!enterprise?<Landing list={list} busy={busy} onCreate={()=>void create()} onOpen={open}/>:<>
    <div className="step-nav">{STEPS.map(s=><button className={`step-pill ${step===s.n?'active':''}`} key={s.n} onClick={()=>{setStep(s.n);setData(enterprise[sectionForStep(s.n)]||{})}}><b style={{color:gold}}>0{s.n}</b><span style={{display:'block',fontSize:11,marginTop:3}}>{s.label}</span></button>)}</div>
    <div className="enterprise-grid">
     <aside style={{...card,padding:12,height:'fit-content'}}><div style={{fontSize:10,color:muted,lineHeight:1.6,padding:'4px 7px 10px'}}>ONBOARDING PATH</div>{STEPS.map(s=><button key={s.n} onClick={()=>{setStep(s.n);setData(enterprise[sectionForStep(s.n)]||{})}} style={{display:'block',width:'100%',textAlign:'left',padding:'10px 9px',border:0,borderRadius:12,background:step===s.n?'rgba(201,168,76,.08)':'transparent',color:step===s.n?ink:muted,cursor:'pointer'}}><span style={{color:gold,marginRight:8}}>0{s.n}</span>{s.title}</button>)}</aside>
     <section style={{display:'grid',gap:12,minWidth:0}}>
      <section style={{...card,padding:'18px'}}><Eyebrow>STEP 0{step} · {STEPS[step-1].label}</Eyebrow><h2 style={{fontSize:'clamp(24px,6vw,38px)',fontWeight:400,margin:'8px 0 7px'}}>{STEPS[step-1].title}</h2><p style={{color:muted,lineHeight:1.65,margin:0}}>{STEPS[step-1].intro}</p></section>
      <StepEditor step={step} data={data} setData={setData}/>
      <AttachmentZone attachments={attachments} busy={busy} inputRef={fileRef} onPick={attach}/>
      {analysis&&<section style={{...card,padding:17,borderColor:'rgba(0,212,170,.22)'}}><Eyebrow color="#00D4AA">ARKANA · ADVISORY</Eyebrow><div style={{whiteSpace:'pre-wrap',fontSize:12,lineHeight:1.7,color:'rgba(233,231,223,.72)',marginTop:8}}>{analysis}</div></section>}
     </section>
    </div>
    <div className="mobile-actions"><div className="mobile-actions-inner"><button className="secondary" style={secondary} disabled={busy} onClick={()=>void ask()}>✦ Ask Oracle</button><button style={secondary} disabled={busy||step===1} onClick={()=>{const n=Math.max(1,step-1);setStep(n);setData(enterprise[sectionForStep(n)]||{})}}>Back</button><button style={primary} disabled={busy} onClick={()=>void save(step<7)}>{busy?'Saving…':step<7?'Save & continue':'Save onboarding'}</button>{step===7&&<button style={secondary} disabled={busy} onClick={()=>void showDashboard()}>Dashboard</button>}</div></div>
   </>}
   {error&&<div role="alert" style={{...card,padding:12,color:'#f0aaaa',fontSize:12}}>{error}</div>}
  </div>
 </main>
}

function sectionForStep(step:number){return ['context','pilot_workload','workstreams','members','operating_context','week_one','dashboard_config'][step-1]}

function Eyebrow({children,color=gold}:{children:React.ReactNode;color?:string}){return <div style={{fontSize:9,letterSpacing:'.16em',textTransform:'uppercase',color}}>{children}</div>}
const primary:React.CSSProperties={flex:1,padding:'13px 15px',borderRadius:13,border:'1px solid rgba(201,168,76,.5)',background:'linear-gradient(135deg,rgba(201,168,76,.18),rgba(201,168,76,.07))',color:ink,cursor:'pointer',fontSize:12};
const secondary:React.CSSProperties={padding:'13px 14px',borderRadius:13,border:'1px solid rgba(233,231,223,.12)',background:'rgba(255,255,255,.035)',color:'rgba(233,231,223,.68)',cursor:'pointer',fontSize:12};
const iconButton:React.CSSProperties={border:0,background:'transparent',color:'rgba(233,231,223,.35)',fontSize:26,cursor:'pointer'};

function Landing({list,busy,onCreate,onOpen}:{list:any[];busy:boolean;onCreate:()=>void;onOpen:(e:any)=>void}){
 return <section style={{display:'grid',gap:12}}>
  <section style={{...card,padding:20}}><div style={{fontSize:34,marginBottom:8}}>▦</div><h2 style={{fontSize:24,fontWeight:400,margin:'0 0 7px'}}>Start an enterprise workspace</h2><p style={{color:muted,lineHeight:1.65}}>SolSpire will guide you through identity, pilot workload, workstreams, people, operating context, Week 1 and dashboard projection.</p><button style={primary} disabled={busy} onClick={onCreate}>{busy?'Creating…':'Create enterprise workspace'}</button></section>
  {list.length>0&&<section style={{display:'grid',gap:8}}><Eyebrow>YOUR ENTERPRISES</Eyebrow>{list.map(e=><button key={e.enterprise_id} onClick={()=>onOpen(e)} style={{...card,padding:15,textAlign:'left',color:ink,cursor:'pointer'}}><b>{e.display_name}</b><span style={{display:'block',fontSize:10,color:muted,marginTop:6}}>Step {e.onboarding_step}/7 · {e.lifecycle}</span></button>)}</section>}
 </section>
}

function StepEditor({step,data,setData}:{step:number;data:any;setData:(v:any)=>void}){
 const set=(k:string,v:any)=>setData({...data,[k]:v});
 const choices=(key:string,multi=false)=><ChoiceGrid options={OPTIONS[key]||[]} value={data[key]} multi={multi} onChange={v=>set(key,v)}/>;
 const text=(key:string,label:string,placeholder:string)=> <label style={field}><span>{label}</span><textarea value={data[key]||''} onChange={e=>set(key,e.target.value)} placeholder={placeholder} rows={3}/></label>;

 if(step===1)return <section style={{...card,padding:16,display:'grid',gap:18}}><Question title="What kind of organization is this?">{choices('organization_type')}</Question><Question title="Where is it in its journey?">{choices('stage')}</Question><Question title="What domain is closest?">{choices('industry')}</Question>{text('jurisdiction','Operating geography','Country, region, or jurisdictions…')}{data.organization_type==='other'&&text('organization_type_other','Describe it','A short description…')}{text('display_name','What should SolSpire call it?','Enterprise display name…')}{text('description','Anything the Oracle should understand now?','Purpose, operating model, important context…')}</section>;
 if(step===2)return <section style={{...card,padding:16,display:'grid',gap:18}}><Question title="What is the pilot mainly about?">{choices('workload_type')}</Question><Question title="What horizon matters first?">{choices('horizon')}</Question>{text('name','Pilot name','e.g. Abuja market intelligence sprint')}{text('objective','What outcome are you trying to produce?','One clear outcome…')}{text('success_criteria','How will you know it worked?','Evidence, metric, deliverable, or decision…')}</section>;
 if(step===3)return <section style={{...card,padding:16,display:'grid',gap:18}}><Question title="Which workstreams are actually involved?"><span style={{color:muted,fontSize:11}}>Choose as many as needed.</span>{choices('workstreams',true)}</Question>{text('structure_notes','Anything about the structure?','Dependencies, existing teams, important boundaries…')}</section>;
 if(step===4)return <section style={{...card,padding:16,display:'grid',gap:18}}><Question title="What role do you hold in this enterprise?">{choices('member_role')}</Question>{text('members','Who should be involved?','Name or role, one per line. The Oracle can help structure this later…')}{text('ownership_rules','What ownership should be explicit?','For example: finance lead owns budget context; operations lead owns delivery context…')}</section>;
 if(step===5)return <section style={{...card,padding:16,display:'grid',gap:18}}><Question title="How should the pilot operate?">{choices('cadence')}</Question><Question title="What budget frame is known?">{choices('budget_band')}</Question>{text('currency','Currency','NGN, USD, GBP…')}{text('budget_total','Known budget amount','Leave blank if unknown. UNKNOWN is valid.')}{text('allocations','Known allocations','Optional: one allocation per line…')}{text('financial_assumptions','Important assumptions','Known constraints, funding conditions, payment timing…')}</section>;
 if(step===6)return <section style={{...card,padding:16,display:'grid',gap:18}}><Question title="What should Week 1 emphasize?"><ChoiceGrid options={[{value:'clarity',label:'Clarify the operating picture'},{value:'evidence',label:'Collect evidence and documents'},{value:'execution',label:'Move a concrete workload forward'},{value:'people',label:'Align owners and relationships'},{value:'measurement',label:'Establish metrics and review'}]} value={data.week_one_focus} multi onChange={v=>set('week_one_focus',v)}/></Question>{text('objectives','Week 1 objectives','One objective per line…')}{text('tasks','Known tasks or first actions','One task per line…')}{text('readiness_criteria','What must be true by the end of Week 1?','A short readiness definition…')}</section>;
 return <section style={{...card,padding:16,display:'grid',gap:18}}><Question title="What should the master dashboard foreground?"><ChoiceGrid options={OPTIONS.dashboard_focus} value={data.focus} multi onChange={v=>set('focus',v)}/></Question><Question title="What should remain visible?"><ChoiceGrid options={[{value:'workload',label:'Pilot workload'},{value:'workstreams',label:'Workstreams'},{value:'people',label:'People & ownership'},{value:'budget',label:'Budget context'},{value:'objectives',label:'Week 1 objectives'},{value:'evidence',label:'Evidence & review'}]} value={data.views} multi onChange={v=>set('views',v)}/></Question>{text('critical_path_fields','Critical path fields','What must never be buried?')}{text('evidence_fields','Evidence fields','What evidence should the dashboard surface?')}</section>;
}

function Question({title,children}:{title:string;children:React.ReactNode}){return <div style={{display:'grid',gap:9}}><div><b style={{fontSize:14,fontWeight:500}}>{title}</b></div>{children}</div>}
const field:React.CSSProperties={display:'grid',gap:7,fontSize:11,color:muted};
function ChoiceGrid({options,value,multi,onChange}:{options:Option[];value:any;multi?:boolean;onChange:(v:any)=>void}){
 const current=multi?(Array.isArray(value)?value:[]):value;
 return <div className="choice-grid">{options.map(o=>{const active=multi?current.includes(o.value):current===o.value;return <button type="button" className={`choice ${active?'selected':''}`} key={o.value} onClick={()=>multi?onChange(active?current.filter((v:string)=>v!==o.value):[...current,o.value]):onChange(o.value)}><b>{o.label}</b>{o.hint&&<small>{o.hint}</small>}</button>})}</div>
}

function AttachmentZone({attachments,busy,inputRef,onPick}:{attachments:Attachment[];busy:boolean;inputRef:React.RefObject<HTMLInputElement | null>;onPick:(f:File)=>void}){
 return <section style={{...card,padding:16,display:'grid',gap:10}}><div style={{display:'flex',justifyContent:'space-between',gap:10,alignItems:'center'}}><div><Eyebrow>ORACLE EVIDENCE</Eyebrow><b style={{display:'block',marginTop:5}}>Attach anything relevant</b></div><span style={{fontSize:10,color:muted}}>{attachments.length} attached</span></div><p style={{fontSize:11,lineHeight:1.6,color:muted,margin:'0 0 3px'}}>PDF, Word, spreadsheets, images, archives, text, presentations, or other formats can be attached. SolSpire preserves the original file and extracts readable content where supported.</p><input ref={inputRef} type="file" hidden onChange={e=>{const f=e.target.files?.[0];if(f)void onPick(f);e.currentTarget.value=''}}/><button style={{...secondary,width:'100%'}} disabled={busy} onClick={()=>inputRef.current?.click()}>＋ Attach file</button>{attachments.map(a=><div key={a.attachment_id} style={{display:'flex',gap:10,alignItems:'center',padding:'9px 10px',borderRadius:12,background:'rgba(255,255,255,.025)'}}><span style={{fontSize:16}}>⌁</span><div style={{minWidth:0,flex:1}}><div style={{fontSize:11,overflow:'hidden',textOverflow:'ellipsis',whiteSpace:'nowrap'}}>{a.original_name}</div><div style={{fontSize:9,color:muted,marginTop:3}}>{formatBytes(a.size_bytes)} · {a.extraction_status==='EXTRACTED'?'Readable content extracted':'File preserved; extraction limited'}</div></div></div>)}</section>
}

function Dashboard({d,onBack}:{d:any;onBack:()=>void}){return <main style={{maxWidth:1180,margin:'0 auto',display:'grid',gap:12,paddingBottom:40}}><section style={{...card,padding:20}}><Eyebrow>SOLSPIRE · MASTER DASHBOARD</Eyebrow><h1 style={{fontSize:'clamp(28px,8vw,44px)',fontWeight:400,margin:'8px 0'}}>{d.enterprise.name}</h1><p style={{color:muted,lineHeight:1.6}}>A projection of the enterprise operating context. It does not authorize or execute work.</p></section><section style={{display:'grid',gridTemplateColumns:'repeat(auto-fit,minmax(145px,1fr))',gap:9}}>{[['Lifecycle',d.enterprise.lifecycle],['Onboarding',`${d.enterprise.onboarding_step}/7`],['Budget',d.financial.budget_total],['Workstreams',d.control.workstreams?.length||0],['Members',d.control.members?.length||0]].map(([l,v])=><article key={String(l)} style={{...card,padding:15}}><div style={{fontSize:9,color:muted,textTransform:'uppercase'}}>{l}</div><div style={{fontSize:20,marginTop:7}}>{v??'UNKNOWN'}</div></article>)}</section><section style={{...card,padding:17}}><b>Operating structure</b><pre style={{whiteSpace:'pre-wrap',font:'11px/1.55 monospace',color:'rgba(233,231,223,.55)',overflow:'auto'}}>{JSON.stringify(d.control,null,2)}</pre></section><section style={{...card,padding:17,borderColor:'rgba(0,212,170,.2)'}}><b style={{color:'#00D4AA'}}>Truthfulness boundary</b><p style={{fontSize:11,lineHeight:1.6,color:muted}}>{d.truthfulness.rule}</p><p style={{fontSize:11,color:muted}}>{d.truthfulness.unknown_policy}</p></section><button style={secondary} onClick={onBack}>← Return to onboarding</button></main>}
