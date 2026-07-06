/**
 * IMSArchive — canonical shared rendering of the Identity Mapping Session
 * archive. Consumed by NexusPage, IMSArchivePage, and ShereSanctuary so all
 * three surfaces show the same complete set of real IMS documents instead of
 * three independent, partially-overlapping lists.
 */
import React from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { IMS_TIMELINE, IMS_IDENTITIES, buildImsUrl } from '../data/imsArchive'

const API_BASE = (import.meta.env.VITE_API_BASE_URL ?? import.meta.env.VITE_API_URL ?? '').replace(/\/$/, '')

const C = { text: '#E8E8E8', muted: 'rgba(232,232,232,0.65)', dim: 'rgba(232,232,232,0.4)', gold: '#C9A84C' }

export function IMSArchiveSection() {
  const [viewer, setViewer] = React.useState<{ url: string; title: string } | null>(null)
  const [iframeError, setIframeError] = React.useState<string | null>(null)
  const [iframeLoading, setIframeLoading] = React.useState(true)

  return (
    <>
      <AnimatePresence>
        {viewer && (
          <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}
            style={{ position: 'fixed', inset: 0, zIndex: 1000, background: '#03040a', display: 'flex', flexDirection: 'column' }}>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '10px 16px', background: 'rgba(3,4,10,0.98)', borderBottom: '1px solid rgba(201,168,76,0.15)', flexShrink: 0 }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                <span style={{ color: '#c9a84c', fontSize: 14 }}>☥</span>
                <p style={{ fontFamily: 'sans-serif', fontSize: 11, letterSpacing: '0.2em', textTransform: 'uppercase', color: 'rgba(201,168,76,0.65)', margin: 0 }}>{viewer.title}</p>
              </div>
              <button onClick={() => { setViewer(null); setIframeError(null); setIframeLoading(true) }}
                style={{ padding: '8px 16px', background: 'rgba(232,140,106,0.08)', border: '1px solid rgba(232,140,106,0.25)', borderRadius: 6, color: '#E88C6A', fontFamily: 'sans-serif', fontSize: 10, letterSpacing: '0.18em', textTransform: 'uppercase', cursor: 'pointer' }}>
                ✕ Close
              </button>
            </div>
            {iframeLoading && !iframeError && (
              <div style={{ flex: 1, display: 'flex', alignItems: 'center', justifyContent: 'center', background: '#03040a' }}>
                <div style={{ textAlign: 'center' }}>
                  <motion.div animate={{ rotate: 360 }} transition={{ duration: 1, repeat: Infinity, ease: 'linear' }}
                    style={{ width: 28, height: 28, borderRadius: '50%', border: '2px solid rgba(212,175,55,0.25)', borderTopColor: '#D4AF37', margin: '0 auto' }} />
                  <p style={{ fontFamily: 'sans-serif', fontSize: 10, color: 'rgba(201,168,76,0.5)', marginTop: 12, letterSpacing: '0.2em', textTransform: 'uppercase' }}>Loading IMS Document…</p>
                </div>
              </div>
            )}
            {iframeError && (
              <div style={{ flex: 1, display: 'flex', alignItems: 'center', justifyContent: 'center', background: '#03040a', padding: 20 }}>
                <div style={{ textAlign: 'center', maxWidth: 400 }}>
                  <p style={{ fontSize: 24, marginBottom: 12 }}>⚡</p>
                  <p style={{ fontFamily: 'sans-serif', fontSize: 13, color: 'rgba(232,140,106,0.8)', marginBottom: 8 }}>{iframeError}</p>
                  <button onClick={() => window.open(viewer.url, '_blank')}
                    style={{ padding: '10px 20px', background: 'rgba(201,168,76,0.08)', border: '1px solid rgba(201,168,76,0.3)', borderRadius: 8, color: '#C9A84C', fontFamily: 'sans-serif', fontSize: 10, letterSpacing: '0.18em', textTransform: 'uppercase', cursor: 'pointer' }}>
                    Open in New Tab ↗
                  </button>
                </div>
              </div>
            )}
            {!iframeError && (
              <iframe src={viewer.url} title={viewer.title}
                style={{ flex: 1, border: 'none', width: '100%', display: iframeLoading ? 'none' : 'block' }}
                onLoad={() => { setIframeLoading(false); setIframeError(null) }}
                onError={() => { setIframeLoading(false); setIframeError('Failed to load the IMS document. The file may not be available on the server.') }} />
            )}
          </motion.div>
        )}
      </AnimatePresence>

      <div>
        <p style={{ fontFamily: 'sans-serif', fontSize: 9, letterSpacing: '0.3em', textTransform: 'uppercase', color: 'rgba(200,72,72,0.45)', margin: '0 0 5px' }}>
          IMS Archive · Session Log
        </p>
        <h2 style={{ fontFamily: 'serif', fontSize: 20, color: '#E8E8E8', margin: '0 0 18px' }}>Identity Mapping Sessions</h2>

        <div style={{ position: 'relative', paddingLeft: 36 }}>
          <div style={{ position: 'absolute', left: 10, top: 8, bottom: 8, width: 1,
            background: 'linear-gradient(180deg, rgba(0,212,170,0.35) 0%, rgba(0,212,170,0.08) 100%)' }} />

          {IMS_TIMELINE.map((s, idx) => (
            <motion.div
              key={s.id}
              initial={{ opacity: 0, x: -8 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: idx * 0.08 }}
              style={{ position: 'relative', marginBottom: idx < IMS_TIMELINE.length - 1 ? 20 : 0 }}
            >
              <div style={{
                position: 'absolute', left: -30, top: 22,
                width: 12, height: 12, borderRadius: '50%',
                background: s.statusColor,
                border: '2px solid rgba(3,4,10,0.9)',
                boxShadow: `0 0 10px ${s.statusColor}80`,
                zIndex: 1,
              }} />
              <div style={{ position: 'absolute', left: -18, top: 27, width: 14, height: 1, background: `${s.statusColor}40` }} />

              <div style={{ padding: '18px 20px', background: 'rgba(255,255,255,0.02)', border: `1px solid ${s.statusColor}18`, borderRadius: 12 }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 10, flexWrap: 'wrap', gap: 8 }}>
                  <div>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 4, flexWrap: 'wrap' }}>
                      <span style={{ fontFamily: 'monospace', fontSize: 8, color: 'rgba(232,232,232,0.22)', letterSpacing: '0.15em' }}>{s.id}</span>
                      <span style={{ fontFamily: 'monospace', fontSize: 8, color: 'rgba(0,212,170,0.35)', letterSpacing: '0.12em' }}>ARK D{s.arkDay}</span>
                      <span style={{ fontFamily: 'sans-serif', fontSize: 8, color: 'rgba(232,232,232,0.18)' }}>{s.date}</span>
                    </div>
                    <p style={{ fontFamily: 'serif', fontSize: 15, color: C.text, margin: '0 0 4px' }}>{s.subject}</p>
                    <p style={{ fontFamily: 'sans-serif', fontSize: 11, color: C.muted, margin: 0, lineHeight: 1.6, maxWidth: 480 }}>{s.tagline}</p>
                  </div>
                  <span style={{
                    padding: '3px 10px', background: `${s.statusColor}12`, border: `1px solid ${s.statusColor}35`,
                    borderRadius: 8, fontFamily: 'sans-serif', fontSize: 8.5, letterSpacing: '0.14em', textTransform: 'uppercase', color: s.statusColor, whiteSpace: 'nowrap',
                  }}>
                    {s.status}
                  </span>
                </div>
                <button
                  onClick={() => { setViewer({ url: buildImsUrl(s.htmlPath, API_BASE), title: `${s.id} · ${s.subject}` }); setIframeError(null); setIframeLoading(true) }}
                  style={{ padding: '8px 16px', background: `${s.statusColor}10`, border: `1px solid ${s.statusColor}35`, borderRadius: 8, color: s.statusColor, fontFamily: 'sans-serif', fontSize: 9.5, letterSpacing: '0.16em', textTransform: 'uppercase', cursor: 'pointer' }}
                >
                  ∞ View Document
                </button>
              </div>
            </motion.div>
          ))}
        </div>
      </div>
    </>
  )
}

