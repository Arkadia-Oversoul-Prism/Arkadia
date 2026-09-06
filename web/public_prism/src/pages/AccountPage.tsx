import { useState } from 'react';
import { deleteUser } from 'firebase/auth';
import { useAuth } from '../contexts/AuthContext';
import { auth } from '../lib/firebase';
import { API_BASE } from '../lib/apiConfig';

export default function AccountPage() {
  const { user, profile, refreshProfile, signOut } = useAuth();
  const [displayName, setDisplayName] = useState(profile?.display_name || user?.displayName || '');
  const [username, setUsername] = useState(profile?.username || '');
  const [bio, setBio] = useState(profile?.bio || '');
  const [avatar, setAvatar] = useState(profile?.avatar_url || '');
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState('');
  const [confirmDelete, setConfirmDelete] = useState(false);

  const save = async () => {
    if (!user?.idToken) return;
    setSaving(true); setMessage('');
    try {
      const res = await fetch(`${API_BASE.replace(/\/$/,'')}/api/me`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${user.idToken}` },
        body: JSON.stringify({ display_name: displayName.trim(), username: username.trim().replace(/^@/, ''), bio: bio.trim(), avatar_url: avatar.trim() }),
      });
      if (!res.ok) throw new Error((await res.json().catch(() => ({})))?.detail || 'Could not save profile');
      await refreshProfile();
      setMessage('Profile saved.');
    } catch (e: any) { setMessage(e?.message || 'Could not save profile.'); }
    finally { setSaving(false); }
  };

  const removeAccount = async () => {
    if (!auth?.currentUser) return;
    setSaving(true); setMessage('');
    try {
      // Delete the server-owned profile first while the Firebase token is valid.
      await fetch(`${API_BASE.replace(/\/$/,'')}/api/me`, { method: 'DELETE', headers: { Authorization: `Bearer ${user?.idToken || ''}` } }).catch(() => undefined);
      await deleteUser(auth.currentUser);
      await signOut();
    } catch (e: any) {
      setMessage(e?.code === 'auth/requires-recent-login' ? 'For safety, sign in again before deleting your account.' : (e?.message || 'Account deletion failed.'));
      setSaving(false);
    }
  };

  return <main style={{ minHeight:'calc(100vh - 57px)', background:'#0A0A0F', color:'#E8E8E8', padding:'36px 18px 70px' }}>
    <div style={{ maxWidth:720, margin:'0 auto' }}>
      <p style={{ fontSize:9, letterSpacing:'.28em', color:'rgba(0,212,170,.65)', textTransform:'uppercase', margin:0 }}>YOUR NODE</p>
      <h1 style={{ fontFamily:'serif', fontWeight:400, fontSize:38, color:'#C9A84C', margin:'8px 0 8px' }}>Profile & account</h1>
      <p style={{ color:'rgba(232,232,232,.52)', lineHeight:1.7, fontSize:14, marginBottom:28 }}>This is the public face people meet in NovaNet and ReasoMate. Your deeper identity stays in your private field.</p>
      <section style={{ display:'grid', gap:14, padding:22, border:'1px solid rgba(0,212,170,.14)', background:'rgba(14,17,32,.72)', borderRadius:14 }}>
        <label>Display name<input value={displayName} onChange={e=>setDisplayName(e.target.value)} placeholder="Your name" /></label>
        <label>Username<input value={username} onChange={e=>setUsername(e.target.value)} placeholder="your-handle" /></label>
        <label>Bio<textarea value={bio} onChange={e=>setBio(e.target.value)} placeholder="A few words about you" rows={4} /></label>
        <label>Profile picture<input value={avatar} onChange={e=>setAvatar(e.target.value)} placeholder="Image URL" /></label>
        {avatar && <img src={avatar} alt="Profile preview" style={{ width:76,height:76,borderRadius:'50%',objectFit:'cover',border:'1px solid rgba(201,168,76,.35)' }} />}
        <button onClick={save} disabled={saving} style={{ padding:'13px 18px', borderRadius:9, border:'1px solid rgba(0,212,170,.45)', background:'rgba(0,212,170,.1)', color:'#00D4AA', cursor:'pointer' }}>{saving ? 'Saving…' : 'Save profile'}</button>
        {message && <p style={{ fontSize:12, color:'rgba(232,232,232,.6)', margin:0 }}>{message}</p>}
      </section>
      <section style={{ marginTop:18, padding:22, border:'1px solid rgba(220,90,90,.2)', background:'rgba(40,12,18,.25)', borderRadius:14 }}>
        <p style={{ fontSize:9, letterSpacing:'.22em', color:'rgba(220,120,120,.7)', textTransform:'uppercase' }}>ACCOUNT</p>
        <h2 style={{ fontFamily:'serif', fontWeight:400, fontSize:23, margin:'7px 0' }}>Leave Arkadia</h2>
        <p style={{ color:'rgba(232,232,232,.48)', lineHeight:1.6, fontSize:13 }}>Delete your Firebase account and request removal of your server profile. This cannot be undone.</p>
        {!confirmDelete ? <button onClick={()=>setConfirmDelete(true)} style={{ padding:'10px 14px', borderRadius:8, border:'1px solid rgba(220,90,90,.35)', background:'transparent', color:'rgba(240,150,150,.8)', cursor:'pointer' }}>Delete account</button> : <div style={{ display:'flex', gap:8, flexWrap:'wrap' }}><button onClick={removeAccount} disabled={saving} style={{ padding:'10px 14px', borderRadius:8, border:'1px solid rgba(220,90,90,.55)', background:'rgba(220,90,90,.12)', color:'#f0aaaa', cursor:'pointer' }}>{saving ? 'Deleting…' : 'Yes, delete my account'}</button><button onClick={()=>setConfirmDelete(false)} style={{ padding:'10px 14px', borderRadius:8, border:'1px solid rgba(255,255,255,.1)', background:'transparent', color:'rgba(232,232,232,.55)', cursor:'pointer' }}>Keep account</button></div>}
      </section>
    </div>
    <style>{`label{font:11px sans-serif;letter-spacing:.08em;color:rgba(232,232,232,.55);display:grid;gap:7px}input,textarea{font:14px sans-serif;letter-spacing:normal;color:#E8E8E8;background:rgba(0,0,0,.2);border:1px solid rgba(255,255,255,.1);border-radius:8px;padding:12px;outline:none}input:focus,textarea:focus{border-color:rgba(0,212,170,.45)}`}</style>
  </main>;
}
