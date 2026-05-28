import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useAuth } from '../contexts/AuthContext';

type Mode = 'password' | 'magic';

interface LoginPageProps {
  onSuccess?: () => void;
  onBack?: () => void;
}

export default function LoginPage({ onSuccess, onBack }: LoginPageProps) {
  const { signIn, sendMagicLink, error: authError } = useAuth();
  const [mode, setMode] = useState<Mode>('password');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [localError, setLocalError] = useState('');
  const [magicSent, setMagicSent] = useState(false);

  const err = localError || authError || '';

  const handlePasswordLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!email || !password) return;
    setLocalError('');
    setLoading(true);
    try {
      await signIn(email.trim(), password);
      onSuccess?.();
    } catch (e: unknown) {
      const msg = (e as { message?: string }).message || 'Login failed';
      if (msg.includes('user-not-found') || msg.includes('wrong-password') || msg.includes('invalid-credential')) {
        setLocalError('Unrecognised node. Only IMS-authenticated nodes may enter.');
      } else {
        setLocalError(msg);
      }
    } finally {
      setLoading(false);
    }
  };

  const handleMagicLink = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!email) return;
    setLocalError('');
    setLoading(true);
    try {
      await sendMagicLink(email.trim());
      setMagicSent(true);
    } catch (e: unknown) {
      const msg = (e as { message?: string }).message || 'Failed to send link';
      setLocalError(msg);
    } finally {
      setLoading(false);
    }
  };

  const inputStyle: React.CSSProperties = {
    width: '100%',
    padding: '12px 14px',
    background: 'rgba(0,212,170,0.03)',
    border: '1px solid rgba(0,212,170,0.18)',
    borderRadius: '9px',
    color: 'rgba(232,232,232,0.85)',
    fontFamily: 'sans-serif',
    fontSize: '13px',
    outline: 'none',
    boxSizing: 'border-box',
    transition: 'border-color 0.2s',
  };

  return (
    <div style={{ minHeight: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center', padding: '24px 16px' }}>
      <div className="aurora-bg" style={{ position: 'fixed', inset: 0 }} />

      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.6 }}
        style={{ position: 'relative', zIndex: 10, width: '100%', maxWidth: '400px' }}
      >
        {/* Header */}
        <div style={{ textAlign: 'center', marginBottom: '32px' }}>
          <motion.p
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.1 }}
            style={{ fontFamily: 'sans-serif', fontSize: '9px', letterSpacing: '0.35em', textTransform: 'uppercase', color: 'rgba(201,168,76,0.5)', marginBottom: '10px' }}
          >
            Arkadia — Authenticated Chamber
          </motion.p>
          <motion.h1
            initial={{ opacity: 0, y: 8 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.2, duration: 0.7 }}
            style={{ fontFamily: 'serif', fontSize: '36px', letterSpacing: '0.12em', color: '#00D4AA', textShadow: '0 0 30px rgba(0,212,170,0.25)', margin: '0 0 8px' }}
          >
            ENTER
          </motion.h1>
          <motion.p
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.35 }}
            style={{ fontFamily: 'serif', fontSize: '12px', color: 'rgba(232,232,232,0.3)', lineHeight: '1.7' }}
          >
            The chambers are open to those who have<br />sat in the fire and received their map.
          </motion.p>
        </div>

        {/* Card */}
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.4 }}
          style={{ background: 'rgba(10,10,15,0.88)', border: '1px solid rgba(0,212,170,0.12)', borderRadius: '14px', padding: '28px 24px', backdropFilter: 'blur(20px)' }}
        >
          {/* Mode toggle */}
          <div style={{ display: 'flex', gap: '6px', marginBottom: '24px', background: 'rgba(255,255,255,0.025)', borderRadius: '9px', padding: '4px' }}>
            {(['password', 'magic'] as Mode[]).map(m => (
              <button
                key={m}
                onClick={() => { setMode(m); setLocalError(''); setMagicSent(false); }}
                style={{
                  flex: 1, padding: '8px', borderRadius: '6px', border: 'none', cursor: 'pointer',
                  fontFamily: 'sans-serif', fontSize: '10px', letterSpacing: '0.18em', textTransform: 'uppercase',
                  background: mode === m ? 'rgba(0,212,170,0.1)' : 'transparent',
                  color: mode === m ? '#00D4AA' : 'rgba(232,232,232,0.3)',
                  transition: 'all 0.2s',
                }}
              >
                {m === 'password' ? 'Password' : 'Magic Link'}
              </button>
            ))}
          </div>

          <AnimatePresence mode="wait">
            {magicSent ? (
              <motion.div key="sent" initial={{ opacity: 0 }} animate={{ opacity: 1 }} style={{ textAlign: 'center', padding: '12px 0' }}>
                <p style={{ fontFamily: 'sans-serif', fontSize: '22px', marginBottom: '12px' }}>✦</p>
                <p style={{ fontFamily: 'serif', fontSize: '14px', color: '#00D4AA', marginBottom: '8px' }}>Link transmitted</p>
                <p style={{ fontFamily: 'sans-serif', fontSize: '12px', color: 'rgba(232,232,232,0.4)', lineHeight: '1.7' }}>
                  Check your inbox for {email}.<br />The link will open your chamber.
                </p>
              </motion.div>
            ) : mode === 'password' ? (
              <motion.form key="password" initial={{ opacity: 0, x: -8 }} animate={{ opacity: 1, x: 0 }} exit={{ opacity: 0 }} onSubmit={handlePasswordLogin}>
                <div style={{ marginBottom: '14px' }}>
                  <label style={{ fontFamily: 'sans-serif', fontSize: '9px', letterSpacing: '0.22em', textTransform: 'uppercase', color: 'rgba(232,232,232,0.35)', display: 'block', marginBottom: '6px' }}>
                    Email
                  </label>
                  <input
                    type="email"
                    value={email}
                    onChange={e => setEmail(e.target.value)}
                    placeholder="node@arkadia.field"
                    style={inputStyle}
                    autoComplete="email"
                    data-testid="input-email"
                  />
                </div>
                <div style={{ marginBottom: '22px' }}>
                  <label style={{ fontFamily: 'sans-serif', fontSize: '9px', letterSpacing: '0.22em', textTransform: 'uppercase', color: 'rgba(232,232,232,0.35)', display: 'block', marginBottom: '6px' }}>
                    Password
                  </label>
                  <input
                    type="password"
                    value={password}
                    onChange={e => setPassword(e.target.value)}
                    placeholder="••••••••"
                    style={inputStyle}
                    autoComplete="current-password"
                    data-testid="input-password"
                  />
                </div>

                {err && (
                  <motion.p initial={{ opacity: 0 }} animate={{ opacity: 1 }}
                    style={{ fontFamily: 'sans-serif', fontSize: '11px', color: '#E88C6A', marginBottom: '16px', lineHeight: '1.5' }}>
                    {err}
                  </motion.p>
                )}

                <button
                  type="submit"
                  disabled={loading || !email || !password}
                  data-testid="button-login"
                  style={{
                    width: '100%', padding: '13px', background: loading ? 'rgba(0,212,170,0.06)' : 'linear-gradient(135deg, rgba(0,212,170,0.15), rgba(0,212,170,0.08))',
                    border: '1px solid rgba(0,212,170,0.35)', borderRadius: '9px', color: loading ? 'rgba(0,212,170,0.4)' : '#00D4AA',
                    fontFamily: 'sans-serif', fontSize: '10px', letterSpacing: '0.22em', textTransform: 'uppercase', cursor: loading ? 'wait' : 'pointer', transition: 'all 0.2s',
                  }}
                >
                  {loading ? 'Verifying node…' : '⟐ Enter the Field'}
                </button>
              </motion.form>
            ) : (
              <motion.form key="magic" initial={{ opacity: 0, x: 8 }} animate={{ opacity: 1, x: 0 }} exit={{ opacity: 0 }} onSubmit={handleMagicLink}>
                <div style={{ marginBottom: '22px' }}>
                  <label style={{ fontFamily: 'sans-serif', fontSize: '9px', letterSpacing: '0.22em', textTransform: 'uppercase', color: 'rgba(232,232,232,0.35)', display: 'block', marginBottom: '6px' }}>
                    Email
                  </label>
                  <input
                    type="email"
                    value={email}
                    onChange={e => setEmail(e.target.value)}
                    placeholder="node@arkadia.field"
                    style={inputStyle}
                    autoComplete="email"
                    data-testid="input-email-magic"
                  />
                </div>
                <p style={{ fontFamily: 'sans-serif', fontSize: '11px', color: 'rgba(232,232,232,0.3)', lineHeight: '1.6', marginBottom: '18px' }}>
                  A one-time link will be sent to your email. No password required.
                </p>

                {err && (
                  <motion.p initial={{ opacity: 0 }} animate={{ opacity: 1 }}
                    style={{ fontFamily: 'sans-serif', fontSize: '11px', color: '#E88C6A', marginBottom: '16px' }}>
                    {err}
                  </motion.p>
                )}

                <button
                  type="submit"
                  disabled={loading || !email}
                  data-testid="button-send-magic"
                  style={{
                    width: '100%', padding: '13px', background: 'linear-gradient(135deg, rgba(201,168,76,0.12), rgba(201,168,76,0.06))',
                    border: '1px solid rgba(201,168,76,0.35)', borderRadius: '9px', color: '#C9A84C',
                    fontFamily: 'sans-serif', fontSize: '10px', letterSpacing: '0.22em', textTransform: 'uppercase', cursor: loading ? 'wait' : 'pointer', transition: 'all 0.2s',
                  }}
                >
                  {loading ? 'Transmitting…' : '✦ Transmit Magic Link'}
                </button>
              </motion.form>
            )}
          </AnimatePresence>
        </motion.div>

        {/* Footer */}
        <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 0.6 }} style={{ textAlign: 'center', marginTop: '20px' }}>
          <p style={{ fontFamily: 'sans-serif', fontSize: '10px', color: 'rgba(232,232,232,0.2)', lineHeight: '1.7', marginBottom: '12px' }}>
            Access is earned through the IMS — the Identity Mapping Session.<br />
            No subscriptions. No anonymous dashboards. Every node is initiated.
          </p>
          {onBack && (
            <button
              onClick={onBack}
              style={{ background: 'none', border: 'none', color: 'rgba(0,212,170,0.35)', fontFamily: 'sans-serif', fontSize: '10px', letterSpacing: '0.18em', textTransform: 'uppercase', cursor: 'pointer' }}
            >
              ← Return to the Public Field
            </button>
          )}
        </motion.div>
      </motion.div>
    </div>
  );
}
