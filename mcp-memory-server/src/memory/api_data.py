"""Read-only API helpers for graph, metrics, and event feeds."""

from __future__ import annotations

import json
import math
import re
import sqlite3
from pathlib import Path
from typing import Any

from config import settings
from storage.db_manager import get_db_connection, get_total_turns
from memory.scopes import MemoryScope

_QUERY_STOP_WORDS = {
    "a",
    "an",
    "and",
    "are",
    "as",
    "at",
    "be",
    "by",
    "can",
    "for",
    "from",
    "i",
    "in",
    "is",
    "it",
    "me",
    "my",
    "of",
    "on",
    "or",
    "our",
    "the",
    "to",
    "use",
    "using",
    "what",
    "with",
}


def _ucb_score(q_i: float, n_i: int, total_turns: int) -> float:
    return q_i + settings.UCB_EXPLORATION_C * math.sqrt(
        math.log(max(total_turns, 1)) / (n_i + 1)
    )


def _norm_term(value: str | None) -> str:
    return re.sub(r"[_\s]+", "-", (value or "").lower()).strip()


def _search_terms(query: str) -> list[str]:
    """Tokenize natural memory_search queries into useful SQL LIKE terms."""
    seen: set[str] = set()
    terms: list[str] = []
    for raw in re.findall(r"[a-zA-Z0-9_+-]+", query.lower()):
        term = raw.strip("_+-")
        if len(term) < 2 or term in _QUERY_STOP_WORDS or term in seen:
            continue
        seen.add(term)
        terms.append(term)
    return terms[:12]


