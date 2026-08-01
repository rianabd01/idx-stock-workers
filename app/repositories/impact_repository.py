from typing import Any

from psycopg import Connection


def ensure_impact_schema(conn: Connection) -> None:
    with conn.cursor() as cur:
        cur.execute(
            """
            create table if not exists article_impact_analysis (
                id bigserial primary key,
                article_id bigint not null references news_articles(id) on delete cascade,
                affected_tickers text[],
                relevance text not null check (relevance in ('relevant', 'not_relevant')),
                confidence numeric not null default 0,
                reasoning text,
                model_name text not null,
                raw_response jsonb not null default '{}',
                analyzed_at timestamptz not null default now(),
                unique (article_id, model_name)
            )
            """
        )
        cur.execute(
            "create index if not exists article_impact_analysis_article_idx on article_impact_analysis (article_id)"
        )
        cur.execute(
            "create index if not exists article_impact_analysis_tickers_idx on article_impact_analysis using gin (affected_tickers)"
        )


def company_universe(conn: Connection, limit: int = 1200) -> list[dict[str, Any]]:
    with conn.cursor() as cur:
        cur.execute(
            """
            select
                data->>'ticker' as ticker,
                coalesce(data->>'company_name', label) as name
            from network_nodes
            where type = 'company'
              and data->>'ticker' is not null
            order by pagerank desc, degree desc, label
            limit %s
            """,
            (limit,),
        )
        return list(cur.fetchall())


def pending_articles(conn: Connection, model_name: str, limit: int = 20) -> list[dict[str, Any]]:
    with conn.cursor() as cur:
        cur.execute(
            """
            select a.id, a.title, a.summary, a.url, s.name as source_name
            from news_articles a
            join news_sources s on s.id = a.source_id
            left join article_impact_analysis impact
              on impact.article_id = a.id
             and impact.model_name = %s
            where impact.id is null
            order by coalesce(a.published_at, a.scraped_at) desc
            limit %s
            """,
            (model_name, limit),
        )
        return list(cur.fetchall())


def save_impact_analysis(
    conn: Connection,
    article_id: int,
    model_name: str,
    affected_tickers: list[str] | None,
    confidence: float,
    reasoning: str,
    raw_response: str,
) -> None:
    relevance = "relevant" if affected_tickers else "not_relevant"
    with conn.cursor() as cur:
        cur.execute(
            """
            insert into article_impact_analysis
                (article_id, affected_tickers, relevance, confidence, reasoning, model_name, raw_response)
            values (%s, %s, %s, %s, %s, %s, %s::jsonb)
            on conflict (article_id, model_name) do update set
                affected_tickers = excluded.affected_tickers,
                relevance = excluded.relevance,
                confidence = excluded.confidence,
                reasoning = excluded.reasoning,
                raw_response = excluded.raw_response,
                analyzed_at = now()
            """,
            (
                article_id,
                affected_tickers,
                relevance,
                confidence,
                reasoning,
                model_name,
                raw_response,
            ),
        )
