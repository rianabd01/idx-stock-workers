"""Analyzer worker: fetch article content via article_reader without AI dependency.

Pipeline: news_sources.sitemap_url --(collector)--> news_articles (title/url)
          --(analyzer)--> content + published_at + description.
"""

import argparse
import json
import time

from app.core.db import get_connection
from app.repositories.news_repository import save_article_content
from app.services.article_reader import FetchBlocked, fetch_article_content
from app.services.news_collector import parse_datetime_raw


def run_once(limit: int, sleep_seconds: float = 0.3) -> dict:
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                select a.id, a.title, a.url
                from news_articles a
                join news_sources s on s.id = a.source_id
                where a.content is null
                order by coalesce(a.published_at, a.scraped_at) desc nulls last, a.id
                limit %s
                """,
                (limit,),
            )
            articles = list(cur.fetchall())

        result = {
            "articles_checked": len(articles),
            "contents_fetched": 0,
            "errors": [],
        }

        for row in articles:
            try:
                try:
                    fetched = fetch_article_content(row["url"])
                except FetchBlocked as exc:
                    result["errors"].append(
                        {"article_id": row["id"], "error": str(exc)[:300]}
                    )
                    continue
                if not fetched:
                    result["errors"].append(
                        {"article_id": row["id"], "error": "fetch_failed"}
                    )
                    save_article_content(
                        conn,
                        row["id"],
                        content="",
                        confidence=0.0,
                        published_at=None,
                        summary=None,
                    )
                    conn.commit()
                    continue

                # Simpan konten artikel bersih + fallback summary dari description meta
                save_article_content(
                    conn,
                    row["id"],
                    fetched["content"],
                    confidence=1.0,
                    published_at=parse_datetime_raw(fetched.get("published_time")),
                    summary=fetched.get("description"),
                )
                conn.commit()
                result["contents_fetched"] += 1
                print(
                    f"ok {row['id']}: fetched {len(fetched['content'])} chars",
                    flush=True,
                )
            except Exception as exc:
                try:
                    conn.rollback()
                except Exception:
                    pass
                err_str = str(exc).lower()
                result["errors"].append(
                    {"article_id": row["id"], "error": str(exc)[:300]}
                )
                if "connection" in err_str or "shutdown" in err_str:
                    break
            time.sleep(sleep_seconds)

        return result


def main() -> None:
    parser = argparse.ArgumentParser(description="Fetch article content without AI.")
    parser.add_argument(
        "--once", action="store_true", help="Run one analysis cycle and exit."
    )
    parser.add_argument("--limit", type=int, default=20, help="Max articles per cycle.")
    parser.add_argument(
        "--interval",
        type=int,
        default=600,
        help="Seconds between cycles when running continuously and queue is empty.",
    )
    args = parser.parse_args()

    while True:
        try:
            summary = run_once(args.limit)
            print(json.dumps(summary, ensure_ascii=False), flush=True)

            if args.once:
                break

            if summary.get("contents_fetched", 0) > 0:
                time.sleep(1)
            else:
                time.sleep(args.interval)
        except Exception as err:
            print(
                f"[ERROR] news_analyzer error: {err}. Retrying in 5 seconds...",
                flush=True,
            )
            if args.once:
                break
            time.sleep(5)


if __name__ == "__main__":
    main()
