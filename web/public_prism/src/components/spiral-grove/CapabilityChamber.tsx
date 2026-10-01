import React, { useEffect, useState } from 'react'
import { motion } from 'framer-motion'
import type { GroveCapability, GroveLearningActivity, GroveLearningPathActivityProjection, GroveLearningPathProjection, LearnerCapabilityState } from '../../data/spiralGroveCatalog'

const C = { teal: '#00D4AA', text: 'rgba(232,232,232,0.90)', muted: 'rgba(232,232,232,0.58)', dim: 'rgba(232,232,232,0.34)' }
const ACTIVITY_DRAFT_PREFIX = 'arkadia.spiral-grove.activity-draft.v1:'
const EVIDENCE_KEY_PREFIX = 'arkadia.spiral-grove.evidence.v1:'
const FALLBACK_SURFACE = { mode: 'notes' as const, prompt_label: 'Your work', placeholder: 'Start your work here…', artifact_type: 'draft' }
interface Props { capability: GroveCapability; state: LearnerCapabilityState; prerequisites: GroveCapability[]; learningPath: GroveLearningPathProjection | null; activities: GroveLearningPathActivityProjection | null; onBack: () => void; onOpenCapability: (capabilityId: string) => void }
interface EvidenceSubmission { version: 1; activityId: string; capabilityId: string; pathId: string; summary: string; artifactRef: string; submittedAt: string }

export default function CapabilityChamber({ capability, state, prerequisites, learningPath, activities, onBack, onOpenCapability }: Props) {
  const pathIds = Array.isArray(learningPath?.capability_ids) ? learningPath.capability_ids : []
  const nextId = learningPath?.next_capability_id
  const nextCapability = nextId ? [capability, ...prerequisites].find(item => item.id === nextId) : undefined
  const activity = activities?.activities?.[0] ?? null
  const [activityOpen, setActivityOpen] = useState(false)
  return <motion.section initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} data-testid="capability-chamber" style={shell}>
    <div style={topbar}><button type="button" onClick={onBack} style={buttonStyle}>← Return to capability map</button><span style={badge}>Capability Chamber · L{capability.level}</span></div>
    <div style={{ padding: 22 }}>
      <p style={eyebrow}>Enter chamber</p><h2 style={heading}>{capability.name}</h2><p style={description}>{capability.description}</p>
      <div style={grid}>
        <Panel title="What this capability means"><p style={copy}>This capability is an A.I.S learning unit: a reusable human capability that can be developed, practiced, and eventually demonstrated. The chamber is for orientation and action, not passive content consumption.</p></Panel>
        <Panel title="Current learner state"><strong style={status}>{state.status.replaceAll('_', ' ')}</strong><p style={copy}>{state.next_recommended_action || 'Choose a practical next step.'}</p>{state.confidence !== null && <p style={meta}>Confidence: {Math.round(state.confidence * 100)}%</p>}</Panel>
        <Panel title="Prerequisites">{prerequisites.length ? prerequisites.map(item => <button key={item.id} type="button" onClick={() => onOpenCapability(item.id)} data-testid={`prerequisite-${item.slug}`} style={pathButton}>{item.name}<span style={meta}>Level {item.level} · open chamber →</span></button>) : <p style={copy}>No prerequisite capabilities. This is an entry point.</p>}</Panel>
        <Panel title="Knowledge OS sources"><p style={copy}>Knowledge OS remains the canonical, source-backed knowledge authority for this capability.</p><span style={meta}>SOURCE RETRIEVAL / PROJECTION → KNOWLEDGE OS</span></Panel>
      </div>
      <div data-testid="learning-path-panel" style={pathPanel}>
        <p style={eyebrow}>Your next move</p>
        {learningPath ? <><p style={pathReason}>{learningPath.reason}</p><div data-testid="learning-path-steps" style={{ display: 'grid', gap: 7, marginTop: 12 }}>{pathIds.map((id, index) => { const item = [capability, ...prerequisites].find(candidate => candidate.id === id); if (!item) return null; const isCurrent = id === capability.id; const isNext = id === nextId; return <div key={id} style={row}><span aria-hidden="true" style={step}>{index + 1}</span><button type="button" onClick={() => onOpenCapability(id)} data-testid={`path-step-${item.slug}`} style={{ ...pathButton, padding: '7px 9px', border: isCurrent ? '1px solid rgba(0,212,170,.18)' : '1px solid rgba(255,255,255,.05)' }}><span style={{ color: isCurrent || isNext ? C.teal : C.text }}>{item.name}</span><span style={meta}>{isCurrent ? 'Current chamber' : isNext ? 'Recommended next' : 'Prerequisite context'}</span></button>{isNext && <span style={nextLabel}>Next</span>}</div>})}</div>
          {nextCapability && <button type="button" onClick={() => onOpenCapability(nextCapability.id)} data-testid="next-capability" style={nextButton}>Continue to {nextCapability.name} →</button>}
          {activity && <ActivityCard activity={activity} pathId={learningPath.id} capabilityId={capability.id} open={activityOpen} onOpen={() => setActivityOpen(true)} onClose={() => setActivityOpen(false)} />}
          <p style={boundary}>SG-03 activity contract · local work/progress only. It does not change your learner capability state. Evidence submission, assessment, and capability-state mutation remain explicit downstream stages.</p>
          <p data-testid="sg03-contract-boundary" style={boundary}>SG-03 activity contract: local work/progress only. It does not mutate learner capability state. Evidence submission, assessment, and capability-state updates remain separate explicit downstream stages.</p>
        </> : <p style={copy}>No learning path is available for this learner state.</p>}
      </div>
    </div>
  </motion.section>
}

