import React, { useEffect, useMemo, useState } from 'react';
import './solspire.css';
import './solspire-canonical.css';
import ArkanaCommune from '../ArkanaCommune';
import ResilientProjectDashboard from './ResilientProjectDashboard';
import type { Project, ProjTab } from '../../pages/ProjectDashboard';
import ProjectsWorkspace from './ProjectsWorkspace';
import { FilesWorkspace, ConversationsWorkspace, TasksWorkspace } from './WorkspaceActionSurfaces';
import SolariunHomeCockpit from './SolariunHomeCockpit';
import KnowledgeOSPage from '../../pages/knowledge/KnowledgeOSPage';
import SettingsPage from '../../pages/SettingsPage';
import SourceSyncPanel from './SourceSyncPanel';
import { CommercialPanel, WeaverSummary, WorkspaceCollection } from '../../pages/SolSpireWorkspacePanels';
import { search as searchKnowledge } from '../../lib/knowledgeApi';
import { apiFetch } from '../../lib/apiClient';
import { useAuth } from '../../contexts/AuthContext';
import EngineeringLabLens from './EngineeringLabLens';

export type SolSpireLens = 'overview'|'projects'|'commercial'|'knowledge'|'files'|'conversations'|'tasks'|'memory'|'weaver'|'observatory'|'engineering-lab'|'settings';
type NavItem = { id: SolSpireLens; label: string; sigil: string; accent: string; question: string };
/** P0.1: lenses that stay inside the open project (no re-pick). */
const PROJECT_LENS_TO_TAB: Partial<Record<SolSpireLens, ProjTab>> = {
  overview: 'overview',
  files: 'files',
  tasks: 'tasks',
  conversations: 'conversations',
  memory: 'memory',
  knowledge: 'knowledge',
  weaver: 'weaver',
  observatory: 'events',
};

const NAV: NavItem[] = [
  {id:'overview',label:'Home',sigil:'◎',accent:'#6A9FD8',question:'What matters now?'},
  {id:'projects',label:'Projects',sigil:'◈',accent:'#C9A84C',question:'What am I building?'},
  {id:'commercial',label:'Commercial',sigil:'◇',accent:'#C9A84C',question:'Where is value emerging?'},
  {id:'knowledge',label:'Knowledge',sigil:'◉',accent:'#00D4AA',question:'What does the system know?'},
  {id:'files',label:'Files',sigil:'◫',accent:'#C9A84C',question:'What exists?'},
  {id:'conversations',label:'Conversations',sigil:'◌',accent:'#6A9FD8',question:'What am I thinking through?'},
  {id:'tasks',label:'Tasks',sigil:'□',accent:'#00D4AA',question:'What commitments are active?'},
  {id:'memory',label:'Memory',sigil:'∞',accent:'#B08DE8',question:'What persists?'},
  {id:'weaver',label:'Weaver',sigil:'⚒',accent:'#B08DE8',question:'What is being worked on?'},
  {id:'observatory',label:'Activity',sigil:'⟐',accent:'#6A9FD8',question:'What happened?'},
  {id:'engineering-lab',label:'Engineering Lab',sigil:'⌬',accent:'#00D4AA',question:'How is Arkadia observing itself?'},
  {id:'settings',label:'Settings',sigil:'◆',accent:'#9A9AA2',question:'How does the environment behave?'},
];
const NETWORK=[
  {view:'novanet',label:'Nexus Hub',sigil:'◉',sub:'Public field / hub'},
  {view:'solspire',label:'Solariun',sigil:'◈',sub:'Private workspace'},
  {view:'grove',label:'Spiral Grove',sigil:'✧',sub:'Learning grove'},
  {view:'spiral-command',label:'Spiral Command',sigil:'⌘',sub:'Governance / command'},
  {view:'spiral-codex',label:'Spiral Codex',sigil:'✦',sub:'Living transmissions'},
  {view:'personal-echofeild',label:'Echofeild',sigil:'◎',sub:'Personal field'},
] as const;

