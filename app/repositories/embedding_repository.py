"""Repository untuk Phase 5: profil + versi, dan chunks embedding untuk retrieval."""

FETCH_PROFILES_FOR_EMBEDDING_SQL = """
select ticker, company_name, sector, subsector, commodities, tags,
       compact_profile, full_profile, profile_version
from company_profiles
order by ticker
"""

FETCH_CHUNKS_SQL = """
select c.ticker, c.chunk_type, c.content, c.embedding
from company_profile_chunks c
where c.model_name = %s
"""


def fetch_profiles_for_embedding(conn) -> list[dict]:
    """Profil lengkap termasuk profile_version (dibutuhkan indexer chunks)."""
    with conn.cursor() as cur:
        cur.execute(FETCH_PROFILES_FOR_EMBEDDING_SQL)
        return list(cur.fetchall())


def fetch_chunks(conn, model_name: str) -> list[dict]:
    """Semua chunks untuk satu embedding model (embedding sebagai list of float)."""
    with conn.cursor() as cur:
        cur.execute(FETCH_CHUNKS_SQL, (model_name,))
        return [
            {
                "ticker": row["ticker"],
                "chunk_type": row["chunk_type"],
                "content": row["content"],
                "embedding": list(row["embedding"]),
            }
            for row in cur.fetchall()
        ]