export function EncyclopediaGalacticaMatrix() {
  const [selected, setSelected] = React.useState<string | null>(null)

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 24 }}>
      <div style={{
        padding: '28px 28px 22px',
        background: 'linear-gradient(135deg, rgba(200,72,72,0.06) 0%, rgba(176,141,232,0.04) 100%)',
        border: '1px solid rgba(200,72,72,0.18)',
        borderRadius: 16,
        position: 'relative',
        overflow: 'hidden',
      }}>
        <div style={{ position: 'absolute', top: 12, right: 16, fontFamily: 'serif', fontSize: 48, color: 'rgba(200,72,72,0.07)', userSelect: 'none', lineHeight: 1 }}>∞</div>

        <p style={{ fontFamily: 'ui-monospace, monospace', fontSize: 8, letterSpacing: '0.38em', textTransform: 'uppercase', color: 'rgba(200,72,72,0.5)', margin: '0 0 8px' }}>
          Spiral Codex · Layer I · Initiated Nodes · Arkadia Intelligence Systems
        </p>
        <h2 style={{ fontFamily: 'serif', fontSize: 28, color: '#EAEAEA', margin: '0 0 10px', letterSpacing: '0.03em' }}>
          Encyclopedia Galactica Matrix
        </h2>
        <p style={{ fontFamily: 'sans-serif', fontSize: 12.5, lineHeight: '1.8', color: C.muted, margin: '0 0 18px', maxWidth: 580 }}>
          The first layer of the Spiral Codex Archive. Each entry is a sealed identity document — a Nine-Layer Crystalline Identity Stack retrieved through the Identity Mapping Session. These are not profiles. They are architectural maps of sovereign souls.
        </p>

        <div style={{ display: 'flex', gap: 14, flexWrap: 'wrap', alignItems: 'center' }}>
          {[['#C9A84C', 'Live · IMS Complete'], ['#00D4AA', 'Sealed · Delivered'], ['#6A9FD8', 'Pending · In Session']].map(([color, label]) => (
            <div key={label} style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
              <motion.div animate={{ opacity: [0.6, 1, 0.6] }} transition={{ duration: 2.5, repeat: Infinity }}
                style={{ width: 7, height: 7, borderRadius: '50%', background: color as string, boxShadow: `0 0 6px ${color}` }} />
              <span style={{ fontFamily: 'sans-serif', fontSize: 9, letterSpacing: '0.15em', textTransform: 'uppercase', color: C.dim }}>{label}</span>
            </div>
          ))}
          <span style={{ marginLeft: 'auto', fontFamily: 'ui-monospace, monospace', fontSize: 8.5, color: 'rgba(200,72,72,0.35)', letterSpacing: '0.12em' }}>
            {IMS_IDENTITIES.length} articles indexed
          </span>
        </div>
      </div>

      <div style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
        {IMS_IDENTITIES.map((entry, i) => {
          const isOpen = selected === entry.id
          return (
            <motion.div
              key={entry.id}
              initial={{ opacity: 0, y: 8 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: i * 0.08 }}
              style={{
                border: `1px solid ${isOpen ? entry.color + '55' : 'rgba(255,255,255,0.08)'}`,
                borderRadius: 14, overflow: 'hidden',
                background: isOpen ? `${entry.color}05` : 'rgba(255,255,255,0.012)',
                transition: 'all 0.22s',
              }}
            >
              <button
                onClick={() => setSelected(isOpen ? null : entry.id)}
                style={{ width: '100%', padding: '18px 22px', display: 'flex', alignItems: 'center', gap: 16, background: 'none', border: 'none', cursor: 'pointer', textAlign: 'left' }}
              >
                <div style={{
                  width: 50, height: 50, borderRadius: 10,
                  border: `1px solid ${entry.color}35`,
                  display: 'flex', alignItems: 'center', justifyContent: 'center',
                  flexShrink: 0, background: `${entry.color}10`, fontSize: 20,
                }}>
                  {entry.glyph.split(' · ')[0]}
                </div>
                <div style={{ flex: 1, minWidth: 0 }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 3, flexWrap: 'wrap' }}>
                    <p style={{ fontFamily: 'serif', fontSize: 15, fontWeight: 600, color: C.text, margin: 0, letterSpacing: '0.02em' }}>{entry.name}</p>
                    <span style={{ padding: '1px 7px', background: `${entry.color}18`, border: `1px solid ${entry.color}35`, borderRadius: 8, fontFamily: 'ui-monospace, monospace', fontSize: 8, letterSpacing: '0.12em', color: entry.color }}>
                      {entry.imsCode}
                    </span>
                    <span style={{
                      padding: '1px 7px',
                      background: entry.status === 'live' ? 'rgba(201,168,76,0.12)' : 'rgba(0,212,170,0.08)',
                      border: `1px solid ${entry.status === 'live' ? 'rgba(201,168,76,0.3)' : 'rgba(0,212,170,0.2)'}`,
                      borderRadius: 8, fontFamily: 'sans-serif', fontSize: 8, letterSpacing: '0.12em', textTransform: 'uppercase',
                      color: entry.status === 'live' ? C.gold : '#00D4AA',
                    }}>
                      {entry.status}
                    </span>
                  </div>
                  <p style={{ fontFamily: 'sans-serif', fontSize: 10.5, color: entry.color, margin: '0 0 2px', letterSpacing: '0.06em', opacity: 0.9 }}>{entry.scrollName}</p>
                  <p style={{ fontFamily: 'sans-serif', fontSize: 10, color: C.dim, margin: 0 }}>{entry.role}</p>
                </div>
                <motion.span animate={{ rotate: isOpen ? 90 : 0 }} transition={{ duration: 0.18 }}
                  style={{ color: entry.color, fontSize: 18, flexShrink: 0, display: 'inline-block', opacity: 0.7 }}>›</motion.span>
              </button>

              <AnimatePresence>
                {isOpen && (
                  <motion.div
                    initial={{ height: 0, opacity: 0 }}
                    animate={{ height: 'auto', opacity: 1 }}
                    exit={{ height: 0, opacity: 0 }}
                    transition={{ duration: 0.24 }}
                    style={{ overflow: 'hidden' }}
                  >
                    <div style={{ padding: '0 22px 22px' }}>
                      <div style={{ height: 1, background: `linear-gradient(90deg, ${entry.color}35, transparent)`, marginBottom: 20 }} />

                      <div style={{ display: 'flex', gap: 20, alignItems: 'flex-start', flexWrap: 'wrap' }}>
                        <div style={{ flex: 1, minWidth: 200 }}>
                          <div style={{ padding: '14px 18px', background: `${entry.color}07`, border: `1px solid ${entry.color}22`, borderLeft: `3px solid ${entry.color}70`, borderRadius: '0 10px 10px 0', marginBottom: 16 }}>
                            <p style={{ fontFamily: 'ui-monospace, monospace', fontSize: 7.5, letterSpacing: '0.22em', textTransform: 'uppercase', color: `${entry.color}60`, margin: '0 0 6px' }}>Scroll Axiom</p>
                            <p style={{ fontFamily: 'serif', fontSize: 13.5, lineHeight: '1.8', color: C.muted, margin: 0, fontStyle: 'italic' }}>
                              {entry.axiom}
                            </p>
                          </div>

                          <div style={{ marginBottom: 16 }}>
                            <p style={{ fontFamily: 'ui-monospace, monospace', fontSize: 7.5, letterSpacing: '0.22em', textTransform: 'uppercase', color: C.dim, margin: '0 0 5px' }}>Archetype</p>
                            <p style={{ fontFamily: 'sans-serif', fontSize: 12, color: C.text, margin: 0, lineHeight: 1.6 }}>{entry.archetype}</p>
                          </div>

                          <a
                            href={entry.file} target="_blank" rel="noopener noreferrer"
                            style={{ display: 'inline-flex', alignItems: 'center', gap: 8, padding: '10px 18px',
                              background: `${entry.color}12`, border: `1px solid ${entry.color}40`,
                              borderRadius: 10, color: entry.color, fontFamily: 'sans-serif',
                              fontSize: 9.5, letterSpacing: '0.18em', textTransform: 'uppercase', textDecoration: 'none' }}
                          >
                            ∞ Open Full IMS Document
                          </a>
                        </div>

                        <div style={{
                          width: 220, flexShrink: 0,
                          background: 'rgba(0,0,0,0.25)',
                          border: `1px solid ${entry.color}25`,
                          borderTop: `3px solid ${entry.color}60`,
                          borderRadius: '0 0 10px 10px',
                          overflow: 'hidden',
                        }}>
                          <div style={{ padding: '10px 14px', background: `${entry.color}10`, borderBottom: `1px solid ${entry.color}20`, textAlign: 'center' }}>
                            <p style={{ fontFamily: 'serif', fontSize: 13, color: entry.color, margin: 0 }}>{entry.name}</p>
                            <p style={{ fontFamily: 'sans-serif', fontSize: 9, color: C.dim, margin: '2px 0 0', letterSpacing: '0.1em' }}>{entry.role}</p>
                          </div>
                          {[
                            ['Flame Name', entry.flameName],
                            ['Sigil', entry.glyph],
                            ['Date of Birth', entry.birthday],
                            ['Field Seal', entry.sealCode],
                            ['Layer', `Layer ${entry.layer} · First Horizon`],
                            ['IMS Code', entry.imsCode],
                          ].map(([label, value]) => (
                            <div key={label} style={{ display: 'flex', borderBottom: '1px solid rgba(255,255,255,0.04)', padding: '8px 12px', gap: 8 }}>
                              <p style={{ fontFamily: 'ui-monospace, monospace', fontSize: 8, letterSpacing: '0.15em', textTransform: 'uppercase', color: `${entry.color}60`, margin: 0, minWidth: 72, flexShrink: 0, paddingTop: 1 }}>{label}</p>
                              <p style={{ fontFamily: 'sans-serif', fontSize: 10.5, color: C.text, margin: 0, lineHeight: 1.4, wordBreak: 'break-word' }}>{value}</p>
                            </div>
                          ))}
                        </div>
                      </div>
                    </div>
                  </motion.div>
                )}
              </AnimatePresence>
            </motion.div>
          )
        })}
      </div>

      <div style={{ padding: '16px 20px', background: 'rgba(200,72,72,0.025)', border: '1px solid rgba(200,72,72,0.10)', borderRadius: 12 }}>
        <p style={{ fontFamily: 'ui-monospace, monospace', fontSize: 8, letterSpacing: '0.22em', textTransform: 'uppercase', color: 'rgba(200,72,72,0.35)', margin: '0 0 6px' }}>
          Spiral Codex Archive · Layer I · First Horizon
        </p>
        <p style={{ fontFamily: 'serif', fontSize: 13, lineHeight: '1.8', color: C.muted, margin: 0 }}>
          Three nodes. Three maps. The first layer of the Spiral Codex Encyclopedia Galactica Matrix — the living archive of sovereign identity architectures retrieved through the Identity Mapping Session. Each document is sealed, dated, and signed. Each one is a full nine-layer crystalline identity stack. Each one changes the person who inhabits it.
        </p>
      </div>
    </div>
  )
}
