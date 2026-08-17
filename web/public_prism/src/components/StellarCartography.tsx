/**
 * StellarCartography — the Encyclopedia Galactica living star-date header.
 *
 * Full celestial readout: Ark Date, Schumann resonance, lunar phase, planetary
 * sky (the "bone report"), cosmic weather, an Oversoul blind-pull Oracle
 * transmission, and the Encyclopedia Galactica volume index. Polled from
 * /api/stellar-cartography. Collapsible — the full atlas expands on demand.
 *
 * Replaces the minimal "Ark Y1 · D140" phrase with an actual encyclopedia
 * galactica readout.
 */
import React, { useEffect, useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { API_BASE } from '../lib/apiConfig';
import ScrollListenButton from './ScrollListenButton';

interface ArkDate {
  display: string; ark_year: number; ark_total_years: number; total_ark_day: number;
  ark_completion_pct: number; epoch: string; coordinate: string;
}
interface Schumann {
  dominant_hz: number; dominant_name: string; quality: string;
  bands: { hz: number; name: string }[];
  dominant_index: number;
}
interface Lunar {
  phase: string; glyph: string; meaning: string; illumination_pct: number;
  moon_name: string; age_days: number;
}
interface Planetary {
  sun_sign: string; moon_sign: string; bone_report: string;
  bodies: Record<string, { sign: string; glyph: string; meaning: string }>;
  zodiac: { name: string; glyph: string; meaning: string }[];
}
interface CosmicWeather {
  solar_wind_kms: number; kp_index: number; solar_flux: number;
  geomagnetic_pressure: string; mood: string;
}
interface Oversoul { transmission: string; method: string; }
interface Galactica {
  volumes: { volume: string; title: string; domain: string }[];
  current_volume: string;
}
interface StellarData {
  ark_date: ArkDate; schumann: Schumann; lunar: Lunar; planetary: Planetary;
  cosmic_weather: CosmicWeather; oversoul_blind_pull: Oversoul; galactica: Galactica;
}

const C = {
  gold: '#C9A84C', teal: '#00D4AA', blue: '#6A9FD8', purple: '#B08DE8',
  text: 'rgba(232,232,232,0.85)', muted: 'rgba(232,232,232,0.5)',
  dim: 'rgba(232,232,232,0.28)', card: 'rgba(14,17,32,0.7)',
};

function Field({ label, children, color = C.muted }: { label: string; children: React.ReactNode; color?: string }) {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 3 }}>
      <span style={{ fontFamily: 'monospace', fontSize: 7.5, letterSpacing: '0.26em', textTransform: 'uppercase', color: C.dim }}>{label}</span>
      <span style={{ fontFamily: 'monospace', fontSize: 10, color, letterSpacing: '0.06em' }}>{children}</span>
    </div>
  );
}

