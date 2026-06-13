"""Waking phase — embedding, UCB retrieval, RWR hops, and Qwen payload construction."""

from __future__ import annotations

import logging
import math
import re
import sqlite3
from pathlib import Path

import aiohttp
import networkx as nx

from config import settings
from memory.event_log import log_memory_event
from storage.db_manager import VEC_AVAILABLE, get_db_connection, upsert_vec_embedding

logger = logging.getLogger(__name__)

_embedding_cache: dict[str, list[float]] = {}
_local_model = None

CORE_TECH_DICTIONARY = {
    "python", "javascript", "typescript", "java", "react", "vue", "angular",
    "express", "fastify", "docker", "kubernetes", "postgres", "postgresql",
    "redis", "mysql", "mariadb", "mongodb", "tailwind", "graphql", "rest",
    "aws", "azure", "gcp", "nginx", "linux", "node", "nodejs", "fastapi",
    "django", "flask", "spring", "kotlin", "swift", "rust", "go", "golang",
    "csharp", "dotnet", "terraform", "ansible", "jenkins", "github", "gitlab",
    "vscode", "vim", "webpack", "vite", "nextjs", "nuxt", "svelte", "lodash",
    "heroku", "ecs", "lambda", "sqlite", "qwen", "openclaw",
}

SYSTEM_PROMPT_TEMPLATE = """You are an autonomous engineering agent with a persistent memory layer called MnemOS.

[MEMORY CONTEXT — Retrieved from long-term storage]
{injected_facts}

Use the memory context above to personalize your responses. Reference stored
preferences naturally without re-asking.

MANDATORY: Every response MUST begin with a <memory_update> block BEFORE any other text.
- If nothing new was learned: <memory_update>{{"skip": true}}</memory_update>
- If facts were learned: one JSON object per line (JSONL) inside the block
- Never output raw memory JSON outside the tags

Format:
<memory_update>
{{"entity":"subject","relation":"type","value":"detail","category":"preference|persona|system_state","conviction":0.0}}
</memory_update>
Your conversational reply follows here.

Categories: preference, persona, system_state.
Conviction: 1.0=definitive, 0.8=strong, 0.5=stated, 0.3=tentative.

EXAMPLE (multiple facts):
User: "We use React and deploy on AWS."
Assistant:
<memory_update>
{{"entity":"frontend","relation":"uses","value":"react","category":"system_state","conviction":0.9}}
{{"entity":"cloud","relation":"uses","value":"aws","category":"system_state","conviction":0.9}}
</memory_update>
React and AWS are a solid stack. What features are you building?

EXAMPLE (nothing to store):
User: "Thanks!"
Assistant:
<memory_update>{{"skip": true}}</memory_update>
You're welcome! Let me know if you need anything else.
"""

# Bump when prompt semantics change — surfaced in /health for Docker verification.
PROMPT_VERSION = "v2-mandatory-skip"


def _get_local_model():
    """Lazy-load the sentence-transformers model."""
    global _local_model
    if _local_model is None:
        from sentence_transformers import SentenceTransformer

        _local_model = SentenceTransformer("all-MiniLM-L6-v2")
    return _local_model


def get_local_embedding_sync(text: str) -> list[float]:
    """
    Compute a local embedding synchronously (for background executor threads).

    Args:
        text: Input text.

    Returns:
        384-dimensional embedding vector.

    Raises:
        ValueError: If EMBEDDING_DIM does not match local model output.
    """
    if text in _embedding_cache:
        return _embedding_cache[text]
    model = _get_local_model()
    vector = model.encode(text).tolist()
    if len(vector) != settings.EMBEDDING_DIM:
        raise ValueError(
            f"EMBEDDING_DIM={settings.EMBEDDING_DIM} but local model produces "
            f"{len(vector)}-dim. Fix your .env."
        )
    _embedding_cache[text] = vector
    return vector


