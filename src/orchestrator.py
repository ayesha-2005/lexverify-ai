import os
from openai import OpenAI
from src.state import create_initial_state, AgentState
from src.agents.research import run_research_agent
from src.agents.retrieval import run_retrieval_agent
from src.agents.verification import run_verification_agent
from src.agents.synthesis import run_synthesis_agent

def run_lexverify_pipeline(
    user_question: str,
    client: OpenAI = None,
    truth_registry_path: str = "data/truth_registry.json"
) -> AgentState:
    """
    Main multi-agent orchestrator pipeline:
    Research Agent -> Retrieval Agent -> Verification Agent -> Synthesis Agent
    """
    # 1. Initialize default Groq client if none provided
    if client is None:
        client = OpenAI(
            base_url="https://api.groq.com/openai/v1",
            api_key=os.getenv("GROQ_API_KEY")
        )

    # 2. Create initial state
    state = create_initial_state(user_question)

    try:
        # Step 1: Research Agent (Generates candidate citations/keywords)
        state = run_research_agent(state, client)
        if state.get("status") == "research_failed":
            return state

        # Step 2: Retrieval Agent (Performs FAISS vector search)
        state = run_retrieval_agent(state)
        if state.get("status") == "retrieval_failed":
            return state

        # Step 3: Verification Agent (Deterministic Citation Truth Gate)
        state = run_verification_agent(state, truth_registry_path=truth_registry_path)
        if state.get("status") == "verification_failed":
            return state

        # Step 4: Synthesis Agent (Generates final answer using verified citations only)
        state = run_synthesis_agent(state, client)

    except Exception as e:
        if "errors" in state:
            state["errors"].append(f"Orchestrator Pipeline Error: {str(e)}")
        state["status"] = "pipeline_failed"

    return state