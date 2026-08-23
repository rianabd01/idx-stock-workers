"""Generic XML sitemap news collector driven by per-source DB config.

Fetch uses curl_cffi with browser impersonation so CDN challenges
(Cloudflare/Akamai) that only serve browser-like TLS fingerprints pass.
"""

from __future__ import annotations

import hashlib
import json
import re
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Mapping
from urllib.parse import urlparse
from urllib.robotparser import RobotFileParser

from curl_cffi import requests as curl_requests
from lxml import etree

from app.repositories.news_repository import (
    active_sources,
    insert_article,
    log_fetch,
    mark_source_result,
)

USER_AGENT = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Safari/537.36"
REQUEST_TIMEOUT_SECONDS = 20
MAX_ITEMS_PER_SITEMAP = 500

_FALLBACK_DATE_FORMATS = (
    "%Y-%m-%dT%H:%M:%S",
    "%Y-%m-%d %H:%M:%S",
    "%Y-%m-%d",
)


@dataclass(frozen=True)
class SitemapConfig:
    item_xpath: str
    url_xpath: str
    title_xpath: str | None = None
    publication_date_xpath: str | None = None


def build_config(source_row: Mapping[str, Any]) -> SitemapConfig | None:
    """Return a config only when the row is fully set up for sitemap scraping."""
    if not source_row.get("sitemap_url"):
        return None
    item_xpath = (source_row.get("item_xpath") or "").strip()
    url_xpath = (source_row.get("url_xpath") or "").strip()
    if not item_xpath or not url_xpath:
        return None
    return SitemapConfig(
        item_xpath=item_xpath,
        url_xpath=url_xpath,
        title_xpath=(source_row.get("title_xpath") or "").strip() or None,
        publication_date_xpath=(source_row.get("publication_date_xpath") or "").strip() or None,
    )


def parse_datetime_raw(raw: str | None) -> datetime | None:
    """Parse W3C/ISO-8601 dates; naive values are assumed UTC. None on failure."""
    if not raw:
        return None
    text = raw.strip()
    if text.endswith(("Z", "z")):
        text = text[:-1] + "+00:00"
    parsed = None
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError:
        for fmt in _FALLBACK_DATE_FORMATS:
            try:
                parsed = datetime.strptime(text, fmt)
                break
            except ValueError:
                continue
    if parsed is None:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    else:
        # Normalisasi ke UTC agar konsisten dengan format standar aplikasi.
        parsed = parsed.astimezone(timezone.utc)
    return parsed


def fetch_sitemap(url: str) -> bytes | None:
    """GET sitemap via curl_cffi (Chrome impersonation); None on any failure."""
    try:
        response = curl_requests.get(url, impersonate="chrome", timeout=REQUEST_TIMEOUT_SECONDS)
        response.raise_for_status()
        return response.content
    except Exception:
        return None


def _node_text(node: Any) -> str | None:
    if node is None:
        return None
    if isinstance(node, str):
        return " ".join(node.split()) or None
    if isinstance(node, etree._Element):  # noqa: SLF001 - lxml private attr check
        return " ".join("".join(node.itertext()).split()) or None
    return None


def _first_text(item: Any, xpath_expr: str, namespaces: dict[str, str]) -> str | None:
    results = item.xpath(xpath_expr, namespaces=namespaces)
    if not results:
        return None
    return _node_text(results[0])


def _collect_namespaces(root: Any) -> dict[str, str]:
    """Gather prefix->uri mappings from every element in the tree.

    Prefixes may be declared on child elements (e.g. news: on <news:news>),
    not only on the root.
    """
    namespaces: dict[str, str] = {}
    for element in root.iter():
        for prefix, uri in element.nsmap.items():
            if prefix and uri and prefix not in namespaces:
                namespaces[prefix] = uri
    return namespaces


def _local_name_xpath(xpath_expr: str) -> str:
    """Rewrite simple child/descendant steps into local-name() predicates.

    Handles common sitemap shapes like './loc', 'news:title', './/news:title'
    so documents with a default namespace still match. Complex expressions are
    returned unchanged.
    """
    pattern = re.compile(r"(\./|//|/)(?:([A-Za-z_][\w.-]*):)?([A-Za-z_][\w.-]*)")
    rewritten = pattern.sub(lambda m: f"{m.group(1)}*[local-name()='{m.group(3)}']", xpath_expr)
    return rewritten


