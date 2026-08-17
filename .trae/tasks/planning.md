Berikut roadmap development yang paling masuk akal, dari yang **paling cepat jalan** sampai yang **scalable untuk semua saham IDX**.

---

# Phase 0 — Current Baseline

Status sekarang:

```text
news_articles
   ↓
news_impact_worker
   ↓
company_universe dari network_nodes
   ↓
AI analyze
   ↓
article_impact_analysis
```

Kelebihan:
- Sudah bisa jalan.
- Sudah validasi ticker dari DB.
- Sudah pakai AI model dari `.env`.

Kekurangan:
- Konteks saham masih tipis.
- AI cuma tahu `ticker + company_name`.
- Belum pakai vault.
- Kalau semua saham + vault panjang dikirim ke prompt, bisa mahal.

---

# Phase 1 — Vault Enrichment Sederhana

Tujuan: **AI mulai pakai isi Markdown vault.**

## Yang dibangun

### 1. Loader vault lokal
Buat module:
```text
app/repositories/company_vault_loader.py
```

Tugas:
- Baca `company_vault/lq45/*.md`
- Parse frontmatter:
  - `ticker`
  - `name`
  - `sektor`
  - `subsektor`
  - `komoditas`
  - `tag`
- Ambil body markdown sebagai profile text.

### 2. Merge dengan company universe DB
Sekarang:
```python
companies = company_universe(conn)
```

Nanti:
```python
companies = enrich_companies_with_vault(company_universe(conn))
```

### 3. Update prompt AI
Dari:
```text
- BBCA: Bank Central Asia Tbk
```

Menjadi:
```text
- BBCA: Bank Central Asia Tbk
  Sektor: Perbankan
  Subsektor: Bank Swasta Besar
  Komoditas: []
  Tag: bank-transaksi, kredit-korporasi, CASA
  Profil: Bank swasta besar dengan fokus transaksi, kredit konsumer...
```

## Output phase 1
- Impact worker tetap 1 tahap.
- Tapi AI punya konteks lebih kaya.
- Schema DB belum berubah.

## Risiko
- Kalau vault makin banyak dan panjang, prompt makin mahal.
- Masih belum scalable untuk semua saham.

## Cocok untuk
- LQ45 dulu.
- Validasi kualitas hasil AI sebelum bikin retrieval.

---

# Phase 2 — Hash Versioning Vault

Tujuan: **sistem tahu vault mana yang berubah.**

## Yang dibangun

### 1. Table baru `company_profiles`
Contoh schema:
```sql
company_profiles (
  ticker text primary key,
  name text,
  sector text,
  subsector text,
  commodities text[],
  tags text[],
  compact_profile text,
  full_profile text,
  profile_hash text not null,
  profile_version integer not null default 1,
  source_path text,
  last_indexed_at timestamptz not null default now()
)
```

### 2. Indexer
Module:
```text
app/services/company_profile_indexer.py
```

Tugas:
- Scan `company_vault/**/*.md`
- Hitung hash isi file
- Cek DB:
  - kalau hash sama → skip
  - kalau hash beda → update profile + naikkan version
  - kalau ticker baru → insert

### 3. Worker startup indexing
Di awal `news_impact_worker`:
```python
ensure_company_profiles_indexed(conn)
```

## Output phase 2
- Vault bisa diupdate kapan saja.
- Sistem otomatis tahu file berubah.
- Artikel baru akan pakai profile terbaru.
- Belum pakai embedding/vector.

## Risiko
- Masih retrieval sederhana / prompt bisa besar.
- Tapi fondasinya sudah siap untuk vector.

## Cocok untuk
- Vault mulai banyak.
- Kamu sering edit isi file MD.

---

# Phase 3 — Two-Stage Impact Analysis

Tujuan: **hemat token AI.**

## Flow baru

```text
Artikel
  ↓
Stage A: Candidate Selection
  ↓
Top 10-15 ticker kandidat
  ↓
Stage B: Final Impact Analysis
  ↓
affected_tickers
```

## Stage A
Input:
- Artikel
- Semua company compact profile super pendek

Output:
```json
{
  "candidate_tickers": ["ANTM", "MDKA", "BBCA"]
}
```

## Stage B
Input:
- Artikel
- Full vault hanya untuk kandidat

Output:
```json
{
  "affected_tickers": ["ANTM", "MDKA"],
  "confidence": 0.84,
  "reasoning": "..."
}
```

## Yang dibangun
- `select_candidate_tickers()`
- `analyze_article_impact_final()`
- Update worker supaya 2 tahap.

## Output phase 3
- Token jauh lebih hemat.
- AI tidak baca full vault semua saham.
- Reasoning lebih fokus.

## Risiko
- Kalau Stage A gagal memilih kandidat, Stage B tidak akan menemukan saham yang benar.
- Perlu fallback, misal:
  - selalu tambah ticker yang disebut eksplisit di artikel
  - always include top sector match
  - kalau Stage A confidence rendah, naikkan top_k

## Cocok untuk
- Vault 100+ saham.
- Artikel harian mulai banyak.

---

# Phase 4 — Retrieval Tanpa AI untuk Kandidat Awal

Tujuan: **mengurangi biaya Stage A.**

Di phase 3, Stage A masih pakai AI. Di phase 4, kandidat awal dipilih lokal dulu.

