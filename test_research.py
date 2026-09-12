import os
from dotenv import load_dotenv
from openai import OpenAI
from src.state import create_initial_state
from src.agents.research import run_research_agent

# Load environment variables from .env
load_dotenv()

# Initialize OpenAI client configured for Groq
client = OpenAI(
    base_url="https://api.groq.com/openai/v1",
    api_key=os.getenv("GROQ_API_KEY")
)

# Test Research Agent
state = create_initial_state("What is the standard for granting bail in non-bailable offenses?")
res = run_research_agent(state, client)

print("\n--- RESEARCH PLAN OUTPUT ---")
print(res["research_plan"])