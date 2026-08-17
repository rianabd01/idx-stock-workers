from dataclasses import FrozenInstanceError

import pytest

from app.core.config import get_ai_config, get_database_config
from app.core.db import check_required_tables


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


class FakeCursor:
    def __init__(self, rows):
        self.rows = rows
        self.executed = None

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return None

    def execute(self, query, params):
        self.executed = (query, params)

    def fetchall(self):
        return self.rows


class FakeConnection:
    def __init__(self, rows):
        self.cursor_instance = FakeCursor(rows)

    def cursor(self):
        return self.cursor_instance


def test_schema_preflight_success_is_read_only():
    conn = FakeConnection([{"table_name": "news_articles", "exists": True}])
    check_required_tables(conn, "impact", {"news_articles"})
    assert "to_regclass" in conn.cursor_instance.executed[0]
    assert conn.cursor_instance.executed[1] == (["news_articles"],)


def test_schema_preflight_lists_missing_tables_and_migration_command():
    conn = FakeConnection(
        [
            {"table_name": "network_nodes", "exists": False},
            {"table_name": "news_articles", "exists": True},
        ]
    )
    with pytest.raises(RuntimeError, match=r"network_nodes.*uv run alembic upgrade head.*idx-stock-backend"):
        check_required_tables(conn, "news impact", {"network_nodes", "news_articles"})
