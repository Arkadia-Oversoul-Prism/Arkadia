import React, { useMemo, useState } from 'react'
import CrystalGateway, { type GroveGatewayState } from '../components/spiral-grove/CrystalGateway'
import CapabilityChamber from '../components/spiral-grove/CapabilityChamber'
import {
  AIS_CAPABILITIES,
  GROVE_DOMAINS,
  INITIAL_LEARNER_STATES,
  prerequisitesFor,
  type GroveCapability,
  type LearnerCapabilityState,
} from '../data/spiralGroveCatalog'

const C = { teal: '#00D4AA', text: 'rgba(232,232,232,0.86)', muted: 'rgba(232,232,232,0.52)', dim: 'rgba(232,232,232,0.30)' }
const DOMAIN_STATE_KEY = 'arkadia.spiral-grove.domain-state.v1'

function readDomainState(): Record<string, GroveGatewayState> {
  if (typeof window === 'undefined') return {}
  try {
    const parsed = JSON.parse(window.localStorage.getItem(DOMAIN_STATE_KEY) || '{}')
    return parsed && typeof parsed === 'object' ? parsed : {}
  } catch { return {} }
}

function CapabilityCard({ capability, state, onEnter }: { capability: GroveCapability; state: LearnerCapabilityState; onEnter: () => void }) {
  const domain = GROVE_DOMAINS.find(item => item.id === capability.domain)
  return (
    <button type="button" onClick={onEnter} data-testid={`capability-${capability.slug}`} style={{ textAlign: 'left', width: '100%', padding: 15, cursor: 'pointer', background: 'rgba(255,255,255,0.025)', border: '1px solid rgba(255,255,255,0.07)', borderRadius: 12, color: C.text }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', gap: 10, marginBottom: 8 }}><span style={{ fontFamily: 'sans-serif', fontSize: 11, fontWeight: 600 }}>{capability.name}</span><span style={{ color: domain?.accent || C.teal, fontSize: 9 }}>L{capability.level}</span></div>
      <p style={{ fontFamily: 'sans-serif', fontSize: 10, lineHeight: 1.55, color: C.muted, margin: '0 0 10px' }}>{capability.description}</p>
      <div style={{ display: 'flex', justifyContent: 'space-between', gap: 8 }}><span style={{ fontFamily: 'sans-serif', fontSize: 8, letterSpacing: '.11em', textTransform: 'uppercase', color: state.status === 'NOT_STARTED' ? C.dim : domain?.accent || C.teal }}>{state.status.replaceAll('_', ' ')}</span><span style={{ fontFamily: 'sans-serif', fontSize: 8, color: C.dim }}>Enter chamber →</span></div>
    </button>
  )
}

export default function SpiralGrovePage() {
  const [activeDomain, setActiveDomain] = useState('digital_intelligence')
  const [selectedId, setSelectedId] = useState(AIS_CAPABILITIES[0]?.id)
  const [states] = useState<LearnerCapabilityState[]>(INITIAL_LEARNER_STATES)
  const [domainStates, setDomainStates] = useState<Record<string, GroveGatewayState>>(() => readDomainState())
  const [chamberOpen, setChamberOpen] = useState(false)

  const domainCapabilities = useMemo(() => AIS_CAPABILITIES.filter(item => item.domain === activeDomain), [activeDomain])
  const selected = AIS_CAPABILITIES.find(item => item.id === selectedId) || domainCapabilities[0]
  const selectedState = states.find(item => item.capability_id === selected?.id) || INITIAL_LEARNER_STATES[0]
  const started = states.filter(item => item.status !== 'NOT_STARTED').length
  const demonstrated = states.filter(item => item.status === 'DEMONSTRATED' || item.status === 'MASTERED').length

  const selectDomain = (domainId: string) => {
    setActiveDomain(domainId)
    const first = AIS_CAPABILITIES.find(item => item.domain === domainId)
    if (first) { setSelectedId(first.id); setChamberOpen(false) }
    const next = { ...domainStates, [domainId]: domainStates[domainId] === 'integrated' ? 'integrated' : 'exploring' as GroveGatewayState }
    setDomainStates(next)
    if (typeof window !== 'undefined') { try { window.localStorage.setItem(DOMAIN_STATE_KEY, JSON.stringify(next)) } catch {} }
  }

  const enterChamber = (capabilityId: string) => { setSelectedId(capabilityId); setChamberOpen(true) }
  const exitChamber = () => setChamberOpen(false)

  return (
    <div style={{ paddingBottom: 40 }} data-testid="spiral-grove">
      <header style={{ marginBottom: 22 }}>
        <p style={{ fontFamily: 'sans-serif', fontSize: 9, letterSpacing: '.3em', textTransform: 'uppercase', color: 'rgba(0,212,170,.48)', margin: '0 0 5px' }}>Arkadia / Spiral Grove / A.I.S.</p>
        <div style={{ display: 'flex', alignItems: 'flex-end', justifyContent: 'space-between', gap: 16, flexWrap: 'wrap' }}><div><h1 style={{ fontFamily: 'serif', fontSize: 30, fontWeight: 400, color: '#E8E8E8', margin: 0 }}>The Spiral Grove</h1><p style={{ fontFamily: 'sans-serif', fontSize: 11, lineHeight: 1.6, color: C.muted, margin: '7px 0 0', maxWidth: 620 }}>A capability-growth layer for the A.I.S. Living University. Learn → practice → demonstrate → compound.</p></div><div style={{ display: 'flex', gap: 8 }}><Stat label="Capabilities" value={String(AIS_CAPABILITIES.length)} /><Stat label="Started" value={String(started)} /><Stat label="Demonstrated" value={String(demonstrated)} /></div></div>
      </header>
      <div style={{ padding: '11px 13px', marginBottom: 16, background: 'rgba(0,212,170,.035)', border: '1px solid rgba(0,212,170,.13)', borderRadius: 10 }}><p style={{ fontFamily: 'sans-serif', fontSize: 9, lineHeight: 1.55, color: C.muted, margin: 0 }}><strong style={{ color: C.teal }}>Architecture boundary:</strong> Spiral Grove models capability progression. Knowledge OS remains the canonical source-backed knowledge authority. Exercises and evidence are downstream and are not generated by the Learning Path Engine here.</p></div>
      <CrystalGateway activeDomain={activeDomain} onSelectDomain={selectDomain} stateByDomain={domainStates} />
      <nav style={{ display: 'flex', gap: 7, overflowX: 'auto', paddingBottom: 5, marginBottom: 14 }} aria-label="A.I.S capability domains">{GROVE_DOMAINS.map(domain => <button key={domain.id} type="button" onClick={() => selectDomain(domain.id)} style={{ flexShrink: 0, padding: '9px 11px', borderRadius: 9, cursor: 'pointer', background: activeDomain === domain.id ? `${domain.accent}12` : 'rgba(255,255,255,.02)', border: `1px solid ${activeDomain === domain.id ? `${domain.accent}45` : 'rgba(255,255,255,.06)'}`, color: activeDomain === domain.id ? domain.accent : C.muted, fontFamily: 'sans-serif', fontSize: 8, letterSpacing: '.1em', textTransform: 'uppercase' }}>{domain.icon} {domain.label}</button>)}</nav>
      {chamberOpen && selected ? <CapabilityChamber capability={selected} state={selectedState} prerequisites={prerequisitesFor(selected.id)} onBack={exitChamber} /> : <div style={{ display: 'grid', gridTemplateColumns: '1fr', gap: 14 }}><section><div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(210px, 1fr))', gap: 8 }}>{domainCapabilities.map(capability => <CapabilityCard key={capability.id} capability={capability} state={states.find(item => item.capability_id === capability.id) || INITIAL_LEARNER_STATES[0]} onEnter={() => enterChamber(capability.id)} />)}</div></section></div>}
    </div>
  )
}

function Stat({ label, value }: { label: string; value: string }) { return <div style={{ padding: '7px 10px', border: '1px solid rgba(255,255,255,.07)', borderRadius: 8, minWidth: 72 }}><span style={{ display: 'block', fontFamily: 'sans-serif', fontSize: 8, color: C.dim, textTransform: 'uppercase', letterSpacing: '.12em' }}>{label}</span><strong style={{ display: 'block', fontFamily: 'serif', fontSize: 16, fontWeight: 400, color: C.text, marginTop: 2 }}>{value}</strong></div> }
