"""Tests for entity dictionary qualification."""

from __future__ import annotations

from memory.entity_lexicon import normalize_entity_dict_term, terms_for_entity_dict


def test_normalize_rejects_generic_slots() -> None:
    assert normalize_entity_dict_term("user") is None
    assert normalize_entity_dict_term("preference") is None


def test_normalize_accepts_tech_and_backend() -> None:
    assert normalize_entity_dict_term("prisma") == "prisma"
    assert normalize_entity_dict_term("backend") == "backend"
    assert normalize_entity_dict_term("python") == "python"


def test_normalize_rejects_multi_word_values() -> None:
    assert normalize_entity_dict_term("April 1") is None
    assert normalize_entity_dict_term("FAST student") is None


def test_terms_for_entity_dict_deduplicates() -> None:
    terms = terms_for_entity_dict("backend", "prisma")
    assert terms == ["backend", "prisma"]
