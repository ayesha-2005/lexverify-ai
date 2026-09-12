import re
from typing import List, Dict, Any
from src.state import AgentState
from src.rag.retriever import retrieve_chunks

def extract_candidate_citations(chunks: List[Dict[str, Any]]) -> List[str]:
    """
    Regex pattern matcher to extract candidate legal citations from retrieved text chunks.
    """
    citation_pattern = r'\b(?:PLD|SCMR|CLC|PCrLJ|PTD|YLR|ALD|PLJ|PSC|K\.L\.R\.)\s+\d{4}\s+(?:SC|HC|LHR|KHI|Pesh|Quetta|Cr\.C\.|Crl\.|Criminal Cases|\d+)\b'
    candidates = set()
    for chunk in chunks:
        text = chunk.get("text", "")
        matches = re.findall(citation_pattern, text, flags=re.IGNORECASE)
        for m in matches:
            candidates.add(m.strip())
    return list(candidates)

def run_retrieval_agent(state: AgentState, retrieval_func=retrieve_chunks) -> AgentState:
    """
    Agent 2: Executes real FAISS vector retrieval using queries from state['research_plan']
    and extracts candidate citations.
    """
    try:
        queries = state.get("research_plan", {}).get("search_queries", [state["user_question"]])
        
        # Call Member 2's real FAISS vector retriever
        chunks = retrieval_func(queries, top_k=3)
        state["retrieved_chunks"] = chunks
        
        # Extract candidate citation strings from chunk text
        state["candidate_citations"] = extract_candidate_citations(chunks)
        state["status"] = "retrieval_completed"
        
    except Exception as e:
        state["errors"].append(f"Retrieval Agent Error: {str(e)}")
        state["status"] = "retrieval_failed"
        
    return state