async def get_embedding(text: str) -> list[float]:
    """
    Compute embedding via cloud API (optional) or local sentence-transformers.

    Args:
        text: Input text.

    Returns:
        Embedding vector of length EMBEDDING_DIM.
    """
    if text in _embedding_cache:
        return _embedding_cache[text]

    if settings.EMBEDDING_MODEL.startswith("text-embedding"):
        try:
            url = f"{settings.QWEN_BASE_URL}/embeddings"
            headers = {
                "Authorization": f"Bearer {settings.QWEN_API_KEY}",
                "Content-Type": "application/json",
            }
            payload = {"model": settings.EMBEDDING_MODEL, "input": text}
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=payload, headers=headers) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        vector = data["data"][0]["embedding"]
                        if len(vector) != settings.EMBEDDING_DIM:
                            logger.error(
                                "Embedding dim mismatch: got %s, expected %s. "
                                "Falling back to local model.",
                                len(vector),
                                settings.EMBEDDING_DIM,
                            )
                        else:
                            _embedding_cache[text] = vector
                            return vector
                    else:
                        logger.warning("DashScope embedding failed with status %s", resp.status)
        except (aiohttp.ClientError, KeyError, TypeError) as exc:
            logger.warning("DashScope embedding error: %s", exc)

    vector = get_local_embedding_sync(text)
    return vector


def store_belief_embedding_sync(
    belief_id: int,
    entity_source: str,
    relation: str,
    entity_target: str,
    db_path: Path | None = None,
) -> None:
    """
    Store vector embedding for a belief using the local model (sync-safe).

    Args:
        belief_id: semantic_graph row id.
        entity_source: Belief source entity.
        relation: Belief relation.
        entity_target: Belief target value.
        db_path: Optional database path override.
    """
    text = f"{entity_source} {relation} {entity_target}"
    embedding = get_local_embedding_sync(text)
    upsert_vec_embedding(belief_id, embedding, db_path)


def extract_entities_robust(text: str) -> list[str]:
    """
    Extract tech terms and proper nouns from user text.

    Args:
        text: User input.

    Returns:
        Deduplicated lowercase entity list.
    """
    tokens = re.split(r"[^\w]+", text.lower())
    found = {token for token in tokens if token in CORE_TECH_DICTIONARY}
    for match in re.findall(r"\b[A-Z][a-z]{2,}\b", text):
        found.add(match.lower())
    return sorted(found)


def _calculate_ucb_score(
    q_i: float,
    n_i: int,
    total_turns: int,
    c: float | None = None,
) -> float:
    """
    Compute UCB score for a memory candidate.

    Args:
        q_i: Base utility Q_i.
        n_i: Injection count N_i.
        total_turns: Total user turns T.
        c: Exploration constant.

    Returns:
        UCB score.
    """
    exploration = c if c is not None else settings.UCB_EXPLORATION_C
    return q_i + exploration * math.sqrt(math.log(total_turns) / (n_i + 1))


def _confidence_label(node_weight: float) -> str:
    if node_weight >= 0.85:
        return "HIGH"
    if node_weight >= 0.55:
        return "CONFIDENT"
    return "FADING"


def _get_rwr_associations(
    graph_edges: list[tuple[int, int]],
    primary_node_id: int,
    alpha: float | None = None,
    top_k: int = 2,
) -> list[tuple[int, float]]:
    """
    Run personalized PageRank from a primary node.

    Args:
        graph_edges: Directed edges as (source_id, target_id).
        primary_node_id: Origin node for restart.
        alpha: Restart probability.
        top_k: Number of associations to return.

    Returns:
        List of (node_id, score) tuples excluding the primary node.
    """
    alpha_val = alpha if alpha is not None else settings.RWR_ALPHA
    graph = nx.DiGraph()
    graph.add_edges_from(graph_edges)
    if primary_node_id not in graph.nodes():
        return []
    try:
        personalization = {node: 0.0 for node in graph.nodes()}
        personalization[primary_node_id] = 1.0
        scores = nx.pagerank(graph, alpha=alpha_val, personalization=personalization)
        scores.pop(primary_node_id, None)
        return sorted(scores.items(), key=lambda item: item[1], reverse=True)[:top_k]
    except (nx.NetworkXError, ZeroDivisionError) as exc:
        logger.warning("RWR failed: %s", exc)
        return []


def _get_single_entity_hop(
    user_id: str,
    top_entity_source: str,
    exclude_ids: set[int],
    db_path: Path | None = None,
) -> list[int]:
    """
    Find one related belief sharing an entity with the top UCB result.

    Args:
        user_id: User identifier.
        top_entity_source: Entity to match.
        exclude_ids: Belief IDs already selected.
        db_path: Optional database path override.

    Returns:
        List of matching belief IDs (max 1).
    """
    conn = get_db_connection(db_path)
    try:
        rows = conn.execute(
            """
            SELECT id FROM semantic_graph
            WHERE user_id = ? AND node_weight > ?
              AND (entity_source = ? OR entity_target = ?)
            """,
            (user_id, settings.PRUNE_THRESHOLD, top_entity_source, top_entity_source),
        ).fetchall()
        for row in rows:
            belief_id = int(row["id"])
            if belief_id not in exclude_ids:
                return [belief_id]
        return []
    finally:
        conn.close()


