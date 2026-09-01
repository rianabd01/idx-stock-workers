"""Analyzer worker: fetch article content via Jina, then summarize with the AI model.

Pipeline: news_sources.sitemap_url --(collector)--> news_articles (title/url)
          --(analyzer)--> content + summary + published_at + confidence.
"""

import argparse
import json
import time

from app.core.config import get_ai_config, get_jina_config
from app.core.db import get_connection
from app.repositories.news_repository import save_article_content
from app.services.news_analyzer import fetch_article_content, summarize_article
from app.services.news_collector import parse_datetime_raw


def run_once(limit: int, sleep_seconds: float = 0.3) -> dict:
    config = get_ai_config()
    jina_config = get_jina_config()

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                select a.id, a.title, a.url, s.target_selector
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
            "summarized": 0,
            "errors": [],
        }

        for row in articles:
            try:
                fetched = fetch_article_content(jina_config, row["url"], target_selector=row.get("target_selector"))
                if not fetched:
                    result["errors"].append({"article_id": row["id"], "error": "jina_fetch_failed"})
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

                summary = summarize_article(config, row["title"], fetched["content"])
                save_article_content(
                    conn,
                    row["id"],
                    fetched["content"],
                    confidence=1.0,
                    published_at=parse_datetime_raw(fetched.get("published_time")),
                    summary=summary or None,
                )
                conn.commit()
                result["contents_fetched"] += 1
                result["summarized"] += 1 if summary else 0
                print(f"ok {row['id']}: {summary[:90]}", flush=True)
            except Exception as exc:
                try:
                    conn.rollback()
                except Exception:
                    pass
                result["errors"].append({"article_id": row["id"], "error": str(exc)[:300]})
                if "connection" in str(exc).lower() or "shutdown" in str(exc).lower():
                    break
            time.sleep(sleep_seconds)

        return result


def main() -> None:
    parser = argparse.ArgumentParser(description="Analyze articles: fetch content + AI summary.")
    parser.add_argument("--once", action="store_true", help="Run one analysis cycle and exit.")
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

            # If there were articles processed, immediately process the next batch; otherwise wait for interval.
            if summary.get("articles_checked", 0) > 0:
                time.sleep(1)
            else:
                time.sleep(args.interval)
        except Exception as err:
            print(f"[ERROR] news_analyzer error: {err}. Retrying in 5 seconds...", flush=True)
            if args.once:
                break
            time.sleep(5)


if __name__ == "__main__":
    main()