function ActivityCard({ activity, pathId, capabilityId, open, onOpen, onClose }: { activity: GroveLearningActivity; pathId: string; capabilityId: string; open: boolean; onOpen: () => void; onClose: () => void }) {
  const key = `${ACTIVITY_DRAFT_PREFIX}${activity.id}`
  const evidenceKey = `${EVIDENCE_KEY_PREFIX}${activity.id}`
  const [draft, setDraft] = useState('')
  const [saved, setSaved] = useState(false)
  const [evidenceOpen, setEvidenceOpen] = useState(false)
  const [evidenceSummary, setEvidenceSummary] = useState('')
  const [artifactRef, setArtifactRef] = useState('')
  const [submitted, setSubmitted] = useState(false)
  useEffect(() => { if (typeof window === 'undefined') return; try { setDraft(window.localStorage.getItem(key) || ''); const stored = window.sessionStorage.getItem(evidenceKey); if (stored) { const parsed = JSON.parse(stored) as Partial<EvidenceSubmission>; setEvidenceSummary(typeof parsed.summary === 'string' ? parsed.summary : ''); setArtifactRef(typeof parsed.artifactRef === 'string' ? parsed.artifactRef : ''); setSubmitted(Boolean(parsed.submittedAt)) } } catch {} }, [key, evidenceKey])
  const saveDraft = () => { if (typeof window === 'undefined') return; try { window.localStorage.setItem(key, draft); setSaved(true); window.setTimeout(() => setSaved(false), 1800) } catch {} }
  const submitEvidence = () => { if (typeof window === 'undefined' || !activity.evidence_required || !evidenceSummary.trim()) return; const submission: EvidenceSubmission = { version: 1, activityId: activity.id, capabilityId, pathId, summary: evidenceSummary.trim(), artifactRef: artifactRef.trim(), submittedAt: new Date().toISOString() }; try { window.sessionStorage.setItem(evidenceKey, JSON.stringify(submission)); setSubmitted(true); setEvidenceOpen(false) } catch {} }
  const surface = activity.work_surface ?? FALLBACK_SURFACE
  if (!open) return <div data-testid="learning-activity" style={activityCard}><div style={{ display: 'flex', justifyContent: 'space-between', gap: 10, alignItems: 'center' }}><span style={eyebrow}>Learning activity</span><span style={activityType}>{activity.kind}</span></div><h3 style={activityTitle}>{activity.title}</h3><p style={activityInstruction}>{activity.instruction}</p><div style={activityMeta}><span>{activity.estimated_minutes} min</span><span>{activity.deliverable}</span><span>{activity.evidence_required ? 'Evidence required' : 'Reflection only'}</span></div><button type="button" onClick={onOpen} data-testid="activity-action" style={actionButton}>Open {surface.mode.replaceAll('_', ' ')} surface →</button></div>
  return <div data-testid="learning-activity-work-surface" style={workSurface}><div style={workHeader}><div><p style={eyebrow}>{surface.mode.replaceAll('_', ' ')} surface</p><h3 style={activityTitle}>{activity.title}</h3></div><button type="button" onClick={onClose} style={buttonStyle}>Close</button></div><p style={activityInstruction}>{activity.instruction}</p><div style={surfaceMeta}><span>Deliverable: {activity.deliverable}</span><span>Tools: {activity.tools.join(' · ')}</span><span>Artifact: {surface.artifact_type}</span></div><label style={label} htmlFor="activity-draft">{surface.prompt_label}</label><textarea id="activity-draft" data-testid="activity-draft" value={draft} onChange={event => setDraft(event.target.value)} placeholder={surface.placeholder} style={textarea} /><div style={workActions}><button type="button" onClick={saveDraft} data-testid="save-activity-draft" style={saveButton}>{saved ? 'Saved locally ✓' : 'Save draft'}</button><span style={meta}>{draft.length} characters · local progress only</span></div>{activity.evidence_required && <EvidenceCapture open={evidenceOpen} submitted={submitted} summary={evidenceSummary} artifactRef={artifactRef} onOpen={() => setEvidenceOpen(true)} onClose={() => setEvidenceOpen(false)} onSummary={setEvidenceSummary} onArtifactRef={setArtifactRef} onSubmit={submitEvidence} />}</div>
}

