import React from 'react'
import { GROVE_DOMAINS } from '../../data/spiralGroveCatalog'

export type GroveGatewayState = 'dormant' | 'exploring' | 'integrated'

export interface GroveGatewayProps {
  activeDomain: string
  onSelectDomain: (domainId: string) => void
  stateByDomain?: Record<string, GroveGatewayState>
}

const FALLBACK_STATE: GroveGatewayState = 'exploring'

export default function CrystalGateway({ activeDomain, onSelectDomain, stateByDomain = {} }: GroveGatewayProps) {
  const count = GROVE_DOMAINS.length
  const radius = 34
  const center = 50

  return (
    <section
      aria-label="Spiral Grove capability gateway"
      data-testid="crystal-gateway"
      style={{
        position: 'relative',
        minHeight: 245,
        overflow: 'hidden',
        borderRadius: 18,
        border: '1px solid rgba(201,168,76,.14)',
        background: 'radial-gradient(circle at center, rgba(0,212,170,.07), rgba(8,12,22,.92) 54%, rgba(4,7,14,.98))',
        marginBottom: 18,
      }}
    >
      <div aria-hidden="true" style={{ position: 'absolute', inset: '16% 24%', border: '1px solid rgba(201,168,76,.10)', transform: 'rotate(45deg)', borderRadius: 14 }} />
      <div aria-hidden="true" style={{ position: 'absolute', inset: '23% 31%', border: '1px solid rgba(0,212,170,.08)', transform: 'rotate(12deg)', borderRadius: 14 }} />

      <div style={{ position: 'absolute', left: '50%', top: '50%', transform: 'translate(-50%,-50%)', width: 86, height: 86, borderRadius: 20, display: 'grid', placeItems: 'center', background: 'rgba(201,168,76,.08)', border: '1px solid rgba(201,168,76,.30)', boxShadow: '0 0 36px rgba(0,212,170,.08)' }}>
        <div style={{ textAlign: 'center' }}>
          <div style={{ fontSize: 26, color: '#C9A84C' }}>◇</div>
          <span style={{ display: 'block', fontFamily: 'sans-serif', fontSize: 7, letterSpacing: '.2em', textTransform: 'uppercase', color: 'rgba(232,232,232,.48)' }}>Grove</span>
        </div>
      </div>

      {GROVE_DOMAINS.map((domain, index) => {
        const angle = (index / count) * Math.PI * 2 - Math.PI / 2
        const x = center + Math.cos(angle) * radius
        const y = center + Math.sin(angle) * radius
        const selected = activeDomain === domain.id
        const state = stateByDomain[domain.id] || FALLBACK_STATE
        return (
          <button
            key={domain.id}
            type="button"
            data-testid={`gateway-domain-${domain.id}`}
            aria-pressed={selected}
            onClick={() => onSelectDomain(domain.id)}
            style={{
              position: 'absolute', left: `${x}%`, top: `${y}%`, transform: 'translate(-50%,-50%)',
              width: 108, minHeight: 50, padding: '7px 8px', cursor: 'pointer',
              borderRadius: 10, border: `1px solid ${selected ? domain.accent + '65' : domain.accent + '22'}`,
              background: selected ? `${domain.accent}12` : 'rgba(5,9,18,.86)', color: selected ? domain.accent : 'rgba(232,232,232,.58)',
            }}
          >
            <span style={{ display: 'block', fontFamily: 'sans-serif', fontSize: 8, letterSpacing: '.07em', textTransform: 'uppercase' }}>{domain.icon} {domain.label}</span>
            <span style={{ display: 'block', marginTop: 4, fontFamily: 'sans-serif', fontSize: 7, color: selected ? domain.accent : 'rgba(232,232,232,.28)', textTransform: 'uppercase', letterSpacing: '.12em' }}>{state}</span>
          </button>
        )
      })}

      <p style={{ position: 'absolute', left: 14, bottom: 10, margin: 0, fontFamily: 'sans-serif', fontSize: 7, letterSpacing: '.13em', textTransform: 'uppercase', color: 'rgba(232,232,232,.22)' }}>
        Explore a domain · select a capability · follow the prerequisite chain
      </p>
    </section>
  )
}
