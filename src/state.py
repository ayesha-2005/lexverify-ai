from typing import TypedDict, List, Dict, Any


class AgentState(TypedDict):
    # =========================
    # User Input
    # =========================
    user_question: str

    # =========================
    # Research Agent
    # =========================
    research_plan: Dict[str, Any]
    extracted_keywords: List[str]

    # =========================
    # Retrieval Agent
    # =========================
    retrieved_chunks: List[Dict[str, Any]]
    candidate_citations: List[str]
    source_trace: List[Dict[str, Any]]

    # =========================
    # Verification Agent
    # =========================
    verified_citations: List[Dict[str, Any]]
    rejected_citations: List[str]
    verification_results: List[Dict[str, Any]]

    # =========================
    # Pipeline Metrics
    # =========================
    metrics_summary: Dict[str, int]

    # =========================
    # Final Response
    # =========================
    final_answer: str

    # =========================
    # Pipeline Status
    # =========================
    status: str
    errors: List[str]


def create_initial_state(user_question: str) -> AgentState:
    return {
        # User input
        "user_question": user_question,

        # Research
        "research_plan": {},
        "extracted_keywords": [],

        # Retrieval
        "retrieved_chunks": [],
        "candidate_citations": [],
        "source_trace": [],

        # Verification
        "verified_citations": [],
        "rejected_citations": [],
        "verification_results": [],

        # Metrics
        "metrics_summary": {
            "total_citations": 0,
            "verified_count": 0,
            "rejected_count": 0,
        },

        # Final answer
        "final_answer": "",

        # Status
        "status": "initialized",
        "errors": [],
    }