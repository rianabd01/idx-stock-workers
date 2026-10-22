from app.core.config import AIConfig
from app.services.news_analyzer import clean_markdown, summarize_article

AI_CONFIG = AIConfig(api_key="ai-key", base_url="http://localhost:9999/v1", model="test-model", timeout_seconds=5)


# --- fakes -------------------------------------------------------------------


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
