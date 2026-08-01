import os
from dataclasses import dataclass

from dotenv import load_dotenv

load_dotenv(".env")


@dataclass(frozen=True)
class AIConfig:
    api_key: str
    base_url: str
    model: str
    timeout_seconds: int = 45


def get_ai_config() -> AIConfig:
    api_key = os.getenv("AI_API_KEY") or os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("AI_API_KEY or OPENAI_API_KEY is required")

    return AIConfig(
        api_key=api_key,
        base_url=os.getenv("AI_BASE_URL", "https://api.openai.com/v1").rstrip("/"),
        model=os.getenv("AI_MODEL", "gpt-4o-mini"),
        timeout_seconds=int(os.getenv("AI_TIMEOUT_SECONDS", "45")),
    )
