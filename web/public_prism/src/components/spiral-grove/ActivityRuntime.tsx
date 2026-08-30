import React, { useEffect, useMemo, useState } from 'react'
import type { GroveLearningActivity, LearningActivityKind } from '../../data/spiralGroveCatalog'

const DRAFT_PREFIX = 'arkadia.spiral-grove.activity-runtime-draft.v1:'
const COMPLETE_PREFIX = 'arkadia.spiral-grove.activity-runtime-complete.v1:'
const STORAGE_VERSION = 1

type DraftRecord = { version: number; activity_id: string; activity_kind: LearningActivityKind; value: string; updated_at: string }
type CompletionRecord = { version: number; activity_id: string; completed: true; completed_at: string }

export interface ActivityRuntimeProps { activity: GroveLearningActivity }

function readDraft(key: string, activity: GroveLearningActivity): string {
  if (typeof window === 'undefined') return ''
  try {
    const raw = window.localStorage.getItem(key)
    if (!raw) return ''
    const record = JSON.parse(raw) as Partial<DraftRecord>
    if (record.version !== STORAGE_VERSION || record.activity_id !== activity.id || record.activity_kind !== activity.kind || typeof record.value !== 'string') return ''
    return record.value
  } catch { return '' }
}

function readCompletion(key: string, activity: GroveLearningActivity): boolean {
  if (typeof window === 'undefined') return false
  try {
    const raw = window.localStorage.getItem(key)
    if (!raw) return false
    const record = JSON.parse(raw) as Partial<CompletionRecord>
    return record.version === STORAGE_VERSION && record.activity_id === activity.id && record.completed === true && typeof record.completed_at === 'string'
  } catch { return false }
}

function writeDraft(key: string, activity: GroveLearningActivity, value: string): boolean {
  if (typeof window === 'undefined') return false
  try { const record: DraftRecord = { version: STORAGE_VERSION, activity_id: activity.id, activity_kind: activity.kind, value, updated_at: new Date().toISOString() }; window.localStorage.setItem(key, JSON.stringify(record)); return true } catch { return false }
}

function writeCompletion(key: string, activity: GroveLearningActivity): boolean {
  if (typeof window === 'undefined') return false
  try { const record: CompletionRecord = { version: STORAGE_VERSION, activity_id: activity.id, completed: true, completed_at: new Date().toISOString() }; window.localStorage.setItem(key, JSON.stringify(record)); return true } catch { return false }
}

function clearCompletion(key: string): boolean {
  if (typeof window === 'undefined') return false
  try { window.localStorage.removeItem(key); return true } catch { return false }
}

/**
 * SG-04 bounded learner-work runtime.
 * All activity kinds enter through this same runtime boundary. Renderers below
 * only change the learner-work surface; they cannot submit evidence, assess
 * work, or mutate learner capability state.
 */
