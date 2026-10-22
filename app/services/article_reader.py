"""Pengganti Jina Reader (self-hosted): fetch HTML artikel lalu ekstrak jadi markdown.

Anti-deteksi dengan cara yang sopan, bukan menembus proteksi:
- fingerprint TLS/HTTP2 Chrome asli (curl_cffi impersonate) + satu Session per host (cookie/koneksi dipakai ulang)
- jeda per host + jitter, hormati robots.txt
- kena 403/429/503/challenge -> host di-cooldown, tidak di-retry beruntun
"""

import random
import re
import time
from functools import lru_cache
from typing import Any
from urllib.parse import urlsplit
from urllib.robotparser import RobotFileParser

import trafilatura
from curl_cffi import requests as curl_requests
from lxml import html as lxml_html

MAX_CONTENT_CHARS = 20_000
TIMEOUT_SECONDS = 30
MIN_DELAY_SECONDS = 4.0
JITTER_SECONDS = 3.0
COOLDOWN_SECONDS = 1800
BLOCK_STATUSES = {403, 429, 503}
HEADERS = {"Accept-Language": "id-ID,id;q=0.9,en-US;q=0.8,en;q=0.7"}

# ponytail: state in-memory per proses; pindah ke Redis/DB kalau worker dijalankan paralel.
_sessions: dict[str, curl_requests.Session] = {}
_last_hit: dict[str, float] = {}
_blocked_until: dict[str, float] = {}


class FetchBlocked(Exception):
    """Gagal sementara (diblokir/timeout): artikel sebaiknya dicoba lagi nanti."""


def _session(host: str) -> curl_requests.Session:
    if host not in _sessions:
        _sessions[host] = curl_requests.Session(impersonate="chrome", headers=HEADERS)
    return _sessions[host]


def _throttle(host: str) -> None:
    wait = (
        _last_hit.get(host, 0)
        + MIN_DELAY_SECONDS
        + random.uniform(0, JITTER_SECONDS)
        - time.monotonic()
    )
    if wait > 0:
        time.sleep(wait)
    _last_hit[host] = time.monotonic()


@lru_cache(maxsize=256)
def _robots(origin: str) -> RobotFileParser | None:
    host = urlsplit(origin).netloc
    _throttle(host)
    try:
        response = _session(host).get(f"{origin}/robots.txt", timeout=TIMEOUT_SECONDS)
    except Exception:
        return None
    if response.status_code != 200:
        return None
    parser = RobotFileParser()
    parser.parse(response.text.splitlines())
    return parser


def _published_time(tree: Any, html: str, fallback: str | None) -> str | None:
    # meta OpenGraph dulu karena selalu ber-timezone; JSON-LD Bisnis kadang naive (WIB tanpa offset).
    meta = tree.xpath('//meta[@property="article:published_time"]/@content')
    if meta and meta[0].strip():
        return meta[0].strip()
    match = re.search(r'"datePublished"\s*:\s*"([^"]+)"', html)
    return match.group(1) if match else fallback


def extract_article(
    html: str, url: str, max_chars: int = MAX_CONTENT_CHARS
) -> dict[str, Any] | None:
    """HTML -> {title, content (markdown), published_time, description}; None kalau isi kosong."""
    content = trafilatura.extract(
        html,
        url=url,
        output_format="markdown",
        favor_precision=True,
        include_images=False,
        include_comments=False,
    )
    if not content or not content.strip():
        return None
    meta = trafilatura.extract_metadata(html, default_url=url)
    return {
        "title": (meta.title if meta else None) or None,
        "content": content.strip()[:max_chars],
        "published_time": _published_time(
            lxml_html.fromstring(html), html, meta.date if meta else None
        ),
        "description": (meta.description if meta else None) or None,
    }


def fetch_article_content(url: str) -> dict[str, Any] | None:
    """Fetch + ekstrak artikel.

    Return None  -> gagal permanen (robots disallow, 4xx selain blokir, isi tidak terekstrak).
    Raise FetchBlocked -> gagal sementara (diblokir, rate-limited, timeout); coba lagi siklus berikutnya.
    """
    parts = urlsplit(url)
    host = parts.netloc
    if time.monotonic() < _blocked_until.get(host, 0):
        raise FetchBlocked(f"cooldown {host}")

    robots = _robots(f"{parts.scheme}://{host}")
    if robots and not robots.can_fetch("*", url):
        return None

    _throttle(host)
    try:
        response = _session(host).get(url, timeout=TIMEOUT_SECONDS)
    except Exception as exc:
        raise FetchBlocked(f"network {host}: {exc}") from exc

    text = response.text
    challenged = "challenge-platform" in text and "<title>Just a moment" in text
    if response.status_code in BLOCK_STATUSES or challenged:
        retry_after = response.headers.get("Retry-After", "")
        _blocked_until[host] = time.monotonic() + (
            int(retry_after) if retry_after.isdigit() else COOLDOWN_SECONDS
        )
        raise FetchBlocked(f"blocked_{response.status_code} {host}")
    if response.status_code >= 400:
        return None
    return extract_article(text, url)
