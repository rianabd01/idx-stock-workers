from datetime import datetime, timezone
from typing import Any

from psycopg import Connection

DEFAULT_SOURCES = [
    {
        "name": "Antara Market",
        "base_url": "https://www.antaranews.com",
        "feed_url": "https://www.antaranews.com/rss/ekonomi.xml",
        "crawl_delay_seconds": 600,
    },
]


def seed_default_sources(conn: Connection) -> None:
    with conn.cursor() as cur:
        for source in DEFAULT_SOURCES:
            cur.execute(
                """
                insert into news_sources (name, base_url, feed_url, crawl_delay_seconds)
                values (%s, %s, %s, %s)
                on conflict (feed_url) do nothing
                """,
                (
                    source["name"],
                    source["base_url"],
                    source["feed_url"],
                    source["crawl_delay_seconds"],
                ),
            )


def active_sources(conn: Connection) -> list[dict[str, Any]]:
    with conn.cursor() as cur:
        cur.execute(
            """
            select *
            from news_sources
            where is_active = true
              and (
                last_fetched_at is null
                or last_fetched_at <= now() - (crawl_delay_seconds || ' seconds')::interval
              )
            order by last_fetched_at nulls first, id
            """
        )
        return list(cur.fetchall())


def mark_source_result(
    conn: Connection,
    source_id: int,
    status_code: int | None,
    error: str | None,
    etag: str | None,
    last_modified: str | None,
) -> None:
    with conn.cursor() as cur:
        cur.execute(
            """
            update news_sources
            set last_fetched_at = now(),
                last_status_code = %s,
                last_error = %s,
                etag = coalesce(%s, etag),
                last_modified = coalesce(%s, last_modified)
            where id = %s
            """,
            (status_code, error, etag, last_modified, source_id),
        )


def insert_article(conn: Connection, article: dict[str, Any]) -> bool:
    with conn.cursor() as cur:
        cur.execute(
            """
            insert into news_articles
                (source_id, url, title, summary, published_at, content_hash, raw_payload)
            values (%s, %s, %s, %s, %s, %s, %s::jsonb)
            on conflict (url) do nothing
            returning id
            """,
            (
                article["source_id"],
                article["url"],
                article["title"],
                article.get("summary"),
                article.get("published_at"),
                article["content_hash"],
                article["raw_payload"],
            ),
        )
        return cur.fetchone() is not None


def log_fetch(
    conn: Connection,
    source_id: int | None,
    url: str,
    status_code: int | None,
    duration_ms: int,
    error: str | None,
) -> None:
    with conn.cursor() as cur:
        cur.execute(
            """
            insert into news_fetch_logs (source_id, url, status_code, duration_ms, error)
            values (%s, %s, %s, %s, %s)
            """,
            (source_id, url, status_code, duration_ms, error),
        )


def parsed_datetime(value: Any) -> datetime | None:
    if not value:
        return None
    return datetime(*value[:6], tzinfo=timezone.utc)
