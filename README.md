# IDX Stock Workers

Repository terpisah untuk background workers IDX Stock. Worker tidak melayani request user; tugasnya mengumpulkan/memproses data lalu menulis hasil ke PostgreSQL. API backend membaca hasil matang dari DB.

## Worker yang tersedia

```text
workers/news_collector_worker.py
workers/news_impact_worker.py
```

### News collector

News collector saat ini RSS-first dan compliance-first:

- seed source RSS publik ke `news_sources`.
- cek `robots.txt` sebelum fetch feed.
- pakai User-Agent transparan `IDXStockBot/1.0`.
- rate limit per source via `crawl_delay_seconds`.
- support `ETag` dan `Last-Modified`.
- dedupe artikel dengan `unique(url)`.
- simpan audit fetch ke `news_fetch_logs`.
- tidak melakukan bypass anti-bot/CAPTCHA/proxy rotation.

## Struktur

```text
app/
  core/
    db.py                       PostgreSQL connection helper
  repositories/
    news_repository.py           schema + write helpers news collector
    impact_repository.py         schema + query/write helpers AI impact
  services/
    news_collector.py            logic collect RSS, parse, dedupe, insert
    impact_analyzer.py           OpenAI-compatible ticker impact classifier
workers/
  news_collector_worker.py       entrypoint collector worker
  news_impact_worker.py          entrypoint AI impact worker
```

## Environment

Copy `.env.example` ke `.env`:

```bash
cp .env.example .env
```

Isi:

```env
DATABASE_URL=postgresql://USER:PASSWORD@HOST:PORT/DB_NAME
```

## Install

```bash
uv sync
```

## Run sekali

```bash
uv run python -m workers.news_collector_worker --once
```

Contoh output:

```json
{"sources_checked": 1, "sources_skipped": 0, "articles_inserted": 0, "errors": []}
```

`articles_inserted` bisa `0` jika artikel sudah ada atau feed return `304 Not Modified`.

## Run continuous local

```bash
uv run python -m workers.news_collector_worker --interval 600
```

## AI impact worker

Worker ini membaca artikel yang belum dianalisis, mengambil universe emiten dari `network_nodes`, lalu memanggil OpenAI-compatible chat completions API.

Jika artikel tidak relevan ke saham IDX, hasilnya disimpan sebagai:

```json
{
  "affected_tickers": null,
  "relevance": "not_relevant"
}
```

Run tanpa memanggil AI untuk validasi DB/query flow:

```bash
uv run python -m workers.news_impact_worker --once --limit 2 --dry-run
```

Run dengan AI:

```bash
uv run python -m workers.news_impact_worker --once --limit 10
```

Continuous local:

```bash
uv run python -m workers.news_impact_worker --interval 600 --limit 10
```

Environment OpenAI-compatible:

```env
AI_API_KEY=your-openai-compatible-api-key
AI_BASE_URL=https://api.openai.com/v1
AI_MODEL=gpt-4o-mini
AI_TIMEOUT_SECONDS=45
```

`AI_BASE_URL` harus base URL `/v1`, karena worker memanggil:

```text
{AI_BASE_URL}/chat/completions
```

Untuk production nanti, jalankan via service manager seperti systemd. Jangan deploy dulu kalau masih fase eksplorasi local.

## Database contract

Worker menulis ke table:

```text
news_sources
news_articles
news_fetch_logs
article_impact_analysis
```

Backend API membaca dari:

```text
news_articles
news_sources
```

Boundary antar service adalah PostgreSQL, bukan import Python antar repo.

## Smoke test

```bash
uv run python -m py_compile app/core/db.py app/repositories/news_repository.py app/services/news_collector.py workers/news_collector_worker.py
uv run python -m workers.news_collector_worker --once
```

Cek artikel:

```bash
uv run python - <<'PY'
from app.core.db import get_connection

with get_connection() as conn:
    with conn.cursor() as cur:
        cur.execute('select count(*) as count from news_articles')
        print(cur.fetchone()['count'])
PY
```
