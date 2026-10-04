"""
LexVerify AI - Retrieval Agent

Retrieves legally relevant evidence from the FAISS index.

Important design:
- Statute questions prioritize statutes.
- Case-law questions prioritize judgments.
- Mixed questions deliberately retrieve BOTH:
    1. relevant CrPC/statutory evidence
    2. relevant Pakistani case-law evidence
- Mixed bail questions use dedicated bail queries so that
  generic semantic similarity does not dominate the result.
"""

from typing import Any, Dict, List

from src.rag.retriever import retrieve_chunks


# ============================================================
# Basic helpers
# ============================================================

def _unique_chunks(
    chunks: List[Dict[str, Any]]
) -> List[Dict[str, Any]]:
    """Remove duplicate chunks while preserving order."""

    result = []
    seen = set()

    for chunk in chunks:
        chunk_id = chunk.get("chunk_id")

        if chunk_id in seen:
            continue

        seen.add(chunk_id)
        result.append(chunk)

    return result


def _text(chunk: Dict[str, Any]) -> str:
    """
    Return whatever textual field exists in the chunk.

    Different versions of the metadata may use different names.
    """

    for key in (
        "text",
        "content",
        "chunk_text",
        "page_text",
    ):
        value = chunk.get(key)

        if isinstance(value, str) and value.strip():
            return value

    return ""


def _metadata_text(
    chunk: Dict[str, Any]
) -> str:
    """
    Build searchable text from structured metadata.

    This is important because not every metadata record necessarily
    contains the original chunk text.
    """

    values = []

    for key in (
        "source_file",
        "document_title",
        "case_name",
        "case_id",
        "document_type",
    ):
        value = chunk.get(key)

        if value:
            values.append(str(value))

    citations = chunk.get("citations", [])

    if isinstance(citations, list):
        values.extend(
            str(x)
            for x in citations
            if x
        )

    return " ".join(values)


def _combined_text(
    chunk: Dict[str, Any]
) -> str:
    """Return text + metadata for deterministic matching."""

    return (
        _text(chunk)
        + " "
        + _metadata_text(chunk)
    ).lower()


def _score(
    chunk: Dict[str, Any]
) -> float:
    """Return the retriever's existing ranked score."""

    return float(
        chunk.get(
            "ranked_score",
            chunk.get("score", 0.0),
        )
        or 0.0
    )


# ============================================================
# Legal relevance scoring
# ============================================================

def _legal_relevance_score(
    chunk: Dict[str, Any],
    question: str,
) -> float:
    """
    Add deterministic legal relevance on top of semantic score.

    This is intentionally simple and explainable.
    """

    q = question.lower()
    t = _combined_text(chunk)

    score = _score(chunk)

    document_type = str(
        chunk.get("document_type", "")
    ).lower()

    # --------------------------------------------------------
    # General bail relevance
    # --------------------------------------------------------

    if "bail" in q and "bail" in t:
        score += 0.12

    # --------------------------------------------------------
    # Section 497
    # --------------------------------------------------------

    if "497" in q or "bail" in q:

        if "497." in t:
            score += 0.20

        if "section 497" in t:
            score += 0.20

        if "when bail may be taken" in t:
            score += 0.15

    # --------------------------------------------------------
    # Section 498
    # --------------------------------------------------------

    if "bail" in q:

        if "498." in t:
            score += 0.22

        if "section 498" in t:
            score += 0.22

        if "power to direct admission to bail" in t:
            score += 0.18

    # --------------------------------------------------------
    # Section 498-A
    # --------------------------------------------------------

    if "bail" in q:

        if "498a" in t or "498-a" in t:
            score += 0.18

        if "not in custody" in t:
            score += 0.12

        if "no case is registered" in t:
            score += 0.12

    # --------------------------------------------------------
    # Pre-arrest bail
    # --------------------------------------------------------

    if "pre-arrest" in q or "pre arrest" in q:

        if "pre-arrest bail" in t:
            score += 0.35

        if "pre arrest bail" in t:
            score += 0.35

        if "before arrest" in t:
            score += 0.20

        if "bail before arrest" in t:
            score += 0.25

    # --------------------------------------------------------
    # Post-arrest bail
    # --------------------------------------------------------

    if "post-arrest" in q or "post arrest" in q:

        if "post-arrest bail" in t:
            score += 0.35

        if "post arrest bail" in t:
            score += 0.35

        if "after arrest" in t:
            score += 0.20

        if "bail after arrest" in t:
            score += 0.25

    # --------------------------------------------------------
    # Source-specific relevance
    # --------------------------------------------------------

    if document_type == "statute":

        if "crpc_1898.pdf" in t:
            score += 0.10

        if "code of criminal procedure" in t:
            score += 0.08

    if document_type == "judgment":

        if "pre-arrest bail" in t:
            score += 0.20

        if "pre arrest bail" in t:
            score += 0.20

        if "bail before arrest" in t:
            score += 0.15

    return score


