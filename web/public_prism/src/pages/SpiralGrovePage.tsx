import React, { useMemo, useState } from 'react'
import { motion } from 'framer-motion'
import {
  AIS_CAPABILITIES,
  GROVE_DOMAINS,
  INITIAL_LEARNER_STATES,
  prerequisitesFor,
  type GroveCapability,
  type LearnerCapabilityState,
  type LearnerCapabilityStatus,
} from '../data/spiralGroveCatalog'

const C = {
  gold: '#C9A84C',
  teal: '#00D4AA',
  text: 'rgba(232,232,232,0.86)',
  muted: 'rgba(232,232,232,0.52)',
  dim: 'rgba(232,232,232,0.30)',
}

const STATUS_LABELS: Record<LearnerCapabilityStatus, string> = {
  NOT_STARTED: 'Not started',
  EXPLORING: 'Exploring',
  PRACTICING: 'Practicing',
  DEMONSTRATED: 'Demonstrated',
  MASTERED: 'Mastered',
}

function CapabilityCard({
  capability,
  state,
  selected,
  onSelect,
}: {
  capability: GroveCapability
  state: LearnerCapabilityState
  selected: boolean
  onSelect: () => void
}) {
  const domain = GROVE_DOMAINS.find(item => item.id === capability.domain)
  return (
    <button
      type="button"
      onClick={onSelect}
      data-testid={`capability-${capability.slug}`}
      style={{
        textAlign: 'left', width: '100%', padding: 15, cursor: 'pointer',
        background: selected ? `${domain?.accent || C.teal}10` : 'rgba(255,255,255,0.025)',
        border: `1px solid ${selected ? `${domain?.accent || C.teal}55` : 'rgba(255,255,255,0.07)'}`,
        borderRadius: 12, color: C.text, transition: 'all .18s',
      }}
    >
      <div style={{ display: 'flex', justifyContent: 'space-between', gap: 10, marginBottom: 8 }}>
        <span style={{ fontFamily: 'sans-serif', fontSize: 11, fontWeight: 600 }}>{capability.name}</span>
        <span style={{ color: domain?.accent || C.teal, fontSize: 9, flexShrink: 0 }}>L{capability.level}</span>
      </div>
      <p style={{ fontFamily: 'sans-serif', fontSize: 10, lineHeight: 1.55, color: C.muted, margin: '0 0 10px' }}>{capability.description}</p>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 8 }}>
        <span style={{ fontFamily: 'sans-serif', fontSize: 8, letterSpacing: '.11em', textTransform: 'uppercase', color: state.status === 'NOT_STARTED' ? C.dim : domain?.accent || C.teal }}>
          {STATUS_LABELS[state.status]}
        </span>
        <span style={{ fontFamily: 'sans-serif', fontSize: 8, color: C.dim }}>{capability.prerequisites.length} prerequisite{capability.prerequisites.length === 1 ? '' : 's'}</span>
      </div>
    </button>
  )
}