export type SolSpireObject = { id:string; type:string; title:string; summary?:string; status?:string; projectId?:string; source?:string; updatedAt?:string|number };
export type SolSpireRelation = { type:'CONNECTED TO'|'DERIVED FROM'|'REFERENCES'|'BELONGS TO'|'FOLLOW-UP FOR'|'GENERATED FROM'; sourceId:string; targetId:string };
export function ObjectCard({object, accent='#C9A84C', onOpen}:{object:SolSpireObject; accent?:string; onOpen?:()=>void}) { return <article className="solspire-object" onClick={onOpen} role={onOpen?'button':undefined} tabIndex={onOpen?0:undefined} onKeyDown={e=>{if(onOpen&&(e.key==='Enter'||e.key===' '))onOpen()}}><div className="solspire-kicker" style={{color:`${accent}aa`}}>{object.type}</div><h3 className="solspire-title">{object.title}</h3>{object.summary&&<p className="solspire-object-summary">{object.summary}</p>}<div className="solspire-object-meta"><span>{object.status||'ACTIVE'}</span>{object.projectId&&<span>{object.projectId}</span>}</div><div className="solspire-id">{object.id}</div></article>; }
export function RelationChip({relation, label}:{relation:SolSpireRelation; label?:string}) { return <span className="solspire-relation" title={`${relation.type} ${relation.targetId}`}>{relation.type}{label?` · ${label}`:''}</span>; }
export function ActivityItem({type,title,context,time,id}:{type:string;title:string;context?:string;time?:string;id?:string}) { return <div className="solspire-activity-item"><span className="solspire-activity-dot"/><div><div className="solspire-kicker">{type}</div><div className="solspire-activity-title">{title}</div>{context&&<div className="solspire-activity-context">{context}</div>}</div><div className="solspire-activity-time">{time||''}{id&&<small>{id}</small>}</div></div>; }

