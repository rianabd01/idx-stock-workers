"""Impact analysis service: keyword retrieval kandidat lokal, lalu AI final reasoning."""

import re
from dataclasses import dataclass

from curl_cffi import requests as curl_requests

from app.services.news_analyzer import _message_content, _parse_response_json, clean_markdown
from app.core.config import AIConfig

ANALYSIS_VERSION = "hybrid-v2"
DEFAULT_TOP_K = 15
MIN_CANDIDATE_SCORE = 2.0
EXPLICIT_TICKER_SCORE = 10.0
NAME_PHRASE_SCORE = 5.0
NAME_TOKEN_SCORE = 1.5
SECTOR_SCORE = 2.0
SUBSECTOR_SCORE = 1.5
COMMODITY_SCORE = 3.0
TAG_SCORE = 2.0
PROFILE_KEYWORD_SCORE = 0.25
PROFILE_KEYWORD_CAP = 2.0
SCAN_CONTENT_CHARS = 6000
PROFILE_CONTEXT_MAX_CHARS = 1500

STOPWORDS = {
    "yang", "dan", "dari", "dengan", "untuk", "pada", "adalah", "ini", "itu", "di", "ke",
    "akan", "tidak", "dalam", "the", "and", "of", "pt", "tbk", "persero", "indonesia",
    "persen", "rupiah", "company", "profil", "ringkasan", "sumber", "pendapatan",
}

@dataclass(frozen=True)
class Candidate:
    ticker: str
    company_name: str
    score: float
    matched_terms: tuple[str, ...]

def _distinctive_tokens(text: str, limit: int = 60) -> list[str]:
    tokens: list[str] = []
    for token in re.findall(r"[a-z]{4,}", (text or "").lower()):
        if token in STOPWORDS or token in tokens:
            continue
        tokens.append(token)
        if len(tokens) >= limit:
            break
    return tokens

def _has_phrase(haystack: str, phrase: str) -> bool:
    phrase = (phrase or "").strip().lower()
    if not phrase:
        return False
    return re.search(rf"\b{re.escape(phrase)}\b", haystack) is not None

def retrieve_candidates(title: str, content: str, profiles: list[dict], top_k: int = DEFAULT_TOP_K) -> list[Candidate]:
    """Scoring deterministik: ticker eksplisit > nama > komoditas/tags > sektor > kata profil."""
    cleaned = clean_markdown(f"{title or ''}\n{(content or '')[:SCAN_CONTENT_CHARS]}")
    lowered = cleaned.lower()

    candidates: list[Candidate] = []
    for row in profiles:
        ticker = str(row["ticker"]).strip().upper()
        if not ticker:
            continue
        score = 0.0
        terms: list[str] = []

        if re.search(rf"\b{re.escape(ticker)}\b", cleaned):
            score += EXPLICIT_TICKER_SCORE
            terms.append(ticker)

        name = str(row.get("company_name") or "").strip()
        name_lower = name.lower()
        if name and _has_phrase(lowered, name_lower):
            score += NAME_PHRASE_SCORE
            terms.append(name_lower)
        for token in _distinctive_tokens(name, limit=8):
            if _has_phrase(lowered, token):
                score += NAME_TOKEN_SCORE
                terms.append(token)

        for commodity in row.get("commodities") or []:
            if _has_phrase(lowered, str(commodity)):
                score += COMMODITY_SCORE
                terms.append(str(commodity).lower())
        for tag in row.get("tags") or []:
            if _has_phrase(lowered, str(tag)):
                score += TAG_SCORE
                terms.append(str(tag).lower())
        if _has_phrase(lowered, str(row.get("sector") or "")):
            score += SECTOR_SCORE
            terms.append(str(row["sector"]).lower())
        if _has_phrase(lowered, str(row.get("subsector") or "")):
            score += SUBSECTOR_SCORE
            terms.append(str(row["subsector"]).lower())

        keyword_hits = sum(1 for kw in _distinctive_tokens(row.get("compact_profile") or "", limit=60) if _has_phrase(lowered, kw))
        if keyword_hits:
            score += min(keyword_hits * PROFILE_KEYWORD_SCORE, PROFILE_KEYWORD_CAP)
            terms.append(f"profile-keywords:{keyword_hits}")

        if ticker in terms or score >= MIN_CANDIDATE_SCORE:
            candidates.append(Candidate(ticker=ticker, company_name=name, score=round(score, 2), matched_terms=tuple(dict.fromkeys(terms))))

    candidates.sort(key=lambda c: (-c.score, c.ticker))
    return candidates[:top_k]


