from typing import List, Dict, Any

from src.state import AgentState
from src.rag.retriever import retrieve_chunks

<<<<<<< HEAD

# Canonical citation parser.
# Handles common Pakistani legal citation formats while preserving
# the actual citation number.
CITATION_REGEX = re.compile(
    r"\b(?:"
    # PLD 2022 Supreme Court 743
    r"(?:PLD|PLJ|SCMR|YLR|CLC|PTD|ALD|PSC|K\.L\.R\.)"
    r"\s+\d{4}"
    r"(?:\s+(?:Supreme\s+Court|High\s+Court|SC|HC|LHR|KHI|Pesh|Quetta|Cr\.?C\.?|Crl\.?|Criminal\s+Cases))?"
    r"\s+\d+"
    r"|"
    # 2022 PLD Supreme Court 743
    r"\d{4}"
    r"\s+(?:PLD|PLJ|SCMR|YLR|CLC|PTD|ALD|PSC|K\.L\.R\.)"
    r"(?:\s+(?:Supreme\s+Court|High\s+Court|SC|HC|LHR|KHI|Pesh|Quetta|Cr\.?C\.?|Crl\.?|Criminal\s+Cases))?"
    r"\s+\d+"
    r"|"
    # 2018 P Cr. L. J. 323
    r"\d{4}"
    r"\s+P\s*\.?\s*Cr\s*\.?\s*L\s*\.?\s*J\s*\.?\s*\d+"
    r")\b",
    re.IGNORECASE,
)


def normalize_citation(citation: str) -> str:
    """
    Normalize superficial formatting differences while preserving
    the actual legal citation.
    """
    if not citation:
        return ""

    citation = citation.strip()

    # Normalize whitespace
    citation = re.sub(r"\s+", " ", citation)

    # Normalize P Cr. L. J. variants
    citation = re.sub(
        r"P\s*\.?\s*Cr\s*\.?\s*L\s*\.?\s*J",
        "P Cr. L. J.",
        citation,
        flags=re.IGNORECASE,
    )

    # Normalize Cr.C / Cr. C. / Crl. variants
    citation = re.sub(
        r"Cr\s*\.?\s*C\.?",
        "Cr.C.",
        citation,
        flags=re.IGNORECASE,
    )

    return citation.strip()


def extract_candidate_citations(chunks: List[Dict[str, Any]]) -> List[str]:
    """
    Extract candidate legal citations from retrieved chunks.

    Priority:
    1. Structured citations already supplied by the retriever.
    2. Regex extraction from chunk text as a fallback.

    This prevents the retrieval layer from losing citation information
    that is already available in chunk metadata.
    """
    candidates = set()

    for chunk in chunks:
        # ---------------------------------------------------------
        # 1. Prefer structured citation metadata
        # ---------------------------------------------------------
        structured_citations = chunk.get("citations", [])

        if isinstance(structured_citations, str):
            structured_citations = [structured_citations]

        if isinstance(structured_citations, list):
            for citation in structured_citations:
                if isinstance(citation, str) and citation.strip():
                    normalized = normalize_citation(citation)
                    if normalized:
                        candidates.add(normalized)

        # ---------------------------------------------------------
        # 2. Fallback: extract citations from raw text
        # ---------------------------------------------------------
        text = chunk.get("text", "")

        if text:
            matches = CITATION_REGEX.findall(text)

            for match in matches:
                normalized = normalize_citation(match)

                if normalized:
                    candidates.add(normalized)

    return sorted(candidates)


def run_retrieval_agent(
    state: AgentState,
    retrieval_func=retrieve_chunks
) -> AgentState:
    """
    Agent 2: Executes FAISS vector retrieval using queries from
    state['research_plan'] and extracts candidate citations.
=======

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
>>>>>>> origin/rag-data-pipeline
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
<<<<<<< HEAD
        queries = state.get(
            "research_plan",
            {}
        ).get(
=======
        research_plan = state.get(
            "research_plan",
            {}
        )

        queries = research_plan.get(
>>>>>>> origin/rag-data-pipeline
            "search_queries",
            [state["user_question"]]
        )

<<<<<<< HEAD
        # Real FAISS vector retrieval
        chunks = retrieval_func(queries, top_k=3)

        state["retrieved_chunks"] = chunks

        # Extract citations using structured metadata first,
        # then raw text as fallback.
        state["candidate_citations"] = extract_candidate_citations(chunks)
=======
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
>>>>>>> origin/rag-data-pipeline

        state["status"] = "retrieval_completed"

    except Exception as e:
<<<<<<< HEAD
        state["errors"].append(
            f"Retrieval Agent Error: {str(e)}"
        )
=======
        state.setdefault(
            "errors",
            []
        ).append(
            f"Retrieval Agent Error: {str(e)}"
        )

>>>>>>> origin/rag-data-pipeline
        state["status"] = "retrieval_failed"

    return state