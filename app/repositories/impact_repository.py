"""Repository untuk impact analysis: universe profil, artikel pending, dan persist hasil."""

from psycopg.types.json import Jsonb

FETCH_UNIVERSE_SQL = """
select ticker, company_name, sector, subsector, commodities, tags, compact_profile, full_profile
from company_profiles
order by ticker
"""

FETCH_PENDING_SQL = """
select a.id, a.title, a.url, a.content
from news_articles a
where a.content is not null
  and not exists (
      select 1 from article_impact_analysis i
      where i.article_id = a.id and i.model_name = %s
  )
order by coalesce(a.published_at, a.scraped_at) desc nulls last, a.id
limit %s
"""

INSERT_ANALYSIS_SQL = """
insert into article_impact_analysis
    (article_id, affected_tickers, relevance, confidence, reasoning, model_name, raw_response)
values (%s, %s, %s, %s, %s, %s, %s)
returning id
"""

INSERT_TICKER_SQL = """
insert into article_impact_tickers
    (article_id, analysis_id, ticker, impact_type, confidence, reasoning, source)
values (%s, %s, %s, %s, %s, %s, %s)
"""


def fetch_company_profiles(conn) -> list[dict]:
    with conn.cursor() as cur:
        cur.execute(FETCH_UNIVERSE_SQL)
        return list(cur.fetchall())


def fetch_pending_articles(conn, model_name: str, limit: int) -> list[dict]:
    with conn.cursor() as cur:
        cur.execute(FETCH_PENDING_SQL, (model_name, limit))
        return list(cur.fetchall())


def save_impact_analysis(
    conn,
    article_id: int,
    affected_tickers: list[str],
    relevance: str,
    confidence: float,
    reasoning: str,
    model_name: str,
    raw_response: dict,
    ticker_rows: list[dict] | None = None,
) -> int:
    """Simpan ringkasan analisis + baris per-ticker. Return id analisis."""
    with conn.cursor() as cur:
        cur.execute(
            INSERT_ANALYSIS_SQL,
            (article_id, affected_tickers, relevance, confidence, reasoning, model_name, Jsonb(raw_response)),
        )
        analysis_id = cur.fetchone()["id"]
        if ticker_rows:
            cur.executemany(
                INSERT_TICKER_SQL,
                [
                    (
                        article_id,
                        analysis_id,
                        row["ticker"],
                        row.get("impact_type", "neutral"),
                        row.get("confidence", 0),
                        row.get("reasoning", ""),
                        row.get("source", "ai"),
                    )
                    for row in ticker_rows
                ],
            )
        return analysis_id
