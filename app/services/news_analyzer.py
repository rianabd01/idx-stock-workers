"""Analyzer service: fetch artikel via Jina Reader + ringkas dengan AI model."""

import json
import re
from typing import Any

from curl_cffi import requests as curl_requests

from app.core.config import AIConfig, JinaConfig

# --- Jina Reader ---------------------------------------------------------

MAX_CONTENT_CHARS = 20_000


def _extract_payload(data: dict[str, Any], max_chars: int = MAX_CONTENT_CHARS) -> dict[str, Any] | None:
    content = (data.get("content") or "").strip()
    if not content:
        return None
    return {
        "title": (data.get("title") or "").strip() or None,
        "content": content[:max_chars],
        "published_time": (data.get("publishedTime") or "").strip() or None,
        "description": (data.get("description") or "").strip() or None,
    }


def parse_jina_response(payload: dict[str, Any], max_chars: int = MAX_CONTENT_CHARS) -> dict[str, Any] | None:
    """Extract title/content/publishedTime from a Jina Reader JSON response."""
    data = payload.get("data")
    if not isinstance(data, dict):
        return None
    return _extract_payload(data, max_chars=max_chars)


def fetch_article_content(
    config: JinaConfig,
    url: str,
    target_selector: str | None = None,
) -> dict[str, Any] | None:
    """Fetch article via Jina Reader and return {title, content, published_time}.

    Returns None on failure. target_selector narrows extraction to a CSS block.
    """
    headers = {
        "Authorization": f"Bearer {config.api_key}",
        "Content-Type": "application/json",
        "Accept": "application/json",
    }
    body: dict[str, Any] = {"url": url}
    if target_selector:
        body["targetSelector"] = target_selector

    try:
        response = curl_requests.post(
            f"{config.base_url.rstrip('/')}/",
            json=body,
            headers=headers,
            timeout=config.timeout_seconds,
        )
        response.raise_for_status()
        return parse_jina_response(response.json())
    except Exception:
        return None


# --- AI summarization -----------------------------------------------------

SYSTEM_PROMPT = """Kamu meringkas berita pasar modal Indonesia untuk investor.
Tulis ringkasan 1-2 kalimat bahasa Indonesia yang padat: inti peristiwa, angka/pembanding penting, dan siapa yang terdampak jika disebut. Jangan mulai dengan nama media atau kota. Tanpa komentar tambahan, hanya ringkasannya."""

PROMPT_CONTENT_MAX_CHARS = 4000


def clean_markdown(text: str) -> str:
    """Bersihkan markdown Jina (gambar/link/format) jadi teks polos."""
    text = re.sub(r"!\[[^\]]*\]\([^)]*\)", " ", text)  # gambar
    text = re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", text)  # link → teksnya
    text = re.sub(r"[#>*_`]+", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def _parse_response_json(text: str) -> dict:
    """Provider kadang menambahkan 'data: [DONE]' setelah objek JSON."""
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        decoder = json.JSONDecoder()
        for match in re.finditer(r"\{", text):
            try:
                parsed, _ = decoder.raw_decode(text[match.start() :])
                if isinstance(parsed, dict):
                    return parsed
            except json.JSONDecodeError:
                continue
        raise


def _message_content(raw: dict) -> str:
    """Ekstrak teks jawaban; beberapa provider menaruhnya di reasoning_details."""
    message = raw["choices"][0]["message"]
    if isinstance(message.get("content"), str) and message["content"].strip():
        return message["content"]
    details = message.get("reasoning_details") or []
    for part in details:
        text = part.get("text") or part.get("summary") or ""
        if isinstance(text, str) and text.strip():
            return text
    return (message.get("reasoning") or "").strip()


def summarize_article(config: AIConfig, title: str, content: str) -> str:
    payload = {
        "model": config.model,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {
                "role": "user",
                "content": f"Judul: {title}\n\nIsi:\n{clean_markdown(content)[:PROMPT_CONTENT_MAX_CHARS]}",
            },
        ],
        "temperature": 0,
    }
    headers = {"Authorization": f"Bearer {config.api_key}", "Content-Type": "application/json"}
    response = curl_requests.post(
        f"{config.base_url}/chat/completions",
        json=payload,
        headers=headers,
        timeout=config.timeout_seconds,
    )
    response.raise_for_status()
    return _message_content(_parse_response_json(response.text)).strip()