function Header({identity,onSearch,onArkana,onMenu,onPrism}:{identity:string;onSearch:()=>void;onArkana:()=>void;onMenu:()=>void;onPrism:()=>void}) { return <header className="solspire-canonical-header"><button type="button" className="solspire-prism-return" onClick={onPrism} aria-label="Return to Arkadia Prism"><span>◈</span><strong>ARKADIA PRISM</strong><small>RETURN TO NEXUS</small></button><div className="solspire-brand"><span className="solspire-mark">◈</span><div><div className="solspire-brand-name">SOLARIUN</div><div className="solspire-brand-sub">personal intelligence workspace</div></div></div><div className="solspire-header-actions"><button type="button" className="solspire-quiet-button" onClick={onSearch} aria-label="Search Solariun">⌕ <span>Search</span></button><button type="button" className="solspire-arkana-button" onClick={onArkana} aria-label="Ask Arkana">⌁ <span>Ask Arkana</span></button><button type="button" className="solspire-menu-button" onClick={onMenu} aria-label="Open Solariun navigation">☰</button><div className="solspire-identity"><span className="solspire-online-dot"/><span className="solspire-identity-copy"><small>AUTHENTICATED NODE</small><strong>{identity}</strong></span></div></div></header>; }
function GlobalDoors({onNavigate}:{onNavigate:(view:string)=>void}) { return <section className="solspire-global-doors solspire-prism-rail" aria-label="Arkadia Prism horizontal navigation"><div className="solspire-global-label"><span>ARKADIA PRISM</span><small>NEXUS → SOLARIUN → FIELD</small></div><div className="solspire-global-door-row">{NETWORK.map(item=><button key={item.view} type="button" onClick={()=>onNavigate(item.view)} title={item.sub}><span>{item.sigil}</span><div><strong>{item.label}</strong><small>{item.sub}</small></div></button>)}</div></section>; }
const BOTTOM_NAV: NavItem[] = ['overview','projects','files','conversations','tasks','memory','observatory','commercial','settings'].map(id=>NAV.find(n=>n.id===id)!).filter(Boolean);
function MobileNav({section,onSection}:{section:SolSpireLens;onSection:(s:SolSpireLens)=>void}) { return <nav className="solspire-mobile-bottom solariun-bottom-rail" aria-label="Solariun primary navigation">{BOTTOM_NAV.map(n=><button key={n.id} type="button" className={section===n.id?'active':''} aria-current={section===n.id?'page':undefined} onClick={()=>onSection(n.id)}><span>{n.sigil}</span><small>{n.label}</small></button>)}</nav>; }
function Sidebar({section,onSection}:{section:SolSpireLens;onSection:(s:SolSpireLens)=>void}) { return <aside className="solspire-sidebar" aria-label="Solariun navigation"><div className="solspire-sidebar-intro"><span className="solspire-online-dot"/><span>AUTHENTICATED FIELD</span><small>one surface · private</small></div>{NAV.map(n=><button key={n.id} type="button" className={`solspire-nav-button ${section===n.id?'active':''}`} aria-current={section===n.id?'page':undefined} style={{'--lens-accent':n.accent} as React.CSSProperties} onClick={()=>onSection(n.id)}><span>{n.sigil}</span><div><strong>{n.label}</strong><small>{n.question}</small></div></button>)}</aside>; }
function ContextBar({lens,project,onArkana,onPrism}:{lens:NavItem;project?:Project|null;onArkana:()=>void;onPrism:()=>void}) { return <div className="solspire-context-bar"><div><span className="solspire-mono">ARKADIA / SOLARIUN / {lens.label.toUpperCase()}</span>{project&&<><span className="solspire-context-separator">/</span><strong>{project.name}</strong></>}</div><div className="solspire-context-actions"><button type="button" onClick={onPrism} className="solspire-context-return">← Prism / Nexus</button><button type="button" onClick={onArkana}>⌁ Ask Arkana {project?'about this context':'about this workspace'}</button></div></div>; }
function SearchOverlay({onClose, project}:{onClose:()=>void; project?: Project|null}) {
  /** P2 Universal Search — honest coverage: Knowledge OS + optional project corpus federation. No new index. */
  const {user}=useAuth();
  const [query,setQuery]=useState('');
  const [results,setResults]=useState<any[]>([]);
  const [loading,setLoading]=useState(false);
  const [error,setError]=useState<string|null>(null);
  const [channels,setChannels]=useState<string[]>([]);
  useEffect(()=>{},[user?.idToken]);
  useEffect(()=>{
    if(!query.trim()){setResults([]);setError(null);setChannels([]);return;}
    const timer=window.setTimeout(async()=>{
      setLoading(true);setError(null);
      const q=query.trim().toLowerCase();
      const used:string[]=['knowledge-os'];
      try {
        const r=await searchKnowledge(query.trim(),['semantic','fulltext','project','timeline'],12);
        const groups=['semantic','fulltext','project','timeline'];
        const flat=groups.flatMap(k=>(r as any)[k]||[]);
        const seen=new Set<string>();
        let items=flat.filter((x:any)=>{const key=String(x.note_uuid||x.id||x.title||JSON.stringify(x));if(seen.has(key))return false;seen.add(key);return true;}).map((x:any)=>({
          ...x,
          _channel:'knowledge-os',
          _label:x.note_type||x.type||'KNOWLEDGE',
        }));
        if(project?.id){
          used.push('project-corpus');
          const [files,tasks,mem]=await Promise.all([
            apiFetch(`/solspire/projects/${project.id}/files`).then(r=>r.json()).catch(()=>({files:[]})),
            apiFetch(`/solspire/projects/${project.id}/tasks`).then(r=>r.json()).catch(()=>({tasks:[]})),
            apiFetch(`/solspire/projects/${project.id}/memory`).then(r=>r.json()).catch(()=>({memory:[]})),
          ]);
          const match=(s:string)=>s.toLowerCase().includes(q);
          for(const f of (files.files||[])){
            if(match(String(f.name||''))) items.push({id:f.id,title:f.name,_label:'FILE',_channel:'project-corpus',summary:f.mime_type||''});
          }
          for(const task of (tasks.tasks||[])){
            if(match(String(task.title||task.name||''))) items.push({id:task.id,title:task.title||task.name,_label:'TASK',_channel:'project-corpus',summary:task.status||''});
          }
          for(const mem of (mem.memory||mem.items||[])){
            const text=String(mem.content||mem.body||mem.title||'');
            if(match(text)||match(String(mem.title||''))) items.push({id:mem.id,title:mem.title||text.slice(0,48),_label:'MEMORY',_channel:'project-corpus',summary:text.slice(0,120)});
          }
        }
        setChannels(used);
        setResults(items);
      } catch(e:any) {
        setError(e.message||'Search unavailable');
      } finally {
        setLoading(false);
      }
    },320);
    return()=>window.clearTimeout(timer);
  },[query, project?.id]);
  return <div className="solspire-overlay" role="dialog" aria-modal="true" aria-label="Search Solariun" data-solariun-search="federated" data-testid="solariun-search-overlay">
    <div className="solspire-search-panel">
      <div className="solspire-overlay-head">
        <div>
          <span className="solspire-kicker">Federated search</span>
          <h2>Search Solariun</h2>
        </div>
        <button type="button" onClick={onClose} aria-label="Close search">×</button>
      </div>
      <div data-testid="solariun-search-coverage" style={{margin:'0 0 10px',padding:'8px 10px',borderRadius:8,border:'1px solid rgba(0,212,170,0.2)',fontSize:10,color:'rgba(233,231,223,0.45)'}}>
        <strong style={{color:'#00D4AA'}}>COVERAGE (honest)</strong>
        {' · '}Knowledge OS channels always attempted
        {project?.id ? ' · Project corpus (files/tasks/memory) filtered client-side when a project is open' : ' · Open a project to include project corpus'}
        {' · '}No universal object index · Semantic may be unavailable
      </div>
      <input autoFocus value={query} onChange={e=>setQuery(e.target.value)} placeholder={project?.id ? 'Search knowledge + this project corpus…' : 'Search Knowledge OS…'} />
      {loading&&<div className="solspire-search-state">Searching…</div>}
      {error&&<div className="solspire-search-error">{error}</div>}
      {!loading&&query.trim()&&!results.length&&!error&&<div className="solspire-search-state">No matching results in active channels.</div>}
      <div className="solspire-search-results">{results.map((x:any,i:number)=><article key={`${x.note_uuid||x.id||i}`} data-search-channel={x._channel||'knowledge-os'}><div className="solspire-kicker">{x._label||x.note_type||x.type||'KNOWLEDGE'} · {x._channel||'knowledge-os'}</div><h3>{x.title||x.name||'Untitled'}</h3><p>{String(x.content||x.summary||'').slice(0,220)}</p><span>{x.note_uuid||x.id||''}</span></article>)}</div>
      <div className="solspire-search-hint" data-testid="solariun-search-channels">Channels: {channels.join(', ')||'—'}. Not a parallel search database.</div>
    </div>
  </div>;
}

