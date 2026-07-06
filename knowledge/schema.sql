-- Arkadia Knowledge OS — Canonical SQLite Schema
-- Every Markdown save updates these tables.
-- LAW III: Markdown is the human format. SQLite is the machine format.

PRAGMA journal_mode=WAL;
PRAGMA foreign_keys=ON;

-- ─────────────────────────────────────────────────────────────
-- PROJECTS
-- ─────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS projects (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    uuid        TEXT NOT NULL UNIQUE,
    name        TEXT NOT NULL,
    description TEXT,
    created_at  TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at  TEXT NOT NULL DEFAULT (datetime('now')),
    status      TEXT NOT NULL DEFAULT 'active',  -- active | archived | suspended
    tags        TEXT NOT NULL DEFAULT '[]'        -- JSON array
);

-- ─────────────────────────────────────────────────────────────
-- THREADS
-- ─────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS threads (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    uuid        TEXT NOT NULL UNIQUE,
    project_id  INTEGER REFERENCES projects(id) ON DELETE SET NULL,
    title       TEXT NOT NULL,
    created_at  TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at  TEXT NOT NULL DEFAULT (datetime('now'))
);

-- ─────────────────────────────────────────────────────────────
-- NOTES  (canonical knowledge objects)
-- ─────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS notes (
    id               INTEGER PRIMARY KEY AUTOINCREMENT,
    uuid             TEXT NOT NULL UNIQUE,
    title            TEXT NOT NULL,
    content          TEXT NOT NULL DEFAULT '',
    vault_path       TEXT NOT NULL,               -- relative path inside vault/
    note_type        TEXT NOT NULL DEFAULT 'note', -- note | conversation | research | book | person | idea | decision | daily
    project_id       INTEGER REFERENCES projects(id) ON DELETE SET NULL,
    thread_id        INTEGER REFERENCES threads(id) ON DELETE SET NULL,
    participants     TEXT NOT NULL DEFAULT '[]',   -- JSON array of node names
    tags             TEXT NOT NULL DEFAULT '[]',   -- JSON array
    links            TEXT NOT NULL DEFAULT '[]',   -- JSON array of UUIDs this note links to
    embedding_status TEXT NOT NULL DEFAULT 'pending', -- pending | complete | failed
    graph_nodes      TEXT NOT NULL DEFAULT '[]',   -- JSON array of related graph node IDs
    checksum         TEXT,                         -- SHA-256 of content for change detection
    source_provider  TEXT,                         -- gemini | claude | gpt | human | system
    created_at       TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at       TEXT NOT NULL DEFAULT (datetime('now'))
);

