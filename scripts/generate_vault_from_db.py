"""Generate skeleton vault Markdown untuk seluruh emiten IDX dari network_nodes.

Sumber: network_nodes (type='company') pada versi aktif.
Output: company_vault/idx/{TICKER}.md — file lq45/ yang sudah ada tidak disentuh.
"""

import json
from pathlib import Path

from app.core.db import get_connection

DEFAULT_OUTPUT_DIR = "company_vault/idx"

SKELETON_TEMPLATE = """---
ticker: {ticker}
name: {name}
sektor: {sektor}
subsektor: {subsektor}
komoditas: []
tag: []
---

# Ringkasan bisnis
{name} ({ticker}) adalah emiten yang tercatat di Bursa Efek Indonesia. Profil bisnis lengkap belum tersedia dan perlu diisi manual atau via enrichment.

# Sumber pendapatan utama
- Belum tersedia.

# Driver bisnis
- Belum tersedia.

# Risiko utama
- Belum tersedia.

# Sensitif terhadap berita
- Kondisi umum pasar modal dan ekonomi makro Indonesia.
"""

RICH_DIRS = [Path("company_vault/lq45")]


def _has_rich_file(ticker: str) -> bool:
    return any((rich_dir / f"{ticker}.md").exists() for rich_dir in RICH_DIRS)


def fetch_active_companies(conn) -> list[dict]:
    with conn.cursor() as cur:
        cur.execute(
            """
            select distinct n.data->>'ticker' as ticker,
                   n.data->>'company_name' as company_name,
                   n.data->>'normalized_name' as normalized_name
            from network_nodes n
            join network_versions v on v.id = n.version_id
            where n.type = 'company' and v.is_active
              and n.data->>'ticker' is not null
            order by 1
            """
        )
        return list(cur.fetchall())


def generate(output_dir: str) -> dict:
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    with get_connection() as conn:
        companies = fetch_active_companies(conn)

    counts = {"total": len(companies), "created": 0, "skipped_existing": 0, "skipped_lq45_rich": 0}
    for row in companies:
        ticker = str(row["ticker"]).strip().upper()
        name = str(row["company_name"] or row["normalized_name"] or ticker).strip()
        target = output_path / f"{ticker}.md"
        if _has_rich_file(ticker):
            counts["skipped_lq45_rich"] += 1
            continue
        if target.exists():
            counts["skipped_existing"] += 1
            continue
        # Emiten LQ45 sudah punya file kaya; skeleton hanya untuk sisanya.
        target.write_text(
            SKELETON_TEMPLATE.format(ticker=ticker, name=name, sektor="-", subsektor="-"),
            encoding="utf-8",
        )
        counts["created"] += 1
    return counts


if __name__ == "__main__":
    print(json.dumps(generate(DEFAULT_OUTPUT_DIR), ensure_ascii=False))