function ArkanaOverlay({context,pack,onClose}:{context:string;pack:{surface:string;projectName?:string|null;projectId?:string|null;authenticated:boolean};onClose:()=>void}) {
  /** P1.1 Bounded Arkana Context Pack — display-only context; the conversation remains the canonical persistent thread. */
  const lines = [
    pack.authenticated ? 'Authenticated session: yes' : 'Authenticated session: unknown',
    `Surface: ${pack.surface}`,
    pack.projectName ? `Project: ${pack.projectName}` : 'Project: (none open)',
    pack.projectId ? `Project id: ${pack.projectId}` : null,
    'Files / knowledge / tasks: available via project APIs only when a project is open',
    'Arkana receives no silent full-corpus dump',
  ].filter(Boolean) as string[];
  return <div className="solspire-overlay" role="dialog" aria-modal="true" aria-label="Ask Arkana"><div className="solspire-arkana-panel"><div className="solspire-overlay-head"><div><div className="solspire-kicker">Persistent Arcana thread</div><h2>Arkana</h2><p>{context}</p></div><button type="button" onClick={onClose} aria-label="Close Arkana">×</button></div>
    <div data-testid="solariun-arkana-context-pack" style={{margin:'0 16px 12px',padding:'10px 12px',borderRadius:10,border:'1px solid rgba(0,212,170,0.22)',background:'rgba(0,212,170,0.05)',fontSize:11,color:'rgba(233,231,223,0.5)'}}>
      <strong style={{color:'#00D4AA'}}>CURRENT CONTEXT</strong>
      <ul style={{margin:'8px 0 0',paddingLeft:18}}>{lines.map(l=><li key={l}>{l}</li>)}</ul>
      <div style={{marginTop:8,opacity:0.75}}>Context is displayed here. It is not injected into the visible conversation as a synthetic user message.</div>
    </div>
    <ArkanaCommune projectId={pack.projectId ? Number(pack.projectId) : undefined} /></div></div>;
}
class SolariunHomeBoundary extends React.Component<{children:React.ReactNode},{hasError:boolean}> {
  state = { hasError: false };
  static getDerivedStateFromError() { return { hasError: true }; }
  componentDidCatch(error: Error) { console.error('[CAL-09] Solariun Home render failure', error); }
  render() {
    if (this.state.hasError) return <div role="alert" data-solariun-home-render-state="FAILED" style={{ color: 'rgba(232,232,232,.54)', font: '12px/1.6 Inter,system-ui,sans-serif', padding: 16 }}>Solariun Home failed during rendering. No synthetic workspace state has been substituted.</div>;
    return this.props.children;
  }
}

