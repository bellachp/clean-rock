import os
from pathlib import Path

import pytest


@pytest.fixture
def tmp_settings(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    """Isolated config + filesystem for each test."""
    db_path = tmp_path / "scores.db"
    site_dir = tmp_path / "site"
    web_dir = Path(__file__).resolve().parents[1] / "web"

    monkeypatch.setenv("ADMIN_PASSWORD", "test-pw")
    monkeypatch.setenv("SESSION_SECRET", "test-secret-32-chars-long-xxxxxxxxx")
    monkeypatch.setenv("DATABASE_PATH", str(db_path))
    monkeypatch.setenv("SITE_DIR", str(site_dir))
    monkeypatch.setenv("WEB_DIR", str(web_dir))

    from clean_rock import config
    config.get_settings.cache_clear()
    settings = config.get_settings()
    yield settings
    config.get_settings.cache_clear()
