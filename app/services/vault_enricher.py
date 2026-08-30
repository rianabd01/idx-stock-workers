"""Vault enricher: isi skeleton emiten via web search + Jina fetch + AI terstruktur.

Alur per emiten:
  1. Cari sumber referensi via Jina Search API (s.jina.ai).
  2. Fetch konten terbaik via Jina Reader.
  3. AI susun profil terstruktur sesuai section vault.
  4. Tulis ulang file Markdown (frontmatter lama dipertahankan, sektor diisi).
"""

import json
import re
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import quote_plus

from curl_cffi import requests as curl_requests

from app.core.config import AIConfig, JinaConfig
from app.services.news_analyzer import _message_content, _parse_response_json

SEARCH_TIMEOUT = 30
MAX_SEARCH_RESULTS = 5
MAX_SOURCE_CHARS = 9000
AI_MAX_ATTEMPTS = 3

REQUIRED_SECTIONS = [
    "Ringkasan bisnis",
    "Sumber pendapatan utama",
    "Driver bisnis",
    "Risiko utama",
    "Sensitif terhadap berita",
]

ENRICH_SYSTEM_PROMPT = f"""Kamu analis riset ekuitas Indonesia. Berdasarkan sumber yang diberikan,
susun profil bisnis emiten dalam bahasa Indonesia. Balas HANYA JSON valid dengan format:
{{
  "sektor": "<nama sektor ringkas>",
  "subsektor": "<subsektor/segmen>",
  "komoditas": ["..."],
  "tag": ["tag-singkat", "..."],
  "sections": {{
    "Ringkasan bisnis": "2-4 kalimat",
    "Sumber pendapatan utama": "- poin\\n- poin",
    "Driver bisnis": "- poin\\n- poin",
    "Risiko utama": "- poin\\n- poin",
    "Sensitif terhadap berita": "- poin\\n- poin"
  }}
}}
Section wajib: {", ".join(REQUIRED_SECTIONS)}. Jika sumber tidak cukup, tulis nilai paling umum yang akurat dan jangan mengarang angka."""


@dataclass(frozen=True)
class EnrichResult:
    ticker: str
    ok: bool
    error: str | None = None


def search_company_sources(jina_config: JinaConfig, ticker: str, name: str) -> list[dict]:
    """Cari URL referensi via Jina Search API (s.jina.ai), dengan query cadangan."""
    queries = [
        f"{ticker} {name} profil perusahaan bisnis",
        f"{ticker}.JK {name} saham Indonesia",
        f"{ticker} IDX company profile",
    ]
    results: list[dict] = []
    seen_urls: set[str] = set()
    for query in queries:
        try:
            response = curl_requests.get(
                f"https://s.jina.ai/{quote_plus(query)}",
                headers={
                    "Authorization": f"Bearer {jina_config.api_key}",
                    "Accept": "application/json",
                    "X-Respond-With": "no-content",
                },
                timeout=SEARCH_TIMEOUT,
            )
            response.raise_for_status()
        except Exception:
            continue
        payload = _parse_response_json(response.text)
        for item in payload.get("data") or []:
            url = str(item.get("url") or "").strip()
            if not url.startswith("http") or url in seen_urls:
                continue
            seen_urls.add(url)
            results.append({"url": url, "title": str(item.get("title") or "").strip()})
        if len(results) >= MAX_SEARCH_RESULTS:
            break
    return results[:MAX_SEARCH_RESULTS]


def gather_source_material(jina_config: JinaConfig, urls: list[str]) -> str:
    """Fetch beberapa kandidat URL via Jina, gabungkan jadi bahan sumber."""
    from app.services.news_analyzer import clean_markdown, fetch_article_content

    parts: list[str] = []
    for url in urls[:3]:
        fetched = fetch_article_content(jina_config, url)
        if not fetched or not fetched.get("content"):
            continue
        text = clean_markdown(fetched["content"])[:MAX_SOURCE_CHARS]
        parts.append(f"SUMBER: {url}\n{text}")
    return "\n\n".join(parts)


def parse_enrich_response(text: str) -> dict:
    data = _parse_enrich_json(_extract_json_object(text))
    sections = data.get("sections") or {}
    return {
        "sektor": str(data.get("sektor") or "-").strip() or "-",
        "subsektor": str(data.get("subsektor") or "-").strip() or "-",
        "komoditas": [str(c).strip() for c in data.get("komoditas") or [] if str(c).strip()],
        "tag": [str(t).strip() for t in data.get("tag") or [] if str(t).strip()],
        "sections": {
            key: str(sections.get(key) or "").strip()
            for key in REQUIRED_SECTIONS
        },
    }


def _extract_json_object(text: str) -> dict:
    """Toleran terhadap fence / newline literal dalam string (strict=False)."""
    text = text.strip()
    if not text:
        raise ValueError("respons AI kosong")
    try:
        return json.loads(text, strict=False)
    except json.JSONDecodeError:
        pass
    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end <= start:
        raise ValueError(f"tidak ada objek JSON di respons (len={len(text)})")
    return json.loads(text[start : end + 1], strict=False)


