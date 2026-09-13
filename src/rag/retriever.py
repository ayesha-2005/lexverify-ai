import json
from pathlib import Path
from typing import List, Dict, Any

import faiss
from sentence_transformers import SentenceTransformer


# ---------------------------------------------------------
# Project paths
# ---------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parents[2]

FAISS_INDEX_PATH = (
    PROJECT_ROOT
    / "data"
    / "faiss_index"
    / "legal_cases.faiss"
)

FAISS_METADATA_PATH = (
    PROJECT_ROOT
    / "data"
    / "faiss_index"
    / "metadata.json"
)


# ---------------------------------------------------------
# Retrieval configuration
# ---------------------------------------------------------

EMBEDDING_MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"

SIMILARITY_THRESHOLD = 0.55


# ---------------------------------------------------------
# Lazy-loaded resources
# ---------------------------------------------------------

_model = None
_index = None
_metadata = None


def _load_model():
    global _model

    if _model is None:
        _model = SentenceTransformer(
            EMBEDDING_MODEL_NAME
        )

    return _model


def _load_index():
    global _index

    if _index is None:

        if not FAISS_INDEX_PATH.exists():
            raise FileNotFoundError(
                f"FAISS index not found: {FAISS_INDEX_PATH}"
            )

        _index = faiss.read_index(
            str(FAISS_INDEX_PATH)
        )

    return _index


def _load_metadata():
    global _metadata

    if _metadata is None:

        if not FAISS_METADATA_PATH.exists():
            raise FileNotFoundError(
                f"FAISS metadata not found: "
                f"{FAISS_METADATA_PATH}"
            )

        with open(
            FAISS_METADATA_PATH,
            "r",
            encoding="utf-8"
        ) as f:

            _metadata = json.load(f)

    return _metadata


# ---------------------------------------------------------
# Metadata helper
# ---------------------------------------------------------

def _get_metadata_item(
    metadata: Any,
    index: int
) -> Dict[str, Any]:

    """
    Supports the metadata structures produced by the
    FAISS index-building pipeline.
    """

    if isinstance(metadata, list):

        if 0 <= index < len(metadata):
            item = metadata[index]

            if isinstance(item, dict):
                return item

        return {}

    if isinstance(metadata, dict):

        # Possible format:
        # {"0": {...}, "1": {...}}

        item = metadata.get(str(index))

        if isinstance(item, dict):
            return item

        # Possible format:
        # {"chunks": [...]}

        chunks = metadata.get("chunks")

        if isinstance(chunks, list):
            if 0 <= index < len(chunks):

                item = chunks[index]

                if isinstance(item, dict):
                    return item

        # Possible format:
        # {"metadata": [...]}

        metadata_list = metadata.get("metadata")

        if isinstance(metadata_list, list):
            if 0 <= index < len(metadata_list):

                item = metadata_list[index]

                if isinstance(item, dict):
                    return item

    return {}


# ---------------------------------------------------------
# Main retrieval function
# ---------------------------------------------------------

def retrieve_chunks(
    search_queries: List[str],
    top_k: int = 3
) -> List[Dict[str, Any]]:

    """
    Retrieve the most relevant legal chunks from FAISS.

    Parameters
    ----------
    search_queries:
        One or more semantic search queries.

    top_k:
        Number of final chunks to return.

    Returns
    -------
    List[Dict[str, Any]]
        Retrieved chunks with legal metadata and similarity
        scores.
    """

    if not search_queries:
        return []

    if isinstance(search_queries, str):
        search_queries = [search_queries]

    # Remove empty queries
    queries = [
        str(q).strip()
        for q in search_queries
        if str(q).strip()
    ]

    if not queries:
        return []

    model = _load_model()
    index = _load_index()
    metadata = _load_metadata()

    # -----------------------------------------------------
    # Encode all search queries
    # -----------------------------------------------------

    embeddings = model.encode(
        queries,
        convert_to_numpy=True,
        normalize_embeddings=True
    )

    # -----------------------------------------------------
    # Search FAISS
    # -----------------------------------------------------

    distances, indices = index.search(
        embeddings,
        top_k
    )

    # -----------------------------------------------------
    # Merge results from multiple queries
    # -----------------------------------------------------

    results_by_chunk = {}

    for query_number in range(
        len(queries)
    ):

        for result_number in range(
            top_k
        ):

            chunk_index = int(
                indices[
                    query_number,
                    result_number
                ]
            )

            score = float(
                distances[
                    query_number,
                    result_number
                ]
            )

            # FAISS can return -1 when no result exists
            if chunk_index < 0:
                continue

            # Ignore weak matches
            if score < SIMILARITY_THRESHOLD:
                continue

            chunk = _get_metadata_item(
                metadata,
                chunk_index
            )

            if not chunk:
                continue

            chunk_id = chunk.get(
                "chunk_id",
                str(chunk_index)
            )

            # Keep the highest score if the same chunk
            # appears for multiple search queries.
            if (
                chunk_id not in results_by_chunk
                or score > results_by_chunk[
                    chunk_id
                ]["score"]
            ):

                result = {
                    "chunk_id": chunk_id,

                    "case_id": chunk.get(
                        "case_id",
                        ""
                    ),

                    "case_name": chunk.get(
                        "case_name",
                        ""
                    ),

                    "citations": chunk.get(
                        "citations",
                        []
                    ),

                    "court": chunk.get(
                        "court",
                        ""
                    ),

                    "date": chunk.get(
                        "date",
                        ""
                    ),

                    "topic": chunk.get(
                        "topic",
                        ""
                    ),

                    "sections": chunk.get(
                        "sections",
                        []
                    ),

                    "principles": chunk.get(
                        "principles",
                        []
                    ),

                    "source_file": chunk.get(
                        "source_file",
                        ""
                    ),

                    "page": chunk.get(
                        "page",
                        ""
                    ),

                    "score": score,

                    "text": chunk.get(
                        "text",
                        ""
                    )
                }

                results_by_chunk[
                    chunk_id
                ] = result

    # -----------------------------------------------------
    # Sort by highest similarity
    # -----------------------------------------------------

    results = sorted(
        results_by_chunk.values(),
        key=lambda x: x["score"],
        reverse=True
    )

    return results[:top_k]


# ---------------------------------------------------------
# Backward-compatible helper
# ---------------------------------------------------------

def retrieve(
    query: str,
    top_k: int = 3
) -> List[Dict[str, Any]]:

    """
    Backward-compatible single-query interface.
    """

    return retrieve_chunks(
        [query],
        top_k=top_k
    )


# ---------------------------------------------------------
# Quick manual test
# ---------------------------------------------------------

if __name__ == "__main__":

    print("=" * 70)
    print("LexVerify AI - FAISS Retriever Test")
    print("=" * 70)

    query = "bail standards in non-bailable offenses"

    print(f"\nQuery: {query}")

    results = retrieve_chunks(
        [query],
        top_k=3
    )

    print(
        f"\nRetrieved {len(results)} chunks:\n"
    )

    for i, result in enumerate(
        results,
        start=1
    ):

        print(
            f"{i}. {result.get('case_name', 'Unknown')}"
        )

        print(
            f"   Citation: "
            f"{result.get('citations', [])}"
        )

        print(
            f"   Score: "
            f"{result.get('score', 0):.4f}"
        )

        print(
            f"   Source: "
            f"{result.get('source_file', '')}"
        )

        print()