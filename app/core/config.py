import os
from dataclasses import dataclass

from dotenv import load_dotenv

load_dotenv(".env")


@dataclass(frozen=True)
class DatabaseConfig:
    url: str


@dataclass(frozen=True)
class AIConfig:
    api_key: str
    base_url: str
    model: str
    timeout_seconds: int = 45


def _required_env(name: str) -> str:
    value = os.getenv(name, "").strip()
    if not value:
        raise RuntimeError(f"{name} is required")
    return value


def _bounded_int_env(name: str, default: int, minimum: int, maximum: int) -> int:
    raw_value = os.getenv(name, str(default))
    try:
        value = int(raw_value)
    except ValueError as exc:
        raise RuntimeError(f"{name} must be an integer") from exc
    if not minimum <= value <= maximum:
        raise RuntimeError(f"{name} must be between {minimum} and {maximum}")
    return value


def get_database_config() -> DatabaseConfig:
    url = _required_env("DATABASE_URL")
    if not url.startswith(("postgresql://", "postgres://")):
        raise RuntimeError("DATABASE_URL must use postgresql:// or postgres://")
    return DatabaseConfig(url=url)


def get_ai_config() -> AIConfig:
    base_url = os.getenv("AI_BASE_URL", "https://api.openai.com/v1").strip().rstrip("/")
    if not base_url.startswith(("http://", "https://")):
        raise RuntimeError("AI_BASE_URL must use http:// or https://")

    model = os.getenv("AI_MODEL", "gpt-4o-mini").strip()
    if not model:
        raise RuntimeError("AI_MODEL is required")

    return AIConfig(
        api_key=_required_env("AI_API_KEY"),
        base_url=base_url,
        model=model,
        timeout_seconds=_bounded_int_env("AI_TIMEOUT_SECONDS", 45, 1, 300),
    )
