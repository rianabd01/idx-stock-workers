"""Embedding indexer: chunking profil + embedding lokal -> company_profile_chunks.

Command satu-off: uv run python -m workers.profile_embeddings
Fase dipisah agar koneksi DB tidak idle saat model menghitung embedding.
"""

import argparse
import json

from app.core.config import get_embedding_config
from app.core.db import get_connection
from app.repositories.embedding_repository import fetch_profiles_for_embedding
from app.services.profile_embeddings import (
    embed_passages,
    load_existing_chunks,
    plan_chunk_sync,
    write_chunk_sync,
)


def run_once() -> dict:
    config = get_embedding_config()

    # Fase 1: baca profil + snapshot chunk existing.
    with get_connection() as conn:
        profiles = fetch_profiles_for_embedding(conn)
        if not profiles:
            return {"error": "company_profiles kosong; jalankan workers/vault_indexer dulu"}
        existing = load_existing_chunks(conn, config.model)

    # Fase 2: compute di luar koneksi DB (model load + embed bisa menit-menit).
    plan = plan_chunk_sync(profiles, existing)
    vectors = embed_passages(config, [task.content for task in plan.tasks]) if plan.tasks else []

    # Fase 3: tulis dengan koneksi segar.
    if plan.tasks:
        with get_connection() as conn:
            write_chunk_sync(conn, profiles, plan, vectors, config.model, existing)
            conn.commit()

    return {
        "model": config.model,
        "profiles_loaded": len(profiles),
        "embedded": len(plan.tasks),
        "unchanged": plan.unchanged,
        "total_chunks": plan.total_chunks,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Index profile chunks with local embeddings.")
    parser.add_argument("--once", action="store_true", help="Parity flag; indexing selalu sekali jalan.")
    args = parser.parse_args()
    print(json.dumps(run_once(), ensure_ascii=False))


if __name__ == "__main__":
    main()
