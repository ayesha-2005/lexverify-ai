from typing import List, Dict, Any

from src.state import AgentState
from src.rag.retriever import retrieve_chunks


def extract_candidate_citations(
    chunks: List[Dict[str, Any]]
) -> List[str]:
    """
    Extract ONLY structured citations attached to retrieved chunks.

    We intentionally do NOT extract arbitrary citations from OCR text.

    A judgment can mention many other cases. Those citations are references
    inside the judgment and are not necessarily the citation of the retrieved
    case itself.

    Therefore chunk["citations"] is the source for primary citation
    verification.
    """

    candidates = []
    seen = set()

    for chunk in chunks:
        citations = chunk.get("citations", [])

        if isinstance(citations, str):
            citations = [citations]

        if not isinstance(citations, list):
            continue

        for citation in citations:
            if not isinstance(citation, str):
                continue

            citation = citation.strip()

            if not citation:
                continue

            normalized = " ".join(
                citation.split()
            ).lower()

            if normalized not in seen:
                candidates.append(citation)
                seen.add(normalized)

    return candidates


def run_retrieval_agent(
    state: AgentState,
    retrieval_func=retrieve_chunks
) -> AgentState:
    """
    Agent 2: Retrieve relevant legal chunks using FAISS.

    Citation candidates come ONLY from structured chunk metadata.
    """

    try:
        research_plan = state.get(
            "research_plan",
            {}
        )

        queries = research_plan.get(
            "search_queries",
            [state["user_question"]]
        )

        if not queries:
            queries = [
                state["user_question"]
            ]

        chunks = retrieval_func(
            queries,
            top_k=3
        )

        state["retrieved_chunks"] = chunks

        state["candidate_citations"] = (
            extract_candidate_citations(chunks)
        )

        state["status"] = "retrieval_completed"

    except Exception as e:
        state.setdefault(
            "errors",
            []
        ).append(
            f"Retrieval Agent Error: {str(e)}"
        )

        state["status"] = "retrieval_failed"

    return state