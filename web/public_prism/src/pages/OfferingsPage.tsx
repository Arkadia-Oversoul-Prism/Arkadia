import React, { useState, useEffect, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';

const API_BASE = (import.meta.env.VITE_API_URL ?? '').replace(/\/$/, '');
const PAYSTACK_KEY = import.meta.env.VITE_PAYSTACK_PUBLIC_KEY ?? '';

// ─── Types ────────────────────────────────────────────────────────────────────

interface Product {
  id: string;
  name: string;
  tagline: string;
  description: string;
  price_usd: number;
  price_ngn: number;
  price_display: string;
  delivery: string;
  duration: string;
  prerequisite: string | null;
  sigil: string;
  color: string;
  available: boolean;
}

interface Order {
  order_id: string;
  product_id: string;
  product_name: string;
  status: 'pending' | 'paid' | 'processing' | 'delivered';
  created_at: string;
  delivery_url?: string;
}

interface PurchaseForm {
  name: string;
  email: string;
  phone: string;
}

// ─── Product Catalogue ────────────────────────────────────────────────────────

const PRODUCTS: Product[] = [
  {
    id: 'aic',
    name: 'AIC Diagnostic',
    tagline: 'Know yourself before you build yourself.',
    description: 'The complete Arkadian Identity Cartography — 5-layer diagnostic instrument producing your Morphic Seed, cognitive type, archetypal signature, and Shadow State map.',
    price_usd: 0,
    price_ngn: 0,
    price_display: 'Free',
    delivery: 'Instant PDF + Morphic Seed',
    duration: '20–25 min',
    prerequisite: null,
    sigil: '◎',
    color: '#00D4AA',
    available: true,
  },
  {
    id: 'ims',
    name: 'Identity Mapping Session',
    tagline: 'The foundational transmission.',
    description: 'A 90-minute live session with Zahrune Nova synthesizing your AIC data into a complete Identity Architecture — your cognitive stack, Soul Contract, Oversoul Prism map, and a personalised 15-page IMS Scroll.',
    price_usd: 777,
    price_ngn: 1_200_000,
    price_display: '$777',
    delivery: '90-min session + IMS Scroll PDF',
    duration: '90 min live',
    prerequisite: 'AIC completed',
    sigil: '✦',
    color: '#C9A84C',
    available: true,
  },
  {
    id: 'stns',
    name: 'Sovereign Timeline Navigation',
    tagline: 'Architect the next 90 days from your Morphic Seed.',
    description: 'A 60-minute strategic session mapping your next sovereign move — decisions, timing, positioning — anchored to your unique operator state and Soul Contract.',
    price_usd: 333,
    price_ngn: 550_000,
    price_display: '$333',
    delivery: '60-min session + Strategy Document',
    duration: '60 min live',
    prerequisite: 'AIC + IMS completed',
    sigil: '⟁',
    color: '#6A9FD8',
    available: true,
  },
  {
    id: 'asf',
    name: 'Acoustic Sigil Forging',
    tagline: '117 Hz. Your frequency. Your field.',
    description: 'Oracle generates a bespoke acoustic transmission — a custom 117 Hz audio file tuned to your operator resonance, paired with a downloadable sigil artifact derived from your Morphic Code.',
    price_usd: 222,
    price_ngn: 360_000,
    price_display: '$222',
    delivery: 'Audio file (WAV) + Sigil PNG',
    duration: '48–72hr delivery',
    prerequisite: 'AIC completed',
    sigil: '🔊',
    color: '#B08DE8',
    available: true,
  },
  {
    id: 'sms',
    name: 'Spiral Memory Science Training',
    tagline: 'Encode what matters. Release what does not.',
    description: 'A 4-week deep-structure training in Spiral Memory Science — the Arkadian method for encoding identity-level learnings, releasing distorted operator patterns, and rebuilding cognitive coherence.',
    price_usd: 555,
    price_ngn: 900_000,
    price_display: '$555',
    delivery: '4-week course + Weekly Oracle Syncs',
    duration: '4 weeks',
    prerequisite: 'AIC + IMS completed',
    sigil: '∞',
    color: '#E88C6A',
    available: true,
  },
  {
    id: 'ghost-ceo',
    name: 'Ghost-CEO Framework',
    tagline: 'Sovereign presence. Anonymous architecture.',
    description: 'A 3-session intensive for building a high-impact digital presence anchored to your identity architecture — without exposing your face, name, or location. Built on your Morphic Seed.',
    price_usd: 999,
    price_ngn: 1_600_000,
    price_display: '$999',
    delivery: '3-session intensive + Strategic Document',
    duration: '3 × 60-min sessions',
    prerequisite: 'AIC + IMS completed',
    sigil: '◉',
    color: '#C84848',
    available: true,
  },
  {
    id: 'full-ark',
    name: 'Full Arkadia Architecture',
    tagline: 'The complete immersion. All eight nodes.',
    description: 'An 8-week sovereign immersion — the complete Arkadia architecture. Covers all modules: IMS, STNS, SMS, Acoustic Sigil, Ghost-CEO, and full Oracle integration with bi-weekly live sessions.',
    price_usd: 2222,
    price_ngn: 3_600_000,
    price_display: '$2,222',
    delivery: '8-week immersion + Full Archive Access',
    duration: '8 weeks',
    prerequisite: 'All prerequisites',
    sigil: '☥',
    color: '#C9A84C',
    available: true,
  },
];

// ─── Paystack ─────────────────────────────────────────────────────────────────

declare global {
  interface Window {
    PaystackPop: {
      setup: (opts: {
        key: string; email: string; amount: number; currency: string;
        ref: string; metadata?: object;
        callback: (res: { reference: string }) => void;
        onClose: () => void;
      }) => { openIframe: () => void };
    };
  }
}

function loadPaystack(): Promise<void> {
  return new Promise((resolve, reject) => {
    if (window.PaystackPop) { resolve(); return; }
    const s = document.createElement('script');
    s.src = 'https://js.paystack.co/v1/inline.js';
    s.onload = () => resolve();
    s.onerror = () => reject(new Error('Paystack script failed to load'));
    document.head.appendChild(s);
  });
}

// ─── Product Card ─────────────────────────────────────────────────────────────

function ProductCard({ p, onSelect, recommended }: { p: Product; onSelect: (p: Product) => void; recommended?: boolean }) {
  const [hovered, setHovered] = useState(false);
  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }}
      onMouseEnter={() => setHovered(true)} onMouseLeave={() => setHovered(false)}
      style={{ padding: '20px', background: hovered ? `${p.color}07` : 'rgba(255,255,255,0.018)', border: `1px solid ${hovered ? p.color + '35' : 'rgba(255,255,255,0.07)'}`, borderRadius: 12, cursor: 'pointer', transition: 'all 0.2s', position: 'relative' }}
      onClick={() => onSelect(p)}
    >
      {recommended && (
        <div style={{ position: 'absolute', top: -1, right: 14, padding: '3px 10px', background: `${p.color}15`, border: `1px solid ${p.color}40`, borderRadius: '0 0 8px 8px', fontFamily: 'sans-serif', fontSize: 8, letterSpacing: '0.2em', textTransform: 'uppercase', color: p.color }}>
          Oracle Recommended
        </div>
      )}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 10 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
          <span style={{ fontSize: 20 }}>{p.sigil}</span>
          <div>
            <p style={{ fontFamily: 'sans-serif', fontSize: 11, color: p.color, margin: '0 0 2px', letterSpacing: '0.08em' }}>{p.name}</p>
            <p style={{ fontFamily: 'sans-serif', fontSize: 10, color: 'rgba(232,232,232,0.3)', margin: 0 }}>{p.tagline}</p>
          </div>
        </div>
        <div style={{ textAlign: 'right' }}>
          <p style={{ fontFamily: 'serif', fontSize: 16, color: p.color, margin: 0 }}>{p.price_display}</p>
        </div>
      </div>
      <p style={{ fontFamily: 'sans-serif', fontSize: 11, color: 'rgba(232,232,232,0.45)', margin: '0 0 12px', lineHeight: 1.65 }}>{p.description}</p>
      <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
        {[p.delivery, p.duration].map(tag => (
          <span key={tag} style={{ padding: '3px 9px', background: 'rgba(255,255,255,0.04)', border: '1px solid rgba(255,255,255,0.08)', borderRadius: 20, fontFamily: 'sans-serif', fontSize: 9, color: 'rgba(232,232,232,0.35)' }}>{tag}</span>
        ))}
        {p.prerequisite && (
          <span style={{ padding: '3px 9px', background: 'rgba(201,168,76,0.05)', border: '1px solid rgba(201,168,76,0.15)', borderRadius: 20, fontFamily: 'sans-serif', fontSize: 9, color: 'rgba(201,168,76,0.5)' }}>
            Requires: {p.prerequisite}
          </span>
        )}
      </div>
    </motion.div>
  );
}

