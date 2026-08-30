import React from 'react'
import { motion } from 'framer-motion'
import type { GroveCapability, GroveLearningPathProjection, LearnerCapabilityState } from '../../data/spiralGroveCatalog'

const C = {
  teal: '#00D4AA',
  text: 'rgba(232,232,232,0.90)',
  muted: 'rgba(232,232,232,0.58)',
  dim: 'rgba(232,232,232,0.34)',
}

interface CapabilityChamberProps {
  capability: GroveCapability
  state: LearnerCapabilityState
  prerequisites: GroveCapability[]
  learningPath: GroveLearningPathProjection | null
  onBack: () => void
}

export default function CapabilityChamber({ capability, state, prerequisites, learningPath, onBack }: CapabilityChamberProps) {
  const nextCapability = learningPath?.next_capability_id === capability.id ? capability : prerequisites.find(item => item.id === learningPath?.next_capability_id)

  return (
    <motion.section
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      data-testid="capability-chamber"
      style={{ border: '1px solid rgba(0,212,170,.20)', borderRadius: 18, background: 'linear-gradient(145deg, rgba(10,18,28,.96), rgba(7,10,18,.94))', overflow: 'hidden' }}
    >
      <div style={{ padding: '12px 16px', borderBottom: '1px solid rgba(255,255,255,.06)', display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: 12 }}>
        <button type="button" onClick={onBack} style={{ background: 'transparent', border: 0, color: C.muted, cursor: 'pointer', fontFamily: 'sans-serif', fontSize: 9, letterSpacing: '.14em', textTransform: 'uppercase' }}>← Return to capability map</button>
        <span style={{ fontFamily: 'sans-serif', fontSize: 8, color: C.teal, letterSpacing: '.18em', textTransform: 'uppercase' }}>Capability Chamber · L{capability.level}</span>
      </div>

      <div style={{ padding: 22 }}>
        <p style={{ fontFamily: 'sans-serif', fontSize: 8, letterSpacing: '.22em', textTransform: 'uppercase', color: C.teal, margin: '0 0 7px' }}>Enter chamber</p>
        <h2 style={{ fontFamily: 'serif', fontWeight: 400, fontSize: 28, color: C.text, margin: '0 0 9px' }}>{capability.name}</h2>
        <p style={{ fontFamily: 'sans-serif', fontSize: 12, lineHeight: 1.75, color: C.muted, maxWidth: 760, margin: 0 }}>{capability.description}</p>

        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(190px, 1fr))', gap: 10, marginTop: 20 }}>
          <Panel title="What this capability means"><p style={copy}>This capability is an A.I.S learning unit: a reusable human capability that can be developed, practiced, and eventually demonstrated. The chamber is for orientation and action, not passive content consumption.</p></Panel>

          <Panel title="Current learner state">
            <strong style={{ fontFamily: 'sans-serif', fontSize: 12, color: C.teal }}>{state.status.replaceAll('_', ' ')}</strong>
            <p style={copy}>{state.next_recommended_action || 'Choose a practical next step.'}</p>
            {state.confidence !== null && <p style={meta}>Confidence: {Math.round(state.confidence * 100)}%</p>}
          </Panel>

          <Panel title="Prerequisites">
            {prerequisites.length ? prerequisites.map(item => <div key={item.id} style={{ padding: '7px 0', borderBottom: '1px solid rgba(255,255,255,.05)' }}><span style={{ fontFamily: 'sans-serif', fontSize: 10, color: C.text }}>{item.name}</span><span style={{ display: 'block', ...meta }}>Level {item.level}</span></div>) : <p style={copy}>No prerequisite capabilities. This is an entry point.</p>}
          </Panel>

          <Panel title="Knowledge OS sources"><p style={copy}>Knowledge OS remains the canonical, source-backed knowledge authority for this capability.</p><span style={{ fontFamily: 'sans-serif', fontSize: 8, color: C.dim, letterSpacing: '.08em' }}>SOURCE RETRIEVAL / PROJECTION → KNOWLEDGE OS</span></Panel>
        </div>

        <div data-testid="learning-path-panel" style={{ marginTop: 14, padding: 16, borderRadius: 12, background: 'rgba(0,212,170,.045)', border: '1px solid rgba(0,212,170,.15)' }}>
          <p style={{ fontFamily: 'sans-serif', fontSize: 8, letterSpacing: '.20em', textTransform: 'uppercase', color: C.teal, margin: '0 0 7px' }}>Your next move</p>
          {learningPath ? <>
            <p style={{ fontFamily: 'sans-serif', fontSize: 12, lineHeight: 1.65, color: C.text, margin: 0 }}>{learningPath.reason}</p>
            <div style={{ display: 'flex', alignItems: 'center', gap: 8, flexWrap: 'wrap', marginTop: 11 }}>
              {learningPath.capability_ids.map((id, index) => <React.Fragment key={id}><span style={{ padding: '6px 9px', borderRadius: 7, border: '1px solid rgba(0,212,170,.15)', color: id === nextCapability?.id ? C.teal : C.muted, fontFamily: 'sans-serif', fontSize: 9 }}>{AISName(id)}</span>{index < learningPath.capability_ids.length - 1 && <span style={{ color: C.dim }}>→</span>}</React.Fragment>)}
            </div>
            <p style={{ fontFamily: 'sans-serif', fontSize: 8, lineHeight: 1.5, color: C.dim, margin: '9px 0 0' }}>SG-03 path projection · completion requires evidence. No exercise or evidence generation occurs here.</p>
          </> : <p style={{ fontFamily: 'sans-serif', fontSize: 12, color: C.muted, margin: 0 }}>No learning path is available for this learner state.</p>}
        </div>
      </div>
    </motion.section>
  )
}

function AISName(id: string) { return id.replace(/^cap-/, '').replaceAll('-', ' ').replace(/\b\w/g, letter => letter.toUpperCase()) }
const copy: React.CSSProperties = { fontFamily: 'sans-serif', fontSize: 10, lineHeight: 1.65, color: C.muted, margin: '7px 0 0' }
const meta: React.CSSProperties = { fontFamily: 'sans-serif', fontSize: 8, color: C.dim, margin: '4px 0 0' }
function Panel({ title, children }: { title: string; children: React.ReactNode }) { return <div style={{ padding: 14, borderRadius: 11, border: '1px solid rgba(255,255,255,.07)', background: 'rgba(255,255,255,.018)', minHeight: 118 }}><p style={{ fontFamily: 'sans-serif', fontSize: 8, letterSpacing: '.15em', textTransform: 'uppercase', color: C.dim, margin: 0 }}>{title}</p>{children}</div> }
