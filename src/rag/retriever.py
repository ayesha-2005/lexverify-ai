import json
import re
from pathlib import Path
from typing import List, Dict, Any, Optional

import faiss
from sentence_transformers import SentenceTransformer


PROJECT_ROOT = Path(__file__).resolve().parents[2]

FAISS_INDEX_PATH = PROJECT_ROOT / "data" / "faiss_index" / "legal_cases.faiss"
FAISS_METADATA_PATH = PROJECT_ROOT / "data" / "faiss_index" / "metadata.json"

EMBEDDING_MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"

SIMILARITY_THRESHOLD = 0.50

# Retrieve a large FAISS pool first.
DEFAULT_CANDIDATE_POOL = 100

# Small semantic/lexical adjustments.
LEXICAL_BOOST = 0.04


_model = None
_index = None
_metadata = None


SOURCE_TYPE_TO_DOCUMENT_TYPES = {
    "statute": {"statute"},
    "constitution": {"constitution"},
    "case_law": {"judgment"},
    "mixed": {"statute", "constitution", "judgment"},
}


def _load_model():
    global _model

    if _model is None:
        _model = SentenceTransformer(EMBEDDING_MODEL_NAME)

    return _model


def _load_index():
    global _index

    if _index is None:
        if not FAISS_INDEX_PATH.exists():
            raise FileNotFoundError(
                f"FAISS index not found: {FAISS_INDEX_PATH}"
            )

        _index = faiss.read_index(str(FAISS_INDEX_PATH))

    return _index


def _load_metadata():
    global _metadata

    if _metadata is None:
        if not FAISS_METADATA_PATH.exists():
            raise FileNotFoundError(
                f"FAISS metadata not found: {FAISS_METADATA_PATH}"
            )

        with open(FAISS_METADATA_PATH, "r", encoding="utf-8") as f:
            _metadata = json.load(f)

    return _metadata


def _get_metadata_item(
    metadata: Any,
    index: int
) -> Dict[str, Any]:

    if isinstance(metadata, list):

        if 0 <= index < len(metadata):
            item = metadata[index]

            if isinstance(item, dict):
                return item

        return {}

    if isinstance(metadata, dict):

        item = metadata.get(str(index))

        if isinstance(item, dict):
            return item

        chunks = metadata.get("chunks")

        if isinstance(chunks, list):

            if 0 <= index < len(chunks):
                item = chunks[index]

                if isinstance(item, dict):
                    return item

        metadata_list = metadata.get("metadata")

        if isinstance(metadata_list, list):

            if 0 <= index < len(metadata_list):
                item = metadata_list[index]

                if isinstance(item, dict):
                    return item

    return {}


def _normalize_document_type(value: Any) -> str:

    value = str(value or "").strip().lower()

    aliases = {
        "case": "judgment",
        "case_law": "judgment",
        "case-law": "judgment",
        "judgement": "judgment",
        "judgment": "judgment",
        "statute": "statute",
        "constitution": "constitution",
    }

    return aliases.get(value, value)


def _extract_legal_terms(query: str) -> List[str]:

    query_lower = query.lower()

    terms = []

    patterns = [
        r"\bsection\s+\d+[a-z]?(?:\(\d+\))?",
        r"\bsec(?:tion)?\.?\s+\d+[a-z]?(?:\(\d+\))?",
        r"\barticle\s+\d+[a-z]?(?:\(\d+\))?",
        r"\bpre[-\s]?arrest bail\b",
        r"\bpost[-\s]?arrest bail\b",
        r"\bbail\b",
        r"\bcr\.?\s*p\.?\s*c\.?\b",
        r"\bcrpc\b",
        r"\bcode of criminal procedure\b",
        r"\bpakistan penal code\b",
        r"\bppc\b",
    ]

    for pattern in patterns:

        matches = re.findall(pattern, query_lower)

        for match in matches:

            normalized = re.sub(r"\s+", " ", match).strip()

            if normalized and normalized not in terms:
                terms.append(normalized)

    return terms


def _lexical_score(
    query: str,
    chunk: Dict[str, Any]
) -> float:

    query_lower = query.lower()

    terms = _extract_legal_terms(query)

    if not terms:
        return 0.0

    searchable_text = " ".join(
        [
            str(chunk.get("text", "")),
            str(chunk.get("topic", "")),
            str(chunk.get("case_name", "")),
            " ".join(map(str, chunk.get("sections", []))),
            " ".join(map(str, chunk.get("citations", []))),
            str(chunk.get("source_file", "")),
        ]
    ).lower()

    matched = 0

    for term in terms:

        if term in searchable_text:
            matched += 1

    return matched / len(terms)


