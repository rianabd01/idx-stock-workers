from datetime import datetime, timezone

from app.services.news_collector import _content_hash, _sitemap_article


def test_content_hash_is_stable_and_sensitive_to_content():
    published = datetime(2026, 8, 17, tzinfo=timezone.utc)
    assert _content_hash("Title", "https://example.com", published) == _content_hash(
        "Title", "https://example.com", published
    )
    assert _content_hash("Other", "https://example.com", published) != _content_hash(
        "Title", "https://example.com", published
    )


def test_sitemap_article_transform_normalizes_fields():
    article = _sitemap_article(
        7,
        {
            "url": "https://example.com/news",
            "title": "Judul berita",
            "publication_date": "2026-08-17T00:00:00+00:00",
        },
    )

    assert article["source_id"] == 7
    assert article["title"] == "Judul berita"
    assert article["summary"] is None
    assert article["published_at"] == datetime(2026, 8, 17, tzinfo=timezone.utc)
    assert article["content_hash"] == _content_hash(
        article["title"], article["url"], article["published_at"]
    )
    assert '"publication_date"' in article["raw_payload"]


def test_sitemap_article_requires_url_and_falls_back_title_to_url():
    assert _sitemap_article(7, {"title": "no url"}) is None
    article = _sitemap_article(7, {"url": "https://example.com/x"})
    assert article["title"] == "https://example.com/x"
    assert article["published_at"] is None