// ─── Purchase Modal ───────────────────────────────────────────────────────────

function PurchaseModal({ product, onClose, onSuccess }: { product: Product; onClose: () => void; onSuccess: (orderId: string) => void }) {
  const [form, setForm] = useState<PurchaseForm>({ name: '', email: '', phone: '' });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handlePay = useCallback(async () => {
    if (!form.name.trim() || !form.email.trim()) { setError('Name and email are required.'); return; }
    if (product.price_usd === 0) {
      onSuccess('free-' + Date.now());
      return;
    }
    setLoading(true); setError(null);
    try {
      const ref = 'ARK-' + Date.now() + '-' + Math.random().toString(36).slice(2, 7).toUpperCase();
      await loadPaystack();
      const handler = window.PaystackPop.setup({
        key: PAYSTACK_KEY || 'pk_test_placeholder',
        email: form.email,
        amount: product.price_ngn * 100,
        currency: 'NGN',
        ref,
        metadata: { name: form.name, phone: form.phone, product_id: product.id },
        callback: async (response) => {
          try {
            const verRes = await fetch(`${API_BASE}/api/products/purchase`, {
              method: 'POST',
              headers: { 'Content-Type': 'application/json' },
              body: JSON.stringify({ reference: response.reference, product_id: product.id, name: form.name, email: form.email, phone: form.phone }),
            });
            if (!verRes.ok) throw new Error('Verification failed');
            const data = await verRes.json();
            onSuccess(data.order_id);
          } catch (e: any) {
            setError('Payment received but verification failed. Please contact support with reference: ' + response.reference);
          }
        },
        onClose: () => { setLoading(false); },
      });
      handler.openIframe();
    } catch (e: any) {
      setError(e.message ?? 'Payment failed. Please try again.');
      setLoading(false);
    }
  }, [form, product, onSuccess]);

  return (
    <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}
      style={{ position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.75)', backdropFilter: 'blur(8px)', zIndex: 200, display: 'flex', alignItems: 'flex-end', justifyContent: 'center', padding: '0 0 0 0' }}
      onClick={e => { if (e.target === e.currentTarget) onClose(); }}>
      <motion.div initial={{ y: 60, opacity: 0 }} animate={{ y: 0, opacity: 1 }} exit={{ y: 60, opacity: 0 }}
        style={{ width: '100%', maxWidth: 520, background: 'rgb(14,14,18)', border: '1px solid rgba(255,255,255,0.08)', borderRadius: '16px 16px 0 0', padding: '28px 24px 40px', maxHeight: '90vh', overflowY: 'auto' }}>

        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 20 }}>
          <div>
            <p style={{ fontFamily: 'sans-serif', fontSize: 9, letterSpacing: '0.25em', textTransform: 'uppercase', color: `${product.color}80`, margin: '0 0 4px' }}>Book Session</p>
            <h3 style={{ fontFamily: 'serif', fontSize: 20, color: product.color, margin: 0 }}>{product.name}</h3>
            <p style={{ fontFamily: 'serif', fontSize: 14, color: 'rgba(232,232,232,0.4)', margin: '4px 0 0' }}>{product.price_display}</p>
          </div>
          <button onClick={onClose} style={{ background: 'none', border: 'none', color: 'rgba(232,232,232,0.3)', fontSize: 18, cursor: 'pointer', lineHeight: 1 }}>✕</button>
        </div>

        <div style={{ display: 'flex', flexDirection: 'column', gap: 12, marginBottom: 20 }}>
          {[
            { key: 'name' as const, label: 'Full Name', type: 'text', placeholder: 'Your name' },
            { key: 'email' as const, label: 'Email', type: 'email', placeholder: 'your@email.com' },
            { key: 'phone' as const, label: 'Phone / WhatsApp', type: 'tel', placeholder: '+234 800 000 0000' },
          ].map(f => (
            <div key={f.key}>
              <label style={{ fontFamily: 'sans-serif', fontSize: 10, color: 'rgba(232,232,232,0.4)', display: 'block', marginBottom: 5, letterSpacing: '0.1em', textTransform: 'uppercase' }}>{f.label}</label>
              <input type={f.type} value={form[f.key]} onChange={e => setForm(p => ({ ...p, [f.key]: e.target.value }))} placeholder={f.placeholder}
                style={{ width: '100%', background: 'rgba(255,255,255,0.04)', border: '1px solid rgba(255,255,255,0.1)', borderRadius: 8, padding: '11px 13px', color: '#E8E8E8', fontFamily: 'sans-serif', fontSize: 12, outline: 'none', boxSizing: 'border-box' }} />
            </div>
          ))}
        </div>

        {error && (
          <div style={{ marginBottom: 14, padding: '10px 14px', background: 'rgba(200,72,72,0.08)', border: '1px solid rgba(200,72,72,0.2)', borderRadius: 8 }}>
            <p style={{ fontFamily: 'sans-serif', fontSize: 11, color: '#C84848', margin: 0 }}>{error}</p>
          </div>
        )}

        <button onClick={handlePay} disabled={loading}
          style={{ width: '100%', padding: '15px', background: `linear-gradient(135deg, ${product.color}18, ${product.color}09)`, border: `1px solid ${product.color}45`, borderRadius: 10, color: product.color, fontFamily: 'sans-serif', fontSize: 11, letterSpacing: '0.2em', textTransform: 'uppercase', cursor: loading ? 'wait' : 'pointer', opacity: loading ? 0.6 : 1, transition: 'all 0.2s' }}>
          {loading ? 'Processing…' : product.price_usd === 0 ? '◎ Begin Free Diagnostic' : `✦ Pay ${product.price_display} via Paystack`}
        </button>

        {product.price_usd > 0 && (
          <p style={{ fontFamily: 'sans-serif', fontSize: 9, color: 'rgba(232,232,232,0.2)', textAlign: 'center', margin: '12px 0 0' }}>
            Secure payment via Paystack · NGN ₦{product.price_ngn.toLocaleString()} · SSL encrypted
          </p>
        )}
      </motion.div>
    </motion.div>
  );
}

