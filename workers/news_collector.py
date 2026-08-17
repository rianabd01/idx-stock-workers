import argparse
import json
import time

from app.core.db import check_required_tables, get_connection
from app.services.news_collector import collect_news_once

REQUIRED_TABLES = {"news_sources", "news_articles", "news_fetch_logs"}


def run_once() -> dict:
    with get_connection() as conn:
        check_required_tables(conn, "news collector", REQUIRED_TABLES)
        return collect_news_once(conn)


def main() -> None:
    parser = argparse.ArgumentParser(description="Collect public news feed data into PostgreSQL.")
    parser.add_argument("--once", action="store_true", help="Run one collection cycle and exit.")
    parser.add_argument(
        "--interval",
        type=int,
        default=600,
        help="Seconds between cycles when running continuously.",
    )
    args = parser.parse_args()

    while True:
        summary = run_once()
        print(json.dumps(summary, ensure_ascii=False), flush=True)

        if args.once:
            break
        time.sleep(args.interval)


if __name__ == "__main__":
    main()
