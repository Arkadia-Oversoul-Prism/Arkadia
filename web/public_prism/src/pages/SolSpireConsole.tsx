/**
 * SolSpire Console
 *
 * Thin route adapter for the canonical authenticated SolSpire experience.
 * The experience owns the workspace chrome and object grammar; this file keeps
 * the existing App/router contract and authenticated identity boundary stable.
 */
import React, { useLayoutEffect } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { setApiAuthToken } from '../lib/apiClient';
import SolSpireExperience, { SolSpireLens } from '../components/solspire/SolSpireExperience';

type LegacySection = SolSpireLens | 'field' | 'codex' | 'loops' | 'projects' | 'encyclopedia' | 'goals' | 'releases' | 'jobs' | 'traces' | 'tools' | 'system';
type AppView = 'home'|'gate'|'commune'|'reset'|'about'|'login'|'codex'|'dashboard'|'nexus'|'encyclopedia'|'spiral-codex'|'loops'|'grove'|'larder'|'novanet'|'ims'|'distribute'|'offerings'|'aic'|'pulse'|'settings'|'account'|'sci'|'solspire'|'knowledge-os'|'reasomate'|'personal-echofeild'|'echofeild-matrix';
const LEGACY_MAP: Record<string, SolSpireLens> = {field:'overview',codex:'knowledge',loops:'tasks',projects:'projects',encyclopedia:'knowledge',goals:'overview',releases:'overview',jobs:'observatory',traces:'observatory',tools:'observatory',system:'settings'};
function resolveIdentity(user: ReturnType<typeof useAuth>['user']) { return user?.displayName?.trim() || (user?.email ? user.email.split('@')[0] : '') || 'Authenticated node'; }
export default function SolSpireConsole({ onNavigate, initialSection = 'overview' }: { onNavigate?: (v: AppView) => void; initialSection?: LegacySection } = {}) {
  const { isAuthenticated, user } = useAuth();
  useLayoutEffect(() => { setApiAuthToken(user?.idToken ?? null); }, [user?.idToken]);
  if (!isAuthenticated) return <div className="solspire-auth-threshold"><div className="solspire-auth-card"><div className="solspire-brand-name">SOLSPIRE</div><div className="solspire-kicker">PRIVATE WORKSPACE</div><p>Sign in to enter the authenticated contextual workspace.</p><button type="button" onClick={() => onNavigate?.('gate')}>Enter workspace</button></div></div>;
  return <SolSpireExperience identity={resolveIdentity(user)} initialSection={(LEGACY_MAP[initialSection] || initialSection) as SolSpireLens} onNavigate={onNavigate} />;
}
