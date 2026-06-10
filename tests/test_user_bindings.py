"""Tests for memory.user_bindings."""

from __future__ import annotations

from pathlib import Path

from memory.user_bindings import bind_user, list_bindings_for_user, resolve_user


def test_bind_user_creates_stable_id(initialized_db: Path) -> None:
    result = bind_user("telegram", "12345", "Alice", db_path=initialized_db)
    assert result["user_id"].startswith("oc_telegram_")
    assert result["created"] is True

    again = bind_user("telegram", "12345", "Alice", db_path=initialized_db)
    assert again["user_id"] == result["user_id"]
    assert again["created"] is False


def test_resolve_user(initialized_db: Path) -> None:
    uid = resolve_user("discord", "user-99", db_path=initialized_db)
    assert uid.startswith("oc_discord_")


def test_list_bindings_for_user(initialized_db: Path) -> None:
    bound = bind_user("whatsapp", "+15551234", db_path=initialized_db)
    bindings = list_bindings_for_user(bound["user_id"], db_path=initialized_db)
    assert len(bindings) == 1
    assert bindings[0]["channel"] == "whatsapp"
