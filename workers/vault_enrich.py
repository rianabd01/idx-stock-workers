"""Enrichment worker: isi skeleton vault via web search + Jina + AI.

Command satu-off: uv run python -m workers.vault_enrich --limit 10
Setelah selesai, jalankan vault_indexer + profile_embeddings untuk sinkron.
"""

import argparse
import json
import time

from app.core.config import get_ai_config, get_jina_config
from app.services.vault_enricher import enrich_vault_file, find_skeletons

DEFAULT_VAULT_DIR = "company_vault/idx"


def run_once(vault_dir: str, limit: int, sleep_seconds: float = 2.0) -> dict:
    ai_config = get_ai_config()
    jina_config = get_jina_config()

    targets = find_skeletons(vault_dir, limit)
    result = {"vault_dir": vault_dir, "targets": len(targets), "enriched": 0, "errors": []}

    for path in targets:
        try:
            enriched = enrich_vault_file(ai_config, jina_config, path)
            if enriched.ok:
                result["enriched"] += 1
                print(f"ok {enriched.ticker}: {path.name}", flush=True)
            else:
                result["errors"].append({"ticker": enriched.ticker, "error": enriched.error})
                print(f"fail {enriched.ticker}: {enriched.error}", flush=True)
        except Exception as exc:
            result["errors"].append({"file": path.name, "error": str(exc)[:200]})
            print(f"fail {path.stem}: {str(exc)[:120]}", flush=True)
        time.sleep(sleep_seconds)

    return result


def main() -> None:
    parser = argparse.ArgumentParser(description="Enrich skeleton vault files with AI-generated profiles.")
    parser.add_argument("--once", action="store_true", help="Parity flag; enrichment selalu sekali jalan.")
    parser.add_argument("--limit", type=int, default=10, help="Jumlah skeleton yang di-enrich.")
    parser.add_argument("--vault-dir", default=DEFAULT_VAULT_DIR, help="Direktori vault skeleton.")
    args = parser.parse_args()
    print(json.dumps(run_once(args.vault_dir, args.limit), ensure_ascii=False))


if __name__ == "__main__":
    main()
