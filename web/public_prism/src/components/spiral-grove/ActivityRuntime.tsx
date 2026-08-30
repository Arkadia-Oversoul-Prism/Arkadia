import React, { useEffect, useMemo, useState } from 'react'
import type { GroveLearningActivity } from '../../data/spiralGroveCatalog'

const DRAFT_PREFIX = 'arkadia.spiral-grove.activity-runtime-draft.v1:'
const COMPLETE_PREFIX = 'arkadia.spiral-grove.activity-runtime-complete.v1:'

export interface ActivityRuntimeProps {
  activity: GroveLearningActivity
}

/**
 * SG-04 bounded learner-work runtime.
 *
 * Owns only local work state. It deliberately does not submit evidence,
 * assess work, call an autonomous exercise generator, or mutate learner
 * capability state.
 */
export default function ActivityRuntime({ activity }: ActivityRuntimeProps) {
  const draftKey = useMemo(() => `${DRAFT_PREFIX}${activity.id}`, [activity.id])
  const completeKey = useMemo(() => `${COMPLETE_PREFIX}${activity.id}`, [activity.id])
  const surface = activity.work_surface
  const [draft, setDraft] = useState('')
  const [saved, setSaved] = useState(false)
  const [completed, setCompleted] = useState(false)

  useEffect(() => {
    if (typeof window === 'undefined') return
    try {
      setDraft(window.localStorage.getItem(draftKey) || '')
      setCompleted(window.localStorage.getItem(completeKey) === 'true')
    } catch {}
  }, [draftKey, completeKey])

  const persistDraft = () => {
    if (typeof window === 'undefined') return
    try {
      window.localStorage.setItem(draftKey, draft)
      setSaved(true)
      window.setTimeout(() => setSaved(false), 1800)
    } catch {}
  }

  const markLocalComplete = () => {
    if (!draft.trim() || typeof window === 'undefined') return
    try {
      window.localStorage.setItem(draftKey, draft)
      window.localStorage.setItem(completeKey, 'true')
      setCompleted(true)
    } catch {}
  }

  const clearLocalCompletion = () => {
    if (typeof window === 'undefined') return
    try {
      window.localStorage.removeItem(completeKey)
      setCompleted(false)
    } catch {}
  }

  return (
    <div data-testid="activity-runtime" style={runtimeSurface}>
      <div data-testid="activity-runtime-header" style={header}>
        <div>
          <p style={eyebrow}>SG-04 activity runtime · {surface.mode.replaceAll('_', ' ')}</p>
          <h3 style={title}>{activity.title}</h3>
        </div>
        <span data-testid="activity-runtime-status" style={status}>{completed ? 'Local work complete' : 'In progress'}</span>
      </div>

      <p style={instruction}>{activity.instruction}</p>
      <div data-testid="activity-runtime-metadata" style={metadata}>
        <span>{activity.estimated_minutes} min</span>
        <span>Deliverable: {activity.deliverable}</span>
        <span>{activity.evidence_required ? 'Evidence later' : 'Reflection only'}</span>
      </div>

      <label htmlFor={`activity-runtime-draft-${activity.id}`} style={label}>{surface.prompt_label}</label>
      <textarea
        id={`activity-runtime-draft-${activity.id}`}
        data-testid="activity-runtime-draft"
        value={draft}
        onChange={event => setDraft(event.target.value)}
        placeholder={surface.placeholder}
        style={textarea}
      />

      <div style={actions}>
        <button type="button" onClick={persistDraft} data-testid="activity-runtime-save" style={primaryButton}>
          {saved ? 'Saved locally ✓' : 'Save draft'}
        </button>
        {!completed ? (
          <button type="button" onClick={markLocalComplete} disabled={!draft.trim()} data-testid="activity-runtime-complete" style={secondaryButton}>
            Mark work complete
          </button>
        ) : (
          <button type="button" onClick={clearLocalCompletion} data-testid="activity-runtime-reopen" style={secondaryButton}>
            Reopen local work
          </button>
        )}
        <span style={meta}>{draft.length} characters · local runtime state only</span>
      </div>

      <div data-testid="activity-runtime-boundary" style={boundary}>
        <strong>Runtime boundary.</strong> Local draft and completion only. This does not submit evidence, perform assessment, or mutate learner capability state.
      </div>
    </div>
  )
}

const C = { teal: '#00D4AA', text: 'rgba(232,232,232,0.90)', muted: 'rgba(232,232,232,0.58)', dim: 'rgba(232,232,232,0.34)' }
const runtimeSurface: React.CSSProperties = { marginTop: 14, padding: 16, borderRadius: 11, background: 'rgba(0,212,170,.035)', border: '1px solid rgba(0,212,170,.18)' }
const header: React.CSSProperties = { display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', gap: 12 }
const eyebrow: React.CSSProperties = { fontFamily: 'sans-serif', fontSize: 8, letterSpacing: '.18em', textTransform: 'uppercase', color: C.teal, margin: '0 0 7px' }
const title: React.CSSProperties = { fontFamily: 'serif', fontWeight: 400, fontSize: 20, color: C.text, margin: '0 0 6px' }
const status: React.CSSProperties = { fontFamily: 'sans-serif', fontSize: 8, color: C.teal, textTransform: 'uppercase', letterSpacing: '.08em' }
const instruction: React.CSSProperties = { fontFamily: 'sans-serif', fontSize: 11, lineHeight: 1.65, color: C.muted, margin: 0 }
const metadata: React.CSSProperties = { display: 'flex', flexWrap: 'wrap', gap: 12, marginTop: 10, fontFamily: 'sans-serif', fontSize: 8, color: C.dim, textTransform: 'uppercase', letterSpacing: '.07em' }
const label: React.CSSProperties = { display: 'block', marginTop: 14, fontFamily: 'sans-serif', fontSize: 9, color: C.text, letterSpacing: '.08em' }
const textarea: React.CSSProperties = { boxSizing: 'border-box', width: '100%', minHeight: 190, marginTop: 7, padding: 12, resize: 'vertical', borderRadius: 9, border: '1px solid rgba(255,255,255,.10)', background: 'rgba(0,0,0,.18)', color: C.text, outline: 'none', fontFamily: 'sans-serif', fontSize: 11, lineHeight: 1.7 }
const actions: React.CSSProperties = { display: 'flex', alignItems: 'center', gap: 10, flexWrap: 'wrap', marginTop: 10 }
const primaryButton: React.CSSProperties = { padding: '9px 13px', borderRadius: 8, cursor: 'pointer', background: 'rgba(0,212,170,.10)', border: '1px solid rgba(0,212,170,.28)', color: C.teal, fontFamily: 'sans-serif', fontSize: 9, letterSpacing: '.08em' }
const secondaryButton: React.CSSProperties = { padding: '9px 13px', borderRadius: 8, cursor: 'pointer', background: 'rgba(255,255,255,.025)', border: '1px solid rgba(255,255,255,.10)', color: C.text, fontFamily: 'sans-serif', fontSize: 9, letterSpacing: '.06em' }
const meta: React.CSSProperties = { fontFamily: 'sans-serif', fontSize: 8, lineHeight: 1.5, color: C.dim }
const boundary: React.CSSProperties = { marginTop: 12, padding: 10, borderRadius: 8, background: 'rgba(255,255,255,.018)', border: '1px solid rgba(255,255,255,.06)', color: C.dim, fontFamily: 'sans-serif', fontSize: 8, lineHeight: 1.55 }
