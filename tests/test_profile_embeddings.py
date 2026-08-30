"""Unit tests untuk Phase 5: chunking profil, cosine, dan merge kandidat hybrid."""

from app.services.profile_embeddings import (
    VALID_CHUNK_TYPES,
    build_profile_chunks,
    chunk_content_hash,
)
from app.services.impact_analysis import Candidate, expand_peers, merge_candidates


def _profile(full_profile: str = "", commodities: list | None = None) -> dict:
    return {
        "ticker": "BBRI",
        "company_name": "Bank Rakyat Indonesia",
        "commodities": commodities or [],
        "full_profile": full_profile,
    }


def _universe() -> list[dict]:
    return [
        {"ticker": "BBRI", "company_name": "Bank Rakyat", "sector": "Perbankan",
         "subsektor": "Bank BUMN Mikro UMKM", "commodities": []},
        {"ticker": "BMRI", "company_name": "Bank Mandiri", "sector": "Perbankan",
         "subsektor": "Bank BUMN Korporasi", "commodities": []},
        {"ticker": "ANTM", "company_name": "Aneka Tambang", "sector": "Pertambangan Logam",
         "subsektor": "Nikel Emas Bauksit", "commodities": ["gold", "nickel"]},
        {"ticker": "AMMN", "company_name": "Amman Mineral", "sector": "Pertambangan Logam",
         "subsektor": "Tembaga dan Emas", "commodities": ["gold", "copper"]},
        {"ticker": "GOTO", "company_name": "GoTo Gojek", "sector": "Teknologi",
         "subsektor": "Digital", "commodities": []},
    ]


SAMPLE_PROFILE = """# Ringkasan bisnis
Bank BUMN fokus mikro dan UMKM.

# Sumber pendapatan utama
- Bunga kredit mikro.
- Fee based income.

# Driver bisnis
- Pertumbuhan KUR.

# Risiko utama
- NPL mikro naik.

# Sensitif terhadap berita
- Kebijakan subsidi bunga KUR.
"""


class TestBuildProfileChunks:
    def test_splits_by_heading_with_correct_types(self):
        chunks = build_profile_chunks(_profile(SAMPLE_PROFILE))
        types = [c_type for c_type, _content in chunks]
        assert types == ["overview", "revenue", "driver", "risk", "sensitivity"]
        assert all(c_type in VALID_CHUNK_TYPES for c_type in types)

    def test_content_includes_heading_and_body(self):
        chunks = build_profile_chunks(_profile(SAMPLE_PROFILE))
        overview = dict(chunks)["overview"]
        assert overview.startswith("Ringkasan bisnis")
        assert "Bank BUMN" in overview

    def test_commodity_chunk_from_metadata(self):
        chunks = build_profile_chunks(_profile(SAMPLE_PROFILE, commodities=["emas", "nikel"]))
        commodity = dict(chunks).get("commodity")
        assert commodity is not None
        assert "emas" in commodity and "nikel" in commodity

    def test_empty_body_yields_only_commodity(self):
        chunks = build_profile_chunks(_profile("", commodities=["batu bara"]))
        assert [(c_type, content) for c_type, content in chunks] == [
            ("commodity", "Komoditas: batu bara")
        ]

    def test_unknown_section_maps_to_overview_once(self):
        body = "# Halaman lain\nisi.\n# Halaman kedua\nisi dua."
        chunks = build_profile_chunks(_profile(body))
        assert len(chunks) == 1  # dedupe: hanya overview pertama yang disimpan


class TestChunkContentHash:
    def test_same_input_same_hash(self):
        assert chunk_content_hash("risk", "abc") == chunk_content_hash("risk", "abc")

    def test_different_type_or_content_changes_hash(self):
        assert chunk_content_hash("risk", "abc") != chunk_content_hash("driver", "abc")
        assert chunk_content_hash("risk", "abc") != chunk_content_hash("risk", "abd")


class TestMergeCandidates:
    def test_union_of_keyword_and_vector(self):
        keyword = [Candidate(ticker="BBRI", company_name="BRI", score=10.0, matched_terms=("BBRI",))]
        vector = {"ANTM": (0.75, "commodity")}
        merged = merge_candidates(keyword, vector)
        tickers = {c.ticker for c in merged}
        assert tickers == {"BBRI", "ANTM"}

    def test_double_signal_gets_bonus_and_marker(self):
        keyword = [Candidate(ticker="MDKA", company_name="Merdeka", score=3.0, matched_terms=("tembaga",))]
        vector = {"MDKA": (0.80, "sensitivity")}
        merged = merge_candidates(keyword, vector)
        assert len(merged) == 1
        candidate = merged[0]
        assert candidate.score > 3.0  # dapat bonus sinyal ganda
        assert any(term.startswith("vector:") for term in candidate.matched_terms)

    def test_vector_only_candidate_uses_scaled_similarity(self):
        vector = {"GOTO": (0.60, "driver")}
        merged = merge_candidates([], vector)
        assert merged[0].score == round(0.60 * 8.0, 2)

    def test_sorted_desc_and_capped_at_top_k(self):
        keyword = [
            Candidate(ticker=f"T{i:02d}", company_name="", score=float(20 - i), matched_terms=())
            for i in range(15)
        ]
        merged = merge_candidates(keyword, {})
        assert len(merged) <= 15
        scores = [c.score for c in merged]
        assert scores == sorted(scores, reverse=True)


class TestExpandPeers:
    def test_sector_peer_added_when_anchor_strong(self):
        anchors = [Candidate(ticker="BBRI", company_name="", score=16.0, matched_terms=("BBRI",))]
        result = expand_peers(anchors, _universe())
        tickers = {c.ticker for c in result}
        assert "BMRI" in tickers  # sesama Perbankan ikut
        assert "GOTO" not in tickers  # sektor beda tidak ditarik

    def test_commodity_peer_added_across_sectors(self):
        # AMMN (Pertambangan Logam) menarik emiten sektor lain yang share komoditas gold
        universe = _universe() + [
            {"ticker": "HRUM", "company_name": "Harum Energy", "sector": "Energi",
             "subsektor": "Batubara", "commodities": ["gold"]},
        ]
        anchors = [Candidate(ticker="AMMN", company_name="", score=9.0, matched_terms=("gold",))]
        result = expand_peers(anchors, universe)
        peer = next(c for c in result if c.ticker == "HRUM")
        assert any(term.startswith("peer:AMMN:gold") for term in peer.matched_terms)
        assert peer.score == 2.5  # PEER_BASE_SCORE

    def test_weak_anchor_pulls_no_peers(self):
        anchors = [Candidate(ticker="BBRI", company_name="", score=3.0, matched_terms=("bank",))]
        result = expand_peers(anchors, _universe())
        assert {c.ticker for c in result} == {"BBRI"}

    def test_existing_candidate_not_duplicated(self):
        anchors = [
            Candidate(ticker="BBRI", company_name="", score=16.0, matched_terms=("BBRI",)),
            Candidate(ticker="BMRI", company_name="", score=5.0, matched_terms=("mandiri",)),
        ]
        result = expand_peers(anchors, _universe())
        bmrn_count = sum(1 for c in result if c.ticker == "BMRI")
        assert bmrn_count == 1
        # skor BMRI asli dipertahankan, bukan diganti skor peer
        assert next(c for c in result if c.ticker == "BMRI").score == 5.0

    def test_capped_at_peer_max_total(self):
        many = [
            Candidate(ticker=f"T{i:02d}", company_name="", score=float(20 - i), matched_terms=())
            for i in range(25)
        ]
        assert len(expand_peers(many, _universe())) <= 20