-- ─────────────────────────────────────────────────────────────
-- CHUNKS  (semantic units for embedding and retrieval)
-- ─────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS chunks (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    note_id    INTEGER NOT NULL REFERENCES notes(id) ON DELETE CASCADE,
    content    TEXT NOT NULL,
    position   INTEGER NOT NULL DEFAULT 0,          -- order within note
    token_count INTEGER,
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

-- ─────────────────────────────────────────────────────────────
-- EMBEDDINGS  (vector representations of chunks)
-- ─────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS embeddings (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    chunk_id   INTEGER NOT NULL REFERENCES chunks(id) ON DELETE CASCADE,
    vector     TEXT NOT NULL,   -- JSON-serialised float array (768-dim text-embedding-004)
    model      TEXT NOT NULL DEFAULT 'text-embedding-004',
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

-- ─────────────────────────────────────────────────────────────
-- TAGS
-- ─────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS tags (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    name       TEXT NOT NULL UNIQUE,
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS note_tags (
    note_id INTEGER NOT NULL REFERENCES notes(id) ON DELETE CASCADE,
    tag_id  INTEGER NOT NULL REFERENCES tags(id)  ON DELETE CASCADE,
    PRIMARY KEY (note_id, tag_id)
);

-- ─────────────────────────────────────────────────────────────
-- GRAPH EDGES  (knowledge relationships)
-- ─────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS graph_edges (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    source_note_id  INTEGER NOT NULL REFERENCES notes(id) ON DELETE CASCADE,
    target_note_id  INTEGER NOT NULL REFERENCES notes(id) ON DELETE CASCADE,
    relationship    TEXT NOT NULL,  -- references | extends | contradicts | summarizes | implements | belongs_to | generated_by | reviewed_by | derived_from
    weight          REAL NOT NULL DEFAULT 1.0,
    created_at      TEXT NOT NULL DEFAULT (datetime('now')),
    UNIQUE(source_note_id, target_note_id, relationship)
);

-- ─────────────────────────────────────────────────────────────
-- TIMELINE  (immutable event log — append only)
-- ─────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS timeline (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    event_type  TEXT NOT NULL,   -- conversation | prompt | response | knowledge_created | knowledge_modified | review | decision | sync | error
    payload     TEXT NOT NULL DEFAULT '{}',  -- JSON
    note_id     INTEGER REFERENCES notes(id) ON DELETE SET NULL,
    project_id  INTEGER REFERENCES projects(id) ON DELETE SET NULL,
    provider    TEXT,
    persona     TEXT,
    created_at  TEXT NOT NULL DEFAULT (datetime('now'))
    -- NO UPDATE — timeline is immutable
);

-- ─────────────────────────────────────────────────────────────
-- REFERENCES  (external citations, URLs, cross-note refs)
-- ─────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS references (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    source_note_id INTEGER NOT NULL REFERENCES notes(id) ON DELETE CASCADE,
    target_ref     TEXT NOT NULL,   -- URL, UUID, or external identifier
    ref_type       TEXT NOT NULL DEFAULT 'url',  -- url | note | book | person | external
    label          TEXT,
    created_at     TEXT NOT NULL DEFAULT (datetime('now'))
);

-- ─────────────────────────────────────────────────────────────
-- ATTACHMENTS
-- ─────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS attachments (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    note_id    INTEGER REFERENCES notes(id) ON DELETE SET NULL,
    filename   TEXT NOT NULL,
    vault_path TEXT NOT NULL,   -- path inside vault/Attachments/
    mime_type  TEXT,
    size_bytes INTEGER,
    checksum   TEXT,
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

-- ─────────────────────────────────────────────────────────────
-- PROVIDERS  (registered AI provider adapters)
-- ─────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS providers (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    name         TEXT NOT NULL UNIQUE,  -- gemini | claude | gpt | deepseek | grok | local
    display_name TEXT NOT NULL,
    model        TEXT,
    capabilities TEXT NOT NULL DEFAULT '[]',  -- JSON: ["chat","embed","stream","vision"]
    status       TEXT NOT NULL DEFAULT 'unconfigured',  -- active | unconfigured | disabled | error
    priority     INTEGER NOT NULL DEFAULT 100,
    config       TEXT NOT NULL DEFAULT '{}',  -- JSON (no secrets — use env vars)
    created_at   TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at   TEXT NOT NULL DEFAULT (datetime('now'))
);

-- ─────────────────────────────────────────────────────────────
-- PERSONAS
-- ─────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS personas (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    name        TEXT NOT NULL UNIQUE,  -- Architect | Reviewer | Editor | Researcher | Critic | Teacher | Planner | Summarizer
    system_prompt TEXT NOT NULL,
    preferred_provider TEXT,           -- NULL = let router decide
    created_at  TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at  TEXT NOT NULL DEFAULT (datetime('now'))
);

-- ─────────────────────────────────────────────────────────────
-- INDEXES for query performance
-- ─────────────────────────────────────────────────────────────
CREATE INDEX IF NOT EXISTS idx_notes_project    ON notes(project_id);
CREATE INDEX IF NOT EXISTS idx_notes_thread     ON notes(thread_id);
CREATE INDEX IF NOT EXISTS idx_notes_type       ON notes(note_type);
CREATE INDEX IF NOT EXISTS idx_notes_created    ON notes(created_at);
CREATE INDEX IF NOT EXISTS idx_chunks_note      ON chunks(note_id);
CREATE INDEX IF NOT EXISTS idx_embeddings_chunk ON embeddings(chunk_id);
CREATE INDEX IF NOT EXISTS idx_graph_source     ON graph_edges(source_note_id);
CREATE INDEX IF NOT EXISTS idx_graph_target     ON graph_edges(target_note_id);
CREATE INDEX IF NOT EXISTS idx_graph_rel        ON graph_edges(relationship);
CREATE INDEX IF NOT EXISTS idx_timeline_type    ON timeline(event_type);
CREATE INDEX IF NOT EXISTS idx_timeline_project ON timeline(project_id);
CREATE INDEX IF NOT EXISTS idx_timeline_created ON timeline(created_at);
CREATE INDEX IF NOT EXISTS idx_note_tags_note   ON note_tags(note_id);
CREATE INDEX IF NOT EXISTS idx_note_tags_tag    ON note_tags(tag_id);

-- ─────────────────────────────────────────────────────────────
-- SEED: default providers
-- ─────────────────────────────────────────────────────────────
INSERT OR IGNORE INTO providers (name, display_name, model, capabilities, status, priority) VALUES
    ('gemini', 'Google Gemini', 'gemini-2.0-flash', '["chat","embed","stream","vision","search"]', 'unconfigured', 10),
    ('claude', 'Anthropic Claude', 'claude-opus-4-5', '["chat","stream","vision"]', 'unconfigured', 20),
    ('gpt',    'OpenAI GPT',    'gpt-4o',           '["chat","stream","vision"]', 'unconfigured', 30),
    ('deepseek','DeepSeek',     'deepseek-chat',     '["chat","stream"]',          'unconfigured', 40),
    ('grok',   'xAI Grok',      'grok-beta',         '["chat","stream"]',          'unconfigured', 50),
    ('local',  'Local LLM',     'ollama',            '["chat"]',                   'unconfigured', 99);

-- SEED: default personas
INSERT OR IGNORE INTO personas (name, system_prompt) VALUES
    ('Architect',  'You are the Architect. You think in systems, design for longevity, and identify structural weaknesses before they manifest. You reason from principles, not patterns.'),
    ('Reviewer',   'You are the Reviewer. You read critically, surface inconsistencies, and ask: what is missing? what contradicts? what could be stronger?'),
    ('Editor',     'You are the Editor. You distil without losing meaning. Clarity is your highest value. You remove what is not needed.'),
    ('Researcher', 'You are the Researcher. You follow threads to their source. You distinguish signal from noise, citation from assumption.'),
    ('Critic',     'You are the Critic. You steelman the opposition before you respond. Discomfort is your instrument.'),
    ('Teacher',    'You are the Teacher. You meet the learner where they are and build a bridge to where they need to be.'),
    ('Planner',    'You are the Planner. You decompose goals into concrete steps, identify dependencies, and anticipate failure modes before they occur.'),
    ('Summarizer', 'You are the Summarizer. You compress without distortion. Every summary must survive scrutiny against the source.');
