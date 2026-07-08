"""Tests for cue-triggered prospective memory."""

from __future__ import annotations

from pathlib import Path

from memory.dreaming import consolidate_and_prune_memory
from memory.prospective import fetch_due_prospective_memories
from storage.db_manager import get_db_connection


def test_consolidate_stores_prospective_memory(initialized_db: Path, monkeypatch) -> None:
    monkeypatch.setattr("memory.dreaming.store_belief_embedding_sync", lambda *_args, **_kwargs: None)
    stored = consolidate_and_prune_memory(
        "u",
        {
            "entity": "when_asked_about_deployment",
            "relation": "remind",
            "value": "check the OSS snapshot",
            "category": "system_state",
            "conviction": 1.0,
        },
        initialized_db,
    )
    assert stored is True

    conn = get_db_connection(initialized_db)
    try:
        row = conn.execute(
            "SELECT cue, action FROM prospective_memories WHERE user_id = ?",
            ("u",),
        ).fetchone()
        assert row["cue"] == "deployment"
        assert row["action"] == "check the OSS snapshot"
    finally:
        conn.close()


def test_prospective_memory_fires_only_on_cue(initialized_db: Path, monkeypatch) -> None:
    monkeypatch.setattr("memory.dreaming.store_belief_embedding_sync", lambda *_args, **_kwargs: None)
    consolidate_and_prune_memory(
        "u",
        {
            "entity": "when_asked_about_pricing",
            "relation": "remind",
            "value": "mention the startup discount",
            "category": "system_state",
            "conviction": 1.0,
        },
        initialized_db,
    )

    off_cue = fetch_due_prospective_memories(
        "u",
        "Let's discuss onboarding today.",
        db_path=initialized_db,
    )
    on_cue = fetch_due_prospective_memories(
        "u",
        "Can we review pricing before launch?",
        db_path=initialized_db,
    )

    assert off_cue == []
    assert on_cue[0]["cue"] == "pricing"
    assert on_cue[0]["action"] == "mention the startup discount"


def test_model_shaped_reminder_becomes_prospective_memory(initialized_db: Path, monkeypatch) -> None:
    monkeypatch.setattr("memory.dreaming.store_belief_embedding_sync", lambda *_args, **_kwargs: None)
    consolidate_and_prune_memory(
        "u",
        {
            "entity": "deployment",
            "relation": "reminder",
            "value": "check the OSS snapshot",
            "category": "preference",
            "conviction": 1.0,
        },
        initialized_db,
    )

    due = fetch_due_prospective_memories(
        "u",
        "Let's discuss deployment.",
        db_path=initialized_db,
    )

    assert due[0]["cue"] == "deployment"
    assert due[0]["action"] == "check the OSS snapshot"


def test_reminder_action_relation_uses_entity_cue(initialized_db: Path, monkeypatch) -> None:
    monkeypatch.setattr("memory.dreaming.store_belief_embedding_sync", lambda *_args, **_kwargs: None)
    consolidate_and_prune_memory(
        "u",
        {
            "entity": "backup_verification",
            "relation": "reminder_action",
            "value": "verify_OSS_snapshot",
            "category": "preference",
            "conviction": 1.0,
        },
        initialized_db,
    )

    due = fetch_due_prospective_memories(
        "u",
        "What should I remember about backups?",
        db_path=initialized_db,
    )

    assert due[0]["cue"] == "backup"
    assert due[0]["action"] == "verify OSS snapshot"


def test_action_relation_with_reminder_entity_becomes_prospective(initialized_db: Path, monkeypatch) -> None:
    monkeypatch.setattr("memory.dreaming.store_belief_embedding_sync", lambda *_args, **_kwargs: None)
    consolidate_and_prune_memory(
        "u",
        {
            "entity": "backup_reminder",
            "relation": "action",
            "value": "verify_OSS_snapshot",
            "category": "persona",
            "conviction": 1.0,
        },
        initialized_db,
    )

    due = fetch_due_prospective_memories(
        "u",
        "Can we talk about backups?",
        db_path=initialized_db,
    )

    assert due[0]["cue"] == "backup"
    assert due[0]["action"] == "verify OSS snapshot"