# --- Vector retrieval (Phase 5) --------------------------------------------

VECTOR_TOP_K = 10
VECTOR_MIN_SIMILARITY = 0.50
VECTOR_SCORE_SCALE = 8.0  # cosine ~1.0 setara bobot skor keyword tinggi saat merge


def _cosine(a: list[float], b: list[float]) -> float:
    return sum(x * y for x, y in zip(a, b))  # kedua vektor sudah L2-normalized


def retrieve_vector_candidates(
    title: str,
    content: str,
    chunks: list[dict],
    query_embedding: list[float],
    top_k: int = VECTOR_TOP_K,
) -> dict[str, tuple[float, str]]:
    """Cosine antara query artikel dan tiap chunk. Return {ticker: (best_similarity, chunk_type)}."""
    query_text = clean_markdown(f"{title or ''}\n{(content or '')[:2000]}")[:1500]
    if not query_text or not chunks:
        return {}

    scores: dict[str, tuple[float, str]] = {}
    for chunk in chunks:
        similarity = _cosine(query_embedding, chunk["embedding"])
        ticker = str(chunk["ticker"]).strip().upper()
        best = scores.get(ticker)
        if best is None or similarity > best[0]:
            scores[ticker] = (similarity, chunk["chunk_type"])
    return {
        ticker: (sim, ctype)
        for ticker, (sim, ctype) in scores.items()
        if sim >= VECTOR_MIN_SIMILARITY
    }


def merge_candidates(
    keyword: list[Candidate],
    vector_scores: dict[str, tuple[float, str]],
) -> list[Candidate]:
    """Union kandidat keyword ∪ vector; skor vector dikonversi ke skala keyword.

    Kandidat yang muncul di dua-duanya mendapat bonus kecil karena sinyal ganda.
    """
    merged: dict[str, Candidate] = {c.ticker: c for c in keyword}
    for ticker, (similarity, chunk_type) in vector_scores.items():
        vector_score = round(similarity * VECTOR_SCORE_SCALE, 2)
        existing = merged.get(ticker)
        if existing:
            bonus = min(similarity * 2.0, 2.0)
            merged[ticker] = Candidate(
                ticker=ticker,
                company_name=existing.company_name,
                score=round(existing.score + bonus, 2),
                matched_terms=existing.matched_terms + (f"vector:{chunk_type}:{vector_score}",),
            )
        else:
            merged[ticker] = Candidate(
                ticker=ticker,
                company_name="",
                score=vector_score,
                matched_terms=(f"vector:{chunk_type}:{vector_score}",),
            )
    result = sorted(merged.values(), key=lambda c: (-c.score, c.ticker))
    return result[:DEFAULT_TOP_K]


# --- Peer expansion ---------------------------------------------------------

PEER_TRIGGER_SCORE = 8.0  # hanya kandidat kuat yang menarik peer-nya masuk
PEER_BASE_SCORE = 2.5     # skor dasar emiten peer yang baru masuk
PEER_MAX_TOTAL = 20       # batas atas kandidat setelah expansion (plan: 10-20)

_NO_SECTOR_VALUES = {"", "-", "n/a", "na", "null", "none", "unknown", "belum tersedia"}


def _clean_sector(value: object) -> str:
    sector = str(value or "").strip().lower()
    return "" if sector in _NO_SECTOR_VALUES else sector


def expand_peers(candidates: list[Candidate], profiles: list[dict]) -> list[Candidate]:
    """Teman se-sector / se-komoditas dari kandidat kuat ikut jadi kandidat.

    Rationale: berita suku bunga memengaruhi seluruh bank, berita emas menggerakkan
    semua produsen emas — walau retrieval literal/semantik melewatkan sebagian.
    """
    profile_by_ticker = {str(p["ticker"]).strip().upper(): p for p in profiles}
    merged: dict[str, Candidate] = {c.ticker: c for c in candidates}
    seen_pairs: set[tuple[str, str]] = set()

    for anchor in [c for c in candidates if c.score >= PEER_TRIGGER_SCORE]:
        anchor_profile = profile_by_ticker.get(anchor.ticker)
        if not anchor_profile:
            continue
        anchor_sector = _clean_sector(anchor_profile.get("sector"))
        anchor_commodities = {str(c).strip().lower() for c in anchor_profile.get("commodities") or []}

        for ticker, profile in profile_by_ticker.items():
            if ticker in merged or ticker == anchor.ticker or (anchor.ticker, ticker) in seen_pairs:
                continue

            reason = None
            profile_sector = _clean_sector(profile.get("sector"))
            if anchor_sector and profile_sector == anchor_sector:
                reason = f"peer:{anchor.ticker}:sector"
            else:
                shared = anchor_commodities & {str(c).strip().lower() for c in profile.get("commodities") or []}
                if shared:
                    reason = f"peer:{anchor.ticker}:{sorted(shared)[0]}"
            if not reason:
                continue

            seen_pairs.add((anchor.ticker, ticker))
            merged[ticker] = Candidate(
                ticker=ticker,
                company_name=str(profile.get("company_name") or ""),
                score=PEER_BASE_SCORE,
                matched_terms=(reason,),
            )

    return sorted(merged.values(), key=lambda c: (-c.score, c.ticker))[:PEER_MAX_TOTAL]