def _fetch_candidates_by_vector(
    user_id: str,
    embedding: list[float],
    db_path: Path | None,
    limit: int = 20,
) -> list[sqlite3.Row]:
    """KNN search via sqlite-vec."""
    import sqlite_vec

    conn = get_db_connection(db_path)
    try:
        rows = conn.execute(
            f"""
            SELECT sg.*, v.distance AS vec_distance
            FROM vec_memory v
            JOIN semantic_graph sg ON sg.id = v.id
            WHERE sg.user_id = ? AND sg.node_weight > ?
              AND v.embedding MATCH ?
            ORDER BY v.distance
            LIMIT ?
            """,
            (
                user_id,
                settings.PRUNE_THRESHOLD,
                sqlite_vec.serialize_float32(embedding),
                limit,
            ),
        ).fetchall()
        return rows
    finally:
        conn.close()


def _fetch_candidates_by_keywords(
    user_id: str,
    entities: list[str],
    db_path: Path | None,
    limit: int = 20,
) -> list[sqlite3.Row]:
    """Keyword fallback when vector search is unavailable."""
    if not entities:
        conn = get_db_connection(db_path)
        try:
            return conn.execute(
                """
                SELECT * FROM semantic_graph
                WHERE user_id = ? AND node_weight > ?
                ORDER BY base_utility_q DESC
                LIMIT ?
                """,
                (user_id, settings.PRUNE_THRESHOLD, limit),
            ).fetchall()
        finally:
            conn.close()

    clauses = []
    params: list[object] = [user_id, settings.PRUNE_THRESHOLD]
    for entity in entities:
        clauses.append("(LOWER(entity_source) LIKE ? OR LOWER(entity_target) LIKE ?)")
        pattern = f"%{entity.lower()}%"
        params.extend([pattern, pattern])
    where_entities = " OR ".join(clauses)
    params.append(limit)
    conn = get_db_connection(db_path)
    try:
        return conn.execute(
            f"""
            SELECT * FROM semantic_graph
            WHERE user_id = ? AND node_weight > ?
              AND ({where_entities})
            LIMIT ?
            """,
            params,
        ).fetchall()
    finally:
        conn.close()


def _build_graph_edges(user_id: str, db_path: Path | None) -> list[tuple[int, int]]:
    """Build directed edges between beliefs sharing entities."""
    conn = get_db_connection(db_path)
    try:
        rows = conn.execute(
            """
            SELECT id, entity_source, entity_target FROM semantic_graph
            WHERE user_id = ? AND node_weight > ?
            """,
            (user_id, settings.PRUNE_THRESHOLD),
        ).fetchall()
    finally:
        conn.close()

    entity_to_ids: dict[str, list[int]] = {}
    for row in rows:
        belief_id = int(row["id"])
        for entity in (row["entity_source"], row["entity_target"]):
            key = entity.lower()
            entity_to_ids.setdefault(key, []).append(belief_id)

    edges: set[tuple[int, int]] = set()
    for ids in entity_to_ids.values():
        for i, src in enumerate(ids):
            for tgt in ids[i + 1 :]:
                edges.add((src, tgt))
                edges.add((tgt, src))
    return list(edges)


