from app.knowledge import company_vault


def test_frontmatter_and_enrichment(tmp_path, monkeypatch):
    vault_path = tmp_path / "vault"
    vault_path.mkdir()
    (vault_path / "bbca.md").write_text(
        "---\nticker: bbca\nname: Bank Central Asia\nsektor: Keuangan\nkomoditas: [rupiah, kredit]\ntag: [bank]\n---\n\n# Profil\nBank besar.",
        encoding="utf-8",
    )

    loaded = company_vault.load_company_vault(vault_path)
    assert loaded["BBCA"]["komoditas"] == ["rupiah", "kredit"]
    assert loaded["BBCA"]["profile"].startswith("# Profil")

    monkeypatch.setattr(company_vault, "load_company_vault", lambda: loaded)
    original = {"ticker": "BBCA", "name": "Nama DB"}
    untouched = {"ticker": "TLKM", "name": "Telkom"}
    enriched = company_vault.enrich_companies_with_vault([original, untouched])

    assert enriched[0]["name"] == "Bank Central Asia"
    assert enriched[0]["vault_sektor"] == "Keuangan"
    assert enriched[0]["vault_tag"] == ["bank"]
    assert enriched[1] is untouched
    assert original == {"ticker": "BBCA", "name": "Nama DB"}
