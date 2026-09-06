import React, { useMemo, useState } from 'react';
import ArkanaCommune from '../ArkanaCommune';
import ProjectDashboard, { Project } from '../../pages/ProjectDashboard';
import Overview from '../../pages/dashboard/Overview';
import KnowledgeOSPage from '../../pages/knowledge/KnowledgeOSPage';
import SettingsPage from '../../pages/SettingsPage';
import { CommercialPanel, Observatory, WeaverSummary, WorkspaceCollection, WorkspaceFiles } from '../../pages/SolSpireWorkspacePanels';
import type { WorkspaceCollectionKind } from '../../pages/SolSpireWorkspacePanels';

export type SolSpireLens = 'overview'|'commercial'|'knowledge'|'files'|'conversations'|'tasks'|'memory'|'weaver'|'observatory'|'settings';

type NavItem = { id: SolSpireLens; label: string; sigil: string; accent: string; question: string };
const NAV: NavItem[] = [
  {id:'overview',label:'Overview',sigil:'◎',accent:'#6A9FD8',question:'What matters now?'},
  {id:'commercial',label:'Commercial',sigil:'◈',accent:'#C9A84C',question:'Where is value emerging?'},
  {id:'knowledge',label:'Knowledge',sigil:'◉',accent:'#00D4AA',question:'What does the system know?'},
  {id:'files',label:'Files',sigil:'◫',accent:'#C9A84C',question:'What exists?'},
  {id:'conversations',label:'Conversations',sigil:'◌',accent:'#6A9FD8',question:'What am I thinking through?'},
  {id:'tasks',label:'Tasks',sigil:'□',accent:'#00D4AA',question:'What commitments are active?'},
  {id:'memory',label:'Memory',sigil:'∞',accent:'#B08DE8',question:'What persists?'},
  {id:'weaver',label:'Weaver',sigil:'⚒',accent:'#B08DE8',question:'What is being worked on?'},
  {id:'observatory',label:'Observatory',sigil:'⟐',accent:'#6A9FD8',question:'What happened?'},
  {id:'settings',label:'Settings',sigil:'◆',accent:'#9A9AA2',question:'How does the environment behave?'},
];

export type SolSpireObject = { id:string; type:string; title:string; summary?:string; status?:string; projectId?:string; source?:string; updatedAt?:string|number };
export type SolSpireRelation = { type:'CONNECTED TO'|'DERIVED FROM'|'REFERENCES'|'BELONGS TO'|'FOLLOW-UP FOR'|'GENERATED FROM'; sourceId:string; targetId:string };

export function ObjectCard({object, accent='#C9A84C', onOpen}:{object:SolSpireObject; accent?:string; onOpen?:()=>void}) {
  return <article className="solspire-object" onClick={onOpen} role={onOpen?'button':undefined} tabIndex={onOpen?0:undefined} onKeyDown={e=>{if(onOpen&&(e.key==='Enter'||e.key===' '))onOpen()}}>
    <div className="solspire-kicker" style={{color:`${accent}aa`}}>{object.type}</div>
    <h3 className="solspire-title">{object.title}</h3>
    {object.summary&&<p className="solspire-object-summary">{object.summary}</p>}
    <div className="solspire-object-meta"><span>{object.status||'ACTIVE'}</span>{object.projectId&&<span>{object.projectId}</span>}</div>
    <div className="solspire-id">{object.id}</div>
  </article>;
}

export function RelationChip({relation, label}:{relation:SolSpireRelation; label?:string}) {
  return <span className="solspire-relation" title={`${relation.type} ${relation.targetId}`}>{relation.type}{label?` · ${label}`:''}</span>;
}

export function ActivityItem({type,title,context,time,id}:{type:string;title:string;context?:string;time?:string;id?:string}) {
  return <div className="solspire-activity-item"><span className="solspire-activity-dot"/><div><div className="solspire-kicker">{type}</div><div className="solspire-activity-title">{title}</div>{context&&<div className="solspire-activity-context">{context}</div>}</div><div className="solspire-activity-time">{time||''}{id&&<small>{id}</small>}</div></div>;
}

function Header({identity,onSearch,onArkana}:{identity:string;onSearch:()=>void;onArkana:()=>void}) {
  return <header className="solspire-canonical-header"><div className="solspire-brand"><span className="solspire-mark">◈</span><div><div className="solspire-brand-name">SOLSPIRE</div><div className="solspire-brand-sub">private contextual workspace</div></div></div><div className="solspire-header-actions"><button type="button" className="solspire-quiet-button" onClick={onSearch}>⌕ <span>Search</span></button><button type="button" className="solspire-arkana-button" onClick={onArkana}>⌁ Ask Arkana</button><div className="solspire-identity"><span className="solspire-online-dot"/>{identity}</div></div></header>;
}

function MobileNav({section,onSection}:{section:SolSpireLens;onSection:(s:SolSpireLens)=>void}) {
  return <nav className="solspire-mobile-bottom">{NAV.slice(0,5).map(n=><button key={n.id} type="button" className={section===n.id?'active':''} onClick={()=>onSection(n.id)}><span>{n.sigil}</span><small>{n.label}</small></button>)}</nav>;
}

