from datetime import datetime, timezone
from types import SimpleNamespace

from app.services.news_collector import _article_from_entry, _content_hash, _entry_url


def test_entry_url_accepts_http_and_rejects_other_schemes():
    assert _entry_url({"link": "https://example.com/news?id=1"}) == "https://example.com/news?id=1"
    assert _entry_url({"link": "javascript:alert(1)"}) is None
    assert _entry_url({}) is None


def test_content_hash_is_stable_and_sensitive_to_content():
    published = datetime(2026, 8, 17, tzinfo=timezone.utc)
    assert _content_hash("Title", "https://example.com", published) == _content_hash(
        "Title", "https://example.com", published
    )
    assert _content_hash("Other", "https://example.com", published) != _content_hash(
        "Title", "https://example.com", published
    )


def test_article_transform_normalizes_fields(monkeypatch):
    published = datetime(2026, 8, 17, tzinfo=timezone.utc)
    monkeypatch.setattr("app.services.news_collector.parsed_datetime", lambda value: published)
    entry = {
        "id": "item-1",
        "link": "https://example.com/news",
        "title": "  Judul berita  ",
        "description": "  Ringkasan  ",
        "published_parsed": SimpleNamespace(),
        "published": "Mon, 17 Aug 2026 00:00:00 GMT",
    }

    article = _article_from_entry(7, entry)

    assert article["source_id"] == 7
    assert article["title"] == "Judul berita"
    assert article["summary"] == "Ringkasan"
    assert article["published_at"] == published
    assert article["content_hash"] == _content_hash(article["title"], article["url"], published)
    assert '"id": "item-1"' in article["raw_payload"]
