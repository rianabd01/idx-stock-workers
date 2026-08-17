from dataclasses import FrozenInstanceError

import pytest

from app.core.config import get_ai_config, get_database_config


def test_database_config_validation_and_immutability(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "postgresql://localhost/stocks")
    config = get_database_config()
    assert config.url == "postgresql://localhost/stocks"
    with pytest.raises(FrozenInstanceError):
        config.url = "postgresql://other/db"

    monkeypatch.setenv("DATABASE_URL", "sqlite:///stocks.db")
    with pytest.raises(RuntimeError, match="postgresql"):
        get_database_config()


def test_ai_config_bounds(monkeypatch):
    monkeypatch.setenv("AI_API_KEY", "secret")
    monkeypatch.setenv("AI_BASE_URL", "https://ai.example/v1/")
    monkeypatch.setenv("AI_MODEL", "model")
    monkeypatch.setenv("AI_TIMEOUT_SECONDS", "301")
    with pytest.raises(RuntimeError, match="between 1 and 300"):
        get_ai_config()

    monkeypatch.setenv("AI_TIMEOUT_SECONDS", "30")
    config = get_ai_config()
    assert config.base_url == "https://ai.example/v1"
    assert config.timeout_seconds == 30
