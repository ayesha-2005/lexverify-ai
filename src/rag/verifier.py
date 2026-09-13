import json
import re
from pathlib import Path
from typing import List, Dict, Any, Tuple


PROJECT_ROOT = Path(__file__).resolve().parents[2]

DEFAULT_TRUTH_REGISTRY_PATH = (
    PROJECT_ROOT / "data" / "truth_registry.json"
)


def load_truth_registry(
    registry_path: str | Path | None = None
) -> Dict[str, Any]:

    path = (
        Path(registry_path)
        if registry_path
        else DEFAULT_TRUTH_REGISTRY_PATH
    )

    if not path.is_absolute():
        path = PROJECT_ROOT / path

    if not path.exists():
        raise FileNotFoundError(
            f"Truth Registry not found: {path}"
        )

    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def normalize_citation(citation: str) -> str:

    if not citation:
        return ""

    citation = str(citation).strip()

    citation = re.sub(
        r"\s+",
        " ",
        citation
    )

    return citation.lower()


def build_normalized_registry(
    registry: Dict[str, Any]
) -> Dict[str, Dict[str, Any]]:

    normalized = {}

    for citation, record in registry.items():

        normalized_citation = normalize_citation(
            citation
        )

        if normalized_citation:

            normalized[normalized_citation] = {
                "citation": citation,
                **record
            }

    return normalized


def verify_citations(
    candidate_citations: List[str],
    registry_path: str | Path | None = None
) -> Tuple[List[Dict[str, Any]], List[str]]:

    registry = load_truth_registry(
        registry_path
    )

    normalized_registry = build_normalized_registry(
        registry
    )

    verified = []
    rejected = []

    seen_verified = set()
    seen_rejected = set()

    for citation in candidate_citations:

        if not citation:
            continue

        original = str(citation).strip()

        normalized = normalize_citation(
            original
        )

        if not normalized:
            continue

        if normalized in normalized_registry:

            record = normalized_registry[
                normalized
            ]

            if normalized not in seen_verified:

                verified.append({
                    "citation": record["citation"],
                    "verified": True,
                    "case_name": record.get(
                        "case_name",
                        ""
                    ),
                    "court": record.get(
                        "court",
                        ""
                    ),
                    "year": record.get(
                        "year",
                        ""
                    ),
                    "source": record.get(
                        "source",
                        ""
                    )
                })

                seen_verified.add(normalized)

        else:

            if normalized not in seen_rejected:

                rejected.append(original)

                seen_rejected.add(
                    normalized
                )

    return verified, rejected


def run_verification(
    state: Dict[str, Any],
    registry_path: str | Path | None = None
) -> Dict[str, Any]:

    state["status"] = "verifying"

    try:

        candidates = state.get(
            "candidate_citations",
            []
        )

        verified, rejected = verify_citations(
            candidates,
            registry_path=registry_path
        )

        state["verified_citations"] = verified
        state["rejected_citations"] = rejected

        if verified and rejected:

            state["status"] = "partially_verified"

        elif verified:

            state["status"] = "verified"

        elif rejected:

            state["status"] = "rejected"

        else:

            state["status"] = "no_citations"

        return state

    except Exception as e:

        state.setdefault(
            "errors",
            []
        ).append(
            f"Verification error: {str(e)}"
        )

        state["status"] = "verification_failed"

        return state


def verify_citation(
    citation: str,
    registry_path: str | Path | None = None
) -> Dict[str, Any]:

    verified, rejected = verify_citations(
        [citation],
        registry_path=registry_path
    )

    if verified:
        return verified[0]

    return {
        "citation": citation,
        "verified": False,
        "reason": "Citation not found in Truth Registry"
    }


if __name__ == "__main__":

    print("=" * 60)
    print("LexVerify AI - Truth Gate Test")
    print("=" * 60)

    test_citations = [
        "PLD 2022 SC 764",
        "2018 YLR 323",
        "PLD 2025 SC 999"
    ]

    for citation in test_citations:

        result = verify_citation(citation)

        print(f"\nCitation: {citation}")
        print(f"Verified: {result['verified']}")

        if result["verified"]:

            print(
                f"Case: {result.get('case_name')}"
            )

            print(
                f"Court: {result.get('court')}"
            )

        else:

            print(
                f"Reason: {result.get('reason')}"
            )

    print("\n" + "=" * 60)