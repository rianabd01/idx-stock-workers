# Future Plan — Company Vault & Impact Analysis

README adalah kontrak operasional utama. Dokumen ini hanya mencatat gagasan yang belum diimplementasikan.

## Fondasi selesai

- Vault lokal LQ45 tersedia dan impact worker memperkaya company universe dari `app/knowledge/company_vault.py`.
- AI dibatasi pada ticker dalam company universe.
- Analisis masih satu tahap dan schema tetap dimiliki penuh oleh backend.

## Roadmap tersisa

### Hash dan versioning vault

Tambahkan migration di **idx-stock-backend** untuk `company_profiles`: ticker, metadata sektor/komoditas/tag, compact/full profile, profile hash/version, source path, dan waktu indexing. Workers memindai perubahan vault saat startup; hash sama dilewati, hash berubah menaikkan versi.

### Retrieval kandidat

Kurangi token sebelum analisis final:

1. MVP keyword scoring lokal dari ticker, nama, sektor, komoditas, tag, ringkasan bisnis, dan sinonim; selalu sertakan ticker yang disebut eksplisit.
2. Opsional two-stage AI untuk memilih 10–15 kandidat jika retrieval lokal belum cukup.
3. Untuk skala seluruh IDX, evaluasi pgvector dengan embedding multilingual lokal; kirim hanya kandidat teratas dan full profile terkait ke AI.
4. Tambahkan local reranker bila kualitas vector candidate membutuhkan peningkatan.

Model yang dapat dievaluasi: `BAAI/bge-m3`, `intfloat/multilingual-e5-base`, dan `BAAI/bge-reranker-v2-m3`.

### Audit dan re-analysis

Tambahkan candidate tickers, profile versions, evidence, impact type, dan analysis version agar hasil lama dapat ditemukan dan dijadwalkan ulang ketika profile berubah.

## Target alur

```text
Vault Markdown
  → hash/version profile
  → compact profile + keyword/vector index
Artikel baru
  → retrieval lokal top-K
  → load full vault kandidat
  → AI final impact analysis
  → article_impact_analysis dengan metadata audit
```

## Prinsip biaya dan ownership

- Hindari setiap artikel × seluruh emiten × full vault.
- Pertahankan deduplikasi/cache per `(article_id, model_name)`.
- Gunakan compact profile untuk retrieval dan full profile untuk reasoning final.
- Backend tetap satu-satunya pemilik DDL/Alembic; workers hanya mengonsumsi schema yang sudah dimigrasikan.
