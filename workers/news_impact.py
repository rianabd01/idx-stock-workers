import argparse
import json
import time

from app.core.config import get_ai_config
from app.core.db import get_connection
from app.knowledge.company_vault import enrich_companies_with_vault
from app.repositories.impact_repository import (
    company_universe,
    pending_articles,
    save_impact_analysis,
)
from app.services.impact_analyzer import analyze_article_impact

def run_once(limit: int, dry_run: bool = False) -> dict:
    config = None if dry_run else get_ai_config()
    model_name = "dry-run" if dry_run else config.model

    with get_connection() as conn:
        companies = enrich_companies_with_vault(company_universe(conn))
        articles = pending_articles(conn, model_name, limit)

        summary = {
            "model": model_name,
            "articles_checked": len(articles),
            "articles_analyzed": 0,
            "relevant_articles": 0,
            "dry_run": dry_run,
            "errors": [],
        }

        for article in articles:
            if dry_run:
                summary["articles_analyzed"] += 1
                continue

            try:
                result = analyze_article_impact(config, article, companies)
                save_impact_analysis(
                    conn,
                    article_id=article["id"],
                    model_name=model_name,
                    affected_tickers=result["affected_tickers"],
                    confidence=result["confidence"],
                    reasoning=result["reasoning"],
                    raw_response=result["raw_response"],
                )
                summary["articles_analyzed"] += 1
                if result["affected_tickers"]:
                    summary["relevant_articles"] += 1
            except Exception as exc:
                summary["errors"].append({"article_id": article["id"], "error": str(exc)[:500]})

        return summary


def main() -> None:
    parser = argparse.ArgumentParser(description="Analyze news impact against IDX listed-stock tickers.")
    parser.add_argument("--once", action="store_true", help="Run one analysis cycle and exit.")
    parser.add_argument("--limit", type=int, default=10, help="Max pending articles per cycle.")
    parser.add_argument("--dry-run", action="store_true", help="Validate DB/query flow without calling AI.")
    parser.add_argument(
        "--interval",
        type=int,
        default=600,
        help="Seconds between cycles when running continuously.",
    )
    args = parser.parse_args()

    while True:
        summary = run_once(args.limit, args.dry_run)
        print(json.dumps(summary, ensure_ascii=False), flush=True)

        if args.once:
            break
        time.sleep(args.interval)


if __name__ == "__main__":
    main()