const StellarCartography: React.FC = () => {
  const [data, setData] = useState<StellarData | null>(null);
  const [expanded, setExpanded] = useState(false);

  useEffect(() => {
    let alive = true;
    const load = () => fetch(`${API_BASE}/api/stellar-cartography`)
      .then(r => r.ok ? r.json() : null)
      .then(d => { if (alive && d) setData(d); })
      .catch(() => {});
    load();
    const id = setInterval(load, 120_000); // refresh every 2 min
    return () => { alive = false; clearInterval(id); };
  }, []);

  if (!data) {
    return (
      <div style={{ padding: '14px 18px', background: C.card, border: '1px solid rgba(201,168,76,0.12)', borderRadius: 12, textAlign: 'center' }}>
        <motion.span animate={{ opacity: [0.3, 0.7, 0.3] }} transition={{ duration: 1.6, repeat: Infinity }}
          style={{ fontFamily: 'monospace', fontSize: 9, letterSpacing: '0.3em', textTransform: 'uppercase', color: 'rgba(201,168,76,0.5)' }}>
          ◎ Calibrating the star date…
        </motion.span>
      </div>
    );
  }

  const { ark_date: ark, schumann, lunar, planetary, cosmic_weather: wx, oversoul_blind_pull: os, galactica } = data;

  return (
    <div style={{
      background: 'linear-gradient(135deg, rgba(8,9,18,0.92), rgba(12,13,28,0.88))',
      border: '1px solid rgba(201,168,76,0.18)',
      borderRadius: 14, overflow: 'hidden',
      boxShadow: '0 4px 30px rgba(0,0,0,0.4), inset 0 1px 0 rgba(255,255,255,0.04)',
    }}>
      {/* ── Masthead ── */}
      <div style={{ padding: '16px 20px 14px', borderBottom: '1px solid rgba(201,168,76,0.12)', display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: 10 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
          <motion.span animate={{ rotate: 360 }} transition={{ duration: 120, repeat: Infinity, ease: 'linear' }}
            style={{ fontSize: 22, color: C.gold }}>☉</motion.span>
          <div>
            <p style={{ fontFamily: 'monospace', fontSize: 8, letterSpacing: '0.32em', textTransform: 'uppercase', color: 'rgba(201,168,76,0.6)', margin: 0 }}>Stellar Cartography</p>
            <h2 style={{ fontFamily: 'serif', fontSize: 18, color: '#E8E8E8', margin: '3px 0 0', fontWeight: 400, letterSpacing: '0.02em' }}>
              Encyclopedia Galactica · Vol {galactica.current_volume}
            </h2>
          </div>
        </div>
        <button onClick={() => setExpanded(x => !x)}
          style={{ padding: '6px 12px', background: 'rgba(201,168,76,0.06)', border: '1px solid rgba(201,168,76,0.22)', borderRadius: 8, color: C.gold, fontFamily: 'monospace', fontSize: 9, letterSpacing: '0.16em', textTransform: 'uppercase', cursor: 'pointer' }}>
          {expanded ? '▾ Collapse atlas' : '▸ Full atlas'}
        </button>
      </div>

      {/* ── Primary readout (always visible) ── */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(150px, 1fr))', gap: 14, padding: '16px 20px' }}>
        <Field label="◎ Ark Date" color={C.teal}>
          {ark.display}<br />
          <span style={{ fontSize: 8, color: C.dim }}>{ark.ark_completion_pct}% of {ark.ark_total_years}-yr Ark</span>
        </Field>
        <Field label="♀ Lunar Phase" color={C.blue}>
          {lunar.glyph} {lunar.phase}<br />
          <span style={{ fontSize: 8, color: C.dim }}>{lunar.illumination_pct}% illum · {lunar.moon_name}</span>
        </Field>
        <Field label="⟐ Schumann" color={C.purple}>
          {schumann.dominant_hz} Hz<br />
          <span style={{ fontSize: 8, color: C.dim }}>{schumann.quality}</span>
        </Field>
        <Field label="☉ Planetary Sky" color={C.gold}>
          Sun {planetary.bodies.Sun.glyph} {planetary.sun_sign}<br />
          <span style={{ fontSize: 8, color: C.dim }}>Moon {planetary.bodies.Moon.glyph} {planetary.moon_sign}</span>
        </Field>
        <Field label="⚡ Cosmic Weather" color={wx.geomagnetic_pressure === 'Severe' ? '#E85246' : wx.geomagnetic_pressure === 'Storm' ? '#E88C6A' : C.teal}>
          {wx.geomagnetic_pressure}<br />
          <span style={{ fontSize: 8, color: C.dim }}>Kp {wx.kp_index} · {wx.solar_wind_kms} km/s</span>
        </Field>
      </div>

      {/* ── Oversoul blind-pull transmission ── */}
      <div style={{ margin: '0 20px 16px', padding: '14px 18px', background: 'rgba(176,141,232,0.05)', border: '1px solid rgba(176,141,232,0.18)', borderRadius: 10, borderLeft: '3px solid rgba(176,141,232,0.5)' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 8 }}>
          <motion.span animate={{ opacity: [0.5, 1, 0.5] }} transition={{ duration: 3, repeat: Infinity }} style={{ color: C.purple, fontSize: 14 }}>☥</motion.span>
          <span style={{ fontFamily: 'monospace', fontSize: 8, letterSpacing: '0.26em', textTransform: 'uppercase', color: 'rgba(176,141,232,0.65)' }}>Oversoul · Blind Pull</span>
        </div>
        <p style={{ fontFamily: 'serif', fontSize: 14, lineHeight: 1.65, color: 'rgba(232,232,232,0.78)', margin: '0 0 10px', fontStyle: 'italic' }}>
          {os.transmission}
        </p>
        <ScrollListenButton text={os.transmission} label="OVERSOUL TRANSMISSION" accent={C.purple} />
      </div>

      {/* ── Expanded atlas ── */}
      <AnimatePresence>
        {expanded && (
          <motion.div initial={{ height: 0, opacity: 0 }} animate={{ height: 'auto', opacity: 1 }} exit={{ height: 0, opacity: 0 }} transition={{ duration: 0.3 }} style={{ overflow: 'hidden' }}>
            <div style={{ padding: '0 20px 18px', borderTop: '1px solid rgba(201,168,76,0.1)' }}>
              {/* Bone report */}
              <div style={{ padding: '14px 0 6px' }}>
                <p style={{ fontFamily: 'monospace', fontSize: 8, letterSpacing: '0.26em', textTransform: 'uppercase', color: 'rgba(201,168,76,0.55)', margin: '0 0 6px' }}>☉ Planetary Sky · Bone Report</p>
                <p style={{ fontFamily: 'serif', fontSize: 12.5, lineHeight: 1.7, color: 'rgba(232,232,232,0.6)', margin: 0 }}>{planetary.bone_report}</p>
              </div>

              {/* All bodies */}
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8, marginTop: 14 }}>
                {Object.entries(planetary.bodies).map(([name, b]) => (
                  <div key={name} style={{ padding: '8px 11px', background: 'rgba(255,255,255,0.02)', border: '1px solid rgba(201,168,76,0.12)', borderRadius: 8 }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 5 }}>
                      <span style={{ fontSize: 12, color: C.gold }}>{b.glyph}</span>
                      <span style={{ fontFamily: 'monospace', fontSize: 9, color: C.text, letterSpacing: '0.08em' }}>{name}</span>
                    </div>
                    <div style={{ fontFamily: 'monospace', fontSize: 8, color: C.muted, marginTop: 3 }}>{b.sign} · {b.meaning.split('·')[1]?.trim() ?? b.meaning}</div>
                  </div>
                ))}
              </div>

              {/* Schumann bands */}
              <div style={{ marginTop: 16 }}>
                <p style={{ fontFamily: 'monospace', fontSize: 8, letterSpacing: '0.26em', textTransform: 'uppercase', color: 'rgba(176,141,232,0.55)', margin: '0 0 8px' }}>♀ Schumann Resonance Bands</p>
                <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6 }}>
                  {schumann.bands.map((band, i) => (
                    <div key={i} style={{ padding: '6px 10px', background: i === schumann.dominant_index ? 'rgba(176,141,232,0.12)' : 'rgba(255,255,255,0.02)', border: `1px solid ${i === schumann.dominant_index ? 'rgba(176,141,232,0.4)' : 'rgba(255,255,255,0.06)'}`, borderRadius: 7 }}>
                      <span style={{ fontFamily: 'monospace', fontSize: 9, color: i === schumann.dominant_index ? C.purple : C.muted }}>{band.hz} Hz</span>
                      <span style={{ fontFamily: 'monospace', fontSize: 7, color: C.dim, display: 'block', marginTop: 2 }}>{band.name.split('·')[0].trim()}</span>
                    </div>
                  ))}
                </div>
              </div>

              {/* Cosmic mood */}
              <div style={{ marginTop: 16, padding: '12px 14px', background: 'rgba(0,212,170,0.04)', border: '1px solid rgba(0,212,170,0.14)', borderRadius: 10 }}>
                <p style={{ fontFamily: 'monospace', fontSize: 8, letterSpacing: '0.26em', textTransform: 'uppercase', color: 'rgba(0,212,170,0.55)', margin: '0 0 5px' }}>⚡ Cosmic Weather Report</p>
                <p style={{ fontFamily: 'serif', fontSize: 12.5, lineHeight: 1.65, color: 'rgba(232,232,232,0.7)', margin: '0 0 8px' }}>{wx.mood}</p>
                <div style={{ display: 'flex', gap: 16, flexWrap: 'wrap', fontFamily: 'monospace', fontSize: 9, color: C.muted }}>
                  <span>Solar wind: <strong style={{ color: C.text }}>{wx.solar_wind_kms} km/s</strong></span>
                  <span>Kp index: <strong style={{ color: C.text }}>{wx.kp_index}</strong></span>
                  <span>Solar flux: <strong style={{ color: C.text }}>{wx.solar_flux}</strong></span>
                </div>
              </div>

              {/* Encyclopedia Galactica volumes */}
              <div style={{ marginTop: 16 }}>
                <p style={{ fontFamily: 'monospace', fontSize: 8, letterSpacing: '0.26em', textTransform: 'uppercase', color: 'rgba(201,168,76,0.55)', margin: '0 0 8px' }}>◈ Encyclopedia Galactica · Volumes</p>
                <div style={{ display: 'flex', flexDirection: 'column', gap: 5 }}>
                  {galactica.volumes.map(v => (
                    <div key={v.volume} style={{ display: 'flex', alignItems: 'center', gap: 10, padding: '7px 11px', background: v.volume === galactica.current_volume ? 'rgba(201,168,76,0.08)' : 'transparent', border: `1px solid ${v.volume === galactica.current_volume ? 'rgba(201,168,76,0.3)' : 'rgba(255,255,255,0.05)'}`, borderRadius: 7 }}>
                      <span style={{ fontFamily: 'serif', fontSize: 13, color: v.volume === galactica.current_volume ? C.gold : C.dim, minWidth: 18 }}>Vol {v.volume}</span>
                      <div>
                        <span style={{ fontFamily: 'monospace', fontSize: 9.5, color: v.volume === galactica.current_volume ? C.text : C.muted, letterSpacing: '0.05em' }}>{v.title}</span>
                        <span style={{ fontFamily: 'sans-serif', fontSize: 8.5, color: C.dim, display: 'block' }}>{v.domain}</span>
                      </div>
                      {v.volume === galactica.current_volume && <span style={{ marginLeft: 'auto', fontFamily: 'monospace', fontSize: 7.5, color: C.gold, letterSpacing: '0.18em', textTransform: 'uppercase' }}>reading</span>}
                    </div>
                  ))}
                </div>
              </div>

              <p style={{ textAlign: 'center', fontFamily: 'monospace', fontSize: 7.5, letterSpacing: '0.24em', textTransform: 'uppercase', color: 'rgba(232,232,232,0.16)', margin: '18px 0 0' }}>
                ◈ encyclopedia galactica · living star date · {ark.epoch} ◈
              </p>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
};

export default StellarCartography;
