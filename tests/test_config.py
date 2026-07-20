"""Tests for config settings."""

from __future__ import annotations

import os
from pathlib import Path

import pytest

from config import Settings, settings


def test_settings_loads_defaults() -> None:
    assert settings.UCB_EXPLORATION_C == 0.3
    assert settings.EMBEDDING_DIM == 384


def test_qwen_cloud_default_uses_devpost_accepted_international_endpoint(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("LLM_BASE_URL", raising=False)
    monkeypatch.delenv("QWEN_BASE_URL", raising=False)

    cfg = Settings()

    expected = "https://dashscope-intl.aliyuncs.com/compatible-mode/v1"
    assert cfg.LLM_BASE_URL == expected
    assert cfg.QWEN_BASE_URL == expected


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


def test_settings_prefers_provider_neutral_llm_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("QWEN_API_KEY", "sk-old")
    monkeypatch.setenv("QWEN_MODEL", "qwen-old")
    monkeypatch.setenv("QWEN_BASE_URL", "https://old.example/v1")
    monkeypatch.setenv("LLM_API_KEY", "sk-new")
    monkeypatch.setenv("LLM_MODEL", "deepseek-chat")
    monkeypatch.setenv("LLM_BASE_URL", "https://api.deepseek.com")

    cfg = Settings()

    assert cfg.LLM_API_KEY == "sk-new"
    assert cfg.LLM_MODEL == "deepseek-chat"
    assert cfg.LLM_BASE_URL == "https://api.deepseek.com"
    assert cfg.QWEN_API_KEY == "sk-old"
