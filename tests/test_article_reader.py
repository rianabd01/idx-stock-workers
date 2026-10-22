import pytest

from app.services import article_reader as reader

PARAGRAPH = "Harga saham emiten perbankan naik tajam setelah laporan laba kuartal ketiga melampaui ekspektasi analis pasar. "
ARTICLE_HTML = f"""<html><head>
<title>Laba Bank Melonjak</title>
<meta property="og:title" content="Laba Bank Melonjak">
<meta name="description" content="Deskripsi singkat">
<meta property="article:published_time" content="2026-10-20T09:15:00+07:00">
<script type="application/ld+json">{{"@type":"NewsArticle","datePublished":"2026-10-20 09:15:00"}}</script>
</head><body><nav>Menu Home Market</nav>
<article><h1>Laba Bank Melonjak</h1>{"".join(f"<p>{PARAGRAPH * 3}</p>" for _ in range(5))}</article>
<footer>Copyright</footer></body></html>"""


class FakeResponse:
    def __init__(self, status_code=200, text="", headers=None):
        self.status_code = status_code
        self.text = text
        self.headers = headers or {}


class FakeSession:
    def __init__(self, routes):
        self.routes = routes
        self.calls = []

    def get(self, url, timeout=None):
        self.calls.append(url)
        return self.routes.get(url) or FakeResponse(404)


@pytest.fixture
def session(monkeypatch):
    fake = FakeSession({})
    monkeypatch.setattr(reader, "_session", lambda host: fake)
    monkeypatch.setattr(reader, "_throttle", lambda host: None)
    monkeypatch.setattr(reader, "_blocked_until", {})
    reader._robots.cache_clear()
    yield fake
    reader._robots.cache_clear()


def test_extract_article_returns_markdown_and_metadata():
    result = reader.extract_article(ARTICLE_HTML, "https://news.example/a")
    assert result["title"] == "Laba Bank Melonjak"
    assert result["description"] == "Deskripsi singkat"
    # meta ber-timezone diutamakan di atas JSON-LD naive
    assert result["published_time"] == "2026-10-20T09:15:00+07:00"
    assert "laporan laba kuartal ketiga" in result["content"]
    assert "Copyright" not in result["content"]


def test_extract_article_empty_page_returns_none():
    assert (
        reader.extract_article("<html><body></body></html>", "https://news.example/a")
        is None
    )


def test_fetch_ok(session):
    session.routes["https://news.example/a"] = FakeResponse(200, ARTICLE_HTML)
    assert (
        reader.fetch_article_content("https://news.example/a")["title"]
        == "Laba Bank Melonjak"
    )


def test_fetch_respects_robots(session):
    session.routes["https://news.example/robots.txt"] = FakeResponse(
        200, "User-agent: *\nDisallow: /a"
    )
    session.routes["https://news.example/a"] = FakeResponse(200, ARTICLE_HTML)
    assert reader.fetch_article_content("https://news.example/a") is None
    assert "https://news.example/a" not in session.calls


def test_blocked_host_cools_down_without_new_requests(session):
    session.routes["https://news.example/a"] = FakeResponse(403, "denied")
    with pytest.raises(reader.FetchBlocked):
        reader.fetch_article_content("https://news.example/a")
    calls = len(session.calls)
    with pytest.raises(reader.FetchBlocked, match="cooldown"):
        reader.fetch_article_content("https://news.example/b")
    assert len(session.calls) == calls


def test_cloudflare_challenge_counts_as_blocked(session):
    page = '<html><head><title>Just a moment...</title></head><script src="/cdn-cgi/challenge-platform/x.js"></script></html>'
    session.routes["https://news.example/a"] = FakeResponse(200, page)
    with pytest.raises(reader.FetchBlocked):
        reader.fetch_article_content("https://news.example/a")


def test_not_found_is_permanent_failure(session):
    assert reader.fetch_article_content("https://news.example/missing") is None
