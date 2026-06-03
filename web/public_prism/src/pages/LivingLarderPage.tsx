import React from 'react'
import { LivingLarder } from './NexusPage'

export default function LivingLarderPage() {
  return (
    <div>
      <div style={{ marginBottom: 24 }}>
        <p style={{ fontFamily: 'sans-serif', fontSize: 9, letterSpacing: '0.3em', textTransform: 'uppercase', color: 'rgba(76,175,80,0.4)', margin: '0 0 4px' }}>
          Arkadia / Living Larder
        </p>
        <h1 style={{ fontFamily: 'serif', fontSize: 28, color: '#E8E8E8', margin: 0, letterSpacing: '0.04em' }}>
          The Living Larder
        </h1>
      </div>
      <LivingLarder />
    </div>
  )
}
