import json
import re
from typing import Any, Dict, List, Optional

from rapidfuzz import fuzz


# ============================================================
# Configuration
# ============================================================

FUZZY_THRESHOLD = 90


# ============================================================
# Citation Normalization
# ============================================================

def normalize_citation(citation: str) -> str:
    """
    Normalize citation formatting while preserving
    the actual legal citation information.
    """

    citation = str(citation).strip()

    # Lowercase
    citation = citation.lower()

    # Normalize whitespace
    citation = re.sub(r"\s+", " ", citation)

    # Normalize common spacing around punctuation
    citation = re.sub(r"\s*,\s*", ", ", citation)
    citation = re.sub(r"\s*-\s*", "-", citation)

    # Remove unnecessary spaces between common citation components.
    # Example:
    # PLD 2024 SC 123
    # PLD 2024 SC123
    citation = re.sub(
        r"\b(sc|pld|scr|ylr|psc|clc)\s+(\d+)\b",
        r"\1 \2",
        citation,
        flags=re.IGNORECASE
    )

    return citation.strip()


# ============================================================
# Registry Preparation
# ============================================================

def build_normalized_registry(
    truth_registry: List[Dict[str, Any]]
) -> Dict[str, Dict[str, Any]]:
    """
    Build normalized citation lookup.

    Expected registry format:

    [
        {
            "citation": "PLD 2021 SC 1",
            "source": "Justice_Qazi_Faez_Isa.pdf",
            ...
        }
    ]
    """

    normalized_registry = {}

    for record in truth_registry:
        citation = record.get("citation")

        if not citation:
            continue

        normalized = normalize_citation(citation)

        normalized_registry[normalized] = record

    return normalized_registry


# ============================================================
# Fuzzy Matching
# ============================================================

def find_fuzzy_match(
    citation: str,
    truth_registry: List[Dict[str, Any]],
    threshold: int = FUZZY_THRESHOLD
):
    """
    Find the strongest fuzzy match in the Truth Registry.

    Returns:

    {
        "record": registry record or None,
        "score": integer,
        "matched_citation": string or None
    }
    """

    normalized_candidate = normalize_citation(citation)

    best_record = None
    best_score = 0
    best_citation = None

    for record in truth_registry:
        registry_citation = record.get("citation")

        if not registry_citation:
            continue

        normalized_registry = normalize_citation(
            registry_citation
        )

        score = fuzz.ratio(
            normalized_candidate,
            normalized_registry
        )

        if score > best_score:
            best_score = score
            best_record = record
            best_citation = registry_citation

    if best_record and best_score >= threshold:
        return {
            "record": best_record,
            "score": best_score,
            "matched_citation": best_citation
        }

    return {
        "record": None,
        "score": best_score,
        "matched_citation": best_citation
    }


# ============================================================
# Single Citation Verification
# ============================================================

def verify_citation(
    citation: str,
    truth_registry: List[Dict[str, Any]],
    threshold: int = FUZZY_THRESHOLD
) -> Dict[str, Any]:

    normalized_candidate = normalize_citation(
        citation
    )

    normalized_registry = build_normalized_registry(
        truth_registry
    )

    # --------------------------------------------------------
    # 1. Exact Match
    # --------------------------------------------------------

    if normalized_candidate in normalized_registry:

        record = normalized_registry[
            normalized_candidate
        ]

        return {
            "citation": citation,
            "verified": True,
            "match_type": "exact",
            "match_score": 100,
            "matched_citation": record.get(
                "citation"
            ),
            "citation_reason": (
                "Exact citation match found "
                "in the Truth Registry."
            ),
            "source": record.get("source"),
            "record": record
        }

    # --------------------------------------------------------
    # 2. Fuzzy Match
    # --------------------------------------------------------

    fuzzy_result = find_fuzzy_match(
        citation,
        truth_registry,
        threshold
    )

    if fuzzy_result["record"]:

        record = fuzzy_result["record"]

        return {
            "citation": citation,
            "verified": True,
            "match_type": "fuzzy",
            "match_score": fuzzy_result["score"],
            "matched_citation": fuzzy_result[
                "matched_citation"
            ],
            "citation_reason": (
                "Citation formatting differs from "
                "the Truth Registry, but the citation "
                "matches above the verification threshold."
            ),
            "source": record.get("source"),
            "record": record
        }

    # --------------------------------------------------------
    # 3. Rejected
    # --------------------------------------------------------

    return {
        "citation": citation,
        "verified": False,
        "match_type": "none",
        "match_score": fuzzy_result["score"],
        "matched_citation": fuzzy_result[
            "matched_citation"
        ],
        "citation_reason": (
            "Citation was not found in the Truth Registry "
            "and did not meet the fuzzy matching threshold."
        ),
        "source": None,
        "record": None
    }


