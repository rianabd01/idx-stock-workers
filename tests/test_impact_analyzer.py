import json

import pytest

from app.core.config import AIConfig
from app.services.impact_analyzer import _extract_json, analyze_article_impact


def test_extract_json_supports_fenced_json():
    assert _extract_json('```json\n{"affected_tickers": ["BBCA"]}\n```') == {
        "affected_tickers": ["BBCA"]
    }


def test_extract_json_rejects_invalid_payload():
    with pytest.raises(json.JSONDecodeError):
        _extract_json("not JSON")


def test_analysis_filters_tickers_outside_company_universe(monkeypatch):
    raw = {
        "choices": [
            {
                "message": {
                    "content": '```json\n{"affected_tickers":["BBCA","FAKE"],"confidence":0.8,"reasoning":"uji"}\n```'
                }
            }
        ]
    }

    class FakeResponse:
        def raise_for_status(self):
            return None

        def json(self):
            return raw

    class FakeClient:
        def __init__(self, **kwargs):
            pass

        def __enter__(self):
            return self

        def __exit__(self, *args):
            return None

        def post(self, url, json):
            return FakeResponse()

    monkeypatch.setattr("app.services.impact_analyzer.httpx.Client", FakeClient)
    result = analyze_article_impact(
        AIConfig("secret", "https://ai.example/v1", "model"),
        {"source_name": "Source", "title": "Title", "summary": "Summary", "url": "https://example.com"},
        [{"ticker": "BBCA", "name": "Bank Central Asia"}],
    )

    assert result["affected_tickers"] == ["BBCA"]
    assert result["confidence"] == 0.8
