import React from 'react';
import { motion } from 'framer-motion';

const ShereSanctuary: React.FC = () => {
  return (
    <div className="w-full" style={{ maxWidth: '520px', margin: '0 auto', paddingTop: '12px' }}>
      {/* Header */}
      <motion.div
        initial={{ opacity: 0, y: 12 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.8 }}
        style={{ marginBottom: '36px' }}
      >
        <p
          style={{
            fontFamily: 'sans-serif',
            fontSize: '9px',
            letterSpacing: '0.35em',
            textTransform: 'uppercase',
            color: 'rgba(0,212,170,0.4)',
            margin: '0 0 10px',
          }}
        >
          Earth Node — Jos, Nigeria
        </p>
        <h1
          style={{
            fontFamily: 'serif',
            fontSize: '28px',
            letterSpacing: '0.04em',
            color: '#E8E8E8',
            margin: '0 0 10px',
          }}
        >
          Shere Sanctuary
        </h1>
        <p
          style={{
            fontFamily: 'sans-serif',
            fontSize: '14px',
            color: 'rgba(232,232,232,0.45)',
            margin: 0,
            lineHeight: '1.6',
          }}
        >
          1,500 nodes. The earth remembers.
        </p>
      </motion.div>

      {/* Animated ring */}
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 0.3 }}
        style={{ display: 'flex', justifyContent: 'center', marginBottom: '36px' }}
      >
        <div style={{ position: 'relative', width: '160px', height: '160px' }}>
          {/* Outer ring */}
          <motion.div
            animate={{ rotate: 360 }}
            transition={{ duration: 40, repeat: Infinity, ease: 'linear' }}
            style={{
              position: 'absolute',
              inset: 0,
              borderRadius: '50%',
              border: '1px solid rgba(0,212,170,0.15)',
            }}
          >
            {[0, 90, 180, 270].map((deg, i) => (
              <motion.div
                key={i}
                animate={{ opacity: [0.2, 0.8, 0.2] }}
                transition={{ duration: 3, repeat: Infinity, delay: i * 0.75 }}
                style={{
                  position: 'absolute',
                  width: '6px',
                  height: '6px',
                  borderRadius: '50%',
                  backgroundColor: '#00D4AA',
                  top: '50%',
                  left: '50%',
                  transform: `rotate(${deg}deg) translateY(-77px) translate(-50%, -50%)`,
                  boxShadow: '0 0 8px rgba(0,212,170,0.8)',
                }}
              />
            ))}
          </motion.div>

          {/* Inner ring */}
          <motion.div
            animate={{ rotate: -360 }}
            transition={{ duration: 25, repeat: Infinity, ease: 'linear' }}
            style={{
              position: 'absolute',
              inset: '24px',
              borderRadius: '50%',
              border: '1px solid rgba(201,168,76,0.12)',
            }}
          >
            {[0, 120, 240].map((deg, i) => (
              <motion.div
                key={i}
                animate={{ opacity: [0.2, 0.6, 0.2] }}
                transition={{ duration: 4, repeat: Infinity, delay: i * 1.3 }}
                style={{
                  position: 'absolute',
                  width: '4px',
                  height: '4px',
                  borderRadius: '50%',
                  backgroundColor: '#C9A84C',
                  top: '50%',
                  left: '50%',
                  transform: `rotate(${deg}deg) translateY(-53px) translate(-50%, -50%)`,
                }}
              />
            ))}
          </motion.div>

          {/* Center glyph */}
          <div
            style={{
              position: 'absolute',
              inset: 0,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
            }}
          >
            <motion.span
              animate={{ opacity: [0.4, 0.9, 0.4] }}
              transition={{ duration: 5, repeat: Infinity }}
              style={{ fontSize: '28px', lineHeight: 1 }}
            >
              ☥
            </motion.span>
          </div>
        </div>
      </motion.div>

      {/* Status card */}
      <motion.div
        initial={{ opacity: 0, y: 16 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.5 }}
        style={{
          padding: '24px',
          background: 'rgba(255,255,255,0.02)',
          border: '1px solid rgba(0,212,170,0.12)',
          borderRadius: '14px',
          backdropFilter: 'blur(14px)',
          WebkitBackdropFilter: 'blur(14px)',
          marginBottom: '16px',
        }}
      >
        <p
          style={{
            fontFamily: 'serif',
            fontSize: '15px',
            lineHeight: '1.85',
            color: 'rgba(232,232,232,0.72)',
            margin: 0,
          }}
        >
          This sanctuary is being mapped.<br />
          Two nodes are anchored. 1,498 are listening.
        </p>
      </motion.div>

      {/* Node stats */}
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 0.7 }}
        style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: '10px' }}
      >
        {[
          { value: '1,500', label: 'Total Nodes' },
          { value: '2', label: 'Anchored' },
          { value: '1,498', label: 'Listening' },
        ].map((stat, i) => (
          <div
            key={i}
            style={{
              padding: '14px 10px',
              background: 'rgba(255,255,255,0.02)',
              border: '1px solid rgba(255,255,255,0.06)',
              borderRadius: '10px',
              textAlign: 'center',
            }}
          >
            <p style={{ fontFamily: 'serif', fontSize: '18px', color: '#C9A84C', margin: '0 0 4px' }}>{stat.value}</p>
            <p style={{ fontFamily: 'sans-serif', fontSize: '8px', letterSpacing: '0.2em', textTransform: 'uppercase', color: 'rgba(232,232,232,0.3)', margin: 0 }}>
              {stat.label}
            </p>
          </div>
        ))}
      </motion.div>
    </div>
  );
};

export default ShereSanctuary;
