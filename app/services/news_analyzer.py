"""Analyzer service: ringkas artikel dengan AI model (fetch ada di article_reader)."""

import json
import re

from curl_cffi import requests as curl_requests

from app.core.config import AIConfig

# --- AI summarization -----------------------------------------------------

SYSTEM_PROMPT = """Kamu meringkas berita pasar modal Indonesia untuk investor.
Tulis ringkasan 1-2 kalimat bahasa Indonesia yang padat: inti peristiwa, angka/pembanding penting, dan siapa yang terdampak jika disebut. Jangan mulai dengan nama media atau kota. Tanpa komentar tambahan, hanya ringkasannya."""

PROMPT_CONTENT_MAX_CHARS = 4000


def clean_markdown(text: str) -> str:
    """Bersihkan markdown (gambar/link/format) jadi teks polos."""
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