function Sidebar({section,onSection}:{section:SolSpireLens;onSection:(s:SolSpireLens)=>void}) {
  return <aside className="solspire-sidebar"><div className="solspire-sidebar-intro"><span className="solspire-online-dot"/><span>AUTHENTICATED FIELD</span><small>one surface · private</small></div>{NAV.map(n=><button key={n.id} type="button" className={`solspire-nav-button ${section===n.id?'active':''}`} style={{'--lens-accent':n.accent} as React.CSSProperties} onClick={()=>onSection(n.id)}><span>{n.sigil}</span><div><strong>{n.label}</strong><small>{n.question}</small></div></button>)}</aside>;
}

function ContextBar({lens,project,onArkana}:{lens:NavItem;project?:Project|null;onArkana:()=>void}) {
  return <div className="solspire-context-bar"><div><span className="solspire-mono">SOLSPIRE / {lens.label.toUpperCase()}</span>{project&&<><span className="solspire-context-separator">/</span><strong>{project.name}</strong></>}</div><button type="button" onClick={onArkana}>⌁ Ask Arkana {project?'about this context':'about this workspace'}</button></div>;
}

function SearchOverlay({onClose}:{onClose:()=>void}) {
  return <div className="solspire-overlay" role="dialog" aria-modal="true"><div className="solspire-search-panel"><div className="solspire-overlay-head"><span className="solspire-kicker">Universal search</span><button type="button" onClick={onClose}>×</button></div><input autoFocus placeholder="Search files, knowledge, conversations, tasks, memory…" /><div className="solspire-search-hint">Knowledge OS semantic and full-text search remain the underlying search authorities.</div><div className="solspire-search-actions"><span>⌘K</span><span>ESC close</span></div></div></div>;
}

function ArkanaOverlay({context,onClose}:{context:string;onClose:()=>void}) {
  return <div className="solspire-overlay" role="dialog" aria-modal="true"><div className="solspire-arkana-panel"><div className="solspire-overlay-head"><div><div className="solspire-kicker">Contextual intelligence</div><h2>Ask Arkana</h2><p>{context}</p></div><button type="button" onClick={onClose}>×</button></div><ArkanaCommune initialMessage={`You are being invoked from SolSpire. Current workspace context: ${context}. Keep this context in view when interpreting the user's request. Do not imply autonomous authority; proposals remain subject to human decision.`}/></div></div>;
}

function LensContent({section,onOpenProject}:{section:SolSpireLens;onOpenProject:(p:Project)=>void}) {
  if(section==='overview') return <><Overview/><div className="solspire-attention-note"><div className="solspire-kicker">Experience grammar</div><h3>One field, many lenses.</h3><p>Projects, files, conversations, tasks, memory, knowledge and governed work remain existing capabilities. This lens is for situational awareness, not another dashboard kingdom.</p></div></>;
  if(section==='commercial') return <CommercialPanel/>;
  if(section==='knowledge') return <KnowledgeOSPage/>;
  if(section==='files') return <WorkspaceFiles onOpenProject={onOpenProject}/>;
  if(section==='conversations'||section==='tasks'||section==='memory') return <WorkspaceCollection kind={section as WorkspaceCollectionKind}/>;
  if(section==='weaver') return <WeaverSummary onOpenProject={onOpenProject}/>;
  if(section==='observatory') return <Observatory/>;
  return <SettingsPage/>;
}

export default function SolSpireExperience({identity='Authenticated node',initialSection='overview',onExit}:{identity?:string;initialSection?:SolSpireLens;onExit?:()=>void}) {
  const [section,setSection]=useState<SolSpireLens>(initialSection);
  const [project,setProject]=useState<Project|null>(null);
  const [search,setSearch]=useState(false);
  const [arkana,setArkana]=useState(false);
  const lens=useMemo(()=>NAV.find(n=>n.id===section)||NAV[0],[section]);
  const context=project?`${project.name} project context · files, conversations, tasks, memory, knowledge and governed Weaver work`:`${lens.label} lens · authenticated SolSpire workspace state`;

  if(project) return <div className="solspire-workspace"><Header identity={identity} onSearch={()=>setSearch(true)} onArkana={()=>setArkana(true)}/><div className="solspire-project-context"><button type="button" onClick={()=>setProject(null)}>← Files</button><div><span className="solspire-kicker">PROJECT CONTEXT</span><strong>{project.name}</strong></div><span className="solspire-mono">same SolSpire · deeper context</span></div><ProjectDashboard project={project} onBack={()=>setProject(null)} onProjectUpdated={setProject}/>{search&&<SearchOverlay onClose={()=>setSearch(false)}/>} {arkana&&<ArkanaOverlay context={context} onClose={()=>setArkana(false)}/>}</div>;

  return <div className="solspire-workspace"><Header identity={identity} onSearch={()=>setSearch(true)} onArkana={()=>setArkana(true)}/><div className="solspire-body"><Sidebar section={section} onSection={setSection}/><main className="solspire-main"><ContextBar lens={lens} onArkana={()=>setArkana(true)}/><div className="solspire-lens-heading"><div><span className="solspire-lens-sigil" style={{color:lens.accent}}>{lens.sigil}</span><div><div className="solspire-kicker">{lens.question}</div><h1>{lens.label}</h1></div></div><div className="solspire-lens-actions"><button type="button" onClick={()=>setSearch(true)}>⌕ Search</button><button type="button" onClick={()=>setArkana(true)}>⌁ Arkana</button></div></div><div className="solspire-divider"/><section className="solspire-content"><LensContent section={section} onOpenProject={setProject}/></section></main></div><MobileNav section={section} onSection={setSection}/>{search&&<SearchOverlay onClose={()=>setSearch(false)}/>} {arkana&&<ArkanaOverlay context={context} onClose={()=>setArkana(false)}/>}</div>;
}