def _build_result(
    chunk: Dict[str, Any],
    score: float,
    query: str
) -> Dict[str, Any]:

    lexical_score = _lexical_score(query, chunk)

    ranked_score = score + (
        LEXICAL_BOOST * lexical_score
    )

    return {
        "chunk_id": chunk.get("chunk_id", ""),
        "case_id": chunk.get("case_id", ""),
        "case_name": chunk.get("case_name", ""),
        "citations": chunk.get("citations", []),
        "court": chunk.get("court", ""),
        "date": chunk.get("date", ""),
        "topic": chunk.get("topic", ""),
        "sections": chunk.get("sections", []),
        "principles": chunk.get("principles", []),
        "document_type": chunk.get("document_type", ""),
        "source_file": chunk.get("source_file", ""),
        "page": chunk.get("page", ""),
        "score": score,
        "lexical_score": lexical_score,
        "ranked_score": ranked_score,
        "text": chunk.get("text", ""),
    }


def retrieve_chunks(
    search_queries: List[str],
    top_k: int = 3,
    source_type: Optional[str] = None,
    candidate_pool: int = DEFAULT_CANDIDATE_POOL,
) -> List[Dict[str, Any]]:

    if not search_queries:
        return []

    if isinstance(search_queries, str):
        search_queries = [search_queries]

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

    source_type = (
        str(source_type).strip().lower()
        if source_type
        else None
    )

    allowed_document_types = SOURCE_TYPE_TO_DOCUMENT_TYPES.get(
        source_type
    )

    embeddings = model.encode(
        queries,
        convert_to_numpy=True,
        normalize_embeddings=True,
    )

    distances, indices = index.search(
        embeddings,
        candidate_pool,
    )

    # ---------------------------------------------------------
    # IMPORTANT:
    #
    # When a source type is explicitly requested, collect
    # candidates separately by document type.
    #
    # This prevents highly similar judgments from completely
    # crowding out relevant statute/constitution chunks.
    # ---------------------------------------------------------

    results_by_chunk = {}

    for query_number, query in enumerate(queries):

        for result_number in range(candidate_pool):

            chunk_index = int(
                indices[query_number, result_number]
            )

            score = float(
                distances[query_number, result_number]
            )

            if chunk_index < 0:
                continue

            if score < SIMILARITY_THRESHOLD:
                continue

            chunk = _get_metadata_item(
                metadata,
                chunk_index
            )

            if not chunk:
                continue

            document_type = _normalize_document_type(
                chunk.get("document_type", "")
            )

            # -------------------------------------------------
            # Source-aware filtering.
            #
            # If Research Agent says statute, only statutes
            # participate in the final retrieval ranking.
            # -------------------------------------------------

            if allowed_document_types:

                if document_type not in allowed_document_types:
                    continue

            chunk_id = chunk.get(
                "chunk_id",
                str(chunk_index)
            )

            result = _build_result(
                chunk,
                score,
                query,
            )

            if (
                chunk_id not in results_by_chunk
                or result["ranked_score"]
                > results_by_chunk[chunk_id]["ranked_score"]
            ):

                results_by_chunk[chunk_id] = result

    results = sorted(
        results_by_chunk.values(),
        key=lambda x: x["ranked_score"],
        reverse=True,
    )

    return results[:top_k]


def retrieve(
    query: str,
    top_k: int = 3,
    source_type: Optional[str] = None,
) -> List[Dict[str, Any]]:

    return retrieve_chunks(
        [query],
        top_k=top_k,
        source_type=source_type,
    )


if __name__ == "__main__":

    print("=" * 70)
    print("LexVerify AI - Source-Aware FAISS Retriever Test")
    print("=" * 70)

    query = (
        "What is the difference between "
        "pre-arrest bail and post-arrest bail in Pakistan?"
    )

    print(f"\nQuery: {query}")

    results = retrieve_chunks(
        [query],
        top_k=5,
        source_type="statute",
    )

    print(
        f"\nRetrieved {len(results)} statute chunks:\n"
    )

    for i, result in enumerate(results, start=1):

        print(
            f"{i}. "
            f"{result.get('source_file', '')} "
            f"page {result.get('page', '')}"
        )

        print(
            f"   Document type: "
            f"{result.get('document_type', '')}"
        )

        print(
            f"   Citation: "
            f"{result.get('citations', [])}"
        )

        print(
            f"   Semantic score: "
            f"{result.get('score', 0):.4f}"
        )

        print(
            f"   Ranked score: "
            f"{result.get('ranked_score', 0):.4f}"
        )

        print()