def _build_graph_edges(beliefs: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """
    Semantic edges with healthy density: cluster stars+rings, concept meshes, bridges, affinity.
    """
    edges: list[dict[str, Any]] = []
    pair_best: dict[str, dict[str, Any]] = {}

    def add_edge(a: dict[str, Any], b: dict[str, Any], kind: str, weight: float) -> None:
        if a["id"] == b["id"]:
            return
        lo, hi = sorted((int(a["id"]), int(b["id"])))
        key = f"{lo}-{hi}"
        current = pair_best.get(key)
        if current is None or weight > float(current["weight"]):
            pair_best[key] = {"source": lo, "target": hi, "kind": kind, "weight": weight}

    by_subject: dict[str, list[dict[str, Any]]] = {}
    for belief in beliefs:
        key = _norm_term(belief["entity_source"])
        if not key:
            continue
        by_subject.setdefault(key, []).append(belief)

    for group in by_subject.values():
        if len(group) < 2:
            continue
        ordered = sorted(group, key=lambda b: (b.get("relation") or "", int(b["id"])))
        hub = ordered[0]
        for node in ordered[1:]:
            add_edge(hub, node, "cluster", 0.65)
        for i, node in enumerate(ordered):
            nxt = ordered[(i + 1) % len(ordered)]
            if node["id"] != nxt["id"]:
                add_edge(node, nxt, "cluster", 0.52)

    by_object: dict[str, list[dict[str, Any]]] = {}
    for belief in beliefs:
        key = _norm_term(belief["entity_target"])
        if len(key) < 2:
            continue
        by_object.setdefault(key, []).append(belief)

    for group in by_object.values():
        if len(group) < 2:
            continue
        subjects = {_norm_term(b["entity_source"]) for b in group}
        if len(subjects) < 2:
            continue
        for i, a in enumerate(group):
            for b in group[i + 1 :]:
                add_edge(a, b, "concept", 0.5)

    subject_lookup: dict[str, list[dict[str, Any]]] = {}
    for belief in beliefs:
        key = _norm_term(belief["entity_source"])
        if key:
            subject_lookup.setdefault(key, []).append(belief)

    for belief in beliefs:
        bridge_key = _norm_term(belief["entity_target"])
        for other in subject_lookup.get(bridge_key, []):
            if belief["id"] == other["id"]:
                continue
            if _norm_term(belief["entity_source"]) == _norm_term(other["entity_source"]):
                continue
            add_edge(belief, other, "bridge", 0.48)

    for i, a in enumerate(beliefs):
        a_terms = {_norm_term(a["entity_source"]), _norm_term(a["entity_target"])}
        for b in beliefs[i + 1 :]:
            if _norm_term(a["entity_source"]) == _norm_term(b["entity_source"]):
                continue
            b_terms = {_norm_term(b["entity_source"]), _norm_term(b["entity_target"])}
            shared = len({t for t in a_terms if len(t) > 2} & {t for t in b_terms if len(t) > 2})
            if shared:
                add_edge(a, b, "affinity", 0.32 + shared * 0.1)

    edges.extend(pair_best.values())
    return edges


def _belief_row(row: sqlite3.Row, total_turns: int) -> dict[str, Any]:
    q_i = float(row["base_utility_q"])
    n_i = int(row["injection_count"])
    inf_pct = (int(row["influence_count"]) / n_i * 100) if n_i else 0.0
    return {
        "id": int(row["id"]),
        "user_id": row["user_id"],
        "scope_type": row["scope_type"] if "scope_type" in row.keys() else "core",
        "scope_id": row["scope_id"] if "scope_id" in row.keys() else "core",
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


def get_graph_data(
    user_id: str,
    db_path: Path | None = None,
    *,
    query: str = "",
    category: str | None = None,
    lifecycle: str | None = None,
    cursor: str | None = None,
    limit: int = 150,
    focus_id: int | None = None,
    include_summary: bool = True,
    scope_type: str = "core",
    scope_id: str = "core",
    include_core: bool = False,
) -> dict[str, Any]:
    """
    Return beliefs, graph edges, and turn count for the visualizer.

    Args:
        user_id: User identifier.
        db_path: Optional database path override.

    Returns:
        Dict with beliefs, edges, and total_turns keys.
    """
    scope = MemoryScope(scope_type, scope_id)
    total_turns = get_total_turns(user_id, db_path)
    conn = get_db_connection(db_path)
    try:
        limit = max(1, min(int(limit), 150))
        predicates = ["user_id = ?", "node_weight > ?"]
        base_params: list[Any] = [user_id, settings.PRUNE_THRESHOLD]
        if scope.scope_type == "repository" and include_core:
            predicates.append("((scope_type = ? AND scope_id = ?) OR (scope_type = 'core' AND scope_id = 'core'))")
            base_params.extend([scope.scope_type, scope.scope_id])
        else:
            predicates.extend(["scope_type = ?", "scope_id = ?"])
            base_params.extend([scope.scope_type, scope.scope_id])
        scope_where = " AND ".join(predicates)
        scope_params = list(base_params)
        if category:
            predicates.append("category = ?")
            base_params.append(category)
        if lifecycle == "fading":
            predicates.append("node_weight < 0.35")
        elif lifecycle == "vivid":
            predicates.append("node_weight >= 0.65")
        terms = _search_terms(query)
        for term in terms:
            predicates.append(
                "(LOWER(entity_source) LIKE ? OR LOWER(relation) LIKE ? "
                "OR LOWER(entity_target) LIKE ? OR LOWER(category) LIKE ?)"
            )
            pattern = f"%{term}%"
            base_params.extend([pattern, pattern, pattern, pattern])
        where = " AND ".join(predicates)

        total_row = conn.execute(
            f"SELECT COUNT(*) AS count FROM semantic_graph WHERE {scope_where}", scope_params,
        ).fetchone()
        total_beliefs = int(total_row["count"] if total_row else 0)
        filtered_row = conn.execute(
            f"SELECT COUNT(*) AS count FROM semantic_graph WHERE {where}", base_params
        ).fetchone()
        filtered_total = int(filtered_row["count"] if filtered_row else 0)

        rows = conn.execute(
            f"SELECT * FROM semantic_graph WHERE {where} "
            "ORDER BY base_utility_q DESC, node_weight DESC, id DESC LIMIT ?",
            [*base_params, limit],
        ).fetchall()
        if focus_id is not None and all(int(row["id"]) != focus_id for row in rows):
            focus = conn.execute(
                f"SELECT * FROM semantic_graph WHERE {where} AND id = ?",
                (*base_params, focus_id),
            ).fetchone()
            if focus:
                rows = [focus, *rows[: max(0, limit - 1)]]
        beliefs = [_belief_row(row, total_turns) for row in rows]
        edges = _build_graph_edges(beliefs)[:120]
        summary: dict[str, Any] = {"categories": {}, "average_vitality": 0.0}
        if include_summary:
            category_rows = conn.execute(
                """SELECT category, COUNT(*) AS count FROM semantic_graph
                WHERE user_id = ? AND node_weight > ? AND scope_type = ? AND scope_id = ? GROUP BY category""",
                (user_id, settings.PRUNE_THRESHOLD, scope.scope_type, scope.scope_id),
            ).fetchall()
            summary["categories"] = {row["category"]: int(row["count"]) for row in category_rows}
            vitality = conn.execute(
                """SELECT AVG(node_weight) AS average FROM semantic_graph
                WHERE user_id = ? AND node_weight > ? AND scope_type = ? AND scope_id = ?""",
                (user_id, settings.PRUNE_THRESHOLD, scope.scope_type, scope.scope_id),
            ).fetchone()
            summary["average_vitality"] = round(float(vitality["average"] or 0), 3)
        render_mode = "individual" if total_beliefs <= 120 else "hybrid" if total_beliefs <= 500 else "summary"
        return {
            "beliefs": beliefs,
            "edges": edges,
            "total_turns": total_turns,
            "total_beliefs": total_beliefs,
            "returned_beliefs": len(beliefs),
            "next_cursor": str(beliefs[-1]["id"]) if filtered_total > len(beliefs) and beliefs else None,
            "archive_revision": f"{total_beliefs}:{max((b['id'] for b in beliefs), default=0)}",
            "summary": summary,
            "render_mode": render_mode,
            "truncated": filtered_total > len(beliefs),
        }
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
    category: str | None = None,
    min_confidence: float | None = None,
    db_path: Path | None = None,
    scope_type: str = "core",
    scope_id: str = "core",
) -> list[dict[str, Any]]:
    """
    Keyword search over semantic_graph for MCP memory_search.

    Args:
        user_id: User identifier.
        query: Search text.
        top_k: Maximum results.
        category: Optional category filter (preference, persona, system_state).
        min_confidence: Optional minimum node_weight (0-1).
        db_path: Optional database path override.

    Returns:
        Matching belief dicts.
    """
    scope = MemoryScope(scope_type, scope_id)
    total_turns = get_total_turns(user_id, db_path)
    min_weight = min_confidence if min_confidence is not None else settings.PRUNE_THRESHOLD
    conn = get_db_connection(db_path)
    try:
        terms = _search_terms(query)
        sql = """
            SELECT *, 0 AS term_matches FROM semantic_graph
            WHERE user_id = ? AND node_weight > ? AND scope_type = ? AND scope_id = ?
        """
        params: list[Any] = [user_id, min_weight, scope.scope_type, scope.scope_id]

        if terms:
            term_clauses: list[str] = []
            rank_cases: list[str] = []
            rank_params: list[Any] = []
            for term in terms:
                pattern = f"%{term}%"
                term_clauses.append(
                    """
                    LOWER(entity_source) LIKE ?
                    OR LOWER(entity_target) LIKE ?
                    OR LOWER(relation) LIKE ?
                    """
                )
                params.extend([pattern, pattern, pattern])
                rank_cases.append(
                    """
                    CASE WHEN (
                        LOWER(entity_source) LIKE ?
                        OR LOWER(entity_target) LIKE ?
                        OR LOWER(relation) LIKE ?
                    ) THEN 1 ELSE 0 END
                    """
                )
                rank_params.extend([pattern, pattern, pattern])
            sql = f"""
                SELECT *, ({' + '.join(rank_cases)}) AS term_matches
                FROM semantic_graph
                WHERE user_id = ? AND node_weight > ? AND scope_type = ? AND scope_id = ?
                  AND ({' OR '.join(f'({clause})' for clause in term_clauses)})
            """
            params = rank_params + [user_id, min_weight, scope.scope_type, scope.scope_id] + params[4:]

        if category:
            sql += " AND category = ?"
            params.append(category)
        sql += " ORDER BY term_matches DESC, base_utility_q DESC, node_weight DESC LIMIT ?"
        params.append(top_k)
        rows = conn.execute(sql, params).fetchall()
        return [_belief_row(row, total_turns) for row in rows]
    finally:
        conn.close()


def retrieve_scoped_beliefs(
    user_id: str,
    repository_id: str,
    query: str,
    limit: int = 6,
    db_path: Path | None = None,
) -> list[dict[str, Any]]:
    """Return a deterministic repository-first context window (max 4 repo + 2 core)."""
    scope = MemoryScope("repository", repository_id)
    bounded = max(1, min(int(limit), 6))
    repository_limit = min(4, bounded)
    core_limit = min(2, max(0, bounded - repository_limit))
    repository = search_memories(
        user_id, query, top_k=repository_limit, db_path=db_path,
        scope_type=scope.scope_type, scope_id=scope.scope_id,
    )
    core = search_memories(
        user_id, query, top_k=core_limit, db_path=db_path,
        scope_type="core", scope_id="core",
    ) if core_limit else []
    return [*repository, *core][:bounded]
