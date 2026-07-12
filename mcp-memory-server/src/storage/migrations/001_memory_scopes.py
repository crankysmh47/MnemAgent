"""Idempotent SQLite migration for core/repository memory scopes."""

import sqlite3


def migrate_sqlite(conn: sqlite3.Connection) -> None:
    columns = {row[1] for row in conn.execute("PRAGMA table_info(semantic_graph)")}
    if "scope_type" in columns:
        return
    conn.execute("PRAGMA foreign_keys = OFF")
    conn.executescript("""
    CREATE TABLE semantic_graph_scoped (
      id INTEGER PRIMARY KEY AUTOINCREMENT, user_id TEXT NOT NULL,
      scope_type TEXT NOT NULL DEFAULT 'core' CHECK(scope_type IN ('core','repository')),
      scope_id TEXT NOT NULL DEFAULT 'core', category TEXT DEFAULT 'preference',
      entity_source TEXT NOT NULL, relation TEXT NOT NULL, entity_target TEXT NOT NULL,
      base_utility_q REAL DEFAULT 1.0, injection_count INTEGER DEFAULT 0,
      influence_count INTEGER DEFAULT 0, node_weight REAL DEFAULT 1.0,
      conviction_score REAL DEFAULT 1.0, created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
      last_accessed DATETIME DEFAULT CURRENT_TIMESTAMP,
      UNIQUE(user_id, scope_type, scope_id, entity_source, relation) ON CONFLICT REPLACE
    );
    INSERT INTO semantic_graph_scoped
      (id,user_id,category,entity_source,relation,entity_target,base_utility_q,injection_count,influence_count,node_weight,conviction_score,created_at,last_accessed)
      SELECT id,user_id,category,entity_source,relation,entity_target,base_utility_q,injection_count,influence_count,node_weight,conviction_score,created_at,last_accessed FROM semantic_graph;
    DROP TABLE semantic_graph;
    ALTER TABLE semantic_graph_scoped RENAME TO semantic_graph;
    CREATE INDEX idx_graph_user ON semantic_graph(user_id, category, base_utility_q DESC) WHERE node_weight > 0.1;
    """)
    for table in ("episodic_logs", "memory_events", "prospective_memories"):
        table_columns = {row[1] for row in conn.execute(f"PRAGMA table_info({table})")}
        if "scope_type" not in table_columns:
            conn.execute(f"ALTER TABLE {table} ADD COLUMN scope_type TEXT NOT NULL DEFAULT 'core'")
            conn.execute(f"ALTER TABLE {table} ADD COLUMN scope_id TEXT NOT NULL DEFAULT 'core'")
    conn.execute("PRAGMA foreign_keys = ON")
