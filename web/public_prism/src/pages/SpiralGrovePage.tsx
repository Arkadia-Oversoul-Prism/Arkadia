import React from 'react'
import { AISUniversity } from './NexusPage'

export default function SpiralGrovePage() {
  return (
    <div>
      <div style={{ marginBottom: 24 }}>
        <p style={{ fontFamily: 'sans-serif', fontSize: 9, letterSpacing: '0.3em', textTransform: 'uppercase', color: 'rgba(0,212,170,0.4)', margin: '0 0 4px' }}>
          Arkadia / Spiral Grove
        </p>
        <h1 style={{ fontFamily: 'serif', fontSize: 28, color: '#E8E8E8', margin: 0, letterSpacing: '0.04em' }}>
          The Spiral Grove
        </h1>
      </div>
      <AISUniversity />
    </div>
  )
}
