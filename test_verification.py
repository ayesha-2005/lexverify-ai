import os
from dotenv import load_dotenv
from openai import OpenAI
from src.state import create_initial_state
from src.agents.research import run_research_agent
from src.agents.retrieval import run_retrieval_agent
from src.agents.verification import run_verification_agent

load_dotenv()

client = OpenAI(
    base_url="https://api.groq.com/openai/v1",
    api_key=os.getenv("GROQ_API_KEY")
)

# 1. Initialize State
state = create_initial_state("What is the standard for granting bail in non-bailable offenses?")

# 2. Run Pipeline Steps 1 to 3
state = run_research_agent(state, client)
state = run_retrieval_agent(state)
state = run_verification_agent(state, truth_registry_path="data/truth_registry.json")

print("\n--- VERIFIED CITATIONS ---")
print(state["verified_citations"])

print("\n--- REJECTED CITATIONS ---")
print(state["rejected_citations"])

print("\n--- STATUS ---")
print(state["status"])