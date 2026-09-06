import React, { useEffect, useState } from 'react'
import { useAuth } from '../contexts/AuthContext'
import ReasoMateField from './ReasoMateField'
import MarkdownViewer from '../components/MarkdownViewer'
import { formatToArkadiaMarkdown } from '../lib/arkadiaFormatter'

const API_BASE = (import.meta.env.VITE_API_BASE_URL ?? '').replace(/\/$/, '')
const C = { teal:'#00D4AA', blue:'#6A9FD8', gold:'#C9A84C', red:'#C84848', text:'rgba(232,232,232,.9)', dim:'rgba(232,232,232,.35)', card:'rgba(14,17,32,.78)', border:'rgba(106,159,216,.14)' }

type Post = { id:string; owner_uid?:string; author:any; content:string; timestamp:number; edited_at?:number; reactions:any; comments:any[] }
const ago = (ts:number) => { const d=Date.now()-ts; if(d<60000)return'now'; if(d<3600000)return`${Math.floor(d/60000)}m`; if(d<86400000)return`${Math.floor(d/3600000)}h`; return`${Math.floor(d/86400000)}d` }
const btn = (color:string, disabled=false):React.CSSProperties => ({padding:'7px 11px',background:`${color}10`,border:`1px solid ${color}35`,borderRadius:8,color:disabled?C.dim:color,cursor:disabled?'not-allowed':'pointer',fontSize:9,letterSpacing:'.1em',textTransform:'uppercase'})

function Composer({ token, profile, onCreated }:{token:string;profile:any;onCreated:(p:Post)=>void}) {
  const [text,setText]=useState(''); const [busy,setBusy]=useState(false)
  const send=async()=>{ if(!text.trim()||busy)return; setBusy(true); try{const r=await fetch(`${API_BASE}/api/transmissions`,{method:'POST',headers:{'Content-Type':'application/json',Authorization:`Bearer ${token}`},body:JSON.stringify({content:formatToArkadiaMarkdown(text),author:{name:profile?.display_name||'Node',avatar:profile?.role_sigil||'◈',role:profile?.role||'Node'}})}); if(r.ok){const d=await r.json();onCreated(d.transmission);setText('')}}finally{setBusy(false)} }
  return <div style={{background:C.card,border:`1px solid ${C.border}`,borderRadius:12,padding:13,marginBottom:12}}><textarea value={text} onChange={e=>setText(e.target.value)} placeholder="Transmit something to the field…" rows={3} style={{width:'100%',boxSizing:'border-box',background:'rgba(0,0,0,.22)',border:'1px solid rgba(255,255,255,.07)',borderRadius:9,padding:10,color:C.text,resize:'vertical',outline:'none'}}/><div style={{display:'flex',justifyContent:'flex-end',marginTop:7}}><button onClick={send} disabled={!text.trim()||busy} style={btn(C.teal,!text.trim()||busy)}>{busy?'Transmitting…':'Transmit'}</button></div></div>
}