function CapabilityDetail({ capability, state }: { capability: GroveCapability; state: LearnerCapabilityState }) {
  const domain = GROVE_DOMAINS.find(item => item.id === capability.domain)
  const prerequisites = prerequisitesFor(capability.id)
  return (
    <motion.aside
      key={capability.id}
      initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }}
      style={{ padding: 20, background: 'rgba(8,12,22,.82)', border: `1px solid ${domain?.accent || C.teal}30`, borderRadius: 15, position: 'sticky', top: 20 }}
      data-testid="capability-detail"
    >
      <p style={{ fontFamily: 'sans-serif', fontSize: 8, letterSpacing: '.25em', textTransform: 'uppercase', color: domain?.accent || C.teal, margin: '0 0 6px' }}>
        {domain?.label || capability.domain} · Capability L{capability.level}
      </p>
      <h3 style={{ fontFamily: 'serif', fontSize: 22, fontWeight: 400, color: '#E8E8E8', margin: '0 0 8px' }}>{capability.name}</h3>
      <p style={{ fontFamily: 'sans-serif', fontSize: 11, lineHeight: 1.7, color: C.muted, margin: '0 0 16px' }}>{capability.description}</p>

      <div style={{ padding: 12, borderRadius: 10, background: `${domain?.accent || C.teal}07`, border: `1px solid ${domain?.accent || C.teal}18`, marginBottom: 14 }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 6 }}>
          <span style={{ fontFamily: 'sans-serif', fontSize: 8, letterSpacing: '.15em', textTransform: 'uppercase', color: C.dim }}>Learner state</span>
          <span style={{ fontFamily: 'sans-serif', fontSize: 9, color: domain?.accent || C.teal }}>{STATUS_LABELS[state.status]}</span>
        </div>
        <p style={{ fontFamily: 'sans-serif', fontSize: 10, lineHeight: 1.55, color: C.muted, margin: 0 }}>
          {state.next_recommended_action}
        </p>
      </div>

      <Section title="Prerequisite chain">
        {prerequisites.length ? prerequisites.map(item => (
          <div key={item.id} style={{ padding: '7px 9px', borderLeft: `2px solid ${domain?.accent || C.teal}35`, marginBottom: 5 }}>
            <span style={{ fontFamily: 'sans-serif', fontSize: 10, color: C.text }}>{item.name}</span>
            <span style={{ display: 'block', fontFamily: 'sans-serif', fontSize: 8, color: C.dim }}>Level {item.level}</span>
          </div>
        )) : <p style={{ fontFamily: 'sans-serif', fontSize: 10, color: C.dim, margin: 0 }}>No prerequisites. This is an entry capability.</p>}
      </Section>

      <Section title="Demonstrable outcomes">
        <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6 }}>
          {capability.outcomes.map(outcome => <span key={outcome} style={{ padding: '5px 7px', borderRadius: 6, background: 'rgba(255,255,255,.035)', color: C.muted, fontFamily: 'sans-serif', fontSize: 8 }}>{outcome.replaceAll('-', ' ')}</span>)}
        </div>
      </Section>

      <Section title="Downstream">
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 7 }}>
          <Downstream label="Exercises" value="Ready for SG-03" />
          <Downstream label="Evidence" value="Captured after work" />
        </div>
      </Section>
    </motion.aside>
  )
}

function Section({ title, children }: { title: string; children: React.ReactNode }) {
  return <section style={{ marginTop: 17 }}><p style={{ fontFamily: 'sans-serif', fontSize: 8, letterSpacing: '.18em', textTransform: 'uppercase', color: C.dim, margin: '0 0 8px' }}>{title}</p>{children}</section>
}

function Downstream({ label, value }: { label: string; value: string }) {
  return <div style={{ padding: 9, borderRadius: 8, border: '1px solid rgba(255,255,255,.06)' }}><span style={{ display: 'block', fontFamily: 'sans-serif', fontSize: 9, color: C.text }}>{label}</span><span style={{ display: 'block', fontFamily: 'sans-serif', fontSize: 7, color: C.dim, marginTop: 3 }}>{value}</span></div>
}

