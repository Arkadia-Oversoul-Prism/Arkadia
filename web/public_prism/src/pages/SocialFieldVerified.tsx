/**
 * NovaNet — public social field (M03).
 *
 * Public transmissions use /api/transmissions.
 * Private ReasoMate uses ReasoMateSurface (same as /reasomate) — never Knowledge OS.
 */
import { apiFetch } from "../lib/apiClient";
import { API_BASE as API_BASE_CONFIG } from "../lib/apiConfig";
import React, { useEffect, useState } from "react";
import { useAuth } from "../contexts/AuthContext";
import MarkdownViewer from "../components/MarkdownViewer";
import ReasoMateSurface from "../components/ReasoMateSurface";
import { formatToArkadiaMarkdown } from "../lib/arkadiaFormatter";

const API_BASE = (API_BASE_CONFIG ?? "").replace(/\/$/, "");
const C = {
  teal: "#00D4AA",
  blue: "#6A9FD8",
  red: "#C84848",
  text: "rgba(232,232,232,.9)",
  dim: "rgba(232,232,232,.35)",
  card: "rgba(14,17,32,.78)",
  border: "rgba(106,159,216,.14)",
  gold: "#C9A84C",
};

type Post = {
  id: string;
  owner_uid?: string;
  author: any;
  content: string;
  timestamp: number;
  edited_at?: number;
};

const ago = (ts: number) => {
  const d = Date.now() - ts;
  if (d < 60000) return "now";
  if (d < 3600000) return `${Math.floor(d / 60000)}m`;
  if (d < 86400000) return `${Math.floor(d / 3600000)}h`;
  return `${Math.floor(d / 86400000)}d`;
};

const button = (color: string, disabled = false): React.CSSProperties => ({
  padding: "7px 11px",
  background: `${color}10`,
  border: `1px solid ${color}35`,
  borderRadius: 8,
  color: disabled ? C.dim : color,
  cursor: disabled ? "not-allowed" : "pointer",
  fontSize: 9,
  letterSpacing: ".1em",
  textTransform: "uppercase",
});

function Composer({
  profile,
  onCreated,
}: {
  profile: any;
  onCreated: (post: Post) => void;
}) {
  const [text, setText] = useState("");
  const [busy, setBusy] = useState(false);
  const submit = async () => {
    if (!text.trim() || busy) return;
    setBusy(true);
    try {
      const response = await apiFetch(`/api/transmissions`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          content: formatToArkadiaMarkdown(text),
          author: {
            name: profile?.display_name || "Node",
            avatar: profile?.role_sigil || "◈",
            role: profile?.role || "Node",
          },
        }),
      });
      if (response.ok) {
        const data = await response.json();
        onCreated(data.transmission);
        setText("");
      }
    } finally {
      setBusy(false);
    }
  };
  return (
    <div
      style={{
        background: C.card,
        border: `1px solid ${C.border}`,
        borderRadius: 12,
        padding: 13,
        marginBottom: 12,
      }}
    >
      <div style={{ fontSize: 9, color: C.dim, marginBottom: 8, letterSpacing: ".08em" }}>
        PUBLIC TRANSMISSION · visible on the field
      </div>
      <textarea
        value={text}
        onChange={(event) => setText(event.target.value)}
        placeholder="Transmit something to the public field…"
        rows={3}
        style={{
          width: "100%",
          boxSizing: "border-box",
          background: "rgba(0,0,0,.22)",
          border: "1px solid rgba(255,255,255,.07)",
          borderRadius: 9,
          padding: 10,
          color: C.text,
          resize: "vertical",
          outline: "none",
          fontFamily: "inherit",
          fontSize: 13,
        }}
      />
      <div style={{ display: "flex", justifyContent: "flex-end", marginTop: 8 }}>
        <button type="button" onClick={submit} disabled={busy || !text.trim()} style={button(C.teal, busy || !text.trim())}>
          {busy ? "Sending…" : "Transmit"}
        </button>
      </div>
    </div>
  );
}

