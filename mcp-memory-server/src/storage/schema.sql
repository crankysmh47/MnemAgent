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

-- vec_memory virtual table is created in db_manager.py after sqlite-vec loads.