function EvidenceCapture({ open, submitted, summary, artifactRef, onOpen, onClose, onSummary, onArtifactRef, onSubmit }: { open: boolean; submitted: boolean; summary: string; artifactRef: string; onOpen: () => void; onClose: () => void; onSummary: (value: string) => void; onArtifactRef: (value: string) => void; onSubmit: () => void }) {
  if (!open) return <div data-testid="evidence-capture" style={evidenceBoundary}><div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: 10 }}><div><strong style={{ color: C.text }}>{submitted ? 'Evidence captured' : 'Ready to prove the work?'}</strong><p style={{ margin: '4px 0 0', color: C.dim }}>Submit a concise proof record and optional artifact link. Submission is explicit and remains local until a later authenticated evidence service exists.</p></div><button type="button" onClick={onOpen} data-testid="open-evidence-capture" style={saveButton}>{submitted ? 'Review evidence' : 'Add evidence'}</button></div></div>
  return <div data-testid="evidence-capture-form" style={evidenceForm}><div style={workHeader}><div><p style={eyebrow}>Proof stage</p><h4 style={activityTitle}>Capture your evidence</h4></div><button type="button" onClick={onClose} style={buttonStyle}>Close</button></div><p style={activityInstruction}>Describe what you actually demonstrated. Keep the claim grounded in the work you can show.</p><label style={label} htmlFor="evidence-summary">Evidence summary</label><textarea id="evidence-summary" data-testid="evidence-summary" value={summary} onChange={event => onSummary(event.target.value)} placeholder="What did you make, do, test, or demonstrate?" style={textareaSmall} /><label style={label} htmlFor="evidence-artifact-ref">Artifact or proof link (optional)</label><input id="evidence-artifact-ref" data-testid="evidence-artifact-ref" value={artifactRef} onChange={event => onArtifactRef(event.target.value)} placeholder="https://… or a local reference" style={inputStyle} /><div style={workActions}><button type="button" disabled={!summary.trim()} onClick={onSubmit} data-testid="submit-evidence" style={{ ...saveButton, opacity: summary.trim() ? 1 : .45, cursor: summary.trim() ? 'pointer' : 'not-allowed' }}>{submitted ? 'Update evidence' : 'Submit evidence'}</button><span style={meta}>Explicit proof record · no learner-state mutation</span></div></div>
}

