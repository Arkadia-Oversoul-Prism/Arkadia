import React from 'react'
import { AISUniversity } from '../../../web/public_prism/src/pages/NexusPage'

/**
 * Archived SG-02-FE placeholder.
 * Preserved for lineage; no longer used by the Prism frontend.
 */
export default function SpiralGrovePagePlaceholder() {
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
