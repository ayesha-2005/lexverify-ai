from src.rag.verifier import (
    verify_citation,
    verify_citations,
    normalize_citation,
)


TRUTH_REGISTRY = [
    {
        "citation": "PLD 2021 SC 1",
        "source": "Justice_Qazi_Faez_Isa.pdf",
    },
    {
        "citation": "PLD 2017 692",
        "source": "Imran_Khan_v_Nawaz_Sharif.pdf",
    },
    {
        "citation": "PLD 2005 605",
        "source": "Fecto_Belarus.pdf",
    },
]


def test_exact_match():

    result = verify_citation(
        "PLD 2021 SC 1",
        TRUTH_REGISTRY
    )

    assert result["verified"] is True
    assert result["match_type"] == "exact"
    assert result["match_score"] == 100


def test_case_and_spacing_normalization():

    result = verify_citation(
        "  pld   2021   sc 1  ",
        TRUTH_REGISTRY
    )

    assert result["verified"] is True


def test_fuzzy_match():

    result = verify_citation(
        "PLD 2021 SC1",
        TRUTH_REGISTRY
    )

    assert result["verified"] is True
    assert result["match_type"] == "fuzzy"
    assert result["match_score"] >= 90


def test_fake_citation_rejected():

    result = verify_citation(
        "PLD 2025 SC 999",
        TRUTH_REGISTRY
    )

    assert result["verified"] is False
    assert result["match_type"] == "none"


def test_multiple_citations():

    candidates = [
        "PLD 2021 SC 1",
        "PLD 2017 692",
        "PLD 2025 SC 999",
    ]

    verified, rejected, results = verify_citations(
        candidates,
        TRUTH_REGISTRY
    )

    assert len(verified) == 2
    assert len(rejected) == 1
    assert len(results) == 3
def test_mixed_valid_and_invalid_citations():
    from src.rag.verifier import verify_citations

    truth_registry = [
        {
            "citation": "PLD 2022 Supreme Court 743",
            "verified": True,
            "case_name": "Syed Raza Hussain Bukhari v. The State",
            "court": "Supreme Court of Pakistan",
            "year": 2022,
            "source": "case_007_syed_raza_hussain_bukhari.pdf",
        },
        {
            "citation": "2016 PLD Supreme Court 171",
            "verified": True,
            "case_name": "Malik Nazir Ahmed v. Syed Shamas-ul-Abbas",
            "court": "Supreme Court of Pakistan",
            "year": 2016,
            "source": "case_002_malik_nazir_ahmed.pdf",
        },
    ]

    citations = [
        "PLD 2022 Supreme Court 743",
        "PLD 2099 Supreme Court 999",
    ]

    verified, rejected, results = verify_citations(
        citations,
        truth_registry
    )

    # One verified result
    assert len(verified) == 1

    # One rejected result
    assert len(rejected) == 1

    # Two total verification results
    assert len(results) == 2

    # Verify the valid citation result
    valid_result = next(
        item for item in results
        if item["citation"] == "PLD 2022 Supreme Court 743"
    )

    assert valid_result["verified"] is True
    assert valid_result["match_type"] == "exact"

    # Verify the fake citation result
    invalid_result = next(
        item for item in results
        if item["citation"] == "PLD 2099 Supreme Court 999"
    )

    assert invalid_result["verified"] is False

    # Make sure the correct results went into each collection
    assert verified[0]["citation"] == "PLD 2022 Supreme Court 743"
    assert rejected[0] == "PLD 2099 Supreme Court 999"