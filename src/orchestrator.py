import os

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

from src.state import create_initial_state, AgentState
from src.agents.research import run_research_agent
from src.agents.retrieval import run_retrieval_agent
from src.rag.verifier import run_verification
from src.agents.synthesis import run_synthesis_agent


def run_lexverify_pipeline(
    user_question: str,
    client: OpenAI = None,
    truth_registry_path: str = "data/truth_registry.json"
) -> AgentState:
    """
    Main LexVerify AI pipeline:

    Research Agent
        ->
    Retrieval Agent
        ->
    Deterministic Truth Gate
        ->
    Synthesis Agent
    """

    if client is None:
        client = OpenAI(
            base_url="https://api.groq.com/openai/v1",
            api_key=os.getenv("GROQ_API_KEY")
        )

    # Fresh state for every user question
    state = create_initial_state(user_question)

    try:

        # ==================================================
        # 1. RESEARCH
        # ==================================================

        state = run_research_agent(
            state,
            client
        )

        # Research failure may still contain fallback queries.
        # Therefore, continue to retrieval.

        # ==================================================
        # 2. RETRIEVAL
        # ==================================================

        state = run_retrieval_agent(
            state
        )

        if state.get("status") == "retrieval_failed":
            return state

        # ==================================================
        # 3. DETERMINISTIC TRUTH GATE
        # ==================================================

        state = run_verification(
            state,
            registry_path=truth_registry_path
        )

        if state.get("status") == "verification_failed":
            return state

        # ==================================================
        # 4. SYNTHESIS
        # ==================================================

        state = run_synthesis_agent(
            state,
            client
        )

        return state

    except Exception as e:

        state.setdefault(
            "errors",
            []
        ).append(
            f"Orchestrator Pipeline Error: {str(e)}"
        )

        state["status"] = "pipeline_failed"

        return state