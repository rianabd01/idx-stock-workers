import hashlib
import json
import time
from typing import Any
from urllib.parse import urlparse
from urllib.robotparser import RobotFileParser

import feedparser
import httpx

from app.repositories.news_repository import (
    active_sources,
    insert_article,
    log_fetch,
    mark_source_result,
    parsed_datetime,
    seed_default_sources,
)

USER_AGENT = "IDXStockBot/1.0 (+https://idx-stock.netlify.app)"
REQUEST_TIMEOUT_SECONDS = 15


def _robots_allowed(base_url: str, feed_url: str) -> bool:
    robots_url = f"{base_url.rstrip('/')}/robots.txt"
    parser = RobotFileParser()
    parser.set_url(robots_url)
    try:
        parser.read()
    except Exception:
        return True
    return parser.can_fetch(USER_AGENT, feed_url) and parser.can_fetch("*", feed_url)


def _content_hash(title: str, url: str, published_at: Any) -> str:
    payload = f"{title}|{url}|{published_at or ''}"
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _entry_url(entry: Any) -> str | None:
    link = entry.get("link")
    if not link:
        return None
    parsed = urlparse(link)
    if parsed.scheme not in {"http", "https"}:
        return None
    return link


def _article_from_entry(source_id: int, entry: Any) -> dict[str, Any] | None:
    url = _entry_url(entry)
    title = (entry.get("title") or "").strip()
    if not url or not title:
        return None

    published_at = parsed_datetime(entry.get("published_parsed") or entry.get("updated_parsed"))
    summary = (entry.get("summary") or entry.get("description") or "").strip() or None

    return {
        "source_id": source_id,
        "url": url,
        "title": title,
        "summary": summary,
        "published_at": published_at,
        "content_hash": _content_hash(title, url, published_at),
        "raw_payload": json.dumps(
            {
                "id": entry.get("id"),
                "link": url,
                "title": title,
                "summary": summary,
                "published": entry.get("published"),
                "updated": entry.get("updated"),
            },
            ensure_ascii=False,
        ),
    }


def collect_news_once(conn) -> dict[str, Any]:
    seed_default_sources(conn)

    summary = {
        "sources_checked": 0,
        "sources_skipped": 0,
        "articles_inserted": 0,
        "errors": [],
    }

    for source in active_sources(conn):
        summary["sources_checked"] += 1
        source_id = source["id"]
        feed_url = source["feed_url"]
        started_at = time.monotonic()

        if not _robots_allowed(source["base_url"], feed_url):
            error = "blocked_by_robots_txt"
            mark_source_result(conn, source_id, None, error, None, None)
            log_fetch(conn, source_id, feed_url, None, 0, error)
            summary["sources_skipped"] += 1
            summary["errors"].append({"source": source["name"], "error": error})
            continue

        headers = {"User-Agent": USER_AGENT}
        if source.get("etag"):
            headers["If-None-Match"] = source["etag"]
        if source.get("last_modified"):
            headers["If-Modified-Since"] = source["last_modified"]

        status_code = None
        try:
            with httpx.Client(
                timeout=REQUEST_TIMEOUT_SECONDS,
                follow_redirects=True,
                headers=headers,
            ) as client:
                response = client.get(feed_url)
            status_code = response.status_code
            duration_ms = int((time.monotonic() - started_at) * 1000)
            log_fetch(conn, source_id, feed_url, status_code, duration_ms, None)

            if response.status_code == 304:
                mark_source_result(
                    conn,
                    source_id,
                    status_code,
                    None,
                    response.headers.get("etag"),
                    response.headers.get("last-modified"),
                )
                continue
            if response.status_code in {403, 429}:
                error = f"source_returned_{response.status_code}"
                mark_source_result(conn, source_id, status_code, error, None, None)
                summary["errors"].append({"source": source["name"], "error": error})
                continue
            response.raise_for_status()

            parsed = feedparser.parse(response.content)
            for entry in parsed.entries:
                article = _article_from_entry(source_id, entry)
                if article and insert_article(conn, article):
                    summary["articles_inserted"] += 1

            mark_source_result(
                conn,
                source_id,
                status_code,
                None,
                response.headers.get("etag"),
                response.headers.get("last-modified"),
            )
        except Exception as exc:
            duration_ms = int((time.monotonic() - started_at) * 1000)
            error = str(exc)[:500]
            log_fetch(conn, source_id, feed_url, status_code, duration_ms, error)
            mark_source_result(conn, source_id, status_code, error, None, None)
            summary["errors"].append({"source": source["name"], "error": error})

    return summary
