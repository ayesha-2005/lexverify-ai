import json
import os
import re
from src.state import AgentState

# Comprehensive Regex for Pakistani Case Law Citations
CITATION_REGEX = re.compile(
    r'\b(?:'
    r'(?:PLD|PLJ|SCMR|YLR|CLC|PCrLJ|PTD|PLC|GBLR|KLR|PSC)\s+\d{4}(?:\s+[A-Za-z\.]+)*\s+\d+|'
    r'\d{4}\s+(?:PLD|PLJ|SCMR|YLR|CLC|PCrLJ|PTD|PLC|GBLR|KLR|PSC)(?:\s+[A-Za-z\.]+)*\s+\d+'
    r')\b',
    re.IGNORECASE
)

def normalize_citation(citation: str) -> str:
    """Normalizes citation strings for consistent lookup."""
    if not citation:
        return ""
    c = str(citation).upper().strip()
    
    # Handle CRL. abbreviation variation before stripping periods
    c = c.replace("CRL.", "CRL")
    
    # Normalize common court acronyms and remove remaining periods
    c = c.replace("SUPREME COURT", "SC").replace("CRIMINAL CASES", "CR").replace(".", "")
    c = re.sub(r'(?<=[A-Z])\s+(?=[A-Z])', '', c)
    return re.sub(r'\s+', ' ', c)

def extract_citations_from_text(text: str) -> list[str]:
    """Extracts Pakistani legal citations directly from text."""
    if not text:
        return []
    matches = CITATION_REGEX.findall(text)
    return list(dict.fromkeys([m.strip() for m in matches]))

def run_verification_agent(state: AgentState, truth_registry_path: str = "data/truth_registry.json") -> AgentState:
    """
    Agent 3: Verification Gate. Checks extracted citations against truth_registry.json.
    """
    try:
        if not os.path.exists(truth_registry_path):
            state["errors"].append(f"Truth Registry File Not Found at '{truth_registry_path}'")
            state["status"] = "verification_failed"
            return state

        with open(truth_registry_path, "r", encoding="utf-8") as f:
            truth_registry = json.load(f)

        normalized_registry = {}
        for raw_key, meta in truth_registry.items():
            norm_k = normalize_citation(raw_key)
            normalized_registry[norm_k] = (raw_key, meta)

        # Force extraction from chunks if candidates list is empty
        candidates = state.get("candidate_citations", [])
        if not candidates:
            all_text_content = state.get("user_question", "") + " "
            for chunk in state.get("retrieved_chunks", []):
                if isinstance(chunk, dict):
                    all_text_content += f" {chunk.get('text', '')} {chunk.get('source_file', '')}"
                else:
                    all_text_content += f" {str(chunk)}"
            candidates = extract_citations_from_text(all_text_content)

        verified = []
        rejected = []
        seen_verified = set()

        for citation in candidates:
            norm_cand = normalize_citation(citation)
            if not norm_cand:
                continue

            matched_meta = None
            matched_official_key = None

            if norm_cand in normalized_registry:
                matched_official_key, matched_meta = normalized_registry[norm_cand]
            else:
                for reg_norm_key, (official_key, meta) in normalized_registry.items():
                    if norm_cand in reg_norm_key or reg_norm_key in norm_cand:
                        matched_official_key = official_key
                        matched_meta = meta
                        break

            if matched_meta:
                if matched_official_key not in seen_verified:
                    seen_verified.add(matched_official_key)
                    verified.append({
                        "citation": matched_official_key,
                        "title": matched_meta.get("case_name", matched_meta.get("title", "Unknown Case")),
                        "court": matched_meta.get("court", "Unknown Court"),
                        "year": str(matched_meta.get("year", "N/A"))
                    })
            else:
                if citation not in rejected:
                    rejected.append(citation)

        state["verified_citations"] = verified
        state["rejected_citations"] = rejected
        state["status"] = "verification_completed"

    except Exception as e:
        state["errors"].append(f"Verification Error: {str(e)}")
        state["status"] = "verification_failed"

    return state