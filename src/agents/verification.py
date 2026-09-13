import json
import os
import re
from src.state import AgentState

# Updated Regex: Handles dots inside reporter acronyms like PCr.LJ, P.Cr.L.J., P Cr. LJ
CITATION_REGEX = re.compile(
    r'\b(?:'
    r'(?:PLD|PLJ|SCMR|YLR|CLC|PCr\.?LJ|PCrLJ|PTD|PLC|GBLR|KLR|PSC)\s+\d{4}(?:\s+[A-Za-z\.]+)*\s+\d+|'
    r'\d{4}\s+(?:PLD|PLJ|SCMR|YLR|CLC|PCr\.?LJ|PCrLJ|PTD|PLC|GBLR|KLR|PSC)(?:\s+[A-Za-z\.]+)*\s+\d+|'
    r'\d{4}\s+P\s*\.?\s*Cr\s*\.?\s*L\s*\.?\s*J\s*\.?\s*\d+'
    r')\b',
    re.IGNORECASE
)

def normalize_citation(citation: str) -> str:
    """
    Aggressively normalizes citations so '1993 PCr.LJ 781', '1993 P Cr. L. J. 781',
    and '1993 PCRLJ 781' all resolve to the exact same key.
    """
    if not citation:
        return ""
    c = str(citation).upper().strip()
    
    # Standardize common Pakistani reporter variations
    c = c.replace("SUPREME COURT", "SC")
    c = c.replace("CRIMINAL CASES", "CR")
    
    # Remove all periods and internal spaces inside reporter names (e.g. P. CR. L. J. -> PCRLJ)
    c = c.replace(".", "")
    c = re.sub(r'(?<=[A-Z])\s+(?=[A-Z])', '', c)
    
    # Collapse multiple spaces
    return re.sub(r'\s+', ' ', c)

def extract_citations_from_text(text: str) -> list[str]:
    """Extracts Pakistani legal reporter citations directly from raw text."""
    if not text:
        return []
    matches = CITATION_REGEX.findall(text)
    return list(dict.fromkeys([m.strip() for m in matches]))

def run_verification_agent(state: AgentState, truth_registry_path: str = "data/truth_registry.json") -> AgentState:
    """
    Agent 3: Deterministic Verification Gate.
    """
    try:
        if not os.path.exists(truth_registry_path):
            state["errors"].append(f"Truth Registry File Not Found at '{truth_registry_path}'")
            state["status"] = "verification_failed"
            return state

        with open(truth_registry_path, "r", encoding="utf-8") as f:
            truth_registry = json.load(f)

        # Build normalized registry mapping
        normalized_registry = {}
        for raw_key, meta in truth_registry.items():
            norm_k = normalize_citation(raw_key)
            normalized_registry[norm_k] = (raw_key, meta)

        candidates = state.get("candidate_citations", [])
        
        # Force extraction from chunks if candidate list is empty
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