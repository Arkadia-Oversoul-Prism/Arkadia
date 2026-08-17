/**
 * HorizonNav — persistent horizontal navigation bar.
 *
 * Sits below the top bar and is accessible on EVERY page. Carries the
 * secondary surfaces the user wants reachable everywhere: SolSpire,
 * ReasoMate, Echofeild, Encyclopedia, Offerings, IMS, Grove, Larder,
 * Distribute, Projects, Knowledge OS, Dashboard, Pulse.
 *
 * The primary vertical nav (ArkadiaNavigation drawer) is reserved for the
 * six anchors: Home, Oracle, Living Gate, NovaNet, About, Settings.
 * Everything else lives here on the horizon.
 */
import React from 'react';
import { motion } from 'framer-motion';

export type HorizonView =
  | 'home' | 'gate' | 'commune' | 'about' | 'login'
  | 'novanet' | 'settings'
  // horizon-only surfaces
  | 'solspire' | 'reasomate' | 'echofeild-matrix' | 'encyclopedia'
  | 'offerings' | 'ims' | 'grove' | 'larder' | 'distribute'
  | 'knowledge-os' | 'dashboard' | 'pulse' | 'loops'
  | 'codex' | 'personal-echofeild' | 'spiral-codex';

interface Props {
  current: HorizonView;
  onNavigate: (v: HorizonView) => void;
}

interface HItem { view: HorizonView; label: string; sigil: string; color: string }

// The horizon bar — every secondary surface. Order matters for prominence.
const HORIZON: HItem[] = [
  { view: 'solspire',         label: 'SolSpire',    sigil: '◉', color: '#C9A84C' },
  { view: 'reasomate',        label: 'ReasoMate',  sigil: '✧', color: '#6A9FD8' },
  { view: 'echofeild-matrix', label: 'Echofeild',  sigil: '⬡', color: '#B08DE8' },
  { view: 'encyclopedia',     label: 'Encyclopedia',sigil: '◈', color: '#D4AF37' },
  { view: 'offerings',        label: 'Offerings',   sigil: '✦', color: '#00D4AA' },
  { view: 'knowledge-os',     label: 'Knowledge OS',sigil: '❖', color: '#00D4AA' },
  { view: 'ims',              label: 'IMS',         sigil: '∞', color: '#C84848' },
  { view: 'grove',            label: 'Grove',       sigil: '🌿', color: '#00D4AA' },
  { view: 'larder',           label: 'Larder',      sigil: '🌾', color: '#4CAF50' },
  { view: 'distribute',       label: 'Distribute',  sigil: '⟁', color: '#B08DE8' },
  { view: 'dashboard',        label: 'Dashboard',   sigil: '▦', color: '#C9A84C' },
  { view: 'pulse',            label: 'Pulse',       sigil: '◉', color: '#00D4AA' },
];

const HorizonNav: React.FC<Props> = ({ current, onNavigate }) => {
  return (
    <div
      style={{
        position: 'sticky', top: 52, zIndex: 35,
        display: 'flex', alignItems: 'center', gap: 4,
        overflowX: 'auto',
        padding: '6px 12px',
        background: 'rgba(10,11,20,0.96)',
        borderBottom: '1px solid rgba(201,168,76,0.12)',
        backdropFilter: 'blur(20px)',
        WebkitBackdropFilter: 'blur(20px)',
        scrollbarWidth: 'thin',
      }}
      className="horizon-nav"
    >
      {HORIZON.map(item => {
        const active = current === item.view;
        return (
          <motion.button
            key={item.view}
            onClick={() => onNavigate(item.view)}
            whileHover={{ y: -1 }}
            style={{
              flexShrink: 0,
              display: 'flex', alignItems: 'center', gap: 6,
              padding: '6px 12px',
              background: active ? `${item.color}14` : 'transparent',
              border: active ? `1px solid ${item.color}45` : '1px solid transparent',
              borderRadius: 8,
              cursor: 'pointer', transition: 'all 0.16s',
            }}
          >
            <span style={{ fontSize: 11, color: active ? item.color : 'rgba(232,232,232,0.4)' }}>{item.sigil}</span>
            <span style={{
              fontFamily: 'sans-serif', fontSize: 9.5,
              letterSpacing: '0.14em', textTransform: 'uppercase',
              color: active ? item.color : 'rgba(232,232,232,0.5)',
              fontWeight: active ? 600 : 400, whiteSpace: 'nowrap',
            }}>
              {item.label}
            </span>
          </motion.button>
        );
      })}
      <style>{`
        .horizon-nav::-webkit-scrollbar { height: 4px; }
        .horizon-nav::-webkit-scrollbar-thumb { background: rgba(201,168,76,0.2); border-radius: 2px; }
        .horizon-nav::-webkit-scrollbar-track { background: transparent; }
      `}</style>
    </div>
  );
};

export default HorizonNav;