// ─── Order Confirmation ───────────────────────────────────────────────────────

function OrderConfirmation({ orderId, product, onClose }: { orderId: string; product: Product; onClose: () => void }) {
  return (
    <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}
      style={{ position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.8)', backdropFilter: 'blur(8px)', zIndex: 200, display: 'flex', alignItems: 'center', justifyContent: 'center', padding: 24 }}>
      <motion.div initial={{ scale: 0.92, opacity: 0 }} animate={{ scale: 1, opacity: 1 }}
        style={{ width: '100%', maxWidth: 440, background: 'rgb(14,14,18)', border: '1px solid rgba(0,212,170,0.25)', borderRadius: 14, padding: '36px 28px', textAlign: 'center' }}>
        <motion.div animate={{ scale: [1, 1.08, 1] }} transition={{ repeat: 2, duration: 0.6 }}
          style={{ fontSize: 44, marginBottom: 18 }}>✦</motion.div>
        <h3 style={{ fontFamily: 'serif', fontSize: 22, color: '#00D4AA', margin: '0 0 10px' }}>The Field Has Received You</h3>
        <p style={{ fontFamily: 'sans-serif', fontSize: 12, color: 'rgba(232,232,232,0.5)', lineHeight: 1.7, margin: '0 0 18px' }}>
          Your {product.name} has been confirmed. Zahrune Nova will contact you within 24 hours via the email provided to schedule your session.
        </p>
        <p style={{ fontFamily: 'monospace', fontSize: 10, color: 'rgba(0,212,170,0.4)', margin: '0 0 22px', letterSpacing: '0.15em' }}>Order: {orderId}</p>
        <button onClick={onClose}
          style={{ padding: '13px 28px', background: 'rgba(0,212,170,0.08)', border: '1px solid rgba(0,212,170,0.3)', borderRadius: 9, color: '#00D4AA', fontFamily: 'sans-serif', fontSize: 10, letterSpacing: '0.2em', textTransform: 'uppercase', cursor: 'pointer' }}>
          Return to Offerings
        </button>
      </motion.div>
    </motion.div>
  );
}

