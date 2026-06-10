"""Read-only API helpers for graph, metrics, and event feeds."""

from __future__ import annotations

import json
import math
import sqlite3
from pathlib import Path
from typing import Any

from config import settings
from storage.db_manager import get_db_connection, get_total_turns


def _ucb_score(q_i: float, n_i: int, total_turns: int) -> float:
    return q_i + settings.UCB_EXPLORATION_C * math.sqrt(
        math.log(max(total_turns, 1)) / (n_i + 1)
    )


def _belief_row(row: sqlite3.Row, total_turns: int) -> dict[str, Any]:
    q_i = float(row["base_utility_q"])
    n_i = int(row["injection_count"])
    inf_pct = (int(row["influence_count"]) / n_i * 100) if n_i else 0.0
    return {
        "id": int(row["id"]),
        "user_id": row["user_id"],
        "category": row["category"],
        "entity_source": row["entity_source"],
        "relation": row["relation"],
        "entity_target": row["entity_target"],
        "base_utility_q": q_i,
        "injection_count": n_i,
        "influence_count": int(row["influence_count"]),
        "influence_pct": round(inf_pct, 1),
        "node_weight": float(row["node_weight"]),
        "conviction_score": float(row["conviction_score"]),
        "created_at": row["created_at"],
        "last_accessed": row["last_accessed"],
        "ucb_score": round(_ucb_score(q_i, n_i, total_turns), 3),
    }


def get_graph_data(user_id: str, db_path: Path | None = None) -> dict[str, Any]:
    """
    Return beliefs, graph edges, and turn count for the visualizer.

    Args:
        user_id: User identifier.
        db_path: Optional database path override.

    Returns:
        Dict with beliefs, edges, and total_turns keys.
    """
    total_turns = get_total_turns(user_id, db_path)
    conn = get_db_connection(db_path)
    try:
        rows = conn.execute(
            """
            SELECT * FROM semantic_graph
            WHERE user_id = ? AND node_weight > ?
            ORDER BY base_utility_q DESC
            """,
            (user_id, settings.PRUNE_THRESHOLD),
        ).fetchall()
        beliefs = [_belief_row(row, total_turns) for row in rows]

        edges: list[dict[str, Any]] = []
        for i, a in enumerate(beliefs):
            for b in beliefs[i + 1 :]:
                shared = 0
                a_terms = {a["entity_source"], a["entity_target"]}
                b_terms = {b["entity_source"], b["entity_target"]}
                shared = len(a_terms & b_terms)
                if shared:
                    edges.append(
                        {
                            "source": a["id"],
                            "target": b["id"],
                            "weight": shared,
                        }
                    )
        return {"beliefs": beliefs, "edges": edges, "total_turns": total_turns}
    finally:
        conn.close()


def get_events_since(
    user_id: str,
    since: str | None = None,
    limit: int = 100,
    db_path: Path | None = None,
) -> list[dict[str, Any]]:
    """
    Return memory events for a user since an ISO timestamp.

    Args:
        user_id: User identifier.
        since: Optional ISO timestamp filter.
        limit: Maximum events to return.
        db_path: Optional database path override.

    Returns:
        List of event dicts newest-first.
    """
    conn = get_db_connection(db_path)
    try:
        if since:
            rows = conn.execute(
                """
                SELECT * FROM memory_events
                WHERE user_id = ? AND timestamp > ?
                ORDER BY timestamp DESC LIMIT ?
                """,
                (user_id, since, limit),
            ).fetchall()
        else:
            rows = conn.execute(
                """
                SELECT * FROM memory_events
                WHERE user_id = ?
                ORDER BY timestamp DESC LIMIT ?
                """,
                (user_id, limit),
            ).fetchall()
        events: list[dict[str, Any]] = []
        for row in rows:
            detail = None
            if row["detail"]:
                try:
                    detail = json.loads(row["detail"])
                except json.JSONDecodeError:
                    detail = row["detail"]
            events.append(
                {
                    "id": int(row["id"]),
                    "event_type": row["event_type"],
                    "entity_source": row["entity_source"],
                    "entity_target": row["entity_target"],
                    "detail": detail,
                    "timestamp": row["timestamp"],
                }
            )
        return events
    finally:
        conn.close()


def get_metrics_data(user_id: str, db_path: Path | None = None) -> dict[str, Any]:
    """
    Return aggregate metrics and UCB timeline for the visualizer.

    Args:
        user_id: User identifier.
        db_path: Optional database path override.

    Returns:
        Metrics dict including ucb_timeline series.
    """
    graph = get_graph_data(user_id, db_path)
    beliefs = graph["beliefs"]
    total_turns = graph["total_turns"]

    conn = get_db_connection(db_path)
    try:
        session_row = conn.execute(
            "SELECT COUNT(DISTINCT session_id) AS cnt FROM episodic_logs WHERE user_id = ?",
            (user_id,),
        ).fetchone()
        total_sessions = int(session_row["cnt"]) if session_row else 0

        avg_q = (
            sum(b["base_utility_q"] for b in beliefs) / len(beliefs) if beliefs else 0.0
        )

        top_beliefs = sorted(beliefs, key=lambda b: b["base_utility_q"], reverse=True)[:5]
        timeline_labels = list(range(max(1, total_turns - 19), total_turns + 1))
        ucb_timeline: dict[str, list[float]] = {}
        for belief in top_beliefs:
            label = belief["entity_source"][:14]
            ucb_timeline[label] = [
                round(
                    _ucb_score(
                        belief["base_utility_q"],
                        max(0, belief["injection_count"] - (total_turns - turn)),
                        turn,
                    ),
                    3,
                )
                for turn in timeline_labels
            ]

        return {
            "total_beliefs": len(beliefs),
            "total_sessions": total_sessions,
            "avg_q_i": round(avg_q, 3),
            "total_turns": total_turns,
            "ucb_timeline": {
                "turns": timeline_labels,
                "series": ucb_timeline,
            },
        }
    finally:
        conn.close()


def search_memories(
    user_id: str,
    query: str,
    top_k: int = 5,
    db_path: Path | None = None,
) -> list[dict[str, Any]]:
    """
    Keyword search over semantic_graph for MCP memory_search.

    Args:
        user_id: User identifier.
        query: Search text.
        top_k: Maximum results.
        db_path: Optional database path override.

    Returns:
        Matching belief dicts.
    """
    total_turns = get_total_turns(user_id, db_path)
    conn = get_db_connection(db_path)
    try:
        pattern = f"%{query.lower()}%"
        rows = conn.execute(
            """
            SELECT * FROM semantic_graph
            WHERE user_id = ? AND node_weight > ?
              AND (
                LOWER(entity_source) LIKE ?
                OR LOWER(entity_target) LIKE ?
                OR LOWER(relation) LIKE ?
              )
            ORDER BY base_utility_q DESC
            LIMIT ?
            """,
            (user_id, settings.PRUNE_THRESHOLD, pattern, pattern, pattern, top_k),
        ).fetchall()
        return [_belief_row(row, total_turns) for row in rows]
    finally:
        conn.close()