# ============================================================
# Multiple Citation Verification
# ============================================================

def verify_citations(
    candidate_citations: List[str],
    truth_registry: List[Dict[str, Any]],
    threshold: int = FUZZY_THRESHOLD
):
    """
    Verify all candidate citations.

    Returns:

    verified
    rejected
    verification_results
    """

    verified = []
    rejected = []
    verification_results = []

    for citation in candidate_citations:

        result = verify_citation(
            citation,
            truth_registry,
            threshold
        )

        verification_results.append(
            result
        )

        if result["verified"]:
            verified.append(result)
        else:
            rejected.append(citation)

    return (
        verified,
        rejected,
        verification_results
    )


# ============================================================
# Agent Integration
# ============================================================

def run_verification(
    state: Dict[str, Any],
    truth_registry: Optional[Any] = None,
    registry_path: str = "data/truth_registry.json",
) -> Dict[str, Any]:
    """
    Run deterministic citation verification.

    Backward compatibility:
    1. run_verification(state)
       -> loads the existing V1 JSON registry.

    2. run_verification(state, registry_path="...")
       -> loads registry from the supplied path.

    3. run_verification(state, truth_registry)
       -> directly uses a V2 list-style registry.

    The existing V1 dictionary-style registry is converted internally
    into the V2 list-style representation.
    """

    try:
        # ---------------------------------------------------------
        # 1. Resolve registry
        # ---------------------------------------------------------
        if truth_registry is None:
            with open(registry_path, "r", encoding="utf-8") as f:
                truth_registry = json.load(f)

        # ---------------------------------------------------------
        # 2. Convert V1 dict registry -> V2 list registry
        # ---------------------------------------------------------
        if isinstance(truth_registry, dict):
            normalized_registry = []

            for citation, metadata in truth_registry.items():
                record = {
                    "citation": citation,
                    **metadata,
                }
                normalized_registry.append(record)

            truth_registry = normalized_registry

        # ---------------------------------------------------------
        # 3. Validate registry format
        # ---------------------------------------------------------
        if not isinstance(truth_registry, list):
            raise TypeError(
                "Truth registry must be either a list or a dictionary."
            )

        # ---------------------------------------------------------
        # 4. Get candidate citations from state
        # ---------------------------------------------------------
        candidate_citations = state.get("candidate_citations", [])

        # ---------------------------------------------------------
        # 5. Verify citations deterministically
        # ---------------------------------------------------------
        verified, rejected, verification_results = verify_citations(
            candidate_citations,
            truth_registry,
            threshold=FUZZY_THRESHOLD,
        )

        # ---------------------------------------------------------
        # 6. Store V2 outputs
        # ---------------------------------------------------------
        state["verified_citations"] = verified
        state["rejected_citations"] = rejected
        state["verification_results"] = verification_results

        state["metrics_summary"] = {
            "total_citations": len(candidate_citations),
            "verified_count": len(verified),
            "rejected_count": len(rejected),
        }

        state["status"] = "verification_completed"

        return state

    except Exception as e:
        state["status"] = "verification_failed"

        state.setdefault("errors", []).append(
            {
                "stage": "verification",
                "error": str(e),
            }
        )

        return state