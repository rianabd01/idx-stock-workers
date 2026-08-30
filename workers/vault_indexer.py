"""Indexer worker: sinkronisasi company_vault/*.md -> tabel company_profiles.

Command satu-off, bukan daemon: uv run python -m workers.vault_indexer
Folder diurutkan dari yang paling kaya konten (LQ45 menang atas skeleton IDX).
"""

import argparse
import json

from app.core.db import get_connection
from app.services.vault_indexer import load_vault_profiles, sync_profiles

VAULT_DIRS = ["company_vault/lq45", "company_vault/idx"]


def run_once(vault_dirs: list[str] | None = None) -> dict:
    dirs = vault_dirs or VAULT_DIRS
    profiles = load_vault_profiles(dirs)
    with get_connection() as conn:
        counts = sync_profiles(conn, profiles)
        conn.commit()
    return {"vault_dirs": dirs, "profiles_loaded": len(profiles), **counts}


def main() -> None:
    parser = argparse.ArgumentParser(description="Index company vault Markdown into company_profiles.")
    parser.add_argument("--once", action="store_true", help="Parity flag; indexing selalu sekali jalan.")
    parser.add_argument(
        "--vault-dir",
        action="append",
        dest="vault_dirs",
        help="Direktori vault Markdown. Boleh diulang; default lq45 lalu idx.",
    )
    args = parser.parse_args()
    print(json.dumps(run_once(args.vault_dirs), ensure_ascii=False))


if __name__ == "__main__":
    main()
