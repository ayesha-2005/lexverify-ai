import json
import os
import re
from src.state import AgentState

def normalize_citation(citation: str) -> str:
    """
    Normalizes citation strings by converting to uppercase, stripping whitespace,
    and collapsing multiple spaces into a single space.
    """
    citation = citation.upper().strip()
    return re.sub(r'\s+', ' ', citation)

def run_verification_agent(state: AgentState, truth_registry_path: str = "data/truth_registry.json") -> AgentState:
    """
    Agent 3: Deterministic Citation Gate. Matches extracted candidate citations
    against truth_registry.json using exact key lookups without calling an LLM.
    """
    try:
        # 1. Load Truth Registry database
        if not os.path.exists(truth_registry_path):
            state["errors"].append(f"Truth Registry File Not Found at '{truth_registry_path}'")
            state["status"] = "verification_failed"
            return state

        with open(truth_registry_path, "r", encoding="utf-8") as f:
            truth_registry = json.load(f)

        # Normalize truth registry keys for case-insensitive exact matching
        normalized_registry = {normalize_citation(k): v for k, v in truth_registry.items()}

        verified = []
        rejected = []

        # 2. Perform deterministic string matching
        for citation in state.get("candidate_citations", []):
            norm_key = normalize_citation(citation)
            if norm_key in normalized_registry:
                meta = normalized_registry[norm_key]
                verified.append({
                    "citation": norm_key,
                    "title": meta.get("title", "Unknown Case"),
                    "court": meta.get("court", "Unknown Court"),
                    "year": meta.get("year", "N/A"),
                    "snippet": meta.get("snippet", "")
                })
            else:
                rejected.append(citation)

        state["verified_citations"] = verified
        state["rejected_citations"] = rejected
        state["status"] = "verification_completed"

    except Exception as e:
        state["errors"].append(f"Verification Agent Error: {str(e)}")
        state["status"] = "verification_failed"

    return state