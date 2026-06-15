"""Alibaba Cloud OSS backup for memory_state.db snapshots."""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import TYPE_CHECKING, Any

from config import settings

if TYPE_CHECKING:
    import oss2

logger = logging.getLogger(__name__)

_PLACEHOLDER_OSS_ID = "xxxxxxxxxxxx"
_PLACEHOLDER_OSS_SECRET = "xxxxxxxxxxxx"


def _import_oss2() -> Any | None:
    try:
        import oss2 as oss2_module
    except ImportError:
        logger.debug("oss2 not installed; cloud sync unavailable")
        return None
    return oss2_module


def _get_oss_bucket() -> Any | None:
    """
    Create an OSS bucket client when credentials are configured.

    Returns:
        oss2.Bucket instance or None if credentials are missing/invalid.
    """
    oss2 = _import_oss2()
    if oss2 is None:
        return None

    key_id = settings.ALIBABA_CLOUD_ACCESS_KEY_ID
    key_secret = settings.ALIBABA_CLOUD_ACCESS_KEY_SECRET
    if (
        not key_id
        or not key_secret
        or key_id == _PLACEHOLDER_OSS_ID
        or key_secret == _PLACEHOLDER_OSS_SECRET
    ):
        logger.warning("OSS credentials not configured; cloud sync skipped")
        return None
    try:
        auth = oss2.Auth(key_id, key_secret)
        return oss2.Bucket(auth, settings.ALIBABA_CLOUD_OSS_ENDPOINT, settings.ALIBABA_CLOUD_OSS_BUCKET)
    except Exception as exc:
        logger.error("Failed to create OSS bucket client: %s", exc)
        return None


def sync_to_cloud(db_path: Path | None = None) -> bool:
    """
    Upload a SQLite database snapshot to Alibaba Cloud OSS.

    Args:
        db_path: Path to memory_state.db; defaults to settings.DB_PATH.

    Returns:
        True on successful upload, False otherwise.
    """
    path = db_path or settings.DB_PATH
    if not path.exists():
        logger.error("Database file not found at %s", path)
        return False

    bucket = _get_oss_bucket()
    if bucket is None:
        return False

    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    remote_key = f"agent_runtime/backups/memory_state_{timestamp}.db"
    try:
        bucket.put_object_from_file(remote_key, str(path))
        logger.info("Uploaded database snapshot to OSS: %s", remote_key)
        return True
    except Exception as exc:
        logger.error("OSS upload failed: %s", exc)
        return False