def parse_sitemap(xml_content: bytes, config: SitemapConfig) -> list[dict[str, Any]]:
    """Parse sitemap XML into normalized items.

    Returns [] on malformed XML or invalid XPath. Items without a URL are
    skipped; missing title/publication date are kept as None.

    XPath prefixes resolve against namespace declarations found anywhere in
    the document. For documents with a default namespace (no prefix), use
    local-name() based XPath since lxml cannot bind an unprefixed name.
    """
    parser = etree.XMLParser(resolve_entities=False, no_network=True)
    try:
        root = etree.fromstring(xml_content, parser=parser)
    except etree.XMLSyntaxError:
        return []

    namespaces = _collect_namespaces(root)

    try:
        items = root.xpath(config.item_xpath, namespaces=namespaces)
        if not items and "local-name()" not in config.item_xpath:
            # Fallback for default-namespace documents where unprefixed
            # names never match: retry with local-name() predicates.
            fallback = SitemapConfig(
                item_xpath=_local_name_xpath(config.item_xpath),
                url_xpath=_local_name_xpath(config.url_xpath),
                title_xpath=_local_name_xpath(config.title_xpath) if config.title_xpath else None,
                publication_date_xpath=(
                    _local_name_xpath(config.publication_date_xpath)
                    if config.publication_date_xpath
                    else None
                ),
            )
            items = root.xpath(fallback.item_xpath, namespaces=namespaces)
            config = fallback
    except etree.XPathError:
        return []

    articles: list[dict[str, Any]] = []
    for item in items[:MAX_ITEMS_PER_SITEMAP]:
        url = _first_text(item, config.url_xpath, namespaces)
        if not url:
            continue
        title = _first_text(item, config.title_xpath, namespaces) if config.title_xpath else None
        published_raw = (
            _first_text(item, config.publication_date_xpath, namespaces)
            if config.publication_date_xpath
            else None
        )
        published_at = parse_datetime_raw(published_raw)
        articles.append(
            {
                "url": url,
                "title": title,
                "publication_date": published_at.isoformat() if published_at else None,
            }
        )
    return articles


# ---------------------------------------------------------------------------
# Collector orchestration
# ---------------------------------------------------------------------------

# Respect robots.txt
def _robots_allowed(base_url: str, feed_url: str) -> bool:
    robots_url = f"{base_url.rstrip('/')}/robots.txt"
    parser = RobotFileParser()
    try:
        # curl_cffi + impersonation agar CDN tidak memblokir fetch robots.txt.
        response = curl_requests.get(robots_url, impersonate="chrome", timeout=REQUEST_TIMEOUT_SECONDS)
        response.raise_for_status()
        parser.parse(response.text.splitlines())
    except Exception:
        return True
    return parser.can_fetch(USER_AGENT, feed_url) and parser.can_fetch("*", feed_url)


def _content_hash(title: str, url: str, published_at: Any) -> str:
    payload = f"{title}|{url}|{published_at or ''}"
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _sitemap_article(source_id: int, item: dict[str, Any]) -> dict[str, Any] | None:
    url = (item.get("url") or "").strip()
    title = (item.get("title") or "").strip()
    if not url:
        return None

    published_at = parse_datetime_raw(item.get("publication_date"))
    return {
        "source_id": source_id,
        "url": url,
        "title": title or url,
        "summary": None,
        "published_at": published_at,
        "content_hash": _content_hash(title or url, url, published_at),
        "raw_payload": json.dumps({"sitemap_item": item}, ensure_ascii=False),
    }


def _collect_source_via_sitemap(
    conn,
    source: dict[str, Any],
    config: SitemapConfig,
    summary: dict[str, Any],
) -> None:
    source_id = source["id"]
    sitemap_url = source["sitemap_url"]
    started_at = time.monotonic()

    sitemap_host = f"{urlparse(sitemap_url).scheme}://{urlparse(sitemap_url).netloc}"
    
    # Respect robots.txt
    if not _robots_allowed(sitemap_host, sitemap_url):
        error = "blocked_by_robots_txt"
        mark_source_result(conn, source_id, None, error, None, None)
        log_fetch(conn, source_id, sitemap_url, None, 0, error)
        summary["sources_skipped"] += 1
        summary["errors"].append({"source": source["name"], "error": error})
        return

    try:
        content = fetch_sitemap(sitemap_url)
        if content is None:
            error = "sitemap_fetch_blocked"
            mark_source_result(conn, source_id, 403, error, None, None)
            log_fetch(conn, source_id, sitemap_url, 403, int((time.monotonic() - started_at) * 1000), error)
            summary["sources_skipped"] += 1
            summary["errors"].append({"source": source["name"], "error": error})
            return
        items = parse_sitemap(content, config)
        duration_ms = int((time.monotonic() - started_at) * 1000)

        log_fetch(conn, source_id, sitemap_url, 200, duration_ms, None)

        inserted = 0
        for entry in items:
            article = _sitemap_article(source_id, entry)
            if article and insert_article(conn, article):
                inserted += 1
        summary["articles_inserted"] += inserted

        mark_source_result(conn, source_id, 200, None, None, None)
    except Exception as exc:
        duration_ms = int((time.monotonic() - started_at) * 1000)
        error = str(exc)[:500]
        log_fetch(conn, source_id, sitemap_url, None, duration_ms, error)
        mark_source_result(conn, source_id, None, error, None, None)
        summary["errors"].append({"source": source["name"], "error": error})


def collect_news_once(conn) -> dict[str, Any]:
    summary = {
        "sources_checked": 0,
        "sources_skipped": 0,
        "articles_inserted": 0,
        "errors": [],
    }

    for source in active_sources(conn):
        summary["sources_checked"] += 1
        sitemap_config = build_config(source)
        if not sitemap_config:
            continue
        _collect_source_via_sitemap(conn, source, sitemap_config, summary)

    return summary