function PostCard({post,token,myUid,onChange}:{post:Post;token:string;myUid:string;onChange:(p:Post|null)=>void}) {
  const [editing,setEditing]=useState(false); const [draft,setDraft]=useState(post.content); const [busy,setBusy]=useState(false)
  const own=post.owner_uid===myUid
  const edit=async()=>{if(!draft.trim())return;setBusy(true);try{const r=await fetch(`${API_BASE}/api/transmissions/${post.id}`,{method:'PATCH',headers:{'Content-Type':'application/json',Authorization:`Bearer ${token}`},body:JSON.stringify({content:draft.trim()})});if(r.ok){const d=await r.json();onChange(d.transmission);setEditing(false)}}finally{setBusy(false)}}
  const remove=async()=>{if(!confirm('Delete this transmission?'))return;setBusy(true);try{const r=await fetch(`${API_BASE}/api/transmissions/${post.id}`,{method:'DELETE',headers:{Authorization:`Bearer ${token}`});if(r.ok)onChange(null)}finally{setBusy(false)}}
  return <article style={{background:C.card,border:`1px solid ${C.border}`,borderRadius:12,overflow:'hidden',marginBottom:10}}><div style={{padding:12,display:'flex',alignItems:'center',gap:9}}><div style={{width:34,height:34,borderRadius:'50%',display:'grid',placeItems:'center',background:'rgba(106,159,216,.1)',color:C.blue}}>{post.author?.avatar||'◈'}</div><div style={{flex:1}}><div style={{color:C.text,fontSize:12,fontWeight:600}}>{post.author?.name||'Node'}</div><div style={{color:C.dim,fontSize:9}}>{post.author?.role||'Node'} · {ago(post.timestamp)}{post.edited_at?' · edited':''}</div></div>{own&&<div style={{display:'flex',gap:5}}><button onClick={()=>{setDraft(post.content);setEditing(v=>!v)}} style={btn(C.blue)}>Edit</button><button onClick={remove} disabled={busy} style={btn(C.red,busy)}>Delete</button></div>}</div><div style={{padding:'0 13px 13px'}}>{editing?<><textarea value={draft} onChange={e=>setDraft(e.target.value)} rows={5} style={{width:'100%',boxSizing:'border-box',background:'rgba(0,0,0,.2)',border:`1px solid ${C.blue}30`,borderRadius:9,color:C.text,padding:10}}/><div style={{display:'flex',justifyContent:'flex-end',gap:5,marginTop:6}}><button onClick={()=>setEditing(false)} style={btn(C.dim)}>Cancel</button><button onClick={edit} disabled={busy} style={btn(C.teal,busy)}>Save</button></div></>:<MarkdownViewer content={post.content} compact/>}</div></article>
}

export default function GovernedSocialField(){
  const {isAuthenticated,profile,user}=useAuth(); const token=user?.idToken||''
  const [posts,setPosts]=useState<Post[]>([]); const [mode,setMode]=useState<'field'|'reasomate'>('field')
  useEffect(()=>{fetch(`${API_BASE}/api/transmissions`).then(r=>r.json()).then(d=>setPosts(d.transmissions||[])).catch(()=>{})},[])
  if(!isAuthenticated)return <div style={{padding:40,textAlign:'center',color:C.dim}}>Sign in to enter the Social Identity + ReasoMate Field.</div>
  return <div style={{minHeight:'calc(100vh - 80px)',color:C.text}}>
    <header style={{display:'flex',alignItems:'center',gap:10,marginBottom:14}}><span style={{color:C.blue,fontSize:20}}>◉</span><div><h2 style={{margin:0,fontFamily:'Cinzel,serif',fontSize:20}}>The Social Field</h2><div style={{color:C.dim,fontSize:9}}>One public identity · one governed relationship field</div></div><div style={{marginLeft:'auto',display:'flex',gap:5}}><button onClick={()=>setMode('field')} style={btn(mode==='field'?C.teal:C.dim)}>NovaNet</button><button onClick={()=>setMode('reasomate')} style={btn(mode==='reasomate'?C.blue:C.dim)}>ReasoMate</button></div></header>
    {mode==='field'?<div style={{maxWidth:720,margin:'0 auto'}}><Composer token={token} profile={profile} onCreated={p=>setPosts(v=>[p,...v])}/>{posts.map(p=><PostCard key={p.id} post={p} token={token} myUid={profile?.uid||''} onChange={next=>setPosts(v=>next?v.map(x=>x.id===next.id?next:x):v.filter(x=>x.id!==p.id))}/>)}</div>:<ReasoMateField/>}
    <footer style={{padding:'14px 0',color:C.dim,fontSize:9,textAlign:'center'}}>Public profile is the bridge. Private memory remains private. Shared relational context comes from the existing ReasoMate thread.</footer>
  </div>
}
