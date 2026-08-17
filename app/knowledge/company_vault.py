from pathlib import Path
from typing import Any

VAULT_PATH = Path("company_vault/lq45")


def _parse_scalar(value: str) -> str:
    value = value.strip()
    if len(value) >= 2 and value[0] in {"'", '"'} and value[-1] == value[0]:
        return value[1:-1]
    return value


def _parse_list(value: str) -> list[str]:
    value = value.strip()
    if not value.startswith("[") or not value.endswith("]"):
        return []
    inner = value[1:-1].strip()
    if not inner:
        return []
    return [_parse_scalar(item) for item in inner.split(",") if item.strip()]


def _parse_frontmatter(content: str) -> tuple[dict[str, Any], str]:
    if not content.startswith("---\n"):
        return {}, content.strip()

    end = content.find("\n---\n", 4)
    if end == -1:
        return {}, content.strip()

    metadata: dict[str, Any] = {}
    frontmatter = content[4:end]
    body = content[end + 5 :].strip()

    for line in frontmatter.splitlines():
        if ":" not in line:
            continue
        key, raw_value = line.split(":", 1)
        key = key.strip()
        raw_value = raw_value.strip()
        metadata[key] = _parse_list(raw_value) if raw_value.startswith("[") else _parse_scalar(raw_value)

    return metadata, body


def load_company_vault(vault_path: Path = VAULT_PATH) -> dict[str, dict[str, Any]]:
    if not vault_path.exists():
        return {}

    companies: dict[str, dict[str, Any]] = {}
    for path in sorted(vault_path.glob("*.md")):
        metadata, body = _parse_frontmatter(path.read_text(encoding="utf-8"))
        ticker = str(metadata.get("ticker") or path.stem).upper()
        companies[ticker] = {
            "ticker": ticker,
            "name": metadata.get("name") or ticker,
            "sektor": metadata.get("sektor"),
            "subsektor": metadata.get("subsektor"),
            "komoditas": metadata.get("komoditas") or [],
            "tag": metadata.get("tag") or [],
            "profile": body,
            "source_path": str(path),
        }
    return companies


def enrich_companies_with_vault(companies: list[dict[str, Any]]) -> list[dict[str, Any]]:
    vault = load_company_vault()
    enriched = []

    for company in companies:
        ticker = str(company["ticker"]).upper()
        vault_company = vault.get(ticker)
        if not vault_company:
            enriched.append(company)
            continue

        merged = dict(company)
        merged.update(
            {
                "name": vault_company.get("name") or company["name"],
                "vault_sektor": vault_company.get("sektor"),
                "vault_subsektor": vault_company.get("subsektor"),
                "vault_komoditas": vault_company.get("komoditas") or [],
                "vault_tag": vault_company.get("tag") or [],
                "vault_profile": vault_company.get("profile") or "",
                "vault_source_path": vault_company.get("source_path"),
            }
        )
        enriched.append(merged)

    return enriched
