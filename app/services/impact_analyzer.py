import json
import re
from typing import Any

import httpx

from app.core.config import AIConfig

SYSTEM_PROMPT = """You are an Indonesian capital-market news classifier.
Return only valid JSON. Identify Indonesian listed-stock tickers affected by the news.
If the news is not relevant to any listed stock, return affected_tickers as null.
Do not guess. Only use tickers from the provided company universe.
Prefer direct business impact, issuer mention, commodity impact, sector impact, or regulation impact.
"""


def _compact_universe(companies: list[dict[str, Any]]) -> str:
    return "\n".join(f"- {company['ticker']}: {company['name']}" for company in companies)


def _extract_json(content: str) -> dict[str, Any]:
    try:
        return json.loads(content)
    except json.JSONDecodeError:
        decoder = json.JSONDecoder()
        for match in re.finditer(r"\{", content):
            try:
                parsed, _ = decoder.raw_decode(content[match.start() :])
            except json.JSONDecodeError:
                continue
            if isinstance(parsed, dict):
                return parsed
        raise


def _response_json(response: httpx.Response) -> dict[str, Any]:
    try:
        return response.json()
    except json.JSONDecodeError:
        return _extract_json(response.text)


def analyze_article_impact(
    config: AIConfig,
    article: dict[str, Any],
    companies: list[dict[str, Any]],
) -> dict[str, Any]:
    user_prompt = f"""
Company universe:
{_compact_universe(companies)}

News article:
Source: {article['source_name']}
Title: {article['title']}
Summary: {article.get('summary') or ''}
URL: {article['url']}

Return JSON with this exact shape:
{{
  "affected_tickers": ["BBCA"] or null,
  "confidence": 0.0-1.0,
  "reasoning": "short Indonesian explanation"
}}
""".strip()

    payload = {
        "model": config.model,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
        "temperature": 0,
        "response_format": {"type": "json_object"},
    }
    headers = {
        "Authorization": f"Bearer {config.api_key}",
        "Content-Type": "application/json",
    }

    with httpx.Client(timeout=config.timeout_seconds, headers=headers) as client:
        response = client.post(f"{config.base_url}/chat/completions", json=payload)
    response.raise_for_status()

    raw = _response_json(response)
    content = raw["choices"][0]["message"]["content"]
    parsed = _extract_json(content)

    valid_tickers = {company["ticker"] for company in companies}
    affected_tickers = parsed.get("affected_tickers")
    if affected_tickers:
        affected_tickers = [ticker for ticker in affected_tickers if ticker in valid_tickers]
        if not affected_tickers:
            affected_tickers = None

    return {
        "affected_tickers": affected_tickers,
        "confidence": float(parsed.get("confidence") or 0),
        "reasoning": str(parsed.get("reasoning") or ""),
        "raw_response": json.dumps(raw, ensure_ascii=False),
    }
