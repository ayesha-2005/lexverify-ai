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
    Main pipeline wrapper running:
    Research Agent -> Retrieval Agent -> Verification Agent -> Synthesis Agent
    """
    # Initialize default Groq client if none provided
    if client is None:
        client = OpenAI(
            base_url="https://api.groq.com/openai/v1",
            api_key=os.getenv("GROQ_API_KEY")
        )

    state = create_initial_state(user_question)

    # Step 1: Research Agent (Pass client!)
    state = run_research_agent(state, client)
    if state["status"] == "research_failed":
        return state

    # Step 2: Retrieval Agent (Real FAISS Search)
    state = run_retrieval_agent(state)
    if state["status"] == "retrieval_failed":
        return state

    # Step 3: Verification Agent (Deterministic Truth Gate)
    state = run_verification_agent(state, truth_registry_path=truth_registry_path)
    if state["status"] == "verification_failed":
        return state

    # Step 4: Synthesis Agent (Pass client!)
    state = run_synthesis_agent(state, client)

    return state