export default function ActivityRuntime({ activity }: ActivityRuntimeProps) {
  const draftKey = useMemo(() => `${DRAFT_PREFIX}${activity.id}`, [activity.id])
  const completeKey = useMemo(() => `${COMPLETE_PREFIX}${activity.id}`, [activity.id])
  const [draft, setDraft] = useState('')
  const [saved, setSaved] = useState(false)
  const [completed, setCompleted] = useState(false)
  const [storageAvailable, setStorageAvailable] = useState(true)

  useEffect(() => {
    setDraft(readDraft(draftKey, activity))
    setCompleted(readCompletion(completeKey, activity))
    if (typeof window !== 'undefined') { try { const probe = `${DRAFT_PREFIX}__probe`; window.localStorage.setItem(probe, '1'); window.localStorage.removeItem(probe); setStorageAvailable(true) } catch { setStorageAvailable(false) } }
  }, [draftKey, completeKey, activity])

  const persistDraft = () => { const ok = writeDraft(draftKey, activity, draft); setSaved(ok); if (ok) window.setTimeout(() => setSaved(false), 1800) }
  const markLocalComplete = () => { if (!draft.trim()) return; const draftSaved = writeDraft(draftKey, activity, draft); const completionSaved = draftSaved && writeCompletion(completeKey, activity); if (completionSaved) setCompleted(true); setSaved(draftSaved) }
  const clearLocalCompletion = () => { if (clearCompletion(completeKey)) setCompleted(false) }

  return <div data-testid="activity-runtime" data-activity-kind={activity.kind} style={runtimeSurface}>
    <div data-testid="activity-runtime-header" style={header}>
      <div><p style={eyebrow}>SG-04 activity runtime · {activity.kind}</p><h3 style={title}>{activity.title}</h3></div>
      <span data-testid="activity-runtime-status" style={status}>{completed ? 'Local work complete' : 'In progress'}</span>
    </div>
    <p style={instruction}>{activity.instruction}</p>
    <div data-testid="activity-runtime-metadata" style={metadata}><span>{activity.estimated_minutes} min</span><span>Deliverable: {activity.deliverable}</span><span>{activity.evidence_required ? 'Evidence later' : 'Reflection only'}</span></div>
    <ActivityWorkSurface activity={activity} value={draft} onChange={setDraft} />
    <div style={actions}>
      <button type="button" onClick={persistDraft} disabled={!storageAvailable} data-testid="activity-runtime-save" style={primaryButton}>{!storageAvailable ? 'Local storage unavailable' : saved ? 'Saved locally ✓' : 'Save draft'}</button>
      {!completed ? <button type="button" onClick={markLocalComplete} disabled={!draft.trim() || !storageAvailable} data-testid="activity-runtime-complete" style={secondaryButton}>Mark work complete</button> : <button type="button" onClick={clearLocalCompletion} data-testid="activity-runtime-reopen" style={secondaryButton}>Reopen local work</button>}
      <span style={meta}>{draft.length} characters · local runtime state only</span>
    </div>
    <div data-testid="activity-runtime-boundary" style={boundary}><strong>Runtime boundary.</strong> Local draft and completion only. This does not submit evidence, perform assessment, or mutate learner capability state.</div>
  </div>
}

function ActivityWorkSurface({ activity, value, onChange }: { activity: GroveLearningActivity; value: string; onChange: (value: string) => void }) {
  const props = { value, onChange, label: activity.work_surface.prompt_label, placeholder: activity.work_surface.placeholder }
  switch (activity.kind) {
    case 'research': return <ResearchSurface {...props} />
    case 'writing': return <WritingSurface {...props} />
    case 'build': return <BuildSurface {...props} />
    case 'reflection': return <ReflectionSurface {...props} />
    case 'presentation': return <PresentationSurface {...props} />
    case 'field': return <FieldSurface {...props} />
    case 'creative': return <CreativeSurface {...props} />
    case 'collaborative': return <CollaborativeSurface {...props} />
    default: return assertNever(activity.kind)
  }
}

type SurfaceProps = { value: string; onChange: (value: string) => void; label: string; placeholder: string }
function Surface({ kind, value, onChange, label, placeholder, prompts }: SurfaceProps & { kind: LearningActivityKind; prompts: string[] }) { return <div data-testid={`activity-surface-${kind}`}><label htmlFor={`activity-runtime-draft-${kind}`} style={labelStyle}>{label}</label><div style={promptRow}>{prompts.map(prompt => <span key={prompt} style={promptChip}>{prompt}</span>)}</div><textarea id={`activity-runtime-draft-${kind}`} data-testid={`activity-${kind}-workspace`} value={value} onChange={event => onChange(event.target.value)} placeholder={placeholder} style={textarea} /></div> }
function ResearchSurface(p: SurfaceProps) { return <Surface {...p} kind="research" prompts={['Question','Sources','Claims','Synthesis']} /> }
function WritingSurface(p: SurfaceProps) { return <Surface {...p} kind="writing" prompts={['Draft','Structure','Revision']} /> }
function BuildSurface(p: SurfaceProps) { return <Surface {...p} kind="build" prompts={['Goal','Steps','Decisions','Test']} /> }
function ReflectionSurface(p: SurfaceProps) { return <Surface {...p} kind="reflection" prompts={['Notice','Interpret','Change','Next']} /> }
function PresentationSurface(p: SurfaceProps) { return <Surface {...p} kind="presentation" prompts={['Opening','Key points','Evidence','Closing']} /> }
function FieldSurface(p: SurfaceProps) { return <Surface {...p} kind="field" prompts={['Where','When','Observe','Infer']} /> }
function CreativeSurface(p: SurfaceProps) { return <Surface {...p} kind="creative" prompts={['Concept','Audience','Iteration','Artifact']} /> }
function CollaborativeSurface(p: SurfaceProps) { return <Surface {...p} kind="collaborative" prompts={['Roles','Decisions','Contributions','Open questions']} /> }
function assertNever(value: never): never { throw new Error(`Unsupported learning activity kind: ${String(value)}`) }

