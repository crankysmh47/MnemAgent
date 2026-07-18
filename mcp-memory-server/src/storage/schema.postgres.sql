CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE IF NOT EXISTS episodic_logs (
    id             BIGSERIAL PRIMARY KEY,
    user_id        TEXT NOT NULL,
    scope_type     TEXT NOT NULL DEFAULT 'core' CHECK(scope_type IN ('core', 'repository')),
    scope_id       TEXT NOT NULL DEFAULT 'core',
    session_id     TEXT NOT NULL,
    timestamp      TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    user_prompt    TEXT NOT NULL,
    agent_response TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_logs_user
    ON episodic_logs(user_id, timestamp DESC);

CREATE TABLE IF NOT EXISTS semantic_graph (
    id               BIGSERIAL PRIMARY KEY,
    user_id          TEXT NOT NULL,
    scope_type       TEXT NOT NULL DEFAULT 'core' CHECK(scope_type IN ('core', 'repository')),
    scope_id         TEXT NOT NULL DEFAULT 'core',
    category         TEXT DEFAULT 'preference',
    entity_source    TEXT NOT NULL,
    relation         TEXT NOT NULL,
    entity_target    TEXT NOT NULL,
    base_utility_q   DOUBLE PRECISION DEFAULT 1.0,
    injection_count  INTEGER DEFAULT 0,
    influence_count  INTEGER DEFAULT 0,
    node_weight      DOUBLE PRECISION DEFAULT 1.0,
    conviction_score DOUBLE PRECISION DEFAULT 1.0,
    created_at       TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    last_accessed    TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, scope_type, scope_id, entity_source, relation)
);

CREATE INDEX IF NOT EXISTS idx_graph_user
    ON semantic_graph(user_id, category, base_utility_q DESC)
    WHERE node_weight > 0.1;

CREATE TABLE IF NOT EXISTS memory_events (
    id            BIGSERIAL PRIMARY KEY,
    user_id       TEXT NOT NULL,
    scope_type    TEXT NOT NULL DEFAULT 'core' CHECK(scope_type IN ('core', 'repository')),
    scope_id      TEXT NOT NULL DEFAULT 'core',
    event_type    TEXT NOT NULL,
    entity_source TEXT,
    entity_target TEXT,
    detail        TEXT,
    timestamp     TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_events_user
    ON memory_events(user_id, timestamp DESC);

CREATE TABLE IF NOT EXISTS user_bindings (
    id           BIGSERIAL PRIMARY KEY,
    user_id      TEXT NOT NULL,
    channel      TEXT NOT NULL,
    sender_id    TEXT NOT NULL,
    display_name TEXT,
    created_at   TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(channel, sender_id)
);

CREATE INDEX IF NOT EXISTS idx_bindings_user
    ON user_bindings(user_id);

CREATE TABLE IF NOT EXISTS user_entities (
    id          BIGSERIAL PRIMARY KEY,
    user_id     TEXT NOT NULL,
    entity_name TEXT NOT NULL,
    source      TEXT DEFAULT 'memory_update',
    created_at  TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, entity_name)
);

CREATE INDEX IF NOT EXISTS idx_entities_user
    ON user_entities(user_id);

CREATE TABLE IF NOT EXISTS vec_memory (
    id        BIGINT PRIMARY KEY REFERENCES semantic_graph(id) ON DELETE CASCADE,
    embedding vector(384)
);

CREATE TABLE IF NOT EXISTS prospective_memories (
    id             BIGSERIAL PRIMARY KEY,
    user_id        TEXT NOT NULL,
    scope_type     TEXT NOT NULL DEFAULT 'core' CHECK(scope_type IN ('core', 'repository')),
    scope_id       TEXT NOT NULL DEFAULT 'core',
    cue            TEXT NOT NULL,
    action         TEXT NOT NULL,
    source_belief  BIGINT REFERENCES semantic_graph(id) ON DELETE SET NULL,
    fired_count    INTEGER DEFAULT 0,
    created_at     TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    last_fired_at  TIMESTAMPTZ,
    UNIQUE(user_id, scope_type, scope_id, cue, action)
);

