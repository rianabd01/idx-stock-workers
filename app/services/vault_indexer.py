"""Vault indexer: parse Markdown vault, hitung profile_hash, upsert ke company_profiles."""

import hashlib
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

FRONTMATTER_PATTERN = re.compile(r"^---\s*\n(.*?)\n---\s*\n?", re.DOTALL)


@dataclass(frozen=True)
class VaultProfile:
    ticker: str
    company_name: str
    sector: str | None
    subsector: str | None
    commodities: list[str]
    tags: list[str]
    compact_profile: str
    full_profile: str
    source_path: str
    profile_hash: str


def _parse_scalar(value: str) -> Any:
    value = value.strip()
    if value.startswith("[") and value.endswith("]"):
        inner = value[1:-1].strip()
        if not inner:
            return []
        return [item.strip().strip("'\"") for item in inner.split(",") if item.strip()]
    return value.strip("'\"")


def parse_frontmatter(raw: str) -> tuple[dict[str, Any], str]:
    """Split Markdown menjadi (metadata frontmatter, body). Tanpa frontmatter -> ({}, raw)."""
    match = FRONTMATTER_PATTERN.match(raw)
    if not match:
        return {}, raw
    meta: dict[str, Any] = {}
    for line in match.group(1).splitlines():
        if ":" not in line or line.lstrip().startswith("#"):
            continue
        key, _, value = line.partition(":")
        meta[key.strip()] = _parse_scalar(value)
    return meta, raw[match.end():]


def compute_profile_hash(meta: dict[str, Any], body: str) -> str:
    """sha256 dari frontmatter ternormalisasi + body (whitespace trailing diabaikan)."""
    normalized_body = "\n".join(line.rstrip() for line in body.strip().splitlines())
    payload = dict(meta)
    payload["__body__"] = normalized_body
    canonical = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def build_compact_profile(meta: dict[str, Any], body: str) -> str:
    """Profil ringkas: identitas + baris pertama tiap section. Dipakai untuk retrieval."""
    sections: list[tuple[str, str]] = []
    heading: str | None = None
    lines: list[str] = []
    for line in body.splitlines():
        if line.startswith("#"):
            if heading and lines:
                sections.append((heading, lines[0]))
            heading = line.lstrip("#").strip()
            lines = []
        elif line.strip():
            lines.append(line.strip())
    if heading and lines:
        sections.append((heading, lines[0]))

    parts = [
        f"{meta.get('ticker', '')} - {meta.get('name', '')}",
        f"Sektor: {meta.get('sektor', '-')} | Subsektor: {meta.get('subsektor', '-')}",
        f"Komoditas: {', '.join(meta.get('komoditas', []) or []) or '-'}"
        f" | Tag: {', '.join(meta.get('tag', []) or []) or '-'}",
    ]
    parts.extend(f"{section_heading}: {first_line}" for section_heading, first_line in sections)
    return "\n".join(parts)[:1500]


def _as_str_list(value: Any) -> list[str]:
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    text = str(value or "").strip()
    return [text] if text else []


def load_vault_profiles(vault_dirs: list[str | Path] | str | Path) -> list[VaultProfile]:
    """Load semua *.md dari beberapa vault dir.

    Kalau satu ticker muncul di lebih dari satu dir, entri pertama dalam urutan
    daftar yang menang — taruh dir paling kaya konten di depan.
    """
    if isinstance(vault_dirs, (str, Path)):
        vault_dirs = [vault_dirs]
    profiles: list[VaultProfile] = []
    seen: set[str] = set()
    for vault_dir in vault_dirs:
        for path in sorted(Path(vault_dir).glob("*.md")):
            meta, body = parse_frontmatter(path.read_text(encoding="utf-8"))
            ticker = str(meta.get("ticker", "")).strip().upper()
            name = str(meta.get("name", "")).strip()
            if not ticker or not name or not body.strip() or ticker in seen:
                continue
            seen.add(ticker)
            profiles.append(
            VaultProfile(
                ticker=ticker,
                company_name=name,
                sector=str(meta.get("sektor", "")).strip() or None,
                subsector=str(meta.get("subsektor", "")).strip() or None,
                commodities=_as_str_list(meta.get("komoditas")),
                tags=_as_str_list(meta.get("tag")),
                compact_profile=build_compact_profile(meta, body),
                full_profile=body.strip(),
                source_path=str(path),
                profile_hash=compute_profile_hash(meta, body),
            )
        )
    return profiles


UPSERT_SQL = """
insert into company_profiles (
    ticker, company_name, sector, subsector, commodities, tags,
    compact_profile, full_profile, source_path, profile_hash
) values (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
on conflict (ticker) do update set
    company_name = excluded.company_name,
    sector = excluded.sector,
    subsector = excluded.subsector,
    commodities = excluded.commodities,
    tags = excluded.tags,
    compact_profile = excluded.compact_profile,
    full_profile = excluded.full_profile,
    source_path = excluded.source_path,
    profile_hash = excluded.profile_hash,
    profile_version = company_profiles.profile_version + 1,
    indexed_at = now(),
    updated_at = now()
"""


def sync_profiles(conn, profiles: list[VaultProfile]) -> dict[str, int]:
    """Upsert ke company_profiles. Hash sama -> skip total (version & indexed_at tak tersentuh)."""
    with conn.cursor() as cur:
        cur.execute("select ticker, profile_hash from company_profiles")
        existing = {row["ticker"]: row["profile_hash"] for row in cur.fetchall()}
        counts = {"inserted": 0, "updated": 0, "skipped": 0}
        for profile in profiles:
            current_hash = existing.get(profile.ticker)
            if current_hash == profile.profile_hash:
                counts["skipped"] += 1
                continue
            cur.execute(
                UPSERT_SQL,
                (
                    profile.ticker,
                    profile.company_name,
                    profile.sector,
                    profile.subsector,
                    profile.commodities,
                    profile.tags,
                    profile.compact_profile,
                    profile.full_profile,
                    profile.source_path,
                    profile.profile_hash,
                ),
            )
            counts["inserted" if current_hash is None else "updated"] += 1
    return counts
