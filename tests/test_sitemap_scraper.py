import pytest

from app.services.news_collector import (
    SitemapConfig,
    build_config,
    fetch_sitemap,
    parse_datetime_raw,
    parse_sitemap,
)

STANDARD_SITEMAP = b"""<?xml version="1.0" encoding="UTF-8"?>
<urlset>
    <url>
        <loc>https://example.com/article-1</loc>
        <title>First Article</title>
        <date>2026-08-23T10:00:00+07:00</date>
    </url>
    <url>
        <loc>https://example.com/article-2</loc>
        <title>Second Article</title>
        <date>2026-08-23T09:30:00+07:00</date>
    </url>
</urlset>
"""

NEWS_SITEMAP_NS = b"""<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"
        xmlns:news="http://www.google.com/schemas/sitemap-news/0.9">
    <url>
        <loc>https://example.com/news-1</loc>
        <news:news>
            <news:publication>
                <news:name>CNBC</news:name>
                <news:language>en</news:language>
                <news:date>2026-08-23T10:00:00+07:00</news:date>
            </news:publication>
            <news:title>Example News</news:title>
        </news:news>
    </url>
    <url>
        <loc>https://example.com/news-2</loc>
        <news:news>
            <news:publication>
                <news:name>CNBC</news:name>
                <news:date>2026-08-22T08:00:00Z</news:date>
            </news:publication>
            <news:title>Another News Title</news:title>
        </news:news>
    </url>
</urlset>
"""

STANDARD_CONFIG = SitemapConfig(
    item_xpath="//url",
    url_xpath="./loc",
    title_xpath="./title",
    publication_date_xpath="./date",
)

NEWS_CONFIG = SitemapConfig(
    item_xpath="//url",
    url_xpath="./loc",
    title_xpath="./news:news/news:title",
    publication_date_xpath="./news:news/news:publication/news:date",
)


def test_standard_sitemap_without_namespace():
    items = parse_sitemap(STANDARD_SITEMAP, STANDARD_CONFIG)
    assert len(items) == 2
    assert items[0] == {
        "url": "https://example.com/article-1",
        "title": "First Article",
        "publication_date": "2026-08-23T03:00:00+00:00",
    }
    assert items[1]["title"] == "Second Article"


def test_news_sitemap_with_namespaces():
    items = parse_sitemap(NEWS_SITEMAP_NS, NEWS_CONFIG)
    assert len(items) == 2
    assert items[0]["url"] == "https://example.com/news-1"
    assert items[0]["title"] == "Example News"
    assert items[0]["publication_date"] == "2026-08-23T03:00:00+00:00"
    assert items[1]["publication_date"] == "2026-08-22T08:00:00+00:00"


def test_different_configs_for_different_structures():
    # Sama XML dengan namespace, tapi pakai XPath alternatif berbasis local-name().
    alt_config = SitemapConfig(
        item_xpath="//*[local-name()='url']",
        url_xpath="./*[local-name()='loc']",
        title_xpath=".//*[local-name()='title' and namespace-uri()='http://www.google.com/schemas/sitemap-news/0.9']",
        publication_date_xpath=None,
    )
    items = parse_sitemap(NEWS_SITEMAP_NS, alt_config)
    assert len(items) == 2
    assert items[0]["title"] == "Example News"
    assert items[0]["publication_date"] is None


def test_missing_optional_fields_and_missing_url():
    xml = b"""<?xml version="1.0"?>
    <urlset>
        <url>
            <loc>https://example.com/no-title-date</loc>
            <news:news xmlns:news="http://www.google.com/schemas/sitemap-news/0.9"></news:news>
        </url>
        <url>
            <title>Tanpa URL</title>
        </url>
    </urlset>
    """
    config = SitemapConfig(
        item_xpath="//url",
        url_xpath="./loc",
        title_xpath=".//news:title",
        publication_date_xpath=".//news:date",
    )
    items = parse_sitemap(xml, config)
    assert len(items) == 1
    assert items[0]["url"] == "https://example.com/no-title-date"
    assert items[0]["title"] is None
    assert items[0]["publication_date"] is None


def test_invalid_xml_returns_empty():
    assert parse_sitemap(b"<urlset><url><loc>", STANDARD_CONFIG) == []
    assert parse_sitemap(b"", STANDARD_CONFIG) == []


def test_empty_item_results():
    xml = b"""<?xml version="1.0"?>
    <urlset><other><loc>https://example.com/x</loc></other></urlset>
    """
    assert parse_sitemap(xml, STANDARD_CONFIG) == []


def test_invalid_xpath_config_returns_empty():
    config = SitemapConfig(item_xpath="//url[[", url_xpath="./loc")
    assert parse_sitemap(b"<urlset></urlset>", config) == []


def test_parse_datetime_raw_variants():
    assert parse_datetime_raw("2026-08-23T10:00:00+07:00").isoformat() == "2026-08-23T03:00:00+00:00"
    assert parse_datetime_raw("2026-08-23T03:00:00Z").tzinfo is not None
    naive = parse_datetime_raw("2026-08-23")
    assert naive.tzinfo is not None
    assert parse_datetime_raw("bukan-tanggal") is None
    assert parse_datetime_raw("") is None
    assert parse_datetime_raw(None) is None


def test_build_config_requires_minimum_fields():
    base = {
        "sitemap_url": "https://example.com/sitemap.xml",
        "item_xpath": "//url",
        "url_xpath": "./loc",
        "title_xpath": None,
        "publication_date_xpath": None,
    }
    config = build_config(base)
    assert config == SitemapConfig(item_xpath="//url", url_xpath="./loc")

    missing_url_xpath = dict(base, url_xpath=None)
    assert build_config(missing_url_xpath) is None

    no_sitemap = dict(base, sitemap_url=None)
    assert build_config(no_sitemap) is None


class FakeErrorResponse:
    def raise_for_status(self):
        raise Exception("404 not found")


class FakeErrorClient:
    def get(self, url):
        return FakeErrorResponse()


def test_fetch_failure_returns_none(monkeypatch):
    monkeypatch.setattr("app.services.news_collector.curl_requests", FakeErrorClient())
    assert fetch_sitemap("https://example.com/x") is None