function PostCard({
  post,
  myUid,
  onChange,
}: {
  post: Post;
  myUid: string;
  onChange: (next: Post | null) => void;
}) {
  const [editing, setEditing] = useState(false);
  const [draft, setDraft] = useState(post.content);
  const [busy, setBusy] = useState(false);
  const mine = Boolean(myUid && post.owner_uid && myUid === post.owner_uid);

  const save = async () => {
    setBusy(true);
    try {
      const response = await apiFetch(`/api/transmissions/${post.id}`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ content: formatToArkadiaMarkdown(draft) }),
      });
      if (response.ok) {
        const data = await response.json();
        onChange(data.transmission || { ...post, content: draft });
        setEditing(false);
      }
    } finally {
      setBusy(false);
    }
  };

  const remove = async () => {
    setBusy(true);
    try {
      const response = await apiFetch(`/api/transmissions/${post.id}`, { method: "DELETE" });
      if (response.ok) onChange(null);
    } finally {
      setBusy(false);
    }
  };

  return (
    <article
      data-testid="novanet-public-post"
      style={{
        background: C.card,
        border: `1px solid ${C.border}`,
        borderRadius: 12,
        padding: 14,
        marginBottom: 10,
      }}
    >
      <div style={{ display: "flex", gap: 10, marginBottom: 8 }}>
        <span style={{ fontSize: 18 }}>{post.author?.avatar || "◈"}</span>
        <div style={{ flex: 1 }}>
          <div style={{ fontSize: 12, color: C.text }}>{post.author?.name || "Node"}</div>
          <div style={{ fontSize: 9, color: C.dim }}>
            {ago(post.timestamp)} · public field
          </div>
        </div>
        {mine && (
          <div style={{ display: "flex", gap: 6 }}>
            <button type="button" style={button(C.blue)} onClick={() => setEditing((v) => !v)} disabled={busy}>
              Edit
            </button>
            <button type="button" style={button(C.red)} onClick={remove} disabled={busy}>
              Delete
            </button>
          </div>
        )}
      </div>
      {editing ? (
        <div>
          <textarea
            value={draft}
            onChange={(e) => setDraft(e.target.value)}
            rows={4}
            style={{
              width: "100%",
              boxSizing: "border-box",
              background: "rgba(0,0,0,.22)",
              border: "1px solid rgba(255,255,255,.07)",
              borderRadius: 9,
              padding: 10,
              color: C.text,
            }}
          />
          <button type="button" onClick={save} disabled={busy} style={{ ...button(C.teal), marginTop: 8 }}>
            Save
          </button>
        </div>
      ) : (
        <MarkdownViewer content={post.content} />
      )}
    </article>
  );
}

function PublicFeed({ canTransmit, profile }: { canTransmit: boolean; profile: any }) {
  const [posts, setPosts] = useState<Post[]>([]);
  const [error, setError] = useState("");

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const response = await apiFetch(`/api/transmissions`);
        if (!response.ok) throw new Error(String(response.status));
        const data = await response.json();
        if (!cancelled) setPosts(data.transmissions || data.posts || []);
      } catch (e: any) {
        if (!cancelled) setError(e?.message || "feed unavailable");
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [canTransmit]);

  return (
    <div data-testid="novanet-public-feed" style={{ maxWidth: 720, margin: "0 auto" }}>
      <div
        style={{
          marginBottom: 12,
          padding: "10px 12px",
          borderRadius: 10,
          border: `1px solid ${C.border}`,
          background: "rgba(0,212,170,0.06)",
          fontSize: 11,
          color: C.dim,
        }}
      >
        <strong style={{ color: C.teal }}>PUBLIC FIELD</strong>
        {" · "}
        Transmissions are visible on NovaNet. This is not ReasoMate, private memory, or Knowledge OS.
      </div>
      {canTransmit ? (
        <Composer
          profile={profile}
          onCreated={(post) => setPosts((current) => [post, ...current])}
        />
      ) : (
        <div style={{ color: C.dim, fontSize: 12, marginBottom: 12 }}>
          Sign in to transmit. The public feed remains readable where the API allows.
        </div>
      )}
      {error && <div style={{ color: C.red, fontSize: 12, marginBottom: 8 }}>{error}</div>}
      {posts.map((post) => (
        <PostCard
          key={post.id}
          post={post}
          myUid={profile?.uid || ""}
          onChange={(next) =>
            setPosts((current) =>
              next
                ? current.map((item) => (item.id === next.id ? next : item))
                : current.filter((item) => item.id !== post.id)
            )
          }
        />
      ))}
      {!posts.length && !error && (
        <div style={{ color: C.dim, fontSize: 12, textAlign: "center", padding: 24 }}>
          No public transmissions yet.
        </div>
      )}
    </div>
  );
}

