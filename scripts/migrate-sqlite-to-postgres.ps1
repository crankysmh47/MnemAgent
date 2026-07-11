param(
    [string]$SqlitePath = "data/memory_state.db",
    [string]$DatabaseUrl = $env:DATABASE_URL
)

$ErrorActionPreference = "Stop"

if (-not (Test-Path -LiteralPath $SqlitePath)) {
    throw "SQLite database not found: $SqlitePath"
}

if (-not $DatabaseUrl) {
    throw "DATABASE_URL is required. Example: postgresql://mnemagent:password@host:5432/mnemagent"
}

$script = @'
import os
import sqlite3
import sys

import psycopg
from psycopg.rows import dict_row

sqlite_path = sys.argv[1]
database_url = sys.argv[2]

tables = [
    "episodic_logs",
    "semantic_graph",
    "memory_events",
    "user_bindings",
    "user_entities",
    "prospective_memories",
]

sqlite = sqlite3.connect(sqlite_path)
sqlite.row_factory = sqlite3.Row

with psycopg.connect(database_url, row_factory=dict_row) as pg:
    with pg.cursor() as cur:
        for table in tables:
            rows = sqlite.execute(f"SELECT * FROM {table}").fetchall()
            if not rows:
                print(f"{table}: 0 rows")
                continue
            columns = [c for c in rows[0].keys() if c != "id"]
            placeholders = ", ".join(["%s"] * len(columns))
            column_sql = ", ".join(columns)
            for row in rows:
                values = [row[c] for c in columns]
                cur.execute(
                    f"INSERT INTO {table} ({column_sql}) VALUES ({placeholders}) ON CONFLICT DO NOTHING",
                    values,
                )
            print(f"{table}: {len(rows)} row(s)")
    pg.commit()

sqlite.close()
'@

$tmp = New-TemporaryFile
try {
    Set-Content -LiteralPath $tmp -Value $script -Encoding UTF8
    python $tmp $SqlitePath $DatabaseUrl
}
finally {
    Remove-Item -LiteralPath $tmp -Force -ErrorAction SilentlyContinue
}