const C = { teal: '#00D4AA', text: 'rgba(232,232,232,0.90)', muted: 'rgba(232,232,232,0.58)', dim: 'rgba(232,232,232,0.34)' }
const runtimeSurface: React.CSSProperties = { marginTop: 14, padding: 16, borderRadius: 11, background: 'rgba(0,212,170,.035)', border: '1px solid rgba(0,212,170,.18)' }
const header: React.CSSProperties = { display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', gap: 12 }
const eyebrow: React.CSSProperties = { fontFamily: 'sans-serif', fontSize: 8, letterSpacing: '.18em', textTransform: 'uppercase', color: C.teal, margin: '0 0 7px' }
const title: React.CSSProperties = { fontFamily: 'serif', fontWeight: 400, fontSize: 20, color: C.text, margin: '0 0 6px' }
const status: React.CSSProperties = { fontFamily: 'sans-serif', fontSize: 8, color: C.teal, textTransform: 'uppercase', letterSpacing: '.08em' }
const instruction: React.CSSProperties = { fontFamily: 'sans-serif', fontSize: 11, lineHeight: 1.65, color: C.muted, margin: 0 }
const metadata: React.CSSProperties = { display: 'flex', flexWrap: 'wrap', gap: 12, marginTop: 10, fontFamily: 'sans-serif', fontSize: 8, color: C.dim, textTransform: 'uppercase', letterSpacing: '.07em' }
const labelStyle: React.CSSProperties = { display: 'block', marginTop: 14, fontFamily: 'sans-serif', fontSize: 9, color: C.text, letterSpacing: '.08em' }
const promptRow: React.CSSProperties = { display: 'flex', flexWrap: 'wrap', gap: 5, marginTop: 7 }
const promptChip: React.CSSProperties = { padding: '4px 7px', borderRadius: 6, background: 'rgba(255,255,255,.025)', border: '1px solid rgba(255,255,255,.06)', color: C.dim, fontFamily: 'sans-serif', fontSize: 7, textTransform: 'uppercase', letterSpacing: '.07em' }
const textarea: React.CSSProperties = { boxSizing: 'border-box', width: '100%', minHeight: 190, marginTop: 7, padding: 12, resize: 'vertical', borderRadius: 9, border: '1px solid rgba(255,255,255,.10)', background: 'rgba(0,0,0,.18)', color: C.text, outline: 'none', fontFamily: 'sans-serif', fontSize: 11, lineHeight: 1.7 }
const actions: React.CSSProperties = { display: 'flex', alignItems: 'center', gap: 10, flexWrap: 'wrap', marginTop: 10 }
const primaryButton: React.CSSProperties = { padding: '9px 13px', borderRadius: 8, cursor: 'pointer', background: 'rgba(0,212,170,.10)', border: '1px solid rgba(0,212,170,.28)', color: C.teal, fontFamily: 'sans-serif', fontSize: 9, letterSpacing: '.08em' }
const secondaryButton: React.CSSProperties = { padding: '9px 13px', borderRadius: 8, cursor: 'pointer', background: 'rgba(255,255,255,.025)', border: '1px solid rgba(255,255,255,.10)', color: C.text, fontFamily: 'sans-serif', fontSize: 9, letterSpacing: '.06em' }
const meta: React.CSSProperties = { fontFamily: 'sans-serif', fontSize: 8, lineHeight: 1.5, color: C.dim }
const boundary: React.CSSProperties = { marginTop: 12, padding: 10, borderRadius: 8, background: 'rgba(255,255,255,.018)', border: '1px solid rgba(255,255,255,.06)', color: C.dim, fontFamily: 'sans-serif', fontSize: 8, lineHeight: 1.55 }