from typing import TypedDict, List, Dict, Any

class AgentState(TypedDict):
    user_question: str
    research_plan: Dict[str, Any]
    retrieved_chunks: List[Dict[str, Any]]
    candidate_citations: List[str]
    verified_citations: List[Dict[str, Any]]
    rejected_citations: List[str]
    final_answer: str
    status: str
    errors: List[str]

def create_initial_state(user_question: str) -> AgentState:
    return {
        "user_question": user_question,
        "research_plan": {},
        "retrieved_chunks": [],
        "candidate_citations": [],
        "verified_citations": [],
        "rejected_citations": [],
        "final_answer": "",
        "status": "initialized",
        "errors": []
    }