export default function SocialFieldVerified() {
  const { profile, isAuthenticated } = useAuth();
  const [mode, setMode] = useState<"field" | "reasomate">("field");
  const canTransmit = Boolean(isAuthenticated && profile);

  return (
    <div
      data-testid="novanet-public-field"
      style={{ minHeight: "calc(100vh - 80px)", color: C.text }}
    >
      <header
        style={{
          display: "flex",
          alignItems: "center",
          gap: 10,
          marginBottom: 14,
          flexWrap: "wrap",
        }}
      >
        <span style={{ color: C.blue, fontSize: 20 }}>◉</span>
        <div>
          <h2 style={{ margin: 0, fontFamily: "Cinzel,serif", fontSize: 20 }}>NovaNet</h2>
          <div style={{ color: C.dim, fontSize: 9 }}>
            Public social field · private ReasoMate remains separate
          </div>
        </div>
        <div style={{ marginLeft: "auto", display: "flex", gap: 5 }}>
          <button
            type="button"
            data-testid="novanet-tab-public"
            onClick={() => setMode("field")}
            style={button(mode === "field" ? C.teal : C.dim)}
          >
            Public Field
          </button>
          <button
            type="button"
            data-testid="novanet-tab-reasomate"
            onClick={() => setMode("reasomate")}
            style={button(mode === "reasomate" ? C.blue : C.dim)}
          >
            ReasoMate (private)
          </button>
        </div>
      </header>

      {/* P0.4 persistent public/private mode chrome */}
      <div
        data-testid="novanet-mode-chrome"
        role="tablist"
        aria-label="NovaNet mode"
        style={{
          display: 'flex',
          gap: 8,
          marginBottom: 14,
          padding: 6,
          borderRadius: 12,
          border: `1px solid ${C.border}`,
          background: 'rgba(0,0,0,0.25)',
        }}
      >
        <button
          type="button"
          role="tab"
          aria-selected={mode === 'field'}
          data-testid="novanet-mode-public"
          onClick={() => setMode('field')}
          style={{
            flex: 1,
            padding: '10px 12px',
            borderRadius: 10,
            border: mode === 'field' ? `1px solid ${C.teal}` : '1px solid transparent',
            background: mode === 'field' ? 'rgba(0,212,170,0.12)' : 'transparent',
            color: mode === 'field' ? C.teal : C.dim,
            cursor: 'pointer',
            fontSize: 11,
            letterSpacing: '0.12em',
            textTransform: 'uppercase' as const,
          }}
        >
          Public Field
        </button>
        <button
          type="button"
          role="tab"
          aria-selected={mode === 'reasomate'}
          data-testid="novanet-mode-private"
          onClick={() => setMode('reasomate')}
          style={{
            flex: 1,
            padding: '10px 12px',
            borderRadius: 10,
            border: mode === 'reasomate' ? `1px solid ${C.gold}` : '1px solid transparent',
            background: mode === 'reasomate' ? 'rgba(201,168,76,0.12)' : 'transparent',
            color: mode === 'reasomate' ? C.gold : C.dim,
            cursor: 'pointer',
            fontSize: 11,
            letterSpacing: '0.12em',
            textTransform: 'uppercase' as const,
          }}
        >
          Private Thread
        </button>
      </div>
      {mode === "field" ? (
        <PublicFeed canTransmit={canTransmit} profile={profile} />
      ) : (
        <div data-testid="novanet-private-reasomate-slot">
          <div
            data-testid="novanet-private-chrome"
            style={{
              marginBottom: 12,
              padding: '10px 12px',
              borderRadius: 10,
              border: `1px solid rgba(201,168,76,0.28)`,
              background: 'rgba(201,168,76,0.06)',
              fontSize: 11,
              color: C.dim,
            }}
          >
            <strong style={{ color: C.gold }}>PRIVATE THREAD</strong>
            {' · '}
            ReasoMate — not the public field, not Knowledge OS, not transmissions.
          </div>
          {!isAuthenticated ? (
            <div style={{ color: C.dim, padding: 24, textAlign: "center", fontSize: 13 }}>
              ReasoMate is private. Authenticate to open the messenger — it never posts to the public field.
            </div>
          ) : null}
          <ReasoMateSurface />
        </div>
      )}
    </div>
  );
}
