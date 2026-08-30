"""Phase 5 service: chunking profil emiten + embedding lokal + sync ke company_profile_chunks."""

import hashlib
from dataclasses import dataclass, field
from typing import Any

from app.core.config import EmbeddingConfig

CHUNK_TYPE_BY_HEADING = [
    ("ringkasan bisnis", "overview"),
    ("sumber pendapatan", "revenue"),
    ("driver bisnis", "driver"),
    ("risiko", "risk"),
    ("sensitif", "sensitivity"),
]

VALID_CHUNK_TYPES = {"overview", "revenue", "driver", "risk", "commodity", "sensitivity"}

_model_cache: dict[str, Any] = {}


@dataclass(frozen=True)
class ChunkTask:
    ticker: str
    profile_version: int
    chunk_type: str
    content: str
    content_hash: str


@dataclass(frozen=True)
class SyncPlan:
    tasks: list[ChunkTask] = field(default_factory=list)
    unchanged: int = 0
    total_chunks: int = 0


def get_embedding_model(config: EmbeddingConfig):
    """Lazy-load SentenceTransformer sekali per proses."""
    if config.model not in _model_cache:
        from sentence_transformers import SentenceTransformer

        _model_cache[config.model] = SentenceTransformer(config.model)
    return _model_cache[config.model]


def _is_e5(model_name: str) -> bool:
    return "e5" in model_name.lower()


def embed_passages(config: EmbeddingConfig, texts: list[str]) -> list[list[float]]:
    """Embed dokumen/profil. E5 butuh prefix 'passage: '. Output sudah L2-normalized."""
    model = get_embedding_model(config)
    prefix = "passage: " if _is_e5(config.model) else ""
    vectors = model.encode(
        [prefix + text for text in texts],
        batch_size=config.batch_size,
        normalize_embeddings=True,
    )
    return [[float(x) for x in vector] for vector in vectors]


def embed_query(config: EmbeddingConfig, text: str) -> list[float]:
    """Embed query artikel. E5 butuh prefix 'query: '."""
    model = get_embedding_model(config)
    prefix = "query: " if _is_e5(config.model) else ""
    vector = model.encode([prefix + text], normalize_embeddings=True)[0]
    return [float(x) for x in vector]


def _heading_to_chunk_type(heading: str) -> str:
    lowered = heading.strip().lower()
    for prefix, chunk_type in CHUNK_TYPE_BY_HEADING:
        if lowered.startswith(prefix):
            return chunk_type
    return "overview"


def build_profile_chunks(row: dict) -> list[tuple[str, str]]:
    """Split full_profile per heading menjadi (chunk_type, content), plus chunk komoditas dari metadata."""
    body = row.get("full_profile") or ""
    chunks: list[tuple[str, str]] = []
    section: str | None = None
    lines: list[str] = []

    def flush() -> None:
        if section and lines:
            chunks.append((_heading_to_chunk_type(section), f"{section}\n" + "\n".join(lines)))

    for line in body.splitlines():
        if line.startswith("#"):
            flush()
            section = line.lstrip("# ").strip()
            lines = []
        elif line.strip():
            lines.append(line.strip())
    flush()

    commodities = row.get("commodities") or []
    if commodities:
        chunks.append(("commodity", "Komoditas: " + ", ".join(str(c) for c in commodities)))

    # Dedupe per chunk_type (simpan kemunculan pertama) dan validasi nilai enum.
    seen: set[str] = set()
    result: list[tuple[str, str]] = []
    for chunk_type, content in chunks:
        if chunk_type in seen or chunk_type not in VALID_CHUNK_TYPES or not content.strip():
            continue
        seen.add(chunk_type)
        result.append((chunk_type, content.strip()))
    return result


def chunk_content_hash(chunk_type: str, content: str) -> str:
    payload = f"{chunk_type}\n{content}"
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def load_existing_chunks(conn, model_name: str) -> dict[tuple[str, str], dict]:
    """Snapshot chunk existing per (ticker, chunk_type) untuk satu embedding model."""
    with conn.cursor() as cur:
        cur.execute(
            """
            select id, ticker, chunk_type, profile_version, content_hash
            from company_profile_chunks
            where model_name = %s
            """,
            (model_name,),
        )
        return {
            (row["ticker"], row["chunk_type"]): dict(row)
            for row in cur.fetchall()
        }


def plan_chunk_sync(profiles: list[dict], existing: dict[tuple[str, str], dict]) -> SyncPlan:
    """Fase murni (tanpa DB/model): tentukan chunk mana yang perlu re-embed."""
    tasks: list[ChunkTask] = []
    unchanged = 0
    total = 0
    for profile in profiles:
        ticker = str(profile["ticker"]).strip().upper()
        version = int(profile["profile_version"])
        for chunk_type, content in build_profile_chunks(profile):
            total += 1
            content_hash = chunk_content_hash(chunk_type, content)
            prior = existing.get((ticker, chunk_type))
            if (
                prior
                and prior["content_hash"] == content_hash
                and prior["profile_version"] == version
            ):
                unchanged += 1
                continue
            tasks.append(ChunkTask(ticker, version, chunk_type, content, content_hash))
    return SyncPlan(tasks=tasks, unchanged=unchanged, total_chunks=total)


UPSERT_CHUNK_SQL = """
insert into company_profile_chunks (
    ticker, profile_version, chunk_type, content, embedding, content_hash, model_name
) values (%s, %s, %s, %s, %s, %s, %s)
on conflict (ticker, profile_version, chunk_type, model_name) do update set
    content = excluded.content,
    embedding = excluded.embedding,
    content_hash = excluded.content_hash,
    embedded_at = now()
"""


def write_chunk_sync(
    conn,
    profiles: list[dict],
    plan: SyncPlan,
    vectors: list[list[float]],
    model_name: str,
    existing: dict[tuple[str, str], dict],
) -> None:
    """Fase tulis: jalankan pada koneksi segar setelah embedding selesai."""
    assert len(vectors) == len(plan.tasks)
    with conn.cursor() as cur:
        for task, vector in zip(plan.tasks, vectors):
            cur.execute(
                UPSERT_CHUNK_SQL,
                (
                    task.ticker,
                    task.profile_version,
                    task.chunk_type,
                    task.content,
                    vector,
                    task.content_hash,
                    model_name,
                ),
            )

        # Purge chunk milik ticker yang sudah keluar vault atau versinya sudah tua.
        current_by_ticker = {str(p["ticker"]).strip().upper(): int(p["profile_version"]) for p in profiles}
        seen_ids: set[int] = set()
        for (_ticker, _chunk_type), row in existing.items():
            if row["id"] in seen_ids:
                continue
            seen_ids.add(row["id"])
            current_version = current_by_ticker.get(str(row["ticker"]).strip().upper())
            if current_version is None or row["profile_version"] != current_version:
                cur.execute("delete from company_profile_chunks where id = %s", (row["id"],))


def sync_profile_chunks(conn, profiles: list[dict], config: EmbeddingConfig) -> dict[str, int]:
    """Sinkronisasi satu-koneksi (dipakai test/kasus kecil); worker memakai plan/write terpisah."""
    existing = load_existing_chunks(conn, config.model)
    plan = plan_chunk_sync(profiles, existing)
    vectors = embed_passages(config, [task.content for task in plan.tasks]) if plan.tasks else []
    write_chunk_sync(conn, profiles, plan, vectors, config.model, existing)
    return {
        "embedded": len(plan.tasks),
        "unchanged": plan.unchanged,
        "total_chunks": plan.total_chunks,
    }
