from typing import List, Dict, Any, Set, Tuple

from src.rag.retriever import retrieve_chunks


# ============================================================
# Source-Aware Retrieval Configuration
# ============================================================

SOURCE_TYPE_TO_DOCUMENT_TYPES = {
    "statute": {"statute"},
    "constitution": {"constitution"},
    "case_law": {"judgment"},
    "mixed": {
        "statute",
        "constitution",
        "judgment",
    },
}


# ============================================================
# Citation Extraction
# ============================================================

def extract_candidate_citations(
    chunks: List[Dict[str, Any]]
) -> List[str]:
    """
    Extract candidate citations ONLY from structured chunk metadata.

    Never extract citations from arbitrary OCR/text content.
    This prevents truncated or hallucinated citation strings.
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
            if not citation:
                continue

            citation = str(citation).strip()

            if not citation:
                continue

            normalized = " ".join(
                citation.lower().split()
            )

            if normalized not in seen:
                seen.add(normalized)
                candidates.append(citation)

    return candidates


# ============================================================
# Source Trace
# ============================================================

def build_source_trace(
    chunks: List[Dict[str, Any]]
) -> List[Dict[str, Any]]:
    """
    Build transparent source information for every
    selected retrieved chunk.
    """

    source_trace = []

    for chunk in chunks:
        source_trace.append({
            "chunk_id": chunk.get("chunk_id"),
            "source_file": chunk.get("source_file"),
            "page": chunk.get("page"),
            "case_id": chunk.get("case_id"),
            "case_name": chunk.get("case_name"),
            "citations": chunk.get("citations", []),
            "document_type": chunk.get(
                "document_type",
                "judgment"
            ),
            "score": chunk.get("score"),
        })

    return source_trace


# ============================================================
# Helpers
# ============================================================

def normalize_document_type(
    chunk: Dict[str, Any]
) -> str:
    """
    Normalize the document_type stored in chunk metadata.
    """

    document_type = chunk.get(
        "document_type",
        ""
    )

    if document_type is None:
        return ""

    return str(
        document_type
    ).strip().lower()


def get_chunk_key(
    chunk: Dict[str, Any]
) -> str:
    """
    Return a stable identifier used to prevent duplicate
    chunks from appearing in the final retrieval result.
    """

    chunk_id = chunk.get("chunk_id")

    if chunk_id:
        return str(chunk_id)

    return (
        f"{chunk.get('source_file', '')}:"
        f"{chunk.get('page', '')}:"
        f"{chunk.get('case_id', '')}"
    )


def get_score(
    chunk: Dict[str, Any]
) -> float:
    """
    Safely convert retrieval score to float.
    """

    try:
        return float(
            chunk.get("score", 0.0)
        )
    except (
        TypeError,
        ValueError
    ):
        return 0.0


def sort_by_score(
    chunks: List[Dict[str, Any]]
) -> List[Dict[str, Any]]:
    """
    Sort chunks from highest retrieval score to lowest.
    """

    return sorted(
        chunks,
        key=get_score,
        reverse=True
    )


def deduplicate_chunks(
    chunks: List[Dict[str, Any]]
) -> List[Dict[str, Any]]:
    """
    Remove duplicate chunks while preserving order.
    """

    unique_chunks = []
    seen: Set[str] = set()

    for chunk in chunks:
        key = get_chunk_key(chunk)

        if key in seen:
            continue

        seen.add(key)
        unique_chunks.append(chunk)

    return unique_chunks


# ============================================================
# Source-Aware Selection
# ============================================================

def select_source_aware_chunks(
    chunks: List[Dict[str, Any]],
    source_type: str,
    final_top_k: int = 3
) -> List[Dict[str, Any]]:
    """
    Select final retrieval results according to the Research
    Agent's source classification.

    Rules:

    STATUTE
        Prefer statute chunks.
        If available, include a supporting judgment only
        when needed to fill the result set.

    CONSTITUTION
        Prefer constitution chunks.
        If available, include a supporting judgment only
        when needed to fill the result set.

    CASE_LAW
        Prefer judgment chunks.

    MIXED
        Preserve source diversity when possible.
        Prefer the highest scoring relevant sources.
    """

    if not chunks:
        return []

    source_type = str(
        source_type or "mixed"
    ).strip().lower()

    if source_type not in SOURCE_TYPE_TO_DOCUMENT_TYPES:
        source_type = "mixed"

    chunks = deduplicate_chunks(chunks)
    chunks = sort_by_score(chunks)

    # --------------------------------------------------------
    # Separate chunks by document type
    # --------------------------------------------------------

    by_type: Dict[str, List[Dict[str, Any]]] = {
        "statute": [],
        "constitution": [],
        "judgment": [],
    }

    unknown_chunks = []

    for chunk in chunks:
        document_type = normalize_document_type(chunk)

        if document_type in by_type:
            by_type[document_type].append(chunk)
        else:
            unknown_chunks.append(chunk)

    # --------------------------------------------------------
    # STATUTE
    # --------------------------------------------------------

    if source_type == "statute":

        selected = []

        # First priority: statutes
        selected.extend(
            by_type["statute"][:final_top_k]
        )

        # If fewer than final_top_k statute chunks exist,
        # use judgments as supporting evidence.
        if len(selected) < final_top_k:

            remaining = final_top_k - len(selected)

            selected.extend(
                by_type["judgment"][:remaining]
            )

        # Last fallback: constitution
        if len(selected) < final_top_k:

            remaining = final_top_k - len(selected)

            selected.extend(
                by_type["constitution"][:remaining]
            )

        # Absolute fallback for unexpected metadata
        if len(selected) < final_top_k:

            selected_keys = {
                get_chunk_key(chunk)
                for chunk in selected
            }

            for chunk in unknown_chunks:

                if get_chunk_key(chunk) in selected_keys:
                    continue

                selected.append(chunk)

                if len(selected) >= final_top_k:
                    break

        return selected[:final_top_k]

    # --------------------------------------------------------
    # CONSTITUTION
    # --------------------------------------------------------

    if source_type == "constitution":

        selected = []

        # First priority: Constitution
        selected.extend(
            by_type["constitution"][:final_top_k]
        )

        # Supporting judgments
        if len(selected) < final_top_k:

            remaining = final_top_k - len(selected)

            selected.extend(
                by_type["judgment"][:remaining]
            )

        # Last fallback: statutes
        if len(selected) < final_top_k:

            remaining = final_top_k - len(selected)

            selected.extend(
                by_type["statute"][:remaining]
            )

        # Absolute fallback
        if len(selected) < final_top_k:

            selected_keys = {
                get_chunk_key(chunk)
                for chunk in selected
            }

            for chunk in unknown_chunks:

                if get_chunk_key(chunk) in selected_keys:
                    continue

                selected.append(chunk)

                if len(selected) >= final_top_k:
                    break

        return selected[:final_top_k]

    # --------------------------------------------------------
    # CASE LAW
    # --------------------------------------------------------

    if source_type == "case_law":

        selected = []

        # Primary source: judgments
        selected.extend(
            by_type["judgment"][:final_top_k]
        )

        # If necessary, fill from other legal sources.
        if len(selected) < final_top_k:

            remaining = final_top_k - len(selected)

            selected.extend(
                by_type["statute"][:remaining]
            )

        if len(selected) < final_top_k:

            remaining = final_top_k - len(selected)

            selected.extend(
                by_type["constitution"][:remaining]
            )

        # Absolute fallback
        if len(selected) < final_top_k:

            selected_keys = {
                get_chunk_key(chunk)
                for chunk in selected
            }

            for chunk in unknown_chunks:

                if get_chunk_key(chunk) in selected_keys:
                    continue

                selected.append(chunk)

                if len(selected) >= final_top_k:
                    break

        return selected[:final_top_k]

    # --------------------------------------------------------
    # MIXED
    # --------------------------------------------------------

    # For mixed questions, preserve diversity where possible.
    #
    # We select the best chunk from each available legal source
    # first, then fill remaining slots using global score.

    selected = []
    selected_keys: Set[str] = set()

    source_order = [
        "statute",
        "constitution",
        "judgment",
    ]

    # First pass:
    # one strong chunk from each available source type.
    for document_type in source_order:

        available = by_type[document_type]

        if not available:
            continue

        chunk = available[0]
        key = get_chunk_key(chunk)

        if key not in selected_keys:

            selected.append(chunk)
            selected_keys.add(key)

        if len(selected) >= final_top_k:
            break

    # Second pass:
    # fill remaining slots by overall retrieval score.
    if len(selected) < final_top_k:

        for chunk in chunks:

            key = get_chunk_key(chunk)

            if key in selected_keys:
                continue

            selected.append(chunk)
            selected_keys.add(key)

            if len(selected) >= final_top_k:
                break

    return selected[:final_top_k]


# ============================================================
# Retrieval Agent
# ============================================================

def run_retrieval_agent(
    state
):
    """
    Retrieval Agent.

    Pipeline:

        Research Agent
              |
              v
        search queries
              |
              v
        Retrieve larger candidate pool
              |
              v
        Source-aware selection
              |
              v
        Candidate citations
              |
              v
        Source Trace

    IMPORTANT:

    The lower-level retriever remains responsible for
    semantic/hybrid retrieval.

    This agent is responsible for applying the Research
    Agent's source classification to the retrieved candidates.
    """

    try:

        # ====================================================
        # 1. Read Research Plan
        # ====================================================

        research_plan = state.get(
            "research_plan",
            {}
        )

        search_queries = research_plan.get(
            "search_queries",
            []
        )

        source_type = research_plan.get(
            "source_type",
            "mixed"
        )

        if not search_queries:

            search_queries = [
                state["user_question"]
            ]

        # ====================================================
        # 2. Retrieve Larger Candidate Pool
        # ====================================================
        #
        # Previously we requested only 3 chunks.
        #
        # That made source-aware selection impossible because
        # the correct statute/constitution might be ranked
        # below the first three semantic results.
        #
        # We now retrieve 12 candidates and then select
        # the best source-aware 3.
        # ====================================================

        candidate_pool = retrieve_chunks(
            search_queries,
            top_k=12
        )

        # ====================================================
        # 3. Source-Aware Selection
        # ====================================================

        retrieved_chunks = select_source_aware_chunks(
            candidate_pool,
            source_type=source_type,
            final_top_k=3
        )

        # ====================================================
        # 4. Store Retrieved Chunks
        # ====================================================

        state["retrieved_chunks"] = retrieved_chunks

        # ====================================================
        # 5. Extract Candidate Citations
        # ====================================================

        state["candidate_citations"] = (
            extract_candidate_citations(
                retrieved_chunks
            )
        )

        # ====================================================
        # 6. Build Source Trace
        # ====================================================

        state["source_trace"] = (
            build_source_trace(
                retrieved_chunks
            )
        )

        # ====================================================
        # 7. Logging
        # ====================================================

        selected_types = [
            normalize_document_type(chunk)
            for chunk in retrieved_chunks
        ]

        selected_files = [
            chunk.get("source_file")
            for chunk in retrieved_chunks
        ]

        print(
            "\n"
            "RETRIEVAL COMPLETED\n"
            f"  Research source_type: {source_type}\n"
            f"  Candidate pool: {len(candidate_pool)}\n"
            f"  Final chunks: {len(retrieved_chunks)}\n"
            f"  Document types: {selected_types}\n"
            f"  Source files: {selected_files}\n"
        )

        state["status"] = "retrieval_completed"

        return state

    except Exception as e:

        state["status"] = "retrieval_failed"

        state.setdefault(
            "errors",
            []
        ).append(
            f"Retrieval error: {str(e)}"
        )

        return state