def _parse_enrich_json(data: dict) -> dict:
    """Toleransi skema: model kadang pakai key alternatif untuk sections."""
    sections = dict(data.get("sections") or {})
    aliases = {
        "Ringkasan bisnis": ["ringkasan_bisnis", "ringkasan"],
        "Sumber pendapatan utama": ["sumber_pendapatan_utama", "sumber_pendapatan"],
        "Driver bisnis": ["driver_bisnis", "driver"],
        "Risiko utama": ["risiko_utama", "risiko"],
        "Sensitif terhadap berita": ["sensitif_terhadap_berita", "sensitif"],
    }
    for canonical, keys in aliases.items():
        if not sections.get(canonical):
            for alt in keys:
                value = data.get(alt) or sections.get(alt)
                if value:
                    sections[canonical] = str(value)
                    break
    return {**data, "sections": sections}


def build_profile_via_ai(config: AIConfig, ticker: str, name: str, source_material: str) -> dict:
    """Panggil AI dengan retry — model lokal kadang balikin body kosong/flaky."""
    payload = {
        "model": config.model,
        "messages": [
            {"role": "system", "content": ENRICH_SYSTEM_PROMPT},
            {
                "role": "user",
                "content": f"Emiten: {ticker} - {name}\n\nBahan sumber:\n{source_material[:12000]}",
            },
        ],
        "temperature": 0,
    }
    headers = {"Authorization": f"Bearer {config.api_key}", "Content-Type": "application/json"}
    last_error: Exception | None = None
    for attempt in range(AI_MAX_ATTEMPTS):
        try:
            response = curl_requests.post(
                f"{config.base_url}/chat/completions",
                json=payload,
                headers=headers,
                timeout=config.timeout_seconds,
            )
            response.raise_for_status()
            return parse_enrich_response(_message_content(_parse_response_json(response.text)))
        except (ValueError, json.JSONDecodeError) as exc:
            last_error = exc
    raise RuntimeError(f"AI gagal setelah {AI_MAX_ATTEMPTS} percobaan: {last_error}")


def render_vault_markdown(meta: dict, ticker: str, name: str, profile: dict) -> str:
    """Susun file Markdown lengkap dari hasil enrichment."""
    commodities = ", ".join(profile["komoditas"])
    tags = ", ".join(profile["tag"]) if profile["tag"] else ""
    tag_line = f"tag: [{tags}]" if tags else "tag: []"
    commodity_line = f"komoditas: [{commodities}]" if commodities else "komoditas: []"

    body_parts = [f"# Ringkasan bisnis\n{profile['sections']['Ringkasan bisnis']}"]
    for key in REQUIRED_SECTIONS[1:]:
        body_parts.append(f"# {key}\n{profile['sections'][key]}")

    return (
        "---\n"
        f"ticker: {ticker}\n"
        f"name: {name}\n"
        f"sektor: {profile['sektor']}\n"
        f"subsektor: {profile['subsektor']}\n"
        f"{commodity_line}\n"
        f"{tag_line}\n"
        "---\n\n" + "\n\n".join(body_parts) + "\n"
    )


def is_skeleton(path: Path) -> bool:
    """Skeleton ditandai body yang masih memuat placeholder 'Belum tersedia.'"""
    text = path.read_text(encoding="utf-8")
    return "Belum tersedia." in text


def enrich_vault_file(
    ai_config: AIConfig,
    jina_config: JinaConfig,
    vault_path: Path,
) -> EnrichResult:
    meta_text = vault_path.read_text(encoding="utf-8")
    ticker_match = re.search(r"^ticker:\s*(\S+)", meta_text, re.MULTILINE)
    name_match = re.search(r"^name:\s*(.+)$", meta_text, re.MULTILINE)
    if not ticker_match or not name_match:
        return EnrichResult(vault_path.stem, False, "frontmatter tidak lengkap")
    ticker = ticker_match.group(1).strip().upper()
    name = name_match.group(1).strip()

    sources = search_company_sources(jina_config, ticker, name)
    if not sources:
        return EnrichResult(ticker, False, "tidak ada hasil pencarian")
    material = gather_source_material(jina_config, [s["url"] for s in sources])
    if not material.strip():
        return EnrichResult(ticker, False, "gagal fetch semua sumber")

    profile = build_profile_via_ai(ai_config, ticker, name, material)
    filled_sections = sum(1 for v in profile["sections"].values() if v and "belum tersedia" not in v.lower())
    if filled_sections < len(REQUIRED_SECTIONS):
        return EnrichResult(ticker, False, f"section tidak lengkap ({filled_sections}/{len(REQUIRED_SECTIONS)})")

    vault_path.write_text(render_vault_markdown({}, ticker, name, profile), encoding="utf-8")
    return EnrichResult(ticker, True)


def find_skeletons(vault_dir: str | Path, limit: int) -> list[Path]:
    """Skeleton pertama secara alfabetis yang belum di-enrich."""
    skeletons = [
        p for p in sorted(Path(vault_dir).glob("*.md"))
        if is_skeleton(p)
    ]
    return skeletons[:limit]
