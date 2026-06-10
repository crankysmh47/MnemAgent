"""Tests for config settings."""

from __future__ import annotations

import os
from pathlib import Path

import pytest

from config import Settings, settings


def test_settings_loads_defaults() -> None:
    assert settings.UCB_EXPLORATION_C == 0.3
    assert settings.EMBEDDING_DIM == 384


def test_settings_masks_secrets() -> None:
    text = repr(settings)
    assert "sk-" not in text or "***masked***" in text


def test_settings_db_path_is_pathlib() -> None:
    assert isinstance(settings.DB_PATH, Path)


def test_settings_validates_api_key(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("QWEN_API_KEY", "sk-xxxxxxxxxxxx")
    cfg = Settings()
    with pytest.raises(ValueError):
        cfg.validate_qwen_api_key()
