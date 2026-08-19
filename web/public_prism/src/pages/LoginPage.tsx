import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useAuth } from '../contexts/AuthContext';

type Mode = 'signin' | 'register' | 'magic';

interface LoginPageProps {
  onSuccess?: () => void;
  onBack?: () => void;
}

export default function LoginPage({ onSuccess, onBack }: LoginPageProps) {
  const { signIn, register, sendMagicLink, error: authError } = useAuth();
  const [mode, setMode] = useState<Mode>('signin');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirm, setConfirm] = useState('');
  const [loading, setLoading] = useState(false);
  const [localError, setLocalError] = useState('');
  const [magicSent, setMagicSent] = useState(false);

  const err = localError || authError || '';

  const mapAuthError = (msg: string): string => {
    const m = msg.toLowerCase();
    if (m.includes('email-already-in-use')) return 'That email already has an account. Sign in instead.';
    if (m.includes('weak-password')) return 'Password is too weak. Use at least 8 characters.';
    if (m.includes('invalid-email')) return 'Enter a valid email address.';
    if (m.includes('user-not-found') || m.includes('wrong-password') || m.includes('invalid-credential')) {
      return 'Email or password not recognised. Create an account if you are new.';
    }
    if (m.includes('too-many-requests')) return 'Too many attempts. Wait a moment and try again.';
    return msg || 'Authentication failed';
  };

  const handleSignIn = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!email || !password) return;
    setLocalError('');
    setLoading(true);
    try {
      await signIn(email.trim(), password);
      onSuccess?.();
    } catch (e: unknown) {
      setLocalError(mapAuthError((e as { message?: string }).message || ''));
    } finally {
      setLoading(false);
    }
  };

  const handleRegister = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!email || !password) return;
    if (password !== confirm) {
      setLocalError('Passwords do not match.');
      return;
    }
    if (password.length < 8) {
      setLocalError('Password must be at least 8 characters.');
      return;
    }
    setLocalError('');
    setLoading(true);
    try {
      await register(email.trim(), password);
      onSuccess?.();
    } catch (e: unknown) {
      setLocalError(mapAuthError((e as { message?: string }).message || ''));
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
      setLocalError(mapAuthError((e as { message?: string }).message || 'Failed to send link'));
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
  };

  const tabStyle = (active: boolean): React.CSSProperties => ({
    flex: 1,
    padding: '10px 8px',
    background: active ? 'rgba(0,212,170,0.1)' : 'transparent',
    border: active ? '1px solid rgba(0,212,170,0.35)' : '1px solid transparent',
    borderRadius: '8px',
    color: active ? '#00D4AA' : 'rgba(232,232,232,0.4)',
    fontFamily: 'sans-serif',
    fontSize: '10px',
    letterSpacing: '0.14em',
    textTransform: 'uppercase' as const,
    cursor: 'pointer',
  });

  return (
    <div style={{ minHeight: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center', padding: '24px 16px' }}>
      <div className="aurora-bg" style={{ position: 'fixed', inset: 0 }} />

      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        style={{ width: '100%', maxWidth: 400, position: 'relative', zIndex: 1 }}
      >
        <div style={{ textAlign: 'center', marginBottom: 22 }}>
          <p style={{ fontFamily: 'sans-serif', fontSize: 9, letterSpacing: '0.28em', textTransform: 'uppercase', color: 'rgba(201,168,76,0.65)', marginBottom: 8 }}>
            Private memory · your field
          </p>
          <h1 style={{ fontFamily: '"Cinzel", serif', fontSize: 28, letterSpacing: '0.16em', color: '#C9A84C', margin: 0 }}>
            ARKADIA
          </h1>
          <p style={{ fontFamily: 'serif', fontSize: 13, color: 'rgba(212,223,232,0.5)', marginTop: 10, lineHeight: 1.6 }}>
            Create an account to keep notes and Oracle memory private to you.
            Guest mode still works without signing in.
          </p>
        </div>

        <div style={{ display: 'flex', gap: 6, marginBottom: 16 }}>
          <button type="button" style={tabStyle(mode === 'signin')} onClick={() => { setMode('signin'); setLocalError(''); }} data-testid="tab-signin">
            Sign in
          </button>
          <button type="button" style={tabStyle(mode === 'register')} onClick={() => { setMode('register'); setLocalError(''); }} data-testid="tab-register">
            Create account
          </button>
          <button type="button" style={tabStyle(mode === 'magic')} onClick={() => { setMode('magic'); setLocalError(''); setMagicSent(false); }} data-testid="tab-magic">
            Magic link
          </button>
        </div>

        <motion.div
          style={{
            padding: 22,
            background: 'rgba(14,17,32,0.85)',
            border: '1px solid rgba(0,212,170,0.18)',
            borderRadius: 12,
            backdropFilter: 'blur(16px)',
          }}
        >
          <AnimatePresence mode="wait">
            {mode === 'signin' && (
              <motion.form key="signin" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} onSubmit={handleSignIn}>
                <label style={{ display: 'block', fontSize: 10, letterSpacing: '0.12em', textTransform: 'uppercase', color: 'rgba(232,232,232,0.4)', marginBottom: 6 }}>Email</label>
                <input type="email" value={email} onChange={e => setEmail(e.target.value)} required autoComplete="email" data-testid="input-email-signin" style={{ ...inputStyle, marginBottom: 14 }} />
                <label style={{ display: 'block', fontSize: 10, letterSpacing: '0.12em', textTransform: 'uppercase', color: 'rgba(232,232,232,0.4)', marginBottom: 6 }}>Password</label>
                <input type="password" value={password} onChange={e => setPassword(e.target.value)} required autoComplete="current-password" data-testid="input-password-signin" style={{ ...inputStyle, marginBottom: 16 }} />
                {err && <p style={{ fontSize: 11, color: '#E88C6A', marginBottom: 12 }}>{err}</p>}
                <button type="submit" disabled={loading || !email || !password} data-testid="button-signin" style={{
                  width: '100%', padding: 13, background: 'linear-gradient(135deg, rgba(0,212,170,0.14), rgba(0,212,170,0.05))',
                  border: '1px solid rgba(0,212,170,0.4)', borderRadius: 9, color: '#00D4AA',
                  fontFamily: 'sans-serif', fontSize: 10, letterSpacing: '0.2em', textTransform: 'uppercase',
                  cursor: loading ? 'wait' : 'pointer',
                }}>
                  {loading ? 'Signing in…' : 'Sign in'}
                </button>
              </motion.form>
            )}

            {mode === 'register' && (
              <motion.form key="register" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} onSubmit={handleRegister}>
                <label style={{ display: 'block', fontSize: 10, letterSpacing: '0.12em', textTransform: 'uppercase', color: 'rgba(232,232,232,0.4)', marginBottom: 6 }}>Email</label>
                <input type="email" value={email} onChange={e => setEmail(e.target.value)} required autoComplete="email" data-testid="input-email-register" style={{ ...inputStyle, marginBottom: 14 }} />
                <label style={{ display: 'block', fontSize: 10, letterSpacing: '0.12em', textTransform: 'uppercase', color: 'rgba(232,232,232,0.4)', marginBottom: 6 }}>Password (min 8)</label>
                <input type="password" value={password} onChange={e => setPassword(e.target.value)} required minLength={8} autoComplete="new-password" data-testid="input-password-register" style={{ ...inputStyle, marginBottom: 14 }} />
                <label style={{ display: 'block', fontSize: 10, letterSpacing: '0.12em', textTransform: 'uppercase', color: 'rgba(232,232,232,0.4)', marginBottom: 6 }}>Confirm password</label>
                <input type="password" value={confirm} onChange={e => setConfirm(e.target.value)} required minLength={8} autoComplete="new-password" data-testid="input-confirm-register" style={{ ...inputStyle, marginBottom: 16 }} />
                <p style={{ fontSize: 11, color: 'rgba(232,232,232,0.35)', lineHeight: 1.5, marginBottom: 14 }}>
                  Your notes and Oracle context stay private to this account. No IMS session required to start.
                </p>
                {err && <p style={{ fontSize: 11, color: '#E88C6A', marginBottom: 12 }}>{err}</p>}
                <button type="submit" disabled={loading || !email || !password} data-testid="button-register" style={{
                  width: '100%', padding: 13, background: 'linear-gradient(135deg, rgba(201,168,76,0.14), rgba(201,168,76,0.05))',
                  border: '1px solid rgba(201,168,76,0.4)', borderRadius: 9, color: '#C9A84C',
                  fontFamily: 'sans-serif', fontSize: 10, letterSpacing: '0.2em', textTransform: 'uppercase',
                  cursor: loading ? 'wait' : 'pointer',
                }}>
                  {loading ? 'Creating…' : 'Create account'}
                </button>
              </motion.form>
            )}

            {mode === 'magic' && (
              <motion.form key="magic" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} onSubmit={handleMagicLink}>
                {magicSent ? (
                  <p style={{ fontSize: 13, color: 'rgba(0,212,170,0.75)', lineHeight: 1.6 }}>
                    Link sent to <strong>{email}</strong>. Open it on this device to finish signing in.
                  </p>
                ) : (
                  <>
                    <label style={{ display: 'block', fontSize: 10, letterSpacing: '0.12em', textTransform: 'uppercase', color: 'rgba(232,232,232,0.4)', marginBottom: 6 }}>Email</label>
                    <input type="email" value={email} onChange={e => setEmail(e.target.value)} required autoComplete="email" data-testid="input-email-magic" style={{ ...inputStyle, marginBottom: 14 }} />
                    <p style={{ fontSize: 11, color: 'rgba(232,232,232,0.35)', marginBottom: 14 }}>One-time link — no password required.</p>
                    {err && <p style={{ fontSize: 11, color: '#E88C6A', marginBottom: 12 }}>{err}</p>}
                    <button type="submit" disabled={loading || !email} data-testid="button-send-magic" style={{
                      width: '100%', padding: 13, background: 'linear-gradient(135deg, rgba(201,168,76,0.12), rgba(201,168,76,0.06))',
                      border: '1px solid rgba(201,168,76,0.35)', borderRadius: 9, color: '#C9A84C',
                      fontFamily: 'sans-serif', fontSize: 10, letterSpacing: '0.2em', textTransform: 'uppercase',
                      cursor: loading ? 'wait' : 'pointer',
                    }}>
                      {loading ? 'Transmitting…' : 'Send magic link'}
                    </button>
                  </>
                )}
              </motion.form>
            )}
          </AnimatePresence>
        </motion.div>

        <div style={{ textAlign: 'center', marginTop: 18 }}>
          <p style={{ fontSize: 10, color: 'rgba(232,232,232,0.25)', lineHeight: 1.6, marginBottom: 12 }}>
            IMS sessions deepen identity architecture for initiated nodes.
            Private Knowledge OS works for every signed-in account.
          </p>
          {onBack && (
            <button
              type="button"
              onClick={onBack}
              style={{ background: 'none', border: 'none', color: 'rgba(0,212,170,0.4)', fontFamily: 'sans-serif', fontSize: 10, letterSpacing: '0.16em', textTransform: 'uppercase', cursor: 'pointer' }}
            >
              ← Return to the public field
            </button>
          )}
        </div>
      </motion.div>
    </div>
  );
}