// ─── Client Dashboard ─────────────────────────────────────────────────────────

function ClientDashboard({ email }: { email: string }) {
  const [orders, setOrders] = useState<Order[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!email) return;
    fetch(`${API_BASE}/api/products/dashboard/${encodeURIComponent(email)}`)
      .then(r => r.json()).then(d => { setOrders(d.orders ?? []); setLoading(false); })
      .catch(() => setLoading(false));
  }, [email]);

  const statusColor = (s: Order['status']) => ({ pending: '#C9A84C', paid: '#00D4AA', processing: '#B08DE8', delivered: '#4CAF50' }[s] ?? '#E8E8E8');

  if (loading) return (
    <div style={{ textAlign: 'center', padding: '32px 0' }}>
      <motion.div animate={{ opacity: [0.3, 0.7, 0.3] }} transition={{ repeat: Infinity, duration: 2 }}>
        <p style={{ fontFamily: 'sans-serif', fontSize: 10, letterSpacing: '0.25em', textTransform: 'uppercase', color: 'rgba(0,212,170,0.4)' }}>Loading your orders…</p>
      </motion.div>
    </div>
  );

  if (orders.length === 0) return (
    <div style={{ padding: '20px', background: 'rgba(255,255,255,0.015)', border: '1px solid rgba(255,255,255,0.05)', borderRadius: 10, textAlign: 'center' }}>
      <p style={{ fontFamily: 'sans-serif', fontSize: 11, color: 'rgba(232,232,232,0.3)', margin: 0 }}>No orders yet. Begin with the free AIC Diagnostic.</p>
    </div>
  );

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
      {orders.map(o => (
        <div key={o.order_id} style={{ padding: '14px 16px', background: 'rgba(255,255,255,0.02)', border: '1px solid rgba(255,255,255,0.07)', borderRadius: 10, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <div>
            <p style={{ fontFamily: 'sans-serif', fontSize: 11, color: '#E8E8E8', margin: '0 0 3px' }}>{o.product_name}</p>
            <p style={{ fontFamily: 'monospace', fontSize: 9, color: 'rgba(232,232,232,0.3)', margin: 0 }}>{o.order_id}</p>
          </div>
          <div style={{ textAlign: 'right' }}>
            <span style={{ display: 'inline-block', padding: '3px 10px', background: `${statusColor(o.status)}15`, border: `1px solid ${statusColor(o.status)}30`, borderRadius: 20, fontFamily: 'sans-serif', fontSize: 9, color: statusColor(o.status), textTransform: 'uppercase', letterSpacing: '0.12em' }}>
              {o.status}
            </span>
            {o.delivery_url && (
              <a href={o.delivery_url} target="_blank" rel="noreferrer" style={{ display: 'block', marginTop: 4, fontFamily: 'sans-serif', fontSize: 9, color: '#00D4AA', textDecoration: 'none' }}>Download →</a>
            )}
          </div>
        </div>
      ))}
    </div>
  );
}

