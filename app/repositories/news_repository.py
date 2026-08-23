from typing import Any

from psycopg import Connection


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
    content_confidence = 1.0 if article.get("content") else (0.5 if article.get("summary") else 0)
    with conn.cursor() as cur:
        cur.execute(
            """
            insert into news_articles
                (source_id, url, title, summary, published_at, content_hash, raw_payload, content, content_confidence)
            values (%s, %s, %s, %s, %s, %s, %s::jsonb, %s, %s)
            on conflict (url) do update set
                content = coalesce(news_articles.content, excluded.content),
                content_confidence = case
                    when news_articles.content is not null then news_articles.content_confidence
                    else excluded.content_confidence
                end
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
                article.get("content"),
                content_confidence,
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


def save_article_content(
    conn: Connection,
    article_id: int,
    content: str,
    confidence: float = 1.0,
    published_at: Any = None,
    summary: str | None = None,
) -> None:
    with conn.cursor() as cur:
        cur.execute(
            """
            update news_articles
            set content = %s,
                content_confidence = %s,
                published_at = coalesce(published_at, %s),
                summary = coalesce(summary, %s)
            where id = %s and content is null
            """,
            (content, confidence, published_at, summary, article_id),
        )
