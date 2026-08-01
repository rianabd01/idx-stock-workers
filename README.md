# IDX Stock Workers

Repository background workers untuk platform **IDX Stock**. Worker bertugas mengumpulkan sitemap berita, mengekstrak konten & ringkasan AI, menganalisis dampak saham (ticker impact), mengindeks company vault, serta menghasilkan vector embeddings.

Semua worker menulis data matang ke database PostgreSQL (`idx2`), yang kemudian disajikan secara langsung oleh backend API (`idx-stock-backend`).

---

## Arsitektur Worker

| Worker | Entrypoint | Deskripsi & Pipeline |
| :--- | :--- | :--- |
| **News Collector** | `workers/news_collector.py` | Membaca konfigurasi sumber di `news_sources`, scraping sitemap XML (XPath dinamis), dan mencatat artikel baru ke `news_articles`. Mendukung filter `--source-id`. |
| **News Analyzer** | `workers/news_analyzer.py` | Mengambil artikel dengan `content is null`, fetch teks bersih via Jina Reader (`target_selector`), meringkas via AI model (`AI_MODEL`), serta memperbarui `summary`, `published_at`, dan `content_confidence`. Dilengkapi *auto-reconnect & queue draining*. |
| **News Impact** | `workers/news_impact.py` | Menganalisis dampak sentimen (*bullish / bearish / neutral*), skor confidence, dan memetakan keterkaitan artikel terhadap emiten (`article_impact_tickers`). |
| **Vault Indexer** | `workers/vault_indexer.py` | Mengindeks Markdown profil perusahaan/emiten dari knowledge vault ke dalam tabel `company_profiles` dan `company_profile_chunks`. |
| **Profile Embeddings** | `workers/profile_embeddings.py` | Menghasilkan vector embeddings untuk setiap chunk profil emiten untuk semantic search. |

---

## Struktur Folder

```text
app/
  core/
    config.py                  # Validasi env 
    db.py                      # Koneksi connection pool PostgreSQL
  repositories/
    news_repository.py         # Query & write news_sources & news_articles
    impact_repository.py       # Query & write article_impact_tickers
    embedding_repository.py    # Query & write company_profile_chunks
  services/
    news_collector.py          
    news_analyzer.py           
    impact_analysis.py         # Logika penentuan dampak emiten & sentimen
    vault_indexer.py           # Parser Markdown vault ke DB
    profile_embeddings.py      # Client vector embedding generator
workers/
  news_collector.py            # CLI entrypoint News Collector
  news_analyzer.py             # CLI entrypoint News Analyzer
  news_impact.py               # CLI entrypoint Impact Analysis
  vault_indexer.py             # CLI entrypoint Vault Indexer
  profile_embeddings.py        # CLI entrypoint Profile Embeddings
```

---

## Environment & Instalasi

Salin `.env.example` ke `.env`:

```env
# Database
DATABASE_URL=postgresql://USER:PASSWORD@HOST:PORT/idx2

# AI Summarizer & Analyzer
AI_API_KEY=your-api-key
AI_BASE_URL=http://localhost:20128/v1
AI_MODEL=scrape
AI_TIMEOUT_SECONDS=45

# Jina Reader (Article Fetcher)
JINA_API_KEY=your-jina-key
JINA_BASE_URL=https://r.jina.ai

# Embeddings (Opsional / Profile Embeddings)
EMBEDDING_API_KEY=your-embedding-key
EMBEDDING_BASE_URL=http://localhost:20128/v1
EMBEDDING_MODEL=text-embedding-3-small
```

Instalasi dependensi menggunakan `uv`:

```bash
uv sync --dev
```

---

## Menjalankan Workers

### 1. News Collector (Sitemap Scraping)
```bash
# Satu kali jalan
uv run python -m workers.news_collector --once

# Berjalan periodik (misal setiap 10 menit / 600 detik)
uv run python -m workers.news_collector --interval 600
```

### 2. News Analyzer (Content Fetching & AI Summary)
```bash
# Satu batch (misal limit 20 artikel)
uv run python -m workers.news_analyzer --once --limit 20

# Continuous daemon mode (otomatis drain antrean saat ada artikel baru)
uv run python -m workers.news_analyzer --limit 20 --interval 600
```

### 3. News Impact Analysis
```bash
# Analisis dampak artikel terhadap emiten
uv run python -m workers.news_impact --once --limit 20
uv run python -m workers.news_impact --limit 20 --interval 600
```

### 4. Company Vault & Profile Embeddings
```bash
# Indeks Markdown vault emiten ke database
uv run python -m workers.vault_indexer --once

# Generate vector embeddings untuk chunk profil emiten
uv run python -m workers.profile_embeddings --once
```

---

## Database Contract

- Backend `idx-stock-backend` adalah pemilik utama schema dan migration database (`alembic`).
- Workers **tidak membuat atau mengubah schema table**.
- Sebelum menjalankan workers pada database baru, pastikan migrasi sudah dijalankan dari repository backend:
  ```bash
  github.com/rianabd01/idx-stock-backend
  alembic upgrade head
  ```

---

## Verifikasi & Testing

Jalankan test suite untuk memastikan semua unit test lulus:

```bash
# Syntax & bytecode check
uv run python -m compileall -q app workers tests

# Menjalankan seluruh test suite (pytest)
uv run pytest
```
