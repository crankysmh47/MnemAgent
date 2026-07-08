"""Centralized configuration — reads .env and exposes typed settings."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

from dotenv import load_dotenv

_SRC_DIR = Path(__file__).resolve().parent
for _env_candidate in (
    _SRC_DIR.parents[2] / ".env" if len(_SRC_DIR.parents) > 2 else None,
    _SRC_DIR.parent / ".env",
    _SRC_DIR / ".env",
    Path.cwd() / ".env",
):
    if _env_candidate is not None and _env_candidate.is_file():
        load_dotenv(_env_candidate)
        break
else:
    load_dotenv()

_PLACEHOLDER_API_KEY = "sk-xxxxxxxxxxxx"
_PLACEHOLDER_OSS_ID = "xxxxxxxxxxxx"
_PLACEHOLDER_OSS_SECRET = "xxxxxxxxxxxx"


def _env_str(key: str, default: str) -> str:
    return os.getenv(key, default)


def _env_float(key: str, default: float) -> float:
    return float(os.getenv(key, str(default)))


def _env_int(key: str, default: int) -> int:
    return int(os.getenv(key, str(default)))


@dataclass
class Settings:
    """Application settings loaded from environment variables."""

    LLM_PROVIDER: str = field(default_factory=lambda: _env_str("LLM_PROVIDER", "openai_compatible"))
    LLM_API_KEY: str = field(
        default_factory=lambda: _env_str("LLM_API_KEY", _env_str("QWEN_API_KEY", _PLACEHOLDER_API_KEY))
    )
    LLM_MODEL: str = field(default_factory=lambda: _env_str("LLM_MODEL", _env_str("QWEN_MODEL", "qwen-plus")))
    LLM_BASE_URL: str = field(
        default_factory=lambda: _env_str(
            "LLM_BASE_URL",
            _env_str("QWEN_BASE_URL", "https://dashscope.aliyuncs.com/compatible-mode/v1"),
        )
    )
    ANTHROPIC_API_KEY: str = field(
        default_factory=lambda: _env_str("ANTHROPIC_API_KEY", _env_str("LLM_API_KEY", _PLACEHOLDER_API_KEY))
    )
    ANTHROPIC_BASE_URL: str = field(
        default_factory=lambda: _env_str("ANTHROPIC_BASE_URL", "https://api.anthropic.com")
    )
    ANTHROPIC_VERSION: str = field(default_factory=lambda: _env_str("ANTHROPIC_VERSION", "2023-06-01"))

    # Backward-compatible aliases used by older scripts and embedding code.
    QWEN_API_KEY: str = field(default_factory=lambda: _env_str("QWEN_API_KEY", _env_str("LLM_API_KEY", _PLACEHOLDER_API_KEY)))
    QWEN_MODEL: str = field(default_factory=lambda: _env_str("QWEN_MODEL", _env_str("LLM_MODEL", "qwen-plus")))
    QWEN_BASE_URL: str = field(
        default_factory=lambda: _env_str(
            "QWEN_BASE_URL",
            _env_str("LLM_BASE_URL", "https://dashscope.aliyuncs.com/compatible-mode/v1"),
        )
    )
    ALIBABA_CLOUD_ACCESS_KEY_ID: str = field(
        default_factory=lambda: _env_str("ALIBABA_CLOUD_ACCESS_KEY_ID", _PLACEHOLDER_OSS_ID)
    )
    ALIBABA_CLOUD_ACCESS_KEY_SECRET: str = field(
        default_factory=lambda: _env_str("ALIBABA_CLOUD_ACCESS_KEY_SECRET", _PLACEHOLDER_OSS_SECRET)
    )
    ALIBABA_CLOUD_OSS_BUCKET: str = field(
        default_factory=lambda: _env_str("ALIBABA_CLOUD_OSS_BUCKET", "mnemos-backups")
    )
    ALIBABA_CLOUD_OSS_ENDPOINT: str = field(
        default_factory=lambda: _env_str(
            "ALIBABA_CLOUD_OSS_ENDPOINT",
            "https://oss-ap-southeast-1.aliyuncs.com",
        )
    )
    EMBEDDING_MODEL: str = field(
        default_factory=lambda: _env_str("EMBEDDING_MODEL", "all-MiniLM-L6-v2")
    )
    EMBEDDING_DIM: int = field(default_factory=lambda: _env_int("EMBEDDING_DIM", 384))
    UCB_EXPLORATION_C: float = field(default_factory=lambda: _env_float("UCB_EXPLORATION_C", 0.3))
    RWR_ALPHA: float = field(default_factory=lambda: _env_float("RWR_ALPHA", 0.85))
    RWR_MIN_NODES: int = field(default_factory=lambda: _env_int("RWR_MIN_NODES", 15))
    DECAY_RATE: float = field(default_factory=lambda: _env_float("DECAY_RATE", 0.85))
    PRUNE_THRESHOLD: float = field(default_factory=lambda: _env_float("PRUNE_THRESHOLD", 0.1))
    MAX_INJECTED_FACTS: int = field(default_factory=lambda: _env_int("MAX_INJECTED_FACTS", 6))
    SEMANTIC_SIMILARITY_FLOOR: float = field(
        default_factory=lambda: _env_float("SEMANTIC_SIMILARITY_FLOOR", 0.3)
    )
    CHAT_MAX_TOKENS: int = field(default_factory=lambda: _env_int("CHAT_MAX_TOKENS", 2000))
    EXTRACTION_MODEL: str = field(default_factory=lambda: _env_str("EXTRACTION_MODEL", ""))
    ENABLE_DREAMING_EXTRACTION: bool = field(
        default_factory=lambda: _env_str("ENABLE_DREAMING_EXTRACTION", "true").lower()
        in ("1", "true", "yes")
    )
    AWAIT_DREAMING: bool = field(
        default_factory=lambda: _env_str("AWAIT_DREAMING", "true").lower()
        in ("1", "true", "yes")
    )
    EXTRACTION_MIN_CONVICTION: float = field(
        default_factory=lambda: _env_float("EXTRACTION_MIN_CONVICTION", 0.4)
    )
    HOST: str = field(default_factory=lambda: _env_str("HOST", "0.0.0.0"))
    PORT: int = field(default_factory=lambda: _env_int("PORT", 8000))
    LOG_LEVEL: str = field(default_factory=lambda: _env_str("LOG_LEVEL", "INFO"))
    DB_PATH: Path = field(
        default_factory=lambda: Path(
            _env_str("DB_PATH", str(Path(__file__).parent / "data" / "memory_state.db"))
        )
    )

    def validate_qwen_api_key(self) -> None:
        """
        Ensure the configured LLM API key is available for live usage.

        Raises:
            ValueError: If the API key is missing or still a placeholder.
        """
        api_key = self.ANTHROPIC_API_KEY if self.LLM_PROVIDER.lower() == "anthropic" else self.LLM_API_KEY
        if not api_key or api_key == _PLACEHOLDER_API_KEY:
            raise ValueError(
                "LLM_API_KEY/ANTHROPIC_API_KEY is not configured. Copy config/env.template to .env and set a real key."
            )

    def __repr__(self) -> str:
        return (
            f"Settings(LLM_PROVIDER={self.LLM_PROVIDER!r}, "
            f"LLM_MODEL={self.LLM_MODEL!r}, "
            f"EMBEDDING_MODEL={self.EMBEDDING_MODEL!r}, "
            f"EMBEDDING_DIM={self.EMBEDDING_DIM}, "
            f"DB_PATH={self.DB_PATH!r}, "
            f"LLM_API_KEY=***masked***)"
        )


settings = Settings()
