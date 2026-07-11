PRAGMA journal_mode = WAL;
PRAGMA synchronous = NORMAL;
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS episodic_logs (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id        TEXT NOT NULL,
    session_id     TEXT NOT NULL,
    timestamp      DATETIME DEFAULT CURRENT_TIMESTAMP,
    user_prompt    TEXT NOT NULL,
    agent_response TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_logs_user
    ON episodic_logs(user_id, timestamp DESC);

CREATE TABLE IF NOT EXISTS semantic_graph (
    id               INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id          TEXT NOT NULL,
    category         TEXT DEFAULT 'preference',
    entity_source    TEXT NOT NULL,
    relation         TEXT NOT NULL,
    entity_target    TEXT NOT NULL,
    base_utility_q   REAL DEFAULT 1.0,
    injection_count  INTEGER DEFAULT 0,
    influence_count  INTEGER DEFAULT 0,
    node_weight      REAL DEFAULT 1.0,
    conviction_score REAL DEFAULT 1.0,
    created_at       DATETIME DEFAULT CURRENT_TIMESTAMP,
    last_accessed    DATETIME DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, entity_source, relation) ON CONFLICT REPLACE
);

CREATE INDEX IF NOT EXISTS idx_graph_user
    ON semantic_graph(user_id, category, base_utility_q DESC)
    WHERE node_weight > 0.1;

CREATE TABLE IF NOT EXISTS memory_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT NOT NULL,
    event_type TEXT NOT NULL,
    entity_source TEXT,
    entity_target TEXT,
    detail TEXT,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_events_user
    ON memory_events(user_id, timestamp DESC);

CREATE TABLE IF NOT EXISTS user_bindings (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id      TEXT NOT NULL,
    channel      TEXT NOT NULL,
    sender_id    TEXT NOT NULL,
    display_name TEXT,
    created_at   DATETIME DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(channel, sender_id) ON CONFLICT REPLACE
);

CREATE INDEX IF NOT EXISTS idx_bindings_user
    ON user_bindings(user_id);

CREATE TABLE IF NOT EXISTS user_entities (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id     TEXT NOT NULL,
    entity_name TEXT NOT NULL COLLATE NOCASE,
    source      TEXT DEFAULT 'memory_update',
    created_at  DATETIME DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, entity_name) ON CONFLICT IGNORE
);

CREATE INDEX IF NOT EXISTS idx_entities_user
    ON user_entities(user_id);

CREATE TABLE IF NOT EXISTS prospective_memories (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id        TEXT NOT NULL,
    cue            TEXT NOT NULL,
    action         TEXT NOT NULL,
    source_belief  INTEGER,
    fired_count    INTEGER DEFAULT 0,
    created_at     DATETIME DEFAULT CURRENT_TIMESTAMP,
    last_fired_at  DATETIME,
    UNIQUE(user_id, cue, action) ON CONFLICT IGNORE
);

CREATE INDEX IF NOT EXISTS idx_prospective_user_cue
    ON prospective_memories(user_id, cue);

-- vec_memory virtual table is created in db_manager.py after sqlite-vec loads.
