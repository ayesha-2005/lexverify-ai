import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.state import create_initial_state
from src.rag.retriever import retrieve_chunks
from src.rag.verifier import run_verification


def test_retrieval_returns_relevant_chunks():
    """Test that a known legal question retrieves relevant case-law chunks."""

    question = "Can pre-arrest bail be granted where mala fide is alleged?"

    search_queries = [
        "pre arrest bail mala fide FIR",
        "section 498 CrPC pre arrest bail",
        "pre arrest bail ill will investigation",
    ]

    retrieved = retrieve_chunks(search_queries, top_k=3)

    assert len(retrieved) > 0
    assert len(retrieved) <= 3

    # Every result should contain the fields required by the pipeline.
    for chunk in retrieved:
        assert "text" in chunk
        assert "case_name" in chunk
        assert "citations" in chunk
        assert "score" in chunk

    # At least one retrieved result should be from our known pre-arrest
    # bail cases.
    case_names = [
        chunk.get("case_name", "").lower()
        for chunk in retrieved
    ]

    assert any(
        "muhammad shafique" in name
        or "malik nazir" in name
        for name in case_names
    )


def test_valid_citation_is_verified():
    """Test that a citation present in the Truth Registry is verified."""

    state = create_initial_state(
        "Can pre-arrest bail be granted where mala fide is alleged?"
    )

    state["candidate_citations"] = [
        "PLJ 2018 Cr.C. 656"
    ]

    state = run_verification(state)

    assert len(state["verified_citations"]) == 1
    assert state["verified_citations"][0]["verified"] is True
    assert (
        state["verified_citations"][0]["citation"]
        == "PLJ 2018 Cr.C. 656"
    )

    assert "PLJ 2018 Cr.C. 656" not in state["rejected_citations"]


def test_fake_citation_is_rejected():
    """Test that a fake citation is blocked by the Truth Registry."""

    state = create_initial_state(
        "What does PLD 2025 SC 999 say about bail?"
    )

    state["candidate_citations"] = [
        "PLD 2025 SC 999"
    ]

    state = run_verification(state)

    assert len(state["verified_citations"]) == 0
    assert "PLD 2025 SC 999" in state["rejected_citations"]


def test_multiple_valid_citations_are_verified():
    """Test verification of citations from different cases."""

    state = create_initial_state(
        "What are the principles governing bail?"
    )

    state["candidate_citations"] = [
        "PLD 2022 SC 764",
        "PLD 2022 Supreme Court 743",
    ]

    state = run_verification(state)

    verified = state["verified_citations"]

    assert len(verified) == 2

    verified_citations = [
        item["citation"]
        for item in verified
    ]

    assert "PLD 2022 SC 764" in verified_citations
    assert "PLD 2022 Supreme Court 743" in verified_citations


def test_unrelated_question_returns_safe_retrieval_result():
    """
    Test an unrelated question.

    The RAG system may still return mathematically nearest chunks because
    FAISS always returns nearest neighbours. Therefore we do not require
    zero results here. We only require that the retrieval call completes
    and returns properly structured results.
    """

    search_queries = [
        "foreign maritime tax rates"
    ]

    retrieved = retrieve_chunks(
        search_queries,
        top_k=3
    )

    assert isinstance(retrieved, list)
    assert len(retrieved) <= 3

    for chunk in retrieved:
        assert "score" in chunk
        assert "text" in chunk
        assert "case_name" in chunk


def test_unknown_citation_does_not_get_verified():
    """Test another clearly unknown citation."""

    state = create_initial_state(
        "Test unknown legal citation"
    )

    state["candidate_citations"] = [
        "PLD 2099 SC 999"
    ]

    state = run_verification(state)

    assert state["verified_citations"] == []
    assert "PLD 2099 SC 999" in state["rejected_citations"]