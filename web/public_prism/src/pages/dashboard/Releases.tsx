/**
 * Arkadia Distribution — Releases Dashboard Tab
 * Shows artist releases with status, artwork, and detail modal.
 */
import React, { useEffect, useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { COLORS, Card, Empty, ErrorBox } from './ui'
import { useAuth } from '../../contexts/AuthContext'

const API_BASE = (import.meta.env.VITE_API_BASE_URL ?? '').replace(/\/$/, '')

interface Release {
  releaseId: string
  title: string
  artistName: string
  featuring: string
  genre: string
  releaseDate: string
  status: 'draft' | 'submitted' | 'processing' | 'live' | 'failed'
  artworkUrl: string
  covenantSigned: boolean
  createdAt: string
  updatedAt: string
  isrc: string
}

const STATUS_META: Record<string, { bg: string; fg: string; border: string; label: string }> = {
  draft:      { bg: 'rgba(232,232,232,0.05)', fg: 'rgba(232,232,232,0.5)',  border: 'rgba(232,232,232,0.2)',  label: 'Draft' },
  submitted:  { bg: 'rgba(201,168,76,0.10)',  fg: '#C9A84C',               border: 'rgba(201,168,76,0.4)',   label: 'Submitted' },
  processing: { bg: 'rgba(0,212,170,0.08)',   fg: '#00D4AA',               border: 'rgba(0,212,170,0.35)',   label: 'Processing' },
  live:       { bg: 'rgba(76,175,80,0.10)',   fg: '#4CAF50',               border: 'rgba(76,175,80,0.4)',    label: 'Live' },
  failed:     { bg: 'rgba(239,108,108,0.10)', fg: '#EF6C6C',               border: 'rgba(239,108,108,0.4)',  label: 'Failed' },
}

function StatusBadge({ status }: { status: string }) {
  const m = STATUS_META[status] ?? STATUS_META['draft']
  return (
    <span style={{
      display: 'inline-block', padding: '3px 10px',
      background: m.bg, color: m.fg, border: `1px solid ${m.border}`,
      borderRadius: 999, fontFamily: 'sans-serif', fontSize: 9.5,
      letterSpacing: '0.18em', textTransform: 'uppercase',
    }}>
      {m.label}
    </span>
  )
}

type Filter = 'all' | 'draft' | 'submitted' | 'processing' | 'live' | 'failed'

const FILTERS: { id: Filter; label: string }[] = [
  { id: 'all', label: 'All' },
  { id: 'live', label: 'Live' },
  { id: 'processing', label: 'Processing' },
  { id: 'submitted', label: 'Submitted' },
  { id: 'draft', label: 'Draft' },
  { id: 'failed', label: 'Failed' },
]

function ReleaseModal({ release, onClose }: { release: Release; onClose: () => void }) {
  const [analytics, setAnalytics] = useState<Record<string, unknown> | null>(null)
  const { user } = useAuth()

  useEffect(() => {
    if (release.status !== 'live') return
    const headers: Record<string, string> = user?.idToken ? { Authorization: `Bearer ${user.idToken}` } : {}
    fetch(`${API_BASE}/api/distribution/analytics/${release.releaseId}`, { headers })
      .then(r => r.ok ? r.json() : null)
      .then(d => d?.analytics && setAnalytics(d.analytics))
      .catch(() => null)
  }, [release.releaseId, release.status, user])

  const artSrc = release.artworkUrl
    ? (release.artworkUrl.startsWith('http') ? release.artworkUrl : `${API_BASE}${release.artworkUrl}`)
    : null

  return (
    <motion.div
      initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}
      onClick={onClose}
      style={{
        position: 'fixed', inset: 0, zIndex: 100,
        background: 'rgba(2,3,8,0.8)', backdropFilter: 'blur(6px)',
        display: 'flex', alignItems: 'center', justifyContent: 'center', padding: 16,
      }}
    >
      <motion.div
        initial={{ scale: 0.94, y: 16 }} animate={{ scale: 1, y: 0 }} exit={{ scale: 0.94, y: 16 }}
        onClick={e => e.stopPropagation()}
        style={{
          background: '#0D0D1A', border: '1px solid rgba(201,168,76,0.14)',
          borderRadius: 16, width: '100%', maxWidth: 480,
          maxHeight: '85vh', overflowY: 'auto', padding: '24px 22px',
        }}
      >
        {/* Header */}
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 20 }}>
          <div style={{ display: 'flex', gap: 14, alignItems: 'center', flex: 1 }}>
            {artSrc && (
              <img src={artSrc} alt="artwork"
                style={{ width: 56, height: 56, objectFit: 'cover', borderRadius: 8, border: '1px solid rgba(201,168,76,0.2)', flexShrink: 0 }} />
            )}
            <div style={{ flex: 1, overflow: 'hidden' }}>
              <h3 style={{ fontFamily: 'serif', fontSize: 17, color: COLORS.text, margin: '0 0 4px', letterSpacing: '0.04em' }}>
                {release.title}
              </h3>
              <p style={{ fontFamily: 'sans-serif', fontSize: 11, color: COLORS.muted, margin: 0 }}>
                {release.artistName}{release.featuring ? ` ft. ${release.featuring}` : ''}
              </p>
            </div>
          </div>
          <button onClick={onClose}
            style={{ background: 'none', border: 'none', color: COLORS.muted, fontSize: 16, cursor: 'pointer', padding: '0 0 0 12px', flexShrink: 0 }}>
            ✕
          </button>
        </div>

        <div style={{ marginBottom: 16 }}>
          <StatusBadge status={release.status} />
        </div>

        {/* Metadata grid */}
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '8px 16px', marginBottom: 20 }}>
          {[
            ['Genre', release.genre || '—'],
            ['Release Date', release.releaseDate || '—'],
            ['ISRC', release.isrc || '—'],
            ['Covenant', release.covenantSigned ? '✓ Signed' : '✗ Unsigned'],
            ['Created', new Date(release.createdAt).toLocaleDateString()],
          ].map(([k, v]) => (
            <div key={k}>
              <p style={{ fontFamily: 'sans-serif', fontSize: 8.5, letterSpacing: '0.28em', textTransform: 'uppercase', color: COLORS.dim, margin: '0 0 2px' }}>{k}</p>
              <p style={{ fontFamily: 'sans-serif', fontSize: 12, color: k === 'Covenant' && v === '✓ Signed' ? '#00D4AA' : COLORS.muted, margin: 0 }}>{v}</p>
            </div>
          ))}
        </div>

        {/* Analytics (live only) */}
        {release.status === 'live' && analytics && (
          <div style={{ background: 'rgba(0,212,170,0.04)', border: '1px solid rgba(0,212,170,0.12)', borderRadius: 10, padding: '14px 16px', marginBottom: 16 }}>
            <p style={{ fontFamily: 'sans-serif', fontSize: 8.5, letterSpacing: '0.28em', textTransform: 'uppercase', color: COLORS.dim, margin: '0 0 10px' }}>
              Streaming Analytics
            </p>
            <p style={{ fontFamily: 'serif', fontSize: 28, color: '#00D4AA', margin: '0 0 8px', lineHeight: 1 }}>
              {(analytics as { totalStreams?: number }).totalStreams?.toLocaleString() ?? '—'}
            </p>
            <p style={{ fontFamily: 'sans-serif', fontSize: 10, color: COLORS.muted, margin: '0 0 10px' }}>total streams</p>
            {(analytics as { platforms?: Record<string, number> }).platforms && (
              <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
                {Object.entries((analytics as { platforms: Record<string, number> }).platforms).map(([p, n]) => (
                  <div key={p} style={{ display: 'flex', justifyContent: 'space-between' }}>
                    <span style={{ fontFamily: 'sans-serif', fontSize: 11, color: COLORS.muted }}>{p}</span>
                    <span style={{ fontFamily: 'sans-serif', fontSize: 11, color: COLORS.text }}>{n.toLocaleString()}</span>
                  </div>
                ))}
              </div>
            )}
            <p style={{ fontFamily: 'sans-serif', fontSize: 9, color: COLORS.dim, marginTop: 8, fontStyle: 'italic' }}>
              Placeholder data — connect live aggregator for real analytics
            </p>
          </div>
        )}

        {/* Covenant status */}
        {release.covenantSigned && (
          <div style={{ background: 'rgba(201,168,76,0.04)', border: '1px solid rgba(201,168,76,0.1)', borderRadius: 10, padding: '10px 14px' }}>
            <p style={{ fontFamily: 'sans-serif', fontSize: 11, color: 'rgba(201,168,76,0.6)', margin: 0, lineHeight: 1.6 }}>
              ✦ Covenant sealed. Masters owned by artist. Arkadia 5% (capped $500). Exit anytime.
            </p>
          </div>
        )}
      </motion.div>
    </motion.div>
  )
}

