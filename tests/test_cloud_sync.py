"""Tests for storage.cloud_sync."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import oss2

from config import settings
from storage import cloud_sync


def test_sync_to_cloud_no_credentials(tmp_path: Path, monkeypatch) -> None:
    db_file = tmp_path / "memory_state.db"
    db_file.write_bytes(b"data")
    monkeypatch.setattr(cloud_sync, "_get_oss_bucket", lambda: None)
    assert cloud_sync.sync_to_cloud(db_file) is False


def test_sync_to_cloud_no_db_file(tmp_path: Path) -> None:
    missing = tmp_path / "nope.db"
    assert cloud_sync.sync_to_cloud(missing) is False


def test_sync_to_cloud_success(tmp_path: Path, monkeypatch) -> None:
    db_file = tmp_path / "memory_state.db"
    db_file.write_bytes(b"sqlite-data")
    mock_bucket = MagicMock()
    monkeypatch.setattr(cloud_sync, "_get_oss_bucket", lambda: mock_bucket)
    assert cloud_sync.sync_to_cloud(db_file) is True
    mock_bucket.put_object_from_file.assert_called_once()


def test_sync_to_cloud_oss_error(tmp_path: Path, monkeypatch) -> None:
    db_file = tmp_path / "memory_state.db"
    db_file.write_bytes(b"sqlite-data")
    mock_bucket = MagicMock()
    mock_bucket.put_object_from_file.side_effect = Exception("oss upload failed")
    monkeypatch.setattr(cloud_sync, "_get_oss_bucket", lambda: mock_bucket)
    assert cloud_sync.sync_to_cloud(db_file) is False


def test_get_oss_bucket_missing_vars(monkeypatch) -> None:
    monkeypatch.setattr(settings, "ALIBABA_CLOUD_ACCESS_KEY_ID", "")
    assert cloud_sync._get_oss_bucket() is None
