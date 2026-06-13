"""Tests for memory.response_grounding."""

from __future__ import annotations

from memory.response_grounding import (
    ground_response_with_injection,
    is_compound_probe,
    strip_suppressed_mentions,
)


def test_is_compound_probe_detects_stack_summary() -> None:
    assert is_compound_probe("Summarize our full backend stack for a new engineer.")
    assert is_compound_probe("What language and database should the API service use?")


def test_is_compound_probe_rejects_simple_chat() -> None:
    assert not is_compound_probe("Thanks, that helps!")


def test_strip_suppressed_mentions_removes_stale_value() -> None:
    text = "We switched from Express to Fastify for all routes."
    cleaned = strip_suppressed_mentions(text, ["Express"])
    assert "express" not in cleaned.lower()
    assert "fastify" in cleaned.lower()


def test_ground_response_prepends_missing_facts_on_compound_probe() -> None:
    response = "We deploy on AWS with FastAPI."
    grounded = ground_response_with_injection(
        response,
        "Summarize our full backend stack for a new engineer.",
        ["Python", "PostgreSQL", "FastAPI", "AWS"],
        suppressed=[],
    )
    assert "python" in grounded.lower()
    assert "postgresql" in grounded.lower()


def test_ground_response_strips_rejected_salience_values() -> None:
    response = "You could use Vue or TypeScript for the dashboard."
    grounded = ground_response_with_injection(
        response,
        "What frontend language should I use?",
        ["TypeScript"],
        rejected=["Vue"],
    )
    assert "vue" not in grounded.lower()
    assert "typescript" in grounded.lower()


def test_record_hedged_teach_rejections_logs_vue(tmp_path, monkeypatch) -> None:
    from memory.response_grounding import fetch_salience_rejected_values, record_hedged_teach_rejections
    from storage.db_manager import initialize_database

    db_path = tmp_path / "test.db"
    monkeypatch.setenv("DB_PATH", str(db_path))
    initialize_database(db_path)

    record_hedged_teach_rejections(
        "u1",
        "Maybe we could try Vue for the dashboard someday.",
        db_path,
    )
    rejected = fetch_salience_rejected_values("u1", db_path)
    assert any("vue" in v.lower() for v in rejected)