const shell: React.CSSProperties = { border: '1px solid rgba(0,212,170,.20)', borderRadius: 18, background: 'linear-gradient(145deg, rgba(10,18,28,.96), rgba(7,10,18,.94))', overflow: 'hidden' }
const topbar: React.CSSProperties = { padding: '12px 16px', borderBottom: '1px solid rgba(255,255,255,.06)', display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: 12 }
const buttonStyle: React.CSSProperties = { background: 'transparent', border: 0, color: C.muted, cursor: 'pointer', fontFamily: 'sans-serif', fontSize: 9, letterSpacing: '.14em', textTransform: 'uppercase' }
const badge: React.CSSProperties = { fontFamily: 'sans-serif', fontSize: 8, color: C.teal, letterSpacing: '.18em', textTransform: 'uppercase' }
const eyebrow: React.CSSProperties = { fontFamily: 'sans-serif', fontSize: 8, letterSpacing: '.22em', textTransform: 'uppercase', color: C.teal, margin: '0 0 7px' }
const heading: React.CSSProperties = { fontFamily: 'serif', fontWeight: 400, fontSize: 28, color: C.text, margin: '0 0 9px' }
const description: React.CSSProperties = { fontFamily: 'sans-serif', fontSize: 12, lineHeight: 1.75, color: C.muted, maxWidth: 760, margin: 0 }
const grid: React.CSSProperties = { display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(190px, 1fr))', gap: 10, marginTop: 20 }
const copy: React.CSSProperties = { fontFamily: 'sans-serif', fontSize: 10, lineHeight: 1.65, color: C.muted, margin: '7px 0 0' }
const meta: React.CSSProperties = { display: 'block', fontFamily: 'sans-serif', fontSize: 8, lineHeight: 1.5, color: C.dim, margin: '4px 0 0' }
const status: React.CSSProperties = { fontFamily: 'sans-serif', fontSize: 12, color: C.teal }
const pathPanel: React.CSSProperties = { marginTop: 14, padding: 16, borderRadius: 12, background: 'rgba(0,212,170,.045)', border: '1px solid rgba(0,212,170,.15)' }
const pathReason: React.CSSProperties = { fontFamily: 'sans-serif', fontSize: 12, lineHeight: 1.65, color: C.text, margin: 0 }
const pathButton: React.CSSProperties = { width: '100%', textAlign: 'left', background: 'rgba(255,255,255,.018)', borderRadius: 8, padding: '8px 9px', cursor: 'pointer', color: C.text, fontFamily: 'sans-serif', fontSize: 9 }
const row: React.CSSProperties = { display: 'grid', gridTemplateColumns: '28px 1fr auto', gap: 9, alignItems: 'center' }
const step: React.CSSProperties = { width: 24, height: 24, display: 'grid', placeItems: 'center', borderRadius: 7, border: '1px solid rgba(255,255,255,.09)', color: C.dim, fontFamily: 'sans-serif', fontSize: 8 }
const nextLabel: React.CSSProperties = { fontFamily: 'sans-serif', fontSize: 8, color: C.teal, textTransform: 'uppercase', letterSpacing: '.1em' }
const nextButton: React.CSSProperties = { marginTop: 13, width: '100%', padding: '11px 13px', borderRadius: 9, cursor: 'pointer', background: 'rgba(0,212,170,.08)', border: '1px solid rgba(0,212,170,.24)', color: C.teal, fontFamily: 'sans-serif', fontSize: 10, letterSpacing: '.08em', textAlign: 'left' }
const activityCard: React.CSSProperties = { marginTop: 14, padding: 15, borderRadius: 11, background: 'rgba(255,255,255,.025)', border: '1px solid rgba(255,255,255,.09)' }
const activityType: React.CSSProperties = { fontFamily: 'sans-serif', fontSize: 8, color: C.dim, textTransform: 'uppercase', letterSpacing: '.13em' }
const activityTitle: React.CSSProperties = { fontFamily: 'serif', fontWeight: 400, fontSize: 20, color: C.text, margin: '5px 0 6px' }
const activityInstruction: React.CSSProperties = { fontFamily: 'sans-serif', fontSize: 11, lineHeight: 1.65, color: C.muted, margin: 0 }
const activityMeta: React.CSSProperties = { display: 'flex', flexWrap: 'wrap', gap: 12, marginTop: 10, fontFamily: 'sans-serif', fontSize: 8, color: C.dim, textTransform: 'uppercase', letterSpacing: '.08em' }
const surfaceMeta: React.CSSProperties = { display: 'flex', flexDirection: 'column', gap: 4, marginTop: 12, fontFamily: 'sans-serif', fontSize: 8, lineHeight: 1.5, color: C.dim }
const actionButton: React.CSSProperties = { marginTop: 12, width: '100%', padding: '10px 11px', borderRadius: 8, cursor: 'pointer', background: 'rgba(0,212,170,.08)', border: '1px solid rgba(0,212,170,.24)', color: C.teal, fontFamily: 'sans-serif', fontSize: 9, letterSpacing: '.08em', textAlign: 'left' }
const workSurface: React.CSSProperties = { marginTop: 14, padding: 16, borderRadius: 11, background: 'rgba(0,212,170,.035)', border: '1px solid rgba(0,212,170,.18)' }
const workHeader: React.CSSProperties = { display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', gap: 12 }
const label: React.CSSProperties = { display: 'block', marginTop: 14, fontFamily: 'sans-serif', fontSize: 9, color: C.text, letterSpacing: '.08em' }
const textarea: React.CSSProperties = { boxSizing: 'border-box', width: '100%', minHeight: 170, marginTop: 7, padding: 12, resize: 'vertical', borderRadius: 9, border: '1px solid rgba(255,255,255,.10)', background: 'rgba(0,0,0,.18)', color: C.text, outline: 'none', fontFamily: 'sans-serif', fontSize: 11, lineHeight: 1.7 }
const textareaSmall: React.CSSProperties = { ...textarea, minHeight: 120 }
const inputStyle: React.CSSProperties = { boxSizing: 'border-box', width: '100%', marginTop: 7, padding: 12, borderRadius: 9, border: '1px solid rgba(255,255,255,.10)', background: 'rgba(0,0,0,.18)', color: C.text, outline: 'none', fontFamily: 'sans-serif', fontSize: 11 }
const workActions: React.CSSProperties = { display: 'flex', alignItems: 'center', gap: 10, flexWrap: 'wrap', marginTop: 10 }
const saveButton: React.CSSProperties = { padding: '9px 13px', borderRadius: 8, cursor: 'pointer', background: 'rgba(0,212,170,.10)', border: '1px solid rgba(0,212,170,.28)', color: C.teal, fontFamily: 'sans-serif', fontSize: 9, letterSpacing: '.08em' }
const evidenceBoundary: React.CSSProperties = { marginTop: 12, padding: 10, borderRadius: 8, background: 'rgba(255,255,255,.018)', border: '1px solid rgba(255,255,255,.06)', color: C.dim, fontFamily: 'sans-serif', fontSize: 8, lineHeight: 1.55 }
const evidenceForm: React.CSSProperties = { marginTop: 12, padding: 14, borderRadius: 9, background: 'rgba(201,168,76,.035)', border: '1px solid rgba(201,168,76,.16)' }
const boundary: React.CSSProperties = { marginTop: 12, fontFamily: 'sans-serif', fontSize: 8, lineHeight: 1.55, color: C.dim }
function Panel({ title, children }: { title: string; children: React.ReactNode }) { return <div style={{ padding: 14, borderRadius: 11, border: '1px solid rgba(255,255,255,.07)', background: 'rgba(255,255,255,.018)', minHeight: 118 }}><p style={{ fontFamily: 'sans-serif', fontSize: 8, letterSpacing: '.15em', textTransform: 'uppercase', color: C.dim, margin: 0 }}>{title}</p>{children}</div> }