CREATE INDEX IF NOT EXISTS idx_prospective_user_cue
    ON prospective_memories(user_id, cue);

ALTER TABLE episodic_logs ADD COLUMN IF NOT EXISTS scope_type TEXT NOT NULL DEFAULT 'core';
ALTER TABLE episodic_logs ADD COLUMN IF NOT EXISTS scope_id TEXT NOT NULL DEFAULT 'core';
ALTER TABLE semantic_graph ADD COLUMN IF NOT EXISTS scope_type TEXT NOT NULL DEFAULT 'core';
ALTER TABLE semantic_graph ADD COLUMN IF NOT EXISTS scope_id TEXT NOT NULL DEFAULT 'core';
ALTER TABLE memory_events ADD COLUMN IF NOT EXISTS scope_type TEXT NOT NULL DEFAULT 'core';
ALTER TABLE memory_events ADD COLUMN IF NOT EXISTS scope_id TEXT NOT NULL DEFAULT 'core';
ALTER TABLE prospective_memories ADD COLUMN IF NOT EXISTS scope_type TEXT NOT NULL DEFAULT 'core';
ALTER TABLE prospective_memories ADD COLUMN IF NOT EXISTS scope_id TEXT NOT NULL DEFAULT 'core';
ALTER TABLE semantic_graph DROP CONSTRAINT IF EXISTS semantic_graph_user_id_entity_source_relation_key;
ALTER TABLE prospective_memories DROP CONSTRAINT IF EXISTS prospective_memories_user_id_cue_action_key;
CREATE UNIQUE INDEX IF NOT EXISTS uq_semantic_graph_scope
    ON semantic_graph(user_id, scope_type, scope_id, entity_source, relation);
CREATE UNIQUE INDEX IF NOT EXISTS uq_prospective_scope
    ON prospective_memories(user_id, scope_type, scope_id, cue, action);

ALTER TABLE episodic_logs ENABLE ROW LEVEL SECURITY;
ALTER TABLE semantic_graph ENABLE ROW LEVEL SECURITY;
ALTER TABLE memory_events ENABLE ROW LEVEL SECURITY;
ALTER TABLE user_bindings ENABLE ROW LEVEL SECURITY;
ALTER TABLE user_entities ENABLE ROW LEVEL SECURITY;
ALTER TABLE prospective_memories ENABLE ROW LEVEL SECURITY;

DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE policyname = 'tenant_ep_logs') THEN
        CREATE POLICY tenant_ep_logs ON episodic_logs
            USING (user_id = current_setting('mnemagent.user_id', true))
            WITH CHECK (user_id = current_setting('mnemagent.user_id', true));
    END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE policyname = 'tenant_semantic_graph') THEN
        CREATE POLICY tenant_semantic_graph ON semantic_graph
            USING (user_id = current_setting('mnemagent.user_id', true))
            WITH CHECK (user_id = current_setting('mnemagent.user_id', true));
    END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE policyname = 'tenant_memory_events') THEN
        CREATE POLICY tenant_memory_events ON memory_events
            USING (user_id = current_setting('mnemagent.user_id', true))
            WITH CHECK (user_id = current_setting('mnemagent.user_id', true));
    END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE policyname = 'tenant_user_bindings') THEN
        CREATE POLICY tenant_user_bindings ON user_bindings
            USING (user_id = current_setting('mnemagent.user_id', true))
            WITH CHECK (user_id = current_setting('mnemagent.user_id', true));
    END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE policyname = 'tenant_user_entities') THEN
        CREATE POLICY tenant_user_entities ON user_entities
            USING (user_id = current_setting('mnemagent.user_id', true))
            WITH CHECK (user_id = current_setting('mnemagent.user_id', true));
    END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE policyname = 'tenant_prospective') THEN
        CREATE POLICY tenant_prospective ON prospective_memories
            USING (user_id = current_setting('mnemagent.user_id', true))
            WITH CHECK (user_id = current_setting('mnemagent.user_id', true));
    END IF;
END $$;