export default function Releases() {
  const { user, isAuthenticated } = useAuth()
  const [releases, setReleases] = useState<Release[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [filter, setFilter] = useState<Filter>('all')
  const [selected, setSelected] = useState<Release | null>(null)

  const artistId = user?.uid
    ? user.uid
    : 'anonymous'

  const fetchReleases = async () => {
    setLoading(true)
    setError(null)
    try {
      const headers: Record<string, string> = user?.idToken ? { Authorization: `Bearer ${user.idToken}` } : {}
      const res = await fetch(`${API_BASE}/api/distribution/releases/${artistId}`, { headers })
      if (!res.ok) throw new Error(`HTTP ${res.status}`)
      const data = await res.json()
      setReleases(data.releases ?? [])
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : 'Failed to load releases')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { fetchReleases() }, [artistId])

  const filtered = filter === 'all' ? releases : releases.filter(r => r.status === filter)

  if (!isAuthenticated) {
    return (
      <Empty>
        <p style={{ fontFamily: 'sans-serif', fontSize: 12, color: COLORS.muted, margin: 0 }}>
          Log in to see your releases.
        </p>
      </Empty>
    )
  }

  return (
    <div>
      {/* Header */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 16, flexWrap: 'wrap', gap: 10 }}>
        <div>
          <p style={{ fontFamily: 'sans-serif', fontSize: 8.5, letterSpacing: '0.32em', textTransform: 'uppercase', color: COLORS.dim, margin: '0 0 2px' }}>
            Distribution
          </p>
          <h2 style={{ fontFamily: 'serif', fontSize: 18, color: COLORS.text, margin: 0 }}>
            Your Releases
          </h2>
        </div>
        <button onClick={fetchReleases}
          style={{
            padding: '7px 14px', background: 'rgba(255,255,255,0.03)',
            border: '1px solid rgba(255,255,255,0.08)', borderRadius: 8,
            color: COLORS.muted, fontFamily: 'sans-serif', fontSize: 9.5,
            letterSpacing: '0.16em', textTransform: 'uppercase', cursor: 'pointer',
          }}>
          ↻ Refresh
        </button>
      </div>

      {/* Filter tabs */}
      <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap', marginBottom: 18 }}>
        {FILTERS.map(f => (
          <button key={f.id} onClick={() => setFilter(f.id)}
            style={{
              padding: '5px 12px',
              background: filter === f.id ? 'rgba(0,212,170,0.10)' : 'transparent',
              border: filter === f.id ? '1px solid rgba(0,212,170,0.35)' : '1px solid rgba(232,232,232,0.07)',
              borderRadius: 999, color: filter === f.id ? COLORS.teal : COLORS.muted,
              fontFamily: 'sans-serif', fontSize: 9.5, letterSpacing: '0.14em',
              textTransform: 'uppercase', cursor: 'pointer', transition: 'all .15s',
            }}>
            {f.label}
            {f.id !== 'all' && releases.filter(r => r.status === f.id).length > 0 && (
              <span style={{ marginLeft: 5, opacity: 0.6 }}>
                {releases.filter(r => r.status === f.id).length}
              </span>
            )}
          </button>
        ))}
      </div>

      {error && <div style={{ marginBottom: 14 }}><ErrorBox>{error}</ErrorBox></div>}

      {loading ? (
        <motion.div animate={{ opacity: [0.4, 0.8, 0.4] }} transition={{ duration: 1.5, repeat: Infinity }}
          style={{ padding: '32px', textAlign: 'center', fontFamily: 'sans-serif', fontSize: 11, color: COLORS.dim }}>
          ⟐ Loading releases…
        </motion.div>
      ) : filtered.length === 0 ? (
        <Empty>
          {filter === 'all'
            ? 'No releases yet. Use the Distribute page to submit your first release.'
            : `No ${filter} releases.`}
        </Empty>
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
          {filtered.map(r => {
            const artSrc = r.artworkUrl
              ? (r.artworkUrl.startsWith('http') ? r.artworkUrl : `${API_BASE}${r.artworkUrl}`)
              : null
            return (
              <motion.div
                key={r.releaseId}
                initial={{ opacity: 0, y: 6 }}
                animate={{ opacity: 1, y: 0 }}
                onClick={() => setSelected(r)}
                style={{
                  display: 'flex', alignItems: 'center', gap: 14,
                  padding: '14px 16px',
                  background: 'rgba(13,13,26,0.7)',
                  border: '1px solid rgba(0,212,170,0.08)',
                  borderRadius: 12, cursor: 'pointer',
                  transition: 'border-color 0.15s',
                }}
                whileHover={{ borderColor: 'rgba(0,212,170,0.25)' }}
              >
                {/* Artwork */}
                <div style={{
                  width: 48, height: 48, borderRadius: 8, flexShrink: 0, overflow: 'hidden',
                  background: 'rgba(201,168,76,0.06)', border: '1px solid rgba(201,168,76,0.12)',
                  display: 'flex', alignItems: 'center', justifyContent: 'center',
                }}>
                  {artSrc
                    ? <img src={artSrc} alt="art" style={{ width: '100%', height: '100%', objectFit: 'cover' }} />
                    : <span style={{ fontSize: 18 }}>🎵</span>
                  }
                </div>

                {/* Info */}
                <div style={{ flex: 1, overflow: 'hidden' }}>
                  <p style={{ fontFamily: 'serif', fontSize: 14, color: COLORS.text, margin: '0 0 3px', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                    {r.title}
                  </p>
                  <p style={{ fontFamily: 'sans-serif', fontSize: 10, color: COLORS.muted, margin: 0, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                    {r.artistName}{r.featuring ? ` ft. ${r.featuring}` : ''} · {r.genre}
                  </p>
                </div>

                {/* Right: date + status */}
                <div style={{ textAlign: 'right', flexShrink: 0 }}>
                  <StatusBadge status={r.status} />
                  {r.releaseDate && (
                    <p style={{ fontFamily: 'sans-serif', fontSize: 9.5, color: COLORS.dim, margin: '5px 0 0' }}>
                      {r.releaseDate}
                    </p>
                  )}
                </div>

                <span style={{ color: COLORS.dim, fontSize: 12, flexShrink: 0 }}>→</span>
              </motion.div>
            )
          })}
        </div>
      )}

      {/* Stats summary */}
      {releases.length > 0 && (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 10, marginTop: 20 }}>
          {[
            { label: 'Total', value: releases.length, color: COLORS.text },
            { label: 'Live', value: releases.filter(r => r.status === 'live').length, color: '#4CAF50' },
            { label: 'Processing', value: releases.filter(r => r.status === 'processing').length, color: COLORS.teal },
          ].map(s => (
            <Card key={s.label}>
              <p style={{ fontFamily: 'sans-serif', fontSize: 8.5, letterSpacing: '0.28em', textTransform: 'uppercase', color: COLORS.dim, margin: '0 0 4px' }}>{s.label}</p>
              <p style={{ fontFamily: 'serif', fontSize: 24, color: s.color, margin: 0 }}>{s.value}</p>
            </Card>
          ))}
        </div>
      )}

      {/* Release detail modal */}
      <AnimatePresence>
        {selected && <ReleaseModal release={selected} onClose={() => setSelected(null)} />}
      </AnimatePresence>
    </div>
  )
}
