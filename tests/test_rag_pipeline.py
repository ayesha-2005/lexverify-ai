import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.state import create_initial_state
from src.rag.retriever import retrieve_chunks
from src.rag.verifier import run_verification


def main():

    print("=" * 70)
    print("LexVerify AI - Retrieval + Truth Gate Integration Test")
    print("=" * 70)

    # --------------------------------------------------
    # 1. Create AgentState
    # --------------------------------------------------

    question = "Can pre-arrest bail be granted where mala fide is alleged?"

    state = create_initial_state(question)

    print("\nQuestion:")
    print(question)

    # --------------------------------------------------
    # 2. Research Agent output (simulated for now)
    # --------------------------------------------------

    search_queries = [
        "pre arrest bail mala fide FIR",
        "section 498 CrPC pre arrest bail",
        "pre arrest bail ill will investigation"
    ]

    print("\nSearch queries:")
    for query in search_queries:
        print("-", query)

    # --------------------------------------------------
    # 3. Retrieval Agent
    # --------------------------------------------------

    retrieved = retrieve_chunks(
        search_queries,
        top_k=3
    )

    state["retrieved_chunks"] = retrieved

    print("\nRetrieved chunks:", len(retrieved))

    # --------------------------------------------------
    # 4. Extract candidate citations
    # --------------------------------------------------

    candidate_citations = []

    for chunk in retrieved:

        for citation in chunk.get("citations", []):

            if citation not in candidate_citations:
                candidate_citations.append(citation)

    state["candidate_citations"] = candidate_citations

    print("\nCandidate citations:")

    for citation in candidate_citations:
        print("-", citation)

    # --------------------------------------------------
    # 5. Verification Agent / Truth Gate
    # --------------------------------------------------

    state = run_verification(state)

    print("\nVerification status:")
    print(state["status"])

    print("\nVERIFIED CITATIONS:")

    for citation in state["verified_citations"]:
        print(
            f"✓ {citation['citation']} | "
            f"{citation['case_name']}"
        )

    print("\nREJECTED CITATIONS:")

    for citation in state["rejected_citations"]:
        print(
            f"✗ {citation}"
        )

    # --------------------------------------------------
    # 6. Summary
    # --------------------------------------------------

    print("\n" + "=" * 70)
    print("PIPELINE SUMMARY")
    print("=" * 70)

    print("Retrieved chunks :", len(state["retrieved_chunks"]))
    print("Candidate cites  :", len(state["candidate_citations"]))
    print("Verified cites   :", len(state["verified_citations"]))
    print("Rejected cites   :", len(state["rejected_citations"]))
    print("Status            :", state["status"])

    print("=" * 70)


if __name__ == "__main__":
    main()