# IDX Stock Workers

Repository background workers IDX Stock. Worker mengumpulkan/memproses data dan menulis hasil ke PostgreSQL; backend API membaca hasil matang dari DB.

## Worker

- `workers/news_collector.py`: collector RSS publik, compliance-first.
- `workers/news_impact.py`: klasifikasi dampak artikel ke ticker IDX dengan company vault.

Collector memeriksa `robots.txt`, memakai User-Agent transparan, mendukung ETag/Last-Modified, deduplikasi URL, dan mencatat fetch. Worker tidak melakukan bypass anti-bot/CAPTCHA/proxy rotation.

## Struktur

```text
app/
  core/
    config.py                    konfigurasi tervalidasi
    db.py                        koneksi PostgreSQL dan schema preflight read-only
  knowledge/
    company_vault.py             loader dan enrichment company vault
  repositories/
    news_repository.py           query/write news
    impact_repository.py         query/write impact
  services/
    news_collector.py            fetch dan normalisasi RSS
    impact_analyzer.py           ticker impact classifier
workers/
  news_collector.py              entrypoint collector
  news_impact.py                 entrypoint impact
```

## Environment dan instalasi

Copy `.env.example` ke `.env`, lalu isi minimal:

```env
DATABASE_URL=postgresql://USER:PASSWORD@HOST:PORT/DB_NAME
AI_API_KEY=your-api-key
AI_BASE_URL=https://api.openai.com/v1
AI_MODEL=gpt-4o-mini
AI_TIMEOUT_SECONDS=45
```

`AI_BASE_URL` adalah base URL `/v1`; worker memanggil `{AI_BASE_URL}/chat/completions`.

```bash
uv sync --dev
```

## Menjalankan worker

Collector satu siklus atau continuous:

```bash
uv run python -m workers.news_collector --once
uv run python -m workers.news_collector --interval 600
```

Impact tanpa AI untuk validasi DB/query flow, dengan AI, atau continuous:

```bash
uv run python -m workers.news_impact --once --limit 2 --dry-run
uv run python -m workers.news_impact --once --limit 10
uv run python -m workers.news_impact --interval 600 --limit 10
```

Impact worker membaca artikel yang belum dianalisis, mengambil universe dari `network_nodes`, memperkayanya dari `company_vault/lq45`, lalu hanya menerima ticker yang ada dalam universe. Artikel tidak relevan disimpan dengan `affected_tickers: null`.

## Database contract

Backend `idx-stock-backend` adalah satu-satunya pemilik schema dan migration. Workers tidak membuat atau mengubah schema. Sebelum tiap siklus, worker menjalankan preflight read-only sekali:

- collector: `news_sources`, `news_articles`, `news_fetch_logs`;
- impact: `news_articles`, `article_impact_analysis`, `network_nodes`.

Jika tabel belum tersedia, jalankan dari repository backend:

```bash
uv run alembic upgrade head
```

Boundary antar service adalah PostgreSQL, bukan import Python antar repository.

## Verifikasi

```bash
uv run python -m compileall -q app workers tests
uv run pytest
uv run python -m workers.news_collector --help
uv run python -m workers.news_impact --help
```

Smoke test DB tanpa panggilan AI:

```bash
uv run python -m workers.news_impact --once --limit 2 --dry-run
```

Collector `--once` melakukan akses network ke source RSS; jalankan hanya saat network fetch memang diinginkan.