export default function SpiralGrovePage() {
  const [activeDomain, setActiveDomain] = useState<string>('digital_intelligence')
  const [selectedId, setSelectedId] = useState(AIS_CAPABILITIES[0]?.id)
  const [states] = useState<LearnerCapabilityState[]>(INITIAL_LEARNER_STATES)

  const domainCapabilities = useMemo(() => AIS_CAPABILITIES.filter(item => item.domain === activeDomain), [activeDomain])
  const selected = AIS_CAPABILITIES.find(item => item.id === selectedId) || domainCapabilities[0]
  const selectedState = states.find(item => item.capability_id === selected?.id) || INITIAL_LEARNER_STATES[0]
  const started = states.filter(item => item.status !== 'NOT_STARTED').length
  const demonstrated = states.filter(item => item.status === 'DEMONSTRATED' || item.status === 'MASTERED').length

  return (
    <div style={{ paddingBottom: 40 }} data-testid="spiral-grove">
      <header style={{ marginBottom: 22 }}>
        <p style={{ fontFamily: 'sans-serif', fontSize: 9, letterSpacing: '.3em', textTransform: 'uppercase', color: 'rgba(0,212,170,.48)', margin: '0 0 5px' }}>Arkadia / Spiral Grove / A.I.S.</p>
        <div style={{ display: 'flex', alignItems: 'flex-end', justifyContent: 'space-between', gap: 16, flexWrap: 'wrap' }}>
          <div>
            <h1 style={{ fontFamily: 'serif', fontSize: 30, fontWeight: 400, color: '#E8E8E8', margin: 0 }}>The Spiral Grove</h1>
            <p style={{ fontFamily: 'sans-serif', fontSize: 11, lineHeight: 1.6, color: C.muted, margin: '7px 0 0', maxWidth: 620 }}>
              A capability-growth layer for the A.I.S. Living University. Learn → practice → demonstrate → compound.
            </p>
          </div>
          <div style={{ display: 'flex', gap: 8 }}>
            <Stat label="Capabilities" value={String(AIS_CAPABILITIES.length)} />
            <Stat label="Started" value={String(started)} />
            <Stat label="Demonstrated" value={String(demonstrated)} />
          </div>
        </div>
      </header>

      <div style={{ padding: '11px 13px', marginBottom: 16, background: 'rgba(0,212,170,.035)', border: '1px solid rgba(0,212,170,.13)', borderRadius: 10 }}>
        <p style={{ fontFamily: 'sans-serif', fontSize: 9, lineHeight: 1.55, color: C.muted, margin: 0 }}>
          <strong style={{ color: C.teal }}>Architecture boundary:</strong> Spiral Grove models capability progression. Knowledge OS remains the canonical source-backed knowledge authority. Exercises and evidence are downstream and are not yet generated by the Learning Path Engine.
        </p>
      </div>

      <nav style={{ display: 'flex', gap: 7, overflowX: 'auto', paddingBottom: 5, marginBottom: 14 }} aria-label="A.I.S capability domains">
        {GROVE_DOMAINS.map(domain => (
          <button key={domain.id} type="button" onClick={() => { setActiveDomain(domain.id); const first = AIS_CAPABILITIES.find(item => item.domain === domain.id); if (first) setSelectedId(first.id) }}
            style={{ flexShrink: 0, padding: '9px 11px', borderRadius: 9, cursor: 'pointer', background: activeDomain === domain.id ? `${domain.accent}12` : 'rgba(255,255,255,.02)', border: `1px solid ${activeDomain === domain.id ? `${domain.accent}45` : 'rgba(255,255,255,.06)'}`, color: activeDomain === domain.id ? domain.accent : C.muted, fontFamily: 'sans-serif', fontSize: 8, letterSpacing: '.1em', textTransform: 'uppercase' }}>
            {domain.icon} {domain.label}
          </button>
        ))}
      </nav>

      <div style={{ display: 'grid', gridTemplateColumns: 'minmax(0, 1.55fr) minmax(290px, .9fr)', gap: 14, alignItems: 'start' }}>
        <section>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(210px, 1fr))', gap: 8 }}>
            {domainCapabilities.map(capability => (
              <CapabilityCard key={capability.id} capability={capability} state={states.find(item => item.capability_id === capability.id) || INITIAL_LEARNER_STATES[0]} selected={selected?.id === capability.id} onSelect={() => setSelectedId(capability.id)} />
            ))}
          </div>
        </section>
        {selected && selectedState && <CapabilityDetail capability={selected} state={selectedState} />}
      </div>
    </div>
  )
}

function Stat({ label, value }: { label: string; value: string }) {
  return <div style={{ padding: '7px 10px', border: '1px solid rgba(255,255,255,.07)', borderRadius: 8, minWidth: 72 }}><span style={{ display: 'block', fontFamily: 'sans-serif', fontSize: 8, color: C.dim, textTransform: 'uppercase', letterSpacing: '.12em' }}>{label}</span><strong style={{ display: 'block', fontFamily: 'serif', fontSize: 16, fontWeight: 400, color: C.text, marginTop: 2 }}>{value}</strong></div>
}
