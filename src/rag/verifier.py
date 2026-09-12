import json
import re
from pathlib import Path
from typing import List, Dict, Any

# Project root:
# E:\LexVerify-AI\lexverify-ai
PROJECT_ROOT = Path(__file__).resolve().parents[2]

TRUTH_REGISTRY_PATH = PROJECT_ROOT / "data" / "truth_registry.json"


def load_truth_registry() -> Dict[str, Any]:
    """
    Load the curated Truth Registry.

    The registry is the source of truth for citation verification.
    """

    if not TRUTH_REGISTRY_PATH.exists():
        raise FileNotFoundError(
            f"Truth Registry not found: {TRUTH_REGISTRY_PATH}"
        )

    with open(TRUTH_REGISTRY_PATH, "r", encoding="utf-8") as f:
        registry = json.load(f)

    return registry


def normalize_citation(citation: str) -> str:
    """
    Normalize citation formatting so small spacing/case differences
    do not cause unnecessary rejection.

    Example:
        ' PLD 2022 SC 764 ' -> 'pld 2022 sc 764'
    """

    if not citation:
        return ""

    citation = str(citation).strip()

    # Normalize whitespace
    citation = re.sub(r"\s+", " ", citation)

    return citation.lower()


def build_normalized_registry(
    registry: Dict[str, Any]
) -> Dict[str, Dict[str, Any]]:
    """
    Create a normalized lookup table while preserving the original
    registry information.
    """

    normalized = {}

    for citation, record in registry.items():
        normalized_citation = normalize_citation(citation)

        if normalized_citation:
            normalized[normalized_citation] = {
                "citation": citation,
                **record
            }

    return normalized


def verify_citations(
    candidate_citations: List[str]
) -> tuple[List[Dict[str, Any]], List[str]]:
    """
    Verify candidate citations against the curated Truth Registry.

    Returns:
        verified_citations
        rejected_citations
    """

    registry = load_truth_registry()
    normalized_registry = build_normalized_registry(registry)

    verified = []
    rejected = []

    seen_verified = set()
    seen_rejected = set()

    for citation in candidate_citations:

        if not citation:
            continue

        original_citation = str(citation).strip()
        normalized_citation = normalize_citation(original_citation)

        if normalized_citation in normalized_registry:

            record = normalized_registry[normalized_citation]

            # Avoid duplicate verified citations
            if normalized_citation not in seen_verified:

                verified.append({
                    "citation": record["citation"],
                    "verified": True,
                    "case_name": record.get("case_name", ""),
                    "court": record.get("court", ""),
                    "year": record.get("year", ""),
                    "source": record.get("source", "")
                })

                seen_verified.add(normalized_citation)

        else:

            # Avoid duplicate rejected citations
            if normalized_citation not in seen_rejected:

                rejected.append(original_citation)
                seen_rejected.add(normalized_citation)

    return verified, rejected


def run_verification(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Verification Agent.

    Reads candidate_citations from AgentState and updates:

        verified_citations
        rejected_citations
        status
        errors
    """

    state["status"] = "verifying"

    try:

        candidate_citations = state.get("candidate_citations", [])

        verified, rejected = verify_citations(candidate_citations)

        state["verified_citations"] = verified
        state["rejected_citations"] = rejected

        if rejected and verified:
            state["status"] = "partially_verified"

        elif verified:
            state["status"] = "verified"

        elif rejected:
            state["status"] = "rejected"

        else:
            state["status"] = "no_citations"

        return state

    except Exception as e:

        error_message = f"Verification error: {str(e)}"

        state.setdefault("errors", []).append(error_message)
        state["status"] = "verification_error"

        return state


# ---------------------------------------------------------
# Backward-compatible helper
# ---------------------------------------------------------

def verify_citation(citation: str) -> Dict[str, Any]:
    """
    Verify a single citation.

    Useful for testing and for future agent integration.
    """

    verified, rejected = verify_citations([citation])

    if verified:
        return verified[0]

    return {
        "citation": citation,
        "verified": False,
        "reason": "Citation not found in Truth Registry"
    }


# ---------------------------------------------------------
# Command-line test
# ---------------------------------------------------------

if __name__ == "__main__":

    print("=" * 60)
    print("LexVerify AI - Truth Gate Test")
    print("=" * 60)

    test_citations = [
        "PLD 2022 SC 764",
        "2018 YLR 323",
        "PLD 2025 SC 999"
    ]

    print("\nTesting citations:")

    for citation in test_citations:

        result = verify_citation(citation)

        print(f"\nCitation: {citation}")
        print(f"Verified: {result['verified']}")

        if result["verified"]:
            print(f"Case: {result.get('case_name')}")
            print(f"Court: {result.get('court')}")
        else:
            print(f"Reason: {result.get('reason')}")

    print("\n" + "=" * 60)