## Opsi retrieval sederhana

### 1. Keyword retrieval
Dari vault:
- ticker
- sektor
- subsektor
- komoditas
- tag
- ringkasan bisnis

Buat scoring sederhana:
```text
score = keyword_overlap(article, company_profile)
```

Contoh:
- Artikel mengandung "emas" → ANTM, MDKA, AMMN, BRMS
- Artikel mengandung "suku bunga" → BBCA, BBRI, BMRI, BBNI
- Artikel mengandung "ritel" → AMRT, MAPI, MAPA, ACES

## Yang dibangun
```text
app/services/impact_retriever.py
```

Fungsi:
```python
retrieve_candidate_companies(article, profiles, top_k=15)
```

## Flow
```text
Artikel
  ↓
Keyword retrieval lokal
  ↓
Top 15 kandidat
  ↓
AI final analysis
```

## Output phase 4
- Biaya AI turun lagi.
- Cloud AI cuma 1 call per artikel.
- Bisa jalan tanpa vector DB.

## Risiko
- Keyword retrieval bisa miss sinonim.
  - "logam mulia" vs "emas"
  - "daya beli" vs "konsumsi rumah tangga"
- Bisa ditingkatkan dengan synonym dictionary.

## Cocok untuk
- MVP hemat biaya.
- Belum mau install pgvector/embedding.

---

# Phase 5 — Vector DB / Embedding Retrieval

Tujuan: **scalable untuk semua saham IDX.**

## Flow

```text
Vault MD
  ↓
Generate embedding lokal
  ↓
company_profiles.embedding
  ↓
Artikel baru
  ↓
Generate article embedding
  ↓
Vector search top 20
  ↓
AI final analysis
```

## Pilihan stack

### Pilihan paling natural
Karena project sudah PostgreSQL:
```text
PostgreSQL + pgvector
```

Table:
```sql
company_profiles (
  ticker text primary key,
  ...
  embedding vector(384)
)
```

Atau jika embedding model dimensi beda:
- `vector(384)`
- `vector(768)`
- `vector(1024)`

Tergantung model embedding.

## Embedding model lokal
Pilihan ringan:
- `sentence-transformers/all-MiniLM-L6-v2` — ringan, cepat, cukup bagus.
- `BAAI/bge-m3` — lebih kuat multilingual, cocok Indo/English.
- `intfloat/multilingual-e5-base` — multilingual bagus.

## Output phase 5
- Candidate retrieval stabil meski 900+ saham.
- Biaya AI hampir flat.
- Tidak perlu kirim semua saham ke AI.

## Risiko
- Butuh dependency embedding.
- Butuh setup pgvector.
- Perlu re-index saat vault berubah.

## Cocok untuk
- Semua emiten IDX.
- Berita harian banyak.
- Ingin biaya AI rendah dan performa bagus.

---

# Phase 6 — Reranker Lokal

Tujuan: **akurasi kandidat lebih tinggi.**

Vector search bisa dapat top 30, lalu reranker lokal urutkan lebih akurat.

Flow:
```text
Vector search top 30
  ↓
Local reranker
  ↓
Top 8-12
  ↓
AI final analysis
```

Model reranker:
- `BAAI/bge-reranker-v2-m3`
- `jina-reranker-v2-base-multilingual`

Kelebihan:
- Mengurangi miss.
- AI final lebih fokus.
- Masih lokal, tidak ada biaya cloud.

Kekurangan:
- Tambah dependency dan compute.

---

# Phase 7 — Auditability & Re-analysis

Tujuan: **hasil impact bisa diaudit dan diulang kalau vault berubah.**

## Tambah kolom/table
Di `article_impact_analysis`:
```sql
candidate_tickers text[],
profile_versions jsonb,
evidence jsonb,
impact_type text,
analysis_version text
```

Contoh:
```json
{
  "ANTM": 4,
  "MDKA": 2
}
```

Jadi kalau `ANTM.md` berubah dari version 4 ke 5, kita tahu:
- analysis mana yang dibuat dengan profile lama
- mana yang perlu re-run

## Output phase 7
- Hasil bisa diaudit.
- Kalau vault berubah signifikan, artikel lama bisa dianalisis ulang.
- Reasoning bisa lebih transparan.

---

# Rekomendasi urutan implementasi

Kalau mau praktis dan cepat:

## Sprint 1
**Phase 1 + Phase 2**
- Loader MD
- Enrich prompt
- Hash/versioning ke DB

## Sprint 2
**Phase 4**
- Keyword retrieval lokal
- AI final analysis hanya untuk kandidat

## Sprint 3
**Phase 5**
- pgvector + embedding lokal
- Replace keyword retrieval dengan vector retrieval

## Sprint 4
**Phase 6 + 7**
- Reranker
- Evidence/profile_version audit
- Re-analysis mechanism

---

# Urutan minimal paling masuk akal untuk sekarang

Karena vault baru LQ45:

1. **Phase 1** dulu: AI pakai vault MD.
2. **Phase 2**: simpan profile hash/version.
3. **Phase 4**: keyword retrieval sederhana.
4. Baru nanti **Phase 5** kalau vault sudah ratusan saham.

Menurut saya jangan langsung vector DB hari ini. Lebih baik pastikan dulu format vault dan hasil analisisnya cocok.