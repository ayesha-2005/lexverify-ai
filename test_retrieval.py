import os
from dotenv import load_dotenv
from openai import OpenAI
from src.state import create_initial_state
from src.agents.research import run_research_agent
from src.agents.retrieval import run_retrieval_agent

load_dotenv()

client = OpenAI(
    base_url="https://api.groq.com/openai/v1",
    api_key=os.getenv("GROQ_API_KEY")
)

# 1. Initialize State
state = create_initial_state("What is the standard for granting bail in non-bailable offenses?")

# 2. Run Research Agent
state = run_research_agent(state, client)

# 3. Run Retrieval Agent
state = run_retrieval_agent(state)

print("\n--- RETRIEVED CHUNKS ---")
print(state["retrieved_chunks"])
print("\n--- CANDIDATE CITATIONS EXTRACTED ---")
print(state["candidate_citations"])