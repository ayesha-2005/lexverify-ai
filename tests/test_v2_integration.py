from src.orchestrator import run_lexverify_pipeline


def test_full_v2_pipeline():
    state = run_lexverify_pipeline(
        "Can a person get bail in a criminal case?"
    )

    # -----------------------------
    # Pipeline completion
    # -----------------------------
    assert state["status"] == "synthesis_completed"
    assert state["errors"] == []

    # -----------------------------
    # Research Agent
    # -----------------------------
    assert state["research_plan"]
    assert state["research_plan"]["legal_intent"]
    assert state["research_plan"]["key_terms"]
    assert state["research_plan"]["search_queries"]

    # V2 transparency field
    assert (
        state["extracted_keywords"]
        == state["research_plan"]["key_terms"]
    )

    # -----------------------------
    # Retrieval Agent
    # -----------------------------
    assert state["retrieved_chunks"]
    assert state["candidate_citations"]
    assert state["source_trace"]

    # -----------------------------
    # Verification
    # -----------------------------
    assert state["verification_results"]
    assert state["verified_citations"]

    # Every verified citation must actually be verified
    assert all(
        item["verified"]
        for item in state["verified_citations"]
    )

    # -----------------------------
    # Metrics
    # -----------------------------
    metrics = state["metrics_summary"]

    assert metrics["total_citations"] >= 1
    assert metrics["verified_count"] >= 1
    assert metrics["rejected_count"] >= 0

    # -----------------------------
    # Synthesis
    # -----------------------------
    assert state["final_answer"]