import pytest

from app.core.config import AIConfig, JinaConfig
from app.services.news_analyzer import (
    MAX_CONTENT_CHARS,
    clean_markdown,
    fetch_article_content,
    parse_jina_response,
    summarize_article,
)

JINA_URL = "https://r.jina.ai/"
JINA_CONFIG = JinaConfig(api_key="test-key", base_url="https://r.jina.ai", timeout_seconds=10)
AI_CONFIG = AIConfig(api_key="ai-key", base_url="http://localhost:9999/v1", model="test-model", timeout_seconds=5)

SAMPLE_JINA_RESPONSE = {
    "code": 200,
    "status": 20000,
    "data": {
        "title": "Judul Artikel",
        "content": "Isi artikel lengkap.\n\nParagraf kedua.",
        "publishedTime": "2026-08-22T20:34:13+0000",
        "description": "Deskripsi singkat",
    },
}


# --- parse_jina_response ----------------------------------------------------


def test_parse_jina_response_extracts_key_fields():
    result = parse_jina_response(SAMPLE_JINA_RESPONSE)
    assert result == {
        "title": "Judul Artikel",
        "content": "Isi artikel lengkap.\n\nParagraf kedua.",
        "published_time": "2026-08-22T20:34:13+0000",
        "description": "Deskripsi singkat",
    }


def test_parse_jina_response_returns_none_when_content_empty():
    payload = {"data": {"title": "x", "content": ""}}
    assert parse_jina_response(payload) is None
    assert parse_jina_response({}) is None
    assert parse_jina_response({"data": "bukan-dict"}) is None


def test_parse_jina_response_truncates_long_content():
    payload = {"data": {"content": "a" * (MAX_CONTENT_CHARS + 500)}}
    result = parse_jina_response(payload, max_chars=100)
    assert len(result["content"]) == 100


# --- fetch_article_content ---------------------------------------------------


class FakeResponse:
    def __init__(self, json_data=None, status_code=200, text=""):
        self._json = json_data
        self.status_code = status_code
        self.text = text

    def raise_for_status(self):
        if self.status_code >= 400:
            raise Exception(f"HTTP {self.status_code}")

    def json(self):
        return self._json


class FakeCurlRequests:
    """Pengganti curl_cffi.requests untuk pengujian."""

    def __init__(self, response):
        self.response = response
        self.calls = []

    def post(self, url, json=None, headers=None, timeout=None):
        self.calls.append({"url": url, "json": json, "headers": headers})
        return self.response


def test_fetch_sends_target_selector_and_auth(monkeypatch):
    fake = FakeCurlRequests(FakeResponse(SAMPLE_JINA_RESPONSE))
    monkeypatch.setattr("app.services.news_analyzer.curl_requests", fake)

    result = fetch_article_content(
        JINA_CONFIG,
        "https://example.com/a",
        target_selector=".group",
    )

    assert result["title"] == "Judul Artikel"
    req = fake.calls[0]
    assert req["url"] == JINA_URL
    assert req["json"] == {"url": "https://example.com/a", "targetSelector": ".group"}
    assert req["headers"]["Authorization"] == "Bearer test-key"


def test_fetch_without_selector_omits_field(monkeypatch):
    fake = FakeCurlRequests(FakeResponse(SAMPLE_JINA_RESPONSE))
    monkeypatch.setattr("app.services.news_analyzer.curl_requests", fake)

    fetch_article_content(JINA_CONFIG, "https://example.com/a")

    assert fake.calls[0]["json"] == {"url": "https://example.com/a"}


def test_fetch_returns_none_on_http_error(monkeypatch):
    fake = FakeCurlRequests(FakeResponse({}, status_code=422))
    monkeypatch.setattr("app.services.news_analyzer.curl_requests", fake)

    assert fetch_article_content(JINA_CONFIG, "https://example.com/a") is None


# --- summarize_article --------------------------------------------------------


def test_clean_markdown_strips_formatting():
    raw = "# Judul\n![alt](img.png) [teks link](https://x.y) **bold**"
    cleaned = clean_markdown(raw)
    assert "#" not in cleaned and "[" not in cleaned and "*" not in cleaned
    assert "teks link" in cleaned


AI_CHAT_COMPLETIONS_RESPONSE = (
    '{"choices": [{"message": {"role": "assistant", "content": "{\\"summary\\": \\"ok\\"}"}}]}'
)


def test_summarize_article_posts_chat_completions(monkeypatch):
    fake = FakeCurlRequests(
        FakeResponse(text='{"choices": [{"message": {"content": "Ringkasan padat."}}]}')
    )
    monkeypatch.setattr("app.services.news_analyzer.curl_requests", fake)

    summary = summarize_article(AI_CONFIG, "Judul", "Isi berita.")

    assert summary == "Ringkasan padat."
    req = fake.calls[0]
    assert req["url"] == "http://localhost:9999/v1/chat/completions"
    assert req["json"]["model"] == "test-model"
    assert req["headers"]["Authorization"] == "Bearer ai-key"


def test_summarize_tolerates_data_done_suffix(monkeypatch):
    text = '{"choices": [{"message": {"content": "Ringkasan."}}]}\ndata: [DONE]'
    fake = FakeCurlRequests(FakeResponse(text=text))
    monkeypatch.setattr("app.services.news_analyzer.curl_requests", fake)

    assert summarize_article(AI_CONFIG, "Judul", "Isi.") == "Ringkasan."


def test_summarize_falls_back_to_reasoning_details(monkeypatch):
    text = '{"choices": [{"message": {"content": "", "reasoning_details": [{"text": "Dari reasoning."}]}}]}'
    fake = FakeCurlRequests(FakeResponse(text=text))
    monkeypatch.setattr("app.services.news_analyzer.curl_requests", fake)

    assert summarize_article(AI_CONFIG, "Judul", "Isi.") == "Dari reasoning."