function LensContent({section,onOpenProject,onOpenWeaver,onOpenProjectTab}:{section:SolSpireLens;onOpenProject:(p:Project)=>void;onOpenWeaver:(p:Project)=>void;onOpenProjectTab:(p:Project,tab:ProjTab)=>void}) { if(section==='overview')return <SolariunHomeBoundary><SolariunHomeCockpit/></SolariunHomeBoundary>; if(section==='projects')return <ProjectsWorkspace onOpenProject={onOpenProject}/>; if(section==='commercial')return <CommercialPanel/>; if(section==='knowledge')return <div data-testid="solariun-knowledge-library-mode"><div style={{marginBottom:12,padding:'10px 12px',borderRadius:10,border:'1px solid rgba(0,212,170,0.22)',background:'rgba(0,212,170,0.05)',fontSize:11,color:'rgba(233,231,223,0.45)'}}><strong style={{color:'#00D4AA'}}>GLOBAL KNOWLEDGE LIBRARY</strong>{' · '}System-wide Knowledge OS — not the active project corpus. Open a project and use Project → Knowledge for project-scoped sources.</div><KnowledgeOSPage/></div>; if(section==='files')return <FilesWorkspace onOpenProject={onOpenProject}/>; if(section==='conversations')return <ConversationsWorkspace onOpenProject={onOpenProject}/>; if(section==='tasks')return <TasksWorkspace onOpenProject={onOpenProject}/>; if(section==='memory')return <WorkspaceCollection kind="memory" onOpenProject={p=>onOpenProjectTab(p,'memory')}/>; if(section==='weaver')return <WeaverSummary onOpenProject={onOpenWeaver}/>; if(section==='observatory')return <WorkspaceCollection kind="events" onOpenProject={p=>onOpenProjectTab(p,'events')}/>; if(section==='engineering-lab')return <EngineeringLabLens/>; return <><SettingsPage/><SourceSyncPanel/></>; }