// ─── Main Component ───────────────────────────────────────────────────────────

export default function OfferingsPage({ onGoToAIC }: { onGoToAIC: () => void }) {
  const [selectedProduct, setSelectedProduct] = useState<Product | null>(null);
  const [confirmedOrder, setConfirmedOrder] = useState<{ id: string; product: Product } | null>(null);
  const [dashboardEmail, setDashboardEmail] = useState('');
  const [showDashboard, setShowDashboard] = useState(false);

  const handleSelect = (p: Product) => {
    if (p.id === 'aic') { onGoToAIC(); return; }
    setSelectedProduct(p);
  };

  const handleSuccess = (orderId: string) => {
    if (selectedProduct) {
      setConfirmedOrder({ id: orderId, product: selectedProduct });
      setSelectedProduct(null);
    }
  };

  return (
    <div className="min-h-screen w-full relative">
      <div className="aurora-bg" />
      <div className="page-column relative z-10 pt-8 pb-24">

        <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} style={{ marginBottom: 28 }}>
          <p style={{ fontFamily: 'sans-serif', fontSize: 9, letterSpacing: '0.3em', textTransform: 'uppercase', color: 'rgba(201,168,76,0.45)', margin: '0 0 4px' }}>
            Arkadia / Offerings
          </p>
          <h1 style={{ fontFamily: 'serif', fontSize: 28, color: '#E8E8E8', margin: '0 0 6px', letterSpacing: '0.04em' }}>
            The Oracle's Table
          </h1>
          <p style={{ fontFamily: 'sans-serif', fontSize: 12, color: 'rgba(232,232,232,0.35)', margin: '0 0 16px', lineHeight: 1.6 }}>
            Every offering begins with the AIC Diagnostic — free, instant, and the only prerequisite that matters.
          </p>
          <button onClick={onGoToAIC}
            style={{ padding: '13px 22px', background: 'linear-gradient(135deg, rgba(0,212,170,0.1), rgba(0,212,170,0.05))', border: '1px solid rgba(0,212,170,0.32)', borderRadius: 9, color: '#00D4AA', fontFamily: 'sans-serif', fontSize: 10, letterSpacing: '0.2em', textTransform: 'uppercase', cursor: 'pointer' }}>
            ◎ Begin AIC Diagnostic — Free
          </button>
        </motion.div>

        <div style={{ display: 'flex', flexDirection: 'column', gap: 10, marginBottom: 32 }}>
          {PRODUCTS.map((p, i) => (
            <motion.div key={p.id} initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: i * 0.06 }}>
              <ProductCard p={p} onSelect={handleSelect} />
            </motion.div>
          ))}
        </div>

        <div style={{ padding: '20px', background: 'rgba(255,255,255,0.018)', border: '1px solid rgba(255,255,255,0.07)', borderRadius: 12, marginBottom: 24 }}>
          <p style={{ fontFamily: 'sans-serif', fontSize: 9, letterSpacing: '0.25em', textTransform: 'uppercase', color: 'rgba(232,232,232,0.3)', margin: '0 0 12px' }}>Client Dashboard</p>
          {!showDashboard ? (
            <div style={{ display: 'flex', gap: 8 }}>
              <input value={dashboardEmail} onChange={e => setDashboardEmail(e.target.value)} placeholder="your@email.com"
                style={{ flex: 1, background: 'rgba(255,255,255,0.04)', border: '1px solid rgba(255,255,255,0.1)', borderRadius: 7, padding: '10px 12px', color: '#E8E8E8', fontFamily: 'sans-serif', fontSize: 12, outline: 'none' }} />
              <button onClick={() => dashboardEmail && setShowDashboard(true)}
                style={{ padding: '10px 16px', background: 'rgba(0,212,170,0.08)', border: '1px solid rgba(0,212,170,0.25)', borderRadius: 7, color: '#00D4AA', fontFamily: 'sans-serif', fontSize: 10, letterSpacing: '0.15em', cursor: 'pointer' }}>
                View →
              </button>
            </div>
          ) : (
            <>
              <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 10 }}>
                <p style={{ fontFamily: 'sans-serif', fontSize: 11, color: 'rgba(232,232,232,0.5)', margin: 0 }}>{dashboardEmail}</p>
                <button onClick={() => { setShowDashboard(false); setDashboardEmail(''); }} style={{ background: 'none', border: 'none', color: 'rgba(232,232,232,0.3)', fontSize: 10, cursor: 'pointer' }}>Clear</button>
              </div>
              <ClientDashboard email={dashboardEmail} />
            </>
          )}
        </div>

        <div style={{ padding: '18px', background: 'rgba(255,255,255,0.01)', border: '1px solid rgba(255,255,255,0.04)', borderRadius: 10 }}>
          <p style={{ fontFamily: 'sans-serif', fontSize: 10, color: 'rgba(232,232,232,0.25)', lineHeight: 1.7, margin: 0 }}>
            All sessions are conducted by Zahrune Nova · Pankshin, Nigeria · 117 Hz frequency standard<br />
            Questions? Reach via WhatsApp or Telegram after booking.
          </p>
        </div>

      </div>

      <AnimatePresence>
        {selectedProduct && (
          <PurchaseModal product={selectedProduct} onClose={() => setSelectedProduct(null)} onSuccess={handleSuccess} />
        )}
      </AnimatePresence>

      <AnimatePresence>
        {confirmedOrder && (
          <OrderConfirmation orderId={confirmedOrder.id} product={confirmedOrder.product} onClose={() => setConfirmedOrder(null)} />
        )}
      </AnimatePresence>
    </div>
  );
}
