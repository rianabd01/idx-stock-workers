"""Impact worker: retrieval kandidat dari company_profiles lalu AI final impact analysis.

Pipeline: news_articles.content --(analyzer)--> --(impact)--> article_impact_analysis.
Jalankan indexer dulu: uv run python -m workers.vault_indexer
"""

import argparse
import json
import time

from app.core.config import get_ai_config, get_embedding_config
from app.core.db import get_connection
from app.repositories.embedding_repository import fetch_chunks
from app.repositories.impact_repository import (
    fetch_company_profiles,
    fetch_pending_articles,
    save_impact_analysis,
)
from app.services.impact_analysis import (
    ANALYSIS_VERSION,
    analyze_impact,
    expand_peers,
    merge_candidates,
    retrieve_candidates,
    retrieve_vector_candidates,
    validate_impacts,
)
from app.services.profile_embeddings import embed_query

def run_once(limit: int, sleep_seconds: float = 0.3) -> dict:
    config = get_ai_config()
    embedding_config = get_embedding_config()

    with get_connection() as conn:
        profiles = fetch_company_profiles(conn)
        if not profiles:
            return {"error": "company_profiles kosong; jalankan workers/vault_indexer dulu"}

        try:
            chunks = fetch_chunks(conn, embedding_config.model)
        except Exception:
            chunks = []
        articles = fetch_pending_articles(conn, config.model, limit)
        result = {
            "articles_checked": len(articles),
            "analyzed": 0,
            "not_relevant": 0,
            "chunks_loaded": len(chunks),
            "errors": [],
        }

        for row in articles:
            try:
                keyword_candidates = retrieve_candidates(row["title"], row["content"], profiles)
                vector_scores: dict[str, tuple[float, str]] = {}
                if chunks:
                    query_vector = embed_query(embedding_config, f"{row['title']}\n{row['content'][:2000]}")
                    vector_scores = retrieve_vector_candidates(
                        row["title"], row["content"], chunks, query_vector
                    )
                candidates = expand_peers(merge_candidates(keyword_candidates, vector_scores), profiles)
                candidate_rows = [p for p in profiles if p["ticker"] in {c.ticker for c in candidates}]
                audit_base = {
                    "analysis_version": ANALYSIS_VERSION,
                    "candidates": [
                        {"ticker": c.ticker, "score": c.score, "matched_terms": list(c.matched_terms)}
                        for c in candidates
                    ],
                }

                if not candidates:
                    save_impact_analysis(
                        conn, row["id"], [], "not_relevant", 0,
                        "Tidak ada kandidat lolos threshold retrieval.", config.model, audit_base,
                    )
                    conn.commit()
                    result["not_relevant"] += 1
                    continue

                parsed = analyze_impact(config, row["title"], row["content"], candidate_rows)
                selected, dropped = validate_impacts(parsed["impacts"], [c.ticker for c in candidates])
                peer_tickers = {c.ticker for c in candidates if any(t.startswith("peer:") for t in c.matched_terms)}
                ticker_rows = [
                    {
                        "ticker": item["ticker"],
                        "impact_type": item["impact_type"],
                        "confidence": item["confidence"],
                        "reasoning": item["reasoning"],
                        "source": "peer" if item["ticker"] in peer_tickers else "ai",
                    }
                    for item in selected
                ]
                relevance = "relevant" if parsed["relevant"] and selected else "not_relevant"
                confidence = max((item["confidence"] for item in selected), default=0.0)
                reasoning = "; ".join(f"{i['ticker']}: {i['reasoning']}" for i in selected) or "AI menyatakan tidak relevan."
                save_impact_analysis(
                    conn, row["id"],
                    [item["ticker"] for item in selected], relevance, confidence,
                    reasoning, config.model, {**audit_base, "impacts": selected, "dropped_tickers": dropped},
                    ticker_rows=ticker_rows,
                )
                conn.commit()
                result["analyzed"] += 1
                print(f"ok {row['id']}: {relevance} {', '.join(i['ticker'] for i in selected)}", flush=True)
            except Exception as exc:
                conn.rollback()
                result["errors"].append({"article_id": row["id"], "error": str(exc)[:300]})
            time.sleep(sleep_seconds)

        return result

def main() -> None:
    parser = argparse.ArgumentParser(description="Analyze article impact against company profiles.")
    parser.add_argument("--once", action="store_true", help="Run one analysis cycle and exit.")
    parser.add_argument("--limit", type=int, default=20, help="Max articles per cycle.")
    parser.add_argument("--interval", type=int, default=600, help="Seconds between cycles.")
    args = parser.parse_args()

    while True:
        print(json.dumps(run_once(args.limit), ensure_ascii=False), flush=True)
        if args.once:
            break
        time.sleep(args.interval)

if __name__ == "__main__":
    main()