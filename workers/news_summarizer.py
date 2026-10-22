"""Summarizer worker: generate AI summary for articles with content.

Pipeline: news_articles (content available, summary is null)
          --(summarizer)--> news_articles.summary via AI model.
"""

import argparse
import json
import time

from app.core.config import get_ai_config
from app.core.db import get_connection
from app.repositories.news_repository import save_article_summary
from app.services.news_analyzer import summarize_article


def run_once(limit: int, sleep_seconds: float = 0.5) -> dict:
    config = get_ai_config()

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                select id, title, content
                from news_articles
                where length(content) > 50
                  and (summary is null or length(summary) < 10)
                order by coalesce(published_at, scraped_at) desc nulls last, id desc
                limit %s
                """,
                (limit,),
            )
            articles = list(cur.fetchall())

        result = {
            "articles_checked": len(articles),
            "summarized": 0,
            "errors": [],
        }

        for row in articles:
            try:
                summary = summarize_article(config, row["title"], row["content"])
                if summary:
                    save_article_summary(conn, row["id"], summary)
                    conn.commit()
                    result["summarized"] += 1
                    print(f"summary ok {row['id']}: {summary[:80]}", flush=True)
            except Exception as exc:
                try:
                    conn.rollback()
                except Exception:
                    pass
                err_str = str(exc).lower()
                result["errors"].append(
                    {"article_id": row["id"], "error": str(exc)[:300]}
                )
                if "429" in err_str:
                    print(
                        "[WARN] AI rate limited (429). Sleeping 30s before stopping batch...",
                        flush=True,
                    )
                    time.sleep(30)
                    break
                if "connection" in err_str or "shutdown" in err_str:
                    break
            time.sleep(sleep_seconds)

        return result


def main() -> None:
    parser = argparse.ArgumentParser(description="Summarize articles using AI model.")
    parser.add_argument(
        "--once", action="store_true", help="Run one summarization cycle and exit."
    )
    parser.add_argument("--limit", type=int, default=10, help="Max articles per cycle.")
    parser.add_argument(
        "--interval",
        type=int,
        default=60,
        help="Seconds between cycles when queue is empty.",
    )
    args = parser.parse_args()

    while True:
        try:
            summary = run_once(args.limit)
            print(json.dumps(summary, ensure_ascii=False), flush=True)

            if args.once:
                break

            if summary.get("summarized", 0) > 0:
                time.sleep(1)
            else:
                time.sleep(args.interval)
        except Exception as err:
            print(
                f"[ERROR] news_summarizer error: {err}. Retrying in 5 seconds...",
                flush=True,
            )
            if args.once:
                break
            time.sleep(5)


if __name__ == "__main__":
    main()
