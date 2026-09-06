import { apiFetch } from '../lib/apiClient';
import { API_BASE } from '../lib/apiConfig';
import { useEffect, useMemo, useState } from 'react';
import { motion } from 'framer-motion';
import { useAuth } from '../contexts/AuthContext';
import LoginPage from './LoginPage';

interface NodeEntryProps { onEnterNovaNet: () => void; onGoToOfferings?: () => void; onBack?: () => void; onAICComplete?: (seed: any) => void; }
type AnswerMap = Record<string, string | number>;
type Node = 'source'|'spark'|'breath'|'flame'|'ground'|'life'|'harmony'|'seek'|'octave'|'return_node'|'witness'|'weaver';
const NODES: Node[] = ['source','spark','breath','flame','ground','life','harmony','seek','octave','return_node','witness','weaver'];
const LABEL: Record<Node,string> = {source:'Roots',spark:'Start',breath:'People',flame:'Make',ground:'Steady',life:'Change',harmony:'Balance',seek:'Learn',octave:'See again',return_node:'Finish',witness:'Notice',weaver:'Connect'};
const QUESTIONS = [
  ['01 · FIRST FEELING','Something new shows up. What do you want to do first?',[['Find out where it came from.',{source:3,seek:1}],['Try it.',{spark:3,life:1}],['See what it could become.',{flame:2,octave:1}],['Ask a question about it.',{seek:3,witness:1}]]],
  ['02 · AN IDEA','You get a big idea. What happens first?',[['Look at it until it makes sense.',{seek:2,witness:2}],['Tell someone about it.',{breath:2,weaver:2}],['Start making it.',{spark:2,flame:2}],['Join it to other ideas.',{weaver:2,flame:2}]]],
  ['03 · A HARD THING','Something does not make sense. What do you want most?',[['Know what is under it.',{seek:3,source:1}],['See what could be possible.',{spark:2,life:2}],['Make it clear and ordered.',{ground:3,harmony:1}],['See how the parts fit.',{weaver:3,breath:1}]]],
  ['04 · SOMETHING FEELS WRONG','You enter a room and something feels wrong. What do you notice?',[['A pattern.',{witness:3,seek:1}],['How people feel with each other.',{breath:3,harmony:1}],['What is not working.',{ground:2,return_node:1}],['Something nobody has said.',{source:1,witness:2,weaver:1}]]],
  ['05 · WHEN A PLAN BREAKS','A plan stops working. What do you do first?',[['See what changed.',{witness:2,octave:2}],['Try another way.',{life:3,spark:1}],['Put things back in order.',{ground:3,harmony:1}],['Go with what happens next.',{life:2,breath:1,spark:1}]]],
  ['06 · WHEN YOU CARE','You really care about an idea. What do you do?',[['Keep looking.',{seek:3,source:1}],['Give it a shape.',{flame:2,ground:2}],['Get it moving.',{spark:3,life:1}],['Find the people and things it needs.',{weaver:3,harmony:1}]]],
  ['07 · TALKING','A talk gets hard. What comes naturally?',[['Be quiet and watch.',{witness:3,breath:1}],['Hold more than one side.',{breath:3,harmony:1}],['Look for the real thing underneath.',{seek:2,source:2}],['Help people find the same thread.',{weaver:3,harmony:1}]]],
  ['08 · A NEW TURN','Life takes you somewhere you did not expect. What do you say inside?',[['What does this mean?',{octave:2,witness:2}],['What can we do with it?',{life:2,spark:2}],['Let us find something solid first.',{ground:3,source:1}],['Maybe this is where I need to go.',{breath:1,life:2,seek:1}]]],
  ['09 · FREE TIME','You have time and a problem on your mind. What do you do?',[['Look it up.',{seek:3,source:1}],['Draw or build something.',{flame:3,spark:1}],['Put the problem in order.',{ground:3,witness:1}],['Talk about it and see what comes out.',{breath:2,weaver:2}]]],
  ['10 · LOOKING BACK','You think about something from long ago. What pulls you?',[['What I see now that I could not see then.',{octave:3,witness:1}],['Where it started.',{source:3,return_node:1}],['What it became.',{flame:2,life:2}],['The links I missed before.',{weaver:3,octave:1}]]],
  ['11 · A GOOD MOMENT','Which moment feels best?',[['Something becomes clear.',{witness:2,seek:2}],['Something begins.',{spark:3,life:1}],['Pieces fit together.',{flame:2,weaver:2}],['I can see where it is going.',{octave:2,return_node:2}]]],
  ['12 · RIGHT NOW','What feels most like you today?',[['I want to understand.',{seek:2,witness:1,source:1}],['I am becoming.',{life:2,octave:1,spark:1}],['I want to make.',{flame:2,spark:2}],['I want to connect.',{weaver:3,harmony:1}]]],
] as const;
const DEEP = [
  ['d1','I notice things before I know why.', 'witness'],
  ['d2','I can tell when it is time to begin.', 'spark'],
  ['d3','I like joining separate ideas into one.', 'flame'],
  ['d4','I keep asking when there is still more to learn.', 'seek'],
  ['d5','I can change when life changes.', 'life'],
  ['d6','I connect people, ideas, and things.', 'weaver'],
] as const;
const SCALE = ['Not me','A little','Sometimes','Often','Very me'];
const PATTERNS = [
  {name:'Pattern Maker',nodes:['seek','witness','flame'],text:'You like to notice what is there, find what it means, and make something from it.'},
  {name:'First Mover',nodes:['spark','life','flame'],text:'You like to begin, try, change, and turn ideas into action.'},
  {name:'Connector',nodes:['weaver','harmony','breath'],text:'You notice people and parts, then help them work together.'},
  {name:'Deep Seeker',nodes:['source','seek','octave'],text:'You like to go deeper, find the roots, and look again.'},
  {name:'Steady Maker',nodes:['ground','flame','harmony'],text:'You like to turn ideas into things that are clear, useful, and steady.'},
  {name:'Quiet Noticer',nodes:['witness','breath','life'],text:'You notice, feel, learn, and move when the time is right.'},
];
const AIS_URL = `${API_BASE.replace(/\/$/,'')}/api/me/ais-profile`;
function sigilFor(value:string){const chars=['◈','✦','⬡','◇','✧','◉','⌬','⟐','✺','❖','✥','△'];let n=2166136261;for(let i=0;i<value.length;i++){n^=value.charCodeAt(i);n=Math.imul(n,16777619);}return chars[(n>>>0)%chars.length];}
function score(answers:AnswerMap){const raw=Object.fromEntries(NODES.map(n=>[n,0])) as Record<Node,number>;QUESTIONS.forEach(q=>{const choice=q[2].find(o=>o[0]===answers[q[0]]);if(choice)Object.entries(choice[1]).forEach(([n,w])=>raw[n as Node]+=Number(w));});DEEP.forEach(q=>{const v=Number(answers[q[0]]||0);if(v)raw[q[2] as Node]+=v;});const ranked=[...NODES].sort((a,b)=>raw[b]-raw[a]);const pattern=PATTERNS.map(p=>({...p,score:p.nodes.reduce((s,n)=>s+raw[n],0)})).sort((a,b)=>b.score-a.score)[0];return {raw,ranked,pattern,growth:ranked[ranked.length-1]};}

export default function NodeEntry({onEnterNovaNet,onGoToOfferings,onBack,onAICComplete}:NodeEntryProps){
 const {user,isAuthenticated,profile,loading,refreshProfile}=useAuth();
 const [stage,setStage]=useState<'auth'|'test'|'result'>(isAuthenticated?'test':'auth');
 const [checking,setChecking]=useState(false);const [index,setIndex]=useState(0);const [answers,setAnswers]=useState<AnswerMap>({});const [result,setResult]=useState<any>(null);const [saving,setSaving]=useState(false);