# ============================================================
# Mixed retrieval
# ============================================================

def _retrieve_mixed_bail_evidence(
    question: str,
    search_queries: List[str],
) -> List[Dict[str, Any]]:
    """
    Retrieve strong statute + case-law evidence for bail
    comparison questions.

    This uses dedicated retrieval queries instead of relying
    exclusively on the Research Agent's generic queries.
    """

    # --------------------------------------------------------
    # Dedicated statutory queries
    # --------------------------------------------------------

    statute_queries = list(search_queries)

    statute_queries.extend(
        [
            "CrPC 1898 Section 497 bail",
            "CrPC 1898 Section 498 power to direct admission to bail",
            "CrPC 1898 Section 498A person not in custody bail",
            "Code of Criminal Procedure 1898 Chapter XXXIX bail",
        ]
    )

    # --------------------------------------------------------
    # Dedicated case-law queries
    # --------------------------------------------------------

    case_queries = list(search_queries)

    case_queries.extend(
        [
            "Pakistan pre-arrest bail case law",
            "Pakistan pre-arrest bail Section 498 498-A",
            "Pakistan pre-arrest bail Muhammad Shafique",
            "Pakistani courts pre-arrest bail before arrest",
            "Pakistan post-arrest bail case law Section 497",
        ]
    )

    # --------------------------------------------------------
    # Retrieve statutes
    # --------------------------------------------------------

    statute_candidates = retrieve_chunks(
        statute_queries,
        top_k=50,
        source_type="statute",
        candidate_pool=100,
    )

    # --------------------------------------------------------
    # Retrieve judgments
    # --------------------------------------------------------

    judgment_candidates = retrieve_chunks(
        case_queries,
        top_k=50,
        source_type="case_law",
        candidate_pool=100,
    )

    # --------------------------------------------------------
    # Deterministic legal reranking
    # --------------------------------------------------------

    statute_candidates = sorted(
        statute_candidates,
        key=lambda chunk: _legal_relevance_score(
            chunk,
            question,
        ),
        reverse=True,
    )

    judgment_candidates = sorted(
        judgment_candidates,
        key=lambda chunk: _legal_relevance_score(
            chunk,
            question,
        ),
        reverse=True,
    )

    # --------------------------------------------------------
    # BEST STATUTORY EVIDENCE
    #
    # We explicitly prefer chunks containing 497 and 498.
    # --------------------------------------------------------

    section_497 = [
        chunk
        for chunk in statute_candidates
        if (
            "497." in _combined_text(chunk)
            or "section 497" in _combined_text(chunk)
            or "when bail may be taken" in _combined_text(chunk)
        )
    ]

    section_498 = [
        chunk
        for chunk in statute_candidates
        if (
            "498." in _combined_text(chunk)
            or "section 498" in _combined_text(chunk)
            or "power to direct admission to bail" in _combined_text(chunk)
        )
    ]

    selected = []

    # Prefer Section 497.
    if section_497:
        selected.append(section_497[0])

    # Prefer Section 498 / 498-A.
    for chunk in section_498:
        if chunk.get("chunk_id") not in {
            x.get("chunk_id")
            for x in selected
        }:
            selected.append(chunk)
            break

    # If the exact sections were not found, use strongest statutes.
    for chunk in statute_candidates:

        if len(selected) >= 2:
            break

        if chunk.get("chunk_id") in {
            x.get("chunk_id")
            for x in selected
        }:
            continue

        selected.append(chunk)

    # --------------------------------------------------------
    # BEST CASE-LAW EVIDENCE
    # --------------------------------------------------------

    # Strongest candidates explicitly discussing pre-arrest bail.
    pre_arrest_cases = [
        chunk
        for chunk in judgment_candidates
        if (
            "pre-arrest bail" in _combined_text(chunk)
            or "pre arrest bail" in _combined_text(chunk)
            or "bail before arrest" in _combined_text(chunk)
        )
    ]

    # Prefer a judgment explicitly discussing pre-arrest bail.
    if pre_arrest_cases:

        selected.append(
            pre_arrest_cases[0]
        )

    elif judgment_candidates:

        # Still guarantee a judgment for mixed questions.
        selected.append(
            judgment_candidates[0]
        )

    # --------------------------------------------------------
    # Final cleanup
    # --------------------------------------------------------

    selected = _unique_chunks(selected)

    return selected[:3]


# ============================================================
# Main Retrieval Agent
# ============================================================