export default function SolSpireExperience({identity='Authenticated node',initialSection='overview',onNavigate}:{identity?:string;initialSection?:SolSpireLens;onNavigate?:(view:string)=>void}) { const [section,setSection]=useState<SolSpireLens>(initialSection); const [project,setProject]=useState<Project|null>(null); const [projectTab,setProjectTab]=useState<ProjTab>('overview'); const [search,setSearch]=useState(false); const [arkana,setArkana]=useState(false); const [more,setMore]=useState(false); const lens=useMemo(()=>NAV.find(n=>n.id===section)||NAV[0],[section]); const context=project?`${project.name} project context · files, conversations, tasks, memory, knowledge and governed Weaver work`:`${lens.label} lens · authenticated Solariun workspace state`;
  useEffect(()=>{setSection(initialSection);setProject(null);},[initialSection]);
  useEffect(()=>{const onKeyDown=(event:KeyboardEvent)=>{if(event.key==='Escape'){setSearch(false);setArkana(false);setMore(false)}};window.addEventListener('keydown',onKeyDown);return()=>window.removeEventListener('keydown',onKeyDown)},[]);
  const selectSection=(next:SolSpireLens)=>{
    setMore(false);
    const path=next==='overview'?'/solspire':`/solspire/${next}`;
    if(window.location.pathname!==path)window.history.pushState({},'',path);
    // P0.1 Project Field Continuity: keep project when lens maps to a project tab
    if(project && next in PROJECT_LENS_TO_TAB){
      setSection(next);
      setProjectTab(PROJECT_LENS_TO_TAB[next]!);
      return;
    }
    setSection(next);
    setProject(null);
    setProjectTab('overview');
  };
  const leavePrism=()=>{ if(onNavigate) onNavigate('novanet'); else window.history.pushState({},'', '/nexus'); window.dispatchEvent(new PopStateEvent('popstate')); };
  const navigateGlobal=(view:string)=>{setMore(false);if(onNavigate) onNavigate(view);else window.location.assign(view==='novanet'?'/nexus':`/${view}`)};
  const openProject=(p:Project)=>{setProject(p);setProjectTab('overview');}; const openProjectTab=(p:Project,tab:ProjTab)=>{setProject(p);setProjectTab(tab);}; const openWeaver=(p:Project)=>{openProjectTab(p,'weaver')};
  if(project)return <div className="solspire-workspace solariun-canvas" data-solariun-zoom="deep" data-solariun-surface="project" role="application" aria-label="Solariun project canvas"><GlobalDoors onNavigate={navigateGlobal}/><Header identity={identity} onSearch={()=>setSearch(true)} onArkana={()=>setArkana(true)} onMenu={()=>setMore(true)} onPrism={leavePrism}/><div className="solspire-project-context" data-testid="solariun-project-context" data-field-continuity="p0.1"><button type="button" onClick={()=>{setProject(null);setProjectTab('overview');setSection('projects')}}>← Projects</button><div><span className="solspire-kicker">PROJECT CONTEXT</span><strong>{project.name}</strong></div><span className="solspire-mono">field continuity · lens stays in project</span></div><main className="solspire-project-main solspire-object-sheet" data-testid="solariun-object-sheet"><ContextBar lens={{...lens,label:projectTab==='overview'?'Project':projectTab.charAt(0).toUpperCase()+projectTab.slice(1),question:'Project workspace context'}} project={project} onArkana={()=>setArkana(true)} onPrism={leavePrism}/><div className="solspire-project-heading"><div><span className="solspire-lens-sigil" style={{color:'#C9A84C'}}>◈</span><div><div className="solspire-kicker">PROJECT WORKSPACE</div><h1>{project.name}</h1></div></div><div className="solspire-project-heading-meta">{projectTab.toUpperCase()}</div></div><div className="solspire-divider"/><ResilientProjectDashboard key={`${project.id}:${projectTab}`} project={project} initialTab={projectTab} onBack={()=>{setProject(null);setProjectTab('overview');setSection('projects')}} onProjectUpdated={setProject}/></main>{search&&<SearchOverlay onClose={()=>setSearch(false)} project={project}/>} {arkana&&<ArkanaOverlay context={context} pack={{authenticated:true,surface:project?`project:${projectTab}`:`lens:${section}`,projectName:project?.name||null,projectId:project?.id||null}} onClose={()=>setArkana(false)}/>} {more&&<div className="solspire-mobile-menu">{NAV.map(n=><button key={n.id} onClick={()=>{selectSection(n.id);setMore(false)}}>{n.sigil} <span>{n.label}</span><small>{n.question}</small></button>)}{NETWORK.map(n=><button key={n.view} onClick={()=>navigateGlobal(n.view)}>{n.sigil} <span>{n.label}</span><small>{n.sub}</small></button>)}</div>}<MobileNav section={section} onSection={selectSection}/></div>;
  return <div className="solspire-workspace solariun-canvas" data-solariun-zoom="field" data-solariun-surface="field" role="application" aria-label="Solariun field canvas"><GlobalDoors onNavigate={navigateGlobal}/><Header identity={identity} onSearch={()=>setSearch(true)} onArkana={()=>setArkana(true)} onMenu={()=>setMore(true)} onPrism={leavePrism}/><div className="solspire-body"><Sidebar section={section} onSection={selectSection}/><main className="solspire-main"><ContextBar lens={lens} onArkana={()=>setArkana(true)} onPrism={leavePrism}/><div className="solspire-lens-heading"><div><span className="solspire-lens-sigil" style={{color:lens.accent}}>{lens.sigil}</span><div><div className="solspire-kicker">{lens.question}</div><h1>{lens.label}</h1></div></div><div className="solspire-lens-actions"><button type="button" onClick={()=>setSearch(true)}>⌕ Search</button><button type="button" onClick={()=>setArkana(true)}>⌁ Arkana</button></div></div><div className="solspire-divider"/><section className="solspire-content" data-solariun-region="field" aria-label="Solariun field"><LensContent section={section} onOpenProject={openProject} onOpenWeaver={openWeaver} onOpenProjectTab={openProjectTab}/></section></main></div><MobileNav section={section} onSection={selectSection}/>{search&&<SearchOverlay onClose={()=>setSearch(false)} project={project}/>} {arkana&&<ArkanaOverlay context={context} pack={{authenticated:true,surface:project?`project:${projectTab}`:`lens:${section}`,projectName:project?.name||null,projectId:project?.id||null}} onClose={()=>setArkana(false)}/>} {more&&<div className="solspire-mobile-menu">{NAV.map(n=><button key={n.id} onClick={()=>{selectSection(n.id);setMore(false)}}>{n.sigil} <span>{n.label}</span><small>{n.question}</small></button>)}{NETWORK.map(n=><button key={n.view} onClick={()=>navigateGlobal(n.view)}>{n.sigil} <span>{n.label}</span><small>{n.sub}</small></button>)}</div>}</div>;

}
