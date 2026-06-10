"""MCP command handlers for /memory and /memory --mode stats."""

from __future__ import annotations

import logging
import math
from pathlib import Path

from config import settings
from memory.waking import _calculate_ucb_score
from storage.db_manager import get_db_connection

logger = logging.getLogger(__name__)

_EMPTY_MESSAGE = "🧠 No memories stored yet. Start chatting to build your memory graph!"


def _truncate(text: str, max_len: int = 14) -> str:
    if len(text) <= max_len:
        return text
    return text[:12] + ".."


def execute_memory_dump_tool(user_id: str, db_path: Path | None = None) -> str:
    """
    Return a Markdown table of active beliefs and confidence labels.

    Args:
        user_id: User identifier.
        db_path: Optional database path override.

    Returns:
        Markdown formatted memory dump.
    """
    conn = get_db_connection(db_path)
    try:
        rows = conn.execute(
            """
            SELECT entity_source, relation, entity_target, node_weight
            FROM semantic_graph
            WHERE user_id = ? AND node_weight > ?
            ORDER BY base_utility_q DESC
            """,
            (user_id, settings.PRUNE_THRESHOLD),
        ).fetchall()
    finally:
        conn.close()

    if not rows:
        return _EMPTY_MESSAGE

    lines = ["| Belief | Confidence |", "| --- | --- |"]
    for row in rows:
        weight = float(row["node_weight"])
        if weight >= 0.85:
            label = "🟢 High Confidence"
        elif weight >= 0.55:
            label = "🟡 Confident"
        else:
            label = "🔴 Fading Memory"
        belief = f"{row['entity_source']} → {row['relation']} → {row['entity_target']}"
        lines.append(f"| {belief} | {label} |")
    return "\n".join(lines)


def execute_memory_stats_tool(
    user_id: str,
    total_turns: int,
    db_path: Path | None = None,
) -> str:
    """
    Return UCB stats table for jury-facing demo.

    Args:
        user_id: User identifier.
        total_turns: Total episodic turns for live UCB calculation.
        db_path: Optional database path override.

    Returns:
        Markdown formatted stats table.
    """
    conn = get_db_connection(db_path)
    try:
        rows = conn.execute(
            """
            SELECT entity_source, entity_target, category, base_utility_q,
                   injection_count, influence_count
            FROM semantic_graph
            WHERE user_id = ? AND node_weight > ?
            ORDER BY base_utility_q DESC
            """,
            (user_id, settings.PRUNE_THRESHOLD),
        ).fetchall()
    finally:
        conn.close()

    if not rows:
        return _EMPTY_MESSAGE

    lines = ["| Entity Pair (Rel) | Q_i | N_i | Inf% | UCB Score |", "| --- | --- | --- | --- | --- |"]
    total_q = 0.0
    total_injections = 0
    for row in rows:
        q_i = float(row["base_utility_q"])
        n_i = int(row["injection_count"])
        inf_count = int(row["influence_count"])
        inf_pct = (inf_count / max(1, n_i)) * 100
        ucb = _calculate_ucb_score(q_i, n_i, total_turns)
        tag = row["category"][:4].upper()
        pair = (
            f"{_truncate(row['entity_source'])} ➔ {_truncate(row['entity_target'])} [{tag}]"
        )
        lines.append(f"| {pair} | {q_i:.2f} | {n_i} | {inf_pct:.0f}% | {ucb:.3f} |")
        total_q += q_i
        total_injections += n_i

    avg_q = total_q / len(rows)
    lines.append("")
    lines.append(
        f"**Summary:** {len(rows)} beliefs | avg Q_i={avg_q:.2f} | total injections={total_injections}"
    )
    return "\n".join(lines)