IMPACT_SYSTEM_PROMPT = """Kamu analis dampak berita terhadap saham Indonesia.
Analisis artikel berikut hanya terhadap kandidat emiten yang diberikan.
Balas HANYA JSON valid dengan format:
{"relevant": true|false, "impacts": [{"ticker": "<ticker>", "impact_type": "positive|negative|neutral", "confidence": 0.0-1.0, "reasoning": "<1-2 kalimat alasan>"}]}
Ticker wajib diambil dari daftar kandidat. Jika tidak ada dampak material, relevant=false dan impacts=[]."""

def build_candidates_context(candidate_rows: list[dict]) -> str:
    blocks = []
    for row in candidate_rows:
        profile = (row.get("full_profile") or row.get("compact_profile") or "").strip()
        blocks.append(
            f"### {row['ticker']} - {row.get('company_name', '')}\n"
            f"Sektor: {row.get('sector') or '-'} | Subsektor: {row.get('subsector') or '-'}\n"
            f"Komoditas: {', '.join(row.get('commodities') or []) or '-'} | "
            f"Tag: {', '.join(row.get('tags') or []) or '-'}\n"
            f"{profile[:PROFILE_CONTEXT_MAX_CHARS]}"
        )
    return "\n\n".join(blocks)

def parse_impact_response(text: str) -> dict:
    data = _parse_response_json(text)
    impacts = []
    for item in data.get("impacts") or []:
        if not isinstance(item, dict):
            continue
        try:
            confidence = max(0.0, min(1.0, float(item.get("confidence") or 0)))
        except (TypeError, ValueError):
            confidence = 0.0
        impacts.append({
            "ticker": str(item.get("ticker") or "").strip().upper(),
            "impact_type": str(item.get("impact_type") or "neutral").strip().lower(),
            "confidence": round(confidence, 2),
            "reasoning": str(item.get("reasoning") or "").strip(),
        })
    return {"relevant": bool(data.get("relevant")), "impacts": impacts}

def validate_impacts(impacts: list[dict], allowed_tickers: list[str]) -> tuple[list[dict], list[str]]:
    """Ticker hasil AI harus subset kandidat/universe; sisanya dicatat sebagai dropped."""
    allowed = {t.upper() for t in allowed_tickers}
    selected: list[dict] = []
    dropped: list[str] = []
    seen: set[str] = set()
    for item in impacts:
        ticker = item.get("ticker", "")
        if ticker in allowed and ticker not in seen:
            selected.append(item)
            seen.add(ticker)
        elif ticker:
            dropped.append(ticker)
    return selected, dropped

def analyze_impact(config: AIConfig, title: str, content: str, candidate_rows: list[dict]) -> dict:
    payload = {
        "model": config.model,
        "messages": [
            {"role": "system", "content": IMPACT_SYSTEM_PROMPT},
            {
                "role": "user",
                "content": (
                    f"Judul: {title}\n\nIsi:\n{clean_markdown(content)[:4000]}\n\n"
                    f"Kandidat emiten:\n{build_candidates_context(candidate_rows)}"
                ),
            },
        ],
        "temperature": 0,
    }
    headers = {"Authorization": f"Bearer {config.api_key}", "Content-Type": "application/json"}
    response = curl_requests.post(
        f"{config.base_url}/chat/completions",
        json=payload,
        headers=headers,
        timeout=config.timeout_seconds,
    )
    response.raise_for_status()
    return parse_impact_response(_message_content(_parse_response_json(response.text)))