async def build_optimized_qwen_payload(
    user_id: str,
    session_id: str,
    user_input: str,
    total_turns: int,
    db_path: Path | None = None,
) -> dict:
    """
    Build Qwen API payload with retrieved memory context.

    Args:
        user_id: User identifier.
        session_id: Session identifier.
        user_input: Current user message.
        total_turns: Total episodic turns for UCB T parameter.
        db_path: Optional database path override.

    Returns:
        Dict with keys ``payload`` and ``injected_ids``.
    """
    try:
        embedding = await get_embedding(user_input)
        if VEC_AVAILABLE:
            candidates = _fetch_candidates_by_vector(user_id, embedding, db_path)
        else:
            entities = extract_entities_robust(user_input)
            candidates = _fetch_candidates_by_keywords(user_id, entities, db_path)

        scored: list[tuple[float, sqlite3.Row]] = []
        for row in candidates:
            ucb = _calculate_ucb_score(
                float(row["base_utility_q"]),
                int(row["injection_count"]),
                total_turns,
            )
            scored.append((ucb, row))
        scored.sort(key=lambda item: item[0], reverse=True)

        top_n = min(4, settings.MAX_INJECTED_FACTS - 2)
        selected: list[sqlite3.Row] = [row for _, row in scored[:top_n]]
        selected_ids = {int(row["id"]) for row in selected}

        conn = get_db_connection(db_path)
        try:
            node_count = conn.execute(
                """
                SELECT COUNT(*) AS cnt FROM semantic_graph
                WHERE user_id = ? AND node_weight > ?
                """,
                (user_id, settings.PRUNE_THRESHOLD),
            ).fetchone()["cnt"]
        finally:
            conn.close()

        extra_ids: list[int] = []
        if selected:
            primary_id = int(selected[0]["id"])
            if node_count > settings.RWR_MIN_NODES:
                edges = _build_graph_edges(user_id, db_path)
                for node_id, _score in _get_rwr_associations(edges, primary_id):
                    if node_id not in selected_ids:
                        extra_ids.append(node_id)
                        selected_ids.add(node_id)
                    if len(extra_ids) >= 2:
                        break
            else:
                hop_ids = _get_single_entity_hop(
                    user_id,
                    selected[0]["entity_source"],
                    selected_ids,
                    db_path,
                )
                extra_ids.extend(hop_ids)

        if extra_ids:
            conn = get_db_connection(db_path)
            try:
                placeholders = ",".join("?" for _ in extra_ids)
                extra_rows = conn.execute(
                    f"SELECT * FROM semantic_graph WHERE id IN ({placeholders})",
                    extra_ids,
                ).fetchall()
                selected.extend(extra_rows)
            finally:
                conn.close()

        injected_ids: list[int] = []
        fact_lines: list[str] = []
        for row in selected[: settings.MAX_INJECTED_FACTS]:
            belief_id = int(row["id"])
            injected_ids.append(belief_id)
            ucb = _calculate_ucb_score(
                float(row["base_utility_q"]),
                int(row["injection_count"]),
                total_turns,
            )
            log_memory_event(
                user_id,
                "injected",
                entity_source=row["entity_source"],
                entity_target=row["entity_target"],
                detail={
                    "belief_id": belief_id,
                    "q_i": float(row["base_utility_q"]),
                    "ucb_score": round(ucb, 3),
                    "turn": total_turns,
                },
                db_path=db_path,
            )
            fact_lines.append(
                f"- {row['entity_source']} {row['relation']} {row['entity_target']} "
                f"(Q: {row['base_utility_q']:.2f}, confidence: "
                f"{_confidence_label(float(row['node_weight']))})"
            )

        if injected_ids:
            conn = get_db_connection(db_path)
            try:
                placeholders = ",".join("?" for _ in injected_ids)
                conn.execute(
                    f"""
                    UPDATE semantic_graph
                    SET last_accessed = CURRENT_TIMESTAMP,
                        node_weight = MIN(1.0, node_weight + 0.05)
                    WHERE id IN ({placeholders})
                    """,
                    injected_ids,
                )
                conn.commit()
            finally:
                conn.close()

        conn = get_db_connection(db_path)
        try:
            history = conn.execute(
                """
                SELECT user_prompt, agent_response FROM episodic_logs
                WHERE user_id = ? AND session_id = ?
                ORDER BY timestamp DESC LIMIT 3
                """,
                (user_id, session_id),
            ).fetchall()
        finally:
            conn.close()

        injected_facts = "\n".join(fact_lines) if fact_lines else "(no stored memories yet)"
        system_prompt = SYSTEM_PROMPT_TEMPLATE.format(injected_facts=injected_facts)
        messages: list[dict[str, str]] = [{"role": "system", "content": system_prompt}]
        for turn in reversed(history):
            messages.append({"role": "user", "content": turn["user_prompt"]})
            messages.append({"role": "assistant", "content": turn["agent_response"]})
        messages.append({"role": "user", "content": user_input})

        return {
            "payload": {
                "model": settings.QWEN_MODEL,
                "messages": messages,
                "temperature": 0.2,
                "max_tokens": 1000,
            },
            "injected_ids": injected_ids,
        }
    except (sqlite3.Error, ValueError, aiohttp.ClientError) as exc:
        logger.error("Failed to build Qwen payload: %s", exc)
        return {
            "payload": {
                "model": settings.QWEN_MODEL,
                "messages": [{"role": "user", "content": user_input}],
                "temperature": 0.2,
                "max_tokens": 1000,
            },
            "injected_ids": [],
        }
