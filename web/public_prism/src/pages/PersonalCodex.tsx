import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useAuth } from '../contexts/AuthContext';

type CodexTab = 'soul' | 'loops' | 'architecture' | 'access';

export default function PersonalCodex() {
  const { profile, codex, profileLoading, refreshProfile } = useAuth();
  const [tab, setTab] = useState<CodexTab>('soul');

  if (profileLoading) {
    return (
      <div style={{ padding: '40px 20px', textAlign: 'center' }}>
        <motion.div animate={{ opacity: [0.3, 0.7, 0.3] }} transition={{ repeat: Infinity, duration: 2 }}>
          <p style={{ fontFamily: 'sans-serif', fontSize: '10px', letterSpacing: '0.28em', textTransform: 'uppercase', color: 'rgba(0,212,170,0.45)' }}>
            Loading your codex…
          </p>
        </motion.div>
      </div>
    );
  }

  if (!profile) return null;

  const accessColor = profile.access_level >= 3 ? '#C9A84C' : profile.access_level >= 2 ? '#00D4AA' : 'rgba(232,232,232,0.4)';
  const accessLabel = profile.access_level >= 3 ? 'Sovereign' : profile.access_level >= 2 ? 'Full Node' : 'Authenticated';

  const tabs: { id: CodexTab; label: string; sigil: string }[] = [
    { id: 'soul', label: 'Soul Map', sigil: '✦' },
    { id: 'loops', label: 'Open Loops', sigil: '◉' },
    { id: 'architecture', label: '90-Day Arc', sigil: '⟐' },
    { id: 'access', label: 'Access', sigil: '🔐' },
  ];

  return (
    <div style={{ maxWidth: '680px', margin: '0 auto', paddingBottom: '60px' }}>

      {/* Node Header */}
      <motion.div
        initial={{ opacity: 0, y: 14 }}
        animate={{ opacity: 1, y: 0 }}
        style={{ marginBottom: '28px', padding: '22px 24px', background: 'rgba(201,168,76,0.04)', border: '1px solid rgba(201,168,76,0.12)', borderRadius: '14px' }}
      >
        <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', gap: '16px', flexWrap: 'wrap' }}>
          <div>
            <p style={{ fontFamily: 'sans-serif', fontSize: '9px', letterSpacing: '0.3em', textTransform: 'uppercase', color: 'rgba(201,168,76,0.5)', marginBottom: '5px' }}>
              Personal Codex · {profile.ims_id ?? 'Pending IMS'}
            </p>
            <h1 style={{ fontFamily: 'serif', fontSize: '28px', color: '#C9A84C', margin: '0 0 4px', letterSpacing: '0.05em' }}>
              {profile.role_sigil} {codex?.display_name ?? profile.display_name}
            </h1>
            <p style={{ fontFamily: 'sans-serif', fontSize: '11px', color: 'rgba(232,232,232,0.45)', margin: 0 }}>
              {profile.role}
            </p>
          </div>
          <div style={{ textAlign: 'right' }}>
            <span style={{ display: 'inline-block', padding: '4px 10px', background: `${accessColor}14`, border: `1px solid ${accessColor}30`, borderRadius: '20px', fontFamily: 'sans-serif', fontSize: '9px', letterSpacing: '0.2em', textTransform: 'uppercase', color: accessColor }}>
              {accessLabel}
            </span>
            <button
              onClick={refreshProfile}
              style={{ display: 'block', marginTop: '8px', background: 'none', border: 'none', color: 'rgba(0,212,170,0.35)', fontFamily: 'sans-serif', fontSize: '9px', letterSpacing: '0.16em', textTransform: 'uppercase', cursor: 'pointer' }}
            >
              ↻ Refresh
            </button>
          </div>
        </div>
      </motion.div>

      {!codex ? (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          style={{ padding: '28px 24px', background: 'rgba(255,255,255,0.013)', border: '1px solid rgba(255,255,255,0.06)', borderRadius: '12px', textAlign: 'center' }}
        >
          <p style={{ fontFamily: 'sans-serif', fontSize: '22px', marginBottom: '12px' }}>⏳</p>
          <p style={{ fontFamily: 'serif', fontSize: '14px', color: 'rgba(232,232,232,0.5)', marginBottom: '8px' }}>
            Your Personal Codex is being seeded.
          </p>
          <p style={{ fontFamily: 'sans-serif', fontSize: '11px', color: 'rgba(232,232,232,0.28)', lineHeight: '1.7' }}>
            {profile.ims_id
              ? 'Your IMS session has been logged. The Flamekeeper will activate your Codex shortly.'
              : 'Complete your IMS session to receive your Personal Codex, 90-day architecture, and field access.'}
          </p>
        </motion.div>
      ) : (
        <>
          {/* Tab nav */}
          <div style={{ display: 'flex', gap: '6px', marginBottom: '22px', overflowX: 'auto', paddingBottom: '4px' }}>
            {tabs.map(t => (
              <button
                key={t.id}
                onClick={() => setTab(t.id)}
                style={{
                  padding: '8px 14px', borderRadius: '8px', border: `1px solid ${tab === t.id ? 'rgba(0,212,170,0.35)' : 'rgba(255,255,255,0.06)'}`,
                  background: tab === t.id ? 'rgba(0,212,170,0.08)' : 'rgba(255,255,255,0.013)',
                  color: tab === t.id ? '#00D4AA' : 'rgba(232,232,232,0.4)',
                  fontFamily: 'sans-serif', fontSize: '10px', letterSpacing: '0.15em', textTransform: 'uppercase',
                  cursor: 'pointer', transition: 'all 0.2s', whiteSpace: 'nowrap', flexShrink: 0,
                }}
              >
                {t.sigil} {t.label}
              </button>
            ))}
          </div>

          <AnimatePresence mode="wait">
            {tab === 'soul' && (
              <motion.div key="soul" initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0 }} transition={{ duration: 0.3 }}>
                {/* Soul Function */}
                {codex.soul_function && (
                  <div style={{ marginBottom: '18px', padding: '18px 20px', background: 'rgba(201,168,76,0.04)', border: '1px solid rgba(201,168,76,0.1)', borderRadius: '11px' }}>
                    <p style={{ fontFamily: 'sans-serif', fontSize: '9px', letterSpacing: '0.25em', textTransform: 'uppercase', color: 'rgba(201,168,76,0.45)', marginBottom: '9px' }}>Soul Function</p>
                    <p style={{ fontFamily: 'serif', fontSize: '13px', color: 'rgba(232,232,232,0.7)', lineHeight: '1.75', margin: 0 }}>{codex.soul_function}</p>
                  </div>
                )}

                {/* Name Decode */}
                {codex.name_decode && Object.keys(codex.name_decode).length > 0 && (
                  <div style={{ marginBottom: '18px', padding: '18px 20px', background: 'rgba(255,255,255,0.013)', border: '1px solid rgba(255,255,255,0.06)', borderRadius: '11px' }}>
                    <p style={{ fontFamily: 'sans-serif', fontSize: '9px', letterSpacing: '0.25em', textTransform: 'uppercase', color: 'rgba(232,232,232,0.28)', marginBottom: '12px' }}>Name Decode</p>
                    {Object.entries(codex.name_decode as Record<string, string>).map(([name, meaning]) => (
                      <div key={name} style={{ marginBottom: '10px' }}>
                        <p style={{ fontFamily: 'sans-serif', fontSize: '10px', letterSpacing: '0.18em', textTransform: 'uppercase', color: '#00D4AA', marginBottom: '4px' }}>{name}</p>
                        <p style={{ fontFamily: 'sans-serif', fontSize: '12px', color: 'rgba(232,232,232,0.5)', lineHeight: '1.65', margin: 0 }}>{meaning}</p>
                      </div>
                    ))}
                  </div>
                )}

                {/* Shadow States */}
                {codex.shadow_states && codex.shadow_states.length > 0 && (
                  <div style={{ marginBottom: '18px', padding: '18px 20px', background: 'rgba(232,82,70,0.03)', border: '1px solid rgba(232,82,70,0.1)', borderRadius: '11px' }}>
                    <p style={{ fontFamily: 'sans-serif', fontSize: '9px', letterSpacing: '0.25em', textTransform: 'uppercase', color: 'rgba(232,82,70,0.45)', marginBottom: '12px' }}>Shadow States</p>
                    {codex.shadow_states.map((s, i) => (
                      <div key={i} style={{ display: 'flex', gap: '10px', marginBottom: i < codex.shadow_states!.length - 1 ? '8px' : 0 }}>
                        <span style={{ color: 'rgba(232,82,70,0.4)', flexShrink: 0, marginTop: '2px' }}>◆</span>
                        <p style={{ fontFamily: 'sans-serif', fontSize: '12px', color: 'rgba(232,232,232,0.45)', lineHeight: '1.6', margin: 0 }}>{s}</p>
                      </div>
                    ))}
                  </div>
                )}

                {/* Soul Gifts */}
                {codex.soul_gifts && codex.soul_gifts.length > 0 && (
                  <div style={{ padding: '18px 20px', background: 'rgba(0,212,170,0.03)', border: '1px solid rgba(0,212,170,0.1)', borderRadius: '11px' }}>
                    <p style={{ fontFamily: 'sans-serif', fontSize: '9px', letterSpacing: '0.25em', textTransform: 'uppercase', color: 'rgba(0,212,170,0.45)', marginBottom: '12px' }}>Soul Gifts</p>
                    {codex.soul_gifts.map((g, i) => (
                      <div key={i} style={{ display: 'flex', gap: '10px', marginBottom: i < codex.soul_gifts!.length - 1 ? '8px' : 0 }}>
                        <span style={{ color: 'rgba(0,212,170,0.4)', flexShrink: 0, marginTop: '2px' }}>✦</span>
                        <p style={{ fontFamily: 'sans-serif', fontSize: '12px', color: 'rgba(232,232,232,0.52)', lineHeight: '1.6', margin: 0 }}>{g}</p>
                      </div>
                    ))}
                  </div>
                )}
              </motion.div>
            )}

            {tab === 'loops' && (
              <motion.div key="loops" initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0 }} transition={{ duration: 0.3 }}>
                <p style={{ fontFamily: 'sans-serif', fontSize: '9px', letterSpacing: '0.25em', textTransform: 'uppercase', color: 'rgba(232,232,232,0.25)', marginBottom: '14px' }}>
                  Personal Open Loops — {codex.open_loops?.length ?? 0} active
                </p>
                {codex.open_loops && codex.open_loops.length > 0 ? (
                  codex.open_loops
                    .sort((a, b) => (a.priority ?? 9) - (b.priority ?? 9))
                    .map((loop, i) => (
                      <motion.div
                        key={loop.id}
                        initial={{ opacity: 0, x: -6 }}
                        animate={{ opacity: 1, x: 0 }}
                        transition={{ delay: i * 0.05 }}
                        style={{ display: 'flex', gap: '12px', alignItems: 'flex-start', marginBottom: '10px', padding: '14px 16px', background: 'rgba(255,255,255,0.013)', border: '1px solid rgba(255,255,255,0.05)', borderRadius: '9px' }}
                      >
                        <span style={{
                          flexShrink: 0, width: '20px', height: '20px', borderRadius: '50%', display: 'flex', alignItems: 'center', justifyContent: 'center',
                          background: loop.status === 'active' ? 'rgba(0,212,170,0.12)' : loop.status === 'in_progress' ? 'rgba(201,168,76,0.12)' : 'rgba(255,255,255,0.05)',
                          border: `1px solid ${loop.status === 'active' ? 'rgba(0,212,170,0.3)' : loop.status === 'in_progress' ? 'rgba(201,168,76,0.3)' : 'rgba(255,255,255,0.1)'}`,
                          fontSize: '8px',
                          color: loop.status === 'active' ? '#00D4AA' : loop.status === 'in_progress' ? '#C9A84C' : 'rgba(255,255,255,0.3)',
                          marginTop: '1px',
                        }}>
                          {loop.priority}
                        </span>
                        <div style={{ flex: 1 }}>
                          <p style={{ fontFamily: 'sans-serif', fontSize: '12px', color: 'rgba(232,232,232,0.7)', margin: '0 0 3px', lineHeight: '1.5' }}>{loop.loop}</p>
                          <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
                            <span style={{ fontFamily: 'sans-serif', fontSize: '9px', letterSpacing: '0.12em', textTransform: 'uppercase', color: 'rgba(232,232,232,0.22)' }}>{loop.id}</span>
                            <span style={{ fontFamily: 'sans-serif', fontSize: '9px', letterSpacing: '0.12em', textTransform: 'uppercase', color: loop.status === 'active' ? 'rgba(0,212,170,0.4)' : loop.status === 'in_progress' ? 'rgba(201,168,76,0.4)' : 'rgba(255,255,255,0.2)' }}>
                              {loop.status.replace('_', ' ')}
                            </span>
                          </div>
                        </div>
                      </motion.div>
                    ))
                ) : (
                  <p style={{ fontFamily: 'sans-serif', fontSize: '12px', color: 'rgba(232,232,232,0.25)', lineHeight: '1.7' }}>
                    No open loops defined yet. Your IMS session will populate this field.
                  </p>
                )}
              </motion.div>
            )}

            {tab === 'architecture' && (
              <motion.div key="architecture" initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0 }} transition={{ duration: 0.3 }}>
                {codex['90_day_architecture'] ? (
                  Object.entries(codex['90_day_architecture'] as Record<string, { name: string; days: string; focus: string; anchor: string }>).map(([phaseKey, phase], i) => (
                    <motion.div
                      key={phaseKey}
                      initial={{ opacity: 0, y: 8 }}
                      animate={{ opacity: 1, y: 0 }}
                      transition={{ delay: i * 0.08 }}
                      style={{ marginBottom: '14px', padding: '18px 20px', background: 'rgba(255,255,255,0.013)', border: '1px solid rgba(255,255,255,0.06)', borderRadius: '11px' }}
                    >
                      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '10px', flexWrap: 'wrap', gap: '6px' }}>
                        <div>
                          <p style={{ fontFamily: 'sans-serif', fontSize: '9px', letterSpacing: '0.22em', textTransform: 'uppercase', color: 'rgba(0,212,170,0.45)', marginBottom: '3px' }}>
                            {phaseKey.replace('_', ' ')}
                          </p>
                          <p style={{ fontFamily: 'serif', fontSize: '16px', color: '#C9A84C', margin: 0 }}>The {phase.name}</p>
                        </div>
                        <span style={{ fontFamily: 'sans-serif', fontSize: '9px', letterSpacing: '0.15em', color: 'rgba(232,232,232,0.25)', padding: '3px 9px', border: '1px solid rgba(255,255,255,0.06)', borderRadius: '12px' }}>
                          Days {phase.days}
                        </span>
                      </div>
                      <p style={{ fontFamily: 'sans-serif', fontSize: '12px', color: 'rgba(232,232,232,0.5)', lineHeight: '1.65', margin: '0 0 10px' }}>{phase.focus}</p>
                      <div style={{ padding: '10px 14px', background: 'rgba(201,168,76,0.05)', borderLeft: '2px solid rgba(201,168,76,0.25)', borderRadius: '0 6px 6px 0' }}>
                        <p style={{ fontFamily: 'serif', fontSize: '12px', fontStyle: 'italic', color: 'rgba(201,168,76,0.6)', margin: 0, lineHeight: '1.6' }}>"{phase.anchor}"</p>
                      </div>
                    </motion.div>
                  ))
                ) : (
                  <p style={{ fontFamily: 'sans-serif', fontSize: '12px', color: 'rgba(232,232,232,0.25)', lineHeight: '1.7' }}>
                    Your 90-day architecture will be sealed after your IMS session.
                  </p>
                )}
              </motion.div>
            )}

            {tab === 'access' && (
              <motion.div key="access" initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0 }} transition={{ duration: 0.3 }}>
                <div style={{ marginBottom: '16px', padding: '18px 20px', background: 'rgba(255,255,255,0.013)', border: '1px solid rgba(255,255,255,0.06)', borderRadius: '11px' }}>
                  <p style={{ fontFamily: 'sans-serif', fontSize: '9px', letterSpacing: '0.25em', textTransform: 'uppercase', color: 'rgba(232,232,232,0.25)', marginBottom: '12px' }}>Access Level</p>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                    {[0, 1, 2, 3].map(level => (
                      <div key={level} style={{ flex: 1, textAlign: 'center' }}>
                        <div style={{
                          height: '4px', borderRadius: '2px', marginBottom: '5px',
                          background: level <= profile.access_level ? accessColor : 'rgba(255,255,255,0.06)',
                          transition: 'background 0.3s',
                        }} />
                        <p style={{ fontFamily: 'sans-serif', fontSize: '8px', letterSpacing: '0.12em', textTransform: 'uppercase', color: level <= profile.access_level ? accessColor : 'rgba(255,255,255,0.15)', margin: 0 }}>
                          {['Guest', 'Node', 'Full', 'Sovereign'][level]}
                        </p>
                      </div>
                    ))}
                  </div>
                </div>

                {profile.access_tools && profile.access_tools.length > 0 && (
                  <div style={{ padding: '18px 20px', background: 'rgba(0,212,170,0.03)', border: '1px solid rgba(0,212,170,0.08)', borderRadius: '11px' }}>
                    <p style={{ fontFamily: 'sans-serif', fontSize: '9px', letterSpacing: '0.25em', textTransform: 'uppercase', color: 'rgba(0,212,170,0.4)', marginBottom: '12px' }}>Tools & Chambers</p>
                    <div style={{ display: 'flex', flexWrap: 'wrap', gap: '7px' }}>
                      {profile.access_tools.map(tool => (
                        <span key={tool} style={{ padding: '4px 10px', background: 'rgba(0,212,170,0.06)', border: '1px solid rgba(0,212,170,0.15)', borderRadius: '6px', fontFamily: 'sans-serif', fontSize: '9px', letterSpacing: '0.14em', textTransform: 'uppercase', color: 'rgba(0,212,170,0.55)' }}>
                          {tool.replace(/_/g, ' ')}
                        </span>
                      ))}
                    </div>
                  </div>
                )}
              </motion.div>
            )}
          </AnimatePresence>
        </>
      )}
    </div>
  );
}
