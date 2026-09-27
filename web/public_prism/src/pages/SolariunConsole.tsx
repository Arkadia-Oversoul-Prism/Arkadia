/** Solariun Console: personal intelligence canvas. */
import React,{useLayoutEffect} from 'react';
import {useAuth} from '../contexts/AuthContext';
import {setApiAuthToken} from '../lib/apiClient';
import SolSpireExperience,{SolSpireLens} from '../components/solspire/SolSpireExperience';

type AppView='home'|'gate'|'commune'|'reset'|'about'|'login'|'codex'|'dashboard'|'nexus'|'encyclopedia'|'spiral-codex'|'loops'|'grove'|'larder'|'novanet'|'ims'|'distribute'|'offerings'|'aic'|'pulse'|'settings'|'account'|'sci'|'solariun'|'solspire'|'knowledge-os'|'reasomate'|'personal-echofeild'|'echofeild-matrix';
type LegacySection=SolSpireLens|'field'|'codex'|'loops'|'projects'|'encyclopedia'|'goals'|'releases'|'jobs'|'traces'|'tools'|'system';
const LEGACY_MAP:Record<string,SolSpireLens>={field:'overview',codex:'memory',loops:'tasks',projects:'projects',encyclopedia:'memory',goals:'overview',releases:'overview',jobs:'observatory',traces:'observatory',tools:'observatory',system:'settings'};
function identity(user:ReturnType<typeof useAuth>['user']){return user?.displayName?.trim()||(user?.email?user.email.split('@')[0]:'')||'Authenticated node'}
export default function SolariunConsole({onNavigate,initialSection='overview'}:{onNavigate?:(v:AppView)=>void;initialSection?:LegacySection}={}){const {isAuthenticated,user}=useAuth();useLayoutEffect(()=>{setApiAuthToken(user?.idToken??null)},[user?.idToken]);if(!isAuthenticated)return <div className="solspire-auth-threshold"><div className="solspire-auth-card"><div className="solspire-brand-name">SOLARIUN</div><div className="solspire-kicker">PERSONAL INTELLIGENCE CANVAS</div><p>Sign in to enter your personal workspace.</p><button type="button" onClick={()=>onNavigate?.('gate')}>Enter Solariun</button></div></div>;return <SolSpireExperience identity={identity(user)} initialSection={(LEGACY_MAP[initialSection]||initialSection) as SolSpireLens} onNavigate={onNavigate}/>}