import React, { useEffect, useState } from 'react';
import { motion } from 'framer-motion';
import { useAuth } from '../contexts/AuthContext';
import { API_BASE } from '../lib/apiConfig';
import LoginPage from './LoginPage';
import LivingGate, { AisCapabilityPortfolio } from './LivingGate';

interface NodeEntryProps {
  onEnterNovaNet: () => void;
  onBack?: () => void;
  onAICComplete?: (portfolio: AisCapabilityPortfolio) => void;
}

type Stage = 'auth' | 'diagnostic' | 'formed';

export default function NodeEntry({ onEnterNovaNet, onBack, onAICComplete }: NodeEntryProps) {
  const { user, isAuthenticated, profile, loading } = useAuth();
  const [stage, setStage] = useState<Stage>(isAuthenticated ? 'diagnostic' : 'auth');
  const [checkingIdentity, setCheckingIdentity] = useState(false);

  useEffect(() => {
    if (loading) return;
    if (!isAuthenticated || !user?.idToken) {
      setStage('auth');
      return;
    }

    let cancelled = false;
    const resolveNode = async () => {
      setCheckingIdentity(true);
      try {
        const response = await fetch(`${API_BASE.replace(/\/$/, '')}/api/me/ais-profile`, {
          headers: { Authorization: `Bearer ${user.idToken}` },
        });
        if (!response.ok) {
          if (!cancelled) setStage('diagnostic');
          return;
        }
        const data = await response.json() as {
          profile?: { kind?: string; profile?: unknown } | null;
        };
        if (!cancelled) setStage(data.profile?.kind === 'portfolio' ? 'formed' : 'diagnostic');
      } catch {
        if (!cancelled) setStage('diagnostic');
      } finally {
        if (!cancelled) setCheckingIdentity(false);
      }
    };

    void resolveNode();
    return () => { cancelled = true; };
  }, [loading, isAuthenticated, user?.idToken]);

  if (stage === 'auth') {
    return (
      <div className="relative w-full min-h-screen" style={{ background: '#0A0A0F' }}>
        <LoginPage onSuccess={() => setStage('diagnostic')} onBack={onBack} />
      </div>
    );
  }

  if (stage === 'formed') {
    const displayName = profile?.display_name || user?.displayName || 'Node';
    return (
      <div className="relative w-full min-h-screen flex items-center justify-center px-5 py-12" style={{ background: '#0A0A0F' }}>
        <div className="absolute inset-0 pointer-events-none" style={{ background: 'radial-gradient(circle at 50% 42%, rgba(0,212,170,.09), transparent 58%)' }} />
        <motion.div initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }} className="relative z-10 w-full" style={{ maxWidth: 620, textAlign: 'center' }}>
          <p style={{ fontFamily: 'sans-serif', fontSize: 9, letterSpacing: '.34em', textTransform: 'uppercase', color: 'rgba(0,212,170,.62)', margin: '0 0 12px' }}>
            Identity Resolved · A.I.S Complete
          </p>
          <h1 style={{ fontFamily: 'serif', fontSize: 42, fontWeight: 400, color: '#C9A84C', margin: '0 0 12px' }}>
            NODE FORMED
          </h1>
          <p style={{ fontFamily: 'sans-serif', fontSize: 13, lineHeight: 1.7, color: 'rgba(232,232,232,.5)', maxWidth: 470, margin: '0 auto 28px' }}>
            Welcome back, {displayName}. Your identity and A.I.S capability map are already resolved. Arkadia is ready to receive you.
          </p>
          <button type="button" onClick={onEnterNovaNet} data-testid="enter-novanet" style={{ width: '100%', maxWidth: 460, padding: '16px 20px', background: 'linear-gradient(135deg, rgba(0,212,170,.16), rgba(106,159,216,.08))', border: '1px solid rgba(0,212,170,.5)', borderRadius: 11, color: '#00D4AA', fontFamily: 'sans-serif', fontSize: 10, letterSpacing: '.24em', textTransform: 'uppercase', cursor: 'pointer' }}>
            Enter NovaNet →
          </button>
        </motion.div>
      </div>
    );
  }

  if (checkingIdentity) {
    return (
      <div className="relative w-full min-h-screen flex items-center justify-center" style={{ background: '#0A0A0F' }}>
        <p style={{ fontFamily: 'sans-serif', fontSize: 9, letterSpacing: '.28em', textTransform: 'uppercase', color: 'rgba(0,212,170,.5)' }}>Resolving identity…</p>
      </div>
    );
  }

  return (
    <LivingGate
      onAICComplete={(portfolio) => {
        onAICComplete?.(portfolio);
        setStage('formed');
      }}
      onEnterSpiralGrove={onEnterNovaNet}
    />
  );
}
