import React, { useEffect, useState } from 'react'
import { FieldBar } from './NexusPage'
import { IMSArchiveSection, EncyclopediaGalacticaMatrix } from '../components/IMSArchive'
import { apiRequest } from '../lib/apiClient'

interface ArkDateData {
  ark_year: number; ark_total_years: number; total_ark_day: number
  day_in_year: number; ark_completion_pct: number; pulse: number; breath: number
  sync: { auto_sync_active: boolean; last_scroll_count: number; refresh_count: number }
}

export default function IMSArchivePage() {
  const [ark, setArk] = useState<ArkDateData | null>(null)
  useEffect(() => {
    apiRequest<ArkDateData>('/api/ark-date').then(setArk).catch(() => {})
  }, [])

  return (
    <div>
      <div style={{ marginBottom: 24 }}>
        <p style={{ fontFamily: 'sans-serif', fontSize: 9, letterSpacing: '0.3em', textTransform: 'uppercase', color: 'rgba(200,72,72,0.4)', margin: '0 0 4px' }}>
          Arkadia / IMS Archive
        </p>
        <h1 style={{ fontFamily: 'serif', fontSize: 28, color: '#E8E8E8', margin: 0, letterSpacing: '0.04em' }}>
          Identity Mapping Sessions
        </h1>
      </div>
      <div style={{ display: 'flex', flexDirection: 'column', gap: 28 }}>
        <FieldBar ark={ark} />
        <IMSArchiveSection />
        <EncyclopediaGalacticaMatrix />
      </div>
    </div>
  )
}