def run_retrieval_agent(
    state: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Main Retrieval Agent.
    """

    research_plan = state.get(
        "research_plan",
        {},
    )

    question = state.get(
        "user_question",
        "",
    )

    search_queries = research_plan.get(
        "search_queries",
        [],
    )

    source_type = research_plan.get(
        "source_type",
        "mixed",
    )

    if not search_queries:

        state.setdefault(
            "errors",
            [],
        ).append(
            "Retrieval Agent: no search queries were provided."
        )

        state["status"] = "retrieval_failed"

        return state

    try:

        # ====================================================
        # MIXED
        # ====================================================

        if source_type == "mixed":

            is_bail_comparison = (
                "bail" in question.lower()
                and (
                    "pre-arrest" in question.lower()
                    or "pre arrest" in question.lower()
                )
                and (
                    "post-arrest" in question.lower()
                    or "post arrest" in question.lower()
                )
            )

            if is_bail_comparison:

                final_chunks = (
                    _retrieve_mixed_bail_evidence(
                        question,
                        search_queries,
                    )
                )

                # Candidate pool is informational only.
                candidate_pool = final_chunks

            else:

                statute_candidates = retrieve_chunks(
                    search_queries,
                    top_k=30,
                    source_type="statute",
                    candidate_pool=100,
                )

                judgment_candidates = retrieve_chunks(
                    search_queries,
                    top_k=30,
                    source_type="case_law",
                    candidate_pool=100,
                )

                statute_candidates = sorted(
                    statute_candidates,
                    key=lambda c: _legal_relevance_score(
                        c,
                        question,
                    ),
                    reverse=True,
                )

                judgment_candidates = sorted(
                    judgment_candidates,
                    key=lambda c: _legal_relevance_score(
                        c,
                        question,
                    ),
                    reverse=True,
                )

                final_chunks = (
                    statute_candidates[:2]
                    + judgment_candidates[:1]
                )

                candidate_pool = (
                    statute_candidates
                    + judgment_candidates
                )

        # ====================================================
        # SINGLE SOURCE
        # ====================================================

        else:

            candidate_pool = retrieve_chunks(
                search_queries,
                top_k=30,
                source_type=source_type,
                candidate_pool=100,
            )

            candidate_pool = sorted(
                candidate_pool,
                key=lambda c: _legal_relevance_score(
                    c,
                    question,
                ),
                reverse=True,
            )

            final_chunks = candidate_pool[:3]

        # ====================================================
        # Deduplicate
        # ====================================================

        final_chunks = _unique_chunks(
            final_chunks
        )[:3]

        # ====================================================
        # Store chunks
        # ====================================================

        state["retrieved_chunks"] = final_chunks

        # ====================================================
        # Candidate citations
        # ====================================================

        candidate_citations = []

        for chunk in final_chunks:

            citations = chunk.get(
                "citations",
                [],
            )

            if not isinstance(citations, list):
                continue

            for citation in citations:

                if citation not in candidate_citations:
                    candidate_citations.append(
                        citation
                    )

        state["candidate_citations"] = (
            candidate_citations
        )

        # ====================================================
        # Source trace
        # ====================================================

        source_trace = []

        for chunk in final_chunks:

            source_trace.append(
                {
                    "chunk_id": chunk.get(
                        "chunk_id"
                    ),
                    "source_file": chunk.get(
                        "source_file"
                    ),
                    "page": chunk.get(
                        "page"
                    ),
                    "case_id": chunk.get(
                        "case_id"
                    ),
                    "case_name": chunk.get(
                        "case_name"
                    ),
                    "citations": chunk.get(
                        "citations",
                        [],
                    ),
                    "document_type": chunk.get(
                        "document_type"
                    ),
                    "score": chunk.get(
                        "ranked_score",
                        chunk.get(
                            "score",
                            0,
                        ),
                    ),
                }
            )

        state["source_trace"] = source_trace

        # ====================================================
        # Logging
        # ====================================================

        print()
        print("RETRIEVAL COMPLETED")
        print(
            f"  Research source_type: {source_type}"
        )
        print(
            f"  Candidate pool: {len(candidate_pool)}"
        )
        print(
            f"  Final chunks: {len(final_chunks)}"
        )

        print(
            "  Document types:",
            [
                c.get("document_type")
                for c in final_chunks
            ],
        )

        print(
            "  Source files:",
            [
                c.get("source_file")
                for c in final_chunks
            ],
        )

        print(
            "  Pages:",
            [
                c.get("page")
                for c in final_chunks
            ],
        )

        print(
            "  Citations:",
            [
                c.get("citations", [])
                for c in final_chunks
            ],
        )

        state["status"] = (
            "retrieval_completed"
        )

        return state

    except Exception as exc:

        state.setdefault(
            "errors",
            [],
        ).append(
            f"Retrieval Agent Error: {str(exc)}"
        )

        state["status"] = (
            "retrieval_failed"
        )

        return state